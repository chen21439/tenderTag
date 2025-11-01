import { PROJECT_NAME } from '@/config';

export default class StorageService {
  /**
   * LocalStorage读取值
   * @param key key
   * @param defaultValue 缺省值
   * @returns value
   */
  static getLocal(key: string, defaultValue?: any) {
    let stored: any;
    try {
      stored = localStorage.getItem(generateItemKey(key));
      if (isJson(stored)) stored = JSON.parse(stored);
    } catch (err) {
      stored = null;
    }
    if (stored === null) {
      if (typeof defaultValue !== 'undefined') {
        stored = defaultValue;
      }
    }
    return stored;
  }

  /**
   * LocalStorage设置值
   * @param key key
   * @param value value
   */
  static setLocal(key: string, value: any) {
    if (typeof value !== 'undefined') {
      localStorage.setItem(generateItemKey(key), JSON.stringify(value));
    }
  }

  /**
   * LocalStorage清除值
   * @param key key
   */
  static removeLocal(key: string) {
    localStorage.removeItem(generateItemKey(key));
  }

  /**
   * LocalStorage全清空
   */
  static clearLocal() {
    localStorage.clear();
  }

  /**
   * SessionStorage读取值
   * @param key key
   * @param defaultValue 缺省值
   * @returns value
   */
  static getSession(key: string, defaultValue?: any) {
    let stored: any;
    try {
      stored = sessionStorage.getItem(generateItemKey(key));
      if (isJson(stored)) stored = JSON.parse(stored);
    } catch (err) {
      stored = null;
    }
    if (stored === null) {
      if (typeof defaultValue !== 'undefined') {
        stored = defaultValue;
      }
    }
    return stored;
  }

  /**
   * SessionStorage设置值
   * @param key key
   * @param value value
   */
  static setSession(key: string, value: any) {
    if (typeof value !== 'undefined') {
      sessionStorage.setItem(generateItemKey(key), JSON.stringify(value));
    }
  }

  /**
   * SessionStorage清除值
   * @param key key
   */
  static removeSession(key: string) {
    sessionStorage.removeItem(generateItemKey(key));
  }

  /**
   * SessionStorage全清空
   */
  static clearSession() {
    sessionStorage.clear();
  }

  /**
   * Cookie读取值
   * @param key key
   * @returns value
   */
  static getCookie(key: string) {
    const arr = document.cookie.split('; ');
    for (let i = 0; i < arr.length; i++) {
      const arr2 = arr[i].split('=');
      if (arr2[0] === generateItemKey(key)) {
        return arr2[1];
      }
    }
    return '';
  }

  /**
   * Cookie设置值
   * @param key key
   * @param value value
   * @param expires 过期时间(秒)
   */
  static setCookie(key: string, value: string, expires?: number) {
    let str = generateItemKey(key) + '=' + value;
    if (expires) {
      const date = new Date();
      date.setTime(date.getTime() + expires * 1000);
      str += ';expires=' + date + ';path=/';
    } else {
      str += ';path=/';
    }
    document.cookie = str;
  }

  /**
   * Cookie清除值
   * @param key key
   */
  static removeCookie(key: string) {
    StorageService.setCookie(generateItemKey(key), '', -86400);
  }

  /**
   * Cookie全清空
   */
  static clearCookie() {
    const keys = document.cookie.match(/[^ =;]+(?==)/g);
    if (keys) {
      for (let i = keys.length; i--;) {
        document.cookie = keys[i] + '=0;path=/;expires=' + new Date(0).toUTCString();
      }
    }
  }
}

function generateItemKey(key: string) {
  return PROJECT_NAME + '-' + key;
}

function isJson(value: string) {
  if (isNaN(Number(value))) {
    try {
      JSON.parse(value);
      return true;
    } catch (e) {
      return false;
    }
  }
  return false;
}
