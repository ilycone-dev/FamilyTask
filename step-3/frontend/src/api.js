// Adresse du backend.
//
// En local (sans Docker), VITE_API_URL n'est pas défini : on retombe sur
// une chaîne vide, donc les appels comme fetch(apiUrl('/api/tasks'))
// deviennent simplement '/api/tasks' — des chemins relatifs, qui passent
// par le proxy de Vite ou par le même serveur que le frontend.
//
// En production (ex: Render, où le front et le back sont deux services
// séparés avec des adresses différentes), on définit VITE_API_URL à
// l'URL complète du backend, ex: https://familytask-backend.onrender.com
export const API_URL = import.meta.env.VITE_API_URL || ''

export function apiUrl(path) {
  return `${API_URL}${path}`
}
