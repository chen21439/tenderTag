<template>
  <a-flex vertical class="com-app-menu" :class="!isCollapse ? '' : 'is-collapse'">
    <a-tooltip placement="right" :title="isCollapse ? '展开' : '收起'">
      <div
:class="isCollapse ? 'btn-toggle btn-toggle-expand' : 'btn-toggle btn-toggle-collapse'"
           @click.stop="toggleCollapsed">
      </div>
    </a-tooltip>

    <a-flex class="app">
      <img :src="loadThemeImg('logo.png')" alt="logo" width="32" height="32"/>
      <span class="title">{{ systemInfo.htmlTitle }}</span>
    </a-flex>
    <a-menu
      v-model:selected-keys="menuState.selectedKeys"
      v-model:open-keys="menuState.openKeys"
      class="menu layout-aside-menu"
      mode="inline"
      :inline-collapsed="isCollapse"
      @click="handleMenuClick"
    >
      <template v-for="item in dynamicMenus" :key="item.key">
        <menu-item-component
          :item="item"
          :is-collapse="isCollapse"
          @menu-click="handleMenuItemClick"
        />
      </template>
    </a-menu>
    <LayoutUser :user-visible="isCollapse" />
  </a-flex>
</template>
<script setup lang="ts">
import { computed, ref, reactive, onMounted, watch } from 'vue'
import { useMenusStore } from '@/store'
import { useRoute, useRouter } from 'vue-router'
import { loadThemeImg } from '@/hooks/use-theme'
import LayoutUser from '@/layout/layout-user.vue'
import MenuItemComponent from './components/menu-item.vue'

// 菜单项接口定义
interface MenuItem {
  key: string
  title: string
  icon?: string
  route?: string
  children?: MenuItem[]
  type?: 'group' | 'menu'
}

// 菜单状态管理
interface MenuState {
  selectedKeys: string[]
  openKeys: string[]
}

const route = useRoute()
const router = useRouter()
const menusStore = useMenusStore()

// 响应式数据
const isCollapse = ref(menusStore.sidebar.collapsed)
const menuState = reactive<MenuState>({
  selectedKeys: [],
  openKeys: []
})

// 计算属性
const dynamicMenus = computed(() => menusStore.dynamicMenus || [])
const systemInfo = computed(() => menusStore.systemInfo)

// 菜单工具函数
const useMenuUtils = () => {
  /**
   * 递归查找菜单项的所有父级路径
   */
  const findMenuParents = (menus: MenuItem[], targetRoute: string, parents: string[] = []): string[] => {
    for (const menu of menus) {
      const currentPath = [...parents, menu.key]

      if (menu.route === targetRoute) {
        return parents
      }

      if (menu.children && menu.children.length > 0) {
        const found = findMenuParents(menu.children, targetRoute, currentPath)
        if (found.length > 0) {
          return found
        }
      }
    }
    return []
  }

  /**
   * 递归获取所有有子菜单的菜单项key
   */
  const getAllMenuKeys = (menus: MenuItem[]): string[] => {
    const keys: string[] = []
    for (const menu of menus) {
      if (menu.children && menu.children.length > 0) {
        keys.push(menu.key)
        keys.push(...getAllMenuKeys(menu.children))
      }
    }
    return keys
  }

  /**
   * 更新菜单选中和展开状态
   */
  const updateMenuState = (routeName: string) => {
    if (!routeName || !dynamicMenus.value.length) return

    // 更新选中状态
    menuState.selectedKeys = [routeName]

    // 根据收缩状态决定是否展开菜单
    if (!isCollapse.value) {
      // 展开状态：获取所有菜单key，全部展开
      const allMenuKeys = getAllMenuKeys(dynamicMenus.value)
      menuState.openKeys = [...allMenuKeys]
    } else {
      // 收缩状态：不展开任何菜单
      menuState.openKeys = []
    }
  }

  /**
   * 初始化菜单状态
   */
  const initializeMenuState = () => {
    const currentRouteName = route.name as string
    if (currentRouteName) {
      updateMenuState(currentRouteName)
    }
  }

  return {
    findMenuParents,
    getAllMenuKeys,
    updateMenuState,
    initializeMenuState
  }
}

const { getAllMenuKeys, updateMenuState, initializeMenuState } = useMenuUtils()

// 事件处理函数
const handleMenuClick = ({ key }: { key: string }) => {
  menuState.selectedKeys = [key]
}

const handleMenuItemClick = (routeName: string) => {
  if (routeName) {
    router.push({ name: routeName })
  }
}

const toggleCollapsed = () => {
  isCollapse.value = !isCollapse.value
  menusStore.toggleSidebar(isCollapse.value)

  // 切换收缩状态后，重新更新菜单状态
  const currentRouteName = route.name as string
  if (currentRouteName) {
    updateMenuState(currentRouteName)
  }
}

// 监听器设置
const setupWatchers = () => {
  // 监听路由变化
  watch(
    () => route.name,
    (newRouteName) => {
      if (newRouteName) {
        updateMenuState(newRouteName as string)
      }
    },
    { immediate: false }
  )

  // 监听菜单数据变化
  watch(
    dynamicMenus,
    (newMenus) => {
      if (newMenus.length > 0) {
        console.log('菜单数据已加载，重新初始化菜单状态')
        initializeMenuState()
      }
    },
    { immediate: false }
  )
}

// 组件初始化
const initialize = () => {
  // 设置监听器
  setupWatchers()

  // 如果菜单数据已存在，立即初始化
  if (dynamicMenus.value.length > 0) {
    initializeMenuState()
  }
}

// 生命周期
onMounted(() => {
  initialize()
})
</script>

<style scoped lang="scss">
.com-app-menu {
  position: sticky;
  top: 0;
  flex-shrink: 0;
  // width: 256px;
  min-width: 256px;
  padding: 24px 16px;
  gap: 32px;
  background: var(--fill-0);
  border-right:1px solid #E5E6EB;
  height: 100vh;
  z-index: 1;
  &.is-collapse {
    width: 80px;
    min-width: 80px;

    .app {

      .title {
        display: none;
      }
    }
  }
  .svg-logo {
    flex-shrink: 0;
    width: 40px;
    height: 40px;
  }
  .btn-toggle {
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    position: absolute;
    right: 0;
    top: 50%;
    width: 16px;
    height: 32px;
    margin-top: -16px;
    &::before {
      content: '';
      width: 4px;
      height: 20px;
      border-radius: var(--border-radius-2);
      background-color:  var(--theme-bg-3);
    }

  }

  .btn-toggle-expand:hover {
    background: var(--menu-expand) 100% no-repeat;
    &::before{
      display: none;
    }
  }

  .btn-toggle-collapse:hover {
    background: var(--menu-collapse) 100% no-repeat;
    &::before{
      display: none;
    }
  }

  .app {
    align-items: center;
    gap: 8px;

    .title {
      font-size: var(--font-18);
      color: var(--theme-text-1); 
    }
  }

 :deep(.menu) {
    flex: 1;
    background: none;
    border: none !important;
    .ant-menu-sub.ant-menu-inline {
      background-color: transparent;
    }
    .ant-menu-item-selected {
      background-color: #F5F5F7;
    }
    .ant-menu-submenu-selected { 
      >.ant-menu-submenu-title {
        color: var(--text-5);
      }
    }
    >.ant-menu-submenu>.ant-menu-submenu-title {
      height: 36px;
      line-height: 36px; 
    }
    &.ant-menu-inline-collapsed {
      width: 40px;
      >.ant-menu-item,
      >.ant-menu-submenu>.ant-menu-submenu-title {
        width: 40px;
        padding: 0 12px;
        margin: 0 0 4px 0;
        .ant-menu-item-icon +span {
          margin-left: 0;
        }
      }
    }
  }
}

</style>




