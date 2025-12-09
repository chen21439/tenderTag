<template>
  <div class="ppt-slide-base">
    <slot></slot>
  </div>
</template>

<script setup lang="ts">
defineOptions({
  name: 'PptSlideBase'
})
</script>

<style lang="scss" scoped>
.ppt-slide-base {
  width: 100%;
  height: 100%;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  display: flex;
  overflow: hidden;
}

// 响应式调整
@media (max-width: 1200px) {
  .ppt-slide-base {
    flex-direction: column;
  }
}
</style>
