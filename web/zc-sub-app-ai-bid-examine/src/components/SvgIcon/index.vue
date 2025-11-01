<script setup lang="ts">
import { computed, useAttrs } from 'vue'
import { Icon } from '@iconify/vue'
defineOptions({ name: 'SvgIcon' })
interface Props {
  icon: string
  color?: string
}

const props = withDefaults(defineProps<Props>(), {
  color: ''
})
const attrs = useAttrs()
const bindAttrs = computed<{ class: string; style: string }>(() => ({
  class: (attrs.class as string) || '',
  style: (attrs.style as string) || ''
}))

const symbolId = computed(() => `#${props.icon}`)
const isIcon = computed(() => props.icon?.startsWith('icon'))
</script>

<template>
  <svg v-if="isIcon"  class="svg-icon" :color="color">
    <use :xlink:href="symbolId" rel="external nofollow" :fill="color" />
  </svg>
  <Icon v-else :icon="icon" class="svg-icon" v-bind="bindAttrs" />
</template>
<style scoped>
.svg-icon {
  fill: currentColor;
}

/* 强制覆盖内部fill属性 */
.svg-icon :deep(path) {
  fill: currentColor;
}
</style>