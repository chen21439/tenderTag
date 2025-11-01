<template>
  <a-modal
    v-model:open="visible"
    title="请选择反馈原因"
    width="400px"
    :footer="null"
    :closable="true"
    destroy-on-close
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
            <a-checkbox value="推理原因有误">推理原因有误</a-checkbox>
          </div>
          <div class="reason-item">
            <a-checkbox value="风险评级有误">风险评级有误</a-checkbox>
          </div>
        </a-checkbox-group>
      </div>

      <!-- 其他意见输入框 -->
      <div class="other-feedback">
        <div class="other-label">其他意见（可选）</div>
        <a-textarea
          v-model:value="otherFeedback"
          placeholder="Text"
          :rows="4"
          :maxlength="200"
          show-count
          class="feedback-textarea"
        />
      </div>

      <!-- 底部按钮 -->
      <div class="modal-footer">
        <a-button @click="handleCancel">取消</a-button>
        <a-button type="primary" @click="handleConfirm">确定</a-button>
      </div>
    </div>
  </a-modal>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

defineOptions({
  name: 'DislikeModal'
})

interface Props {
  modelValue: boolean
}

interface DislikeData {
  reasons: string[]
  otherFeedback: string
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: false
})

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'confirm': [data: DislikeData]
  'cancel': []
}>()

// 弹框显示状态
const visible = computed({
  get: () => props.modelValue,
  set: (val: boolean) => emit('update:modelValue', val)
})

// 选中的原因
const selectedReasons = ref<string[]>([])

// 其他反馈意见
const otherFeedback = ref('')

// 处理原因选择变化
const handleReasonChange = (checkedValues: string[]) => {
  selectedReasons.value = checkedValues
}

// 确认提交
const handleConfirm = () => {
  const data: DislikeData = {
    reasons: selectedReasons.value,
    otherFeedback: otherFeedback.value.trim()
  }
  
  emit('confirm', data)
  handleReset()
}

// 取消操作
const handleCancel = () => {
  emit('cancel')
  handleReset()
}

// 重置表单数据
const handleReset = () => {
  selectedReasons.value = []
  otherFeedback.value = ''
  visible.value = false
}
</script>

<style lang="scss" scoped>
.dislike-modal-content {
  padding: 8px 0;

  .reason-options {
    margin-bottom: 20px;

    .reason-item {
      margin-bottom: 12px;
      
      :deep(.ant-checkbox-wrapper) {
        font-size: 14px;
        color: #262626;
        line-height: 22px;
        
        .ant-checkbox {
          margin-right: 8px;
          
          .ant-checkbox-inner {
            width: 16px;
            height: 16px;
            border-radius: 2px;
          }
        }
        
        &.ant-checkbox-wrapper-checked {
          .ant-checkbox-inner {
            background-color: #1890ff;
            border-color: #1890ff;
          }
        }
      }
    }
  }

  .other-feedback {
    margin-bottom: 24px;

    .other-label {
      font-size: 14px;
      color: #262626;
      margin-bottom: 8px;
      line-height: 22px;
    }

    .feedback-textarea {
      :deep(.ant-input) {
        font-size: 14px;
        line-height: 1.5;
        
        &::placeholder {
          color: #bfbfbf;
        }
      }
    }
  }

  .modal-footer {
    display: flex;
    justify-content: flex-end;
    gap: 8px;
    margin-top: 16px;

    .ant-btn {
      height: 32px;
      padding: 4px 15px;
      font-size: 14px;
      border-radius: 6px;
      
      &:not(.ant-btn-primary) {
        color: #595959;
        border-color: #d9d9d9;
        background: #fff;
        
        &:hover {
          color: #1890ff;
          border-color: #1890ff;
        }
      }
      
      &.ant-btn-primary {
        background: #1890ff;
        border-color: #1890ff;
        
        &:hover {
          background: #40a9ff;
          border-color: #40a9ff;
        }
      }
    }
  }
}

// 自定义modal样式
:deep(.ant-modal) {
  .ant-modal-header {
    padding: 16px 24px;
    border-bottom: 1px solid #f0f0f0;
    
    .ant-modal-title {
      font-size: 16px;
      font-weight: 500;
      color: #262626;
    }
  }
  
  .ant-modal-body {
    padding: 20px 24px;
  }
  
  .ant-modal-close {
    top: 16px;
    right: 16px;
    
    .ant-modal-close-x {
      width: 22px;
      height: 22px;
      line-height: 22px;
      font-size: 12px;
      color: #8c8c8c;
      
      &:hover {
        color: #262626;
      }
    }
  }
}
</style>
