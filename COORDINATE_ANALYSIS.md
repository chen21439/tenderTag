# 坐标系统问题深度分析

## 问题描述
用户反馈：页面点击元素后，高亮位置不一致，"很明显一个是左上 一个是左下"

## 已验证的事实
1. ✅ JSON数据使用**左下坐标系**（通过图片验证确认）
2. ✅ 两份测试文件都是左下坐标系（玉塘社区医院、泉州实验小学）
3. ❌ 但页面点击时表现不一致

## 关键代码流程

### 1. 点击元素时 (index.vue:897-950)
```javascript
const handleElementClick = async (element: any) => {
  const box = element.box  // [x1, y1, x2, y2] - 左下坐标系

  // 构建 quadPoints（已修改为左下坐标系）
  const quadPoints = [
    box[0], box[3],  // 左上 = (x1, y2)
    box[2], box[3],  // 右上 = (x2, y2)
    box[2], box[1],  // 右下 = (x2, y1)
    box[0], box[1]   // 左下 = (x1, y1)
  ]

  const highlightRect = {
    needsConversion: true  // 🚨 关键点！
  }
}
```

### 2. PdfViewer处理高亮 (PdfViewer.vue:549-609)
```javascript
// 如果标记了需要坐标转换（屏幕坐标 → PDF坐标）
if (needsConversion && rect && rect.length === 4) {
  // 🚨 这里假设输入是"屏幕坐标"（左上），转换成PDF坐标（左下）
  const pdfRect = [
    rect[0],              // x1 不变
    pageHeight - rect[3], // y1 = pageHeight - screenY2
    rect[2],              // x2 不变
    pageHeight - rect[1]  // y2 = pageHeight - screenY1
  ]
}
```

## 问题诊断

### 当前逻辑链：
1. JSON数据 = **左下坐标系**
2. `handleElementClick` 构建 quadPoints = **左下坐标系格式**
3. 设置 `needsConversion = true`
4. PdfViewer **误以为输入是左上坐标系**，再转换一次
5. **双重转换导致错误！**

### needsConversion 的本意：
- `needsConversion = true`：输入是**屏幕坐标（左上）**，需要转换成PDF坐标（左下）
- `needsConversion = false`：输入已经是**PDF坐标（左下）**，不需要转换

## 为什么看起来"一个左上一个左下"？

可能的情况：
1. **某些文件的高度特殊**，导致双重转换后"歪打正着"看起来正确
2. **某些元素的位置特殊**（如页面上半部分vs下半部分），转换后表现不同
3. **代码中有其他地方**设置了不同的needsConversion值

## 解决方案

由于JSON数据已经是PDF坐标（左下），应该：

```javascript
const highlightRect = {
  pageNum: targetPage,
  rect: box,
  quadPoints: quadPoints,
  jump: true,
  needsConversion: false  // ✅ JSON数据已经是PDF坐标，不需要转换
}
```

## 需要验证的问题

1. 是否有其他地方也调用高亮功能，使用了不同的needsConversion值？
2. 是否有某些JSON文件真的是左上坐标系（历史遗留数据）？
3. PDF.js的convertToViewportPoint是否在某些情况下表现不同？

## 下一步行动

1. 先撤销quadPoints的修改（因为那个修改是错的）
2. 只修改 needsConversion: true → false
3. 测试两份文件的点击高亮是否都正确
4. 如果还有问题，检查是否存在混合坐标系的情况
