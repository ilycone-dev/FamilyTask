<script setup>
import { computed } from 'vue'

const props = defineProps({
  name: { type: String, default: '' },
  size: { type: Number, default: 44 },
  // 0–1, si fourni affiche un anneau de progression (ex: part de tâches faites)
  progress: { type: Number, default: null },
})

const initial = computed(() => props.name?.trim()?.[0]?.toUpperCase() || '?')

// Couleur déterministe à partir du prénom, pour que chaque membre garde
// toujours le même avatar coloré d'une session à l'autre.
const hue = computed(() => {
  let hash = 0
  for (const char of props.name || '') {
    hash = (hash * 31 + char.charCodeAt(0)) % 360
  }
  return hash
})

const ringPct = computed(() => Math.max(0, Math.min(1, props.progress ?? 0)) * 100)
</script>

<template>
  <div
    class="avatar-wrap"
    :style="{
      '--h': hue,
      width: size + 'px',
      height: size + 'px',
      '--ring-pct': ringPct,
    }"
  >
    <svg v-if="progress !== null" class="ring" viewBox="0 0 40 40">
      <circle class="ring-track" cx="20" cy="20" r="17.5" />
      <circle class="ring-fill" cx="20" cy="20" r="17.5" />
    </svg>
    <div class="avatar" :style="{ fontSize: Math.round(size * 0.4) + 'px' }">
      {{ initial }}
    </div>
  </div>
</template>

<style scoped>
.avatar-wrap {
  position: relative;
  display: grid;
  place-items: center;
  flex: none;
}
.avatar {
  width: 82%;
  height: 82%;
  border-radius: 50%;
  display: grid;
  place-items: center;
  font-family: 'Fredoka', sans-serif;
  font-weight: 600;
  color: #fff;
  background: linear-gradient(150deg, hsl(var(--h) 78% 62%), hsl(calc(var(--h) + 34) 78% 52%));
  box-shadow: 0 2px 6px rgba(20, 12, 50, 0.18);
}
.ring {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  transform: rotate(-90deg);
}
.ring-track {
  fill: none;
  stroke: var(--border);
  stroke-width: 2.5;
}
.ring-fill {
  fill: none;
  stroke: hsl(var(--h) 78% 55%);
  stroke-width: 2.5;
  stroke-linecap: round;
  stroke-dasharray: 110;
  stroke-dashoffset: calc(110 - (110 * var(--ring-pct)) / 100);
  transition: stroke-dashoffset 0.4s ease;
}
</style>
