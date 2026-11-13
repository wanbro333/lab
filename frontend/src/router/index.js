import { createRouter, createWebHistory } from 'vue-router'
import { auth, ensureSession } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'home',
      component: () => import('@/views/HomeView.vue'),
      meta: { title: '工作台' },
    },
    {
      path: '/inventory',
      name: 'inventory',
      component: () => import('@/views/InventoryView.vue'),
      meta: { title: '器材与材料', requiresAuth: true },
    },
    {
      path: '/procurement',
      component: () => import('@/views/ModuleView.vue'),
      meta: { title: '采购管理', module: 'procurement' },
    },
    {
      path: '/receipts',
      component: () => import('@/views/ModuleView.vue'),
      meta: { title: '收货入库', module: 'receipts' },
    },
    {
      path: '/assistant',
      component: () => import('@/views/ModuleView.vue'),
      meta: { title: '智能问答', module: 'assistant' },
    },
    {
      path: '/profile',
      component: () => import('@/views/ProfileView.vue'),
      meta: { title: '个人中心', requiresAuth: true },
    },
    { path: '/login', component: () => import('@/views/LoginView.vue'), meta: { title: '登录' } },
    {
      path: '/:pathMatch(.*)*',
      component: () => import('@/views/NotFoundView.vue'),
      meta: { title: '页面不存在' },
    },
  ],
  scrollBehavior: () => ({ top: 0 }),
})

router.beforeEach(async (to) => {
  document.title = `${to.meta.title} · 实验室工作台`
  try {
    await ensureSession()
  } catch {
    /* Pages show a recoverable connection error. */
  }
  if (to.meta.requiresAuth && !auth.user)
    return { path: '/login', query: { redirect: to.fullPath } }
})
export default router
