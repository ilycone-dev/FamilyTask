import { createRouter, createWebHistory } from 'vue-router'
import LoginView from './views/LoginView.vue'
import SignupView from './views/SignupView.vue'
import TasksView from './views/TasksView.vue'
import FamilyView from './views/FamilyView.vue'
import AssistantView from './views/AssistantView.vue'
import { authState, fetchUser } from './auth.js'

const routes = [
  { path: '/login', name: 'Login', component: LoginView },
  { path: '/signup', name: 'Signup', component: SignupView },
  { path: '/tasks', name: 'Tasks', component: TasksView, meta: { requiresAuth: true } },
  { path: '/assistant', name: 'Assistant', component: AssistantView, meta: { requiresAuth: true } },
  { path: '/family', name: 'Family', component: FamilyView, meta: { requiresAuth: true, adminOnly: true } },
  { path: '/:pathMatch(.*)*', redirect: '/tasks' },
]

const router = createRouter({ history: createWebHistory(), routes })

router.beforeEach(async (to, from, next) => {
  if (authState.token && !authState.user) {
    await fetchUser()
  }
  const requiresAuth = to.meta.requiresAuth
  if (requiresAuth && !authState.token) {
    return next({ name: 'Login' })
  }
  if (to.name === 'Login' || to.name === 'Signup') {
    if (authState.token) return next({ name: 'Tasks' })
    return next()
  }
  if (to.meta.adminOnly && authState.user && !authState.user.is_admin) {
    return next({ name: 'Tasks' })
  }
  return next()
})

export default router
