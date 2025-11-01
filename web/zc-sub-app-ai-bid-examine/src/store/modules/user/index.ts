import { defineStore } from 'pinia'
import type { UserState } from './helper'
import { defaultSetting, getLocalState, setLocalState } from './helper'
import type { UserInfo } from '@/typings/user'

export const useUserStore = defineStore('user-store', {
  state: (): UserState => getLocalState(),
  actions: {
    updateUserInfo(userInfo: UserInfo) {
      this.userInfo = userInfo
      this.recordState()
    },

    resetUserInfo() {
      this.userInfo = { ...defaultSetting().userInfo }
      this.recordState()
    },

    recordState() {
      setLocalState(this.$state)
    }
  }
})
