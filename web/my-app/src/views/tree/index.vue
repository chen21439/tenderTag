<template>
  <div class="paper-tree-viewer">
    <div class="header">
      <h1>论文层级结构可视化</h1>
      <div class="controls">
        <input
          type="file"
          @change="loadJsonFile"
          accept=".json"
          ref="fileInput"
        />
        <button @click="expandAll">全部展开</button>
        <button @click="collapseAll">全部折叠</button>

        <!-- 模式切换按钮组 -->
        <div class="mode-switcher">
          <button
            @click="layoutMode = 'split'"
            :class="{ active: layoutMode === 'split' }"
            class="mode-btn"
          >
            分栏模式
          </button>
          <button
            @click="layoutMode = 'paper'"
            :class="{ active: layoutMode === 'paper' }"
            class="mode-btn"
          >
            纸张模式
          </button>
        </div>
      </div>
    </div>

    <div class="content-wrapper" :class="layoutMode">
      <!-- 左侧：层级树 -->
      <div class="tree-panel">
        <div v-if="!treeData.length" class="empty-state">
          请选择JSON文件加载论文数据
        </div>
        <div v-else>
          <!-- 元信息区域 -->
          <div v-if="metaNodes.length" class="meta-section">
            <h3>元信息</h3>
            <TreeNode
              v-for="node in metaNodes"
              :key="node.line_id"
              :node="node"
              :depth="0"
              :expanded-nodes="expandedNodes"
              @toggle="toggleNode"
              @select="selectNode"
              :selected-id="selectedNodeId"
            />
          </div>

          <!-- 正文内容树 -->
          <div class="content-section">
            <h3>正文结构</h3>
            <TreeNode
              v-for="node in contentNodes"
              :key="node.line_id"
              :node="node"
              :depth="0"
              :expanded-nodes="expandedNodes"
              @toggle="toggleNode"
              @select="selectNode"
              :selected-id="selectedNodeId"
            />
          </div>
        </div>
      </div>

      <!-- 右侧：详细信息/纸张预览 -->
      <div class="detail-panel">
        <div v-if="layoutMode === 'split' && selectedNode" class="node-detail">
          <h2>节点详情</h2>
          <div class="detail-item">
            <label>ID:</label>
            <span>{{ selectedNode.line_id }}</span>
          </div>
          <div class="detail-item">
            <label>类型:</label>
            <span class="class-tag" :class="selectedNode.class">{{ selectedNode.class }}</span>
          </div>
          <div class="detail-item">
            <label>父节点:</label>
            <span>{{ selectedNode.parent_id === -1 ? '根节点' : selectedNode.parent_id }}</span>
          </div>
          <div class="detail-item">
            <label>关系类型:</label>
            <span class="relation-tag">{{ getRelationLabel(selectedNode.relation) }}</span>
          </div>
          <div class="detail-item">
            <label>页码:</label>
            <span>第 {{ selectedNode.page + 1 }} 页</span>
          </div>
          <div v-if="selectedNode.text" class="detail-item">
            <label>内容:</label>
            <div class="text-content">{{ selectedNode.text }}</div>
          </div>
          <div v-if="selectedNode.box" class="detail-item">
            <label>位置信息:</label>
            <div class="box-info">
              <span>X: {{ selectedNode.box[0] }}, Y: {{ selectedNode.box[1] }}</span><br>
              <span>宽: {{ selectedNode.box[2] - selectedNode.box[0] }}, 高: {{ selectedNode.box[3] - selectedNode.box[1] }}</span>
            </div>
          </div>
          <div class="detail-item">
            <label>原始数据:</label>
            <pre class="json-content">{{ JSON.stringify(selectedNode, null, 2) }}</pre>
          </div>
        </div>

        <!-- 纸张预览模式 -->
        <div v-else-if="layoutMode === 'paper'" class="paper-preview">
          <h2>论文预览</h2>
          <div class="paper-container">
            <PaperView
              :nodes="allNodes"
              :selected-id="selectedNodeId"
              @select="selectNode"
            />
          </div>
        </div>

        <div v-else class="empty-state">
          请选择一个节点查看详情
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import TreeNode from './TreeNode.vue'
import PaperView from './PaperView.vue'

// 数据状态
const rawData = ref([])
const allNodes = ref([])
const treeData = ref([])
const expandedNodes = ref(new Set())
const selectedNodeId = ref(null)
const layoutMode = ref('split') // 'split', 'paper', 'bbox'

// 元信息节点（title, author, affili等）
const metaNodes = computed(() => {
  return treeData.value.filter(node => node.is_meta)
})

// 正文内容节点
const contentNodes = computed(() => {
  return treeData.value.filter(node => !node.is_meta)
})

// 计算选中节点的详细信息
const selectedNode = computed(() => {
  if (!selectedNodeId.value && selectedNodeId.value !== 0) return null
  return findNodeById(allNodes.value, selectedNodeId.value)
})

// 加载JSON文件
const loadJsonFile = (event) => {
  const file = event.target.files[0]
  if (!file) return

  const reader = new FileReader()
  reader.onload = (e) => {
    try {
      const data = JSON.parse(e.target.result)
      rawData.value = Array.isArray(data) ? data : [data]
      allNodes.value = rawData.value
      buildTree()
      // 默认展开第一层
      expandedNodes.value = new Set(
        rawData.value
          .filter(n => n.parent_id === -1 || n.relation === 'meta')
          .map(n => n.line_id)
      )
    } catch (error) {
      console.error('JSON解析失败:', error)
      alert('JSON文件格式错误')
    }
  }
  reader.readAsText(file)
}

// 构建树形结构
const buildTree = () => {
  if (!rawData.value.length) return

  // 创建节点映射
  const nodeMap = new Map()
  rawData.value.forEach(item => {
    nodeMap.set(item.line_id, {
      ...item,
      children: []
    })
  })

  // 构建父子关系
  const roots = []
  rawData.value.forEach(item => {
    const node = nodeMap.get(item.line_id)

    if (item.parent_id === -1) {
      // 根节点
      roots.push(node)
    } else if (item.relation === 'contain') {
      // contain关系：作为树的层级边（父子关系）
      const parent = nodeMap.get(item.parent_id)
      if (parent) {
        parent.children.push(node)
      } else {
        roots.push(node)
      }
    } else if (item.relation === 'equality') {
      // equality关系：并列关系，作为兄弟节点展示
      const parent = nodeMap.get(item.parent_id)
      if (parent) {
        parent.children.push(node)
      } else {
        roots.push(node)
      }
    }
    // connect关系：段内连接，不在树中显示，仅用于文本拼接
  })

  treeData.value = roots
}

// 工具函数：通过ID查找节点
const findNodeById = (nodes, id) => {
  for (const node of nodes) {
    if (node.line_id === id) return node
  }
  return null
}

// 切换节点展开/折叠
const toggleNode = (nodeId) => {
  if (expandedNodes.value.has(nodeId)) {
    expandedNodes.value.delete(nodeId)
  } else {
    expandedNodes.value.add(nodeId)
  }
  expandedNodes.value = new Set(expandedNodes.value)
}

// 选择节点
const selectNode = (nodeId) => {
  selectedNodeId.value = nodeId
}

// 全部展开
const expandAll = () => {
  const allIds = new Set()
  rawData.value.forEach(node => {
    allIds.add(node.line_id)
  })
  expandedNodes.value = allIds
}

// 全部折叠
const collapseAll = () => {
  expandedNodes.value.clear()
}


// 获取关系类型标签
const getRelationLabel = (relation) => {
  const labelMap = {
    contain: '包含',
    equality: '并列',
    connect: '连接',
    meta: '元信息'
  }
  return labelMap[relation] || relation
}
</script>

<style scoped>
.paper-tree-viewer {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f5f5f5;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}

.header {
  background: white;
  padding: 20px;
  border-bottom: 1px solid #e0e0e0;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.header h1 {
  margin: 0 0 15px 0;
  font-size: 24px;
  color: #333;
}

.controls {
  display: flex;
  gap: 10px;
  align-items: center;
}

.controls button {
  padding: 8px 16px;
  background: #1976d2;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: background 0.2s;
}

.controls button:hover {
  background: #1565c0;
}

.mode-switcher {
  display: flex;
  gap: 0;
  border: 2px solid #1976d2;
  border-radius: 4px;
  overflow: hidden;
}

.mode-btn {
  padding: 8px 20px;
  background: white;
  color: #1976d2;
  border: none;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s;
  border-right: 1px solid #1976d2;
}

.mode-btn:last-child {
  border-right: none;
}

.mode-btn:hover {
  background: #e3f2fd;
}

.mode-btn.active {
  background: #1976d2;
  color: white;
}

.content-wrapper {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.content-wrapper.paper .tree-panel {
  width: 350px;
  flex: none;
}

.content-wrapper.paper .detail-panel {
  flex: 1;
  width: auto;
}

.tree-panel {
  flex: 1;
  overflow-y: auto;
  background: white;
  padding: 20px;
  border-right: 1px solid #e0e0e0;
}

.meta-section, .content-section {
  margin-bottom: 30px;
}

.meta-section h3, .content-section h3 {
  margin: 0 0 15px 0;
  font-size: 16px;
  color: #666;
  border-bottom: 2px solid #e0e0e0;
  padding-bottom: 8px;
}

.detail-panel {
  width: 450px;
  overflow-y: auto;
  background: white;
  padding: 20px;
}

.empty-state {
  text-align: center;
  color: #999;
  padding: 40px;
  font-size: 14px;
}

.node-detail h2 {
  margin: 0 0 20px 0;
  font-size: 18px;
  color: #333;
  border-bottom: 2px solid #1976d2;
  padding-bottom: 10px;
}

.detail-item {
  margin-bottom: 15px;
}

.detail-item label {
  display: block;
  font-weight: bold;
  color: #666;
  margin-bottom: 5px;
  font-size: 13px;
}

.class-tag {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.class-tag.title { background: #e3f2fd; color: #1976d2; }
.class-tag.author { background: #f3e5f5; color: #7b1fa2; }
.class-tag.affili { background: #fce4ec; color: #c2185b; }
.class-tag.mail { background: #fff3e0; color: #e65100; }
.class-tag.sec1 { background: #ffebee; color: #c62828; }
.class-tag.sec2 { background: #e8f5e9; color: #2e7d32; }
.class-tag.sec3 { background: #e0f2f1; color: #00695c; }
.class-tag.para { background: #f5f5f5; color: #616161; }
.class-tag.fstline { background: #fafafa; color: #757575; }

.relation-tag {
  display: inline-block;
  padding: 4px 10px;
  background: #eceff1;
  border-radius: 4px;
  font-size: 12px;
  font-family: monospace;
  color: #546e7a;
}

.text-content {
  background: #f9f9f9;
  padding: 12px;
  border-radius: 4px;
  border-left: 3px solid #1976d2;
  line-height: 1.6;
  color: #333;
  font-size: 14px;
  white-space: pre-wrap;
}

.box-info {
  background: #f5f5f5;
  padding: 8px 12px;
  border-radius: 4px;
  font-family: monospace;
  font-size: 12px;
  color: #555;
}

.json-content {
  background: #263238;
  color: #aed581;
  padding: 12px;
  border-radius: 4px;
  font-size: 11px;
  overflow-x: auto;
  max-height: 300px;
  line-height: 1.5;
}

.paper-preview h2 {
  margin: 0 0 20px 0;
  font-size: 18px;
  color: #333;
  border-bottom: 2px solid #1976d2;
  padding-bottom: 10px;
}

.paper-container {
  height: calc(100% - 50px);
  overflow-y: auto;
}
</style>
