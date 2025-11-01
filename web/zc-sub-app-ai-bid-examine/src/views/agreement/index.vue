<template>
  <div class="com-app-agreement">
    <div class="com-app-agreement-box">
      <span class="s1">阳光公采大模型用户协议</span>
      <span class="s2">
        欢迎您使用博思数采科技股份有限公司提供的阳光公采大模型（以下简称“本模型”）。在使用本模型之前，请仔细阅读并理解本用户协议。如果您对本协议的任何条款有异议，您应立即停止使用本模型。<br><br>
        1. 接受条款<br>
        &nbsp;&nbsp;您通过访问或使用本模型，即表示您同意遵守本协议的所有条款和条件。如果您不同意本协议的任何条款，请不要使用本模型。<br>
        2. 使用许可<br>
        &nbsp;&nbsp;博思数采科技股份有限公司授予您有限的、不可转让的、非独占的许可，以访问和使用阳光公采大模型，用于您的个人或商业用途。您不得以任何形式将本模型的许可转让给第三方。<br>
        3. 用户义务<br>
        &nbsp;&nbsp;您同意在使用本模型时遵守适用的法律法规，并承担因违反法律法规而产生的全部法律责任。您不得利用本模型进行任何违法或侵权行为，包括但不限于恶意攻击、盗取信息、破坏系统等行为。<br>
        4. 知识产权<br>
        &nbsp;&nbsp;本模型包含博思数采科技股份有限公司及其关联公司拥有的知识产权，包括但不限于专利、商标、版权等。未经博思数采科技股份有限公司书面许可，您不得以任何方式使用、复制、修改或传播本模型的任何部分。<br>
        5. 免责声明<br>
        &nbsp;&nbsp;本模型按“现状”提供，博思数采科技股份有限公司不对本模型的准确性、完整性、及时性或适用性做出任何明示或暗示的保证。您对使用本模型所产生的结果自行承担责任。<br>
        6. 责任限制<br>
        &nbsp;&nbsp;在法律允许的最大范围内，博思数采科技股份有限公司对因使用本模型而导致的任何直接、间接、附带、特殊或后果性损失不承担任何责任。<br>
        7. 协议修改<br>
        &nbsp;&nbsp;博思数采科技股份有限公司有权随时修改本用户协议的条款，修改后的协议条款将在本模型上公布，并于公布后生效。您继续使用本模型将视为您接受修改后的协议条款。<br>
        8. 法律适用<br>
        &nbsp;&nbsp;本用户协议的订立、生效、履行和解释均适用中华人民共和国法律。如发生与本协议相关的争议，双方应友好协商解决；协商不成的，任何一方均可向博思数采科技股份有限公司所在地的人民法院提起诉讼。<br>
      </span>
      <span class="s1">阳光公采大模型隐私政策</span>
      <span class="s2">
        1. 信息收集<br>
        &nbsp;&nbsp;在您使用阳光公采大模型时，我们可能会收集并存储您提供的个人信息，包括但不限于姓名、联系方式、公司名称等。我们收集这些信息的目的是为了向您提供更好的服务和支持。<br>
        2. 信息使用<br>
        &nbsp;&nbsp;我们会将您提供的个人信息用于以下用途：<br>
        提供、维护和改进阳光公采大模型的服务；<br>
        向您提供与您相关的信息、产品或服务；<br>
        解决您的问题、投诉或其他支持请求；<br>
        根据适用法律法规的要求履行义务。<br>
        3. 信息保护<br>
        &nbsp;&nbsp;我们将采取合理的安全措施保护您的个人信息免遭未经授权的访问、使用或泄露。我们承诺不会将您的个人信息转让给任何未经授权的第三方。<br>
        4. 信息披露<br>
        &nbsp;&nbsp;我们仅在以下情况下可能披露您的个人信息：<br>
        &nbsp;&bull;&nbsp;&nbsp;根据适用法律法规的要求；<br>
        &nbsp;&bull;&nbsp;&nbsp;根据司法或行政机关的要求；<br>
        &nbsp;&bull;&nbsp;&nbsp;为了保护博思数采科技股份有限公司及其用户的合法权益。<br>
        5. 隐私权更新<br>
        &nbsp;&nbsp;您可以随时通过与我们联系更新、更正或删除您的个人信息。我们将尽最大努力在合理范围内满足您的请求。<br>
        6. 隐私政策变更<br>
        &nbsp;&nbsp;我们有权随时修改本隐私政策的条款，修改后的政策将在本模型上公布，并于公布后生效。您继续使用本模型将视为您接受修改后的隐私政策。通过点击“同意”或继续使用阳光公采大模型，即表示您同意本隐私政策的条款和条件。如果您不同意本政策的任何条款，请停止使用本模型。
    </span>
    </div>
    <a-button type="primary" class="btn-yy" @click="doYiYue">我已阅读</a-button>
  </div>
</template>

<script setup lang="ts">
import {useRouter} from "vue-router";
defineOptions({
  name: 'Agreement'
})
const router = useRouter()

function doYiYue() {
  const state = {
    account: history?.state?.account,
    password: history?.state?.password,
    isRead: true
  }
  router.push({path: '/login', state})
}
</script>
<style lang="scss" scoped>
.com-app-agreement {
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  background: var(--login-bg) 100% no-repeat;
  background-size: cover;
  .com-app-agreement-box {
    margin-top: 32px;
    width: 1000px;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 32px;

    .s1 {
      height: 24px;
      font-weight: bold;
    }

    .s2 {
      font-family: Source Han Sans;
      font-size: var(--font-14);
      font-weight: normal;
      line-height: normal;
      text-align: justify;
      font-feature-settings: "kern" on;
    }
  }

  .btn-yy {
    margin-top: 32px;
    width: 96px;
    height: 40px;
    border-radius: var(--border-radius-8);
    margin-bottom: 200px;
  }
}

</style>
