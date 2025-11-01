<script lang="ts" setup>
import { Button } from 'ant-design-vue'
import { useRouter } from 'vue-router'
import { onMounted, onBeforeUnmount } from 'vue'

const router = useRouter()

function goHome() {
  router.push({name: 'Home'})
}

// let timer = null

// onMounted(() => {
//   if(timer){
//     clearTimeout(timer)
//   }
//   timer = setTimeout(() => {
//     goHome()
//     timer = null
//   }, 3000)
// })

// onBeforeUnmount(() => {
//   clearTimeout(timer)
//   timer = null
// })

</script>

<template>
  <div class="flex h-full">
    <div class="px-4 m-auto space-y-4 text-center max-[400px]">
      <h1 class="text-4xl text-slate-800 dark:text-neutral-200">
        抱歉，页面未找到！
      </h1>
      <p class="text-base text-slate-500 dark:text-neutral-400">
        您可能输入了错误的网址？请确保检查您的拼写。我们将在3秒后帮助您跳转回首页。
      </p>
      <div class="flex items-center justify-center text-center">
        <div class="w-[300px]">
          <img src="../../../icons/404.svg" alt="404">
        </div>
      </div>
      <Button type="primary" @click="goHome">
        返回首页
      </Button>
    </div>
  </div>
</template>
