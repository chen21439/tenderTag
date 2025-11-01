import axios from 'axios'
import urlArgs from '../interceptors/url-args'
import format from '../interceptors/format'

class BaseService {
  protected instance
  protected responseHandler

  constructor(options: Object, responseHandler: Function, interceptors?: any[]) {
    this.instance = axios.create(options)
    this.responseHandler = responseHandler

    /* 前置拦截器，保证其处理后的数据可以被传入的requestConfig的值覆盖 */
    // 实现路径参数替换
    this.instance.interceptors.request.use(urlArgs.request.onFulfilled as any, undefined)


    // 自定义拦截器
    if (interceptors?.length) {
      interceptors.forEach((interceptor) => {
        if (Reflect.has(interceptor, 'request')) {
          this.instance.interceptors.request.use(interceptor.request.onFulfilled, interceptor.request.onRejected ?? undefined)
        }
        if (Reflect.has(interceptor, 'response')) {
          this.instance.interceptors.request.use(interceptor.response.onFulfilled, interceptor.response.onRejected ?? undefined)
        }
      })
    }

    // 请求拦截
    this.instance.interceptors.request.use(format.request.onFulfilled, format.request.onRejected)

    // 响应拦截
    this.instance.interceptors.response.use(format.response.onFulfilled, format.response.onRejected)
  }
}

export default BaseService
