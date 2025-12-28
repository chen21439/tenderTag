# 树形视图拖拽功能 API 文档

## 功能概述

在 Review 页面的树形视图中，用户可以通过拖拽节点来改变文档的层级结构。拖拽操作会更新节点的 `parent_id` 字段，并保存到 JSON 文件中。

## API 接口

### 1. 单个节点移动

**接口地址：** `POST /api/runs/:timestamp/move-node`

**请求参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| timestamp | string | 是 | URL 路径参数，runs 目录的时间戳文件夹名 |
| fileName | string | 是 | 文件名（如 "少年宫.json"） |
| lineId | string | 是 | 要移动的节点 ID |
| newParentId | string/null | 是 | 新的父节点 ID，null 表示移动到根节点 |

**请求示例：**

```bash
curl -X POST "http://localhost:3000/api/runs/20251218_141436_checkpoint-3000_096b7b/move-node" \
  -H "Content-Type: application/json" \
  -d '{
    "fileName": "少年宫.json",
    "lineId": "L00006",
    "newParentId": "L00001"
  }'
```

**响应示例：**

```json
{
  "success": true,
  "message": "节点移动成功",
  "timestamp": "20251218_141436_checkpoint-3000_096b7b",
  "fileName": "少年宫.json",
  "lineId": "L00006",
  "newParentId": "L00001"
}
```

### 2. 批量节点移动

**接口地址：** `POST /api/runs/:timestamp/move-nodes`

**请求参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| timestamp | string | 是 | URL 路径参数，runs 目录的时间戳文件夹名 |
| fileName | string | 是 | 文件名（如 "少年宫.json"） |
| lineIds | string[] | 是 | 要移动的节点 ID 数组 |
| newParentId | string/null | 是 | 新的父节点 ID，null 表示移动到根节点 |

**请求示例：**

```bash
curl -X POST "http://localhost:3000/api/runs/20251218_141436_checkpoint-3000_096b7b/move-nodes" \
  -H "Content-Type: application/json" \
  -d '{
    "fileName": "少年宫.json",
    "lineIds": ["L00006", "L00007", "L00008"],
    "newParentId": "L00001"
  }'
```

**响应示例：**

```json
{
  "success": true,
  "message": "成功移动 3 个节点",
  "timestamp": "20251218_141436_checkpoint-3000_096b7b",
  "fileName": "少年宫.json",
  "updatedCount": 3,
  "totalRequested": 3,
  "newParentId": "L00001"
}
```

## 前端实现

### 数据流程

1. **用户操作：** 在树形视图中拖拽节点
2. **事件触发：** `handleNodeMove` 事件被触发
3. **API 调用：** 发送 POST 请求到 `/api/runs/:timestamp/move-node`
4. **服务器处理：**
   - 读取 JSON 文件
   - 查找目标节点
   - 更新 `parent_id` 字段
   - 保存文件
5. **前端更新：** 更新本地数据并显示成功提示

### 代码示例

```typescript
const handleNodeMove = async ({ nodeId, newParentId }) => {
  // 检查是否从 runs 目录加载
  if (!currentFileSource.value.isFromRuns) {
    message.warning('只支持从 runs 目录加载的文件')
    return
  }

  const runName = currentFileSource.value.runName
  const fileName = currentFileSource.value.fileName

  // 调用 API
  const response = await fetch(`http://localhost:3000/api/runs/${runName}/move-node`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      fileName,
      lineId: nodeId,
      newParentId
    })
  })

  const result = await response.json()

  if (result.success) {
    // 更新本地数据
    const node = jsonElements.value.find(el => el.line_id === nodeId)
    if (node) {
      node.parent_id = newParentId
    }
    message.success('节点移动成功')
  }
}
```

## 服务器端实现

### 关键逻辑

```javascript
app.post('/api/runs/:timestamp/move-node', express.json(), (req, res) => {
  const timestamp = req.params.timestamp
  const { fileName, lineId, newParentId } = req.body

  // 构建文件路径
  const jsonPath = path.join(RUNS_DIR, timestamp, 'enriched', fileName)

  // 读取文件
  fs.readFile(jsonPath, 'utf8', (err, data) => {
    const jsonData = JSON.parse(data)

    // 查找并更新节点
    for (let i = 0; i < jsonData.length; i++) {
      if (jsonData[i].line_id === lineId) {
        jsonData[i].parent_id = newParentId
        break
      }
    }

    // 写回文件
    fs.writeFile(jsonPath, JSON.stringify(jsonData, null, 2), 'utf8', (err) => {
      res.json({
        success: true,
        message: '节点移动成功',
        lineId,
        newParentId
      })
    })
  })
})
```

## 数据结构

### JSON 文件结构

```json
[
  {
    "line_id": "L00001",
    "class": "section",
    "page": "0",
    "box": [253, 72, 337, 86],
    "text": "特别警示条款",
    "id": 0,
    "parent_id": null
  },
  {
    "line_id": "L00002",
    "class": "fstline",
    "page": "0",
    "box": [92, 97, 514, 107],
    "text": "参与本项目政府采购活动...",
    "id": 1,
    "parent_id": "L00001"
  }
]
```

### parent_id 说明

- **null**: 表示根节点，无父节点
- **"L00001"**: 表示父节点的 line_id

## 树形视图过滤

树形视图只显示 `class` 为 `section` 或 `title` 的元素，过滤掉其他类型（para、fstline、table 等）：

```typescript
const filteredTreeElements = computed(() => {
  return jsonElements.value.filter(el => {
    const classType = el.class?.toLowerCase()
    return classType === 'section' || classType === 'title'
  })
})
```

## 使用场景

1. **调整文档结构：** 将章节移动到不同的父章节下
2. **重新组织层级：** 调整标题的层级关系
3. **修正识别错误：** 手动修正 AI 识别的文档结构错误

## 注意事项

1. **仅支持 runs 目录：** 只有从 runs 目录加载的文件才能拖拽编辑
2. **仅显示 section/title：** 树形视图只显示结构性元素，不显示内容元素
3. **实时保存：** 拖拽操作立即保存到 JSON 文件
4. **循环依赖检查：** 前端需要防止将节点拖到自己的子节点下

## 测试

使用提供的测试脚本测试 API：

```bash
bash test_move_node_api.sh
```

或手动测试：

```bash
curl -X POST "http://localhost:3000/api/runs/20251218_141436_checkpoint-3000_096b7b/move-node" \
  -H "Content-Type: application/json" \
  -d '{
    "fileName": "少年宫.json",
    "lineId": "L00006",
    "newParentId": "L00001"
  }'
```
