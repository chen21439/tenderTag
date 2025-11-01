<template>
  <div class="com-app-login">
    <div class="main">
      <div class="left">
        <img :src="loadThemeImg('pic.avif')" width="680" height="640" alt=""/>
        <div class="title">
          <img :src="loadThemeImg('logo.png')" width="24" height="24" alt=""/>
          <span>{{systemInfo.htmlTitle}}</span>
        </div>
      </div>
      <div class="right" :style="loginView.loginFormVisible ? '' : 'display:none'">
        <span class="zhdl">帐号登录</span>
        <a-form ref="loginFormRef" class="login-form" :model="loginView.loginForm" :rules="loginFormRules">
          <a-form-item ref="account" name="account">
            <a-input v-model:value="loginView.loginForm.account" placeholder="请输入账号" size="large" class="login-form-input" :maxlength="20">
              <template #prefix>
                <UserOutlined/>
              </template>
            </a-input>
          </a-form-item>
          <a-form-item ref="password" name="password">
            <a-input-password  v-model:value="loginView.loginForm.password"  placeholder="请输入密码" size="large" class="login-form-input"
            autocomplete :maxlength="20">
              <template #prefix>
                <LockOutlined/>
              </template>
            </a-input-password>
          </a-form-item>
          <a-form-item ref="captcha" name="captcha">
            <a-input v-model:value="loginView.loginForm.captcha" placeholder="验证码" size="large" class="login-form-input" :maxlength="20">
              <template #suffix>
                <img :src="loginView.loginForm.captchaUrl" width="140" height="40" alt="" @click="refreshCaptcha"/>
              </template>
            </a-input>
          </a-form-item>
          <div class="wjmm">
            <a-popover>
              <template #content>请联系管理员处理</template>
              忘记密码
            </a-popover>
          </div>
        </a-form>
        <a-checkbox v-model:checked="loginView.isRead" class="yuedu">
          <span class="t1">我已阅读并同意</span>
          <span class="t2" @click.stop="doLookDoc">用户协议、隐私政策</span>
        </a-checkbox>
        <a-button type="primary" class="btn" @click="doLogin">登录</a-button>
      </div>

      <!-- 登录成功 -->
      <div class="right right-success" :style="!loginView.loginFormVisible ? '' : 'display:none'">
        <img src="@/assets/images/common/me64.png">
        <div class="account">{{ loginView.loginForm.account }}</div>
        <div class="dlcg">登录成功</div>
      </div>
    </div>
  </div>

  <!-- 修改默认密码 -->
  <a-modal
v-model:open="loginView.passwordModalVisible" class="password-modal" title="" :closable="false" :footer="null" :width="400" :mask-closable="false"
           @ok="">
    <div class="title">
      <span class="text1">修改密码</span>
      <span class="text2">首次登录需要修改密码，密码不得小于6位数</span>
    </div>
    <a-form ref="passwordFormRef" class="form" :model="loginView.passwordForm" :rules="passwordFormRules">
      <a-form-item ref="password" name="password">
        <a-input-password
         autocomplete :maxlength="20"
v-model:value="loginView.passwordForm.password" placeholder="请输入新密码" size="large"
                          class="password-form-input"/>
      </a-form-item>
      <a-form-item ref="password2" name="password2">
        <a-input-password v-model:value="loginView.passwordForm.password2"  autocomplete :maxlength="20" placeholder="请再次输入" size="large" class="password-form-input"/>
      </a-form-item>
    </a-form>
    <a-button type="primary" class="btn" @click="doModifyPassword">保存</a-button>
  </a-modal>
  <context-holder/>
</template>

<script lang="ts" setup>
import type {Rule} from 'ant-design-vue/es/form'
import type {LoginView, PasswordForm,LoginForm, BosssoftCookie } from '@/typings/login'
import { ref, reactive, onMounted,computed } from 'vue'
import { v4 as uuid } from 'uuid'
import {message} from 'ant-design-vue'
import {useRouter} from 'vue-router'
import {UserOutlined, LockOutlined} from '@ant-design/icons-vue'
import {apiLogin, apiModifyPassword , verifyCodeUrl} from '@/api/login'
import { appLogin, getCookie } from '@/utils/app-gateway'
import  { useMenusStore } from '@/store'
import { loadThemeImg } from '@/hooks/use-theme'
defineOptions({
  name: 'Login'
})
const menusStore = useMenusStore()
// 系统信息
const systemInfo = computed(()=> menusStore.systemInfo)
const bosssoftCookie: BosssoftCookie = computed(()=>getCookie())
const router = useRouter()
const loginView = reactive<LoginView>({
  loginFormVisible: true,
  passwordModalVisible: false,
  loginForm: reactive<LoginForm>({
    account: '',
    password: '',
    captcha: '',
    captchaKey: '',
    captchaUrl: ''
  }),
  passwordForm: reactive<PasswordForm>({
    password: '',
    password2: ''
  }),
  isRead: false
})
const loginFormRef = ref()
const passwordFormRef = ref()

const loginFormRules: Record<string, Rule[]> = {
  account: [
    {required: true, message: '请输入账号'},
    {pattern: /^1[3-9]\d{9}$/, message: '手机号码格式有误，请修改'}
  ],
  password: [
    {required: true, message: '请输入密码'}
  ],
  captcha: [
    {required: true, message: '请输入验证码'}
  ]
}

const passwordFormRules: Record<string, Rule[]> = {
  password: [
    {required: true, message: '请输入密码'},
    {min: 6, message: '密码小于6位数'},
    {
      validator: function (rule, value, callback) {
        if (value == loginView.loginForm.password) {
          return Promise.reject('不能与初始密码一致')
        } else if (!(/\d/.test(value) && /[a-z]/.test(value) && /[A-Z]/.test(value))) {
          return Promise.reject('密码必须包含大写字母、小写字母和数字')
        } else {
          return Promise.resolve()
        }
      }
    }
  ],
  password2: [
    {required: true, message: '请再次输入密码'}
  ]
}
const [messageApi, contextHolder] = message.useMessage()

//修改密码
function doModifyPassword(e: any) {
  passwordFormRef.value.validate().then(async () => {
    if (loginView.passwordForm.password != loginView.passwordForm.password2) {
      messageApi.error('密码前后不一致')
      return
    }
    const { err, data } = await apiModifyPassword({
      uid: bosssoftCookie.value.userId,
      password: loginView.passwordForm.password
    })
    if(err) return
    loginView.passwordModalVisible = false
    messageApi.success('密码修改成功')
    goHome()
  })
}

//跳转到问答首页
function goHome() {
  router.push({name: 'Home'})
}

//登录
function doLogin(e: any) {
  loginFormRef.value.validate().then(() => {
    if (!loginView.isRead) {
      messageApi.info('请勾选【我已阅读并同意用户协议、隐私政策】')
      return
    }
    apiLogin({
      telephone: loginView.loginForm.account,
      password: loginView.loginForm.password,
      code: loginView.loginForm.captcha,
      key: loginView.loginForm.captchaKey,
    }).then((res)=> {
      const { err, data } = res
      if(err?.code == '4019'||err?.code == '4020' || err?.code == '4010') refreshCaptcha()
      if(err) return
      let expireTime = data.expireTime
      let bosssoftCookie: BosssoftCookie = {
        appId: data.appId,
        userId: data.uid,
        userName: data.userName,
        token: data.token,
        expireTime: expireTime,
        expireDateTime: new Date(data.expireDateTime)
      }
      appLogin(JSON.stringify(bosssoftCookie))
      //如果是默认密码，显示修改密码弹窗
      // if (data.defaultPassword == 1) {
      //   loginView.loginFormVisible = false
      //   loginView.passwordModalVisible = true
      // } else {
      //   loginView.loginFormVisible = false
      //   goHome()
      // }
    })
  })
}

//刷新验证码
function refreshCaptcha() {
  loginView.loginForm.captchaKey = uuid()
  loginView.loginForm.captchaUrl = verifyCodeUrl + loginView.loginForm.captchaKey
}

function doLookDoc() {
  const state = {
    account: loginView.loginForm.account,
    password: loginView.loginForm.password
  }
  router.push({path: '/agreement', state})
}

onMounted(() => {
  refreshCaptcha()
  loginView.loginForm.account = history?.state?.account ?? ''
  loginView.loginForm.password = history?.state?.password ?? ''
  loginView.isRead = history?.state?.isRead ?? false
})
</script>
<style lang="scss" scoped>
.com-app-login {
  width: 100vw;
  height: 100vh;
  min-width: 1080px;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-items: center;
  background: var(--login-bg) 100% no-repeat;
  background-size: cover;

  .main {
    display: flex;
    flex-direction: row;
    margin: 0 auto;
    box-shadow: 0px 16px 48px 0px rgba(19, 60, 232, 0.2);
    border-radius: var(--border-radius-16);

    .title {
      display: flex;
      flex-direction: row;
      position: absolute;
      left: 40px;
      top: 40px;
      gap: 8px;
    }

    .left {
      position: relative;
      width: 680px;
      height: 640px;

      img {
        border-radius: var(--border-radius-16) 0 0 var(--border-radius-16);
      }
    }

    .right {
      display: flex;
      align-items: center;
      flex-direction: column;
      width: 400px;
      height: 640px;
      border-radius: 0 var(--border-radius-16) var(--border-radius-16) 0;
      background: rgba(var(--fill-rbg-0), 0.2);
      box-shadow: 0px 6px 16px 0px rgb(19 60 232 / 10%);
      backdrop-filter: blur(10px);

      .zhdl {
        margin: 64px 0px;
        font-size: var(--font-28);
        font-weight: bold;
      }

      .login-form {
        width: 336px;
        height: 296px;

        .login-form-input {
          height: 64px;
          gap: 16px;
        }

        .wjmm {
          width: 336px;
          padding: 0 0 0 248px;
          font-size: var(--font-14);
          color: var(--text-4);
        }
      }

      .yuedu {
        height: 24px;
        margin-top: 24px;
        .t1 {
          font-size: var(--font-12);
          color: var(--text-4);
        }

        .t2 {
          margin-left: 8px;
          font-size: var(--font-12);
          color: var(--main-6);
        }
      }

      .yuedu-div {
        height: 24px;
        margin-top: 24px;
        display: flex;
        align-items: center;
        gap: 8px;

        .yuedu-div-t1 {
          font-size: var(--font-12);
          color: var(--text-4);
        }

        .yuedu-div-t2 {
          font-size: var(--font-12);
          color: var(--main-6);
        }
      }

      .btn {
        width: 336px;
        height: 48px;
        border-radius: var(--border-radius-8);
        font-size: var(--font-16);
        font-weight: bold;
        margin-top: 16px;
      }
    }

    .right-success {
      display: flex;
      flex-direction: column;
      align-items: center;

      img {
        margin-top: 200px;
      }

      .account {
        margin-top: 16px;
        font-family: Source Han Sans;
        font-size: var(--font-24);
        font-weight: bold;
        color: var(--fill-9);
      }

      .dlcg {
        margin-top: 32px;
        font-size: var(--font-28);
        font-weight: bold;
        color: var(--success-6);
      }
    }
  }
}

.password-modal {
  display: flex;

  .title {
    display: flex;
    flex-direction: column;
    align-items: center;

    .text1 {
      font-size: var(--font-28);
      font-weight: bold;
      color: var(--fill-9);
    }

    .text2 {
      font-size: var(--font-16);
    }
  }

  .form {
    margin: 48px 0;

    .password-form-input {
      height: 64px;
      gap: 8px;
    }
  }

  .btn {
    width: 336px;
    height: 48px;
    border-radius: var(--border-radius-8);
    font-size: var(--font-16);
    font-weight: bold;
  }
}

</style>
