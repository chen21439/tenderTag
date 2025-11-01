<template>
  <div>
    <div
      class="examine-item"
      :class="{
        'is-selected': selectedItem === item.id,
        'is-expand': expandedItems.includes(item.id) && !isLeaf,
        'success': isLeaf && !item.reviewResult,
        'error': isLeaf && item.reviewResult === 1
      }"
      @click="toggleItem(item)">
      <div class="item-cell" :class="{'error': item.reviewResult === 1, 'has-child': !isLeaf}">
        <span v-if="!isLeaf" class="expand-icon">
          <CaretRightOutlined  :class="{ 'is-expand': expandedItems.includes(item.id) }"/>
        </span>
        <a-tooltip v-if="item.label" :title="item.label">
          <span class=" text">{{ item.label }}</span>
        </a-tooltip>
        <!-- <svg-icon v-if="isLeaf && item.reviewResult === 1" icon="icon-arrow-right1"  class="leaf-error-icon"/> -->
      </div>
      <svg-icon v-if="item.pointId" class="item-icon" :icon="isPass(item) ? 'icon-shenchadianchenggongtishi' : 'icon-shenchadianfengxiantishi'"/>
      <!-- <a-tag v-if="item.pointId" :color="isPass(item) ? 'success' : 'error'">
        {{ isPass(item) ? '通过' : `风险` }}
      </a-tag> -->
    </div>

    <div v-if="!isLeaf && expandedItems.includes(item.id)" class="sub-item">
      <examine-item
        v-for="child in item.children"
        :key="child.id"
        :item="child"
        :selected-item="selectedItem"
        :expanded-items="expandedItems"
        @toggle="$emit('toggle', $event)"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import {CaretRightOutlined } from '@ant-design/icons-vue'

interface Props {
  item: any;
  selectedItem?: string;
  expandedItems?: string[];
}

const props = withDefaults(defineProps<Props>(), {
  selectedItem: '',
  expandedItems: () => []
})

const emit = defineEmits<{ (e: 'toggle', item: any): void }>()


const isLeaf = computed(() => {
  return !props.item?.children?.length
})
function toggleItem(item: any) {
  emit('toggle', item)
}

function isPass(node: any) {
  return node.pointResult === 0 || node.reviewResult === 0
}
</script>

<style scoped lang="scss">

.examine-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 40px;
  padding:0 16px;
  border-radius: 8px;
  background-color: transparent;
  margin-bottom: 8px;
  cursor: pointer;
  &.is-expand {
      // background: var(--main-1);
    }
  &.is-selected {
    &.success {
      // background: linear-gradient(90deg, rgba(109, 209, 26, 0.15) 0%, rgba(109, 209, 26, 0) 100%);
      background: var(--main-1);
    }

    &.error {
      // background: linear-gradient(90deg, rgba(245, 34, 45, 0.15) 0%, rgba(245, 34, 45, 0) 100%);
      background:var(--error-1);
    }
  }

  &:hover {
    background: var(--main-1);
  }
}

.item-icon {
  width: 20px;
  height: 20px;
}
.item-cell {
  flex: 1;
  display: flex;
  align-items: center;
  margin-right: 16px;
  width: calc(100% - 16px);
  overflow: hidden;
  .text {
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    flex: 1;
  }
  .leaf-error-icon {
    color: var(--error-6);
    width: 20px;
    height: 20px;
    flex-shrink: 0;
  } 
  &.error {
    &::before {
      display: inline-block;
      vertical-align: middle;
      flex-shrink: 0;
      content: '';
      width: 8px;
      height: 8px;
      background: var(--error-6);
      margin: -2px 8px 0 0;
      border-radius: 50%;
    }
  }
  &.has-child {
    &::before {
      display: none
    }
  }

  .expand-icon {
    margin-right: 4px;
    cursor: pointer;
    font-size: 12px;

    .anticon {
      transform: rotate(0);
      transition: transform 0.3s;

      &.is-expand {
        transform: rotate(90deg);
      }
    }
  }
}

.sub-item {
  margin-left: 24px;
  margin-top: 8px;
  padding-left: 12px;
}
</style>
