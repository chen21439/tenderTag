<template>
  <!--  <BaseDialog-->
  <!--    v-model="open" title="查看审查点" width="large"-->
  <!--    :show-confirm-button="false" :show-cancel-button="false">-->
  <!--    删除后将无法找回，是否删除？-->
  <!--  </BaseDialog>-->
  <div class="examine-items-modal">
    <a-modal v-model:open="open" title="查看审查点" :width="1200" :footer="null" :get-container="getContainer">
      <template v-for="(item, index) in data" :key="index">
        <div class="title">
          <div class="line"/>
          <div class="t">{{ item.reviewItemName }}</div>
        </div>
        <a-table :dataSource="item.checkPointList" :columns="columns" :pagination="false">
          <template #bodyCell="{ column, index, record, text }">
            <template v-if="column.dataIndex === 'checkPointStatus'">
              <span :style="`color: ${checkPointStatusMap[text]?.color}`">{{ checkPointStatusMap[text]?.label }}</span>
            </template>
          </template>
        </a-table>
      </template>

      <!--      <div class="title">-->
      <!--        <div class="line" />-->
      <!--        <div class="t">关键词审查</div>-->
      <!--      </div>-->
      <!--      <a-table :dataSource="dataSourceKeyword" :columns="columnsKeyword" :pagination="false">-->
      <!--        <template #bodyCell="{ column, index, record, text }">-->
      <!--          <template v-if="column.dataIndex === 'enable'">-->
      <!--            <span v-if="text" style="color: green">是</span>-->
      <!--            <span v-if="!text" style="color: red">否</span>-->
      <!--          </template>-->
      <!--        </template>-->
      <!--      </a-table>-->
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import {computed} from 'vue'
import { checkPointStatusMap } from '@/views/hooks/use-options'

interface Props {
  modelValue: boolean
  data: any
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: false
})

const emits = defineEmits(['update:model-value'])

const open = computed({
  get: () => props.modelValue,
  set: (val: boolean) => {
    emits('update:model-value', val)
  }
})

const columns = [
  {
    title: '序号',
    key: 'index',
    fixed: 'left',
    width: 60,
    customRender: (row: any) => {
      return row.index + 1
    }
  },
  {title: '审查点名称', dataIndex: 'checkPointName', width: 200},
  {title: '法律依据', dataIndex: 'legalBasic'},
  {title: '是否启用', dataIndex: 'checkPointStatus', width: 100, align: 'center'}
]

// const columnsKeyword = [
//   {
//     title: '序号',
//     key: 'index',
//     fixed: 'left',
//     width: 60,
//     customRender: (row: any) => {
//       return row.index + 1
//     }
//   },
//   {title: '关键词名称', dataIndex: 'keyword'},
//   {title: '是否启用', dataIndex: 'enable', width: 100, align: 'center'}
// ]

function getContainer() {
  return document.querySelector('.examine-items-modal') as HTMLElement
}
</script>

<style scoped lang="scss">
.examine-items-modal {

  :deep(.ant-modal-body) {
    display: flex;
    flex-direction: column;
    gap: 8px;
    max-height: 75vh;
    overflow-y: auto;
  }

  .title {
    display: flex;
    align-items: center;
    gap: 8px;

    .line {
      width: 4px;
      height: 16px;
      background: var(--main-6);
      border-radius: 4px;
    }

    .t {
      font-size: 16px;
    }
  }
}
</style>
