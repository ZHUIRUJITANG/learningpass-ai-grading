import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import Dashboard from '../views/Dashboard.vue'
import GradingList from '../views/grading/GradingList.vue'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'Dashboard',
    component: Dashboard,
  },
  {
    path: '/courses',
    name: 'Courses',
    component: () => import('@/views/courses/CourseList.vue'),
  },
  {
    path: '/assignments',
    name: 'Assignments',
    component: () => import('@/views/assignments/AssignmentList.vue'),
  },
  {
    path: '/grading/:assignmentId',
    name: 'GradingList',
    component: GradingList,
  },
  {
    path: '/assignments/submit',
    name: 'SubmitAssignment',
    component: () => import('@/views/assignments/AssignmentSubmit.vue'),
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
