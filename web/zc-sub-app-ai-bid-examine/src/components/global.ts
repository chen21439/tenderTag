// import   IconFont from './IconFont/index.vue'
// 需要全局注入的组件
const globalComponents: any = {
  // IconFont
}

export default {
  installed: false,
  install(app: any) {
    if (this.installed) return
    for (const k in globalComponents) {
      if (Object.prototype.hasOwnProperty.call(globalComponents, k)) {
        const comp = globalComponents[k]
        app.component(k, comp)
      }
    }
    this.installed = true
  }
};
