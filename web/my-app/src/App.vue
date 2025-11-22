<script setup>
import { RouterLink, RouterView } from 'vue-router'
</script>

<template>
  <div class="app">
    <header class="app-header">
      <div class="header-content">
        <div class="logo">
          <span class="logo-icon">📄</span>
          <span class="logo-text">文档分析系统</span>
        </div>
        <nav class="nav">
          <RouterLink to="/tree" class="nav-link">论文结构树</RouterLink>
          <RouterLink to="/" class="nav-link">PDF 内容解析</RouterLink>
          <RouterLink to="/pdf-viewer" class="nav-link">PDF 查看器</RouterLink>
          <RouterLink to="/sections" class="nav-link">Sections 分析</RouterLink>
          <RouterLink to="/section-header-preview" class="nav-link">sectionHeaderPreview</RouterLink>
        </nav>
      </div>
    </header>

    <main class="app-main">
      <RouterView />
    </main>
  </div>
</template>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
  background: linear-gradient(to bottom, #f8f9fa 0%, #e9ecef 100%);
  min-height: 100vh;
}

.app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

/* Header 样式 */
.app-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  position: sticky;
  top: 0;
  z-index: 1000;
}

.header-content {
  max-width: 100%;
  padding: 1.5rem 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 1rem;
}

.logo {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-size: 1.5rem;
  font-weight: 700;
  cursor: pointer;
  user-select: none;
}

.logo-icon {
  font-size: 2rem;
}

.logo-text {
  letter-spacing: -0.5px;
}

/* 导航样式 */
.nav {
  display: flex;
  gap: 1rem;
  align-items: center;
}

.nav-link {
  color: white;
  text-decoration: none;
  padding: 0.75rem 1.5rem;
  border-radius: 10px;
  font-weight: 600;
  font-size: 0.95rem;
  transition: all 0.3s ease;
  border: 2px solid transparent;
}

.nav-link:hover {
  background: rgba(255, 255, 255, 0.15);
  transform: translateY(-2px);
}

.nav-link.router-link-active {
  background: white;
  color: #667eea;
  border-color: white;
  box-shadow: 0 4px 12px rgba(255, 255, 255, 0.3);
}

/* Main 内容区域 */
.app-main {
  flex: 1;
  width: 100%;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .header-content {
    padding: 1rem;
    flex-direction: column;
    align-items: flex-start;
  }

  .logo {
    font-size: 1.2rem;
  }

  .logo-icon {
    font-size: 1.5rem;
  }

  .nav {
    width: 100%;
    gap: 0.5rem;
  }

  .nav-link {
    flex: 1;
    text-align: center;
    padding: 0.6rem 1rem;
    font-size: 0.9rem;
  }
}

@media (max-width: 480px) {
  .nav {
    flex-direction: column;
  }

  .nav-link {
    width: 100%;
  }
}
</style>
