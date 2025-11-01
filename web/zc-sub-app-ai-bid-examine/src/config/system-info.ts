// 个性化配置常量
import antTheme from './ant-theme'
export const SystemInfo: Record<string,any> = {
  default: {
    htmlTitle: '合规审查系统',
    htmlLogo: `${import.meta.env.VITE_APP_PUBLIC_URL}/logo.png`,
    title: 'Hi，我是数采小招',
    footerVersion: '内容由大模型生成，不代表我们的态度或观点',
    footerVersionSub: '',
    answerTip: '由阳光公采大模型生成',
    antTheme:{
      token: {
        ...antTheme.default
      }
    }
  }
}
