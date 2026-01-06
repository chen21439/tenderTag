<template>
  <div class="range-section">
    <span class="range-label">范围:</span>
    <a-input-number
      v-model:value="localStart"
      placeholder="起始"
      size="small"
      :min="0"
      style="width: 80px;"
    />
    <span class="range-separator">-</span>
    <a-input-number
      v-model:value="localEnd"
      placeholder="结束"
      size="small"
      :min="0"
      style="width: 80px;"
    />
    <a-button
      size="small"
      @click="handleFilter"
    >
      过滤
    </a-button>
    <a-button
      type="primary"
      size="small"
      @click="handleSave"
      :loading="saving"
    >
      保存
    </a-button>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { message } from 'ant-design-vue'

interface Props {
  start: number
  end: number
  runName?: string
  fileName?: string
}

interface Emits {
  (e: 'update:start', value: number): void
  (e: 'update:end', value: number): void
  (e: 'filter'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const localStart = ref(props.start)
const localEnd = ref(props.end)
const saving = ref(false)

watch(() => props.start, (newVal) => {
  localStart.value = newVal
})

watch(() => props.end, (newVal) => {
  localEnd.value = newVal
})

const handleFilter = () => {
  if (localStart.value < 0 || localEnd.value < 0) {
    message.error('页码不能小于0')
    return
  }

  if (localStart.value > localEnd.value) {
    message.error('起始值不能大于结束值')
    return
  }

  emit('update:start', localStart.value)
  emit('update:end', localEnd.value)
  emit('filter')
}

const handleSave = async () => {
  if (!props.runName || !props.fileName) {
    message.warning('只支持从 runs 目录加载的文件')
    return
  }

  if (localStart.value < 0 || localEnd.value < 0) {
    message.error('页码不能小于0')
    return
  }

  if (localStart.value > localEnd.value) {
    message.error('起始值不能大于结束值')
    return
  }

  saving.value = true

  try {
    const response = await fetch(
      `http://localhost:3000/api/runs/${props.runName}/update-metadata`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          filename: props.fileName,
          infer_range: [localStart.value, localEnd.value]
        })
      }
    )

    const result = await response.json()

    if (!response.ok || !result.success) {
      throw new Error(result.error || '保存失败')
    }

    console.log('✅ 推理范围保存到 metadata.jsonl:', {
      filename: props.fileName,
      range: [localStart.value, localEnd.value]
    })
    message.success('推理范围已保存')

    emit('update:start', localStart.value)
    emit('update:end', localEnd.value)
  } catch (error: any) {
    console.error('❌ 保存推理范围失败:', error)
    message.error(`保存失败: ${error.message}`)
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.range-section {
  display: flex;
  gap: 8px;
  align-items: center;
}

.range-label {
  font-size: 14px;
  color: #333;
}

.range-separator {
  color: #999;
}
</style>
