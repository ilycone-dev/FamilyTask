import { reactive } from 'vue'

const authState = reactive({
  token: localStorage.getItem('token'),
  user: null,
})

function saveToken(token) {
  authState.token = token
  localStorage.setItem('token', token)
}

function clearAuth() {
  authState.token = null
  authState.user = null
  localStorage.removeItem('token')
}

async function fetchUser() {
  if (!authState.token) return
  const res = await fetch('/api/me', {
    headers: { Authorization: `Bearer ${authState.token}` },
  })
  if (!res.ok) {
    clearAuth()
    return
  }
  authState.user = await res.json()
}

function getAuthHeaders() {
  return authState.token ? { Authorization: `Bearer ${authState.token}` } : {}
}

function logout() {
  clearAuth()
}

export { authState, saveToken, fetchUser, getAuthHeaders, logout }
