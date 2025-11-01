import StorageService from '@/utils/storage'
import type { UserInfo } from '@/typings/user'

const LOCAL_NAME = 'userStorage'

export interface UserState {
  userInfo: UserInfo
}

export function defaultSetting(): UserState {
  return {
    userInfo: {
      avatar: '',
      username: '助手-博思软件'
    }
  }
}

export function getLocalState(): UserState {
  const localSetting: UserState | undefined = StorageService.getLocal(LOCAL_NAME)
  return { ...defaultSetting(), ...localSetting }
}

export function setLocalState(setting: UserState): void {
  StorageService.setLocale(LOCAL_NAME, setting)
}
