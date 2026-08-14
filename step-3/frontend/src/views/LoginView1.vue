<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { saveToken, fetchUser } from '../auth.js'

const email = ref('')
const password = ref('')
const error = ref(null)
const router = useRouter()

async function submit() {
  error.value = null
  try {
    const res = await fetch('/api/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: email.value, password: password.value }),
    })
    if (!res.ok) throw new Error('Identifiants invalides')
    const data = await res.json()
    saveToken(data.token)
    await fetchUser()
    router.push({ name: 'Tasks' })
  } catch (err) {
    error.value = err.message
  }
}
</script>

<template>
  <div class="card">
    <h2>Connexion</h2>
    <div class="row"><input v-model="email" placeholder="Email" type="email" /></div>
    <div class="row"><input v-model="password" placeholder="Mot de passe" type="password" /></div>
    <button @click="submit">Se connecter</button>
    <p class="hint">Pas encore de compte ? <router-link to="/signup">Créer ma famille</router-link></p>
    <p class="error" v-if="error">{{ error }}</p>
  </div>
</template>
