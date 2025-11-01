export interface ModelType {
  password: string
  account: string
}

export interface UserInfo {
  id?: bigint // 用户id
  username: string // 用户昵称
  avatar: string // 用户头像
  account?: string // 用户账号
  status?: number // 账号状态 0正常 1：禁止登录
  userLevel?: string // 用户等级
  gptApiTokenVo?: gptApiTokenVo
}

export interface gptApiTokenVo {
  balance: string
  balanceStr: string
  visitNumber: number
}
