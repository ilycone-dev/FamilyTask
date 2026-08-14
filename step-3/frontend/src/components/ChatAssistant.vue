<script setup>
import { ref } from 'vue'
import { getAuthHeaders } from '../auth.js'
import { apiUrl } from '../api.js'

const emit = defineEmits(['assistant-response'])
const messages = ref([])
const input = ref('')
const error = ref(null)
const isRecording = ref(false)
let recognition = null

const supportsRecognition = typeof window !== 'undefined' && 'webkitSpeechRecognition' in window || 'SpeechRecognition' in window
if (supportsRecognition) {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
  recognition = new SpeechRecognition()
  recognition.lang = 'fr-FR'
  recognition.interimResults = false
  recognition.maxAlternatives = 1

  recognition.addEventListener('result', (event) => {
    const transcript = event.results[0][0].transcript
    input.value = transcript
  })

  recognition.addEventListener('end', () => {
    isRecording.value = false
  })
}

async function sendMessage() {
  if (!input.value.trim()) return

  const userMessage = input.value.trim()
  messages.value.push({ role: 'user', text: userMessage })
  input.value = ''
  error.value = null

  try {
    const res = await fetch(apiUrl('/api/assistant'), {
      method: 'POST',
      headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: userMessage }),
    })
    if (!res.ok) {
      throw new Error('Impossible de contacter l’assistant')
    }
    const data = await res.json()
    messages.value.push({ role: 'assistant', text: data.text || 'Aucune réponse' })
    emit('assistant-response', !!data.task_created)
  } catch (err) {
    error.value = err.message
  }
}

function startRecording() {
  if (!recognition) return
  isRecording.value = true
  error.value = null
  recognition.start()
}
</script>

<template>
  <div class="assistant-card">
    <div class="message-area">
      <div v-for="(message, index) in messages" :key="index" :class="['message', message.role]">
        <div class="bubble">{{ message.text }}</div>
      </div>
      <p v-if="!messages.length" class="hint">Demande-moi d'ajouter une tâche, par exemple « ajoute la tâche Ranger la chambre à Lea ».</p>
    </div>

    <div class="input-row">
      <input v-model="input" placeholder="Demande à l’assistant..." @keyup.enter="sendMessage" />
      <button type="button" class="icon-round" @click="startRecording" :disabled="!supportsRecognition || isRecording" title="Dicter">🎤</button>
      <button type="button" class="icon-round" @click="sendMessage" title="Envoyer">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 2 11 13" /><path d="M22 2 15 22l-4-9-9-4 20-7Z" /></svg>
      </button>
    </div>
    <p class="error" v-if="error">{{ error }}</p>
  </div>
</template>

<style scoped>
.assistant-card {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.message-area {
  max-height: 340px;
  overflow-y: auto;
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 12px;
  background: var(--surface-2);
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.message { display: flex; }
.message.user { justify-content: flex-end; }
.message.assistant { justify-content: flex-start; }
.bubble {
  max-width: 82%;
  padding: 10px 14px;
  border-radius: 16px;
  font-size: 14.5px;
  line-height: 1.4;
  white-space: pre-wrap;
}
.message.user .bubble {
  background: linear-gradient(120deg, var(--grad-1), var(--grad-2));
  color: #fff;
  border-bottom-right-radius: 4px;
}
.message.assistant .bubble {
  background: var(--surface);
  border: 1px solid var(--border);
  color: var(--text);
  border-bottom-left-radius: 4px;
}
.input-row {
  display: flex;
  gap: 8px;
  align-items: center;
}
.input-row input {
  flex: 1;
  border-radius: 999px;
}
.icon-round {
  width: 44px;
  height: 44px;
  flex: none;
  display: grid;
  place-items: center;
  border-radius: 50%;
  padding: 0;
}
.icon-round svg { width: 18px; height: 18px; }
</style>
