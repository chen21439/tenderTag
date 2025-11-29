# 标记统计组件说明

## 组件位置
`components/markdown/TagStatistics.vue`

## 功能说明
该组件用于统计和展示文档标记数据的统计信息。

### 支持两种数据格式

#### 1. 基于 level 字段的统计
当数据中包含 `level` 字段时，显示：
- **标题总数**：所有标记的总数量
- **Level >= 101**：level 大于等于 101 的标记数量
- **详细分类**：
  - Level < 101
  - Level 101-200
  - Level > 200

#### 2. 基于 label 字段的统计
当数据中不包含 `level` 字段时，显示：
- **标题总数**：所有标记的总数量
- **已分类标签**：label_level1 不为"未分类"的数量
- **详细分类**：
  - 章节标题 (section_header)
  - 正文内容 (text)
  - 表格 (table)
  - 列表 (list)

## 使用方式

```vue
<template>
  <TagStatistics
    :tagged-data="items"
    @refresh="handleRefresh"
  />
</template>

<script setup>
import TagStatistics from './TagStatistics.vue'

const items = ref([
  { id: 1, label: 'section_header', level: 101, ... },
  { id: 2, label: 'text', level: 50, ... }
])

const handleRefresh = () => {
  // 刷新数据逻辑
}
</script>
```

## Props

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| taggedData | Array | [] | 标记数据数组 |
| autoRefresh | Boolean | true | 是否自动刷新统计 |

## Events

| 事件名 | 说明 | 回调参数 |
|--------|------|----------|
| refresh | 点击刷新按钮时触发 | - |

## 集成位置
已集成到 `components/tag/LabeledDataViewer.vue` 组件中
