<template>
  <div class="empty-ppt">
    <PptSlideBase>
      <div class="content">
        <h1 class="title">第二页</h1>
        <p class="subtitle">这是一个空白页面，用于测试翻页效果</p>
      </div>
    </PptSlideBase>
  </div>
</template>

<script setup lang="ts">
import PptSlideBase from './PptSlideBase.vue'

defineOptions({
  name: 'EmptyPpt'
})
</script>

<style lang="scss" scoped>
.empty-ppt {
  width: 100%;
  height: 100%;
  background: #fff;
  display: flex;

  .content {
    width: 100%;
    height: 100%;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    background: #fafafa;

    .title {
      font-size: 48px;
      font-weight: bold;
      color: #1a1a2e;
      margin-bottom: 20px;
    }

    .subtitle {
      font-size: 18px;
      color: #666;
    }
  }
}
</style>
