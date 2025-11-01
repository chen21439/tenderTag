import type { RouteRecordRaw } from 'vue-router'
import Layout from '@/layout/index.vue'
import config from '@/config'
export const dynamicRoutesMap: Record<string,any> = {
  AI_Chat: []
}
// 咨询路由
const aiNormalRoutes : RouteRecordRaw[] = [
  {
    path: '/',
    name: 'Home',
    component: Layout,
    children: [
      {
        path: '',
        name: 'ComplianceReview',
        meta: {
          title: '合规性审查'
        },
        component: () => import('@/views/compliance-review/index.vue')
      },
      {
        path: '/home',
        name: 'HomeIndex',
        meta: {
          title: '首页'
        },
        component: () => import('@/views/home/index.vue')
      },
      {
        name: 'LibraryIndex',
        path: '/library',
        component: () => import('@/views/library/index.vue')
      },
      {
        name: 'ResultIndex',
        path: '/result',
        meta: {
          title: '审查结果-旧'
        },
        component: () => import('@/views/library/result.vue')
      },
      {
        name: 'ExamineItem',
        path: '/examine-item',
        meta: {
          title: '设置审查点-旧'
        },
        component: () => import('@/views/examine-item/index.vue')
      },
      {
        name: 'RuleManager',
        path: '/rule-manager',
        meta: {
          title: '规则管理'
        },
        component: () => import('@/views/rule-manager/index.vue')
      }
    ]
  }
]
const demoRoutes: RouteRecordRaw[] = [
  // 专门放测试的
  {
    path: '/demo',
    name: 'demo',
    component: Layout,
    children: [
      {
        path: 'test',
        name: 'TestIndex',
        meta: {
          title: '测试'
        },
        component: () => import('@/views/demo/test/index.vue')
      },
      {
        path: 'reader',
        name: 'CustumerIndex',
        meta: {
          title: '自定义阅读器'
        },
        component: () => import('@/views/demo/test/reader.vue')
      }
    ]
  }
]
// 通用路由
const commonRoutes: RouteRecordRaw[] = [
  {
    name: 'login',
    path: '/login',
    component: () => import('@/views/login/index.vue')
  },
  {
    path: '/agreement',
    name: 'Agreement',
    component: () => import('@/views/agreement/index.vue')
  },

  {
    path: '/404',
    name: '404',
    component: () => import('@/views/exception/404/index.vue')
  },
  {
    path: '/500',
    name: '500',
    component: () => import('@/views/exception/500/index.vue')
  }
]
// 开发环境路由
const devRoutes = config.env.VITE_ENV === 'dev' ? [...aiNormalRoutes,...demoRoutes]: [...aiNormalRoutes]
export const routes: RouteRecordRaw[] = [
  ...devRoutes,
  ...commonRoutes
]
export const fallbackRoutes = [
  {
    path: '/:pathMatch(.*)*',
    name: 'notFound',
    redirect: '/404'
  }
]
