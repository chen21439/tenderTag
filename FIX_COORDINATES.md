# 坐标系统修复说明

## 问题诊断

经过验证，JSON数据中的 `box` 使用的是 **左下坐标系**（PDF标准），但前端代码在 `handleElementClick` 中错误地将其当作**左上坐标系**处理。

## 错误代码位置

文件：`web/zc-sub-app-ai-bid-examine/src/views/review/index.vue`
行号：908-913

### 当前错误代码：
```javascript
// 转换为 quadPoints 格式 (8个点: 左上、右上、右下、左下的x,y坐标)
const quadPoints = [
    box[0], box[1],  // ❌ 错误：假设box[1]是top
    box[2], box[1],  // ❌ 错误：假设box[1]是top
    box[2], box[3],  // ✅ 正确
    box[0], box[3]   // ❌ 错误：假设box[3]是bottom
]
```

### 正确代码：
```javascript
// box 是左下坐标系: [x1, y1, x2, y2]
// (x1, y1) = 左下角
// (x2, y2) = 右上角
const quadPoints = [
    box[0], box[3],  // ✅ 左上 = (x1, y2)
    box[2], box[3],  // ✅ 右上 = (x2, y2)
    box[2], box[1],  // ✅ 右下 = (x2, y1)
    box[0], box[1]   // ✅ 左下 = (x1, y1)
]
```

## 坐标系统说明

### JSON 数据（左下坐标系）
```
box: [x1, y1, x2, y2]

     (x2, y2) -------- 右上角
        |                 |
        |                 |
     (x1, y1) -------- 左下角 (原点在页面左下)
```

### PDF.js Viewport（左下坐标系）
PDF.js 内部使用的也是左下坐标系，与我们的数据一致。

### Canvas 渲染（左上坐标系）
Canvas 使用左上坐标系，但 `viewport.convertToViewportPoint()` 会自动转换。

## 验证结果

已通过以下两份文件验证：
1. `[GMCG2024000197-A]玉塘社区医院家具及医疗家具项目.json` ✅
2. `泉州市实验小学足球场人造草坪采购项目.json` ✅

可视化结果明确显示红色框（左下坐标系）完美覆盖文本。

## 修复步骤

修改文件：`web/zc-sub-app-ai-bid-examine/src/views/review/index.vue:908-913`

将 quadPoints 的构建逻辑改为正确的左下坐标系转换。
