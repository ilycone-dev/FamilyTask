"""
Tests du back-end FamilyTask.

Important : on doit fixer DATABASE_URL vers une base de test AVANT
d'importer `main`, car `main.py` se connecte à la base dès son import
(variable globale `engine`). Sans ça, les tests utiliseraient — et
pollueraient — ta vraie base `familytask.db`.

Lancer les tests (depuis le dossier backend/, sans Docker) :
    pip install -r requirements.txt
    pytest
"""
import atexit
import os
import shutil
import tempfile

_TEST_DIR = tempfile.mkdtemp(prefix="familytask-tests-")
_TEST_DB_PATH = os.path.join(_TEST_DIR, "test_familytask.db")
os.environ["DATABASE_URL"] = f"sqlite:///{_TEST_DB_PATH}"
atexit.register(shutil.rmtree, _TEST_DIR, True)

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlmodel import SQLModel  # noqa: E402

import main  # noqa: E402  (importé après avoir fixé DATABASE_URL — c'est voulu)


@pytest.fixture(autouse=True)
def base_de_test_propre():
    """Repart d'un schéma vide avant chaque test, pour que les tests
    ne dépendent pas les uns des autres (même email, même famille, etc.)."""
    SQLModel.metadata.drop_all(main.engine)
    SQLModel.metadata.create_all(main.engine)
    yield


@pytest.fixture
def client():
    return TestClient(main.app)


def test_inscription_puis_creation_de_tache_visible_dans_la_liste(client):
    # 1. On inscrit une famille de test (champ "family" vide = nouvelle famille)
    reponse_inscription = client.post(
        "/api/signup",
        json={
            "email": "parent.test@example.com",
            "password": "motdepasse123",
            "name": "ParentTest",
            "lien": "parent",
            "family": "",
        },
    )
    assert reponse_inscription.status_code == 201, reponse_inscription.text
    token = reponse_inscription.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. On crée une tâche pour soi-même (pas de member_id = s'assigne à soi)
    reponse_creation = client.post(
        "/api/tasks",
        json={"title": "Ranger la chambre"},
        headers=headers,
    )
    assert reponse_creation.status_code == 201, reponse_creation.text

    # 3. On vérifie qu'elle apparaît bien dans GET /api/tasks
    reponse_liste = client.get("/api/tasks", headers=headers)
    assert reponse_liste.status_code == 200
    titres = [tache["title"] for tache in reponse_liste.json()]
    assert "Ranger la chambre" in titres


def test_get_tasks_sans_token_renvoie_401(client):
    reponse = client.get("/api/tasks")
    assert reponse.status_code == 401
