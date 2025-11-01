# Claude 开发笔记

## 项目说明

如果有疑问，请告诉我，我们一起讨论。

## 依赖管理

本项目使用 **Poetry** 管理依赖。

### 添加新依赖
```bash
poetry add <package-name>
```

### 添加开发依赖
```bash
poetry add --group dev <package-name>
```

### 安装所有依赖
```bash
poetry install
```

## 表格分析要求

**后续分析表格的时候，需要一起查看 raw.json 中每个表格有多少列**

在分析表格提取结果时，需要同时检查：
- 最终合并后的表格列数（table.json）
- 原始提取的每个表格段的列数（raw.json / tables_first_round）
- 列数不一致的原因（是否需要列补齐、是否是误合并等）
