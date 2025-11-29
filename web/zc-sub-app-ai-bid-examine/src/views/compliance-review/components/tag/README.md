# LabeledDataViewer 标注数据查看器

## 功能介绍

用于展示和浏览文档标注数据的 Vue 组件，支持：

- 📊 展示标注数据列表（文本、表格、章节标题等）
- 🔍 按标签类型筛选
- 🔎 文本内容搜索
- 📄 分页显示
- 🎨 不同标签类型的视觉区分
- 📐 显示边界框坐标信息

## 使用方法

### 基础使用

```vue
<template>
  <LabeledDataViewer />
</template>

<script setup>
import LabeledDataViewer from '@/views/compliance-review/components/tag/LabeledDataViewer.vue'
</script>
```

### 自定义数据源

```vue
<template>
  <LabeledDataViewer :data-url="/custom/path/to/data.json" />
</template>
```

## 数据格式

组件期望的 JSON 数据格式：

```json
{
  "document_name": "文档名称",
  "total_items": 100,
  "items": [
    {
      "id": 0,
      "label": "section_header",
      "text": "章节标题文本",
      "page_no": 1,
      "bbox": {
        "l": 97.27,
        "t": 683.88,
        "r": 182.69,
        "b": 674.09,
        "coord_origin": "BOTTOMLEFT"
      }
    }
  ]
}
```

## 支持的标签类型

- `section_header` - 章节标题（蓝色边框）
- `text` - 正文
- `table` - 表格（绿色边框，渲染 HTML 表格）
- `list` - 列表（紫色边框）
- `title` - 标题（橙色边框）

## Props

| 属性名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| dataUrl | String | '/knowledge-graph/output_20251123_144831_labeled.json' | 数据源 URL |

## 特性

1. **智能筛选**：支持按标签类型和文本内容双重筛选
2. **表格渲染**：自动将 HTML 表格格式的文本渲染为可视化表格
3. **坐标信息**：显示每个标注项的边界框坐标
4. **分页功能**：默认每页显示 20 条数据
5. **响应式设计**：适配不同屏幕尺寸

## 目录结构

```
tag/
├── LabeledDataViewer.vue    # 主组件
├── index.vue                 # 示例页面
├── css/
│   └── labeled-data-viewer.scss  # 样式文件
└── README.md                 # 说明文档
```
