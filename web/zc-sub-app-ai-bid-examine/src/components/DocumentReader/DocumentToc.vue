<template>
  <div class="document-toc">
    <div class="toc-tree">
      <TocNode
        v-for="item in items"
        :key="item.id"
        :item="item"
        :current-page="currentPage"
        :current-toc-item-id="currentTocItemId"
        @item-click="handleItemClick"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { defineProps, defineEmits } from 'vue'
import type { TocItem } from './types'
import TocNode from './TocNode.vue'

interface Props {
  items: TocItem[]
  currentPage: number
  currentTocItemId?: string
}

interface Emits {
  (e: 'item-click', item: TocItem): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const handleItemClick = (item: TocItem) => {
  emit('item-click', item)
}
</script>

<style lang="scss" scoped>
.document-toc {
  .toc-tree {
    padding: 0;
  }
}
</style>
