<template>
  <!-- 菜单分组 - 在折叠状态下不显示分组标题，直接显示子菜单 -->
  <template v-if="item.type === 'group'">
    <!-- 非折叠状态显示分组标题 -->
    <div v-if="!isCollapse" class="menu-group-title">
      {{ item.title }}
    </div>
    <!-- 渲染分组下的子菜单 -->
    <template v-for="child in item.children" :key="child.key">
      <menu-item-component
        :item="child"
        :is-collapse="isCollapse"
        @menu-click="$emit('menuClick', $event)"
      />
    </template>
  </template>

  <!-- 有子菜单的普通菜单项 -->
  <a-sub-menu
    v-else-if="item.children && item.children.length > 0"
    :key="item.key"
    :class="{ 'parent-menu-clickable': item.route }"
  >
    <template #icon>
      <template v-if="item.icon">
        <svg-icon v-if="isSvgIcon(item.icon)" class="icon" :icon="item.icon"/>
        <component v-else :is="item.icon"  class="icon"/>
      </template>
    </template> 
    <!-- 如果父菜单有路由，添加点击遮罩层 -->
    <!-- <template #title>
      <div
        v-if="item.route"
        class="parent-menu-overlay"
        @click.stop="handleParentClick"
      ></div>
      {{ item.title }}
    </template> -->
    <template #title>{{ item.title }}</template>
    <!-- 递归渲染子菜单 -->
    <template v-for="child in item.children" :key="child.key">
      <menu-item-component
        :item="child"
        :is-collapse="isCollapse"
        @menu-click="$emit('menuClick', $event)"
      />
    </template>
  </a-sub-menu>

  <!-- 普通菜单项 -->
  <a-menu-item v-else :key="item.route" @click="handleClick">
    <template #icon>
      <template v-if="item.icon">
        <svg-icon v-if="isSvgIcon(item.icon)" class="icon" :icon="item.icon"/>
        <!-- Ant Design Vue 图标 -->
        <component :is="item.icon"  class="icon"/>
      </template>
    </template>
    <span>{{ item.title }}</span>
  </a-menu-item>
</template>

<script setup lang="ts">
interface MenuItem {
  key: string
  title: string
  icon?: string
  route?: string
  children?: MenuItem[]
  type?: 'group' | 'menu'
}

// 定义组件名称，用于递归
defineOptions({
  name: 'MenuItemComponent'
})

const props = defineProps<{
  item: MenuItem
  isCollapse: boolean
}>()

const emit = defineEmits(['menuClick'])
// 判断是否为 SvgIcon（以 icon- 开头的为 SvgIcon）
const isSvgIcon = (icon?: string) => {
  return icon?.startsWith('icon-') || false
}
const handleClick = () => {
  if (props.item.route) {
    emit('menuClick', props.item.route)
  }
}

// 处理父菜单点击事件
const handleParentClick = () => {
  if (props.item.route) {
    emit('menuClick', props.item.route)
  }
}
</script>

<style scoped lang="scss">
.menu-group-title {
  font-size: 12px;
  color: var(--text-3);
  height: 32px;
  line-height: 32px;
  margin-bottom: 8px;
}
.icon {
  width: 20px;
  height: 20px;
  color: var(--text-5);
}

// 父菜单可点击样式
:deep(.parent-menu-clickable) {
  .ant-menu-submenu-title {
    position: relative;
    cursor: pointer;

    &:hover {
      color: var(--primary-color) !important;
    }

    // 确保箭头区域不被遮罩层覆盖
    .ant-menu-submenu-arrow {
      position: relative;
      z-index: 2;
      cursor: pointer;
    }
  }
}

.parent-menu-overlay {
  position: absolute;
  top: 0;
  left: 0;
  bottom: 0;
  right: 24px; /* 为箭头留出足够空间 */
  z-index: 1;
  cursor: pointer;
}
</style>


