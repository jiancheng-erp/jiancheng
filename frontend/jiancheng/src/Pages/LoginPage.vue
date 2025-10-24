<template>
  <div class="login-page">
    <div class="login-form-container">
      <div class="brand">
        <h1 class="brand-title">XXXXX集团鞋业有限公司</h1>
        <p class="brand-subtitle">ERP 系统</p>
      </div>

      <el-form
        :model="loginForm"
        ref="loginFormRef"
        :rules="rules"
        class="login-form"
        @keyup.enter="handleSubmit"
      >
        <el-form-item prop="username" class="form-item">
          <el-input
            v-model="loginForm.username"
            autocomplete="off"
            placeholder="用户名"
            :prefix-icon="Avatar"
            class="input-large"
          />
        </el-form-item>

        <el-form-item prop="password" class="form-item">
          <el-input
            type="password"
            v-model="loginForm.password"
            autocomplete="off"
            placeholder="密码"
            :prefix-icon="Lock"
            class="input-large"
          />
        </el-form-item>

        <el-button type="primary" @click="handleSubmit" class="button-large">
          登录
        </el-button>
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { getCurrentInstance, reactive, ref } from 'vue'
import { Avatar, Lock } from '@element-plus/icons-vue'
import axios from 'axios'
import CryptoJS from 'crypto-js'
import { ElLoading, ElMessageBox } from 'element-plus'

const loginForm = reactive({ username: '', password: '' })
const rules = reactive({
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
})
const loginFormRef = ref(null)

const secretKey = '6f8e6f9178b12c08dce94bcf57b8df22'
const proxy = getCurrentInstance()
const apiBaseUrl = proxy.appContext.config.globalProperties.$apiBaseUrl

const handleSubmit = () => {
  loginFormRef.value.validate((valid) => {
    if (!valid) return
    const iv = CryptoJS.lib.WordArray.random(16)
    const encryptedPassword = CryptoJS.AES.encrypt(
      loginForm.password,
      CryptoJS.enc.Utf8.parse(secretKey),
      { iv, mode: CryptoJS.mode.CBC, padding: CryptoJS.pad.Pkcs7 }
    ).toString()
    const ivBase64 = CryptoJS.enc.Base64.stringify(iv)

    const loginData = { username: loginForm.username, password: encryptedPassword, iv: ivBase64 }
    const loading = ElLoading.service({ lock: true, text: '正在登录...', background: 'rgba(0,0,0,0.7)' })

    axios.post(`${apiBaseUrl}/login`, loginData)
      .then((response) => {
        const token = response.data.access_token
        localStorage.setItem('token', token)
        localStorage.setItem('role', response.data.role)
        localStorage.setItem('staffid', response.data.staffid)

        const r = response.data.role
        if (r === 14) window.location.href = '/humanresourcesdepartment'
        else if (r === 3) window.location.href = 'productionmanager'
        else if (r === 4) window.location.href = 'businessmanager'
        else if (r === 5) window.location.href = 'technicalmanager'
        else if (r === 6) window.location.href = 'productiongeneral'
        else if (r === 7) window.location.href = 'developmentmanager'
        else if (r === 8) window.location.href = 'headofwarehouse'
        else if (r === 9) window.location.href = 'logistics'
        else if (r === 10) window.location.href = 'financialManager'
        else if (r === 11) window.location.href = 'fabriccutting'
        else if (r === 12) window.location.href = 'sewingmachine'
        else if (r === 13) window.location.href = 'molding'
        else if (r === 17) window.location.href = 'technicalclerk'
        else if (r === 18) window.location.href = 'usagecalculation'
        else if (r === 19) window.location.href = 'semifinishedwarehouse'
        else if (r === 20) window.location.href = 'finishedwarehouse'
        else if (r === 2)  window.location.href = 'companymanager'
        else if (r === 21) window.location.href = 'businessmanager'
        else if (r === 22) window.location.href = 'productionclerk'
        else if (r === 23) window.location.href = 'warehouseclerk'
        else if (r === 24) window.location.href = 'financialclerk'
        else if (r === 1)  window.location.href = 'administrator'
        else if (r === 25) window.location.href = 'laborcostreportclerk'

        loading.close()
      })
      .catch(() => {
        ElMessageBox.alert('登录失败，请检查用户名和密码', '错误', {
          confirmButtonText: '确定',
          type: 'error'
        })
        loading.close()
      })
  })
}
</script>

<style scoped>
/* 兜底主题变量（若全局 main.css 已定义将被覆盖） */
:root {
  --header-grad-a: #6dd5ed;
  --header-grad-b: #2193b0;
  --brand: #2193b0;
  --border-color: #e5e7eb;
  --radius-lg: 14px;
  --radius-xl: 16px;
  --shadow: 0 10px 30px rgba(0, 0, 0, 0.12);
  --shadow-soft: 0 6px 16px rgba(0, 0, 0, 0.08);
}

/* 全屏背景 + 居中布局（浅色主调） */
.login-page {
  min-height: 100vh;
  width: 100%;
  display: grid;
  place-items: center;
  padding: 24px;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.92), rgba(255, 255, 255, 0.92)),
    url('../assets/background.jpg') center/cover fixed;
}

/* 登录卡片（更稳重的留白与圆角） */
.login-form-container {
  width: min(92vw, 460px);
  background: #ffffffee;
  backdrop-filter: saturate(110%) blur(4px);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow);
  padding: 28px 28px 26px;
  animation: fadeUp .28s ease;
}

/* 品牌头部 */
.brand {
  display: grid;
  place-items: center;
  gap: 6px;
  margin-bottom: 14px;
}
.logo {
  width: 54px; height: 54px;
  border-radius: 12px;
  background: linear-gradient(145deg, var(--header-grad-a), var(--header-grad-b));
  box-shadow: 0 8px 18px rgba(33,147,176,.25);
}
.brand-title {
  margin: 0;
  font-size: 20px;
  font-weight: 800;
  color: #0f172a;
  letter-spacing: .3px;
}
.brand-subtitle {
  margin: -2px 0 2px;
  font-size: 13px;
  color: #64748b;
  font-weight: 600;
}

/* 表单布局 */
.login-form {
  display: grid;
  gap: 14px;
  margin-top: 4px;
}
.form-item { margin-bottom: 0; }

/* 输入框（更易点按） */
.input-large :deep(.el-input__wrapper) {
  height: 48px;
  border-radius: 12px;
  box-shadow: 0 0 0 1px var(--border-color) inset;
  background-color: #fff;
  transition: box-shadow .18s ease, background-color .18s ease;
}
.input-large :deep(.el-input__inner) { font-size: 14px; }
.input-large :deep(.el-input__prefix) { margin-right: 4px; }
.input-large :deep(.el-input__wrapper.is-focus),
.input-large :deep(.is-focus .el-input__wrapper) {
  box-shadow: 0 0 0 2px color-mix(in srgb, var(--brand) 28%, transparent) !important;
}

/* 登录按钮（通栏 + 品牌渐变） */
.button-large {
  height: 48px;
  width: 100%;
  border-radius: 12px;
  background: linear-gradient(90deg, var(--header-grad-a), var(--header-grad-b));
  border: none;
  font-weight: 800;
  letter-spacing: .4px;
  color: #fff;
  box-shadow: 0 8px 18px rgba(33,147,176,.25);
  transition: transform .12s ease, box-shadow .2s ease, filter .2s ease;
}
.button-large:hover {
  transform: translateY(-1px);
  filter: brightness(1.02);
  box-shadow: 0 12px 24px rgba(33,147,176,.32);
}
.button-large:active {
  transform: translateY(0);
  filter: brightness(.98);
}

/* 小屏优化 */
@media (max-width: 420px) {
  .login-form-container { width: 94vw; padding: 22px 18px 18px; border-radius: var(--radius-lg); }
  .brand-title { font-size: 18px; }
  .input-large :deep(.el-input__wrapper), .button-large { height: 46px; border-radius: 10px; }
}

/* 微动画 */
@keyframes fadeUp {
  from { opacity: 0; transform: translateY(6px); }
  to   { opacity: 1; transform: translateY(0); }
}
</style>
