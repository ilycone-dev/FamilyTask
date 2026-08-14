<script setup>
import { ref, onMounted } from 'vue'
import TaskList from '../components/TaskList.vue'
import Avatar from '../components/Avatar.vue'
import { authState, getAuthHeaders } from '../auth.js'
import { apiUrl } from '../api.js'

const tasks = ref([])
const members = ref([])
const selectedMemberId = ref(null)
const newTitle = ref('')
const error = ref(null)

async function loadMembers() {
  try {
    if (!authState.user?.is_admin) return
    const res = await fetch(apiUrl('/api/members'), { headers: getAuthHeaders() })
    if (!res.ok) return
    members.value = await res.json()
    if (!selectedMemberId.value && authState.user?.id) {
      selectedMemberId.value = authState.user.id
    }
  } catch {
    // ignore if members cannot be loaded
  }
}

async function loadTasks() {
  try {
    const res = await fetch(apiUrl('/api/tasks'), { headers: getAuthHeaders() })
    if (!res.ok) throw new Error('Impossible de charger les tâches')
    tasks.value = await res.json()
  } catch (err) {
    error.value = err.message
  }
}

onMounted(async () => {
  await Promise.all([loadTasks(), loadMembers()])
})

async function addTask() {
  try {
    const payload = { title: newTitle.value }
    if (selectedMemberId.value) {
      payload.member_id = selectedMemberId.value
    }
    const res = await fetch(apiUrl('/api/tasks'), {
      method: 'POST',
      headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
    if (!res.ok) throw new Error('Impossible d’ajouter la tâche')
    newTitle.value = ''
    await loadTasks()
  } catch (err) {
    error.value = err.message
  }
}

async function toggle(task) {
  try {
    const res = await fetch(apiUrl(`/api/tasks/${task.id}`), { method: 'PATCH', headers: getAuthHeaders() })
    if (!res.ok) throw new Error('Impossible de basculer la tâche')
    await loadTasks()
  } catch (err) {
    error.value = err.message
  }
}

async function remove(task) {
  try {
    const res = await fetch(apiUrl(`/api/tasks/${task.id}`), { method: 'DELETE', headers: getAuthHeaders() })
    if (res.status !== 204) throw new Error('Impossible de supprimer la tâche')
    await loadTasks()
  } catch (err) {
    error.value = err.message
  }
}
</script>

<template>
  <div class="card">
    <h2>Mes tâches</h2>
    <div class="row">
      <input v-model="newTitle" placeholder="Nouvelle tâche" @keyup.enter="addTask" />
      <button @click="addTask">Ajouter</button>
    </div>
    <div v-if="members.length">
      <label class="small">Affecter à</label>
      <div class="member-picker">
        <button
          v-for="member in members"
          :key="member.id"
          type="button"
          class="member-chip"
          :class="{ selected: selectedMemberId === member.id }"
          @click="selectedMemberId = member.id"
        >
          <span class="ring-outer"><Avatar :name="member.name" :size="44" /></span>
          <span>{{ member.name }}</span>
        </button>
      </div>
    </div>
    <TaskList :tasks="tasks" @toggle="toggle" @remove="remove" />
    <p class="error" v-if="error">{{ error }}</p>
  </div>
</template>
