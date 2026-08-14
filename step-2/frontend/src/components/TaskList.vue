<script setup>
import { defineProps, defineEmits } from 'vue'

const props = defineProps({
  tasks: {
    type: Array,
    required: true
  }
})

const emit = defineEmits(['toggle', 'remove'])

function onToggle(task) {
  emit('toggle', task.id)
}

function onRemove(task) {
  emit('remove', task.id)
}
</script>

<template>
  <ul class="tasks">
    <li v-for="task in tasks" :key="task.id">
      <label>
        <input type="checkbox" :checked="task.done" @change="onToggle(task)" />
        <span :class="{ done: task.done }" :style="{ textDecoration: task.done ? 'line-through' : 'none' }">{{ task.title }}</span>
      </label>
      <button class="delete" @click="onRemove(task)">🗑</button>
    </li>
  </ul>
  <p v-if="tasks.length === 0" class="empty-state">Ta liste est vide, ajoute ta première tâche ! ✨</p>
</template>
