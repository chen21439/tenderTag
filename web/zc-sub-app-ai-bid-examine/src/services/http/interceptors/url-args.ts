import type { AxiosRequestConfig } from 'axios';
import type { AppRequestConfig } from '../type';

const urlArgsHandler = {
  request: {
    onFulfilled: (config: AxiosRequestConfig) => {
      const { url, args } = config as AppRequestConfig;
      // 检查config中是否有args属性，没有则跳过以下代码逻辑
      if (args) {
        const lostParams: string[] = [];
        // 使用String.prototype.replace和正则表达式进行匹配替换
        const replacedUrl = (url as string).replace(/\{([^}]+)\}/g, (res, arg: string) => {
          if (!args[arg]) {
            lostParams.push(arg);
          }
          return args[arg] as string;
        });
        // 如果url存在未替换的路径参数，则会直接报错
        if (lostParams.length) {
          return Promise.reject(new Error('在args中找不到对应的路径参数'));
        }
        return { ...config, url: replacedUrl };
      }
      return config;
    }
  }
};

export default urlArgsHandler;
