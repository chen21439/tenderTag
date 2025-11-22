<template>
  <div class="left-actions-fixed" :class="{ 'is-expanded': isExpanded }">
    <!-- 左侧竖向背景栏 -->
    <div class="left-rail">
      <!-- Logo区域 -->
      <div class="logo-area">
        <a-button class="side-icon" shape="circle">AI</a-button>
        <span v-if="isExpanded" class="logo-text">智能采购1.0</span>
      </div>

      <!-- 菜单项 -->
      <a-tooltip placement="right" :title="isExpanded ? '' : '知识图谱配置'">
        <div class="menu-item" @click="goToKnowledgeGraph">
          <svg
            class="menu-icon"
            width="18"
            height="18"
            viewBox="0 0 24 24"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
          >
            <!-- 知识图谱节点和连线 -->
            <circle cx="6" cy="6" r="2" stroke="currentColor" stroke-width="1.5"/>
            <circle cx="18" cy="6" r="2" stroke="currentColor" stroke-width="1.5"/>
            <circle cx="6" cy="18" r="2" stroke="currentColor" stroke-width="1.5"/>
            <!-- 节点连线 -->
            <line x1="8" y1="6" x2="16" y2="6" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
            <line x1="6" y1="8" x2="6" y2="16" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
            <line x1="7.4" y1="7.4" x2="16.6" y2="16.6" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
            <!-- 配置：小齿轮 -->
            <circle cx="17" cy="17" r="2.5" stroke="currentColor" stroke-width="1.5"/>
            <!-- "齿" -->
            <line x1="17" y1="13.8" x2="17" y2="12.5" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
            <line x1="17" y1="21.5" x2="17" y2="20.2" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
            <line x1="13.8" y1="17" x2="12.5" y2="17" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
            <line x1="21.5" y1="17" x2="20.2" y2="17" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
            <line x1="14.6" y1="14.6" x2="13.7" y2="13.7" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
            <line x1="20.3" y1="20.3" x2="19.4" y2="19.4" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
            <line x1="19.4" y1="14.6" x2="20.3" y2="13.7" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
            <line x1="13.7" y1="20.3" x2="14.6" y2="19.4" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
          </svg>
          <span v-if="isExpanded" class="menu-text">知识图谱配置</span>
        </div>
      </a-tooltip>

      <!-- 底部用户区域 -->
      <!-- <div class="user-area">
        <img src="" alt="" class="user-avatar" />
      </div> -->
    </div>

    <!-- 展开/收起按钮 -->
    <a-tooltip :title="isExpanded ? '收起' : '展开'" placement="right">
      <div class="btn-toggle" @click="toggleExpand">
        <RightOutlined v-if="!isExpanded" />
        <LeftOutlined v-else />
      </div>
    </a-tooltip>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { RightOutlined, LeftOutlined } from '@ant-design/icons-vue'

const router = useRouter()
const isExpanded = ref(false)

const toggleExpand = () => {
  isExpanded.value = !isExpanded.value
}

const goToKnowledgeGraph = () => {
  router.push({ name: 'KnowledgeGraphConfig' })
}
const goToLibrary = () => {
  router.push({ name: 'LibraryIndex' })
}
</script>

<style scoped>
.left-actions-fixed {
  position: fixed;
  left: 0;
  top: 0;
  z-index: 3000;
  width: 48px;
  height: 100vh;
  pointer-events: none; /* 容器不拦截事件，避免遮挡页面左侧区域 */
}

.left-actions-fixed.is-expanded {
  width: 200px;
}

/* 背景竖栏 */
.left-rail {
  position: fixed;
  left: 0;
  top: 0;
  width: 48px;
  height: 100vh;
  background: #ffffff;
  border-right: 1px solid #e5e6eb;
  z-index: 2000;
  pointer-events: auto;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 12px 0;
  transition: width 0.3s;
  overflow: hidden;
}

/* Logo区域 */
.logo-area {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin-bottom: 16px;
  padding: 4px 0;
  width: 100%;
}

.is-expanded .logo-area {
  justify-content: flex-start;
  padding-left: 8px;
}

.logo-text {
  font-size: 14px;
  font-weight: 600;
  color: #333;
  white-space: nowrap;
}

.side-icon {
  width: 32px;
  height: 32px;
  min-width: 32px;
  border: none;
  font-weight: 600;
  font-size: 12px;
  background: #2f54eb;
  color: #fff;
  flex-shrink: 0;
}

/* 菜单项 */
.menu-item {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 8px;
  border-radius: 6px;
  cursor: pointer;
  color: #666;
  transition: all 0.2s;
  width: 100%;
}

.is-expanded .menu-item {
  justify-content: flex-start;
  padding-left: 12px;
}

.menu-item:hover {
  background: #f5f5f5;
}

.menu-item.active {
  background: #e6f4ff;
  color: #1677ff;
}

.menu-icon {
  font-size: 18px;
  flex-shrink: 0;
}

.menu-text {
  font-size: 14px;
  white-space: nowrap;
}

/* 用户区域 */
.user-area {
  margin-top: auto;
  padding: 8px 0;
  display: flex;
  justify-content: center;
  width: 100%;
}

.user-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: #f0f0f0;
}

/* 展开/收起按钮 */
.btn-toggle {
  position: fixed;
  left: 48px;
  top: 50%;
  transform: translate(-50%, -50%);
  width: 12px;
  height: 32px;
  background: #fff;
  border: 1px solid #e5e6eb;
  border-radius: 2px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  pointer-events: auto;
  color: #bfbfbf;
  font-size: 8px;
  z-index: 2001;
  transition: all 0.3s;
}

.btn-toggle:hover {
  color: #2f54eb;
}

/* 展开状态下的按钮位置 */
.is-expanded .btn-toggle {
  left: 200px;
}

/* 侧边标签文字 */
.side-label {
  position: fixed;
  left: 48px;
  top: 24px;
  font-size: 14px;
  color: #333;
  white-space: nowrap;
  pointer-events: none;
}

.side-label-doc {
  top: 68px;
}

/* 展开状态 */
.is-expanded .left-rail {
  width: 200px;
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