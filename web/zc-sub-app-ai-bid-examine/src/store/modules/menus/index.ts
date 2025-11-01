
import { defineStore } from 'pinia'
import type { RouteRecordRaw } from 'vue-router'
import config, { LOCALSTORAGE_SIDEBARSTATUS,LOCALSTORAGE_EXTERNALLOGINURL, LOCALSTORAGE_APPID } from '@/config'
import isInIcestark from '@ice/stark-app/lib/isInIcestark'
import StorageService from '@/utils/storage'
interface MenuItem {
  key: string
  title: string
  icon?: string
  route?: string
  children?: MenuItem[]
  type?: 'group' | 'menu'
  authCode?: string
}
export const useMenusStore = defineStore('menus-store', {
  state: () => {
    return {
      systemInfo: {} as Record<string,any>,
      externalLoginUrl: StorageService.getLocal(LOCALSTORAGE_EXTERNALLOGINURL, '') as string,// 外部异常登录地址
      menus: null as null | MenuItem[],// 左侧菜单
      dynamicRoutes: [] as RouteRecordRaw[], // 动态路由数据
      dynamicRoutesState: false, // 是否加载了动态路由
      sidebar: {
        collapsed: StorageService.getLocal(LOCALSTORAGE_SIDEBARSTATUS, true)
      },
      appId: StorageService.getLocal(LOCALSTORAGE_APPID, null),
      dynamicMenus: [] as MenuItem[] // 动态菜单数据
    };
  },
  getters: {
    menusCode: (state: any) => {
      return state.menus?.map((x:MenuItem)=>x.code) ?? []
    },
    defaultMenus: (state: any) => {
      return state.menus?.[0] ?? {}
    },
    themeKey: (state: any) => {
      // return state.isTianda ? 'tianda' :'default'
      return 'default'
    }
  },
  actions: {
    setExternalLoginUrl(url: string) {
      this.externalLoginUrl =  url
      StorageService.setLocal(LOCALSTORAGE_EXTERNALLOGINURL, url)
    },
    setSystemInfo(obj: Record<string,any>) {
      this.systemInfo = obj ?? {}
    },
    setMenu(menus: null | MenuItem[]) {
      this.menus =  menus
    },
    setAppId(val: any) {
      this.appId =  val
      StorageService.setLocal(LOCALSTORAGE_APPID, val)
    },
    setDynamicRoutes(routes: RouteRecordRaw[] = []) {
      this.dynamicRoutes = routes
    },
    setDynamicRoutesState(state?: boolean) {
      this.dynamicRoutesState = !!state
    },
    toggleSidebar(val: boolean) {
      this.sidebar.collapsed = val
      StorageService.setLocal(LOCALSTORAGE_SIDEBARSTATUS, val)
    },
    setDynamicMenus(menus: MenuItem[]) {
      this.dynamicMenus = menus
    },
    buildMenuTree(flatMenus: any[]): MenuItem[] {
      const menuMap = new Map()
      const rootMenus: MenuItem[] = []
      
      // 先创建所有菜单项的映射
      flatMenus.forEach(menu => {
        menuMap.set(menu.id, {
          key: menu.id,
          title: menu.name,
          icon: menu.icon,
          route: menu.route,
          type: menu.type || 'menu',
          authCode: menu.authCode,
          children: []
        })
      })
      
      // 构建树形结构
      flatMenus.forEach(menu => {
        const menuItem = menuMap.get(menu.id)
        if (menu.parentId && menuMap.has(menu.parentId)) {
          const parent = menuMap.get(menu.parentId)
          parent.children.push(menuItem)
        } else {
          rootMenus.push(menuItem)
        }
      })
      
      // 清理空的children数组
      const cleanEmptyChildren = (items: MenuItem[]) => {
        items.forEach(item => {
          if (item.children && item.children.length === 0) {
            delete item.children
          } else if (item.children && item.children.length > 0) {
            cleanEmptyChildren(item.children)
          }
        })
      }
      
      cleanEmptyChildren(rootMenus)
      return rootMenus
    }
  }
})

