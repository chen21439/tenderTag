<template>
  <BaseDrawer
    v-model="visible"
    title="规则验证测试"
    width="600px"
    :loading="loading"
    :footer-visible="true"
    @cancel="handleCancel"
  >
    <div class="rule-test-dialog">
      <!-- 规则选择 -->
      <div class="form-section">
        <div class="section-title">规则选择</div>
        <a-select
          v-model:value="selectedRuleId"
          placeholder="选择规则或开启检测"
          style="width: 100%"
          allow-clear
        >
          <a-select-option v-for="rule in availableRules" :key="rule.id" :value="rule.id">
            {{ rule.name }}
          </a-select-option>
        </a-select>
      </div>

      <!-- 文本输入 -->
      <div class="form-section">
        <div class="section-title">文本输入</div>
        <a-textarea
          v-model:value="testText"
          placeholder="输入需要检测的内容..."
          :rows="6"
          :maxlength="1000"
          show-count
        />
      </div> 
      <!-- 测试结果 -->
      <div v-if="testResult" class="result-section">
        <div class="section-title">测试结果</div>
        <div class="result-content">
          <div class="result-item">
            <span class="result-label">命中片段：</span>
            <template v-if="testResult.matchWords?.length">
              <span 
                v-for="(value,index) in testResult.matchWords"
                :key="value"
              >{{ value }}<template v-if="index !== testResult.matchWords.length - 1">，</template></span>
            </template>
            <span v-else>无</span>
          </div>
          <div class="result-item">
            <span class="result-label">组合：</span>
            <span class="result-value">{{ testResult.group || '无' }}</span>
          </div>
          <div class="result-item">
            <span class="result-label">风险级别：</span>
            <a-tag :color="getLevel(testResult.violationLevel).color">
              {{ getLevel(testResult.violationLevel).text }}
            </a-tag>
          </div>
          <div class="result-item">
            <span class="result-label">是否触发规则：</span>
            <a-tag :color="testResult.result ? 'green' : 'default'">
              {{ testResult.result ? '是' : '否' }}
            </a-tag>
          </div>
          <div class="result-item">
            <span class="result-label">置信度：</span>
            <span class="result-value">{{ testResult.thresholdLevel || '无' }}</span>
            <!-- <a-tag :color="getLevel(testResult.thresholdLevel).color">
              {{ getLevel(testResult.thresholdLevel).text }}
            </a-tag> -->
          </div>
        </div>
      </div>
    </div>

    <!-- 底部操作按钮 -->
    <template #footer> 
      <a-button @click="handleCancel">取消</a-button> 
      <a-button
        type="primary"
        :loading="testing"
        @click="handleTest"
      >
        <template #icon>
          <BugPlay :size="16" />
        </template>
        运行测试
      </a-button> 
    </template>
  </BaseDrawer>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { BugPlay } from 'lucide-vue-next'
import { message } from 'ant-design-vue'
import { BaseDrawer } from '@/components/BaseDrawer'
import { getLevel } from '@/views/hooks/examine'
import {apiRuleTest, apiRuleList } from '@/api/examine'
 
// ==================== Props 和 Emits ====================
interface Props {
  modelValue: boolean 
  ruleId: string
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: false, 
  ruleId: ''
})

const emit = defineEmits(['update:modelValue','save'])

// ==================== 响应式数据 ====================
const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const selectedRuleId = ref<string>('')
const testText = ref('')
const testing = ref(false)
const testResult = ref<any>(null)
const ruleList = ref<any>([])

// 可用规则（只显示已启用的规则）
const availableRules = computed(() => {
  return ruleList.value.filter(rule => rule.status)
}) 
// 处理测试
const handleTest = async () => {
  if (!selectedRuleId.value) {
    message.warning('请选择要测试的规则')
    return
  }
  
  if (!testText.value.trim()) {
    message.warning('请输入测试文本')
    return
  }

  testing.value = true 
  const {data,err} = await apiRuleTest({
    ruleId: selectedRuleId.value,
    testText: testText.value
  })
  testing.value = false
  if (err) return
  testResult.value = data ?? {}
  emit('save', testResult.value)
} 
const loading = ref(false)
const getRuleList = async () => { 
  loading.value = true
  const { data,err } = await apiRuleList({
    pageNum: 1,
    pageSize: 1000
  })
  loading.value = false
  if (err) return
  ruleList.value = data?.list || []
}
// 处理取消
const handleCancel = () => {
  visible.value = false
  testResult.value = null
}

// ==================== 监听器 ==================== 
watch(visible, (newVal) => {
  if (newVal) {
    selectedRuleId.value = props.ruleId
    getRuleList()
  } else {
    // 关闭时重置数据
    selectedRuleId.value = ''
    testText.value = ''
    testResult.value = null
  }
}) 
</script>

<style lang="scss" scoped>
.rule-test-dialog {
  padding:24px;
  .test-info {
    margin-bottom: 32px;
    padding-bottom: 24px;
    border-bottom: 1px solid #f0f0f0;

    .info-item {
      display: flex;
      align-items: center;

      .info-label {
        color: #666;
        margin-right: 8px;
        font-weight: 500;
      }

      .info-value {
        color: #333;
        font-weight: 600;
      }
    }
  }

  .form-section {
    padding-bottom: 32px; 
  }

  .section-title {
    font-size: 16px;
    font-weight: 600; 
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
 

  .result-section {
    border-top: 1px solid #f0f0f0;
    padding-top: 20px;

    .result-content {
      background: #f8f9fa;
      padding: 16px;
      border-radius: 6px;

      .result-item {
        display: flex;
        align-items: center;
        margin-bottom: 12px;

        &:last-child {
          margin-bottom: 0;
        }

        .result-label {
          min-width: 80px;
          color: #666;
          font-size: 14px;
        }

        .result-value {
          color: #333;
          font-weight: 500;
        }
      }
    }
  }
}
</style>
