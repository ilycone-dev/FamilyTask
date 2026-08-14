import hashlib
import json
import os
import sqlite3
import unicodedata
import uuid
from typing import Optional, Generator, List, Dict

import httpx
from fastapi import FastAPI, Depends, Header, HTTPException, status, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel, Field, Session, create_engine, select

# La ligne de connexion à la base — déjà configurée pour toi (Docker fournit l'adresse).
# Hors Docker, on retombe sur un simple fichier SQLite. Tu n'as rien à changer ici.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///familytask.db")
# Certaines plateformes (dont Render) fournissent encore "postgres://",
# alors que SQLAlchemy récent exige "postgresql://". Sans ça, la connexion
# échoue au démarrage une fois déployé.
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, echo=False, connect_args=connect_args)


class Member(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(sa_column_kwargs={"unique": True}, index=True)
    name: str
    lien: Optional[str] = None
    is_admin: bool = False
    family_code: Optional[str] = None
    password_hash: Optional[str] = None
    token: Optional[str] = None


class Task(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    done: bool = False
    member_id: int = Field(foreign_key="member.id")


class Lien(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    family_code: str = Field(index=True)
    label: str


class SignupPayload(SQLModel):
    email: str
    password: str
    name: str
    family: str
    lien: Optional[str] = None


class LoginPayload(SQLModel):
    email: str
    password: str


class AssistantPayload(SQLModel):
    message: str


class MemberCreatePayload(SQLModel):
    email: str
    password: str
    name: str
    lien: str
    is_admin: bool = False


class TaskCreate(SQLModel):
    title: Optional[str] = None
    member_id: Optional[int] = None


class LienCreatePayload(SQLModel):
    label: str


from random import choice


def hash_password(pw: str) -> str:
    return hashlib.sha256(pw.encode('utf-8')).hexdigest()


def generate_family_code() -> str:
    return uuid.uuid4().hex[:8].upper()


def generate_token() -> str:
    return uuid.uuid4().hex


ASSISTANT_TOOLS = [
    {
        "name": "ajouter_tache",
        "description": "Créer une tâche pour un membre de la famille en utilisant son prénom.",
        "parameters": {
            "type": "object",
            "properties": {
                "titre": {
                    "type": "string",
                    "description": "Le titre de la tâche à créer.",
                },
                "personne": {
                    "type": "string",
                    "description": "Le prénom du membre de la famille.",
                },
            },
            "required": ["titre", "personne"],
        },
    }
]


def ensure_database_schema():
    db_file = DATABASE_URL.replace('sqlite:///', '')
    if os.path.exists(db_file):
        try:
            conn = sqlite3.connect(db_file)
            conn.execute('SELECT member_id FROM task LIMIT 1')
            conn.close()
            return
        except sqlite3.OperationalError:
            conn.close()
            os.remove(db_file)
    SQLModel.metadata.create_all(engine)


OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL = "qwen2.5:3b"

ensure_database_schema()

app = FastAPI(title="FamilyTask")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session


def get_current_member(
    authorization: Optional[str] = Header(None),
    session: Session = Depends(get_session),
) -> Member:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    token = authorization.split(" ", 1)[1].strip()
    member = session.exec(select(Member).where(Member.token == token)).first()
    if not member:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    return member


@app.get("/api/health")
def health():
    return {"status": "ok"}


def parse_tool_calls(data: Dict) -> List[Dict]:
    # La réponse d'Ollama place les tool_calls DANS l'objet "message",
    # pas à la racine : {"message": {"tool_calls": [...]}, ...}
    message_obj = data.get("message")
    tool_calls = None
    if isinstance(message_obj, dict):
        tool_calls = message_obj.get("tool_calls")
    if not tool_calls:
        tool_calls = data.get("tool_calls") or data.get("tool_call")
    if not tool_calls:
        return []
    if isinstance(tool_calls, str):
        try:
            tool_calls = json.loads(tool_calls)
        except ValueError:
            return []
    if isinstance(tool_calls, dict):
        return [tool_calls]
    return list(tool_calls)


def find_ambiguous_lien(message: str, family_code: str, session: Session) -> Optional[str]:
    text = message.lower()
    liens: Dict[str, List[Member]] = {}
    members = session.exec(select(Member).where(Member.family_code == family_code)).all()
    for member in members:
        if not member.lien:
            continue
        lien = member.lien.strip().lower()
        if not lien:
            continue
        if lien in text or f"ma {lien}" in text or f"mon {lien}" in text or f"mes {lien}" in text:
            liens.setdefault(lien, []).append(member)

    for lien, matched in liens.items():
        if len(matched) > 1:
            names = ', '.join([m.name for m in matched if m.name])
            plural = lien if lien.endswith('s') else lien + 's'
            return f"Il y a plusieurs {plural} ({names}). Pour qui ?"
    return None


def normalize_text(text: str) -> str:
    return unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii').strip().lower()


def find_family_member_by_first_name(first_name: str, family_code: str, session: Session) -> Optional[Member]:
    normalized_first_name = normalize_text(first_name)
    if not normalized_first_name:
        return None
    members = session.exec(select(Member).where(Member.family_code == family_code)).all()
    exact_matches = []
    partial_matches = []

    for member in members:
        if not member.name:
            continue
        normalized_name = normalize_text(member.name)
        first_word = normalized_name.split()[0] if normalized_name else ''
        if first_word == normalized_first_name:
            exact_matches.append(member)
        elif normalized_first_name in normalized_name:
            partial_matches.append(member)

    if len(exact_matches) == 1:
        return exact_matches[0]
    if len(exact_matches) > 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Plusieurs membres ont le prénom '{first_name}'. Précisez."
        )
    if len(partial_matches) == 1:
        return partial_matches[0]
    if len(partial_matches) > 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Plusieurs membres correspondent à '{first_name}'. Précisez."
        )
    return None


@app.post("/api/signup", status_code=status.HTTP_201_CREATED)
def signup(payload: SignupPayload, session: Session = Depends(get_session)):
    existing = session.exec(select(Member).where(Member.email == payload.email)).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    requested_code = (payload.family or "").strip().upper()
    is_admin = True
    if requested_code:
        family_member = session.exec(
            select(Member).where(Member.family_code == requested_code)
        ).first()
        if not family_member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Aucune famille ne correspond à ce code",
            )
        family_code = requested_code
        is_admin = False
    else:
        family_code = generate_family_code()

    token = generate_token()
    member = Member(
        email=payload.email,
        name=payload.name,
        lien=payload.lien,
        is_admin=is_admin,
        family_code=family_code,
        password_hash=hash_password(payload.password),
        token=token,
    )
    session.add(member)
    session.commit()
    session.refresh(member)
    return {"token": token, "family_code": family_code}


@app.post("/api/login")
def login(payload: LoginPayload, session: Session = Depends(get_session)):
    member = session.exec(select(Member).where(Member.email == payload.email)).first()
    if not member or member.password_hash != hash_password(payload.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    member.token = generate_token()
    session.add(member)
    session.commit()
    session.refresh(member)
    return {"token": member.token}


@app.get("/api/me")
def me(current_member: Member = Depends(get_current_member)):
    return {
        "id": current_member.id,
        "email": current_member.email,
        "name": current_member.name,
        "lien": current_member.lien,
        "is_admin": current_member.is_admin,
        "family_code": current_member.family_code,
    }


@app.post("/api/assistant")
async def assistant(
    payload: AssistantPayload,
    current_member: Member = Depends(get_current_member),
    session: Session = Depends(get_session),
):
    message = payload.message.strip() if payload.message else ""
    if not message:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Message is required")

    ambiguous = find_ambiguous_lien(message, current_member.family_code, session)
    if ambiguous:
        return {"text": ambiguous}

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream(
                "POST",
                f"{OLLAMA_URL}/api/chat",
                json={
                    "model": OLLAMA_MODEL,
                    "messages": [
                        {
                            "role": "system",
                            "content": (
                                "Tu es l'assistant de l'application FamilyTask. "
                                "Ton travail est de transformer les demandes de création de tâche "
                                "en appels d'outil à ajouter_tache. "
                                "Quand l'utilisateur demande d'ajouter une tâche à un membre, "
                                "tu dois répondre en utilisant uniquement le tool ajouter_tache avec "
                                "les arguments {titre, personne}. Ne réponds pas en texte libre pour ce type d'action. "
                                "Utilise uniquement le prénom du membre pour la valeur personne, "
                                "ignore toute précision de lien de parenté (ex: 'qui a le lien fils', 'qui est ma fille') : "
                                "elle ne fait pas partie des arguments de l'outil. "
                                "Exemple : pour 'ajoute la tâche Ranger la chambre à Lea qui a le lien fille', "
                                "appelle ajouter_tache avec titre='Ranger la chambre' et personne='Lea'. "
                                "Si plusieurs membres partagent le même prénom, renvoie une question de clarification. "
                                "Si l'action est clairement une création de tâche, appelle systématiquement le tool, "
                                "ne réponds jamais par une simple confirmation en texte libre.")
                        },
                        {"role": "user", "content": message},
                    ],
                    "tools": ASSISTANT_TOOLS,
                    "tool_calls": "auto",
                    "stream": False,
                },
                headers={"Content-Type": "application/json", "Accept": "application/json"},
            ) as response:
                if response.status_code != 200:
                    raise HTTPException(
                        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        detail="Assistant is not ready",
                    )

                assistant_text = ""
                tool_calls: List[Dict] = []
                last_data: Optional[Dict] = None

                async for line in response.aiter_lines():
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                    except ValueError:
                        continue
                    last_data = data
                    tool_calls.extend(parse_tool_calls(data))
                    if isinstance(data, dict):
                        message_obj = data.get("message")
                        if isinstance(message_obj, dict):
                            assistant_text += message_obj.get("content", "") or ""
                        if not assistant_text and data.get("response"):
                            assistant_text = data.get("response")

                if last_data is not None and not assistant_text:
                    assistant_text = last_data.get("response") or ""
                    if not assistant_text:
                        choices = last_data.get("choices") or []
                        if choices:
                            first = choices[0]
                            assistant_text = (
                                first.get("message", {}).get("content")
                                or first.get("content")
                                or ""
                            )

    except httpx.RequestError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Assistant is not ready",
        )

    if tool_calls:
        for tool_call in tool_calls:
            # Ollama renvoie {"function": {"name": ..., "arguments": ...}} —
            # on garde un repli sur un format plat au cas où.
            function_obj = tool_call.get("function") if isinstance(tool_call.get("function"), dict) else {}
            name = function_obj.get("name") or tool_call.get("name")
            if not name and len(ASSISTANT_TOOLS) == 1:
                # qwen2.5:3b laisse parfois "name" vide tout en remplissant
                # correctement les arguments. Un seul outil existe ici, donc
                # pas d'ambiguïté possible : on complète le nom manquant.
                name = ASSISTANT_TOOLS[0]["name"]
            arguments = function_obj.get("arguments")
            if arguments is None:
                arguments = tool_call.get("arguments") or {}
            if isinstance(arguments, str):
                try:
                    arguments = json.loads(arguments)
                except ValueError:
                    arguments = {}

            if name == "ajouter_tache":
                titre = (arguments.get("titre") or arguments.get("title") or "").strip()
                personne = (arguments.get("personne") or arguments.get("person") or "").strip()
                if not titre or not personne:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Tool ajouter_tache requires titre and personne",
                    )

                member = find_family_member_by_first_name(personne, current_member.family_code, session)
                if not member:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Personne '{personne}' introuvable dans la famille",
                    )

                task = Task(title=titre, member_id=member.id)
                session.add(task)
                session.commit()
                session.refresh(task)
                return {"text": f"La tâche « {task.title} » a été créée pour {member.name}.", "task_created": True}

    if not assistant_text:
        assistant_text = (
            "Je n'ai pas compris cette demande. Essaie une formulation simple, "
            "par exemple : « ajoute la tâche Ranger la chambre à Lea »."
        )
    return {"text": assistant_text, "task_created": False}


@app.get("/api/liens")
def list_liens(
    current_member: Member = Depends(get_current_member),
    session: Session = Depends(get_session),
):
    return session.exec(select(Lien).where(Lien.family_code == current_member.family_code)).all()


@app.post("/api/liens", status_code=status.HTTP_201_CREATED)
def create_lien(
    payload: LienCreatePayload,
    current_member: Member = Depends(get_current_member),
    session: Session = Depends(get_session),
):
    lien = Lien(family_code=current_member.family_code, label=payload.label)
    session.add(lien)
    session.commit()
    session.refresh(lien)
    return lien


@app.post("/api/members", status_code=status.HTTP_201_CREATED)
def create_member(
    payload: MemberCreatePayload,
    current_member: Member = Depends(get_current_member),
    session: Session = Depends(get_session),
):
    if not current_member.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    existing = session.exec(select(Member).where(Member.email == payload.email)).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    member = Member(
        email=payload.email,
        name=payload.name,
        lien=payload.lien,
        is_admin=payload.is_admin,
        family_code=current_member.family_code,
        password_hash=hash_password(payload.password),
        token=generate_token(),
    )
    session.add(member)
    session.commit()
    session.refresh(member)
    return member


@app.delete("/api/members/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_member(
    member_id: int,
    current_member: Member = Depends(get_current_member),
    session: Session = Depends(get_session),
):
    if not current_member.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    if current_member.id == member_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete yourself")

    member = session.get(Member, member_id)
    if not member or member.family_code != current_member.family_code:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")

    tasks = session.exec(select(Task).where(Task.member_id == member_id)).all()
    for task in tasks:
        session.delete(task)
    session.delete(member)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.get("/api/members")
def list_members(
    current_member: Member = Depends(get_current_member),
    session: Session = Depends(get_session),
):
    if not current_member.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return session.exec(select(Member).where(Member.family_code == current_member.family_code)).all()


@app.get("/api/tasks/all")
def list_all_tasks(
    current_member: Member = Depends(get_current_member),
    session: Session = Depends(get_session),
):
    if not current_member.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    members = session.exec(select(Member).where(Member.family_code == current_member.family_code)).all()
    member_ids = [m.id for m in members]
    return session.exec(select(Task).where(Task.member_id.in_(member_ids))).all()


@app.get("/api/tasks")
def list_tasks(
    current_member: Member = Depends(get_current_member),
    session: Session = Depends(get_session),
):
    return session.exec(select(Task).where(Task.member_id == current_member.id)).all()


@app.post("/api/tasks", status_code=status.HTTP_201_CREATED)
def create_task(
    payload: TaskCreate,
    current_member: Member = Depends(get_current_member),
    session: Session = Depends(get_session),
):
    title = payload.title.strip() if payload.title else ""
    if not title:
        title = choice([
            "Repasser les vêtements",
            "Appeler Mamie",
            "Préparer le dîner",
            "Faire les devoirs",
            "Arroser les plantes",
        ])

    member_id = current_member.id
    if payload.member_id is not None:
        if not current_member.is_admin:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        target_member = session.get(Member, payload.member_id)
        if target_member is None or target_member.family_code != current_member.family_code:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")
        member_id = target_member.id

    task = Task(title=title, member_id=member_id)
    session.add(task)
    session.commit()
    session.refresh(task)
    return task


@app.patch("/api/tasks/{task_id}")
def toggle_task(
    task_id: int,
    current_member: Member = Depends(get_current_member),
    session: Session = Depends(get_session),
):
    task = session.get(Task, task_id)
    if task is None or task.member_id != current_member.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "Task not found", "task_id": task_id},
        )
    task.done = not task.done
    session.add(task)
    session.commit()
    session.refresh(task)
    return task


@app.delete("/api/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: int,
    current_member: Member = Depends(get_current_member),
    session: Session = Depends(get_session),
):
    task = session.get(Task, task_id)
    if not task or task.member_id != current_member.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    session.delete(task)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
