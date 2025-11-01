
## 前端框架
基于vue3.5 + vite + ts + ant-design-vue 开发
## 前置要求

### Node

（`node >= 18` 需要安装 [fetch polyfill](https://github.com/developit/unfetch#usage-as-a-polyfill)），使用 [nvm](https://github.com/nvm-sh/nvm) 可管理本地多个 `node` 版本

```shell
node -v
```

### 前端

根目录下运行以下命令

```shell
pnpm i
```
### 前端网页

根目录下运行以下命令

```shell
开发环境：
  文件：.env
  运行：pnpm run dev
  打包：pnpm run build
```
```shell

测试环境：
  文件：.env
  运行：pnpm run test
  打包：pnpm run build:test
```
```shell
生产环境：
  文件：.env.prod
  运行：pnpm run prod
  打包：pnpm run build:prod
```
