<template>
  <div class="left-actions-fixed">
    <!-- 左侧竖向背景栏 -->
    <div class="left-rail" aria-hidden="true"></div>

    <!-- 悬浮菜单 -->
    <a-popover
      placement="right"
      trigger="hover"
      :get-popup-container="node => node.parentNode"
      overlayClassName="left-actions-popover"
      :arrow="false"
    >
      <template #content>
        <div class="side-menu">
          <a-button type="text" class="side-menu-item" @click="goToReview">文件审查</a-button>
          <a-button type="text" class="side-menu-item" @click="goToDemo">演示文件查看</a-button>
        </div>
      </template>
      <a-button class="side-icon" shape="circle">AI</a-button>
    </a-popover>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()
const goToReview = () => {
  router.push({ name: 'ComplianceReview' })
}
const goToDemo = () => {
  router.push('/review')
}
</script>

<style scoped>
.left-actions-fixed {
  position: fixed;
  left: 12px;
  top: 100px;
  z-index: 3000;
  pointer-events: none; /* 容器不拦截事件，避免遮挡页面左侧区域 */
}

/* 背景竖栏 */
.left-rail {
  position: fixed;
  left: 8px;
  top: 80px;
  width: 52px;
  height: calc(100vh - 160px);
  background: #ffffff;
  border: 1px solid var(--line-2);
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.06);
  z-index: 2000; /* 在按钮/弹层下面，但确保可见 */
  pointer-events: none;
}

.side-icon {
  width: 36px;
  height: 36px;
  border: 1px solid var(--line-3);
  font-weight: 600;
  background: #2f54eb;
  color: #fff;
  pointer-events: auto; /* 允许点击与悬浮 */
}

/* 弹层样式（由于 get-popup-container 绑定到父节点，scoped 样式可生效） */
.left-actions-popover .ant-popover-inner {
  border-radius: 8px;
  box-shadow: 0 8px 24px rgba(0,0,0,0.12);
}
.left-actions-popover .ant-popover-inner-content {
  padding: 8px;
}

.side-menu {
  display: flex;
  flex-direction: column;
  gap: 6px;
  pointer-events: auto; /* 弹出菜单可交互 */
}

.side-menu-item {
  text-align: left;
  padding: 0 8px;
}
</style>