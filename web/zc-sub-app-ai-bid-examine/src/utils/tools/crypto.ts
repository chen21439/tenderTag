import { enc, AES, mode, pad } from 'crypto-js';

/**
 * 字符串转base64
 * @param str 字符串
 */
export const stringToBase64 = (str: string) => {
  // 对字符串进行编码
  const encode = encodeURI(str);
  // 对编码的字符串转化base64
  const base64 = btoa(encode);
  return base64;
};

/**
 * AES解密
 * @param url 拿来获取key和iv
 * @param text 加解密内容
 * **/
export const cryptoDecrypt = (url: string, text: string) => {
  if (typeof url !== 'string') return;
  const str = stringToBase64(url).repeat(3);
  const orgKey = str.slice(0, 16);
  const orgIv = str.slice(12, 28);

  const iKey = enc.Utf8.parse(orgKey);
  const iiv = enc.Utf8.parse(orgIv);
  const decrypted = AES.decrypt(text, iKey, {
    iv: iiv,
    mode: mode.CBC,
    padding: pad.Pkcs7
  });
  return decrypted.toString(enc.Utf8);
};
