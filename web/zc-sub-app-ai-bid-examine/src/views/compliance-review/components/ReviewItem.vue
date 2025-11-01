<template>
  <div :class="['review-item',{'active': activeId === item.uniqueId}]" @click.stop="handleClickItem" :data-id="item.uniqueId"> 
    <!-- 头部区域：风险标签 + 描述 + 点赞点踩 -->
    <div class="header-section">
      <div class="content-left">
        <a-tag :class="getRiskStyle(item.result).className" class="tip-tag">
          {{ getRiskStyle(item.result).text }}
        </a-tag>
        <div class="item-description">{{ item.sceneDesc }}</div>
      </div>
      <div class="vote-section" v-if="item.result !==-1">
        <div class="vote-buttons">
          <div
            class="vote-btn"
            :class="{ active: item.likeNum }"
            @click.stop="handleLike($event)"
            @mouseenter="hoverStates.thumbsUp = true"
            @mouseleave="hoverStates.thumbsUp = false"
          >
            <ThumbsUp
              class="icon thumbs-up-icon"
              :size="16"
              :color="item.likeNum ? 'var(--main-6)' : (hoverStates.thumbsUp ? 'var(--main-6)' : 'rgba(0, 0, 0, 0.65)')"
            />
            <span>{{ item.likeNum || 0 }}</span>
          </div>
          <div
            class="vote-btn"
            :class="{ active: item.dislikeNum }"
            @click.stop="handleDislike($event)"
            @mouseenter="hoverStates.thumbsDown = true"
            @mouseleave="hoverStates.thumbsDown = false"
          >
            <ThumbsDown
              class="icon thumbs-down-icon"
              :size="16"
              :color="item.dislikeNum ? 'var(--main-6)' : (hoverStates.thumbsDown ? 'var(--main-6)' : 'rgba(0, 0, 0, 0.65)')"
            />
            <span>{{ item.dislikeNum || 0 }}</span>
          </div>
        </div>
      </div>
    </div>
    <div class="mod-box risk-details" v-if="item.result !==-1">
      <span class="label">风险提示：</span>
      <span class="content" v-if="item.showRiskTip">
        <span class="risk-before" v-if="riskDisplay.before">{{ riskDisplay.before }}</span>
        <span class="risk-quote" v-if="riskDisplay.quote">"{{ riskDisplay.quote }}"</span>
        <span class="risk-after" v-if="riskDisplay.after">{{ riskDisplay.after }}</span>
      </span>
      <span class="content" v-else>
        <span v-if="item.fileText">"{{item.fileText}}"</span>
        {{ item.riskTip }}
      </span>
    </div>
    <!-- 开发模式：显示定位按钮 -->
    <div class="dev-mode-actions" v-if="item._isDevMode">
      <a-button
        v-if="item.spanList?.[0]?.pdfAnnotations?.length > 0"
        size="small"
        @click.stop="handleShowBestMatch"
      >
        定位到最接近的PDF批注
      </a-button>
      <a-button
        v-if="item._originalSpan?.quadPoints?.length > 0"
        size="small"
        type="primary"
        @click.stop="handleShowOriginalSpan"
      >
        定位到annotation.json的位置
      </a-button>
    </div>
    <template v-if="item.result === 1">
      <div class="mod-box legal-basis">
        <span class="label">审查依据：</span>
        <div class="source-box">
          <template v-if="item.legalBasicHide">
            <span class="content">同上</span>
          </template>
          <template v-else>
            <div class="source" v-for="(article,index) in item.legalBasicSourceList" :key="index">
              <span class="font-medium" v-if="item.legalBasicSourceList?.length>1">{{ index+1 }}.</span>
              <span>{{ article.source }}{{article.basicIssue}}{{article.basicNumber}}
              <template v-if="article.basicDesc">：</template>
              </span>
              <span class="content">{{ article.basicDesc }}</span>
              <span v-if="article.sourceLink" class="link" @click.stop="handleOpenLink(article.sourceLink)">
                <Link :size="14"/>
                <span>查看原文</span>
              </span>
            </div>
          </template>
        </div>
      </div> 
      <div class="mod-box suggestion">
        <span v-if="!isEditingMode" class="label">修改建议：</span>
        <div v-if="isEditingMode" class="suggestion-content">
          <a-input placeholder="请输入建议修改内容"
            v-model:value="editingSuggestion"
            :maxlength="500"
            ref="editTextarea"
          />
            <!-- @blur="handleSaveEdit"@keydown.enter.ctrl="handleSaveEdit"
            @keydown.esc="handleCancelEdit" -->
          <div class="edit-actions">
            <a-button type="primary" @click.stop="handleSaveEdit($event)">保存</a-button>
            <a-button  @click.stop="handleCancelEdit($event)">取消</a-button>
          </div>
        </div>
        <template v-else>
          <span class="content">{{ item.revisionSuggestion }}
            <SquarePen
            v-if="item.handleStatus === 0"
            class="btn edit-icon square-pen-icon"
            :size="16"
            :color="hoverStates.editIcon ? 'var(--main-6)' : '#6B7280'"
            @click.stop="handleStartEdit($event)"
            @mouseenter="hoverStates.editIcon = true"
            @mouseleave="hoverStates.editIcon = false"
          /></span>

        </template>
      </div>
      <div class="action-buttons">
        <!-- 已接受状态：显示已修改和撤回按钮 -->
        <template v-if="item.handleStatus === 1">
          <a-button
            size="small"
            class="btn-modify"
            @click.stop=""
          >
            <template #icon>
              <CircleCheck :size="16" color="#52C41A"/>
            </template>
            已修改
          </a-button>
          <a-popover
            v-model:open="withdrawModalVisible"
            placement="bottom"
            trigger="manual"
            overlay-class-name="withdraw-confirm-popover"
            :get-popup-container="() => $el"
          >
            <template #content>
              <div class="withdraw-confirm-content" @click.stop>
                <div class="tip-section">
                  <div class="tip-icon">
                    <InfoCircleOutlined />
                  </div>
                  <div class="tip-text">
                    撤回后数据会返回原始版本，确定执行？
                  </div>
                </div>
                <div class="button-group">
                  <a-button @click.stop="handleWithdrawCancel($event)">取消</a-button>
                  <a-button type="primary" :loading="loadingState.revert" @click.stop="handleWithdrawConfirm($event)">确定</a-button>
                </div>
              </div>
            </template>
            <a-button
              ref="withdrawButtonRef1"
              size="small"
              class="btn-disagree"
              @click.stop="handleShowWithdrawModal($event)"
            >
              <template #icon>
                <CornerUpLeft :size="16" color="rgba(0, 0, 0, 0.65)"/>
              </template>
              撤回
            </a-button>
          </a-popover>
        </template>
        <!-- 待处理状态：显示接受建议和不接受建议按钮 -->
        <template v-else>
          <a-button
            type="primary"
            size="small"
            class="btn-agree"
            :loading="loadingState.suggest"
            @click.stop="handleAcceptSuggestion($event)"
          >
            <template #icon>
              <PenLine :size="16" color="#fff" />
            </template>
            接受建议
          </a-button>
          <a-button
            size="small"
            class="btn-disagree"
            :loading="loadingState.reject"
            @click.stop="handleRejectSuggestion($event)"
          >
            <template #icon>
              <X :size="16" color="rgba(0, 0, 0, 0.65)"/>
            </template>
            不接受建议
          </a-button>
        </template>
      </div>
    </template>

    <!-- 点踩弹框 -->
    <DislikeModal
      ref="dislikeModalRef"
      v-model="dislikeModalVisible"
      @confirm="handleDislikeConfirm"
      @cancel="handleDislikeCancel"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, computed, onMounted, onUnmounted, reactive } from 'vue'
import { getRiskStyle } from '@/views/hooks/examine'
import { SquarePen,X,PenLine,CircleCheck,CornerUpLeft, ThumbsUp, ThumbsDown ,Link } from 'lucide-vue-next'
import { InfoCircleOutlined } from '@ant-design/icons-vue'
import DislikeModal from './DislikeModal.vue'
import { reviewResultLike, apiReviewResultMark , updateSuggestion, resultMarkClear} from '@/api/examine'
import { message } from 'ant-design-vue'

defineOptions({
  name: 'ReviewItem'
})

interface Props {
  data: Record<string,any>
  taskId: string,
  active: string|undefined
}

const props = withDefaults(defineProps<Props>(), {})

const item = computed({
  get() {
    return props.data
  },
  set(val) {
    emit('update:item', val)
  }
})
const activeId = computed(()=>props.active)
const emit = defineEmits(['update:item','clickItem','updateFinishNum','showBestMatch','showOriginalSpan'])

const handleClickItem = ()=> {
  emit('clickItem', item.value)
}

// 开发模式：定位到最接近的PDF批注
const handleShowBestMatch = () => {
  emit('showBestMatch', item.value)
}

// 开发模式：定位到annotation.json的原始位置
const handleShowOriginalSpan = () => {
  emit('showOriginalSpan', item.value)
}
// 格式化风险提示文本，将链接转换为可点击链接
const formatRiskText = (text: string) => {
  if (!text) return ''
  
  // 匹配 http:// 或 https:// 开头的链接
  const urlRegex = /(https?:\/\/[^\s\u4e00-\u9fff]+)/g
  
  return text.replace(urlRegex, (url) => {
    return `<a href="${url}" target="_blank" rel="noopener noreferrer" class="risk-link">${url}</a>`
  })
}
// 风险提示显示处理
const riskDisplay = computed(() => {
  if (!item.value.showRiskTip) {
    return {
      before: '',
      quote: '',
      after: ''
    }
  }

  const text = item.value.showRiskTip
  const quoteRegex = /^(.*?)[""]([^""]+)[""](.*)$/
  const matches = text.match(quoteRegex)

  if (matches) {
    return {
      before: matches[1].trim(),
      quote: matches[2].trim(),
      after: matches[3].trim()
    }
  }

  return {
    before: '',
    quote: '',
    after: text.trim()
  }
})
// 加载状态管理
const loadingState = ref<Record<string,any>>({
  like: false,
  dislike: false,
  suggest: false,
  reject: false,
  revert: false
})
// 当前投票状态
const actionType = ref<number>(props.data.dislikeNum ? 0 : props.data.likeNum ? 1 : 2)

// 图标 hover 状态管理
const hoverStates = ref({
  thumbsUp: false,
  thumbsDown: false,
  editIcon: false
})

// 弹框状态管理
const dislikeModalVisible = ref(false)
const withdrawModalVisible = ref(false)
const feedback = ref<Record<string, any>>({})
// 弹框引用
const dislikeModalRef = ref<any>(null)
const withdrawButtonRef1 = ref<any>(null)

// 内联编辑状态管理
const isEditingMode = ref(false)
const editingSuggestion = ref('')
const editTextarea = ref()

// 点赞处理
const handleLike = async (event: Event) => {
  event.preventDefault()
  event.stopPropagation()
  // 防止重复点击
  if (loadingState.value.like || loadingState.value.dislike) return
  // 确保撤回弹窗关闭
  withdrawModalVisible.value = false
  loadingState.value.like = true
  if (actionType.value === 1) { // 取消点赞
    handleResultMark(2)
  } else {
    // 点赞
    handleResultMark(1)
  }
}

// 点踩处理
const handleDislike = async (event: Event) => {
  event.preventDefault()
  event.stopPropagation()

  // 防止重复点击
  if (loadingState.value.like || loadingState.value.dislike) return

  // 确保撤回弹窗关闭
  withdrawModalVisible.value = false
  if (actionType.value === 0) {
    loadingState.value.dislike = true
    handleResultMark(2)
  } else {
    feedback.value = {}
    dislikeModalVisible.value = true
  }
}
const handleResultMark = async(type: number) => {
  const { data, err } = await reviewResultLike({
    uniqueId: item.value.uniqueId,
    isRisk: item.value.result,
    taskId: props.taskId,
    actionType: type,
    feedbackReason: feedback.value.feedbackReason,
    otherOpinion: feedback.value.otherOpinion
  })
  loadingState.value.like = false
  loadingState.value.dislike = false
  if (err)  return
  actionType.value = type
  // 更新本地状态
  initLikeAction()
}
const initLikeAction = ()=>{
  item.value.dislikeNum = actionType.value === 0 ? 1 : 0
  item.value.likeNum = actionType.value === 1 ? 1 : 0
}
// 处理点踩弹框确认
const handleDislikeConfirm = async (reasons: string[], otherOpinion: string) => {
  if(!(reasons?.length || otherOpinion.trim())){
    message.info('请选择反馈原因')
    return // 验证失败，不关闭弹框
  }
  // 防止重复提交
  if (loadingState.value.dislike) return
  // 组合反馈原因
  const feedbackReasons = [...reasons]
  const reasonText = feedbackReasons.join(',')
  feedback.value.feedbackReason = reasonText || ''
  feedback.value.otherOpinion = otherOpinion
  loadingState.value.dislike = true
  await handleResultMark(0)
  // 验证通过，手动关闭弹框
  dislikeModalRef.value?.closeModal()
}
const handleDislikeCancel = ()=> {

}
// 接受建议并修订
const handleAcceptSuggestion = async (event: Event) => {
  event.preventDefault()
  event.stopPropagation()
  // 确保撤回弹窗关闭
  withdrawModalVisible.value = false

  if(item.value.revisionSuggestion?.trim()?.length >= 500) {
    message.info('建议不能超过500个字符')
    return
  }
  loadingState.suggest = true
  handleSuggestion(1)
}

// 不接受建议
const handleRejectSuggestion = async (event: Event) => {
  event.preventDefault()
  event.stopPropagation()

  // 确保撤回弹窗关闭
  withdrawModalVisible.value = false
  loadingState.reject = true
  handleSuggestion(0)
}
const handleSuggestion = async (status: number|string)=> {
  const { data, err } = await apiReviewResultMark({resultId: item.value.uniqueId, markDesc: item.value.revisionSuggestion,status})
  loadingState.suggest = false
  loadingState.reject = false
  if (err) return
  item.value.handleStatus = 1
  emit('updateFinishNum', 1)
  if(status ===1) {
    item.value.acceptStatus = 1
    item.value.acceptText =  item.value.revisionSuggestion
  }
  if(status === 0) {
    item.value.acceptStatus = 0
    item.value.acceptText = ''
  }
  nextTick(()=> {
    emit('clickItem', item.value)
  })
}
// 显示撤回
const handleShowWithdrawModal = (event: Event) => {
  // 阻止事件冒泡和默认行为
  event.preventDefault()
  event.stopPropagation()

  // 确保只有撤回按钮能触发这个弹窗
  if (item.value.handleStatus === 1) {
    withdrawModalVisible.value = true
  }
}

// 撤回确认
const handleWithdrawConfirm = async(event: Event) => {
  event.preventDefault()
  event.stopPropagation()
  loadingState.revert = true
  const { err } = await resultMarkClear({resultId: item.value.uniqueId})
  loadingState.revert = false
  if (err) return

  item.value.handleStatus = 0
  item.value.acceptStatus = 0
  withdrawModalVisible.value = false
  emit('updateFinishNum', -1)

  nextTick(() => {
    emit('clickItem', item.value)
  })
}

// 撤回取消
const handleWithdrawCancel = (event: Event) => {
  event.preventDefault()
  event.stopPropagation()
  withdrawModalVisible.value = false
}

// 内联编辑建议
const handleStartEdit = (event: Event) => {
  event.preventDefault()
  event.stopPropagation()

  // 确保撤回弹窗关闭
  withdrawModalVisible.value = false

  isEditingMode.value = true
  editingSuggestion.value = item.value.revisionSuggestion || ''

  // 下一帧聚焦到输入框
  nextTick(() => {
    if (editTextarea.value) {
      editTextarea.value.focus()
    }
  })
}

// 保存编辑
const handleSaveEdit = async (event: Event) => {
  event.preventDefault()
  event.stopPropagation()

  try {
    if (editingSuggestion.value.trim() !== item.value.revisionSuggestion) {
      const result = await updateSuggestion({
        resultId: item.value.uniqueId,
        revisionSuggestion: editingSuggestion.value.trim()
      })

      item.value.revisionSuggestion = editingSuggestion.value.trim()
    }
    isEditingMode.value = false
  } catch (error) {
    console.error('保存编辑失败:', error)
  }
}

// 取消编辑
const handleCancelEdit = (event: Event) => {
  event.preventDefault()
  event.stopPropagation()

  editingSuggestion.value = item.value.revisionSuggestion || ''
  isEditingMode.value = false
}
// 打开链接
const handleOpenLink = (url: string) => {
  window.open(url, '_blank')
}
</script>

<style lang="scss" scoped>
.review-item {
  cursor: pointer;
  padding: 16px;
  border-bottom: 1px solid #E5E7EB;
  background: var(--fill-0);
  transition: all 0.2s;
  display: flex;
  flex-direction: column;
  gap: 8px;
  &.active,
  &:hover {
    background-color: #DCE8FF;
  }
  .tip-tag {
    display: block;
    height: 26px;
    line-height: 26px;
    padding: 0 8px;
    font-weight: 400;
    background-color: #fafafa;
    border-color: #d9d9d9;
    color: #8c8c8c;
    &.risk {
      background-color: #fff2f0;
      border-color: #ffccc7;
      color: #ff4d4f;
    }

    &.safe{
      background-color: #F6FFED;
      border-color: #B7EB8F;
      color: #52C41A;
    }
  }
  .header-section {
    display: flex;
    justify-content: space-between;

    .content-left {
      flex: 1;
      display: flex;
      .item-description {
        font-size: 16px;
        line-height: 26px;
      }
    }

    .vote-section {
      flex-shrink: 0;
      margin-left: 4px;
      .vote-buttons {
        display: flex;
        align-items: center;
        gap: 16px;

        .vote-btn {
          display: flex;
          align-items: center;
          gap: 4px;
          cursor: pointer;
          position: relative;

          &.loading {
            pointer-events: none;
            opacity: 0.6;
          }

          .ant-spin {
            margin-left: 4px;
          }
        }
      }
    }
  }
  .mod-box {
    display: flex;
    width: 100%;
    .label {
      flex-shrink: 0;
    }
    .content {
      white-space: break-spaces;
      color: #374151;
      font-weight: 400;
      .edit-icon {
        display: inline-block;
        vertical-align: middle;
        margin-top: -2px;
      }
    }
    .btn {
      margin-left: 8px;
      cursor: pointer; 
    }
  }
  .risk-details {
    font-weight: 600;
    .risk-quote {
        color: var(--main-6);
      }
    .content {
      font-weight: 600;
    }
  }
  .dev-mode-actions {
    display: flex;
    gap: 8px;
    margin-top: 12px;
    padding-left: 0;
  }
 .legal-basis {
  line-height: 22px;
  .link {
    display: inline-flex;
    align-items: center;
    cursor: pointer;
    color: var(--main-6);
    gap: 4px;
    &:hover {
      color: var(--main-5);
    }
    &:focus,
    &:active {
      color: var(--main-7);
    }
  }
 }
  .suggestion-content {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: space-between;
    .edit-actions {
      display: flex;
      justify-content: flex-end;
      align-items: center;
      gap: 4px;
      margin-left: 8px;
    }
    :deep(.ant-input) {
      border-radius: 4px;
      &:focus {
        border-color: #D9D9D9;
        box-shadow: none;
      }
    }
    .ant-btn {
      padding: 4px 9px;
      font-size: 12px;
    }
  }
  .btn-disagree {
    border-color: #D1D5DB;
    color: rgba(0, 0, 0, 0.65);
    &:hover{
      border-color: #D1D5DB;
      color: rgba(0, 0, 0, 0.65);
    }
  }
  .action-buttons {
    display: flex;
    gap: 8px;
    .ant-btn {
      height: 28px;
      font-size: 12px;
      padding: 0 12px;
      border-radius: 6px;
      display: flex;
      align-items: center;
      gap: 4px;
      transition: all 0.3s ease-in-out;
      &:hover{
         opacity: 0.8;
      }
    }
    .btn-modify {
      background-color: #F6FFED;
      border-color: #B7EB8F;
      color: #52C41A;
    }
  }
}

// 撤回确认Popover样式
:deep(.withdraw-confirm-popover) {
  .ant-popover-content {
    padding: 0;
  }

  .ant-popover-inner {
    padding: 16px 20px;
    border-radius: 8px;
    box-shadow: 0 6px 16px 0 rgba(0, 0, 0, 0.08),
                0 3px 6px -4px rgba(0, 0, 0, 0.12),
                0 9px 28px 8px rgba(0, 0, 0, 0.05);
    min-width: 320px;
    max-width: 400px;
  }

  // 确保箭头显示
  .ant-popover-arrow {
    display: block !important;
  }
}

.withdraw-confirm-content {
  .tip-section {
    display: flex;
    align-items: flex-start;
    gap: 12px;
    margin-bottom: 16px;

    .tip-icon {
      flex-shrink: 0;
      margin-top: 2px;
      color: var(--main-6);
    }

    .tip-text {
      flex: 1;
      font-size: 14px;
      line-height: 22px;
      color: rgba(0, 0, 0, 0.88);
    }
  }

  .button-group {
    display: flex;
    justify-content: flex-end;
    gap: 8px;

    .ant-btn {
      height: 32px;
      padding: 0 15px;
      border-radius: 6px;
      font-size: 14px;

      &:first-child {
        color: rgba(0, 0, 0, 0.88);
        border-color: #d9d9d9;
        background: #fff;

        &:hover {
          color: var(--main-6, #1890ff);
          border-color: var(--main-6, #1890ff);
        }
      }

      &[type="primary"] {
        background-color: var(--main-6, #1890ff);
        border-color: var(--main-6, #1890ff);

        &:hover {
          background-color: var(--main-5, #40a9ff);
          border-color: var(--main-5, #40a9ff);
        }
      }
    }
  }
}
</style>



