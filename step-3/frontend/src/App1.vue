<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { authState, logout } from './auth.js'

const router = useRouter()
const isAdmin = computed(() => authState.user?.is_admin)
const userName = computed(() => authState.user?.name || '')

function doLogout() {
  logout()
  router.push({ name: 'Login' })
}
</script>

<template>
  <div class="app-shell">
    <header>
      <div class="header-row">
        <h1>🏠 FamilyTask</h1>
        <button class="logout" v-if="authState.user" @click="doLogout">Déconnexion</button>
      </div>
      <div class="header-subtitle" v-if="authState.user">Bonjour {{ userName }}</div>
    </header>

    <main>
      <router-view />
    </main>

    <footer class="tabbar" v-if="authState.user">
      <router-link to="/tasks">Tâches</router-link>
      <router-link to="/assistant">Assistant</router-link>
      <router-link v-if="isAdmin" to="/family">Famille</router-link>
    </footer>
  </div>
</template>
