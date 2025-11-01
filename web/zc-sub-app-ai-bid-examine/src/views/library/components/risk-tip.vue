<template>
  <a-spin :spinning="loading">
  <div class="risk-tip">
  <div class="block risk-warning">
    <div class="risk-title">
      <div class="text-tip danger">风险提示</div>
      <div class="actions">
        <span class="ignore" @click="clickIgnore">
          <template v-if="ignore">
            <EyeInvisibleOutlined/>取消忽略
          </template>
          <template v-else>
            <EyeOutlined/>忽略
          </template>
        </span>

        <span class="comment" :class="{ 'is-danger': isMark }" @click="clickComment">
          <CommentOutlined/>
          {{ isMark ? '已批注' : '批注' }}
        </span>
      </div>
    </div>

    <div class="risk-content">
      <span>文中</span>
      <span class="risk-body">“{{riskData.fileText}}”</span>
      <span>中采购人存在</span>
      <span class="is-danger">“{{riskData.riskWarning}}”</span>
      <span>，</span>
      <span>不符合采购文件{{riskData.reviewItemName}}要求。</span>
    </div>
    </div>
    <div class="block legal-articles">
      <div class="raw-box">
        <div class="text-tip text-raw">审查依据</div>
      </div>
      <div v-for="(article, index) in legalArticles" :key="index" class="legal-article-item">
        <div class="article-header">
          <span class="article-title" :class="article.basicDesc? '': 'no-desc'">{{ article.source }}{{article.basicNumber}}{{article.basicIssue}}</span>
          <span class="expand-btn" v-if="article.basicDesc" @click="toggleArticle(index)" :class="{ 'expanded': article.expanded }">
            <CaretDownOutlined class="arrow"/>
            {{ article.expanded ? '收起' : '展开' }}
          </span>
          <div v-else class="read-original" @click="onClickLink(article.sourceLink)">
            <svg-icon icon="icon-fujian" class="icon-file"/>
            <span class="read-text">阅读原文</span>
          </div>
        </div>
        <div v-if="article.expanded && article.basicDesc" class="article-content">
          <div class="article-text">{{ article.basicDesc }}</div>
          <div class="read-original" v-if="article.sourceLink" @click="onClickLink(article.sourceLink)">
            <svg-icon icon="icon-fujian" class="icon-file"/>
            <span class="read-text">阅读原文</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</a-spin>
  <!-- 批注 -->
  <BaseDialog v-model="dialogVisible" title="批注" @confirm="dialogConfirm">
    <a-form ref="formRef" :model="form" :label-col="{ span: 0 }">
      <a-form-item name="markDesc" :rules="[{ required: true, message: '批注不能为空' }]">
        <a-textarea
          v-model:value="form.markDesc"
          show-count
          :maxlength="100"
          :rows="6"
          placeholder="请输入您要批注的内容"
        />
      </a-form-item>
    </a-form>
  </BaseDialog>
</template>

<script setup lang="ts">
import {computed, onMounted, ref, watch} from 'vue'
import {EyeOutlined, EyeInvisibleOutlined, CommentOutlined, CaretDownOutlined} from '@ant-design/icons-vue'
import {BaseDialog} from '@/components/BaseDialog'
import {apiReviewResultMark, apiGetMark } from '@/api/examine';

interface Props {
  riskData: Record<string, any>
}

const props = withDefaults(defineProps<Props>(), {})

const ignore = ref(false)
const isMark = ref(false)
const resultId = computed(() => props.riskData.resultId)
const legalArticles = computed({
  get: () => props.riskData.legalBasicSourceList,
  set: (val) => {
    return val
  }
})
// 切换法律条文展开/收起
const toggleArticle = (index: number) => {
  legalArticles.value[index].expanded = !legalArticles.value[index].expanded
}
// 忽略
const clickIgnore = async () => {
}
// 批注
const dialogVisible = ref(false)
const form = ref({
  resultId: resultId.value,
  markDesc: ''
})
// 法律来源
const onClickLink = (link: string) => {
  window.open(link)
}
const formRef = ref()
const loading = ref(false)

const getMark = async () => {
  const params = {resultId: resultId.value}

  loading.value = true
  const {data} = await apiGetMark(params)
  loading.value = false

  form.value.resultId = resultId.value
  form.value.markDesc = data.markDesc || ''
  isMark.value = data.markDesc ? true : false
}

const clickComment = () => {
  formRef.value?.resetFields()
  dialogVisible.value = true
}

const dialogConfirm = async () => {
  formRef.value.validate().then(async () => {
    dialogVisible.value = false
    const params = {...form.value}
    const {err} = await apiReviewResultMark(params)
    if (err) return
    isMark.value = true
  })
}

watch(resultId, async () => {
  await getMark()
})

onMounted(() => {
  getMark()
})
</script>

<style lang="scss" scoped>
.risk-tip {
  width: 480px;
  height: calc(100vh - 56px);
  overflow-y: scroll;
  background: var(--fill-0);
  padding: 20px;
  box-sizing: border-box;
  border-left:1px solid var(--neutral-3);
  .is-danger {
    color: var(--error-6);
  }

  .is-primary {
    color: var(--main-6);
  }

  .is-bold {
    font-weight: 700;
  }
  .block {
    border-radius: 8px;
    background: var(--neutral-1);
    backdrop-filter: blur(10px);
    margin-bottom: 12px;
    box-sizing: border-box;
    padding: 20px;
  }
  .text-tip {
    font-size: 16px;
    font-weight: 500;
  }

  .risk-title {
    display: flex;
    align-items: center;
    margin-bottom: 12px;
    border-radius: 4px;
    box-sizing: border-box;
    .actions {
      margin-left: auto;
      display: flex;
      gap: 12px;
      color: var(--text-4);
      font-size: 14px;
      cursor: pointer;

      .ignore:hover, .comment:hover {
        color: var(--main-6);
      }
    }
  }

  .risk-content {
    line-height: 22px;
    .risk-body {
      color: var(--fill-6);
    }
  }
  .raw-box {
    display: flex;
    align-items: center;
    box-sizing: border-box;
    border-radius: 4px;
    margin-bottom: 12px;
  }
  .legal-articles {
    .legal-article-item {
      padding: 12px 16px;
      border: 1px solid var(--neutral-3);
      border-radius: 8px;
      margin-bottom: 8px;
      background: var(--fill-0);
      overflow: hidden;
      transition: all 0.2s;
      &:last-child {
        margin-bottom: 0;
      }

      .article-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        .article-title {
          flex: 1;
          font-size: 14px;
          font-weight: 500;
          color: var(--text-5);
          &.no-desc {
            text-overflow:ellipsis;
            overflow:hidden;
            white-space:nowrap;
            margin-right:12px;
          }
        }

        .expand-btn {
          font-size: 12px;
          cursor:pointer;
          color: var(--main-6);
          .arrow {
            transition: all 0.2s;
          }
          &.expanded {
            .arrow {
              transform: rotate(180deg);
            }
          }
        }
      }

      .article-content {
        .article-text {
          font-size: 14px;
          line-height: 1.6;
          color: var(--text-4);
          padding: 12px 16px;
          box-sizing: border-box;
          background: var(--neutral-1);
          border-radius: 6px;
          margin: 12px 0;
        } 
        
      }
      .read-original {
        display: flex;
        align-items: center;
        gap: 4px;
        cursor: pointer;
        color: var(--main-6);
        .icon-file {
          width: 16px;
          height: 16px;
        }
      }
    }
  }
}
</style>
