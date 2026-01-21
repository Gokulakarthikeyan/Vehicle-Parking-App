import { createRouter, createWebHistory } from 'vue-router'

import LoginPage from '../views/Login-Page.vue'
import RegisterPage from '../views/Register-Page.vue'

import AdminDashboard from '../views/Admin/Admin-Dashboard.vue'
import AdminViewuser from '../views/Admin/Admin-View-User.vue'
import AdminSearch from '../views/Admin/Admin-Search.vue'
import AdminSummary from '../views/Admin/Admin-Summary.vue'

import UserDashboard from '../views/User/User-Dashboard.vue'
import UserBookparking from '../views/User/User-Book-Parking.vue'
import UserSummary from '../views/User/User-Summary.vue'

const routes = [
  { path: '/', redirect: '/login' },
  { path: '/login', component: LoginPage },
  { path: '/register', component: RegisterPage },

  // ADMIN ROUTES
  { path: '/admin/dashboard', component: AdminDashboard, meta: { requiresAuth: true, role: 'admin' }},
  { path: '/admin/view-user', component: AdminViewuser, meta: { requiresAuth: true, role: 'admin' }},
  { path: '/admin/search', component: AdminSearch, meta: { requiresAuth: true, role: 'admin' }},
  { path: '/admin/summary', component: AdminSummary, meta: {requiresAuth: true, role: 'admin'}},

  // USER ROUTES
  { path: '/user/dashboard', component: UserDashboard, meta: { requiresAuth: true, role: 'user' }},
  { path: '/user/parking', component: UserBookparking, meta: { requiresAuth: true, role: 'user' }},
  { path: '/user/summary', component: UserSummary, meta: { requiresAuth: true, role: 'user' }},
  { path: "/payment", name: "DummyPayment", component: () => import("../views/User/DummyPayment.vue")},

]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, from, next) => {
  const username = localStorage.getItem('username')
  const role = localStorage.getItem('role')

  const isAuthenticated = !!username

  // If route requires login
  if (to.meta.requiresAuth && !isAuthenticated) {
    return next('/login')
  }

  // If route requires specific role
  if (to.meta.role && role !== to.meta.role) {
    return next('/login')
  }

  next()
})

export default router
