<template>
  <div class="tag-statistics">
    <a-card title="标记统计" size="small">
      <a-space direction="vertical" :size="12" style="width: 100%">
        <a-row :gutter="8">
          <a-col :span="12">
            <a-statistic
              title="章节标题"
              :value="statistics.sectionHeaders"
              :value-style="{ color: '#1890ff', fontSize: '18px' }"
            >
              <template #prefix>
                <FileTextOutlined />
              </template>
            </a-statistic>
          </a-col>
          <a-col :span="12">
            <a-statistic
              title="总项数"
              :value="statistics.totalItems"
              :value-style="{ color: '#8c8c8c', fontSize: '18px' }"
            />
          </a-col>
        </a-row>

        <a-divider style="margin: 8px 0" />

        <a-statistic
          v-if="hasLevelField"
          title="Level >= 101"
          :value="statistics.highLevelCount"
          :value-style="{ color: '#52c41a' }"
        >
          <template #prefix>
            <TagOutlined />
          </template>
        </a-statistic>

        <a-statistic
          v-else
          title="已分类标签"
          :value="statistics.labeledCount"
          :value-style="{ color: '#52c41a' }"
        >
          <template #prefix>
            <TagOutlined />
          </template>
        </a-statistic>

        <a-divider style="margin: 8px 0" />

        <a-descriptions v-if="hasLevelField" :column="1" size="small" bordered>
          <a-descriptions-item label="Level < 101">
            {{ statistics.lowLevelCount }}
          </a-descriptions-item>
          <a-descriptions-item label="Level 101-200">
            {{ statistics.level101to200 }}
          </a-descriptions-item>
          <a-descriptions-item label="Level > 200">
            {{ statistics.levelAbove200 }}
          </a-descriptions-item>
        </a-descriptions>

        <a-descriptions v-else :column="1" size="small" bordered>
          <a-descriptions-item label="正文内容">
            {{ statistics.textContent }}
          </a-descriptions-item>
          <a-descriptions-item label="表格">
            {{ statistics.tables }}
          </a-descriptions-item>
          <a-descriptions-item label="列表">
            {{ statistics.lists }}
          </a-descriptions-item>
        </a-descriptions>

        <a-button type="primary" size="small" block @click="$emit('refresh')">
          刷新统计
        </a-button>
      </a-space>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { computed, watch } from 'vue'
import { FileTextOutlined, TagOutlined } from '@ant-design/icons-vue'

interface TaggedItem {
  item_id?: string
  id?: number
  level?: number
  label?: string
  label_level1?: string
  label_level2?: string
  [key: string]: any
}

interface Props {
  taggedData?: TaggedItem[]  // 标记数据
  autoRefresh?: boolean       // 是否自动刷新
}

const props = withDefaults(defineProps<Props>(), {
  taggedData: () => [],
  autoRefresh: true
})

const emit = defineEmits<{
  refresh: []
}>()

// 检测数据是否有 level 字段
const hasLevelField = computed(() => {
  const data = props.taggedData || []
  return data.length > 0 && data.some(item => typeof item.level === 'number')
})

// 统计数据
const statistics = computed(() => {
  const data = props.taggedData || []
  const totalItems = data.length

  // 新格式：所有项都是标题，没有 label 字段
  // 统计章节标题数量（等于总数）
  const sectionHeaders = data.length

  if (hasLevelField.value) {
    // 基于 level 字段的统计（所有项都是标题）
    const highLevelCount = data.filter(item => (item.level || 0) >= 101).length
    const lowLevelCount = data.filter(item => (item.level || 0) < 101).length
    const level101to200 = data.filter(item => {
      const level = item.level || 0
      return level >= 101 && level <= 200
    }).length
    const levelAbove200 = data.filter(item => (item.level || 0) > 200).length

    return {
      totalItems,
      sectionHeaders,
      highLevelCount,
      lowLevelCount,
      level101to200,
      levelAbove200,
      labeledCount: 0,
      textContent: 0,
      tables: 0,
      lists: 0
    }
  } else {
    // 基于 label 字段的统计（兼容旧格式）
    const labeledCount = data.filter(item =>
      item.label_level1 && item.label_level1 !== '未分类'
    ).length
    const textContent = data.filter(item => item.label === 'text').length
    const tables = data.filter(item => item.label === 'table').length
    const lists = data.filter(item => item.label === 'list').length

    return {
      totalItems,
      sectionHeaders,
      highLevelCount: 0,
      lowLevelCount: 0,
      level101to200: 0,
      levelAbove200: 0,
      labeledCount,
      textContent,
      tables,
      lists
    }
  }
})

// 监听数据变化
watch(() => props.taggedData, (newData) => {
  if (props.autoRefresh) {
    console.log('📊 标记统计更新:', statistics.value)
  }
}, { deep: true, immediate: true })
</script>

<style scoped lang="scss">
.tag-statistics {
  width: 100%;

  :deep(.ant-card-body) {
    padding: 16px;
  }

  :deep(.ant-statistic-title) {
    font-size: 13px;
    margin-bottom: 4px;
  }

  :deep(.ant-statistic-content) {
    font-size: 20px;
    font-weight: 600;
  }

  :deep(.ant-descriptions-item-label) {
    font-size: 12px;
    font-weight: 500;
  }

  :deep(.ant-descriptions-item-content) {
    font-size: 13px;
  }
}
</style>
