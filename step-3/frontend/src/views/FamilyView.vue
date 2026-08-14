<script setup>
import { ref, onMounted, computed } from 'vue'
import { authState, getAuthHeaders } from '../auth.js'
import Avatar from '../components/Avatar.vue'
import { apiUrl } from '../api.js'

const members = ref([])
const liens = ref([])
const tasks = ref([])
const error = ref(null)
const newMember = ref({ email: '', password: '', name: '', lien: '', is_admin: false })
const newLien = ref('')

async function loadFamilyData() {
  try {
    const [membersRes, liensRes, tasksRes] = await Promise.all([
      fetch(apiUrl('/api/members'), { headers: getAuthHeaders() }),
      fetch(apiUrl('/api/liens'), { headers: getAuthHeaders() }),
      fetch(apiUrl('/api/tasks/all'), { headers: getAuthHeaders() }),
    ])
    if (!membersRes.ok || !liensRes.ok || !tasksRes.ok) throw new Error('Impossible de charger les données de la famille')
    members.value = await membersRes.json()
    liens.value = await liensRes.json()
    tasks.value = await tasksRes.json()
  } catch (err) {
    error.value = err.message
  }
}

onMounted(loadFamilyData)

function progressFor(memberId) {
  const memberTasks = tasks.value.filter((t) => t.member_id === memberId)
  if (!memberTasks.length) return null
  return memberTasks.filter((t) => t.done).length / memberTasks.length
}

function nameFor(memberId) {
  return members.value.find((m) => m.id === memberId)?.name || `#${memberId}`
}

async function addMember() {
  try {
    const res = await fetch(apiUrl('/api/members'), {
      method: 'POST',
      headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' },
      body: JSON.stringify(newMember.value),
    })
    if (!res.ok) throw new Error('Impossible de créer le membre')
    newMember.value = { email: '', password: '', name: '', lien: '', is_admin: false }
    await loadFamilyData()
  } catch (err) {
    error.value = err.message
  }
}

async function deleteMember(id) {
  try {
    const res = await fetch(apiUrl(`/api/members/${id}`), { method: 'DELETE', headers: getAuthHeaders() })
    if (res.status !== 204) throw new Error('Impossible de supprimer le membre')
    await loadFamilyData()
  } catch (err) {
    error.value = err.message
  }
}

async function addLien() {
  try {
    const res = await fetch(apiUrl('/api/liens'), {
      method: 'POST',
      headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' },
      body: JSON.stringify({ label: newLien.value }),
    })
    if (!res.ok) throw new Error('Impossible de créer le lien')
    newLien.value = ''
    await loadFamilyData()
  } catch (err) {
    error.value = err.message
  }
}
</script>

<template>
  <div class="card">
    <h2>Gestion de la famille</h2>
    <p class="hint">
      Code famille à partager : <strong>{{ authState.user?.family_code }}</strong>
    </p>

    <div class="section">
      <h3>Membres</h3>
      <div class="row"><input v-model="newMember.email" placeholder="Email" type="email" /></div>
      <div class="row"><input v-model="newMember.password" placeholder="Mot de passe" type="password" /></div>
      <div class="row"><input v-model="newMember.name" placeholder="Prénom" /></div>
      <div class="row"><input v-model="newMember.lien" placeholder="Lien" /></div>
      <div class="row">
        <label><input type="checkbox" v-model="newMember.is_admin" /> Admin</label>
      </div>
      <button @click="addMember">Créer un membre</button>
      <ul>
        <li v-for="member in members" :key="member.id" class="member-item">
          <Avatar :name="member.name" :progress="progressFor(member.id)" />
          <div class="member-details">
            <strong>{{ member.name }}</strong>
            <small>{{ member.email }} · {{ member.lien }} {{ member.is_admin ? '· admin' : '' }}</small>
          </div>
          <button class="trash" @click="deleteMember(member.id)">🗑</button>
        </li>
      </ul>
    </div>

    <div class="section">
      <h3>Liens</h3>
      <div class="row"><input v-model="newLien" placeholder="Nouvel intitulé de lien" /></div>
      <button @click="addLien">Ajouter un lien</button>
      <ul>
        <li v-for="l in liens" :key="l.id">{{ l.label }}</li>
      </ul>
    </div>

    <div class="section">
      <h3>Toutes les tâches</h3>
      <ul>
        <li v-for="task in tasks" :key="task.id" :class="{ done: task.done }">
          <Avatar :name="nameFor(task.member_id)" :size="30" />
          <span>{{ task.title }}</span>
        </li>
        <li v-if="tasks.length === 0" class="hint">Aucune tâche pour l'instant. 🎉</li>
      </ul>
    </div>

    <p class="error" v-if="error">{{ error }}</p>
  </div>
</template>
