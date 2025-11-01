import type { AxiosResponse } from 'axios'
import type { AppRequestConfig } from '../type'
import BaseService from './base-service'

class DownloadService extends BaseService {
  download = async (requestConfig?: Partial<AppRequestConfig>) => {
    const url = requestConfig?.url || '';
    const timestamp = new Date().getTime()
    const newUrl = url + (url.indexOf('?') === -1 ? '?' : '&') + '_t=' + timestamp
    const mergedConfig: AppRequestConfig = {
      responseType: 'blob',
      ...requestConfig,
      url: newUrl
    };

    // TODO: 支持单个接口自定义的拦截器

    // 统一处理返回类型
    // const loading = ElLoading.service({
    //   lock: true,
    //   text: '导出中，请稍候...',
    //   background: 'rgba(255, 255, 255, 0.7)'
    // });
    try {
      const response: AxiosResponse<Blob, AppRequestConfig> = await this.instance.request<Blob>(mergedConfig)
      return this.responseHandler(response, mergedConfig.extraInfo ?? {} as any)
    } catch (err: any) {
      return { err, data: null, response: null }
    } finally {
      // loading.close();
    }
  };

  // 下载图片
  static downloadImage(imgSrc: string) {
    // 下载图片地址和图片名
    const image = new Image();
    const name = imgSrc && imgSrc.split('/').pop()
    // 解决跨域 Canvas 污染问题
    image.setAttribute('crossOrigin', 'anonymous')
    image.onload = function () {
      const canvas = document.createElement('canvas')
      canvas.width = image.width;
      canvas.height = image.height;
      const context = canvas.getContext('2d')
      if (!context) return;
      context.drawImage(image, 0, 0, image.width, image.height)
      const url = canvas.toDataURL('image/png')// 得到图片的base64编码数据
      const a = document.createElement('a'); // 生成一个a元素
      const event = new MouseEvent('click') // 创建一个单击事件
      a.download = name || 'photo' // 设置图片名称
      a.href = url // 将生成的URL设置为a.href属性
      a.dispatchEvent(event) // 触发a的单击事件
    };
    image.src = imgSrc
  }
}

export default DownloadService
