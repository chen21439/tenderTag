import  { useMenusStore } from '@/store'
import { computed, watch, ref } from 'vue'
import { SystemInfo } from '@/config'
// 目前只在咨询子应用单独访问时配置主题
export const useTheme = ()=>{
  const menusStore = useMenusStore()
  watch(()=> menusStore.themeKey,
(val)=> {
    const info = SystemInfo[val] 
    const element = document.documentElement
    element.setAttribute('data-theme', val) 
  try {
    const link = document.querySelector('link[rel="icon"]')
    const title = document.getElementsByTagName("title")
    title[0].innerHTML = info.htmlTitle ?? '阳光公采大模型1.0'
    if(link) link.href = info.htmlLogo ?? '/logo.png'
  }
  catch(e) {
    console.log(e,'index.html报错')
  }
  menusStore.setSystemInfo(info)
},
{
  immediate: true
})
}
// 加载主题图片
export const loadThemeImg = (img: string) => {
  const menusStore = useMenusStore()
  // const themeKey = computed(()=>  menusStore.isTianda ? 'tianda' : 'default')
  const themeKey = ref('default')
  const res = new URL(`/src/assets/images/theme/${themeKey.value}/${img}`, import.meta.url).href
  return res
}
