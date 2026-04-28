import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '../views/Dashboard.vue'
import GradingList from '../views/grading/GradingList.vue'

const routes = [
  {
    path: '/',
    name: 'Dashboard',
    component: Dashboard
  },
  {
    path: '/grading/:assignmentId',
    name: 'GradingList',
    component: GradingList
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router   // ✅ 这一行是关键，必须存在！