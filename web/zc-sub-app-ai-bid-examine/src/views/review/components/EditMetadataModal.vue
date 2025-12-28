<template>
  <a-modal
    v-model:open="visible"
    title="编辑文档元信息"
    width="600px"
    @ok="handleSave"
    @cancel="handleCancel"
  >
    <a-form :label-col="{ span: 8 }" :wrapper-col="{ span: 16 }">
      <a-form-item label="文件名">
        <a-input v-model:value="formData.filename" disabled />
      </a-form-item>

      <a-form-item label="推理范围">
        <a-space>
          <a-input-number
            v-model:value="formData.infer_range[0]"
            :min="0"
            placeholder="起始页"
            style="width: 120px"
          />
          <span>-</span>
          <a-input-number
            v-model:value="formData.infer_range[1]"
            :min="0"
            placeholder="结束页"
            style="width: 120px"
          />
        </a-space>
      </a-form-item>

      <a-form-item label="阶段1标注状态">
        <a-switch v-model:checked="formData.stage1_gt_status" />
        <span style="margin-left: 8px">{{ formData.stage1_gt_status ? '已完成' : '未完成' }}</span>
      </a-form-item>

      <a-form-item label="阶段2标注状态">
        <a-switch v-model:checked="formData.stage2_gt_status" />
        <span style="margin-left: 8px">{{ formData.stage2_gt_status ? '已完成' : '未完成' }}</span>
      </a-form-item>

      <a-form-item label="阶段3标注状态">
        <a-switch v-model:checked="formData.stage3_gt_status" />
        <span style="margin-left: 8px">{{ formData.stage3_gt_status ? '已完成' : '未完成' }}</span>
      </a-form-item>

      <a-form-item label="是否完成推理">
        <a-switch v-model:checked="formData.infer_completed" />
        <span style="margin-left: 8px">{{ formData.infer_completed ? '已完成' : '未完成' }}</span>
      </a-form-item>
    </a-form>
  </a-modal>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { message } from 'ant-design-vue'

interface Props {
  open: boolean
  metadata: {
    filename?: string
    stage1_gt_status?: boolean
    stage2_gt_status?: boolean
    stage3_gt_status?: boolean
    infer_range?: [number, number]
    infer_completed?: boolean
  }
  runName?: string
}

const props = defineProps<Props>()
const emit = defineEmits(['update:open', 'save'])

const visible = ref(false)
const formData = ref({
  filename: '',
  stage1_gt_status: false,
  stage2_gt_status: false,
  stage3_gt_status: false,
  infer_range: [0, 0] as [number, number],
  infer_completed: false
})

// 监听 open 变化
watch(() => props.open, (newVal) => {
  visible.value = newVal
  if (newVal) {
    // 打开时初始化表单数据
    formData.value = {
      filename: props.metadata.filename || '',
      stage1_gt_status: props.metadata.stage1_gt_status || false,
      stage2_gt_status: props.metadata.stage2_gt_status || false,
      stage3_gt_status: props.metadata.stage3_gt_status || false,
      infer_range: props.metadata.infer_range || [0, 0],
      infer_completed: props.metadata.infer_completed || false
    }
  }
})

// 监听 visible 变化，同步到父组件
watch(visible, (newVal) => {
  emit('update:open', newVal)
})

const handleSave = async () => {
  if (!props.runName) {
    message.error('缺少 runName 信息')
    return
  }

  if (formData.value.infer_range[0] > formData.value.infer_range[1]) {
    message.error('起始页不能大于结束页')
    return
  }

  try {
    const response = await fetch('http://localhost:3000/api/runs/metadata/update', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        runName: props.runName,
        filename: formData.value.filename,
        metadata: {
          stage1_gt_status: formData.value.stage1_gt_status,
          stage2_gt_status: formData.value.stage2_gt_status,
          stage3_gt_status: formData.value.stage3_gt_status,
          infer_range: formData.value.infer_range,
          infer_completed: formData.value.infer_completed
        }
      })
    })

    const result = await response.json()

    if (!response.ok || !result.success) {
      throw new Error(result.error || 'API请求失败')
    }

    message.success('元信息更新成功')
    emit('save', formData.value)
    visible.value = false
  } catch (error: any) {
    console.error('❌ 元信息更新失败:', error)
    message.error(`更新失败: ${error.message}`)
  }
}

const handleCancel = () => {
  visible.value = false
}
</script>

<style scoped>
.ant-form-item {
  margin-bottom: 16px;
}
</style>
