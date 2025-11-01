<template>
  <BaseDrawer
    v-model="visible"
    title="审查清单"
    :width="640"
    :loading="loading"
    :ok-visible="true"
    :cancel-visible="false"
    :ok-loading="saving"
    :ok-disabled="!hasChanges"
    ok-text="重新审查"
    @ok="handleSave"
    @cancel="handleClose"
  >
    <div class="checklist-content">
      <div class="form-section">
        <div class="form-label">审查方式：</div>
        <a-select
          v-model:value="reviewMethod"
          placeholder="请选择审查方式"
          style="width: 320px"
          :disabled="true"
          :options="reviewMethodOptions"
        />
      </div>
      <div class="form-section">
        <div class="form-label">审查清单：</div>
        <a-select
          v-model:value="reviewContent"
          placeholder="请选择审查清单"
          style="width: 320px"
          :disabled="true"
          :options="reviewContentOptions"
        />
      </div>
      <!--      <div class="form-section">-->
<!--        <div class="form-label">审查项：</div>-->
<!--      </div>-->

      <!-- 审查项目列表 -->
      <div class="checklist-items">
        <div class="sum">完整审查清单共包含 <span>{{sceneNum}}</span> 个审查场景、<span>{{detailedSceneNum}}</span> 个审查点</div>

        <a-checkbox-group
          v-model:value="selectedCheckPoints"
          :disabled="isSkeleton"
          class="checkbox-group"
        >
          <!-- 按分类显示审查项目 -->
          <div
            v-for="category in groupedCheckPoints"
            :key="category.reviewItemCode"
            class="category-section"
          >
            <h4 class="category-title">{{ category.reviewItemName }}</h4>
            <div class="category-items">
              <div
                v-for="checkPoint in category.children"
                :key="checkPoint.sceneId"
                class="checklist-item"
              >

                <div class="detailed-scene-list-info"
                     :class="(checkPoint.expand && Boolean(checkPoint.detailedSceneList))?'detailed-scene-list-info-expand':''">
                  <a-checkbox :value="checkPoint.sceneId" class="checkbox-item" />
                  <div class="title">
                    <span class="t">{{ checkPoint.sceneDesc }}</span>
                    <a-badge :count="checkPoint.detailedSceneList?.length" :number-style="{
                                        background: 'rgba(0, 0, 0, 0.06)',
                                        color: '#4B5563',
                                        margin: '0 0 0 8px',
                                      }" />
                  </div>
                  <a-button v-if="checkPoint.detailedSceneList?.length && 0 < checkPoint.detailedSceneList.length"
                            :icon="h(DownOutlined)"
                            :class="checkPoint.expand?'expand':''"
                            @click="toggleExpand(checkPoint)" />
                </div>

                <div v-if="checkPoint.expand && Boolean(checkPoint.detailedSceneList)" class="detailed-scene-list">
                  <div v-for="item in checkPoint.detailedSceneList" class="detailed-scene">
                    <SvgIcon icon="icon-mark" color="#91CAFF" class="icon-mark" />
                    <span>{{ item }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </a-checkbox-group>

        <!-- 空状态 -->
        <div v-if="checkPointList.length === 0 && !loading" class="empty-state">
          <a-empty description="暂无审查项目" />
        </div>
        <!-- 确认弹框 -->
        <ReviewSuccessModal v-model:open="showReviewSuccessModal"/>
      </div>
    </div>
  </BaseDrawer>
</template>

<script setup lang="ts">
import { h, ref, computed, watch , nextTick} from 'vue'
import { useRoute, useRouter } from 'vue-router'
import BaseDrawer from '@/components/BaseDrawer/base-drawer.vue'
import { checkSceneDetail,reviewAgain } from '@/api/examine'
import ReviewSuccessModal from './ReviewSuccessModal.vue'
import { DownOutlined } from '@ant-design/icons-vue'
import { SvgIcon } from '@/components'

defineOptions({
  name: 'CheckListModal'
})

// 审查点数据类型
interface CheckPoint {
  reviewItemCode: string
  sceneId?: string
  sceneDesc?: string
  status?: number
  reviewItemName: string,
  children?: CheckPoint[]
}

interface Props {
  open: boolean
  taskId: string 
}

const props = withDefaults(defineProps<Props>(), { })

const sceneNum = ref<number>()
const detailedSceneNum = ref<number>()

const toggleExpand = (val: any) => {
  val.expand = !val.expand
}

const emit = defineEmits<{
  'update:open': [value: boolean]
  'save': [data: any]
}>()
const router = useRouter()
// 响应式状态
const visible = computed({
  get: () => props.open,
  set: (value) => emit('update:open', value)
})

const loading = ref(false)
const saving = ref(false)

// 审查方式和清单选项
const reviewMethod = ref('')
const reviewContent = ref('')

const reviewMethodOptions = []

const reviewContentOptions = []

// 审查点数据
const checkPointList = ref<CheckPoint[]>([])
const selectedCheckPoints = ref<any[]>([]) // 选中的审查点ID列表

// 按reviewItemCode分组的审查项目
const groupedCheckPoints = computed(() => {
  let groups: CheckPoint[] = checkPointList.value || []
  groups = groups.reduce((acc, item) => {
    let group = acc.find(group => group.reviewItemCode === item.reviewItemCode);
    if (!group) {
      group = {
        reviewItemCode: item.reviewItemCode,
        reviewItemName: item.reviewItemName,
        children: []
      };
      acc.push(group);
    }
    group.children?.push(item);
    return acc;
  }, [] as CheckPoint[]);
  return groups
})

// 方法

const handleClose = () => {
  visible.value = false
}

const showReviewSuccessModal = ref(false)
const handleSave = async () => {
  saving.value = true
  showReviewSuccessModal.value = false
  const {data, err} = await reviewAgain({taskId: props.taskId,sceneIdList: selectedCheckPoints.value})
  saving.value = false
  if(err) return
  showReviewSuccessModal.value = true
}
const cachedCheckPoints = ref<any[]>([])
const hasChanges = computed(() => {
  if (cachedCheckPoints.value.length !== selectedCheckPoints.value.length) {
    return true
  }
  return !cachedCheckPoints.value.every(id => selectedCheckPoints.value.includes(id))
})
// 加载审查点数据
const loadCheckPoints = async () => {
    loading.value = true
    const {data, err} = await checkSceneDetail({taskId: props.taskId})
    loading.value = false
    checkPointList.value = data?.sceneList || []
    reviewMethod.value = data.procurementMethod || ''
    reviewContent.value = data.checkListName || ''
    // 默认全选
    const selected = checkPointList.value.filter(item=>item.status===1).map(item => item.sceneId) ?? []
    selectedCheckPoints.value = [...selected]
    cachedCheckPoints.value = [...selected]
  sceneNum.value = data.sceneNum
  detailedSceneNum.value = data.detailedSceneNum
}

// 监听抽屉打开状态
watch(() => props.open, (newVal) => {
  if (newVal) {
    loadCheckPoints()
  }
})
watch(() => showReviewSuccessModal.value, (newVal, oldVal) => {
  if (oldVal && !newVal) {
    // 弹窗从打开变为关闭
    nextTick(() => {
      router.push({name: 'LibraryIndex'})
    })
  }
})
</script>

<style lang="scss" scoped>
.checklist-content {
  //width: 640px;
  width: 100%;
  padding: 24px 0;

  :deep(.ant-wave) {
    display: none;
  }

  .form-section {
    display: flex;
    align-items: center;
    margin-bottom: 16px;
    padding: 0 24px;
  }

  .checklist-items {
    display: flex;
    flex-direction: column;
    gap: 12px;

    .sum {
      font-size: 14px;
      font-weight: 400;
      line-height: 22px;
      padding: 0 24px;

      span {
        color: #133CE8;
        font-family: Roboto;
        font-weight: 500;
        line-height: 20px;
        letter-spacing: 0.1px;
      }
    }

    .checkbox-group {
      display: flex;
      flex-direction: column;
      width: 100%;
    }

    .category-section {
      .category-title {
        font-weight: 600;
        padding: 8px 24px;
        color: #000000E0;
        background-color: #00000005;
        border-bottom: 1px solid #F0F0F0;
      }
      .count {
        color: #4B5563;
        border-radius: 50%;
        background-color: #E5E7EB;
        margin-left: 8px;
        padding:0 4px;
        min-width: 20px;
        text-align: center;
      }
    }

    .checklist-item {
      //padding: 12px 0;
      //border-bottom: 1px solid #F0F0F0;

      .ant-checkbox-wrapper {
        display: flex;
        padding: 0 0 0 24px;
      }

      .ant-checkbox-wrapper:last-child {
        background: red;
      }

      .detailed-scene-list-info {
        display: flex;
        align-items: center;

        .title {
          flex: 1;
          padding: 0 0 0 12px;
          white-space: break-spaces;
          display: flex;
          align-items: center;

          .t {
            padding: 12px 0;
          }
        }


          :deep(.ant-badge) {
            .ant-badge-count {
              box-shadow: none;
            }
          }

        .expand {
          rotate: 180deg;
        }

        button {
          border: none;
          background: none;
          box-shadow: none;
          margin: 0 16px;

          span {
            display: inline-flex;
          }
        }
      }

      .detailed-scene-list-info-expand {
        background: #E6EFFF;
      }

      .detailed-scene-list {
        display: flex;
        flex-direction: column;
        padding: 8px 24px;
        background: rgba(230, 239, 255, 0.50);

        .detailed-scene {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 6px 0;
          color: #374151;
          line-height: 22px;
          font-family: Inter;

          .icon-mark {
            width: 8px;
            height: 8px;
            margin: 0 4px;
          }
        }
      }
    }

    .empty-state {
      text-align: center;
      padding: 40px 0;
      color: var(--text-3, #999);
    }
  }
}
</style>
