<template>
  <div class="uploader">
    <div v-if="checkVisible" class="body">
      <div class="scroll-box">
        <div class="files">
          <template v-for="item in fileList" :key="item.uid">
            <div class="files-item">
              <svg-icon icon="icon-guanbi-yuan" class="icon icon-close2" @click="handleRemove(item)" />
              <svg-icon :icon="getFileIcon(item)" class="icon-file" />
              <div class="info">
                <a-tooltip :title="item.name"> <span class="file-name">{{ item.name }}</span></a-tooltip>
                <div class="type-size">
                  <span>{{ item.type }}</span>
                  <span>{{ item.size }}</span>
                </div>
              </div>
              <div v-if="item.status === 'uploading'" class="progress" :style="{width: `${item.percent}%`}">{{ item.percent }}</div>
            </div>
          </template>
          <upload-file
            ref="uploadFileRef"
            v-model:files="fileList"
            button-text="上传文档"
            accept=".pdf,.doc,.docx"
            accept-tip="标书文件只能是pdf/word文件"
            :show-upload-list="false"
          >
          <!-- ,.doc,.docx -->
          <div class="file-add">
            <img width="28" height="28" src="@/assets/images/bid-examine/upload-icon.png" alt="" />
            <div class="t">点击上传文件</div>
          </div>
        </upload-file>
        </div>
      </div>
      <div class="remark">
        仅支持PDF/WORD格式文档，单个文档大小不超过20M，最多上传10份，您上传的所有文档在您审查档案库中查看，其他人不可见
      </div>
    </div>
    <div class="agree-box">
      <a-checkbox v-model:checked="agree">
        <span>阅读并同意</span>
      </a-checkbox>
      <span style="color: var(--main-6);cursor: pointer;" @click.stop="onClickAgreement">用户使用协议</span>
    </div>
    <div class="btns">
      <div class="base-btn-gradient" :class="{disabled: !agree}" @click="doCheck">
        <svg-icon icon="icon-kaishishencha" class="icon" />
        开始审查
      </div>
    </div>
  </div>
   <!-- 关闭上传弹框提示 -->
   <BaseDialog v-model="uploaderConfirmVisible" title="关闭页面" @confirm="doUploaderClose">
    关闭当前页面您所上传的所有文件都将删除？
  </BaseDialog>
  <!-- 用户协议 -->
   <BaseDrawer v-model="agreementVisible" title="用户使用协议" width="90vw">
    <Agreement @read="onClickCloseAgreement"/>
  </BaseDrawer>
</template>

<script setup lang='ts'>
import { ref, computed, watch } from 'vue'
import  { message } from 'ant-design-vue'
import {apiTaskCreate} from '@/api/examine'
import { useRouter } from 'vue-router'
import { BaseDialog } from '@/components/BaseDialog'
import { BaseDrawer } from '@/components/BaseDrawer'
import UploadFile from '@/components/UploadFile/index.vue'
import Agreement from '@/views/user-agreement/index.vue'

const emits = defineEmits(['close','update:files', 'closeAfter'])

interface Props {
  closable?: boolean,
  checkVisible?: boolean,
  files?: any[]
}

const props = withDefaults(defineProps<Props>(), {
  closable: true,
  checkVisible: true,
  files: () => {
    return []
  }
})
const router = useRouter()
const fileList = computed({
  get: () => props.files,
  set: (newFiles:any) => {
    emits('update:files', [...newFiles])
  }
})
const uploadFileRef = ref()
const handleRemove = (file: any) => {
  uploadFileRef.value?.handleRemove(file)
}
const getFileIcon = (item)=> {
  let fileIcon = 'pdf-fill'
  switch (item.type) {
    case 'DOCX':
    case 'DOC':
      fileIcon =  'docx-fill'
      break;
    default:
      break 
  }
  return `icon-${fileIcon}`
}
// 开始审查
const agree = ref(false)
// 用户使用协议
const agreementVisible = ref(false)
const onClickAgreement = () => {
  agreementVisible.value = true
}
const onClickCloseAgreement = () => {
  agreementVisible.value = false
  agree.value = true
}
const doCheck = async () => {
  if (!agree.value) return
  if (fileList.value.length === 0) {
    message.info('请至少上传一个文件')
    return
  }
  // 提示文件上传中
  if (props.files.some((item: any) => item.status === 'uploading')) {
    message.info('文件正在上传中，请稍后')
    return
  }
  emits('close')
  const fileIdList = props.files.map((item: any) => item.response?.fileId)
  const {err} = await apiTaskCreate({fileIdList})
  if (err) return
  agree.value = false
  emits('closeAfter')
}

// 关闭上传弹框提示
const uploaderConfirmVisible = ref(false)
const doUploaderCancel = () =>{
  uploaderConfirmVisible.value = true
}
// const goHome = () => {
//   doUploaderCancel()
//   router.push({ name: 'HomeIndex' })
// }
const doUploaderClose = () => {
  fileList.value = []
  uploaderConfirmVisible.value = false
  emits('close')
}
defineExpose({
  cancel: doUploaderCancel,
  close: doUploaderClose
})
</script>

<style lang="scss" scoped>
.uploader {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  .icon {
    width: 16px;
    height: 16px;
  }

  .icon-file {
    width: 32px;
    height: 32px;
    flex-shrink: 0;
  }

  .icon-close {
    position: absolute;
    top: 8px;
    right: 8px;
    cursor: pointer;
  }

  .icon-close2 {
    position: absolute;
    top: -8px;
    right: -8px;
    cursor: pointer;
    &:hover {
      color: var(--fill-9);
    }
    &:active {
      color: var(--fill-12);
    }
  }

  .body {
    position: relative;
    width: 100%;
    min-height: 400px;
    max-height: 500px;
    display: flex;
    flex-direction: column;
    border-radius: 12px;
    // background: radial-gradient(100% 139% at 0% 0%, rgba(217, 242, 255, 0.5) 0%, rgba(242, 240, 252, 0.5) 27%, rgba(191, 216, 255, 0.5) 100%);
    box-sizing: border-box;
    border: 1px solid var(--neutral-3);
    background-color: var(--neutral-1);
    .scroll-box {
      padding-top: 32px;
      padding-left: 24px;
      overflow-y: auto;
      overflow-x: hidden;
    }

    .files {
      display: flex;
      flex-wrap: wrap;
      gap: 16px;

      .files-item {
        position: relative;
        flex: 1;
        max-width: 272px;
        min-width: 272px;
        height: 72px;
        flex-shrink: 0;
        display: flex;
        align-items: center;
        box-sizing: border-box;
        padding: 16px;
        border-radius: 8px;
        background: var(--fill-0);
        box-sizing: border-box;
        border: 1px solid var(--neutral-3);
        box-shadow: 0px 1px 2px 0px rgba(0, 0, 0, 0.03),0px 1px 6px -1px rgba(0, 0, 0, 0.02),0px 2px 4px 0px rgba(0, 0, 0, 0.02);
        .progress {
          position: absolute;
          top: 0;
          left: 0;
          z-index: 0;
          height: 100%;
          background: var(--main-6);
          border-radius: 8px 0 0 8px;
          opacity: 0.08;
          transition: width 0.3s ease;
        }
        .info {
          display: flex;
          flex-direction: column;
          flex: 1;
          min-width: 0;
          padding: 0 8px;
          .file-name {
            position: relative;
            z-index: 1;
            display: block;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
          }
          .type-size {
            display: flex;
            justify-content: space-between;
            margin-top: 8px;
            color: var(--text-3);
          }
        }
      }

      .file-add {
        width: 272px;
        height: 72px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        box-sizing: border-box;
        padding: 8px;
        cursor: pointer;
        border-radius: 4px; 
        border-radius: 8px;
        background: var(--fill-0);
        box-sizing: border-box;
        border: 1px solid var(--neutral-3);
        box-shadow: 0px 1px 2px 0px rgba(0, 0, 0, 0.03),0px 1px 6px -1px rgba(0, 0, 0, 0.02),0px 2px 4px 0px rgba(0, 0, 0, 0.02);
        &:hover,
        &:active {
          border-width: 2px;
          border-color: var(--main-5);
        }
        .t {
          font-size: var(--font-14);
          font-weight: 500;
          color: var(--main-6);
        }
      }
    }

    .remark {
      font-size: 12px;
      color: var(--text-3);
      padding: 16px 24px 32px 24px;
    }
  }
  .agree-box {
    margin-top: 32px;
    :deep(.ant-checkbox+span){
      padding-right: 0;
    }
  }
  .btns {
    display: flex;
    gap: 12px;
    justify-content: center;
  }
}
</style>
