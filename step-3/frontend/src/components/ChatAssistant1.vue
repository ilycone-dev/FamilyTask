<script setup>
import { ref } from 'vue'
import { getAuthHeaders } from '../auth.js'

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
    const res = await fetch('/api/assistant', {
      method: 'POST',
      headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: userMessage }),
    })
    if (!res.ok) {
      throw new Error('Impossible de contacter l’assistant')
    }
    const data = await res.json()
    messages.value.push({ role: 'assistant', text: data.text || 'Aucune réponse' })
    emit('assistant-response')
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
        <strong>{{ message.role === 'user' ? 'Moi' : 'Assistant' }}</strong>
        <p>{{ message.text }}</p>
      </div>
    </div>

    <div class="input-row">
      <input v-model="input" placeholder="Demande à l’assistant..." @keyup.enter="sendMessage" />
      <button type="button" @click="sendMessage">Envoyer</button>
      <button type="button" @click="startRecording" :disabled="!supportsRecognition || isRecording">🎤</button>
    </div>
    <p class="error" v-if="error">{{ error }}</p>
  </div>
</template>

<style scoped>
.assistant-card {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}
.message-area {
  max-height: 300px;
  overflow-y: auto;
  border: 1px solid #ddd;
  border-radius: 12px;
  padding: 12px;
  background: #fff;
}
.message {
  margin-bottom: 1rem;
}
.message.user {
  text-align: right;
}
.message.assistant {
  text-align: left;
}
.input-row {
  display: flex;
  gap: 0.5rem;
}
.input-row input {
  flex: 1;
  padding: 0.75rem;
  border: 1px solid #ccc;
  border-radius: 999px;
}
.input-row button {
  padding: 0.75rem 1rem;
  border: none;
  border-radius: 999px;
  background: #2d76ff;
  color: white;
  cursor: pointer;
}
.input-row button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.error {
  color: #bf1650;
}
</style>
