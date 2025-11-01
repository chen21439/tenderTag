<template>
  <BaseDrawer
    v-model="visible"
    :title="isEdit ? '编辑规则' : '新建规则'"
    width="600px" 
    :ok-visible="false"
    :footer-visible="true"
    cancel-text="取消"
    @cancel="handleCancel"
    @close="handleClose"
  >
    <div class="rule-editor">
      <div class="rule-editor-content"> 
        <div class="rule-config">
          <!-- 基础信息 -->
          <div class="config-section">
            <h4 class="section-title">基础信息</h4>
            <div class="form-group">
              <label class="form-label required">规则名称</label>
              <a-input
                v-model:value="formData.name"
                placeholder="请输入规则名称"
                :maxlength="100"
                :status="validationErrors.name ? 'error' : ''"
                @input="clearValidationError('name')"
              />
              <div v-if="validationErrors.name" class="error-message">
                {{ validationErrors.name }}
              </div>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label class="form-label required">风险级别</label>
                <a-select
                  v-model:value="formData.violationLevelCode"
                  placeholder="请选择风险级别"
                  style="width: 100%"
                  :status="validationErrors.violationLevelCode ? 'error' : ''"
                  @change="clearValidationError('violationLevelCode')"
                >
                  <a-select-option v-for="item in riskOptions" :key="item.code" :value="item.code">
                    {{ item.name }}
                  </a-select-option>
                </a-select>
                <div v-if="validationErrors.violationLevelCode" class="error-message">
                  {{ validationErrors.violationLevelCode }}
                </div>
              </div>
              <div class="form-group">
                <label class="form-label required">启用状态</label>
                <a-switch
                  v-model:checked="formData.enabled"
                  checked-children="启用"
                  un-checked-children="停用"
                />
              </div>
            </div>
          </div>

          <!-- 标签选择 -->
          <div class="config-section">
            <h4 class="section-title">标签选择</h4>
            <div class="form-group">
              <label class="form-label">规则标签</label>
              <div class="tag-selection">
                <a-checkbox-group v-model:value="formData.lableList">
                  <a-checkbox
                    v-for="item in category"
                    :key="item.code"
                    :value="item.code"
                    class="tag-checkbox"
                  >
                    {{ item.name }}
                  </a-checkbox>
                </a-checkbox-group>
              </div>
            </div>
          </div>

          <!-- 高级参数 -->
          <div class="config-section">
            <h4 class="section-title">高级参数</h4>
            <div class="form-group">
              <label class="form-label">置信度</label>
              <div class="threshold-slider">
                <a-slider
                  v-model:value="formData.threshold"
                  :min="0"
                  :max="100"
                  :step="1"
                  :marks="thresholdMarks"
                  :tooltip-formatter="(value: number) => `${value}%`"
                  @change="handleThresholdChange"
                />
                <div class="threshold-value">
                  {{ formData.threshold }}% 
                </div>
              </div>
            </div>
          </div>

        </div>
      </div>
    </div>

    <!-- 底部操作按钮 -->
    <template #footer>
      <div class="rule-editor-footer">  
        <a-button @click="handleCancel">取消</a-button>
        <!-- <a-button @click="handleSaveAsDraft" :loading="saveLoading">保存为草稿</a-button> -->
        <a-button type="primary" @click="handleSave" :loading="saveLoading">保存规则</a-button> 
      </div>
    </template>
  </BaseDrawer>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue'
import { BaseDrawer } from '@/components/BaseDrawer'
import {
  thresholdMarks
} from '@/views/hooks/examine'
import {apiRuleSaveOrUpdate} from '@/api/examine'
interface Props {
  modelValue: boolean
  riskOptions: any[]
  category: any[]
  ruleData: Record<string, any>
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: false,
  ruleData: () => ({})
})

const emit = defineEmits(['update:modelValue', 'save', 'cancel'])

// ==================== 响应式数据 ====================
const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const isEdit = computed(() => !!props.ruleData?.id)

const saveLoading = ref(false)

// 表单数据
const defaultFormData = {
  name: '',
  violationLevelCode: '',
  enabled: false,
  threshold: 60,
  lableList: []
}
let formData = ref<Record<string, any>>(defaultFormData)

// 验证错误状态
const validationErrors = reactive<Record<string, string>>({})

// 清除验证错误
const clearValidationError = (field: string) => {
  if (validationErrors[field]) {
    delete validationErrors[field]
  }
}

// 表单验证函数
const validateForm = (): boolean => {
  // 清空之前的错误
  Object.keys(validationErrors).forEach(key => {
    delete validationErrors[key]
  })

  let isValid = true

  // 验证规则名称
  if (!formData.value.name || formData.value.name.trim() === '') {
    validationErrors.name = '请输入规则名称'
    isValid = false
  }

  // 验证风险等级
  if (!formData.value.violationLevelCode) {
    validationErrors.violationLevelCode = '请选择风险等级'
    isValid = false
  }

  return isValid
}

// 初始化表单数据
const initFormData = () => {   
  formData.value = {
    ...defaultFormData,
    ...props.ruleData, 
    enabled: props.ruleData.status === 1 ? true : false
  } 
  // 清空验证错误
  Object.keys(validationErrors).forEach(key => {
    delete validationErrors[key]
  })
}
// ==================== 方法 ====================
// 处理阈值变化
const handleThresholdChange = (value: number) => {
  if (value < 60) {
    // 静默修正到最小值，不显示提示
    formData.value.threshold = 60
  }
}
 
// 监听弹窗显示状态，初始化表单
watch(
  () => visible.value,
  (isVisible) => {
    if (isVisible) {
      initFormData()
    }
  }
)



// ==================== 方法 ====================
// 处理取消
const handleCancel = () => {
  visible.value = false
  emit('cancel')
}

// 处理关闭
const handleClose = () => {
  visible.value = false
}

// 处理保存
const handleSave = async () => {
  if (!validateForm()) return
  saveLoading.value = true 
  const { id , name , lableList , violationLevelCode , threshold , enabled } = formData.value
  const {data, err} = await apiRuleSaveOrUpdate({
    id,
    name,
    categoryList: lableList ?? [],
    violationLevel:violationLevelCode,
    threshold,
    status: enabled ? 1 : 0
  })
  if (err) return 
  saveLoading.value = false
  emit('save', formData)
  visible.value = false 
}


</script>

<style lang="scss" scoped>
.rule-editor {
  height: 100%;
  display: flex;
  flex-direction: column;

  .rule-editor-content {
    flex: 1;
    padding: 24px;
    overflow-y: auto;
  }

  .rule-config {
    max-width: 800px;
    margin: 0 auto;
  }

  .config-section {
    margin-bottom: 32px;
    padding-bottom: 24px;
    border-bottom: 1px solid #f0f0f0;

    &:last-child {
      margin-bottom: 0;
      border-bottom: none;
    }
  }

  .section-title {
    font-size: 16px;
    font-weight: 600;
    color: #262626;
    margin: 0 0 16px 0;
    position: relative;
    padding-left: 12px;

    &::before {
      content: '';
      position: absolute;
      left: 0;
      top: 50%;
      transform: translateY(-50%);
      width: 3px;
      height: 16px;
      background: var(--main-6);
      border-radius: 2px;
    }
  }

  .form-group {
    margin-bottom: 16px;

    &:last-child {
      margin-bottom: 0;
    }
  }

  .form-label {
    display: block;
    font-size: 14px;
    font-weight: 600;
    color: #374151;
    margin-bottom: 10px;
    letter-spacing: 0.5px;

    &.required::before {
      content: '*';
      color: #ef4444;
      margin-right: 6px;
      font-weight: 700;
    }
  }

  .error-message {
    color: #ef4444;
    font-size: 12px;
    margin-top: 4px;
    line-height: 1.4;
  }

  .form-row {
    display: flex;
    gap: 16px;

    .form-group {
      flex: 1;
    }
  }

  // 阈值滑动条样式
  .threshold-slider {
    display: flex;
    align-items: center;
    gap: 16px; 
    .ant-slider {
      flex: 1;
    }

    .threshold-value {
      min-width: 40px;
      font-weight: 500;
      color: var(--main-6);
      text-align: center;
    }
  }

  // 标签选择样式
  .tag-selection {
    .ant-checkbox-group {
      display: flex;
      flex-wrap: wrap;
      gap: 8px 12px;
    }

    .tag-checkbox {
      margin-right: 0;

      .ant-checkbox-wrapper {
        padding: 6px 12px;
        border: 1px solid #d9d9d9;
        border-radius: 6px;
        transition: all 0.2s ease;

        &:hover {
          border-color: #40a9ff;
          background-color: #f0f8ff;
        }
      }

      .ant-checkbox-checked + span {
        color: var(--main-6);
        font-weight: 500;
      }

      .ant-checkbox-wrapper-checked {
        border-color: var(--main-6);
        background-color: #e6f7ff;
      }
    }
  }

  // 阈值滑动条样式
  .threshold-slider {
    display: flex;
    align-items: center;
    gap: 16px;
    margin-bottom: 8px;
    position: relative;

    .ant-slider {
      flex: 1;

      // 禁用区域样式
      &::before {
        content: '';
        position: absolute;
        left: 0;
        top: 50%;
        transform: translateY(-50%);
        width: 60%; // 0-0.6的区域
        height: 4px;
        background: repeating-linear-gradient(
          45deg,
          #ff4d4f20,
          #ff4d4f20 4px,
          transparent 4px,
          transparent 8px
        );
        border-radius: 2px;
        z-index: 1;
        pointer-events: none;
      }
    }

    .threshold-value {
      min-width: 80px;
      font-weight: 500;
      color: var(--main-6);
      text-align: center;
      font-size: 14px;

      .recommended-tag {
        display: inline-block;
        background: var(--main-6);
        color: white;
        font-size: 10px;
        padding: 2px 6px;
        border-radius: 8px;
        margin-left: 6px;
        font-weight: 600;
      }
    }
  } 
} 
// 底部操作按钮
.rule-editor-footer{
  display: flex;
  justify-content: flex-end; 
  gap:12px;
}
</style>
