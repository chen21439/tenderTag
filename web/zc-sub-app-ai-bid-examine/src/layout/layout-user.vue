<template>
  <a-flex class="com-app-user">
    <a-popover
:arrow="false" placement="topLeft" :get-popup-container="node => {return node.parentNode}"
overlay-class-name="com-app-user-popover">
      <template #content>
        <a-flex vertical>
          <div class="username">{{ currentView.username }}</div>
          <a-button type="link" @click="onClickFeed">
            <svg-icon icon="icon-feedback" class="icon-feed" />
            <span class="text-feed">我要反馈</span>
          </a-button>
          <a-button type="link" @click="appLoginOut">
            <svg-icon icon="icon-logout" class="icon-logout" color="var(--error-6)" />
            <span class="text-logout">退出登录</span>
          </a-button>
        </a-flex>
      </template>
      <svg-icon icon="icon-user" class="icon-user" />
    </a-popover>

    <a-flex class="name-dep">
      <span class="t1">{{ currentView.username }}</span>
      <span class="t2"></span>
    </a-flex>
  </a-flex>
  <!-- 反馈 -->
   <BaseDialog v-model="feedModalVisible" title="感谢您的反馈" confirm-text="提交" width="600px" :loading="feedLoading" @confirm="onClickConfirm">
    <a-textarea v-model:value="feedText" class="feed-area"/>
   </BaseDialog>
</template>
<script setup lang="ts">
import type { BosssoftCookie } from '@/typings/login'
import { onMounted, reactive, ref } from 'vue'
import { getCookie, appLoginOut } from '@/utils/app-gateway'
import { BaseDialog } from '@/components/BaseDialog'
import { saveComplaint } from '@/api/login'

defineOptions({ name: 'LayoutUser' })

type Props = {
  userVisible?: boolean
}

const props = withDefaults(defineProps<Props>(), {})
const currentView = reactive({
  username: ''
})
// 反馈
const feedModalVisible = ref(false)
const feedLoading = ref(false)
const feedText = ref('')
const onClickFeed = ()=> {
  feedText.value = ''
  feedModalVisible.value = true
}
const onClickConfirm = async ()=> {
  feedLoading.value = true
  const { err, data} =  await saveComplaint({content: feedText.value})
  if(err) return
  feedModalVisible.value = false
  feedLoading.value = false
}
onMounted(() => {
  const bosssoftCookie: BosssoftCookie = getCookie()
  currentView.username = bosssoftCookie?.userName
})
</script>
<style lang="scss" scoped>
.com-app-user {
  display: flex;
  border: none;
  .name-dep {
    display: none;
  }
  .icon-user {
    width: 40px;
    height: 40px;
  }
}
.base-dialog {
  .base-dialog-header {
    height: auto;
    padding: 0;
    font-size: var(--font-16);
    font-weight: bold;
  }

  .feed-area {
    width: 552px;
    height: 195px;
    border-radius: var(--border-radius-16);
    background: var(--fill-1);
    border: 1px solid var(--line-3);
  }
  .base-dialog-footer {
    :deep(.btn-cancel) {
      margin-left: 16px;
    }
  }
}

 :deep(.com-app-user-popover) {
  width: 200px;
  border-radius: var(--border-radius-8);
  box-shadow: 0px 6px 16px 0px rgba(0, 0, 0, 0.15);
  .username {
    font-size: var(--font-14);
    letter-spacing: 0.1em;
    white-space: break-spaces;
    word-break: break-all;
    overflow: hidden;
  }
  .icon-feed,
  .icon-logout{
    width: 16px;
    height: 16px;
  }
  .ant-btn {
    display: flex;
    align-items: center;
    gap: 12px;
    padding-left: 0;
  }

  .ant-btn > span {
    font-size: var(--font-14);
    cursor: pointer;
  }
  .text-logout{
    color: var(--error-6);
  }
  .text-feed {
    color: var(--text-5)
  }
}

</style>
