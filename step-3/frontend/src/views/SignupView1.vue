<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { saveToken, fetchUser } from '../auth.js'

const email = ref('')
const password = ref('')
const name = ref('')
const family = ref('')
const lien = ref('')
const error = ref(null)
const router = useRouter()

async function submit() {
  error.value = null
  try {
    const res = await fetch('/api/signup', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email: email.value,
        password: password.value,
        name: name.value,
        family: family.value,
        lien: lien.value,
      }),
    })
    if (!res.ok) throw new Error('Impossible de créer la famille')
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
    <h2>Créer ma famille</h2>
    <div class="row"><input v-model="email" placeholder="Email" type="email" /></div>
    <div class="row"><input v-model="password" placeholder="Mot de passe" type="password" /></div>
    <div class="row"><input v-model="name" placeholder="Prénom" /></div>
    <div class="row"><input v-model="family" placeholder="Nom de famille" /></div>
    <div class="row"><input v-model="lien" placeholder="Lien (parenté)" /></div>
    <button @click="submit">Créer</button>
    <p class="hint">Déjà inscrit ? <router-link to="/login">Se connecter</router-link></p>
    <p class="error" v-if="error">{{ error }}</p>
  </div>
</template>
