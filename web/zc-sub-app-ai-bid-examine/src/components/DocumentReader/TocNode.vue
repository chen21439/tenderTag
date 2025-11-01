<template>
  <div class="toc-node">
    <div
      class="toc-item"
      :class="{
        'toc-item-active': currentTocItemId ? item.id === currentTocItemId : item.pageId === currentPage,
        [`toc-level-${item.level}`]: true,
        'has-children': hasChildren
      }"
      @click="handleClick"
    >
      <div class="toc-content">
        <!-- 展开/收起图标 -->
        <span
          v-if="hasChildren"
          class="toc-expand-icon"
          :class="{ 'expanded': isExpanded }"
          @click.stop="toggleExpand"
        >
          <CaretRightOutlined />
        </span>
        <span class="toc-title" :title="item.title">{{ item.title }}</span>
        <span class="toc-page">{{ item.pageId }}</span>
      </div>
    </div>

    <!-- 子节点 -->
    <div
      v-if="hasChildren && isExpanded"
      class="toc-children"
      :class="{ 'toc-children-expanded': isExpanded }"
    >
      <TocNode
        v-for="child in item.children"
        :key="child.id"
        :item="child"
        :current-page="currentPage"
        :current-toc-item-id="currentTocItemId"
        @item-click="handleItemClick"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { defineProps, defineEmits, ref, computed } from 'vue'
import { CaretRightOutlined } from '@ant-design/icons-vue'
import type { TocItem } from './types'

interface Props {
  item: TocItem
  currentPage: number
  currentTocItemId?: string
}

interface Emits {
  (e: 'item-click', item: TocItem): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// 展开状态
const isExpanded = ref(true) // 默认展开

// 计算属性
const hasChildren = computed(() => {
  return props.item.children && props.item.children.length > 0
})

// 方法
const handleClick = () => {
  emit('item-click', props.item)
}

const handleItemClick = (item: TocItem) => {
  emit('item-click', item)
}

const toggleExpand = () => {
  isExpanded.value = !isExpanded.value
}
</script>

<style lang="scss" scoped>
.toc-node {
  .toc-item {
    padding: 6px 12px;
    cursor: pointer;
    border-radius: 4px;
    margin: 2px 0;
    transition: all 0.2s ease;

    &:hover {
      background-color: #f5f5f5;
    }

    &.toc-item-active {
      background-color: #e6f7ff;
      color: #1890ff;
      font-weight: 500;
    }

    &.has-children {
      .toc-content {
        .toc-expand-icon {
          margin-right: 4px;
        }
      }
    }

    .toc-content {
      display: flex;
      align-items: center;

      .toc-expand-icon {
        width: 16px;
        height: 16px;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        transition: transform 0.2s ease;
        color: #999;

        &:hover {
          color: #1890ff;
        }

        &.expanded {
          transform: rotate(90deg);
        }
      }

      .toc-title {
        flex: 1;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        font-size: 13px;
        line-height: 1.4;
      }

      .toc-page {
        font-size: 11px;
        color: #999;
        margin-left: 8px;
        flex-shrink: 0;
      }
    }

    // 不同级别的缩进
    &.toc-level-0 {
      padding-left: 12px;
      font-weight: 500;

      .toc-title {
        font-size: 14px;
      }
    }

    &.toc-level-1 {
      padding-left: 24px;
    }

    &.toc-level-2 {
      padding-left: 36px;
    }

    &.toc-level-3 {
      padding-left: 48px;
    }

    &.toc-level-4 {
      padding-left: 60px;
    }
  }

  .toc-children {
    margin-left: 0;
    overflow: hidden;
    transition: all 0.3s ease;

    &.toc-children-expanded {
      animation: expandChildren 0.3s ease;
    }
  }
}

@keyframes expandChildren {
  from {
    opacity: 0;
    max-height: 0;
  }
  to {
    opacity: 1;
    max-height: 1000px;
  }
}
</style>
