
/**
 * 登录页面
 * loginFormVisible
 */
export interface  LoginView {
  loginFormVisible: boolean,
  passwordModalVisible: boolean,
  loginForm: LoginForm,
  passwordForm: PasswordForm,
  isRead: boolean
}

export interface  LoginForm {
  account: string;
  password: string;
  captcha: string;
  captchaKey: string;
  captchaUrl: string;
}

export interface  PasswordForm {
  password: string;
  password2: string;
}

export interface  BosssoftCookie {
  appId: string | number;
  userId: string,
  userName: string,
  token: string,
  expireTime: number,
  expireDateTime: Date,
}
