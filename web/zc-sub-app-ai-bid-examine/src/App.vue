
<template>
  <ConfigProvider class="h-full" :theme="antTheme" :locale="zhCN">
    <StyleProvider hash-priority="high" :transformers="[legacyLogicalPropertiesTransformer]">
      <div class="com-app-container">
        <RouterView />
      </div>
    </StyleProvider>
  </ConfigProvider>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { RouterView } from 'vue-router'
import { ConfigProvider, StyleProvider, legacyLogicalPropertiesTransformer } from 'ant-design-vue'
import { useTheme } from '@/hooks/use-theme'
import  { useMenusStore } from '@/store'
import zhCN from 'ant-design-vue/es/locale/zh_CN'
const menusStore = useMenusStore()
const antTheme = computed(()=> menusStore.systemInfo.antTheme)
useTheme()
</script>
<style scoped lang="scss">
.com-app-container {
  height: 100%;
}
</style>
