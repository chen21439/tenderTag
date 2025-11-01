import type { AxiosResponse } from 'axios'
import { message } from 'ant-design-vue'
import type { AppRequestConfig } from './type'
import HttpService from './core/http-service'
import DownloadService from './core/download-service'
import config from '@/config'
const baseOptions = {
  timeout: config.api.timeout,
  withCredentials: false,
  headers: config.api.commonHeaders,
  baseURL:'/'
  // baseUrl: config.api.baseUrl
};
const responseHandler = (response: AxiosResponse<any, AppRequestConfig>) => {
  const { data } = response
  let result = data
  if (data && data.data) {
    result = data.data
  }
  return { err: null, data: result, response }
}

export const { http } = new HttpService(baseOptions, responseHandler)


// 下载
const downloadResponseHandler = (response: AxiosResponse<Blob, AppRequestConfig>, extraInfo: any) => {
  const { data } = response
  let fileName = ''
  if (extraInfo && extraInfo.fileName) {
    fileName = extraInfo.fileName
  } else {
    fileName = response.headers['content-disposition']
      ? decodeURI(
        response.headers['content-disposition'].split(';')[1].split('=')[1]
      )
      : ''
  }

  try {
    const type = response.headers['content-type']
    let blob: Blob;
    if (type) {
      if (type === 'application/json') {
        const reader = new FileReader()
        reader.readAsText(data, 'utf-8')
        reader.onload = function () {
          const { success: rSuccess, errMsg:rErrMsg } = JSON.parse(reader.result)
          if(!rSuccess) message.error(rErrMsg || '下载失败')
        }
        return Promise.reject('error')
      }
      blob = new Blob([data], {
        type
      })
    } else {
      blob = new Blob([data])
    }

    if ('msSaveBlob' in window.navigator) {
      (window.navigator as any).msSaveBlob(blob)
    } else {
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', fileName)
      link.style.display = 'none'
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      // 释放内存
      window.URL.revokeObjectURL(link.href)
    }
    message.success('下载成功!')
  } catch (err) {
    console.error(err);
    message.error('下载失败!')
  }
};

export const { download: downLoadHttp } = new DownloadService(baseOptions, downloadResponseHandler)
export { DownloadService }
