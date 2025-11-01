import type { Router } from 'vue-router'
import type {  BosssoftCookie } from '@/typings/login'
import config  from '@/config'
import { apiRefreshToken, saltConvert } from '@/api/login'
import  { useMenusStore } from '@/store'
import { getCookie, appLoginHandler, appLoginOutHandler } from '@/utils/app-gateway'
import { ensureRoutesData  } from '@/router/tools'
// 路由白名单
const whiteList = config.route.whiteList
// 开发/测试环境额外白名单（不需要登录）
const devWhiteList = (config.isDev || config.isTest) ? ['/compliance-review', '/', '/home', '/compliance-web', '/compliance-web/'] : []

console.log('🛡️ 路由守卫初始化:', {
  isDev: config.isDev,
  isTest: config.isTest,
  whiteList,
  devWhiteList
})

export function setupPageGuard(router: Router) {
  //前置守卫
  router.beforeEach(async (to, from, next) => {
    console.log('🚦 路由守卫检查:', {
      to: to.path,
      from: from.path,
      isDev: config.isDev,
      isTest: config.isTest
    })

    // 内嵌页不拦截
    if(config.route.robotList.includes(to.name)) {
      console.log('✅ 内嵌页，直接放行')
      next()
      return
    }
    const menusStore = useMenusStore()
    // appid
    const urlAppId = to.query?.appId
    //
    const bosssoftCookie = getCookie()
    console.log('🍪 Cookie 检查:', bosssoftCookie ? '有 Cookie' : '无 Cookie')
    if (bosssoftCookie) {
      // 开发/测试环境：跳过token刷新，直接放行
      if (config.isDev || config.isTest) {
        console.log('✅ 开发/测试模式：跳过 apiRefreshToken 调用，直接放行')
        next()
        return
      }

      console.log('🔑 生产模式：调用 apiRefreshToken')
      // 已登录: 用户信息
      const apiData = await apiRefreshToken()
      if (apiData)  {
        console.log('✅ Token 刷新成功')
        let isRouteTouched = false
        if (!menusStore.dynamicRoutesState) {
          // 动态注册路由
          await ensureRoutesData(router)
          isRouteTouched = true
        }
        let _toRoute: any = undefined
        if (isRouteTouched) {
          _toRoute = { ...to, replace: true }
        }
        // 已登录： 访问登录页面，重定向到首页
        if (from.path === '/') {
          next()
          return
        }else if (to.path === '/login') {
          _toRoute = { name: 'Home', replace: true }
        }
        next(_toRoute)
      }else {
        console.log('❌ Token 刷新失败，跳转登录')
        next({path: '/login',query: {appId: menusStore.appId}})
      }
      //
    } else {
      console.log('📝 无 Cookie，检查白名单')
      // 登录url有Appid更新
      menusStore.setAppId('')
      if(to.path === '/login' && urlAppId) menusStore.setAppId(urlAppId)

       // 开发/测试环境：无 Cookie 时也直接放行
       if (config.isDev || config.isTest) {
         console.log('✅ 开发/测试模式：无 Cookie 也直接放行')
         next()
         return
       }

       // 未登录
       const inWhiteList = whiteList.includes(to.path)
       const inDevWhiteList = devWhiteList.includes(to.path)
       console.log('白名单检查:', {
         path: to.path,
         inWhiteList,
         inDevWhiteList,
         whiteList,
         devWhiteList
       })
       if (inWhiteList || inDevWhiteList) {
        console.log('✅ 在白名单中，直接放行')
        next()
       } else {
        console.log('❌ 不在白名单中，跳转登录')
        next({path: '/login',query: {appId: menusStore.appId}})
       }
    }
  })
}
