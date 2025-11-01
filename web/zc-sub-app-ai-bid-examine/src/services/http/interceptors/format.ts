import { message } from 'ant-design-vue'
import config from '@/config';
import { cryptoDecrypt, snakeCaseToCamelCase, camelCaseToSnakeCase } from '@/utils/tools';
import { appLoginOut, getCookie } from '@/utils/app-gateway'

export const controllerList: any[] = []

// 处理请求取消
const cancelRequest = (config: any) => {
  const controller = new AbortController()
  config.signal = controller.signal
  controllerList.push(controller)
};

// 解码函数
const decode = (data: any, response: any) => {
  const url = response['config']['url'].split('?')
  const result = cryptoDecrypt(url[0], data)
  return result;
};

// 判断请求是否失败，若失败则返回理由
// 此方法只用于响应拦截器中，因此默认逻辑层请求成功，即不考虑http status为非200的情况
const requestFailed = (response: any) => {
  // 文件下载的情况，直接判定为请求成功
  const isBlob = response['data'] instanceof Blob
  if (isBlob) {
    return [false]
  }
  const { errCode: code, errMsg, success } = response['data']
  const message = response.data.message || errMsg
  // 默认success;一般情况下code为200一定意味着请求成功
  if (success) {
    return [false]
  }
  if (code !== 200) {
    return [true, message]
  }

  // 承接上文，除非有特殊情况额外用success表示成功失败
  if (typeof success !== 'undefined' && !success) {
    return [true, message || '网络不佳,请刷新后重试']
  }

  return [false]
};

// 获取响应码
const getErrorCode = (err: any) => {
  // 若应有层有返回，则使用应用层的
  if (err.response?.data?.errCode) {
    return err.response?.data?.errCode
  }
  // 否则返回协议层的
  return err.response?.status
};

// 是否可以提示异常
const canTip = (config: any) => {
  return config.noErrorTip !== true
};

// 提示错误
const tip = (msg: string) => {
  message.error({
    content: msg,
    duration: 3
  })
}

const formatHandler = {
  request: {
    onFulfilled: (request: any) => {
      // 处理请求头
      const bosssoftCookie = getCookie()
      const hasToken = bosssoftCookie?.token
      if (hasToken  && !request.noToken) {
        request.headers['Authorization'] = `Bearer ${bosssoftCookie.token}`
      }
      // 处理请求参数
      const method = (request.method ?? 'get').toLowerCase()
      if (config.api.formatRequestFields) {
        if (method === 'get') {
          camelCaseToSnakeCase(request.params)
        } else {
          request.data = request.data ?? {}
          camelCaseToSnakeCase(request.data)
          // 因为有些post接口也有queryString
          camelCaseToSnakeCase(request.params)
        }
      }
      // 处理请求取消
      cancelRequest(request)
      return request;
    },
    onRejected: (err: any) => {
      return Promise.reject(err)
    }
  },
  response: {
    onFulfilled: (response: any) => {
      // 逻辑层请求失败
      const [isFailed, msg] = requestFailed(response)
      if (isFailed) {
        if (canTip(response.config)) {
          // 失败了，可以提示，才提示
          tip(msg)
        }
        // 开发/测试环境不强制登出
        if (response.data.errCode === 401 || response.data.errCode === 409) {
          if (!config.isDev && !config.isTest) {
            setTimeout(()=> appLoginOut(),1000)
          }
        }
        return Promise.reject({ code: response.data.errCode, message: response.data.errMsg })
      }
      // 判断返回值是否是blob格式,是直接返回文件流
      const isBlob = response.data instanceof Blob
      if (isBlob) return response
      // 逻辑层请求成功
      const { data } = response['data']
      let parsedData = data
      // // 有加密则解密
      if (config.encrypt && data) {
        try {
          parsedData = JSON.parse(decode(data, response))
        } catch (e) {
          parsedData = {}
        }
      }

      if (config.api.formatResponseFields) {
        // 将下划线命名的属性转换为驼峰命名
        snakeCaseToCamelCase(parsedData)
      }

      response.data = parsedData
      return response
    },
    onRejected: (err: any) => {
      // 网络层请求失败
      if (!err.response) {
        return Promise.reject(err)
      }

      // 服务端返回错误
      const code = getErrorCode(err)
      if (canTip(err.response.config)) {
        switch (code) {
          case 403:
            tip('您没有该功能权限，请联系管理员')
            break;
          case 404:
            tip('当前路径不存在')
            break;
          case 500:
            tip('内部服务器错误，请稍后再试')
            break;
          default:
            tip(err.response.data.errMsg || '网络不佳，请刷新后重试')
            break;
        }
      }
      // 开发/测试环境不强制登出
      if (code === 401 || code === 409) {
        controllerList.forEach((controller) => controller.abort())
        if (!config.isDev && !config.isTest) {
          setTimeout(()=> appLoginOut(),1000)
        }
      }

      return Promise.reject(err)
    }
  }
};

export default formatHandler
