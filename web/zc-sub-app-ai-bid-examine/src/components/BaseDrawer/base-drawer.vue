<template>
  <a-drawer
    v-bind="$attrs"
    v-model:open="visible"
    :closable="closable"
    :placement="placement"
    :title="title"
    :width="width"
    @close="onClose"
  >

    <a-spin :spinning="loading">
      <slot></slot>
    </a-spin>

    <template #extra>
      <slot name="extra">
        <a-space>
          <a-button v-if="cancelVisible" @click="onCancel">{{ cancelText }}</a-button>
          <a-button v-if="okVisible" type="primary" @click="onOk" :loading="okLoading" :disabled="okDisabled">{{ okText }}</a-button>
        </a-space>
      </slot>
    </template>

    <!-- 底部操作区域 -->
    <template #footer v-if="footerVisible">
      <div class="drawer-footer"> 
        <slot name="footer">
          <a-button v-if="cancelVisible" @click="onCancel">{{ cancelText }}</a-button>
          <a-button v-if="okVisible" type="primary" @click="onOk" :loading="okLoading" :disabled="okDisabled">{{ okText }}</a-button> 
        </slot>
      </div>
    </template>
  </a-drawer>
</template>

<script setup lang="ts">
defineOptions({ name: 'BaseDrawer' })
import { computed } from 'vue'

const emits = defineEmits([
  'cancel',
  'close',
  'ok',
  'update:model-value'
])

/**
 * cancelText 取消按钮文字
 * okText 确认按钮文字
 * placement 方向 'top' | 'right' | 'bottom' | 'left'
 */
interface Props {
  modelValue: boolean
  cancelText?: string
  cancelVisible?: boolean
  closable?: boolean
  footerVisible?: boolean
  loading?: boolean
  okLoading?: boolean
  okDisabled?: boolean
  okText?: string
  okVisible?: boolean
  placement?: 'top' | 'right' | 'bottom' | 'left'
  title?: string
  width?: string | number
}

const props = withDefaults(defineProps<Props>(), {
  cancelText: '取消',
  cancelVisible: false,
  closable: true,
  footerVisible: false,
  loading: false,
  modelValue: false,
  okLoading: false,
  okDisabled: false,
  okText: '确定',
  okVisible: false,
  placement: 'right',
  title: '',
  width: 'auto'
})

const visible = computed({
  get: () => props.modelValue,
  set: (val: boolean) => emits('update:model-value', val)
})

function onClose() {
  emits('update:model-value', false)
  emits('close')
}

function onCancel() {
  emits('cancel')
}

function onOk() {
  emits('ok')
}
</script>

<style lang="scss" scoped>
.drawer-footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 12px;
  :deep(.ant-btn) { 
    display: flex;
    align-items: center;
    justify-content: center;
  }
} 
</style>
