import type { AxiosResponse } from 'axios';
import type { AppRequestConfig, Http } from '../type';
import BaseService from './base-service';

class HttpService extends BaseService {
  http: Http = async <T>(requestConfig?: Partial<AppRequestConfig>) => {
    const url = requestConfig?.url || '';
    const timestamp = new Date().getTime()
    const newUrl = url + (url.indexOf('?') === -1 ? '?' : '&') + '_t=' + timestamp
    const mergedConfig: AppRequestConfig = { ...requestConfig, url: newUrl }
    // TODO: 支持单个接口自定义的拦截器

    // 统一处理返回类型
    try {
      const response: AxiosResponse<T, AppRequestConfig> = await this.instance.request<T>(mergedConfig);
      return this.responseHandler(response);
    } catch (err: any) {
      return { err, data: null, response: null };
    }
  };
}

export default HttpService;
