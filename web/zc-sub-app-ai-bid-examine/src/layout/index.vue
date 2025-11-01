<template>
  <LayoutMain v-if="isInIcestark()"/>
  <a-flex v-else class="com-app-layout">
    <layout-aside />
    <a-flex vertical class="app-index-right">
      <LayoutMain />
    </a-flex>
  </a-flex>
</template>
<script setup lang="ts">
import isInIcestark from '@ice/stark-app/lib/isInIcestark';
import LayoutAside from '@/layout/layout-aside.vue'
import LayoutMain from '@/layout/layout-main.vue'
defineOptions({
  name: 'LayoutIndex'
})
</script>
<style scoped lang="scss">
.com-app-layout {
  height: 100%;
  .app-index-right {
    flex: 1;
  }
}
</style>
