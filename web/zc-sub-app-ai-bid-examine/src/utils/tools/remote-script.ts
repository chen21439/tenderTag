
/**
 * 导入外部js/动态js
 * @param url 字符串
 */
export const remoteScript = (url: string) => {
  return new Promise((resolve, reject) => {
    const script = document.createElement('script');
    script.type = 'text/javascript'
    script.src = url
    script.onload = resolve
    script.onerror = reject
    document.body.appendChild(script)
  })
}
