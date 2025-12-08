<template>
  <div class="folder-explorer-container">
    <!-- 地址栏 -->
    <div class="address-bar">
      <a-breadcrumb>
        <a-breadcrumb-item>
          <a @click="navigateToNode(null, '根目录')">
            <HomeOutlined />
            根目录
          </a>
        </a-breadcrumb-item>
        <a-breadcrumb-item v-for="(item, index) in pathHistory.slice(1)" :key="index">
          <!-- 只有有 ID 的节点才可以点击 -->
          <a v-if="item.id !== null" @click="navigateToNode(item.id, item.name)">
            {{ item.name }}
          </a>
          <span v-else class="path-text">
            {{ item.name }}
          </span>
        </a-breadcrumb-item>
      </a-breadcrumb>
    </div>

    <!-- 工具栏 -->
    <div class="toolbar-bar">
      <div class="toolbar-left">
        <a-tooltip title="新建文件夹">
          <a-button type="text" size="small" @click="startCreateFolder">
            <template #icon>
              <FolderAddOutlined />
            </template>
          </a-button>
        </a-tooltip>
        <a-tooltip title="上传文件">
          <a-upload
            :show-upload-list="false"
            :before-upload="handleBeforeUpload"
            :custom-request="handleFileUpload"
            multiple
          >
            <a-button type="text" size="small">
              <template #icon>
                <UploadOutlined />
              </template>
            </a-button>
          </a-upload>
        </a-tooltip>
      </div>
      <div class="toolbar-right">
        <a-radio-group v-model:value="viewMode" size="small" button-style="solid">
          <a-tooltip title="文件夹">
            <a-radio-button value="folder">
              <FolderOutlined />
            </a-radio-button>
          </a-tooltip>
          <a-tooltip title="实体列表">
            <a-radio-button value="list">
              <UnorderedListOutlined />
            </a-radio-button>
          </a-tooltip>
          <a-tooltip title="图谱">
            <a-radio-button value="graph">
              <ApartmentOutlined />
            </a-radio-button>
          </a-tooltip>
        </a-radio-group>
      </div>
    </div>

    <!-- 文件列表（文件夹模式） -->
    <div v-if="viewMode === 'folder'" class="file-list">
      <a-empty v-if="currentItems.length === 0 && !isCreatingFolder" description="此文件夹为空" />
      <div v-if="currentItems.length > 0 || isCreatingFolder" class="items-grid">
        <!-- 新建文件夹输入框 -->
        <div v-if="isCreatingFolder" class="file-item creating">
          <div class="item-icon">
            <FolderOutlined style="font-size: 48px; color: #faad14" />
          </div>
          <a-input
            ref="newFolderInput"
            v-model:value="newFolderName"
            size="small"
            placeholder="新建文件夹"
            class="folder-name-input"
            @pressEnter="confirmCreateFolder"
            @blur="cancelCreateFolder"
            @keydown.esc="cancelCreateFolder"
          />
        </div>

        <!-- 现有文件和文件夹 -->
        <div
          v-for="item in currentItems"
          :key="item.key"
          class="file-item"
          :class="{
            selected: selectedKey === item.key,
            renaming: isRenaming && renamingItemKey === item.key
          }"
          @click="handleItemClick(item)"
          @dblclick="handleItemDoubleClick(item)"
          @contextmenu.prevent="handleContextMenu($event, item)"
        >
          <div class="item-icon">
            <FolderOutlined v-if="item.isFolder" style="font-size: 48px; color: #faad14" />
            <FileTextOutlined v-else style="font-size: 48px; color: #1890ff" />
          </div>
          <!-- 正常显示或重命名输入框 -->
          <div v-if="!isRenaming || renamingItemKey !== item.key" class="item-name">{{ item.title }}</div>
          <a-input
            v-else
            ref="renameInputRef"
            v-model:value="renameInput"
            size="small"
            class="rename-input"
            @pressEnter="confirmRename"
            @blur="cancelRename"
            @keydown.esc="cancelRename"
            @click.stop
          />
          <div v-if="!item.isFolder && item.page !== undefined" class="item-info">
            第{{ item.page + 1 }}页
          </div>
        </div>
      </div>
    </div>

    <!-- 右键菜单（使用固定定位的浮层） -->
    <div
      v-if="contextMenuVisible"
      class="context-menu"
      :style="{
        left: contextMenuX + 'px',
        top: contextMenuY + 'px'
      }"
      @click.stop
    >
      <div class="menu-item" @click="handleRenameClick">
        <EditOutlined />
        <span>重命名</span>
      </div>
      <div class="menu-item danger" @click="handleDeleteClick">
        <DeleteOutlined />
        <span>删除</span>
      </div>
    </div>

    <!-- 遮罩层 - 点击关闭菜单 -->
    <div
      v-if="contextMenuVisible"
      class="context-menu-mask"
      @click="contextMenuVisible = false"
    />

    <!-- 实体列表视图 -->
    <div v-if="viewMode === 'list'" class="entity-list">
      <a-spin :spinning="loadingEntities">
        <div v-if="entityTreeData.length > 0" class="tree-container">
          <TreeNode
            v-for="node in entityTreeData"
            :key="node.line_id"
            :node="node"
            :depth="0"
            :expanded-nodes="expandedNodes"
            :selected-id="selectedEntityId"
            :node-map="nodeMap"
            :debug-mode="false"
            @toggle="handleToggle"
            @select="handleEntitySelect"
          />
        </div>
        <a-empty v-else description="暂无实体数据" />
      </a-spin>
    </div>

    <!-- 图谱视图 -->
    <div v-if="viewMode === 'graph'" class="graph-view">
      <a-spin :spinning="loadingGraph">
        <div v-if="graphNodes.length > 0" class="graph-container">
          <CytoscapeComponent
            :use-sample-data="false"
            :nodes="graphNodes"
            :edges="graphEdges"
            layout="cose"
            element-label-mode="value"
          />
        </div>
        <a-empty v-else description="暂无图谱数据" />
      </a-spin>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick, onMounted } from 'vue'
import {
  FolderOutlined,
  FileTextOutlined,
  HomeOutlined,
  FolderAddOutlined,
  EditOutlined,
  DeleteOutlined,
  UploadOutlined,
  AppstoreOutlined,
  ApartmentOutlined,
  UnorderedListOutlined
} from '@ant-design/icons-vue'
import { message, Modal } from 'ant-design-vue'
import TreeNode from './TreeNode.vue'
import CytoscapeComponent from './CytoscapeComponent.vue'

defineOptions({
  name: 'FolderTree'
})

const emit = defineEmits(['node-select'])

// 查看模式：folder（文件夹）、list（实体列表）、graph（图谱）
const viewMode = ref<'folder' | 'list' | 'graph'>('folder')

// 当前路径和当前节点
const currentPath = ref<string>('')
const currentNodeId = ref<number | null>(null) // 当前所在节点的 ID
const selectedKey = ref<string>('')

// 路径历史记录（用于面包屑导航）
interface PathHistory {
  id: number | null
  name: string
  path: string
}
const pathHistory = ref<PathHistory[]>([])

// 新建文件夹相关状态
const isCreatingFolder = ref<boolean>(false)
const newFolderName = ref<string>('')
const newFolderInput = ref<any>(null)

// 右键菜单相关状态
const contextMenuVisible = ref<boolean>(false)
const contextMenuX = ref<number>(0)
const contextMenuY = ref<number>(0)
const contextMenuTarget = ref<any>(null)

// 重命名相关状态
const isRenaming = ref<boolean>(false)
const renamingItemKey = ref<string>('')
const renameInput = ref<string>('')
const renameInputRef = ref<any>(null)

// 当前文件夹数据
const currentFolders = ref<any[]>([])
const currentFiles = ref<any[]>([])
const loading = ref<boolean>(false)

// 实体列表相关状态
const entityTreeData = ref<any[]>([])
const loadingEntities = ref<boolean>(false)
const expandedNodes = ref<Set<number>>(new Set())
const selectedEntityId = ref<number | null>(null)
const nodeMap = ref<Map<number, any>>(new Map())

// 图谱相关状态
const graphNodes = ref<any[]>([])
const graphEdges = ref<any[]>([])
const loadingGraph = ref<boolean>(false)

// 获取文件夹列表（根据节点 ID）
const loadFolderList = async (parentId: number | null = null) => {
  loading.value = true
  try {
    console.log('🗂️ 开始加载文件夹列表，父节点 ID:', parentId === null ? '根节点' : parentId)

    // 构建 URL：不传参数获取根节点，传 parent_id 获取子节点
    const url = parentId === null
      ? '/python/api/document_system/folder/list'
      : `/python/api/document_system/folder/list?parent_id=${parentId}`

    const response = await fetch(url)
    if (!response.ok) {
      throw new Error(`加载失败: ${response.statusText}`)
    }

    const result = await response.json()
    console.log('📡 API 返回数据:', result)

    if (result.success && result.data && result.data.dataList) {
      const dataList = result.data.dataList

      // 分离文件夹和文件：使用 type 字段判断
      currentFolders.value = dataList.filter((item: any) => item.type === 'folder')
      currentFiles.value = dataList.filter((item: any) => item.type === 'file')

      console.log(`✅ 加载成功: ${currentFolders.value.length} 个文件夹, ${currentFiles.value.length} 个文件`)
    } else {
      throw new Error(result.errMsg || '数据格式错误')
    }
  } catch (error) {
    console.error('❌ 加载文件夹列表失败:', error)
    message.error('加载文件夹列表失败')
    currentFolders.value = []
    currentFiles.value = []
  } finally {
    loading.value = false
  }
}

// 当前路径的路径片段（基于路径历史）
const pathSegments = computed(() => {
  return pathHistory.value.slice(1).map(h => h.name) // 排除根目录
})

// 当前文件夹的内容（文件夹 + 文件）
const currentItems = computed(() => {
  const items = [
    ...currentFolders.value.map(folder => ({
      key: `folder_${folder.id}`,
      title: folder.name,
      isFolder: true,
      path: folder.path,
      data: folder
    })),
    ...currentFiles.value.map(file => ({
      key: `file_${file.id}`,
      title: file.name,
      isFolder: false,
      path: file.path,
      page: file.page,
      data: file
    }))
  ]

  return items
})

// 导航到指定节点（通过面包屑）
const navigateToNode = (nodeId: number | null, nodeName: string) => {
  console.log('🚀 导航到节点:', nodeId, nodeName)

  currentNodeId.value = nodeId
  selectedKey.value = ''

  // 更新路径历史：找到目标节点在历史中的位置，截断后续的
  const targetIndex = pathHistory.value.findIndex(h => h.id === nodeId)
  if (targetIndex >= 0) {
    pathHistory.value = pathHistory.value.slice(0, targetIndex + 1)
  }

  // 保存当前文件夹 ID 到 localStorage
  if (nodeId === null) {
    localStorage.removeItem('document_system_current_folder_id')
  } else {
    localStorage.setItem('document_system_current_folder_id', String(nodeId))
  }

  loadFolderList(nodeId)
}

// 单击项目
const handleItemClick = (item: FolderNode) => {
  selectedKey.value = item.key
}

// 双击项目
const handleItemDoubleClick = (item: any) => {
  console.log('🖱️ 双击项目:', item)
  console.log('  - isFolder:', item.isFolder)
  console.log('  - data:', item.data)

  if (item.isFolder) {
    // 双击文件夹，进入该文件夹
    console.log('📂 进入文件夹:', item.data.name, 'ID:', item.data.id)

    // 添加到路径历史
    pathHistory.value.push({
      id: item.data.id,
      name: item.data.name,
      path: item.data.path
    })

    currentNodeId.value = item.data.id

    // 保存当前文件夹 ID 到 localStorage
    localStorage.setItem('document_system_current_folder_id', String(item.data.id))

    loadFolderList(item.data.id)
  } else {
    // 双击文件，触发选择事件
    console.log('📄 打开文件')
    emit('node-select', item.data)
  }
}

// 开始创建文件夹
const startCreateFolder = () => {
  isCreatingFolder.value = true
  newFolderName.value = ''
  nextTick(() => {
    newFolderInput.value?.focus()
  })
}

// 确认创建文件夹
const confirmCreateFolder = async () => {
  const folderName = newFolderName.value.trim()

  if (!folderName) {
    message.warning('文件夹名称不能为空')
    return
  }

  try {
    console.log('📁 开始创建文件夹:', folderName, '父节点 ID:', currentNodeId.value)

    // 构建请求体：根节点不传 parent_id，子节点传 parent_id
    const requestBody: any = {
      name: folderName
    }

    if (currentNodeId.value !== null) {
      requestBody.parent_id = currentNodeId.value
    }

    console.log('📡 请求体:', requestBody)

    const response = await fetch('/python/api/document_system/folder/create', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(requestBody)
    })

    const result = await response.json()
    console.log('📡 创建文件夹 API 返回:', result)

    if (result.success) {
      message.success('文件夹创建成功')
      // 重新加载当前文件夹列表
      await loadFolderList(currentNodeId.value)
    } else {
      throw new Error(result.errMsg || '创建失败')
    }
  } catch (error: any) {
    console.error('❌ 创建文件夹失败:', error)
    message.error(error.message || '创建文件夹失败')
  } finally {
    // 重置状态
    isCreatingFolder.value = false
    newFolderName.value = ''
  }
}

// 取消创建文件夹
const cancelCreateFolder = () => {
  isCreatingFolder.value = false
  newFolderName.value = ''
}

// 显示右键菜单
const handleContextMenu = (event: MouseEvent, item: any) => {
  console.log('🖱️ 右键点击:', item)

  contextMenuX.value = event.clientX
  contextMenuY.value = event.clientY
  contextMenuTarget.value = item
  contextMenuVisible.value = true
}

// 处理重命名点击
const handleRenameClick = () => {
  contextMenuVisible.value = false
  startRename()
}

// 处理删除点击
const handleDeleteClick = () => {
  contextMenuVisible.value = false
  confirmDelete()
}

// 开始重命名
const startRename = () => {
  if (!contextMenuTarget.value) return

  console.log('✏️ 开始重命名:', contextMenuTarget.value)

  isRenaming.value = true
  renamingItemKey.value = contextMenuTarget.value.key
  renameInput.value = contextMenuTarget.value.title

  nextTick(() => {
    renameInputRef.value?.focus()
    renameInputRef.value?.select()
  })
}

// 确认重命名
const confirmRename = async () => {
  const newName = renameInput.value.trim()

  if (!newName) {
    message.warning('名称不能为空')
    return
  }

  if (newName === contextMenuTarget.value?.title) {
    // 名称没有变化，直接取消
    cancelRename()
    return
  }

  try {
    console.log('✏️ 确认重命名:', contextMenuTarget.value?.data.id, '→', newName)

    const response = await fetch('/python/api/document_system/folder/update', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        id: contextMenuTarget.value.data.id,
        name: newName
      })
    })

    const result = await response.json()
    console.log('📡 重命名 API 返回:', result)

    if (result.success) {
      message.success('重命名成功')
      // 重新加载当前文件夹列表
      await loadFolderList(currentNodeId.value)
    } else {
      throw new Error(result.errMsg || '重命名失败')
    }
  } catch (error: any) {
    console.error('❌ 重命名失败:', error)
    message.error(error.message || '重命名失败')
  } finally {
    cancelRename()
  }
}

// 取消重命名
const cancelRename = () => {
  isRenaming.value = false
  renamingItemKey.value = ''
  renameInput.value = ''
}

// 确认删除
const confirmDelete = () => {
  if (!contextMenuTarget.value) return

  const itemType = contextMenuTarget.value.isFolder ? '文件夹' : '文件'

  Modal.confirm({
    title: '确认删除',
    content: `确定要删除${itemType}"${contextMenuTarget.value.title}"吗？此操作不可恢复。`,
    okText: '删除',
    okType: 'danger',
    cancelText: '取消',
    onOk: async () => {
      await handleDelete()
    }
  })
}

// 执行删除
const handleDelete = async () => {
  try {
    const itemType = contextMenuTarget.value.isFolder ? '文件夹' : '文件'
    console.log('🗑️ 删除' + itemType + ':', contextMenuTarget.value?.data.id)

    const response = await fetch(`/python/api/document_system/folder/delete/${contextMenuTarget.value.data.id}`, {
      method: 'DELETE'
    })

    const result = await response.json()
    console.log('📡 删除 API 返回:', result)

    if (result.success) {
      message.success('删除成功')
      // 重新加载当前文件夹列表
      await loadFolderList(currentNodeId.value)
    } else {
      throw new Error(result.errMsg || '删除失败')
    }
  } catch (error: any) {
    console.error('❌ 删除失败:', error)
    message.error(error.message || '删除失败')
  }
}

// 上传前验证
const handleBeforeUpload = (file: File) => {
  console.log('📤 准备上传文件:', file.name)
  return true
}

// 自定义上传
const handleFileUpload = async (options: any) => {
  const { file } = options

  try {
    console.log('📤 开始上传文件:', file.name, '到文件夹 ID:', currentNodeId.value)

    const formData = new FormData()
    formData.append('file', file)
    if (currentNodeId.value !== null) {
      formData.append('parent_id', String(currentNodeId.value))
    }

    const response = await fetch('/python/api/document_system/file/upload', {
      method: 'POST',
      body: formData
    })

    const result = await response.json()
    console.log('📡 上传 API 返回:', result)

    if (result.success) {
      message.success(`${file.name} 上传成功`)
      await loadFolderList(currentNodeId.value)
    } else {
      throw new Error(result.errMsg || '上传失败')
    }
  } catch (error: any) {
    console.error('❌ 上传失败:', error)
    message.error(`${file.name} 上传失败`)
  }
}

// 转换实体数据格式：适配 TreeNode 组件所需格式
const transformEntityData = (nodes: any[]): any[] => {
  return nodes.map(node => {
    // 根据 type 决定显示文本（适配器模式：将不同字段适配到 text）
    let displayText = ''
    if (node.type === 'attribute') {
      // attribute 类型：取 metadata.document_name
      displayText = node.metadata?.document_name || node.label || ''
    } else {
      // 其他类型（label、aggregate 等）：显示 label
      displayText = node.label || node.text || node.name || node.title || ''
    }

    const transformed: any = {
      ...node,
      // TreeNode 需要的字段
      text: displayText,
      title: displayText,
      line_id: node.line_id || node.id,
      pid: node.pid || node.parent_id,
      // 保留原始字段
      label: node.label,
      label_node_entity: node.label_node_entity,
      type: node.type,
      id: node.id || node.line_id
    }

    // 递归转换子节点
    if (node.children && Array.isArray(node.children) && node.children.length > 0) {
      transformed.children = transformEntityData(node.children)
    }

    return transformed
  })
}

// 加载实体列表
const loadEntityList = async (folderId: number | null = null) => {
  if (folderId === null) {
    entityTreeData.value = []
    return
  }

  loadingEntities.value = true
  try {
    console.log('📊 开始加载实体列表，文件夹 ID:', folderId)

    const response = await fetch(`/python/api/document_system/folder/entity?folder_id=${folderId}`)
    const result = await response.json()

    console.log('📡 实体列表 API 返回:', result)

    if (result.success && result.data && result.data.dataList) {
      const rawData = result.data.dataList

      // 转换数据格式：将 label 字段转换为 text 字段
      const treeData = transformEntityData(rawData)

      entityTreeData.value = treeData
      // 构建 nodeMap
      buildNodeMap(treeData)
      console.log('✅ 实体列表加载成功，节点数量:', treeData.length)
    } else {
      throw new Error(result.errMsg || '加载失败')
    }
  } catch (error) {
    console.error('❌ 加载实体列表失败:', error)
    message.error('加载实体列表失败')
    entityTreeData.value = []
  } finally {
    loadingEntities.value = false
  }
}

// 构建节点映射
const buildNodeMap = (nodes: any[]) => {
  nodeMap.value.clear()
  const traverse = (nodeList: any[]) => {
    nodeList.forEach(node => {
      if (node.line_id) {
        nodeMap.value.set(node.line_id, node)
      }
      if (node.children && node.children.length > 0) {
        traverse(node.children)
      }
    })
  }
  traverse(nodes)
}

// 处理树节点展开/折叠
const handleToggle = (lineId: number) => {
  if (expandedNodes.value.has(lineId)) {
    expandedNodes.value.delete(lineId)
  } else {
    expandedNodes.value.add(lineId)
  }
}

// 处理实体选择
const handleEntitySelect = (lineId: number) => {
  selectedEntityId.value = lineId
  const node = nodeMap.value.get(lineId)
  if (node) {
    emit('node-select', node)
  }
}

// 加载图谱数据（始终使用固定的 folder_id=1）
const loadGraphData = async () => {
  loadingGraph.value = true
  try {
    console.log('📊 开始加载图谱数据')

    const response = await fetch('/python/api/document_system/folder/graph?folder_id=1')
    const result = await response.json()

    console.log('📡 图谱数据 API 返回:', result)

    if (result.success && result.data && result.data.elements) {
      // API 返回的格式是 { elements: { nodes: [{ data: {...} }], edges: [{ data: {...} }] } }
      // 需要提取 data 字段
      const nodesData = result.data.elements.nodes || []
      const edgesData = result.data.elements.edges || []

      graphNodes.value = nodesData.map((n: any) => n.data)
      graphEdges.value = edgesData.map((e: any) => e.data)

      console.log('✅ 图谱数据加载成功，节点:', graphNodes.value.length, '边:', graphEdges.value.length)
    } else {
      throw new Error(result.errMsg || '加载失败')
    }
  } catch (error) {
    console.error('❌ 加载图谱数据失败:', error)
    message.error('加载图谱数据失败')
    graphNodes.value = []
    graphEdges.value = []
  } finally {
    loadingGraph.value = false
  }
}

// 监听 viewMode 变化
watch(viewMode, (newMode) => {
  console.log('🔄 切换查看模式:', newMode)
  if (newMode === 'list') {
    // 切换到实体列表时加载数据
    loadEntityList(currentNodeId.value)
  } else if (newMode === 'graph') {
    // 切换到图谱时加载数据（固定使用 folder_id=1）
    loadGraphData()
  }
})

// 监听 currentNodeId 变化，只在实体列表模式下重新加载数据
watch(currentNodeId, (newId) => {
  if (viewMode.value === 'list') {
    loadEntityList(newId)
  }
  // 图谱模式不需要监听文件夹变化，始终使用固定数据
})

// 根据完整路径重建面包屑
const rebuildPathHistory = (fullPath: string, currentId: number) => {
  console.log('🔨 重建面包屑路径:', fullPath)

  // 初始化为根目录
  pathHistory.value = [{
    id: null,
    name: '根目录',
    path: ''
  }]

  // 解析路径：路径格式为 "深圳市交易集团/光明区/深圳理工大学/文件名"
  if (!fullPath || fullPath.trim() === '') {
    return
  }

  const pathParts = fullPath.split('/').filter(p => p.trim() !== '')

  // 注意：我们无法从路径字符串中获取每个节点的 ID
  // 所以这里除了当前节点外，其他节点的 ID 都设为 null
  // 这意味着面包屑中只有"根目录"和"当前文件夹"可以点击跳转

  // 添加所有路径层级（除了最后一个，因为最后一个是文件名）
  let accumulatedPath = ''
  for (let i = 0; i < pathParts.length - 1; i++) {
    const partName = pathParts[i]
    accumulatedPath += (accumulatedPath ? '/' : '') + partName

    // 只有当前文件夹才有 ID，其他层级暂时设为 null
    const isCurrentFolder = (i === pathParts.length - 2)
    pathHistory.value.push({
      id: isCurrentFolder ? currentId : null,
      name: partName,
      path: accumulatedPath
    })
  }

  console.log('📍 重建后的路径历史:', pathHistory.value)
}

// 根据 ID 加载文件夹并重建路径
const loadFolderById = async (folderId: number) => {
  try {
    console.log('🔍 根据 ID 加载文件夹:', folderId)

    // 加载该文件夹的内容
    currentNodeId.value = folderId
    const response = await fetch(`/python/api/document_system/folder/list?parent_id=${folderId}`)
    const result = await response.json()

    if (result.success && result.data && result.data.dataList) {
      const dataList = result.data.dataList

      // 分离文件夹和文件
      currentFolders.value = dataList.filter((item: any) => item.type === 'folder')
      currentFiles.value = dataList.filter((item: any) => item.type === 'file')

      console.log(`✅ 加载成功: ${currentFolders.value.length} 个文件夹, ${currentFiles.value.length} 个文件`)

      // 尝试从返回的数据中获取路径信息来重建面包屑
      // 方案：查找第一个有 path 的项目，从中提取完整路径
      const firstItem = dataList[0]
      if (firstItem && firstItem.path) {
        // path 格式: "深圳市交易集团/光明区/深圳理工大学/test.pdf"
        // 提取完整路径包含当前文件夹
        rebuildPathHistory(firstItem.path, folderId)
      } else {
        console.log('⚠️ 无法从数据中获取路径信息，只显示当前节点')
        // 如果没有路径信息，只显示当前节点
        pathHistory.value.push({
          id: folderId,
          name: '当前文件夹',
          path: ''
        })
      }
    } else {
      throw new Error(result.errMsg || '数据格式错误')
    }
  } catch (error) {
    console.error('❌ 根据 ID 加载文件夹失败:', error)
    // 失败时回到根目录
    currentNodeId.value = null
    await loadFolderList(null)
  }
}

// 组件挂载时加载根目录或恢复上次位置
onMounted(async () => {
  console.log('🚀 组件挂载')

  // 初始化路径历史为根目录
  pathHistory.value = [{
    id: null,
    name: '根目录',
    path: ''
  }]

  // 检查 localStorage 中是否有保存的文件夹 ID
  const savedFolderId = localStorage.getItem('document_system_current_folder_id')

  if (savedFolderId) {
    const folderId = parseInt(savedFolderId, 10)
    console.log('📌 恢复上次访问的文件夹 ID:', folderId)
    await loadFolderById(folderId)
  } else {
    console.log('📂 加载根目录')
    await loadFolderList(null)
  }
})
</script>

<style lang="scss" scoped>
.folder-explorer-container {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #fff;

  .address-bar {
    padding: 12px 16px;
    border-bottom: 1px solid #e8e8e8;
    background: #fafafa;

    :deep(.ant-breadcrumb) {
      font-size: 14px;

      a {
        color: #1890ff;
        text-decoration: none;

        &:hover {
          color: #40a9ff;
          text-decoration: underline;
        }
      }

      .path-text {
        color: rgba(0, 0, 0, 0.45);
        cursor: default;
      }
    }
  }

  .toolbar-bar {
    padding: 8px 16px;
    border-bottom: 1px solid #e8e8e8;
    background: #fff;
    display: flex;
    align-items: center;
    justify-content: space-between;

    .toolbar-left {
      display: flex;
      gap: 4px;
    }

    .toolbar-right {
      display: flex;
      gap: 8px;
      align-items: center;
    }
  }

  .entity-list {
    flex: 1;
    overflow-y: auto;
    padding: 16px;
    background: #fff;

    .tree-container {
      max-width: 1200px;
      margin: 0 auto;
    }
  }

  .graph-view {
    flex: 1;
    display: flex;
    flex-direction: column;
    background: #fafafa;
    position: relative;

    .graph-container {
      flex: 1;
      width: 100%;
      height: 100%;
      position: relative;
    }

    :deep(.ant-spin-nested-loading),
    :deep(.ant-spin-container) {
      height: 100%;
    }
  }

  .file-list {
    flex: 1;
    overflow-y: auto;
    padding: 16px;

    .items-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
      gap: 16px;

      .file-item {
        display: flex;
        flex-direction: column;
        align-items: center;
        padding: 12px;
        border-radius: 4px;
        cursor: pointer;
        transition: all 0.2s;

        &:hover {
          background-color: #f5f5f5;
        }

        &.selected {
          background-color: #e6f7ff;
          border: 1px solid #91d5ff;
        }

        &.creating {
          cursor: default;
          border: 1px solid #1890ff;
          background-color: #f0f5ff;

          &:hover {
            background-color: #f0f5ff;
          }
        }

        &.renaming {
          border: 1px solid #1890ff;
          background-color: #f0f5ff;
        }

        .item-icon {
          margin-bottom: 8px;
        }

        .item-name {
          font-size: 12px;
          text-align: center;
          word-break: break-all;
          max-width: 100%;
          overflow: hidden;
          text-overflow: ellipsis;
          display: -webkit-box;
          -webkit-line-clamp: 2;
          -webkit-box-orient: vertical;
          line-height: 1.4;
        }

        .folder-name-input,
        .rename-input {
          width: 100%;
          text-align: center;
        }

        .item-info {
          margin-top: 4px;
          font-size: 11px;
          color: #999;
        }
      }
    }
  }
}

// 右键菜单样式
.context-menu-mask {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 1000;
  background: transparent;
}

.context-menu {
  position: fixed;
  z-index: 1001;
  background: #fff;
  border-radius: 4px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  padding: 4px 0;
  min-width: 120px;

  .menu-item {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 16px;
    cursor: pointer;
    transition: all 0.2s;
    color: rgba(0, 0, 0, 0.85);
    font-size: 14px;
    white-space: nowrap;

    &:hover {
      background-color: #f5f5f5;
    }

    &.danger {
      color: #ff4d4f;

      &:hover {
        background-color: #fff1f0;
      }
    }

    span {
      flex: 1;
    }
  }
}
</style>
