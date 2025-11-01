<template>
  <div class="result">
    <div class="header">
      <div class="back"  @click="router.push({ name: 'LibraryIndex' })"
      @mouseenter="backIcon = 'icon-btn1'"
      @mouseleave="backIcon = 'icon-a-zu61'">
          <svg-icon :icon="backIcon" class="back-icon" />
      </div>
      <div class="title"><svg-icon class="icon" icon="icon-PDFsuolvetu"/>{{ fileName }}</div>

      <div class="res">
        <span class="t">审核结果：</span>
        <a-tag :color="riskOptions[reviewResult].color">{{ riskOptions[reviewResult].label }}</a-tag>
      </div>

      <div>审查时间：{{ reviewTime }}</div>
      <div class="base-btn-gradient btn btn1" @click="doLook">
        <svg-icon icon="icon-chakanshenchadian" class="icon" />
        <span>查看审查点</span>
      </div>
      <div class="base-btn-gradient btn" @click="exportReport">
        <svg-icon icon="icon-daochushenchabaogao" class="icon" />
        <span>导出报告</span>
      </div>
      <div class="base-btn-gradient btn" @click="exportWord">
        <svg-icon icon="icon-daochushenchabaogao" class="icon" />
        <span>导出word</span>
      </div>
    </div>

    <div class="body">
      <a-spin :spinning="loading">
        <div class="examine">
          <!-- <div class="sum">
            本次审查点共 <span style="color: var(--main-6)">{{ pointNum }}</span> 个，其中有<span
            style="color: var(--error-6)">{{ errorNum }}</span> 处存在风险
          </div> -->
          <div class="result-title">审查结果</div>
          <ul class="result-list">
            <li
            v-for="item in resultList"
            :key="item.value" class="result-item"
            :class="[resultType === item.value && 'active'] " @click="toggleResult(item)">
              <svg-icon v-if="item.icon" class="item-icon" :icon="item.icon"/>
             <span>{{item.label}}</span><span>({{resultTotal[item.key]}})</span>
            </li>
          </ul>
          <div class="tree">
            <a-collapse v-model:active-key="activeKey">
              <template #expandIcon="{ isActive }">
                <caret-right-outlined :rotate="isActive ? 90 : 0" />
              </template>
              <a-collapse-panel v-for="(section) in examineData" :key="section.id">
                <template #header>
                  <span>{{ section.label }} <span class="is-info">({{ section.pointNum || 0 }})</span></span>
                </template>
                <examine-item
                  v-for="item in section.children" :key="item.id"
                  :item="item"
                  :selected-item="selectedItem"
                  :expanded-items="expandedItems"
                  @toggle="toggleItem"
                />
              </a-collapse-panel>
            </a-collapse>
          </div>
        </div>
      </a-spin>
      <RiskTip v-if="riskData && riskTipVisible" :risk-data="riskData"/>
      <pdf-reader v-if="isPdf" :url="pdfSource" :page="currentPage" :rect="currentRect"/>
      <KkfileReader v-else :url="pdfSource"/>
    </div>
  </div>

  <ExamineItemsDialog v-model="dialogVisible" :data="dialogData"/>
</template>

<script setup lang="ts">
import {ref, computed, nextTick, onMounted, getCurrentInstance} from 'vue'
import { CaretRightOutlined } from '@ant-design/icons-vue'
import {useRouter} from 'vue-router'
import ExamineItemsDialog from '@/views/library/examine-items-modal.vue'
import ExamineItem from '@/views/library/components/examine-item.vue'
import RiskTip from '@/views/library/components/risk-tip.vue'
import PdfReader from '@/components/PdfReader/index.vue'
import KkfileReader from '@/components/KkfileReader/index.vue'
import {apiGetFile, apiReviewCheckPointDetail,  apiTaskResult} from "@/api/examine";
import { apiReviewImport, commentedFile } from '@/api/download'
import {riskOptions} from "@/views/hooks/examine";

const router = useRouter()


const dialogData = ref([])
const fileId = ref('')
const fileName = ref('')
const reviewTime = ref('')
const reviewResult = ref(0)
const pointNum = ref(0)
const errorNum = ref(0)
const backIcon = ref('icon-a-zu61')
// pdf
const pdfSource = ref('')
const isPdf = computed(() => {
  if (!pdfSource.value) return false
  return pdfSource.value.toLowerCase().endsWith('.pdf')
})
const {proxy} = getCurrentInstance()
const taskId = ref('')
// 审查点
const activeKey = ref([''])
const expandedItems = ref<string[]>([])
const selectedItem = ref<string>('')
const examineData = ref([])
const riskData = ref(null)
const riskTipVisible = ref(false)
// 点击 检查点
const currentPage = ref(1)
const currentRect = ref([])

function toggleItem(item: any) {
  riskData.value = null
  //风险点为有风险
  if (item.resultId && item.reviewResult === 1) {
    riskData.value = item
    riskTipVisible.value = true
  }

  const index = expandedItems.value.indexOf(item.id)
  selectedItem.value = item.id
  currentRect.value = item.position || []
  if (index > -1) {
    expandedItems.value.splice(index, 1)
  } else {
    expandedItems.value.push(item.id)
  }
  // 用非法页码强制更新，相同的页码也会触发跳转
  currentPage.value = -1
  if (item.page) {
    nextTick(() => {
      currentPage.value = item.page
    })
  }
}

// 查看审查点
const dialogVisible = ref(false)

async function doLook() {
  const params = {taskId: taskId.value}
  const {data, err} = await apiReviewCheckPointDetail(params)
  if (err) return
  dialogData.value = data.reviewItemList
  dialogVisible.value = true
}

// 选项卡
const resultType = ref(-1)
const resultTotal = ref<Record<string, number>>({
  all: 0,
  danger: 0,
  pass: 0
})
const resultList = ref([
  {
    value: -1,
    key: 'all',
    label: '全部',
    icon: ''
  },
  {
    value: 1,
    key: 'danger',
    label: '发现风险',
    icon: 'icon-shenchadianfengxiantishi'
  },
  {
    value: 0,
    key: 'pass',
    label: '未发现风险',
    icon: 'icon-shenchadianchenggongtishi'
  }
])
const toggleResult = (item: any) => {
  resultType.value = item.value
  if(riskData.value && resultType.value === 0) riskTipVisible.value = false
  else riskTipVisible.value = true
  // 获取数据
  initData()
}
//导出
const downloading = ref(false)
async function exportReport() {
  if(downloading.value) return
  downloading.value = true
  const params = {taskId: taskId.value}
  await apiReviewImport(params)
  downloading.value = false
}

/** 导出word */
async function exportWord() {
  if (downloading.value) return
  downloading.value = true
  const params = { taskId: taskId.value }
  await commentedFile(params)
  downloading.value = false
}

const loading = ref(false)
async function initData() {
  if(loading.value) return
  loading.value = true
  const params = {taskId: taskId.value, reviewResult: resultType.value === -1 ? undefined : resultType.value}
  const {data, err} = await apiTaskResult(params)
  loading.value = false
  if (err) return

  fileId.value = data.fileId
  fileName.value = data.fileName
  reviewResult.value = data.reviewResult
  reviewTime.value = data.reviewTime
  pointNum.value = data.pointNum
  errorNum.value = data.errorNum
  resultTotal.value = {
    all: data.pointNum ?? 0,
    danger: data.pointFailureNum ?? 0,
    pass: data.pointSuccessNum ?? 0
  }
  examineData.value = data.reviewItemList ?? []
  activeKey.value = data.reviewItemList.map((item: any) => item.id)
}

async function getFile() {
  const {data, err} = await apiGetFile(fileId.value)
  if (err) return
  pdfSource.value = data.fileUrl
}

onMounted(async () => {
  taskId.value = proxy.$route.query.taskId
  await initData()
  await getFile()
})
</script>

<style scoped lang="scss">
.result {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;

  .is-danger {
    color: var(--error-6);
  }
  .is-info {
    color: var(--text-3);
  }

  :deep(.ant-btn) {
    display: flex;
    align-items: center;
    gap: 8px;
  }
  .result-list {
    display: flex;
    align-items: center;
    gap:4px;
    margin-top: 16px;
    li {
      cursor: pointer;
      flex:1;
      display: flex;
      align-items: center;
      justify-content: center;
      min-width: 0;
      padding: 5px 0px;
      box-sizing: border-box;
      border-radius: 6px;
      font-size: 12px;
      background: var(--neutral-2);
      .item-icon {
        width: 14px;
        height: 14px;
        margin-right: 4px;
      }
      &.active {
        color: var(--fill-0);
        background: linear-gradient(103deg, #3B66F5 0%, #133CE8 100%);
      }
    }
  }
  :deep(.ant-collapse) {
    border: none;
    background-color: transparent;

    .ant-collapse-header {
      padding: 0 16px;
      height: 40px;
      align-items: center;
    }

    .ant-collapse-item {
      border: none;
      // border-radius: 8px;
      // &.ant-collapse-item-active,
      // &:hover {
      //   background: var(--main-1);
      // }
      .ant-collapse-header {
        &:hover {
          border-radius: 8px;
          background: var(--main-1);
        }
      }
      .ant-collapse-content-box {
        padding: 8px;
      }
    }

    &.is-empty {
      .ant-collapse-expand-icon {
        display: none;
      }
    }

    .ant-collapse-content {
      border: none;
    }
  }
  .icon {
    width: 16px;
    height: 16px;
  }

  .header {
    height: 56px;
    display: flex;
    align-items: center;
    padding: 12px 16px;
    border-bottom: 1px solid var(--neutral-3);
    .back {
      width: 32px;
      height: 32px;
      margin-right: 12px;
      cursor: pointer;
      &:hover {
        color: var(--main-6);
      }
      .back-icon {
        width: 100%;
        height: 100%;
      }
    }
    .title {
      flex: 1;
      display: flex;
      align-items: center;
      .icon {
        width: 20px;
        height: 20px;
        margin-right: 8px;
      }
    }

    .res {
      display: flex;
      align-items: center;
      margin-right: 12px;
      .t {

      }
    }
    .btn {
      margin-left: 12px;
      &.btn1 {
        margin-left:20px;
      }
    }
  }

  .body {
    flex: 1;
    display: flex;
    flex-direction: row;
    max-height: calc(100% - 56px);
    .examine {
      width: 400px;
      flex-shrink: 0;
      padding: 20px 16px;
      box-sizing: border-box;
      background: var(--fill-0);
      .result-title {
        font-size: 16px;
        font-weight: 500;
      }
      .sum {
        line-height: 22px;
        color: var(--text-5);
        border-bottom: 1px solid var(--fill-1);
      }

      .tree {
        height: calc(100% - 88px);
        overflow-y: auto;
        margin:16px 0;

        :deep(.ant-collapse-content-box){
          padding-right: 0px;
        }
      }
    }
  }
  :deep(.pdf-reader) {
    border-left:1px solid var(--neutral-3);
  }
}
</style>
