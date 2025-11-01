import type { RouteRecordRaw, RouteLocationNormalizedGeneric } from 'vue-router'
// import config from '@/config'
// import {  getUserBusModuleCodes, saltConvert  } from '@/api/login'
import  { useMenusStore } from '@/store'
import { dynamicRoutesMap, fallbackRoutes } from './routes'
import Layout from '@/layout/index.vue'
import ParentView from '@/layout/parent-view.vue'
import IframeView from '@/layout/iframe-view.vue'
// const currentSystemCode = config.route.currentSystemCode
// 设置系统权限
export const ensureRoutesData = async (router: any) => {
  const menusStore = useMenusStore()
  if (menusStore.dynamicRoutesState) return true
  try {
    // 获取菜单数据 - 这里需要根据实际API调整
    // const { data: menuData = [] } = await getMenuList()
    // 模拟菜单数据，实际项目中从API获取
    const mockMenuData = [
      {
        id: 'bid-examine',
        name: '合规性审查',
        icon: 'icon-shield',
        parentId: null
      },
      {
        id: 'home-index',
        name: '采购文件审查',
        route: 'HomeIndex',
        parentId: 'bid-examine'
      },
      {
        id: 'library-list',
        name: '查看审查档案库',
        route: 'LibraryIndex',
        parentId: 'bid-examine'
      },
      // {
      //   id: 'rule-manager',
      //   name: '规则管理',
      //   route: 'RuleManager',
      //   parentId: 'bid-examine'
      // }
    ]
    // 构建菜单树并设置到store
    const menuTree = menusStore.buildMenuTree(mockMenuData)
    menusStore.setDynamicMenus(menuTree)
    // 路由处理逻辑保持不变
    const routes: RouteRecordRaw[] = useDynamicsRoutes([])
    routes.push(fallbackRoutes[0])
    routes.forEach((item: any) => {
      if (!router.hasRoute(item?.name)) {
        router.addRoute(item)
      }
    })
    menusStore.setDynamicRoutes(routes)
    menusStore.setDynamicRoutesState(true)
    return true
  } catch (e) {
    console.error('菜单数据加载失败:', e)
    return false
  }
}
// 格式化菜单数据
const useDynamicsRoutes = (routes: any[]) => {
  return resolveRoutes(routes)

  // 解析系统菜单
  function resolveRoutes(routesList: any[]) {
    const res: any = []
    resolveRouteChildren(null, routesList)
    function resolveRouteChildren(parent: any, children?: any[]) {
      if (!children?.length) return
      // isValidRoute 逻辑用于去掉多级中没有子路由的二级菜单
      children.forEach((o: any) => {
        const { isValidRoute, ...item } = resolveRouteItem(o) || {}
        if (!isValidRoute) return
        if (parent) {
          if (!parent.children) parent.children = []
          parent.children.push(item)
          parent.isValidRoute = true
        } else {
          res.push(item)
        }
      });

    }
    function resolveRouteItem(route: any) {
      const { children, component, ...obj } = route
      // 用户权限里没有该路由，则不addRoute-暂时无
      const authCode = obj.meta?.authCode
      if (authCode) return null
      const item = { ...obj }
      if (component) item.component = resolveRouteComponent(component)
      if (component && !children?.length) {
        item.isValidRoute = true
      }
      resolveRouteChildren(item, children)
      return item
    }

    return res
  }

  function resolveRouteComponent(component?: any) {
    if (!component || typeof component !== 'string') return component
    if (component === 'Layout') {
      return Layout
    } else if (component === 'ParentView') {// 多级嵌套路由目录
      return ParentView
    } else if (component === 'IframeView') {// iframe
      return IframeView
    } else {
      return loadView(component)
    }
  }
}
// 匹配views里面所有的.vue文件
const modules = import.meta.glob('@/views/**/*.vue');
// const regComponentPath = /^\/src\/views\/(.+)\.vue$/g;
const loadView = (view: string) => {
  const res = modules[`/src/views/${view}.vue`] || null;
  return res;
}







