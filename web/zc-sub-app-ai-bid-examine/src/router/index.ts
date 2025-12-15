import type { App } from 'vue'
import type { Router } from 'vue-router'
import { createRouter ,createWebHistory, createWebHashHistory } from 'vue-router'
import { setupPageGuard } from './permission'
import isInIcestark from '@ice/stark-app/lib/isInIcestark'
import getBasename from '@ice/stark-app/lib/getBasename'


export const genRoute = (): Router => {
  const baseUrl = isInIcestark() ? getBasename() : import.meta.env.VITE_APP_PUBLIC_URL
  // dev 和 test 环境都使用 hash 模式，避免 Nginx 配置问题
  const routerHistory = (import.meta.env.VITE_ENV === 'dev' || import.meta.env.VITE_ENV === 'test') && !isInIcestark()
    ? createWebHashHistory(baseUrl)
    : createWebHistory(baseUrl)
  return createRouter({
    history: routerHistory,
    routes: [],
    scrollBehavior: () => ({ left: 0, top: 0 })
  })
}

export async function setupRouter(app: App) {
  const router = genRoute()

  // 动态注入"文件审查"主页面，保证左侧菜单的跳转可用
  router.addRoute({
    path: '/compliance-review',
    name: 'ComplianceReview',
    meta: { title: '文件审查' },
    component: () => import('@/views/compliance-review/index.vue')
  })

  // 审查结果页面（简化版）
  router.addRoute({
    path: '/review',
    name: 'Review',
    meta: { title: '审查结果' },
    component: () => import('@/views/review/index.vue')
  })

  // 知识图谱配置页面
  router.addRoute({
    path: '/knowledge-graph-config',
    name: 'KnowledgeGraphConfig',
    meta: { title: '知识图谱配置' },
    component: () => import('@/views/knowledge-graph-config/index.vue')
  })

  // 兼容 PPT 演示页，不参与兜底重定向
  router.addRoute({
    path: '/ppt/ai',
    name: 'PptAI',
    meta: { title: 'PPT 演示' },
    component: () => import('@/views/ppt/AI.vue')
  })

  // 首页 Home
  router.addRoute({
    path: '/home',
    name: 'HomeIndex',
    meta: { title: '采购文件审查' },
    component: () => import('@/views/home/index.vue')
  })
  // 根路径重定向到首页
  router.addRoute({
    path: '/',
    redirect: '/home'
  })

  // 兜底 404 重定向，避免未知路径白屏
  router.addRoute({
    path: '/:pathMatch(.*)*',
    redirect: '/home'
  })

  setupPageGuard(router)
  app.use(router)
  await router.isReady()
}