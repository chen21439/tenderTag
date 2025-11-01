export * from './app-constants'
export * from './system-info'
const env = import.meta.env
// 基本配置
const baseConfig = {
  /* 网络请求相关配置 */
  api: {
    timeout: 60000, // 默认60秒超时
    commonHeaders: {
      // eslint-disable-next-line camelcase
      // version_code: 3.1
    }, // 公共请求头
    formatRequestFields: false, // 是否把请求字段中的蛇形命名法改为驼峰命名法
    formatResponseFields: false, // 是否把响应字段中的驼峰命名法改为蛇形命名法
    baseUrl: import.meta.env.VITE_APP_API_BASE_URL
  },
  /* 路由相关配置 */
  route: {
    robotList: ['ChatRobotIndex','ChatRobotFileReader'], // 内嵌页路由
    whiteList: ['/404', '/500', '/login','/agreement'],// 白名单
    currentSystemCode:'AI_Chat',
    codeMap: <Record<string,string>>{
      AI_Chat: 'ai-chat',
      AI_Bid: 'ai-bid',
      AI_Contract: 'ai-contract'
    }
  }, 
  /* 辅助开发的flag*/
  env,
  isDev:  env.VITE_ENV === 'dev',// 是否开发环境；
  isTest: env.VITE_ENV === 'test', // 是否测试环境；
  isProd: env.VITE_ENV === 'prod', // 是否是生产环境；
  isDemo: env.VITE_ENV === 'demo' // 是否是演示环境；
};


// localstorage key
export const LOCALSTORAGE_SIDEBARSTATUS = 'sidebarStatus'// 菜单是否展开
export const LOCALSTORAGE_APPID = 'appId' // 项目appid
export const PROJECT_NAME = 'bossAi'// 项目名称
export const LOCALSTORAGE_EXTERNALLOGINURL = 'externalUrl' // 外部跳转登录地址
const config: Record<string,any> = { ...baseConfig }

// 添加环境变量日志
console.log('🔧 环境配置初始化:', {
  VITE_ENV: env.VITE_ENV,
  isDev: config.isDev,
  isTest: config.isTest,
  isProd: config.isProd,
  isDemo: config.isDemo,
  baseUrl: config.api.baseUrl
})

export default config;
