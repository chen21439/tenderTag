<template>
  <BaseDialog
    v-model="visible"
    title="重新审查提示"
    width="412px"
    :show-cancel-button="false"
    confirm-text="确认"
    :closable="true"
    :mask-closable="true"
    centered 
    get-container=".checklist-content"
    @confirm="handleConfirm"
    @close="handleClose"
    class="review-success-modal">

    <div class="modal-content">
      <div class="modal-text">
        系统正在努力重新审查中，请耐心等待，结果预计将在几分钟内生成。
      </div>
    </div>
  </BaseDialog>
</template>

<script setup lang="ts">
import { computed, nextTick } from 'vue'   
import BaseDialog from '@/components/BaseDialog/base-dialog.vue'

interface Props {
  open: boolean
  message?: string
  showTip?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  open: false,
  message: '',
  showTip: true
})

const emit = defineEmits<{
  'update:open': [value: boolean]
  'confirm': []
  'close': []
}>() 
const visible = computed({
  get: () => props.open,
  set: (value) => emit('update:open', value)
})

const handleClose = () => {
  emit('close') 
  visible.value = false 
}

const handleConfirm = () => {
  emit('confirm')
  visible.value = false 
}
</script>

<style lang="scss" scoped>
.modal-content {
  padding-top: 12px; 
}
</style>
