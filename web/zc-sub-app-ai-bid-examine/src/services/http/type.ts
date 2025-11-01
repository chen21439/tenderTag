import type { AxiosError, AxiosRequestConfig, AxiosResponse } from 'axios';

// 定义返回结果的数据类型
export interface AppResponse<T = any> {
  data: T | null;
  err: AxiosError | null;
  response: AxiosResponse<T> | null;
}

// 重新定义AppRequestConfig，在AxiosRequestConfig基础上再加args等数据
export interface AppRequestConfig extends AxiosRequestConfig {
  args?: Record<string, any>;
  noErrorTip?: boolean;
  noSendingToken?: boolean;
  extraInfo?: any;
  // TODO: 新增支持单个接口自定义拦截器的字段
}

export interface MakeRequest {
  // 未定义请求DTO的情况；MakeRequest类型规定了输入为config，载荷泛型默认为any，输出为一个函数，函数输入为requestConfig，输出为包含载荷泛型的泛型
  <Payload = any>(config: AppRequestConfig): (requestConfig?: Partial<AppRequestConfig>) => Promise<AppResponse<Payload>>;

  // 定义data的情况；MakeRequest类型输出的函数的输入类型先从AppRequestConfig中去掉data的定义，再结合上新定义的data，其余不变
  <Payload, Data>(config: AppRequestConfig): (requestConfig: Partial<Omit<AppRequestConfig, 'data'>> & { data: Data }) => Promise<AppResponse<Payload>>;

  // 定义data和params的情况；依旧需要去掉再加上对应字段的定义，但由于参数队列的特性，data的类型可能未定义，因此增加判断
  <Payload, Data, Params>(
    config: AppRequestConfig
  ): (
    requestConfig: Partial<Omit<AppRequestConfig, 'data' | 'params'>> &
      (Data extends undefined ? { data?: undefined } : { data: Data }) & {
        params: Params;
      }
  ) => Promise<AppResponse<Payload>>;

  // 定义data和params、args的情况；操作同上
  <Payload, Data, Params, Args>(
    config: AppRequestConfig
  ): (
    requestConfig: Partial<Omit<AppRequestConfig, 'data' | 'params' | 'args'>> &
      (Data extends undefined ? { data?: undefined } : { data: Data }) &
      (Params extends undefined ? { params?: undefined } : { params: Params }) & {
        args: Args;
      }
  ) => Promise<AppResponse<Payload>>;
}

export interface Http {
  <Payload = any>(requestConfig?: Partial<AppRequestConfig>): Promise<AppResponse<Payload>>;

  <Payload, Data>(requestConfig: Partial<Omit<AppRequestConfig, 'data'>> & { data: Data }): Promise<AppResponse<Payload>>;

  <Payload, Data, Params>(
    requestConfig: Partial<Omit<AppRequestConfig, 'data' | 'params'>> &
      (Data extends undefined ? { data?: undefined } : { data: Data }) & {
        params: Params;
      }
  ): Promise<AppResponse<Payload>>;

  <Payload, Data, Params, Args>(
    requestConfig: Partial<Omit<AppRequestConfig, 'data' | 'params' | 'args'>> &
      (Data extends undefined ? { data?: undefined } : { data: Data }) &
      (Params extends undefined ? { params?: undefined } : { params: Params }) & {
        args: Args;
      }
  ): Promise<AppResponse<Payload>>;
}
