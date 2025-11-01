<template>
    <div class="file-reader-container">
        <a-spin :spinning="loading" tip="加载中...">
            <iframe :src="fileViewUrl" width="100%" height="100%" @load="handleIframeLoad"></iframe>
        </a-spin>
    </div>
</template>
<script lang="ts" setup>
import { Base64 } from 'js-base64'
import { ref, computed, onMounted } from 'vue'
defineOptions({ name: 'KkfileReader' })
interface Props {
    url: string,
    page?: number
}
const props = withDefaults(defineProps<Props>(), {
    url: '',
    page: 1
})
const loading = ref(true)

// 处理iframe加载完成事件
const handleIframeLoad = () => {
    loading.value = false
}

// kkFileview地址
const fileViewUrl = computed(() => {
    const { page = 1, url = '' } = props
    const previewUrl = url ? encodeURIComponent(Base64.encode(url)) : ''
    if (!previewUrl) return ''
    return import.meta.env.VITE_APP_FILE_VIEW_URL + '?url=' + previewUrl + '&officePreviewType=pdf&tifPreviewType=pdf' + '&page=' + page
})
</script>
<style scoped lang="scss">
.file-reader-container {
    width: 100%;
    height: 100%;
    position: relative;
    overflow: hidden;
    iframe{
        display: flex;
    }
} 
:deep(.ant-spin-nested-loading) {
    width: 100%;
    height: 100%;
    .ant-spin-container,
    .ant-spin-blur{
        width: 100%;
        height: 100%;
    }
} 
</style>