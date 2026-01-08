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
        />
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
  formRef.value?.clearValidate()
}

// 提交表单
const handleSubmit = async () => {
  if (!formRef.value) return

  try {
    // 验证表单
    await formRef.value.validate()

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
.hint-text {
  margin-top: 4px;
  font-size: 12px;
  color: #999;
}
</style>
