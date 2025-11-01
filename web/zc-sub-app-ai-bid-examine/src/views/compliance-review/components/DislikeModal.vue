<template>
  <BaseDialog
    v-model="visible"
    title="请选择反馈原因"
    width="412px"
    :show-cancel-button="true"
    :show-confirm-button="true"
    cancel-text="取消"
    confirm-text="确定"
    @confirm="handleConfirm"
    @cancel="handleCancel"
  >
    <div class="dislike-modal-content">
      <!-- 预设原因选项 -->
      <div class="reason-options">
        <a-checkbox-group v-model:value="selectedReasons" @change="handleReasonChange">
          <div class="reason-item">
            <a-checkbox value="修改建议有误">修改建议有误</a-checkbox>
          </div>
          <div class="reason-item">
            <a-checkbox value="原文定位有误">原文定位有误</a-checkbox>
          </div>
          <div class="reason-item">
            <a-checkbox value="审查依据有误">审查依据有误</a-checkbox>
          </div>
          <div class="reason-item">
            <a-checkbox value="审查结果有误">审查结果有误</a-checkbox>
          </div>
        </a-checkbox-group>
      </div>

      <!-- 其他意见输入框 -->
      <div class="other-opinion">
        <div class="opinion-label">其他意见（可选）</div>
        <a-textarea
          v-model:value="otherOpinion"
          placeholder="Text"
          :rows="4"
          :maxlength="500"
          show-count
        />
      </div>
    </div>
  </BaseDialog>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import BaseDialog from '@/components/BaseDialog/base-dialog.vue'
defineOptions({
  name: 'DislikeModal'
})

interface Props {
  modelValue: boolean 
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: false
})

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'confirm': [reasons: string[], otherOpinion: string]
  'cancel': []
}>()

// 弹框显示状态
const visible = computed({
  get: () => props.modelValue,
  set: (val: boolean) => emit('update:modelValue', val)
})

// 选中的原因
const selectedReasons = ref<string[]>([])

// 其他意见
const otherOpinion = ref('')

// 处理原因选择变化
const handleReasonChange = (checkedValues: string[]) => {
  selectedReasons.value = checkedValues
}

// 确认提交
const handleConfirm = () => {
  emit('confirm', selectedReasons.value, otherOpinion.value)
  // 不在这里关闭弹框，让父组件控制
}

// 关闭弹框的方法（供父组件调用）
const closeModal = () => {
  handleReset()
  visible.value = false
}

// 暴露方法给父组件
defineExpose({
  closeModal
})

// 取消操作
const handleCancel = () => {
  emit('cancel')
  handleReset()
  visible.value = false
}

// 重置表单
const handleReset = () => {
  selectedReasons.value = []
  otherOpinion.value = ''
} 
</script>

<style lang="scss" scoped>
.dislike-modal-content {
  .reason-options { 
    .reason-item {
      width: 100%;
      margin-bottom: 8px; 
    }
  }

   .opinion-label {
    margin-bottom: 8px; 
   }
}
</style>
