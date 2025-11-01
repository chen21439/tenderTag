<template>
  <div class="com-table">
    <div class="header">
      <a-space :size="12">
        <div class="back"  @click="router.push({ name: 'HomeIndex' })"
        @mouseenter="backIcon = 'icon-btn1'"
            @mouseleave="backIcon = 'icon-a-zu61'">
          <svg-icon :icon="backIcon" class="back-icon" /> 
        </div>
        <a-breadcrumb>
          <a-breadcrumb-item>设置审查项</a-breadcrumb-item>
        </a-breadcrumb>
        <ul class="type-box">
          <li
          v-for="item in examineItemTypes"
          :key="item.code"
          :class="{'active': formSearch.reviewItemCode === item.code}"
          @click="changeType(item)">
          {{item.name}}</li>
        </ul>
      </a-space>
      <div class="search-bar">
        <a-input-search v-model:value="formSearch.pointName" style="width: 200px;" placeholder="请输入审查点名称" allow-clear max-length="50" @search="doSearch"/>
        <!-- <div class="base-btn-gradient" @click="doSearch()">
          <SearchOutlined class="icon" />
          <span>查询</span>
        </div>
        <div class="base-btn-gradient" @click="doEdit({})">
          <svg-icon icon="icon-plus" class="icon" />
          <span>新增审查点</span>
        </div> -->
      </div>
    </div>

    <a-table
      :data-source="dataSource"
      :columns="columns"
      :pagination="pagination"
      class="table"
      :loading="listLoading"
      @change="onTableChange">
      <template #bodyCell="{column, record, text}">
        <template v-if="column.dataIndex === 'status'">
          <a-switch :checked="text === 1" @click="clickEnable(record)"/>
        </template>
        <template v-if="column.dataIndex === 'basisDesc'">
          <div v-if="text" class="law-box">
            <span v-for="(item,tindex) in text.split('\n')" :key="tindex" class="law-item">{{item}}</span>
          </div>
        </template>
        <template v-else-if="column.dataIndex === 'handle'">
          <div class="btns">
            <!-- <a-button type="link" size="small" @click="doEdit(record)">编辑</a-button> -->
            <a-button type="link" size="small" @click="doDetail(record)">查看</a-button>
          </div>
        </template>
      </template>
    </a-table>
  </div>

  <BaseDialog
    v-model="open"
    :title="title"
    width="large"
    :show-cancel-button="showCancelButton"
    :show-confirm-button="showConfirmButton"
    @confirm="handleOk">
    <a-form :model="form" :label-col="{ span: 4 }" :disabled="formDisabled">
      <a-form-item label="审查点名称" name="pointName" :rules="[{ required: true, message: '审查点名称不能为空' }]">
        <a-input v-model:value="form.pointName"   max-length="50"/>
      </a-form-item>

      <a-form-item label="法律依据" name="basisDesc" :rules="[{ required: true, message: '法律依据不能为空' }]">
        <a-textarea v-model:value="form.basisDesc"   :auto-size="{ minRows: 3, maxRows: 5 }" max-length="200"/>
      </a-form-item>

      <a-form-item label="是否启用" name="enable">
        <a-switch v-model:checked="form.enable"/>
      </a-form-item>
    </a-form>
  </BaseDialog>
</template>

<script setup lang="ts">
import {computed, onMounted, reactive, ref} from 'vue'
import { v4 as uuid } from 'uuid'
import {useRouter} from 'vue-router'
import {BaseDialog} from '@/components/BaseDialog'
import {
  apiCheckPointDetail,
  apiCheckPointDisable,
  // apiCheckPointEdit,
  apiCheckPointEnable, apiGetCheckPointPage,
  apiGetReviewItemTypeList
} from '@/api/examine';

const router = useRouter()
const backIcon = ref('icon-a-zu61')
const total = ref(0)
const dataSource = ref<any>([])
const examineItemTypes = ref<any>([])
const paginationCurrent = reactive({
  pageNum: 1,
  pageSize: 10
})
// 获取审核项目类型集
async function getExamineItemTypes() {
  examineItemTypes.value = []

  const {err, data} = await apiGetReviewItemTypeList()
  if (err) return
  examineItemTypes.value = data
  formSearch.reviewItemCode = data[0]?.code ?? ''
}
const listLoading = ref(false)
async function getExamineItems(options: Record<string, any> = {}) {
  dataSource.value = []
  const params = {
    pageNum: 1,
    pageSize: paginationCurrent.pageSize,
    ...formSearch,
    ...options
  }
  listLoading.value = true
  const {err, data} = await apiGetCheckPointPage(params)
  listLoading.value = false
  if (err) return
  dataSource.value = data.dataList ?? []
  total.value = data.total ?? 0
}
const changeType = (data: any) => {
  formSearch.reviewItemCode = data.code
  doSearch()
}
// 弹框
const open = ref<boolean>(false)
const title = ref()
const formDisabled = ref(false)
const showCancelButton = ref(false)
const showConfirmButton = ref(false)

const pagination = computed(() => {
  return {
    current: paginationCurrent.pageNum,
    pageSize: paginationCurrent.pageSize,
    total: total.value,
    showSizeChanger: false
  }
})

async function onTableChange(pag: any) {
  const {current, pageSize} = pag

  const params = {
    pageNum: current,
    pageSize
  }

  getExamineItems(params)
  paginationCurrent.pageNum = current
}

const form = reactive<any>({
  reviewItemCode: '',
  pointName: '',
  basisDesc: '',
  status: 0
})

const formSearch = reactive({
  pointName: '',
  reviewItemCode: ''
})

async function doSearch() {
  getExamineItems()
}

// 编辑
async function doEdit(record: any) {
  const isEdit = !!record.pointId
  title.value =  isEdit ? '编辑' : '新增'
  formDisabled.value = false
  showCancelButton.value = true
  showConfirmButton.value = true
  Object.assign(form, {
    pointId: uuid(),
    pointName: '',
    basisDesc: '',
    enable: true
  })
  open.value = true
}
// todo:静态数据
async function handleOk() {
  const item = {
    ...form,
    status: form.enable ? 1 : 0
  }
  delete item.enable
  dataSource.value.push(item)
  open.value = false
}
// 查看
async function doDetail(record: any) {
  let pointId = record.pointId

  let {err, data} = await apiCheckPointDetail({pointId})
  if (err) return

  Object.assign(form, data, {enable: data.status === 1})
  title.value = '查看'
  formDisabled.value = true
  showCancelButton.value = false
  showConfirmButton.value = false
  open.value = true
}

const columns = [
  {
    title: '序号',
    dataIndex: 'index',
    fixed: 'left',
    width: 60,
    customRender: (row: any) => {
      return row.index + 1
    }
  },
  {title: '审查点名称', dataIndex: 'pointName', width: 360},
  {title: '法律依据', dataIndex: 'basisDesc'},
  {title: '是否启用', dataIndex: 'status', width: 100},
  // {title: '操作', dataIndex: 'handle', width: 100, fixed: 'right'}
]

async function clickEnable(record: any) {
  let res: Record<any, any> = {}
  if (record.status === 1) {
    res = await apiCheckPointDisable({pointId: record.pointId})
  } else {
    res = await apiCheckPointEnable({pointId: record.pointId})
  }
  if (res.err) return

  dataSource.value = dataSource.value.map((item: any) => {
    if (item.pointId === record.pointId) {
      let status = item.status === 1 ? 0 : 1
      return {...item, status}
    }
    return item
  })
}

onMounted(async () => {
  await getExamineItemTypes()
  await getExamineItems()
})
</script>

<style scoped>
.com-table {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  padding:0 16px;

  /* :deep(.ant-btn) {
    display: flex;
    align-items: center;
    gap: 8px;
  } */

  .icon {
    width: 16px;
    height: 16px;
  }

  .header {
    display: flex;
    align-items: center;
    padding: 32px 0;
    justify-content: space-between;
    background: radial-gradient(45% 192% at 51% -109%, rgba(27, 88, 255, 0.2) 0%, rgba(133, 191, 251, 0) 100%);
    .back {
      width: 32px;
      height: 32px;
      cursor: pointer;
      &:hover {
        color: var(--main-6);
      }
      .back-icon {
        width: 100%;
        height: 100%;
      }
    }
    :deep(.ant-breadcrumb) {
      .ant-breadcrumb-link{
        font-size: 20px;
        font-weight: 500;
        color: #3D3D3D;
      }
      .ant-breadcrumb-separator {
        display: inline-block;
        vertical-align: middle;
        margin-top: -10px;
        padding:0 8px 0 20px;
        color: #D8D8D8;
      }
    }
    .type-box {
      display: flex;
      align-items: center;
      border: 1px solid var(--neutral-3);
      padding: 4px 0;
      border-radius: 8px;
      box-sizing: border-box;
      li {
        color: var(--text-4);
        margin-left: 4px;
        cursor: pointer;
        padding: 4px 16px;
        border-radius: 6px;
        box-sizing: border-box;
        &:hover {
          color: var(--main-6);
        }
        &:last-child {
          margin-right: 4px;
        }
        &.active {
          color: var(--fill-0);
          background: linear-gradient(103deg, #3B66F5 0%, #133CE8 100%);
          box-shadow: 0px 1px 2px 0px rgba(0, 0, 0, 0.03),0px 1px 6px -1px rgba(0, 0, 0, 0.02),0px 2px 4px 0px rgba(0, 0, 0, 0.02);
        }
      }
    }
    .search-bar {
      display: flex;
      gap: 16px;
    }
  }
  :deep(.ant-input-search) {
        border: 1px solid var(--line-4);
        border-radius: 4px;
        &:hover,
        &:focus {
          border-color: var(--main-6);
        }
        &:active {
          border-color: var(--main-6);
          box-shadow: 0px 0px 0px 2px rgba(19, 60, 232, 0.1);
        }
       .ant-input-affix-wrapper {
        box-shadow: none;
        border:0;
        &.ant-input-affix-wrapper-focused,
        &:focus,&:active,&:hover  {
          box-shadow: none;
          border:0;
        }
       }
        &:hover {
          .ant-input-affix-wrapper {
            border-right: 0;
            box-shadow: none;
          }
        }
        .ant-input-search-button {
          border: 0;
          box-shadow: none;
        }
        .anticon svg {
          vertical-align: middle;
          margin-top: -4px;
        }
        .ant-input-group-addon:last-child
        .ant-input-search-button:not(.ant-btn-primary):hover,
        .ant-input-search-button:not(.ant-btn-primary):active  {
          border-color: var(--line-4);
          color: var(--text-4);
          box-shadow: none;
        }
    }
  :deep(.ant-table) {
    .btns {
      display: flex;
    }
    .law-box {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
    }
    .law-item {
      padding: 5px 8px;
      border-radius: 6px;
      border: 1px solid var(--neutral-3);
      background-color: var(--neutral-1);
      box-sizing: border-box;
    }
    .ant-table-cell{
      color: var(--text-5);
    }
    th.ant-table-cell{
      color: var(--text-5);
    }
  }
}
</style>
