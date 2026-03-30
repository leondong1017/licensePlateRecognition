import { createRouter, createWebHistory } from 'vue-router'

// Lazy imports to avoid circular deps before views exist
const RecognizePage = () => import('../views/RecognizePage.vue')
const HistoryPage = () => import('../views/HistoryPage.vue')

export default createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: RecognizePage },
    { path: '/history', component: HistoryPage },
  ],
})
