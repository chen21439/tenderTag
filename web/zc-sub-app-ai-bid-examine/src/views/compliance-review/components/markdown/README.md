# Markdown 展示功能

## 功能说明

在合规审查页面右上角新增了"Markdown"选项卡，用于展示 Markdown 格式的文档内容。

## 组件结构

```
markdown/
├── MarkdownViewer.vue  # Markdown 展示组件
└── README.md          # 使用说明
```

## 使用方式

### 1. 基本使用

在页面中点击右上角的 "Markdown" 选项卡即可切换到 Markdown 展示模式。

### 2. 更新数据

在 `index.vue` 中修改 `markdownData` 对象来更新展示内容：

```typescript
const markdownData = reactive({
  content: '# 你的 Markdown 内容',
  loading: false,
  error: ''
})
```

### 3. 接口集成示例

当需要从接口获取数据时：

```typescript
// 在 index.vue 中添加获取函数
const fetchMarkdownContent = async () => {
  markdownData.loading = true
  markdownData.error = ''

  try {
    const response = await fetch('/api/your-endpoint')
    const data = await response.json()

    markdownData.content = data.content
  } catch (error) {
    markdownData.error = '内容加载失败，请稍后重试'
    console.error('加载 Markdown 失败:', error)
  } finally {
    markdownData.loading = false
  }
}

// 在 watch 中监听 tab 切换
watch(treeGroupMode, (newMode) => {
  if (newMode === 'markdown') {
    fetchMarkdownContent()
  }
})
```

## MarkdownViewer 组件 Props

| 参数 | 类型 | 默认值 | 说明 |
|-----|------|--------|------|
| content | string | '' | Markdown 内容 |
| loading | boolean | false | 加载状态 |
| error | string | '' | 错误信息 |
| theme | 'light' \| 'dark' | 'light' | 主题模式 |
| previewTheme | string | 'github' | 预览主题 |
| codeTheme | string | 'github' | 代码高亮主题 |
| enableSanitize | boolean | true | 是否启用 HTML 安全过滤 |

## 主题配置

### 预览主题（previewTheme）

- `default` - 默认主题
- `github` - GitHub 风格
- `vuepress` - VuePress 风格
- `mk-cute` - 可爱风格
- `smart-blue` - 智能蓝色
- `cyanosis` - 青色

### 代码高亮主题（codeTheme）

- `atom` - Atom 风格
- `github` - GitHub 风格
- `gradient` - 渐变风格
- `kimbie` - Kimbie 风格
- `stackoverflow` - StackOverflow 风格

## 接口数据格式建议

```json
{
  "id": 123,
  "title": "文档标题",
  "contentType": "markdown",
  "content": "# 一级标题\n\n正文内容...",
  "summary": "文档摘要",
  "author": "作者",
  "createdAt": "2025-11-24T10:00:00Z",
  "updatedAt": "2025-11-24T12:00:00Z",
  "tags": ["标签1", "标签2"]
}
```

## 安全特性

- 内置 HTML 安全过滤，自动移除潜在危险标签（`<script>`、`<iframe>` 等）
- 可通过 `enableSanitize` 参数关闭过滤（不推荐）
- 建议后端也进行内容清理，前端作为二次防护

## 样式说明

- 组件会自动适应容器高度
- 内置优化的滚动条样式
- 响应式布局，支持各种屏幕尺寸
