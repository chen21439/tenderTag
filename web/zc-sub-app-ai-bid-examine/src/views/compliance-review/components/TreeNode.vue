<template>
  <div
    class="tree-node"
    @dragover.prevent="handleDragOver"
    @dragleave="handleDragLeave"
    @drop="handleDrop"
  >
    <div
      class="node-header"
      :class="{
        'selected': selectedId === node.line_id || selectedIds.includes(node.line_id),
        'highlighted-equality': highlightedNodes.has(node.id) || highlightedNodes.has(node.line_id),
        [`depth-${Math.min(depth, 6)}`]: true,
        [`class-${node.class}`]: true,
        'is-meta': node.is_meta,
        'edit-mode': editMode,
        'drag-over': isDragOver
      }"
      :draggable="editMode"
      @click="handleHeaderClick"
      @mousedown="handleMouseDown"
      @mouseup="handleMouseUp"
      @dragstart="handleDragStart"
      @dragend="handleDragEnd"
      @dragover.prevent="handleDragOver"
      @drop="handleDrop"
      @contextmenu.prevent="handleContextMenu"
    >
      <!-- 编辑模式下的多选checkbox -->
      <input
        v-if="editMode"
        type="checkbox"
        class="node-checkbox"
        :checked="selectedIds.includes(node.line_id)"
        @click.stop="handleCheckboxClick"
        @mousedown.stop
        @mouseup.stop
      />

      <!-- 展开/折叠图标 -->
      <span
        v-if="hasAnyRelations"
        class="toggle-icon"
        @click.stop="handleToggle"
      >
        {{ isExpanded ? '▼' : '▶' }}
      </span>
      <span v-else class="toggle-icon placeholder"></span>

      <!-- 节点类型图标已移除 -->

      <!-- 节点标签 -->
      <span class="node-label">
        <!-- 类型标签 -->
        <span v-if="node.type === 'label'" class="type-badge type-label">业务本体</span>
        <span v-else-if="node.type === 'aggregate'" class="type-badge type-aggregate">业务实体</span>

        <!-- 标签节点显示标签名称，不显示前缀 -->
        <span v-if="node.text || node.title" class="node-text">{{ truncateText(node.text || node.title) }}</span>
        <span v-else class="node-id">#{{ node.line_id || node.pid }}</span>

        <!-- 调试模式下显示标签层级信息 -->
        <span v-if="debugMode && node.class === 'label-group'" class="label-prefix label-level-1">一级</span>
        <span v-else-if="debugMode && node.class === 'label-group-2'" class="label-prefix label-level-2">二级</span>
      </span>

      <!-- 只显示 Equality 平级关系 -->
      <span v-if="node.relation === 'equality' && node.parent_id"
            class="equality-indicator"
            :title="`与节点 ${node.parent_id} 平级`">
        <span class="equality-line">━━</span>
        <span class="equality-label">⚖</span>
        <span class="equality-target">#{{ node.parent_id }}</span>
      </span>

      <!-- Level 标记 -->
      <span v-if="node.level !== undefined" class="level-badge">
        L{{ node.level }}
      </span>

      <!-- 页码标记 -->
      <span v-if="node.page !== undefined" class="page-badge">
        P{{ node.page }}
      </span>

      <!-- Class 类型标记 -->
      <span v-if="node.class" class="class-badge" :class="`class-${node.class.toLowerCase()}`">
        {{ node.class }}
      </span>

      <!-- ID 显示（兼容 id 和 line_id） -->
      <span v-if="node.id !== undefined || node.line_id !== undefined" class="id-badge">
        ID:{{ node.id !== undefined ? node.id : node.line_id }}
      </span>

      <!-- Parent ID 显示 -->
      <span v-if="node.parent_id !== undefined && node.parent_id !== null && node.parent_id !== ''" class="parent-id-badge">
        P:{{ node.parent_id }}
      </span>

      <!-- 标签显示 -->
      <span v-if="node.label && node.label.trim()" class="label-tag">
        {{ node.label }}
      </span>
    </div>

    <!-- 右键菜单 -->
    <div
      v-if="showContextMenu"
      class="context-menu"
      :style="{ top: contextMenuY + 'px', left: contextMenuX + 'px' }"
      @click.stop
    >
      <div class="context-menu-item" @click="handleEditRelation">
        编辑关系
      </div>
    </div>

    <!-- Relation 编辑模态框 -->
    <div v-if="showRelationModal" class="label-modal-overlay" @click.stop="closeRelationModal">
      <div class="label-modal" @click.stop>
        <div class="label-modal-header">
          <span>编辑节点关系</span>
          <span class="close-btn" @click="closeRelationModal">×</span>
        </div>
        <div class="label-modal-body">
          <div class="form-group">
            <label>元素类型 (class):</label>
            <select
              v-model="editingClass"
              class="class-select"
            >
              <option value="section">section</option>
              <option value="fstline">fstline</option>
              <option value="para">para</option>
              <option value="table">table</option>
              <option value="title">title</option>
              <option value="caption">caption</option>
            </select>
          </div>
          <div class="form-group">
            <label>关系类型:</label>
            <select
              ref="relationSelectRef"
              v-model="editingRelation"
              class="relation-select"
            >
              <option value="">无关系</option>
              <option value="connect">connect</option>
              <option value="equality">equality</option>
              <option value="contain">contain</option>
            </select>
          </div>
          <div class="form-group">
            <label>父节点 ID:</label>
            <input
              type="number"
              v-model="editingParentId"
              class="parent-id-input"
              placeholder="输入父节点 ID"
            />
          </div>
        </div>
        <div class="label-modal-footer">
          <button class="btn-cancel" @click="closeRelationModal">取消</button>
          <button class="btn-save" @click="saveRelationEdit">保存</button>
        </div>
      </div>
    </div>

    <!-- 子节点和段落列表 -->
    <div v-if="isExpanded" class="node-content">
      <!-- 调试信息（仅调试模式） -->
      <div v-if="debugMode" style="color: red; font-size: 12px; padding: 4px; background: #fff3cd; display: none;">
        Debug: isExpanded={{ isExpanded }},
        has child_line_ids={{ !!node.child_line_ids }},
        count={{ node.child_line_ids?.length || 0 }},
        line_id={{ node.line_id }}
      </div>

      <!-- 段落列表（仅调试模式） -->
      <div v-if="debugMode && node.child_line_ids && node.child_line_ids.length > 0" class="paragraph-list">
        <div
          v-for="(paragraphIds, index) in node.child_line_ids"
          :key="`para-${index}`"
          class="paragraph-item"
          @click.stop="handleParagraphClick(paragraphIds)"
        >
          <span class="paragraph-icon">📄</span>
          <span class="paragraph-text">{{ getParagraphText(paragraphIds) }}</span>
        </div>
      </div>

      <!-- 子节点 (contain 关系) -->
      <div v-if="hasChildren" class="children">
        <TreeNode
          v-for="child in node.children"
          :key="child.line_id"
          :node="child"
          :depth="depth + 1"
          :expanded-nodes="expandedNodes"
          :selected-id="selectedId"
          :selected-ids="selectedIds"
          :highlighted-nodes="highlightedNodes"
          :node-map="nodeMap"
          :debug-mode="debugMode"
          :edit-mode="editMode"
          @toggle="$emit('toggle', $event)"
          @select="$emit('select', $event)"
          @paragraphClick="$emit('paragraphClick', $event)"
          @node-drop="$emit('node-drop', $event)"
          @drag-over-node="$emit('drag-over-node', $event)"
          @drag-end="$emit('drag-end', $event)"
          @drag-start-node="$emit('drag-start-node', $event)"
          @update-label="$emit('update-label', $event)"
          @update-relation="$emit('update-relation', $event)"
        />
      </div>

      <!-- 平级节点 (equality 关系) -->
      <div v-if="hasSiblings" class="siblings">
        <div class="relation-group-label">⚖️ 平级关系</div>
        <TreeNode
          v-for="sibling in node.siblings"
          :key="sibling.line_id"
          :node="sibling"
          :depth="depth + 1"
          :expanded-nodes="expandedNodes"
          :selected-id="selectedId"
          :selected-ids="selectedIds"
          :node-map="nodeMap"
          :debug-mode="debugMode"
          :edit-mode="editMode"
          @toggle="$emit('toggle', $event)"
          @select="$emit('select', $event)"
          @paragraphClick="$emit('paragraphClick', $event)"
          @node-drop="$emit('node-drop', $event)"
          @drag-over-node="$emit('drag-over-node', $event)"
          @drag-end="$emit('drag-end', $event)"
          @drag-start-node="$emit('drag-start-node', $event)"
          @update-label="$emit('update-label', $event)"
          @update-relation="$emit('update-relation', $event)"
        />
      </div>

      <!-- 连接节点 (connect 关系) -->
      <div v-if="hasConnectedNodes" class="connected-nodes">
        <div class="relation-group-label">🔗 连接关系</div>
        <TreeNode
          v-for="connectedNode in node.connectedNodes"
          :key="connectedNode.line_id"
          :node="connectedNode"
          :depth="depth + 1"
          :expanded-nodes="expandedNodes"
          :selected-id="selectedId"
          :selected-ids="selectedIds"
          :node-map="nodeMap"
          :debug-mode="debugMode"
          :edit-mode="editMode"
          @toggle="$emit('toggle', $event)"
          @select="$emit('select', $event)"
          @paragraphClick="$emit('paragraphClick', $event)"
          @node-drop="$emit('node-drop', $event)"
          @drag-over-node="$emit('drag-over-node', $event)"
          @drag-end="$emit('drag-end', $event)"
          @drag-start-node="$emit('drag-start-node', $event)"
          @update-label="$emit('update-label', $event)"
          @update-relation="$emit('update-relation', $event)"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, nextTick } from 'vue'

const props = defineProps({
  node: {
    type: Object,
    required: true
  },
  depth: {
    type: Number,
    default: 0
  },
  expandedNodes: {
    type: Set,
    required: true
  },
  selectedId: {
    type: Number,
    default: null
  },
  selectedIds: {
    type: Array as () => number[],
    default: () => []
  },
  highlightedNodes: {
    type: Set,
    default: () => new Set()
  },
  nodeMap: {
    type: Object,
    default: () => ({})
  },
  debugMode: {
    type: Boolean,
    default: false
  },
  editMode: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['toggle', 'select', 'paragraphClick', 'node-drop', 'drag-over-node', 'drag-end', 'drag-start-node', 'update-label', 'update-relation'])

// 拖拽状态
const isDragOver = ref(false)

// 右键菜单状态
const showContextMenu = ref(false)
const contextMenuX = ref(0)
const contextMenuY = ref(0)

// Relation 编辑状态
const showRelationModal = ref(false)
const editingClass = ref('')
const editingRelation = ref('')
const editingParentId = ref<number | ''>('')
const relationSelectRef = ref<HTMLSelectElement | null>(null)
let isDraggingNow = false
let mouseDownTime = Date.now() // 初始化为当前时间，避免计算错误

// 是否有子节点
const hasChildren = computed(() => {
  return props.node.children && props.node.children.length > 0
})

// 是否有平级节点 (equality)
const hasSiblings = computed(() => {
  return props.node.siblings && props.node.siblings.length > 0
})

// 是否有连接节点 (connect)
const hasConnectedNodes = computed(() => {
  return props.node.connectedNodes && props.node.connectedNodes.length > 0
})

// 是否有任意关系节点（用于显示展开/折叠图标）
const hasAnyRelations = computed(() => {
  return hasChildren.value || hasSiblings.value || hasConnectedNodes.value
})

// 是否展开
const isExpanded = computed(() => {
  return props.expandedNodes.has(props.node.line_id)
})

// 处理展开/折叠
const handleToggle = () => {
  emit('toggle', props.node.line_id)
}

// 处理checkbox点击
const handleCheckboxClick = (event: MouseEvent) => {
  // 阻止所有事件传播
  event.stopPropagation()
  event.preventDefault()

  // 触发选择事件，让父组件处理多选逻辑
  emit('select', props.node.line_id, { ctrlKey: true } as MouseEvent)
}

// Header点击事件
const handleHeaderClick = (event: MouseEvent) => {
  console.log('🎯 header点击:', props.node.line_id, 'editMode:', props.editMode, 'type:', props.node.type, 'ctrlKey:', event.ctrlKey, 'metaKey:', event.metaKey)

  // 在非编辑模式下，直接触发选择
  if (!props.editMode) {
    console.log('✅ 非编辑模式，触发选择')
    emit('select', props.node.line_id, event)

    // 如果是业务本体节点（type === 'label'），同时触发展开/折叠
    if (props.node.type === 'label' && hasChildren.value) {
      console.log('🔄 业务本体节点，触发展开/折叠')
      emit('toggle', props.node.line_id)
    }
  }
  // 编辑模式下，由mouseUp处理
}

// 鼠标按下
const handleMouseDown = (event: MouseEvent) => {
  console.log('🖱️ mouseDown:', props.node.line_id, 'editMode:', props.editMode)
  mouseDownTime = Date.now()
  isDraggingNow = false
}

// 鼠标抬起
const handleMouseUp = (event: MouseEvent) => {
  const clickDuration = Date.now() - mouseDownTime
  console.log('🖱️ mouseUp:', {
    nodeId: props.node.line_id,
    editMode: props.editMode,
    isDraggingNow,
    clickDuration,
    ctrlKey: event.ctrlKey,
    metaKey: event.metaKey
  })

  // 编辑模式下才处理
  if (props.editMode) {
    // 如果是快速点击（不是拖拽），触发选择
    if (!isDraggingNow && clickDuration < 200) {
      console.log('✅ 编辑模式-快速点击，触发选择事件')
      emit('select', props.node.line_id, event)
    } else {
      console.log('⚠️ 编辑模式-跳过选择事件', { isDraggingNow, clickDuration })
    }
  }

  isDraggingNow = false
}

// 处理段落点击
const handleParagraphClick = (paragraphIds: number[]) => {
  emit('paragraphClick', paragraphIds)
}

// 拖拽开始
const handleDragStart = (event: DragEvent) => {
  console.log('🎯 dragStart事件触发:', {
    nodeId: props.node.id,
    editMode: props.editMode,
    draggable: event.target?.getAttribute?.('draggable')
  })

  if (!props.editMode) {
    console.log('⚠️ 非编辑模式，阻止拖拽')
    event.preventDefault()
    return
  }

  isDraggingNow = true

  if (event.dataTransfer) {
    event.dataTransfer.effectAllowed = 'move'
    event.dataTransfer.setData('text/plain', String(props.node.id))
  }

  // 通知父组件拖拽开始，传递节点 ID
  emit('drag-start-node', props.node.id)

  console.log('✅ 开始拖拽节点:', props.node.id)
}

// 拖拽结束
const handleDragEnd = (event: DragEvent) => {
  console.log('🎯 dragEnd事件触发:', {
    nodeId: props.node.id,
    editMode: props.editMode
  })

  if (!props.editMode) {
    console.log('⚠️ 非编辑模式，跳过dragEnd处理')
    return
  }

  // dragEnd 只在被拖拽的节点上触发
  // 通知父组件拖拽结束，父组件会检查 lastDragOverNodeId 来决定是否发送API请求
  console.log('✅ 拖拽结束，通知父组件')
  emit('drag-end', props.node.id)

  // 清理状态
  isDragOver.value = false
  isDraggingNow = false
}

const handleDragOver = (event: DragEvent) => {
  if (!props.editMode) return

  event.preventDefault()
  // 先通知父组件，然后阻止冒泡，防止祖父节点也收到事件
  event.stopPropagation()

  if (event.dataTransfer) {
    event.dataTransfer.dropEffect = 'move'
  }

  if (!isDragOver.value) {
    console.log('🎯 dragOver进入节点:', props.node.id, props.node.text || props.node.title)
  }
  isDragOver.value = true

  // 通知父组件记录这个节点
  emit('drag-over-node', props.node.id)
}

const handleDragLeave = (event: DragEvent) => {
  if (!props.editMode) return

  // 阻止冒泡，防止父节点也触发 dragLeave
  event.stopPropagation()
  console.log('🎯 dragLeave离开节点:', props.node.id)
  isDragOver.value = false
}

const handleDrop = (event: DragEvent) => {
  console.log('🔥🔥🔥 DROP事件触发!!! 🔥🔥🔥', {
    editMode: props.editMode,
    nodeId: props.node.id,
    target: event.target,
    currentTarget: event.currentTarget
  })

  if (!props.editMode) {
    console.log('⚠️ 非编辑模式，忽略drop')
    return
  }

  event.preventDefault()
  event.stopPropagation()

  isDragOver.value = false

  const draggedNodeId = event.dataTransfer?.getData('text/plain')
  const targetNodeId = props.node.id

  console.log('📦 drop数据:', {
    draggedNodeId,
    targetNodeId,
    targetNode: props.node.text || props.node.title,
    dataTransfer: event.dataTransfer
  })

  if (draggedNodeId && String(draggedNodeId) !== String(targetNodeId)) {
    console.log('✅ 发送node-drop事件到父组件')
    // 通知父组件处理节点移动
    emit('node-drop', {
      draggedNodeId,
      targetNodeId
    })
  } else {
    console.log('⚠️ 无效的拖拽:', { draggedNodeId, targetNodeId, same: draggedNodeId === targetNodeId })
  }
}

// 获取段落文本缩略
const getParagraphText = (paragraphIds: number[]): string => {
  if (!paragraphIds || paragraphIds.length === 0) return ''

  // 从 nodeMap 中获取段落文本
  const texts: string[] = []
  for (const id of paragraphIds) {
    const node = props.nodeMap[id]
    if (node && (node.text || node.content)) {
      texts.push(node.text || node.content)
    }
  }

  const fullText = texts.join('')
  // 限制显示长度
  return fullText.length > 50 ? fullText.substring(0, 50) + '...' : fullText
}

// 获取节点类型标签
const getNodeClassLabel = (nodeClass: string) => {
  // 将 sec1/sec2/sec3 等转换为 "一级标题"/"二级标题"/"三级标题"
  const match = nodeClass.match(/^sec(\d+)$/i)
  if (match) {
    const levelMap: Record<string, string> = {
      '1': '一级标题',
      '2': '二级标题',
      '3': '三级标题',
      '4': '四级标题',
      '5': '五级标题'
    }
    return levelMap[match[1]] || `${match[1]}级标题`
  }

  const labelMap: Record<string, string> = {
    title: '标题',
    author: '作者',
    affili: '机构',
    mail: '邮箱',
    paragraph: '段落',
    para: '段落',
    fstline: '首行',
    tab: '表格',
    tabcap: '表格标题',
    footer: '页脚',
    toc: '目录',
    toc1: '目录一级',
    toc2: '目录二级',
    'label-group': '标签',
    'label-group-2': '标签',
    'more-indicator': '更多',
    'field-group': '字段组',
    'field-item': '字段'
  }

  return labelMap[nodeClass.toLowerCase()] || nodeClass.toUpperCase()
}

// 获取节点图标
const getNodeIcon = (nodeClass: string) => {
  const iconMap: Record<string, string> = {
    title: '📄',
    author: '👤',
    affili: '🏛️',
    mail: '✉️',
    sec1: '📌',
    sec2: '📍',
    sec3: '📎',
    paragraph: '📝',  // 合并后的段落
    para: '¶',
    fstline: '▸',
    tab: '📊',
    tabcap: '🏷️',
    footer: '📋',  // 页脚
    toc: '📑',  // 目录
    toc1: '📑',  // 目录一级
    toc2: '📑',  // 目录二级
    'label-group': '🏷️',  // 一级标签分组
    'label-group-2': '🏷️',  // 二级标签分组
    'more-indicator': '⋯',  // 查看更多指示器
    'field-group': '📦',  // 字段组
    'field-item': '🔹',  // 字段项
    default: '•'
  }
  return iconMap[nodeClass] || iconMap.default
}

// 获取关系类型标签
const getRelationLabel = (relation: string) => {
  const labelMap: Record<string, string> = {
    contain: '包含',
    equality: '并列',
    connect: '连接',
    meta: '元信息'
  }
  return labelMap[relation] || relation
}

// 获取关系类型图标
const getRelationIcon = (relation: string) => {
  const iconMap: Record<string, string> = {
    contain: '📦',
    equality: '⚖️',
    connect: '🔗',
    meta: 'ℹ️'
  }
  return iconMap[relation] || '•'
}

// 获取关系类型提示
const getRelationTooltip = (node: any) => {
  const relationMap: Record<string, string> = {
    contain: `被节点 ${node.parent_id} 包含`,
    equality: `与节点 ${node.parent_id} 平级`,
    connect: `连接到节点 ${node.parent_id}`,
    meta: '元信息'
  }
  return relationMap[node.relation] || node.relation
}

// 截断文本
const truncateText = (text: string, maxLength = 60) => {
  if (!text) return ''
  text = text.trim().replace(/\s+/g, ' ')
  return text.length > maxLength
    ? text.substring(0, maxLength) + '...'
    : text
}

// 处理右键菜单
const handleContextMenu = (event: MouseEvent) => {
  // 关闭其他可能打开的右键菜单
  document.querySelectorAll('.context-menu').forEach(menu => {
    if (menu !== event.currentTarget) {
      (menu as HTMLElement).style.display = 'none'
    }
  })

  showContextMenu.value = true
  contextMenuX.value = event.clientX
  contextMenuY.value = event.clientY

  // 点击其他地方关闭菜单
  const closeMenu = () => {
    showContextMenu.value = false
    document.removeEventListener('click', closeMenu)
  }
  setTimeout(() => {
    document.addEventListener('click', closeMenu)
  }, 0)
}

// 处理编辑关系
const handleEditRelation = () => {
  showContextMenu.value = false
  editingClass.value = props.node.class || ''
  editingRelation.value = props.node.relation || ''
  editingParentId.value = props.node.parent_id !== undefined && props.node.parent_id !== null && props.node.parent_id !== ''
    ? Number(props.node.parent_id)
    : ''
  showRelationModal.value = true

  // 自动聚焦选择框
  nextTick(() => {
    relationSelectRef.value?.focus()
  })
}

// 关闭关系编辑模态框
const closeRelationModal = () => {
  showRelationModal.value = false
  editingClass.value = ''
  editingRelation.value = ''
  editingParentId.value = ''
}

// 保存关系编辑
const saveRelationEdit = () => {
  const newClass = editingClass.value.trim()
  const newRelation = editingRelation.value.trim()

  console.log('🔍 调试 editingParentId:', {
    raw: editingParentId.value,
    type: typeof editingParentId.value,
    isEmpty: editingParentId.value === '',
    isNull: editingParentId.value === null,
    isUndefined: editingParentId.value === undefined
  })

  // 处理 parent_id: 空值统一为 '', 有值则转为数字
  const newParentId = (editingParentId.value === '' || editingParentId.value === null || editingParentId.value === undefined)
    ? ''
    : Number(editingParentId.value)

  console.log('💾 保存关系:', {
    nodeId: props.node.id,
    oldClass: props.node.class,
    newClass,
    oldRelation: props.node.relation,
    newRelation,
    oldParentId: props.node.parent_id,
    newParentId
  })

  // 通知父组件更新 class、relation 和 parent_id
  emit('update-relation', {
    nodeId: props.node.id,
    class: newClass,
    relation: newRelation,
    parent_id: newParentId
  })

  closeRelationModal()
}
</script>

<style scoped lang="scss">
.tree-node {
  user-select: none;
}

.node-header {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  margin: 2px 0;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
  gap: 8px;
  border-left: 3px solid transparent;

  // 编辑模式下，让文本内容不干扰拖拽事件（但保留toggle-icon的交互）
  &.edit-mode {
    .node-label,
    .relation-badge,
    .level-badge,
    .page-badge,
    .class-badge {
      pointer-events: none;
    }
  }

  &:hover {
    background: #f5f5f5;
  }

  &.selected {
    background: #e3f2fd;
    border-left-color: #1976d2;
    box-shadow: 0 0 0 2px rgba(25, 118, 210, 0.2);
  }

  &.highlighted-equality {
    background: linear-gradient(90deg, #fff9c4 0%, #fffde7 100%);
    border-left: 3px solid #ffd54f;
    box-shadow: 0 0 0 2px rgba(255, 213, 79, 0.3), 0 2px 8px rgba(245, 127, 23, 0.2);
    animation: pulse-equality 2s ease-in-out infinite;
  }

  &.is-meta {
    background: #fafafa;
  }

  &.is-meta.selected {
    background: #f3e5f5;
    border-left-color: #7b1fa2;
  }

  // 编辑模式样式
  &.edit-mode {
    cursor: move;

    &:hover {
      background: #e8f5e9;
      box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
  }

  // 拖拽悬停样式
  &.drag-over {
    background: #c8e6c9;
    outline: 2px dashed #4caf50; // 使用 outline 代替 border，不会改变元素尺寸
    outline-offset: -2px;
    box-shadow: 0 0 8px rgba(76, 175, 80, 0.3);
  }
}

/* 深度缩进 */
.depth-0 { margin-left: 0; }
.depth-1 { margin-left: 20px; }
.depth-2 { margin-left: 40px; }
.depth-3 { margin-left: 60px; }
.depth-4 { margin-left: 80px; }
.depth-5 { margin-left: 100px; }
.depth-6 { margin-left: 120px; }

/* 根据class类型设置样式 */
.node-header.class-title .node-class { color: #1976d2; font-weight: 700; }
.node-header.class-author .node-class { color: #7b1fa2; font-weight: 600; }
.node-header.class-affili .node-class { color: #c2185b; }
.node-header.class-mail .node-class { color: #e65100; }
.node-header.class-sec1 .node-class { color: #c62828; font-weight: 700; font-size: 13px; }
.node-header.class-sec2 .node-class { color: #2e7d32; font-weight: 600; font-size: 12px; }
.node-header.class-sec3 .node-class { color: #00695c; font-weight: 500; font-size: 12px; }
.node-header.class-paragraph .node-class { color: #616161; font-weight: 500; font-size: 12px; }

/* 类型标签样式 */
.type-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 3px;
  font-size: 11px;
  font-weight: 500;
  margin-right: 6px;
  border: 1px solid;
  white-space: nowrap;
  flex-shrink: 0;
}

/* 业务本体 - 蓝色 */
.type-badge.type-label {
  background: #e6f7ff;
  color: #1890ff;
  border-color: #91d5ff;
}

/* 业务实体 - 绿色 */
.type-badge.type-aggregate {
  background: #f6ffed;
  color: #52c41a;
  border-color: #b7eb8f;
}

/* 标签前缀样式 - Tag标签风格 */
.label-prefix {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 3px;
  font-size: 11px;
  font-weight: 500;
  margin-right: 6px;
  border: 1px solid;
}

/* 一级标签 - 蓝色 Tag */
.label-prefix.label-level-1 {
  background: #ecf5ff;
  color: #409eff;
  border-color: #b3d8ff;
}

/* 二级标签 - 绿色 Tag */
.label-prefix.label-level-2 {
  background: #f0f9ff;
  color: #67c23a;
  border-color: #c2e7b0;
}

/* 一级标签节点整体样式 */
.node-header.class-label-group {
  .node-text {
    color: #409eff; /* 一级标签文字蓝色 */
    font-weight: 600;
    font-size: 13px;
  }

  &.selected {
    background: #ecf5ff;
    border-left-color: #409eff;
  }
}

/* 二级标签节点整体样式 */
.node-header.class-label-group-2 {
  .node-text {
    color: #67c23a; /* 二级标签文字绿色 */
    font-weight: 500;
    font-size: 13px;
  }

  &.selected {
    background: #f0f9ff;
    border-left-color: #67c23a;
  }
}

/* "查看更多"指示器样式 */
.node-header.class-more-indicator {
  background: #f5f5f5;
  color: #1976d2;
  font-style: italic;
  padding: 6px 12px;
  border-radius: 4px;
  border-left: 2px solid #1976d2;
  cursor: pointer;

  &:hover {
    background: #e3f2fd;
    color: #1565c0;
  }

  .node-text {
    color: #1976d2;
    font-size: 12px;
  }
}

/* 字段组样式 */
.node-header.class-field-group {
  background: #fff9e6;

  .node-text {
    color: #d46b08;
    font-weight: 600;
    font-size: 12px;
  }

  &.selected {
    background: #fffbe6;
    border-left-color: #faad14;
  }

  &:hover {
    background: #fff7e6;
  }
}

/* 字段项样式 */
.node-header.class-field-item {
  background: #f6ffed;
  padding: 6px 12px;

  .node-text {
    color: #389e0d;
    font-size: 12px;
    font-family: 'Courier New', monospace;
  }

  &.selected {
    background: #f6ffed;
    border-left-color: #52c41a;
  }

  &:hover {
    background: #d9f7be;
  }
}

.node-checkbox {
  width: 16px;
  height: 16px;
  margin-right: 8px;
  cursor: pointer;
  flex-shrink: 0;
  accent-color: #1976d2;
}

.toggle-icon {
  width: 16px;
  font-size: 10px;
  color: #757575;
  flex-shrink: 0;
  text-align: center;
}

.toggle-icon.placeholder {
  visibility: hidden;
}

.node-icon {
  font-size: 16px;
  flex-shrink: 0;
}

.node-label {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.node-class {
  font-weight: 600;
  font-size: 11px;
  text-transform: uppercase;
  flex-shrink: 0;
  letter-spacing: 0.5px;
}

.node-text {
  color: #333;
  font-size: 13px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  line-height: 1.4;
}

.node-id {
  color: #999;
  font-size: 11px;
  font-family: 'Courier New', monospace;
}

.equality-indicator {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px;
  border-radius: 12px;
  background: linear-gradient(135deg, #fff9c4 0%, #fff59d 100%);
  border: 1px solid #ffd54f;
  flex-shrink: 0;
  font-size: 10px;
  font-weight: 600;
  color: #f57f17;
  box-shadow: 0 1px 3px rgba(245, 127, 23, 0.15);
  cursor: help;
  transition: all 0.2s;
}

.equality-indicator:hover {
  background: linear-gradient(135deg, #fff59d 0%, #ffee58 100%);
  box-shadow: 0 2px 6px rgba(245, 127, 23, 0.3);
  transform: translateY(-1px);
}

.equality-line {
  font-size: 14px;
  color: #f57f17;
  font-weight: bold;
  line-height: 1;
}

.equality-label {
  font-size: 13px;
  line-height: 1;
}

.equality-target {
  font-size: 10px;
  font-family: 'Courier New', monospace;
  background: rgba(255, 255, 255, 0.6);
  padding: 1px 4px;
  border-radius: 4px;
  font-weight: 700;
}

.level-badge {
  font-size: 10px;
  padding: 2px 6px;
  border-radius: 8px;
  background: #e3f2fd;
  color: #1976d2;
  flex-shrink: 0;
  font-family: 'Courier New', monospace;
  font-weight: 500;
}

.page-badge {
  font-size: 10px;
  padding: 2px 6px;
  border-radius: 8px;
  background: #e0e0e0;
  color: #424242;
  flex-shrink: 0;
  font-family: 'Courier New', monospace;
  font-weight: 500;
}

.class-badge {
  font-size: 10px;
  padding: 2px 6px;
  border-radius: 8px;
  flex-shrink: 0;
  font-weight: 500;
  text-transform: capitalize;

  &.class-title {
    background: #fee2e2;
    color: #dc2626;
  }

  &.class-fstline {
    background: #d1fae5;
    color: #059669;
  }

  &.class-para {
    background: #dbeafe;
    color: #2563eb;
  }

  &.class-table {
    background: #fed7aa;
    color: #d97706;
  }

  &.class-section {
    background: #e9d5ff;
    color: #9333ea;
  }

  &.class-caption {
    background: #fce7f3;
    color: #ec4899;
  }
}

.label-tag {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 3px;
  background: #fff3e0;
  color: #e65100;
  border: 1px solid #ffb74d;
  flex-shrink: 0;
  font-weight: 500;
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.id-badge {
  font-size: 10px;
  padding: 2px 6px;
  border-radius: 8px;
  background: #e8f5e9;
  color: #2e7d32;
  flex-shrink: 0;
  font-family: 'Courier New', monospace;
  font-weight: 600;
}

.parent-id-badge {
  font-size: 10px;
  padding: 2px 6px;
  border-radius: 8px;
  background: #fff3e0;
  color: #f57c00;
  flex-shrink: 0;
  font-family: 'Courier New', monospace;
  font-weight: 600;
}

.multi-select-badge {
  font-size: 12px;
  padding: 2px 6px;
  border-radius: 50%;
  background: #1976d2;
  color: white;
  flex-shrink: 0;
  font-weight: bold;
  line-height: 1;
  width: 18px;
  height: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.paragraph-list {
  margin-left: 28px;
  margin-top: 4px;
  margin-bottom: 8px;
}

.paragraph-item {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  padding: 6px 8px;
  margin: 2px 0;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 12px;
  line-height: 1.5;

  &:hover {
    background: #f3f4f6;
    border-color: #d1d5db;
  }
}

.paragraph-icon {
  flex-shrink: 0;
  font-size: 14px;
  margin-top: 1px;
}

.paragraph-text {
  flex: 1;
  color: #4b5563;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.children {
  position: relative;
}

.children::before {
  content: '';
  position: absolute;
  left: 8px;
  top: 0;
  bottom: 0;
  width: 1px;
  background: #e0e0e0;
}

// 平级节点样式 (equality)
.siblings {
  position: relative;
  margin-top: 8px;
  padding-left: 12px;
  border-left: 2px dashed #fbbf24; // 黄色虚线边框
}

// 连接节点样式 (connect)
.connected-nodes {
  position: relative;
  margin-top: 8px;
  padding-left: 12px;
  border-left: 2px dashed #3b82f6; // 蓝色虚线边框
}

// 关系组标签
.relation-group-label {
  font-size: 11px;
  color: #666;
  padding: 4px 8px;
  margin-bottom: 4px;
  font-weight: 500;
  opacity: 0.8;
}

/* 右键菜单样式 */
.context-menu {
  position: fixed;
  z-index: 9999;
  background: white;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  min-width: 120px;
  padding: 4px 0;
}

@keyframes pulse-equality {
  0%, 100% {
    box-shadow: 0 0 0 2px rgba(255, 213, 79, 0.3), 0 2px 8px rgba(245, 127, 23, 0.2);
  }
  50% {
    box-shadow: 0 0 0 4px rgba(255, 213, 79, 0.5), 0 4px 12px rgba(245, 127, 23, 0.4);
  }
}

.context-menu-item {
  padding: 8px 16px;
  cursor: pointer;
  font-size: 14px;
  color: #333;
  transition: background 0.2s;

  &:hover {
    background: #f5f5f5;
  }
}

/* 标签编辑模态框样式 */
.label-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.45);
  z-index: 10000;
  display: flex;
  align-items: center;
  justify-content: center;
}

.label-modal {
  background: white;
  border-radius: 6px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  min-width: 400px;
  max-width: 90vw;
}

.label-modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid #f0f0f0;
  font-size: 16px;
  font-weight: 500;
  color: #333;
}

.close-btn {
  font-size: 24px;
  color: #999;
  cursor: pointer;
  line-height: 1;
  transition: color 0.2s;

  &:hover {
    color: #333;
  }
}

.label-modal-body {
  padding: 20px;

  .form-group {
    margin-bottom: 16px;

    &:last-child {
      margin-bottom: 0;
    }

    label {
      display: block;
      margin-bottom: 8px;
      font-size: 14px;
      font-weight: 500;
      color: #333;
    }
  }
}

.label-input,
.class-select,
.relation-select,
.parent-id-input {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  font-size: 14px;
  outline: none;
  transition: border-color 0.2s;

  &:focus {
    border-color: #1890ff;
    box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.1);
  }

  &::placeholder {
    color: #bfbfbf;
  }
}

.label-modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding: 12px 20px;
  border-top: 1px solid #f0f0f0;
}

.btn-cancel,
.btn-save {
  padding: 6px 16px;
  border-radius: 4px;
  font-size: 14px;
  cursor: pointer;
  border: none;
  outline: none;
  transition: all 0.2s;
}

.btn-cancel {
  background: white;
  color: #333;
  border: 1px solid #d9d9d9;

  &:hover {
    color: #1890ff;
    border-color: #1890ff;
  }
}

.btn-save {
  background: #1890ff;
  color: white;

  &:hover {
    background: #40a9ff;
  }

  &:active {
    background: #096dd9;
  }
}
</style>
