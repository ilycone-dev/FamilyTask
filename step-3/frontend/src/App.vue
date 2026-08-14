<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { authState, logout } from './auth.js'
import Avatar from './components/Avatar.vue'

const router = useRouter()
const isAdmin = computed(() => authState.user?.is_admin)
const userName = computed(() => authState.user?.name || '')

const theme = ref('system')

function applyTheme(value) {
  if (value === 'system') {
    document.documentElement.removeAttribute('data-theme')
  } else {
    document.documentElement.setAttribute('data-theme', value)
  }
}

function toggleTheme() {
  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
  const current = theme.value === 'system' ? (prefersDark ? 'dark' : 'light') : theme.value
  theme.value = current === 'dark' ? 'light' : 'dark'
  localStorage.setItem('familytask-theme', theme.value)
  applyTheme(theme.value)
}

onMounted(() => {
  const saved = localStorage.getItem('familytask-theme')
  theme.value = saved || 'system'
  applyTheme(theme.value)
})

const isDark = computed(() => {
  if (theme.value === 'dark') return true
  if (theme.value === 'light') return false
  return typeof window !== 'undefined' && window.matchMedia('(prefers-color-scheme: dark)').matches
})

function doLogout() {
  logout()
  router.push({ name: 'Login' })
}
</script>

<template>
  <div class="viewport">
    <div class="phone-frame">
      <header class="topbar" v-if="authState.user">
        <div class="topbar-left">
          <Avatar :name="userName" :size="38" />
          <div>
            <h1>FamilyTask</h1>
            <p class="topbar-subtitle">Bonjour {{ userName }}</p>
          </div>
        </div>
        <div class="topbar-actions">
          <button class="icon-btn" type="button" @click="toggleTheme" :title="isDark ? 'Mode clair' : 'Mode sombre'">
            <svg v-if="isDark" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="4" /><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" /></svg>
            <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79Z" /></svg>
          </button>
          <button class="icon-btn" type="button" @click="doLogout" title="Déconnexion">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" /><path d="M16 17l5-5-5-5" /><path d="M21 12H9" /></svg>
          </button>
        </div>
      </header>
      <header class="topbar" v-else>
        <div class="topbar-left">
          <h1>FamilyTask</h1>
        </div>
      </header>

      <main>
        <router-view />
      </main>

      <footer class="tabbar" v-if="authState.user">
        <router-link to="/tasks">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="5" width="6" height="6" rx="1.5" /><path d="M12 8h9" /><rect x="3" y="15" width="6" height="6" rx="1.5" /><path d="M12 18h9" /></svg>
          <span>Tâches</span>
        </router-link>
        <router-link to="/assistant">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 11.5a8.4 8.4 0 0 1-9 8.4A8.4 8.4 0 0 1 3.6 12 8.4 8.4 0 0 1 12 3.6a8.4 8.4 0 0 1 8.4 8.4Z" /><path d="M8 12h.01M12 12h.01M16 12h.01" /></svg>
          <span>Assistant</span>
        </router-link>
        <router-link v-if="isAdmin" to="/family">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" /><circle cx="9" cy="7" r="4" /><path d="M23 21v-2a4 4 0 0 0-3-3.87" /><path d="M16 3.13a4 4 0 0 1 0 7.75" /></svg>
          <span>Famille</span>
        </router-link>
      </footer>
    </div>
  </div>
</template>
