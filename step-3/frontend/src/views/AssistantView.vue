<script setup>
import { ref, onMounted } from 'vue'
import ChatAssistant from '../components/ChatAssistant.vue'
import TaskList from '../components/TaskList.vue'
import { getAuthHeaders } from '../auth.js'
import { apiUrl } from '../api.js'

const tasks = ref([])
const assistantResponse = ref(null)
const error = ref(null)

async function loadTasks() {
  try {
    const res = await fetch(apiUrl('/api/tasks'), { headers: getAuthHeaders() })
    if (!res.ok) throw new Error('Impossible de charger les tâches')
    tasks.value = await res.json()
  } catch (err) {
    error.value = err.message
  }
}

onMounted(loadTasks)

async function handleAssistantResponse(taskCreated) {
  assistantResponse.value = taskCreated
    ? 'La liste des tâches a été rafraîchie.'
    : null
  await loadTasks()
}
</script>

<template>
  <div class="card">
    <h2>Assistant</h2>
    <ChatAssistant @assistant-response="handleAssistantResponse" />
    <p v-if="assistantResponse" class="success">{{ assistantResponse }}</p>
    <div class="section">
      <h3>Mes tâches</h3>
      <TaskList :tasks="tasks" />
      <p class="error" v-if="error">{{ error }}</p>
    </div>
  </div>
</template>


