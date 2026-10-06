import { createRouter, createWebHistory } from 'vue-router'
import { getToken } from '@/utils/auth'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {path: '/', redirect: '/manager/home'},
    {path: '/manager', name: 'Layout', component: () => import('@/layout/Layout.vue'),
      children: [
        {path: 'home', name: 'Home', component: () => import('@/views/Home.vue')},
        {path: 'pet', name: 'Pet', component: () => import('@/views/Pet.vue')},
        {path: 'category', name: 'Category', component: () => import('@/views/Category.vue')},
        {path: 'user', name: 'User', component: () => import('@/views/User.vue')},
        {path: 'profile', name: ' Profile', component: () => import('@/views/Profile.vue')},
        {path: 'password', name: 'Password', component: () => import('@/views/Password.vue')},
        {path: 'ai', name: 'AI', component: () => import('@/views/AI.vue')}
      ]
    },
    {path: '/login', name: 'Login', component: () => import('@/views/Login.vue')},
    {path: '/register', name: 'Register', component: () => import('@/views/Register.vue')},
  ],
})

// 路由守卫：验证token
// 路由守卫：验证token
router.beforeEach((to, from) => {
  const token = getToken()
  
  // 如果要访问的是登录或注册页
  if (to.path === '/login' || to.path === '/register') {
    // 如果已经登录了，直接踢到首页，不要再留在登录页
    if (token) return '/manager/home' 
    return true
  }
  // 如果要访问其他页面，必须有 token，否则打回登录页
  return token ? true : '/login'
})

export default router
