# 树形组件复用实现方案

## 📁 项目结构

```
src/
├── hooks/
│   ├── useTreeBuilder.ts         # ✨ 通用树构建逻辑
│   └── useTreeEditor.ts          # ✨ 树编辑逻辑
├── components/
│   └── tree/
│       ├── EditableTree.vue      # ✨ 可编辑树容器组件
│       └── index.ts              # 导出文件
└── views/
    ├── compliance-review/
    │   ├── components/
    │   │   ├── TreeNode.vue      # 通用树节点组件（已存在）
    │   │   └── ontology/         # 本体树组件
    │   └── index.vue
    └── review/
        └── index.vue             # ✨ 已集成可编辑树
```

## 🎯 核心组件

### 1. **useTreeBuilder.ts** - 树构建策略

支持三种构建策略：

#### 策略1: `parentId` - 通过父子关系构建
```typescript
buildTreeByParentId(data, 'line_id', 'parent_id')
```
- 适用场景：扁平数据，每个节点有 `parent_id` 字段
- 使用页面：**review 页面**

#### 策略2: `path` - 通过路径构建
```typescript
buildTreeByPath(data, 'directory_path')
```
- 适用场景：节点有路径字段（如 `a/b/c`）
- 使用页面：**compliance-review 页面**

#### 策略3: `label` - 通过标签构建本体树
```typescript
buildTreeByLabel(data, 'label')
```
- 适用场景：多级标签路径（如 `项目信息/项目编号`）
- 使用页面：**compliance-review 页面（本体树模式）**

### 2. **useTreeEditor.ts** - 树编辑逻辑

提供完整的树编辑功能：

```typescript
const {
  editMode,              // 编辑模式开关
  selectedNodeIds,       // 选中的节点ID列表
  expandedNodes,         // 展开的节点集合
  moveNode,             // 移动节点
  updateLabel,          // 更新标签
  deleteNode,           // 删除节点
  toggleEditMode,       // 切换编辑模式
  expandAll,            // 全部展开
  collapseAll           // 全部折叠
} = useTreeEditor(treeData, {
  onNodeMove: async (nodeId, newParentId) => {
    // 调用API更新数据
  }
})
```

### 3. **EditableTree.vue** - 可编辑树容器

统一的树形视图容器组件：

```vue
<EditableTree
  :raw-data="jsonElements"
  build-strategy="parentId"
  :build-options="{ idField: 'line_id', parentIdField: 'parent_id' }"
  :editable="true"
  :show-toolbar="true"
  @node-move="handleNodeMove"
  @label-update="handleLabelUpdate"
  @node-select="handleNodeSelect"
/>
```

**Props:**
- `rawData`: 原始数据数组
- `buildStrategy`: 构建策略（'parentId' | 'path' | 'label'）
- `buildOptions`: 构建选项（字段名配置）
- `editable`: 是否可编辑
- `showToolbar`: 是否显示工具栏
- `loading`: 加载状态

**Events:**
- `node-move`: 节点移动事件
- `label-update`: 标签更新事件
- `node-delete`: 节点删除事件
- `node-select`: 节点选择事件
- `tree-built`: 树构建完成事件

## 🚀 在 Review 页面中的使用

### 数据流程

1. **加载数据**: 从 URL 获取 JSON 数据
   ```
   http://localhost:3000/api/runs/{runId}/json?file=enriched/{filename}.json
   ```

2. **构建树**: 使用 `parentId` 策略
   ```typescript
   const treeData = buildTree(
     jsonElements.value,
     'parentId',
     { idField: 'line_id', parentIdField: 'parent_id' }
   )
   ```

3. **编辑节点**: 拖拽改变父节点
   ```typescript
   const handleNodeMove = async ({ nodeId, newParentId }) => {
     // 更新本地数据
     node.parent_id = newParentId

     // TODO: 调用后端API持久化
     await fetch('/api/update-parent', {
       method: 'POST',
       body: JSON.stringify({ lineId: nodeId, parentId: newParentId })
     })
   }
   ```

### 视图切换

Review 页面支持两种视图模式：

- **列表视图**: 按页面展示元素（原有功能）
- **树形视图**: 按层级结构展示元素（新增功能）

```vue
<a-radio-group v-model:value="viewMode">
  <a-radio-button value="list">列表视图</a-radio-button>
  <a-radio-button value="tree">树形视图</a-radio-button>
</a-radio-group>
```

## 📝 待办事项

### 后端API接口

需要实现以下接口：

1. **更新父节点**
   ```
   POST /api/update-parent
   Body: { lineId: string, parentId: string | null }
   ```

2. **更新标签**
   ```
   POST /api/update-label
   Body: { lineId: string, label: string }
   ```

3. **删除节点**
   ```
   DELETE /api/delete-node/:lineId
   ```

### 数据字段补充

当前数据结构缺少 `parent_id` 字段，需要：
1. 后端分析文档结构，推断节点的父子关系
2. 为每个节点添加 `parent_id` 字段
3. 确保根节点的 `parent_id` 为 `null` 或 `undefined`

## 🎨 复用优势

### 1. **高度解耦**
- 树构建逻辑独立于UI组件
- 支持多种数据源和构建策略
- 易于扩展新的构建方式

### 2. **统一交互**
- 所有树形视图使用相同的交互模式
- 编辑功能可选启用
- 一致的用户体验

### 3. **易于维护**
- 逻辑集中管理
- 减少代码重复
- 修改一处，处处生效

### 4. **灵活配置**
- 字段名可配置
- 构建策略可选择
- 功能模块可插拔

## 📊 使用示例

### 示例1: Review 页面（parent_id 策略）

```vue
<EditableTree
  :raw-data="jsonElements"
  build-strategy="parentId"
  :build-options="{
    idField: 'line_id',
    parentIdField: 'parent_id'
  }"
  :editable="true"
  @node-move="handleNodeMove"
/>
```

### 示例2: Compliance Review 页面（path 策略）

```vue
<EditableTree
  :raw-data="ontologyRawData"
  build-strategy="path"
  :build-options="{
    pathField: 'directory_path'
  }"
  :editable="false"
/>
```

### 示例3: 本体树模式（label 策略）

```vue
<EditableTree
  :raw-data="labeledData"
  build-strategy="label"
  :build-options="{
    labelField: 'label'
  }"
  :editable="false"
/>
```

## 🔧 开发建议

1. **数据准备**: 确保数据包含必要的关联字段（parent_id、path 或 label）
2. **性能优化**: 大数据量时考虑虚拟滚动和懒加载
3. **错误处理**: API调用失败时需要回滚本地状态
4. **权限控制**: 根据用户角色控制编辑权限

## 📚 相关文档

- [TreeNode.vue](./src/views/compliance-review/components/TreeNode.vue) - 树节点组件
- [useOntologyTree.ts](./src/views/compliance-review/components/ontology/useOntologyTree.ts) - 本体树逻辑
- [compliance-review/index.vue](./src/views/compliance-review/index.vue) - 参考实现
