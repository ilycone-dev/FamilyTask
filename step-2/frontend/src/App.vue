<script setup>
import { ref, onMounted } from 'vue'
import TaskList from './components/TaskList.vue'

/* -------------------------
   Vérification du backend
   ------------------------- */
const status = ref('...')
onMounted(async () => {
  try {
    const r = await fetch('/api/health')
    status.value = (await r.json()).status
  } catch (e) {
    status.value = 'back pas encore prêt'
  }
})

/* -------------------------
   Todo-list en mémoire (pas de persistance locale)
   - `tasks` initialisées avec 2 tâches d'exemple
   - pas de localStorage ici : les modifications sont temporaires
   - utile si tu veux maintenant connecter un backend pour sauvegarder
   ------------------------- */
const tasks = ref([
  { id: 1, title: 'Faire la vaisselle', done: false },
  { id: 2, title: 'Préparer le dîner', done: true }
])

const newTitle = ref('')

function addTask() {
  const title = newTitle.value && newTitle.value.trim()
  if (!title) return
  const id = Date.now()
  tasks.value.push({ id, title, done: false })
  newTitle.value = ''
}

function removeTask(id) {
  tasks.value = tasks.value.filter((task) => task.id !== id)
}

function toggleTask(id) {
  const task = tasks.value.find((task) => task.id === id)
  if (task) task.done = !task.done
}
</script>

<template>
  <header><h1>🏠 FamilyTask</h1></header>
  <main>
    <div class="card">
      <h2>Ma Todo-list</h2>

      <!-- Formulaire d'ajout : entrée + bouton -->
      <div class="add">
        <input
          v-model="newTitle"
          @keyup.enter="addTask"
          placeholder="Nouvelle tâche"
        />
        <button @click="addTask">Ajouter</button>
      </div>

      <!-- Liste des tâches importée du composant TaskList -->
      <TaskList
        :tasks="tasks"
        @toggle="toggleTask"
        @remove="removeTask"
      />

      <!-- État du backend (toujours utile) -->
      <p class="hint">Réponse du back : <strong>{{ status }}</strong></p>
    </div>
  </main>
</template>
