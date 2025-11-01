/**
 * sse 请求
 * @param str 字符串
 */
import { fetchEventSource } from '@microsoft/fetch-event-source'
import { getCookie, appLoginOutHandler } from '@/utils/app-gateway'
import { message } from 'ant-design-vue'

// 参数处理
const factory = (options: Record<string,any>) => (
    (options.method = options.method || 'POST'),
    (options.headers = {
        'Content-Type': 'application/json',
        Authorization: 'Bearer ' + getCookie()?.token,
        ...options.headers
    }),
    (options.body = JSON.stringify(options.body) || {}),
    options
)
// 参数处理
export default function () {
  return {
    // 开始sse
    start: async (url:string, options = {}, callback: any) => {
      try {
        if (!url) {
          console.log('请输入有效url')
          return
        }
       await fetchEventSource(url, {
          ...factory(options),
          openWhenHidden: true,
          onopen(response) {
            if (response.status === 401 || response.status === 409) {
              message.error( '登录失效，请重新登陆')
              callback({ status: 'noPermission', message: '登录失效，请重新登陆'})
              setTimeout(()=> appLoginOutHandler(),500)
              throw response
            }
          },
          onmessage(event) {
            if (event.data === '[DONE]') return
            if (event.data.length !== 0) {
              callback({ status: 'running', message: JSON.parse(event.data) })
            }
          },
          onerror(error) {
            callback({
              status: 'error',
              message: '服务器出错了， 请稍后重试.....',
              error: true
            })
            throw error // 必须抛出错误，否则停止不了
          },
          onclose() {
            callback({ status: 'close', message: '读取结束' })
          }
        })
      } catch (error) {
        console.log(error,'流式请求')
      }
    },
    // 停止sse
    stop: () => {
      console.log('停止了')
    }
  }
}
