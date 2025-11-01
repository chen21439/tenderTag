import type { BosssoftCookie } from '@/typings/login'
import { AppConstants } from '@/config'
import { useCookies } from 'vue3-cookies'
import { apiLogout } from '@/api/login'
import  { useMenusStore } from '@/store'
import isInIcestark from '@ice/stark-app/lib/isInIcestark'

const { cookies } = useCookies()
const baseUrl = isInIcestark() ? '' : import.meta.env.VITE_APP_PUBLIC_URL
const loginUrl = import.meta.env.VITE_ENV === 'dev' && !isInIcestark() ? '#/login' : '/login'
// token
export const setCookie = (cookie: string) => {
  cookies.set(AppConstants.bosssoftCookieName, cookie)
};
export const getCookie = (): BosssoftCookie => {
  if(window.opener && window.opener !== window && window.opener.BOSSSOFT_COOKIE) {
    return window.opener.BOSSSOFT_COOKIE
  }else if(window.BOSSSOFT_COOKIE) {
    return window.BOSSSOFT_COOKIE
  } else {
    return cookies.get(AppConstants.bosssoftCookieName)
  }
};
export const removeCookie = () => {
  cookies.remove(AppConstants.bosssoftCookieName)
};

// 登录、退出
export const appLogin = (cookie: string) => {
  appLoginHandler(cookie)
};
// 登录后逻辑
export const appLoginHandler = async (cookie: string) => {
  setCookie(cookie)
  const cookieObj = cookie ? JSON.parse(cookie) : {}
  const menusStore = useMenusStore()
  menusStore.setAppId(cookieObj.appId)
  if(cookieObj.callbackUrl)  menusStore.setExternalLoginUrl(cookieObj.callbackUrl)
  location.href = baseUrl + '/'
}

// 退出操作
export const appLoginOut = async () => {
  const menusStore = useMenusStore()
  await apiLogout(menusStore.appId)
  appLoginOutHandler()
  const url =  `${baseUrl}${loginUrl}?appId=${menusStore.appId}`
  menusStore.setAppId('')
  if(menusStore.externalLoginUrl) {
    location.href = menusStore.externalLoginUrl
  }else {
    location.href = url
  }
}
// 退出后逻辑
export const appLoginOutHandler = () => {
  const menusStore = useMenusStore()
  removeCookie()
  menusStore.setMenu(null)
  menusStore.setDynamicRoutes([])
  menusStore.setDynamicRoutesState(false)
  menusStore.toggleSidebar(true)
}
