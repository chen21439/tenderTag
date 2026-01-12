<template>
  <div class="toc-tree-container">
    <div v-if="isLoading" class="loading">加载中...</div>
    <div v-else-if="treeData.length === 0" class="empty">暂无数据</div>
    <div v-else class="tree-list">
      <TreeNode
        v-for="node in treeData"
        :key="node.line_id"
        :node="node"
        :depth="0"
        :expanded-nodes="expandedNodes"
        :selected-ids="selectedIds"
        :node-map="nodeMap"
        :debug-mode="false"
        :edit-mode="false"
        @toggle="handleToggle"
        @select="handleSelect"
        @paragraphClick="handleParagraphClick"
        @update-relation="handleUpdateRelation"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { message } from 'ant-design-vue'
import TreeNode from './TreeNode.vue'
import { useTreeBuilderV2 } from '@/hooks/useTreeBuilderV2'

const props = defineProps<{
  taskId: string
  selectedNodeIds: number[]
  expandedNodes: Set<number>
}>()

const emit = defineEmits<{
  'node-selected': [data: { nodeId: string; node: any }]
  'toggle': [nodeId: number]
  'paragraph-click': [paragraphId: number]
}>()

// 数据状态
const isLoading = ref(false)
const constructRawData = ref<any[]>([])
const treeData = ref<any[]>([])
const nodeMap = ref<Record<string, any>>({})

// 选中的节点 IDs（用于高亮显示）
const selectedIds = computed(() => props.selectedNodeIds)

// 加载 Construct 树数据
const loadConstructTreeData = async (taskId: string) => {
  try {
    isLoading.value = true
    const apiUrl = `/python/api/pdf/task/${taskId}/result?result_type=construct&t=${Date.now()}`
    console.log(`🔄 [TocTree] 加载 Construct 数据:`, apiUrl)

    const response = await fetch(apiUrl)
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`)
    }

    const jsonData = await response.json()

    // 处理 API 格式: { success: true, data: { dataList: [...] } }
    let rawData
    if (jsonData.success && jsonData.data && jsonData.data.dataList) {
      rawData = jsonData.data.dataList
    } else if (Array.isArray(jsonData)) {
      rawData = jsonData
    } else {
      rawData = [jsonData]
    }

    console.log(`📊 [TocTree] 获取到 construct 数据，节点数:`, rawData.length)

    // 显示全量数据（不过滤）
    console.log(`📊 [TocTree] 使用全量数据，节点数: ${rawData.length}`)

    constructRawData.value = rawData
    await buildConstructTree()
  } catch (error) {
    console.error('❌ [TocTree] 数据加载失败:', error)
    message.error('加载 TOC 数据失败')
  } finally {
    isLoading.value = false
  }
}

// 构建 Construct 树
const buildConstructTree = async () => {
  try {
    const dataSource = constructRawData.value

    if (!dataSource.length) {
      console.log('⚠️ [TocTree] 数据为空，无法构建')
      treeData.value = []
      return
    }

    console.log('🏗️ [TocTree] 构建树，数据节点数:', dataSource.length)

    // 创建 line_id 到节点的映射
    const localNodeMap = new Map<string, any>()
    dataSource.forEach(item => {
      localNodeMap.set(String(item.line_id), item)
    })

    // 检测循环引用
    const detectCycle = (nodeId: string, visited: Set<string>): boolean => {
      if (visited.has(nodeId)) return true
      const node = localNodeMap.get(nodeId)
      if (!node || !node.parent_id || node.parent_id === node.line_id) return false
      visited.add(nodeId)
      return detectCycle(String(node.parent_id), visited)
    }

    // 找出需要修正的节点
    const nodesToFix = new Set<string>()

    // 1. 检查自引用
    dataSource.forEach(item => {
      if (item.line_id === item.parent_id) {
        console.warn('[TocTree] 节点自引用: line_id=' + item.line_id)
        nodesToFix.add(String(item.line_id))
      }
    })

    // 2. 检查 equality 互相指向
    const checkedPairs = new Set<string>()
    dataSource.forEach(item => {
      if (item.relation === 'equality' && !nodesToFix.has(String(item.line_id))) {
        const pairKey = [item.line_id, item.parent_id].sort().join('-')
        if (!checkedPairs.has(pairKey)) {
          checkedPairs.add(pairKey)
          const parentNode = localNodeMap.get(String(item.parent_id))
          if (parentNode && parentNode.relation === 'equality' && parentNode.parent_id === item.line_id) {
            console.warn('[TocTree] equality 互相指向: ' + item.line_id + ' ⇔ ' + item.parent_id)
            nodesToFix.add(String(item.line_id))
            nodesToFix.add(String(parentNode.line_id))
          }
        }
      }
    })

    // 3. 检查循环引用
    dataSource.forEach(item => {
      if (!nodesToFix.has(String(item.line_id))) {
        const visited = new Set<string>()
        if (detectCycle(String(item.line_id), visited)) {
          console.warn('[TocTree] 循环引用: line_id=' + item.line_id)
          nodesToFix.add(String(item.line_id))
        }
      }
    })

    console.log('   - [TocTree] 需要修正的节点数: ' + nodesToFix.size)

    // 修正数据
    const fixedData = dataSource.map(item => {
      if (nodesToFix.has(String(item.line_id))) {
        return { ...item, parent_id: item.line_id }
      }
      return item
    })

    // 使用 useTreeBuilderV2 构建树
    const { buildTreeByParentId } = useTreeBuilderV2()
    const result = buildTreeByParentId(fixedData, 'line_id', 'parent_id', 'relation')

    treeData.value = result

    // 创建 nodeMap 供 TreeNode 使用
    const mapObj: Record<string, any> = {}
    const traverse = (nodes: any[]) => {
      nodes.forEach(node => {
        mapObj[node.line_id] = node
        if (node.children) traverse(node.children)
      })
    }
    traverse(treeData.value)
    nodeMap.value = mapObj

    console.log('✅ [TocTree] 树构建完成，根节点数:', treeData.value.length)
  } catch (error) {
    console.error('❌ [TocTree] 树构建失败:', error)
    throw error  // 重新抛出，让外层的 loadConstructTreeData 捕获
  }
}

// 事件处理
const handleToggle = (nodeId: number) => {
  emit('toggle', nodeId)
}
const handleSelect = (nodeId: number, event?: MouseEvent) => {
  console.log('🎯 [TocTree] 选中节点:', nodeId)

  // 从 nodeMap 中查找节点
  const node = nodeMap.value[nodeId]

  if (node) {
    emit('node-selected', { nodeId: String(nodeId), node })
  } else {
    console.warn('⚠️ [TocTree] 未找到节点:', nodeId)
  }
}

const handleParagraphClick = (paragraphId: number) => {
  emit('paragraph-click', paragraphId)
}

const handleUpdateRelation = async (data: {
  nodeId: string
  class?: string
  relation: string
  parent_id?: number | string
}) => {
  console.log('🔗 [TocTree] 更新节点关系:', data)

  try {
    // 准备请求体
    const requestBody: any = {
      lineId: Number(data.nodeId)
    }

    if (data.class !== undefined) {
      requestBody.className = data.class || ''
    }

    requestBody.relation = data.relation || ''

    if (data.parent_id !== undefined) {
      requestBody.parentId = data.parent_id === '' || data.parent_id === null ? '' : Number(data.parent_id)
    }

    console.log('📦 [TocTree] 请求体:', requestBody)

    const response = await fetch(`/python/api/pdf/task/${props.taskId}/construct`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(requestBody)
    })

    const result = await response.json()

    if (response.ok && result.success) {
      message.success('节点信息已更新')
      console.log('✅ [TocTree] 更新成功:', result)

      // 在内存中更新原始数据
      const nodeId = Number(data.nodeId)
      const nodeInRawData = constructRawData.value.find(n => n.line_id === nodeId)
      if (nodeInRawData) {
        if (data.class !== undefined) {
          nodeInRawData.class = data.class
        }
        if (data.relation !== undefined) {
          nodeInRawData.relation = data.relation
        }
        if (data.parent_id !== undefined) {
          nodeInRawData.parent_id = data.parent_id === '' || data.parent_id === null ? null : Number(data.parent_id)
        }
        console.log('📝 [TocTree] 已在内存中更新节点:', nodeInRawData)
      }

      // 重新构建树（不重新请求接口）
      await buildConstructTree()
    } else {
      message.error(result.errMsg || '更新失败')
      console.error('❌ [TocTree] 更新失败:', result)
    }
  } catch (error: any) {
    console.error('❌ [TocTree] 更新关系失败:', error)
    message.error(`更新关系失败: ${error.message}`)
  }
}

// 监听 taskId 变化，自动加载数据
watch(() => props.taskId, (newTaskId) => {
  if (newTaskId) {
    loadConstructTreeData(newTaskId)
  }
}, { immediate: true })

// 暴露方法供父组件调用
defineExpose({
  reload: () => loadConstructTreeData(props.taskId)
})
</script>

<style scoped>
.toc-tree-container {
  height: 100%;
  overflow-y: auto;
}

.loading,
.empty {
  padding: 20px;
  text-align: center;
  color: #999;
}

.tree-list {
  padding: 10px 0;
}
</style>
