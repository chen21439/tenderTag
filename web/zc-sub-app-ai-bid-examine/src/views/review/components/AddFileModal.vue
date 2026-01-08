<template>
  <a-modal
    v-model:open="visible"
    title="添加文档到训练集"
    @ok="handleSubmit"
    @cancel="handleCancel"
    :confirmLoading="loading"
  >
    <a-form
      :model="formData"
      :rules="rules"
      ref="formRef"
      :label-col="{ span: 6 }"
      :wrapper-col="{ span: 18 }"
    >
      <a-form-item label="文件名称" name="fileName" required>
        <a-input
          v-model:value="formData.fileName"
          placeholder="请输入文件名（不含 .json 后缀）"
          @blur="handleFileNameBlur"
        />
        <div v-if="fileExistsChecking" class="check-status">
          <a-spin size="small" /> 检查中...
        </div>
        <div v-else-if="fileExists === true" class="check-status error">
          ⚠️ 该文件名已存在
        </div>
        <div v-else-if="fileExists === false" class="check-status success">
          ✓ 文件名可用
        </div>
      </a-form-item>

      <a-form-item label="推理页码范围">
        <a-space>
          <a-input-number
            v-model:value="formData.inferRangeStart"
            :min="0"
            :max="999"
            placeholder="起始页"
            style="width: 120px"
          />
          <span>-</span>
          <a-input-number
            v-model:value="formData.inferRangeEnd"
            :min="0"
            :max="999"
            placeholder="结束页"
            style="width: 120px"
          />
        </a-space>
        <div class="hint-text">默认 0-999 表示处理所有页面</div>
      </a-form-item>
    </a-form>
  </a-modal>
</template>

<script setup lang="ts">
import { ref, reactive, watch } from 'vue'
import { message } from 'ant-design-vue'
import type { FormInstance } from 'ant-design-vue'

interface Props {
  open: boolean
  runName: string
}

interface Emits {
  (e: 'update:open', value: boolean): void
  (e: 'success', fileName: string): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const visible = ref(false)
const loading = ref(false)
const fileExistsChecking = ref(false)
const fileExists = ref<boolean | null>(null)
const formRef = ref<FormInstance>()

const formData = reactive({
  fileName: '',
  inferRangeStart: 0,
  inferRangeEnd: 999
})

const rules = {
  fileName: [
    { required: true, message: '请输入文件名', trigger: 'blur' },
    { pattern: /^[^<>:"/\\|?*]+$/, message: '文件名包含非法字符', trigger: 'blur' }
  ]
}

// 同步 visible 状态
watch(() => props.open, (val) => {
  visible.value = val
  if (val) {
    // 打开弹窗时重置表单
    resetForm()
  }
})

watch(visible, (val) => {
  emit('update:open', val)
})

// 重置表单
const resetForm = () => {
  formData.fileName = ''
  formData.inferRangeStart = 0
  formData.inferRangeEnd = 999
  fileExists.value = null
  formRef.value?.clearValidate()
}

// 检查文件名是否存在
const checkFileExists = async (fileName: string) => {
  if (!fileName.trim() || !props.runName) {
    fileExists.value = null
    return
  }

  fileExistsChecking.value = true
  fileExists.value = null

  try {
    const response = await fetch(
      `http://localhost:3000/api/runs/metadata?runName=${props.runName}&filename=${fileName}.json`
    )
    const result = await response.json()

    if (response.ok && result.success && result.metadata) {
      // 文件已存在
      fileExists.value = true
    } else {
      // 文件不存在
      fileExists.value = false
    }
  } catch (error) {
    console.error('❌ 检查文件是否存在失败:', error)
    fileExists.value = null
  } finally {
    fileExistsChecking.value = false
  }
}

// 文件名输入框失焦时检查
const handleFileNameBlur = () => {
  if (formData.fileName.trim()) {
    checkFileExists(formData.fileName.trim())
  }
}

// 提交表单
const handleSubmit = async () => {
  if (!formRef.value) return

  try {
    // 验证表单
    await formRef.value.validate()

    // 检查文件是否已存在
    if (fileExists.value === null) {
      await checkFileExists(formData.fileName.trim())
    }

    if (fileExists.value === true) {
      message.error('文件名已存在，请使用其他名称')
      return
    }

    // 验证页码范围
    if (formData.inferRangeStart > formData.inferRangeEnd) {
      message.error('起始页不能大于结束页')
      return
    }

    loading.value = true

    // 发送请求到后端
    const response = await fetch(
      `http://localhost:3000/api/runs/${props.runName}/add-file`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          fileName: formData.fileName.trim() + '.json',
          inferRange: [formData.inferRangeStart, formData.inferRangeEnd]
        })
      }
    )

    const result = await response.json()

    if (!response.ok || !result.success) {
      throw new Error(result.error || '添加文件失败')
    }

    message.success('文件添加成功')
    emit('success', formData.fileName.trim() + '.json')
    visible.value = false
  } catch (error: any) {
    console.error('❌ 添加文件失败:', error)
    message.error(`添加失败: ${error.message}`)
  } finally {
    loading.value = false
  }
}

// 取消
const handleCancel = () => {
  visible.value = false
}
</script>

<style scoped>
.check-status {
  margin-top: 8px;
  font-size: 12px;
}

.check-status.error {
  color: #ff4d4f;
}

.check-status.success {
  color: #52c41a;
}

.hint-text {
  margin-top: 4px;
  font-size: 12px;
  color: #999;
}
</style>
