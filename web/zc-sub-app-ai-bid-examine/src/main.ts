// Promise.withResolvers polyfill for old browsers (like QQ Browser)
if (!Promise.withResolvers) {
  Promise.withResolvers = function () {
    let resolve, reject
    const promise = new Promise((res, rej) => {
      resolve = res
      reject = rej
    })
    return { promise, resolve, reject }
  }
}

import type { App as Root } from 'vue'
import '@/assets/css/theme/index.scss';
import '@/assets/css/base/index.scss';
import Vue3Lottie from 'vue3-lottie'
import VueTyped from 'vue3typed'
import VueCookies from 'vue3-cookies'
import AntDesignVue, { message } from 'ant-design-vue'
import isInIcestark from '@ice/stark-app/lib/isInIcestark'
import App from './App.vue'
import GlobalComponents from '@/components/global'
import 'virtual:svg-icons-register'
import '@/assets/font/iconfont.js'
import '@/plugins'
import { naiveStyleOverride } from '@/plugins'
import { createApp } from 'vue'
import {setupStore} from './store'
import {setupRouter} from './router'
import { store } from '@ice/stark-data'
import { setCookie } from '@/utils/app-gateway'
import  { useMenusStore } from '@/store'
let app : Root<Element> | null = null
async function bootstrap(container: any) {
  app = createApp(App)
  naiveStyleOverride()
  app.use(VueTyped)
  app.use(Vue3Lottie, {name: 'Vue3Lottie'})
  app.use(GlobalComponents)
  app.use(VueCookies)
  app.use(AntDesignVue)
  app.provide('message', message)
  setupStore(app)
  setupRouter(app)
  app.mount(container)
}

if (!isInIcestark()) bootstrap('#app-bid-examine')
export async function mount({ container }: { container: Element }) {
  console.log('mount')
  bootstrap(container)
  const bosssoftCookie = store.get('bosssoftCookie')
  setCookie(bosssoftCookie)
}

export function unmount() {
  const menusStore = useMenusStore()
  menusStore.setDynamicRoutesState(false)
  app?.unmount()
  app =  null
}
