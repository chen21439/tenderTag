# Step2 数据查看器

这是一个用于查看和渲染 Step2 JSON 数据的 Vue 3 应用程序。

## 功能

- 读取 `1978018096320905217_step2_20251024_195443.json` 文件
- 渲染 `sections` 字段的内容
- 展示表格、段落等不同类型的块
- 支持嵌套的 section 结构

## 安装依赖

```bash
npm install
```

## 运行应用

需要同时运行前端开发服务器和后端 API 服务器：

### 1. 启动后端 API 服务器（端口 3000）

```bash
npm run server
```

### 2. 启动前端开发服务器（端口 5173）

打开新的终端窗口：

```bash
npm run dev
```

### 3. 访问应用

打开浏览器访问：http://localhost:5173

## 项目结构

```
my-app/
├── src/
│   ├── App.vue          # 主应用组件（渲染 sections）
│   ├── main.js          # 应用入口
│   └── router/
│       └── index.js     # 路由配置
├── server.js            # Express API 服务器
├── vite.config.js       # Vite 配置（包含代理设置）
└── package.json         # 项目依赖
```

## 数据格式

应用从以下路径读取 JSON 文件：
```
E:\programFile\AIProgram\docxServer\pdf\task\1978018096320905217\1978018096320905217_step2_20251024_195443.json
```

## 显示的内容

- **Section Header**: 显示 section 的 ID、标题、层级和评分
- **Table**: 以表格形式展示
- **Paragraph**: 以段落形式展示
- **Children**: 递归展示子 section（如果有）

## 构建生产版本

```bash
npm run build
```

构建完成后，可以通过以下命令预览生产版本：

```bash
npm run preview
```

## Recommended IDE Setup

[VS Code](https://code.visualstudio.com/) + [Vue (Official)](https://marketplace.visualstudio.com/items?itemName=Vue.volar)
