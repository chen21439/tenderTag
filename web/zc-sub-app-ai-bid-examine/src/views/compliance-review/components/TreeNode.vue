<template>
  <div
    class="tree-node"
    @dragover.prevent="handleDragOver"
    @dragleave="handleDragLeave"
  >
    <div
      class="node-header"
      :class="{
        'selected': selectedId === node.line_id || selectedIds.includes(node.line_id),
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
        v-if="hasChildren"
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

      <!-- 关系类型标记 -->
      <span v-if="node.relation && node.relation !== 'none'" class="relation-badge" :class="node.relation">
        {{ getRelationLabel(node.relation) }}
      </span>

      <!-- Level 标记 -->
      <span v-if="node.level !== undefined" class="level-badge">
        L{{ node.level }}
      </span>

      <!-- 页码标记 -->
      <span v-if="node.page !== undefined" class="page-badge">
        P{{ node.page + 1 }}
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
      <div class="context-menu-item" @click="handleEditLabel">
        编辑标签
      </div>
    </div>

    <!-- 标签编辑模态框 -->
    <div v-if="showLabelModal" class="label-modal-overlay" @click.stop="closeLabelModal">
      <div class="label-modal" @click.stop>
        <div class="label-modal-header">
          <span>编辑标签</span>
          <span class="close-btn" @click="closeLabelModal">×</span>
        </div>
        <div class="label-modal-body">
          <input
            ref="labelInputRef"
            v-model="editingLabel"
            type="text"
            class="label-input"
            placeholder="请输入标签"
            @keyup.enter="saveLabelEdit"
            @keyup.esc="closeLabelModal"
          />
        </div>
        <div class="label-modal-footer">
          <button class="btn-cancel" @click="closeLabelModal">取消</button>
          <button class="btn-save" @click="saveLabelEdit">保存</button>
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

      <!-- 子节点 -->
      <div v-if="hasChildren" class="children">
        <TreeNode
          v-for="child in node.children"
          :key="child.line_id"
          :node="child"
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

const emit = defineEmits(['toggle', 'select', 'paragraphClick', 'node-drop', 'drag-over-node', 'drag-end', 'drag-start-node', 'update-label'])

// 拖拽状态
const isDragOver = ref(false)

// 右键菜单状态
const showContextMenu = ref(false)
const contextMenuX = ref(0)
const contextMenuY = ref(0)

// 标签编辑状态
const showLabelModal = ref(false)
const editingLabel = ref('')
const labelInputRef = ref<HTMLInputElement | null>(null)
let isDraggingNow = false
let mouseDownTime = Date.now() // 初始化为当前时间，避免计算错误

// 是否有子节点
const hasChildren = computed(() => {
  return props.node.children && props.node.children.length > 0
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
    nodeId: props.node.line_id,
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
    event.dataTransfer.setData('text/plain', String(props.node.line_id))
  }

  // 通知父组件拖拽开始，记录被拖拽的节点ID
  emit('drag-start-node', props.node.line_id)

  console.log('✅ 开始拖拽节点:', props.node.line_id)
}

// 拖拽结束
const handleDragEnd = (event: DragEvent) => {
  console.log('🎯 dragEnd事件触发:', {
    nodeId: props.node.line_id,
    editMode: props.editMode
  })

  if (!props.editMode) {
    console.log('⚠️ 非编辑模式，跳过dragEnd处理')
    return
  }

  // dragEnd 只在被拖拽的节点上触发
  // 通知父组件拖拽结束，父组件会检查 lastDragOverNodeId 来决定是否发送API请求
  console.log('✅ 拖拽结束，通知父组件')
  emit('drag-end', props.node.line_id)

  // 清理状态
  isDragOver.value = false
  isDraggingNow = false
}

const handleDragOver = (event: DragEvent) => {
  if (!props.editMode) return

  event.preventDefault()
  // 阻止事件冒泡，避免父节点也被高亮
  event.stopPropagation()

  if (event.dataTransfer) {
    event.dataTransfer.dropEffect = 'move'
  }

  if (!isDragOver.value) {
    console.log('🎯 dragOver进入节点:', props.node.line_id, props.node.text || props.node.title)
  }
  isDragOver.value = true

  // 通知父组件记录这个节点
  emit('drag-over-node', props.node.line_id)
}

const handleDragLeave = (event: DragEvent) => {
  if (!props.editMode) return

  // 阻止事件冒泡，避免影响父节点
  event.stopPropagation()
  console.log('🎯 dragLeave离开节点:', props.node.line_id)
  isDragOver.value = false
}

// handleDrop 已删除，现在由父组件的全局 drop 处理

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

// 处理编辑标签
const handleEditLabel = () => {
  showContextMenu.value = false
  editingLabel.value = props.node.label || ''
  showLabelModal.value = true

  // 自动聚焦输入框
  nextTick(() => {
    labelInputRef.value?.focus()
    labelInputRef.value?.select()
  })
}

// 关闭标签编辑模态框
const closeLabelModal = () => {
  showLabelModal.value = false
  editingLabel.value = ''
}

// 保存标签编辑
const saveLabelEdit = () => {
  const newLabel = editingLabel.value.trim()
  console.log('💾 保存标签:', {
    nodeId: props.node.line_id,
    pid: props.node.pid,
    oldLabel: props.node.label,
    newLabel
  })

  // 通知父组件更新标签
  emit('update-label', {
    nodeId: props.node.line_id,
    pid: props.node.pid,
    label: newLabel
  })

  closeLabelModal()
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
    .page-badge {
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

.relation-badge {
  font-size: 9px;
  padding: 2px 6px;
  border-radius: 8px;
  background: #e0e0e0;
  color: #616161;
  flex-shrink: 0;
  font-weight: 500;
}

.relation-badge.contain {
  background: #c8e6c9;
  color: #2e7d32;
}

.relation-badge.equality {
  background: #fff9c4;
  color: #f57f17;
}

.relation-badge.connect {
  background: #b3e5fc;
  color: #01579b;
}

.relation-badge.meta {
  background: #f3e5f5;
  color: #6a1b9a;
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
}

.label-input {
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
