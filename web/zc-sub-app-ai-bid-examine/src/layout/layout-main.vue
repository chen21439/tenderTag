<template>
  <div class="com-layout-container">
    <RouterView />
  </div>
</template>

<script lang="ts" setup>
import { RouterView } from 'vue-router'
defineOptions({
  name: 'LayoutMain'
})
</script>
<style scoped>
  .com-layout-container {
    height: 100vh;
    overflow-y: scroll;
    min-width: 1200px;
  }
</style>
