<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { saveToken, fetchUser } from '../auth.js'
import { apiUrl } from '../api.js'

const mode = ref('create') // 'create' = nouvelle famille, 'join' = rejoindre avec un code

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
    const res = await fetch(apiUrl('/api/signup'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email: email.value,
        password: password.value,
        name: name.value,
        // En mode "créer", on envoie toujours un code vide, même si le champ
        // a été rempli puis caché en changeant de mode — pas d'ambiguïté possible.
        family: mode.value === 'join' ? family.value : '',
        lien: lien.value,
      }),
    })
    if (!res.ok) {
      let message = `Impossible de créer la famille (code ${res.status})`
      try {
        const data = await res.json()
        if (data.detail) message = data.detail
      } catch {
        // la réponse n'était pas du JSON (ex: erreur réseau/serveur brute)
      }
      throw new Error(message)
    }
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
    <h2>Créer un compte</h2>

    <div class="mode-toggle">
      <button type="button" :class="{ active: mode === 'create' }" @click="mode = 'create'">
        Nouvelle famille
      </button>
      <button type="button" :class="{ active: mode === 'join' }" @click="mode = 'join'">
        Rejoindre une famille
      </button>
    </div>

    <div class="row"><input v-model="email" placeholder="Email" type="email" /></div>
    <div class="row"><input v-model="password" placeholder="Mot de passe" type="password" /></div>
    <div class="row"><input v-model="name" placeholder="Prénom" /></div>
    <div class="row"><input v-model="lien" placeholder="Lien (parenté)" /></div>

    <template v-if="mode === 'join'">
      <div class="row"><input v-model="family" placeholder="Code famille (donné par l'admin de ta famille)" /></div>
      <p class="hint">Demande ce code à l'admin de ta famille — il le trouve dans « Gestion de la famille ».</p>
    </template>
    <p class="hint" v-else>Tu deviendras l'admin d'une toute nouvelle famille.</p>

    <button @click="submit">{{ mode === 'join' ? 'Rejoindre' : 'Créer ma famille' }}</button>
    <p class="hint">Déjà inscrit ? <router-link to="/login">Se connecter</router-link></p>
    <p class="error" v-if="error">{{ error }}</p>
  </div>
</template>
