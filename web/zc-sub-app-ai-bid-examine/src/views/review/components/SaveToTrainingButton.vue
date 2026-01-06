<template>
  <a-button
    size="small"
    type="primary"
    @click="handleSave"
    :loading="saving"
  >
    保存文件
  </a-button>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { message, Modal } from 'ant-design-vue'
import { useMetadata } from '../hooks/useMetadata'

interface Props {
  fileName: string
  runName?: string
  isFromRuns: boolean
  useInferVersion: boolean
  pageRange?: { start: number; end: number }
}

const props = defineProps<Props>()

const saving = ref(false)
const { getMetadata, isAllStagesCompleted, getMissingStages } = useMetadata()

const handleSave = async () => {
  if (!props.fileName) {
    message.warning('没有加载的文件')
    return
  }

  // 校验 stage 状态（只对 runs 目录的文件进行校验）
  if (props.isFromRuns && props.runName) {
    const metadata = await getMetadata(props.runName, props.fileName)

    if (metadata && !isAllStagesCompleted(metadata)) {
      const missingStages = getMissingStages(metadata)

      Modal.warning({
        title: '无法保存',
        content: `该文件的 ${missingStages.join('、')} 尚未完成，请先完成所有标注阶段后再保存到训练目录。`,
      })
      return
    }
  }

  saving.value = true

  try {
    // 准备请求参数
    const payload = {
      fileName: props.fileName,
      runName: props.runName,
      isFromRuns: props.isFromRuns,
      useInferVersion: props.useInferVersion,
      pageRange: props.pageRange
    }

    console.log('📤 发送保存请求:', payload)

    // 发送到后端
    const response = await fetch('http://localhost:3000/api/save-training-data', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(payload)
    })

    const result = await response.json()

    if (!response.ok || !result.success) {
      throw new Error(result.error || '保存失败')
    }

    console.log('✅ 文件保存成功:', result.filePath)
    message.success(`文件已保存到训练目录 (${result.dataCount} 条数据)`)
  } catch (error: any) {
    console.error('❌ 保存文件失败:', error)
    message.error(`保存失败: ${error.message}`)
  } finally {
    saving.value = false
  }
}
</script>
