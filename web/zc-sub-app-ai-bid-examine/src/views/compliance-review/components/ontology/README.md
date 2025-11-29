# 本体树组件 (Ontology Tree Components)

本目录包含处理多级标签路径的本体树构建和渲染逻辑。

## 文件结构

```
ontology/
├── index.ts                 # 导出文件
├── useOntologyTree.ts      # 本体树构建逻辑 (Composable)
├── OntologyTreeView.vue    # 本体树视图组件
└── README.md               # 文档
```

## 组件说明

### useOntologyTree (Composable)

核心业务逻辑，负责将带有多级标签路径的数据构建为树形结构。

**功能：**
- 递归收集所有节点（包括嵌套子节点）
- 构建纯标签树结构（多级嵌套Map）
- 将数据节点挂载到对应标签
- 转换为UI节点树
- 处理"查看更多"展开逻辑

**主要方法：**
```typescript
const {
  buildOntologyTree,      // 主函数：构建本体标签树
  expandMoreNode,         // 展开"查看更多"节点
  collectAllNodes,        // 递归收集节点
  buildLabelTree,         // 构建标签树
  mountDataToLabelTree,   // 挂载数据到标签树
  convertLabelTreeToNodes // 转换为UI节点
} = useOntologyTree()
```

**使用示例：**
```typescript
import { useOntologyTree } from './components/ontology/useOntologyTree'

const { buildOntologyTree } = useOntologyTree()

// 构建树
const treeNodes = buildOntologyTree(rawData)
```

### OntologyTreeView.vue

树形结构的视图组件，封装了树的渲染和交互逻辑。

**Props:**
- `rawTreeData` - 原始树数据（必需）
- `selectedId` - 选中的节点ID
- `nodeMap` - 节点映射表
- `debugMode` - 调试模式

**Events:**
- `select` - 节点选择事件
- `paragraphClick` - 段落点击事件
- `update:treeData` - 树数据更新事件

**使用示例：**
```vue
<OntologyTreeView
  :raw-tree-data="rawTreeData"
  :selected-id="selectedNodeId"
  :node-map="nodeMap"
  @select="handleSelect"
  @update:tree-data="handleTreeUpdate"
/>
```

## 数据结构

### 输入数据格式

```typescript
interface InputNode {
  line_id: number
  text?: string
  content?: string
  label?: string          // 标签路径，如 "采购项目/采购包/符合性要求"
  children?: InputNode[]  // 嵌套子节点
  // ... 其他字段
}
```

### 输出树节点格式

```typescript
interface TreeNode {
  line_id: number
  text: string
  class: 'label-group' | 'label-group-2' | 'more-indicator' | string
  label?: string
  labelDepth?: number
  children: TreeNode[]
  isVirtual?: boolean      // 是否为虚拟节点（标签节点）
  _fullChildren?: TreeNode[] // 完整子节点列表（用于"查看更多"）
  _parentNode?: TreeNode     // 父节点引用（用于"查看更多"）
}
```

## 核心流程

1. **递归收集节点** (`collectAllNodes`)
   - 遍历整个嵌套树结构
   - 收集所有节点和标签路径

2. **构建标签树** (`buildLabelTree`)
   - 解析标签路径（用"/"分隔）
   - 构建多级嵌套的Map结构
   - 每个标签包含：完整路径、子标签Map、数据项数组

3. **挂载数据** (`mountDataToLabelTree`)
   - 将带标签的数据节点挂载到对应标签
   - 保留原始的子节点结构

4. **转换UI节点** (`convertLabelTreeToNodes`)
   - 递归转换Map树为UI节点树
   - 创建虚拟标签节点
   - 默认只显示前3个子节点
   - 超过3个时添加"查看更多"指示器

## 标签路径示例

```
采购项目
└── 采购包
    ├── 符合性要求
    │   └── 符合性审查项
    └── 技术要求
        ├── 核心技术参数
        └── 可选技术参数
```

对应的标签路径：
- `"采购项目"`
- `"采购项目/采购包"`
- `"采购项目/采购包/符合性要求"`
- `"采购项目/采购包/符合性要求/符合性审查项"`

## 与父组件集成

在 `index.vue` 中的集成方式：

```typescript
// 导入
import { useOntologyTree } from './components/ontology/useOntologyTree'

// 初始化
const { buildOntologyTree, expandMoreNode } = useOntologyTree()

// 使用
const buildTreeByLabel = async () => {
  const labelRoots = buildOntologyTree(rawTreeData.value)
  // ... 后续处理
}
```

## 注意事项

1. **标签路径分隔符**：使用 "/" 作为层级分隔符
2. **虚拟节点ID**：标签节点使用负数ID避免与真实数据冲突
3. **响应式更新**：展开"查看更多"后需要强制触发数组更新
4. **嵌套结构**：支持无限层级的标签嵌套
5. **数据保留**：挂载到标签的数据节点保留其原始子节点结构
