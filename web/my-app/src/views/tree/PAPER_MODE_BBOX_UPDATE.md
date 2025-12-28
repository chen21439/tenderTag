# 纸张模式 Bbox 渲染更新

## 更新说明

将纸张模式改为使用 **bbox 坐标绝对定位**渲染元信息，以还原论文的实际布局。

## 主要改动

### 1. 元信息渲染方式改变

**之前**：元信息（title/author/affili/mail）按类型分组，垂直排列
```
标题
作者1
作者2
作者3
机构1
机构2
机构3
邮箱1
邮箱2
邮箱3
```

**现在**：使用 bbox 坐标绝对定位，水平排列（还原实际布局）
```
                标题

作者1          作者2          作者3
机构1          机构2          机构3
邮箱1          邮箱2          邮箱3
```

### 2. 实现细节

#### PaperView.vue 修改

1. **移除分组渲染**
   - 删除了 `currentPageTitleNodes`、`currentPageAuthorNodes` 等单独的计算属性
   - 统一使用 `currentPageMetaNodes` 获取所有元信息节点

2. **添加 bbox 定位逻辑**
   ```javascript
   // 获取元信息节点的样式（基于bbox绝对定位）
   const getMetaNodeStyle = (node) => {
     const [x1, y1, x2, y2] = node.box
     return {
       position: 'absolute',
       left: x1 + 'px',
       top: y1 + 'px',
       width: (x2 - x1) + 'px',
       minHeight: (y2 - y1) + 'px'
     }
   }
   ```

3. **计算页面高度**
   ```javascript
   const pageHeight = computed(() => {
     const nodesOnPage = props.nodes.filter(n => (n.page || 0) === currentPage.value)
     const maxY = Math.max(...nodesOnPage.map(n => n.box ? n.box[3] : 0))
     return Math.max(maxY + 100, 842)
   })
   ```

4. **正文内容动态定位**
   ```javascript
   const metaBottomY = computed(() => {
     const maxY = Math.max(...currentPageMetaNodes.value.map(n => n.box[3]))
     return maxY + 30
   })
   ```

### 3. 样式调整

- `.paper-page`: 改为相对定位容器，移除固定 padding
- `.paper-element`: 使用 flexbox 居中文本，适应绝对定位
- `.content-sections`: 添加 padding，动态 marginTop

## 效果对比

### 数据示例
```json
{
  "text": "Lieke Gelderloos",
  "box": [107, 119, 194, 131],
  "class": "author",
  "page": 0
},
{
  "text": "Grzegorz Chrupała",
  "box": [248, 119, 350, 132],
  "class": "author",
  "page": 0
},
{
  "text": "Afra Alishahi",
  "box": [413, 119, 482, 131],
  "class": "author",
  "page": 0
}
```

**关键发现**：
- 三个作者的 **y 坐标相同** (119-131)，说明在同一行
- **x 坐标不同**，分别在左、中、右位置
- 使用 bbox 绝对定位后，能正确还原水平布局

## 优势

1. ✅ **准确还原布局**：元信息按照实际 PDF 位置排列
2. ✅ **避免重复显示**：相同文本（如 "Tilburg University"）在各自位置显示
3. ✅ **与 Bbox 模式一致**：两种模式使用相同的定位逻辑
4. ✅ **支持分页**：每页独立渲染，自动计算高度

## 注意事项

- 元信息必须有 `box` 字段才能正确定位
- 页面宽度建议 900px 以上，以容纳水平排列的作者信息
- 正文内容仍然使用流式布局，便于阅读
