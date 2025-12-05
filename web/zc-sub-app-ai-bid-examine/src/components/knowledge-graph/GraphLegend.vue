<template>
  <div class="graph-legend" :class="{ collapsed: isCollapsed }">
    <div v-show="!isCollapsed" class="legend-items">
      <!-- 节点类型 -->
      <div class="items-row">
        <div class="legend-item">
          <div class="node-sample node-normal"></div>
          <span>标签节点</span>
        </div>
        <div class="legend-item">
          <div class="node-sample node-element"></div>
          <span>要素节点</span>
        </div>
        <div class="legend-item">
          <div class="node-sample node-doc"></div>
          <span>文档节点</span>
        </div>
        <a-button
          type="text"
          size="small"
          class="collapse-btn"
          @click="toggleCollapse"
        >
          <template #icon>
            <DownOutlined />
          </template>
        </a-button>
      </div>

      <!-- 关系类型 - 第一行 -->
      <div class="items-row">
        <div class="legend-item">
          <div class="edge-sample edge-attached"></div>
          <span>attachedTo</span>
        </div>
        <div class="legend-item">
          <div class="edge-sample edge-part"></div>
          <span>hasPart</span>
        </div>
        <div class="legend-item">
          <div class="edge-sample edge-member"></div>
          <span>hasMember</span>
        </div>
      </div>

      <!-- 关系类型 - 第二行 -->
      <div class="items-row">
        <div class="legend-item">
          <div class="edge-sample edge-same"></div>
          <span>sameAs</span>
        </div>
        <div class="legend-item">
          <div class="edge-sample edge-element"></div>
          <span>hasAttribute</span>
        </div>
      </div>
    </div>

    <!-- 收起状态 - 只显示展开按钮 -->
    <div v-show="isCollapsed" class="collapsed-content">
      <a-button
        type="text"
        size="small"
        class="collapse-btn"
        @click="toggleCollapse"
      >
        <template #icon>
          <UpOutlined />
        </template>
      </a-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { UpOutlined, DownOutlined } from '@ant-design/icons-vue'

const isCollapsed = ref(false)

const toggleCollapse = () => {
  isCollapsed.value = !isCollapsed.value
}
</script>

<style scoped>
.graph-legend {
  background: #ffffff;
  border: 1px solid #e5e6eb;
  border-radius: 8px;
  padding: 16px;
  min-width: 400px;
  transition: all 0.3s ease;
}

.graph-legend.collapsed {
  padding: 8px;
  min-width: auto;
}

.collapsed-content {
  display: flex;
  justify-content: center;
  align-items: center;
}

.collapse-btn {
  padding: 0;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #666;
}

.collapse-btn:hover {
  color: #1890ff;
  background-color: #f0f0f0;
}

.legend-items {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.items-row {
  display: flex;
  flex-direction: row;
  flex-wrap: wrap;
  gap: 16px;
  align-items: center;
}

.items-row .collapse-btn {
  margin-left: auto;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #666;
  white-space: nowrap;
}

/* 节点样式示例 */
.node-sample {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  flex-shrink: 0;
}

.node-normal {
  background-color: #2f4554;
}

.node-element {
  background-color: #722ed1;
  border-radius: 4px;
}

.node-doc {
  background-color: #95a5a6;
}

/* 边样式示例 */
.edge-sample {
  width: 30px;
  height: 2px;
  flex-shrink: 0;
  position: relative;
}

.edge-sample::after {
  content: '';
  position: absolute;
  right: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 0;
  height: 0;
  border-left: 4px solid currentColor;
  border-top: 3px solid transparent;
  border-bottom: 3px solid transparent;
}

.edge-attached {
  background-color: #91cc75;
}

.edge-attached::after {
  color: #91cc75;
}

.edge-part {
  background-color: #fac858;
}

.edge-part::after {
  color: #fac858;
}

.edge-member {
  background-color: #ee6666;
}

.edge-member::after {
  color: #ee6666;
}

.edge-same {
  background: repeating-linear-gradient(
    90deg,
    #fa8c16,
    #fa8c16 4px,
    transparent 4px,
    transparent 8px
  );
}

.edge-same::after {
  color: #fa8c16;
}

.edge-element {
  background: repeating-linear-gradient(
    90deg,
    #9254de,
    #9254de 2px,
    transparent 2px,
    transparent 4px
  );
}

.edge-element::after {
  color: #9254de;
}
</style>
