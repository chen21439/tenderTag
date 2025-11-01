<template>
  <div v-if="iframeSrc" class="pdf-reader">
    <iframe ref="refIframe" width="100%" height="100%" :src="iframeSrc" @load="onLoad" />
    <div v-if="!pdfInitialized" class="loading-wrapper">
      <div class="loading"></div>
    </div>
  </div>
</template>

<script setup lang='ts'>
import { computed, ref,  onMounted, onUnmounted } from 'vue'

defineOptions({
  name: 'PdfReader'
})
type Props = {
  url: string // 地址
  page?:number// 页码
  // zoom?:number | string // 缩放比例
  // search?:string// 高亮关键词
  position?:any[] //  [{page,x1,y1,x2,y2,annotations:[]}] 坐标点 
}
const props = withDefaults(defineProps<Props>(), {
  page: 1,
  // zoom: 'page-fit',
  // search:'',
  position: ()=>[]
}) 
const srcPrefix = new URL(`/static-resources/pdfjs-v5.4.54-dist/web/viewer.html?V3.0&file=`, new URL(import.meta.url).origin).href
const refIframe = ref<HTMLIFrameElement>() 
const isIframeLoaded = ref(false) 
const pdfInitialized = ref(false) 
const pdfReady = ref(false) 
const annotationsInitialized = ref(false)  
const iframeSrc = computed(()=> {
  const {url, page = 1} = props
  if(!url) return ''
  let uri = url
  if (url.startsWith('http')) {
    const protocolIndex = url.indexOf('://')
    const domainStartIndex = protocolIndex + 3
    const pathStartIndex = url.indexOf('/', domainStartIndex)
    if (pathStartIndex !== -1) {
      uri = url.substring(pathStartIndex)
    }
  }
   return srcPrefix.concat(
    encodeURIComponent(uri),
    `#page=${page}`
  )
}) 
// 等待iframe加载完成
const onLoad = () => {
  isIframeLoaded.value = true
}
// 监听来自 iframe 的消息
const handleMessage = (event: MessageEvent) => {
  console.log('handleMessage', event.data.type);
  if(event.data.type === 'annotationReady') {
    annotationsInitialized.value = true 
  }
  if (event.data.type === 'pdfReady') { 
    pdfReady.value = true 
  }
  if (annotationsInitialized.value && pdfReady.value) { 
    pdfInitialized.value = true   
    // 初始化高亮+批注
    setTimeout(() => {
      applyHighlight()
    }, 300)
  }
}
// 
const applyHighlight =()=> {
  const { position } = props
  if (!position?.length) return;
  const iframe = refIframe.value
  if (!iframe || !iframe.contentWindow) {
    console.warn('iframe或contentWindow不可用，无法应用高亮');
    return;
  }
  // 向iframe发送高亮和批注更新消息
  console.log('applyHighlight-向iframe发送高亮和批注更新消息',);
  const message = {
      type: 'updateHighlight',
      highlightarea: JSON.parse(JSON.stringify(position))
  };
  iframe.contentWindow.postMessage(message, '*');
}

onMounted(() => {
  window.addEventListener('message', handleMessage)
})

onUnmounted(() => {
  window.removeEventListener('message', handleMessage)
})
defineExpose({
  refreshHighlight: applyHighlight
})
</script>

<style lang="scss" scoped>
.pdf-reader {
  width: 100%;
  height: 100%;
  position: relative;
}

.loading-wrapper {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(var(--fill-rbg-0), 0.8);
  display: flex;
  justify-content: center;
  align-items: center;
}

.loading {
  width: 40px;
  height: 40px;
  border: 3px solid var(--fill-1);
  border-top: 3px solid var(--main-6);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style>
