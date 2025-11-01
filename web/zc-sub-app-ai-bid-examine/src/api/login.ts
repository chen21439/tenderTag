import config from '@/config'
import { http } from '@/services/http'
import { getCookie } from '@/utils/app-gateway'
/** 刷新验证码 */
export const verifyCodeUrl = config.api.baseUrl+ '/api/encrypt/public/v1/verifyCode?key='
/** 登录 */
export const apiLogin = (data: { telephone: string; password: string; code: string; key: string}) =>
http({
  url: '/api/login/v1/login',
  data,
  method: 'post'
})
/** 修改密码 */
export const apiModifyPassword = (data: { uid: string; password: string;}) =>
http({
  url: '/api/user/v1/modifyPassword',
  data,
  method: 'post'
})
/** 登出 */
export const apiLogout = (appId?: string) =>
http({
  url: `/api/login/v1/logout?uid=${getCookie()?.userId}&appId = ${appId}`,
  method: 'post'
})
/** 刷新token */
export const apiRefreshToken = () =>http({url: '/api/token/v1/refresh?uid=' + getCookie().userId, method: 'get'})
/** 获取授权的业务模块 */
export const getUserBusModuleCodes = () =>http({url: '/api/user/v1/busModuleCodes', method: 'get'})
/**
 * 保存用户投诉
 * @param params
 * @returns {*}
 */
export const saveComplaint = (data: {  content: string;}) =>
  http({
    url: '/api/baseChat/v1/saveComplaint',
    method: 'post',
    data
  })
/**
 * 生成token
 * @param params
 * @returns {*}
 */
export const generateToken = (params: any) => {
  const url = '/auth/v1/token/generate'
  const data = {
    appId: params.appId,
    userId: params.userId,
    username: params.username,
    orgName: params.orgName,
    orgCode: params.orgCode,
    sign: params.sign,
    areaCode: params.areaCode,
    roleCode: params.roleCode,
    jumpKey: params.jumpKey
  }
  return http({
    method: 'post',
    url: url,
    data: data
  })
}

/**
 * 单点登录
 */
export const saltConvert = (data: { salt:string }) => http({
  url: '/auth/v0/token/saltConvert',
  method: 'post',
  data
})
