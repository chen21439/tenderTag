import type { App } from 'vue'
import type { Router } from 'vue-router'
import { createRouter ,createWebHistory, createWebHashHistory } from 'vue-router'
import { setupPageGuard } from './permission'
import isInIcestark from '@ice/stark-app/lib/isInIcestark'
import getBasename from '@ice/stark-app/lib/getBasename'
import { routes } from './routes'

export const genRoute = (): Router => {
  const baseUrl = isInIcestark() ? getBasename() : import.meta.env.VITE_APP_PUBLIC_URL
  // dev 和 test 环境都使用 hash 模式，避免 Nginx 配置问题
  const routerHistory = (import.meta.env.VITE_ENV === 'dev' || import.meta.env.VITE_ENV === 'test') && !isInIcestark()
    ? createWebHashHistory(baseUrl)
    : createWebHistory(baseUrl)
  return createRouter({
    history: routerHistory,
    routes,
    scrollBehavior: () => ({left: 0, top: 0})
  })
}

export async function setupRouter(app: App) {
  const router = genRoute()
  setupPageGuard(router)
  app.use(router)
  await router.isReady()
}