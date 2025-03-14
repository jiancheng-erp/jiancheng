<template>
    <div class="login-form-container">
        <h1>浙江健诚集团鞋业有限公司ERP系统</h1>
        <h2>(Version 0.1)</h2>
        <el-form :model="loginForm" ref="loginFormRef" :rules="rules" class="login-form" @keyup.enter="handleSubmit" >
            <el-form-item prop="username">
                <el-input
                    v-model="loginForm.username"
                    autocomplete="off"
                    placeholder="用户名"
                    :prefix-icon="Avatar"
                    class="input-large"
                ></el-input>
            </el-form-item>
            <el-form-item prop="password">
                <el-input
                    type="password"
                    v-model="loginForm.password"
                    autocomplete="off"
                    placeholder="密码"
                    :prefix-icon="Lock"
                    class="input-large"
                ></el-input>
            </el-form-item>
            <el-button type="primary" @click="handleSubmit" class="button-large">登录</el-button>
        </el-form>
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

const secretKey = '6f8e6f9178b12c08dce94bcf57b8df22' // The secret key you generated
const proxy = getCurrentInstance()
const apiBaseUrl = proxy.appContext.config.globalProperties.$apiBaseUrl

const handleSubmit = () => {

    loginFormRef.value.validate((valid) => {
        if (valid) {
            // Generate random IV
            const iv = CryptoJS.lib.WordArray.random(16)

            // Encrypt the password with CBC mode and the random IV
            const encryptedPassword = CryptoJS.AES.encrypt(
                loginForm.password,
                CryptoJS.enc.Utf8.parse(secretKey),
                {
                    iv: iv,
                    mode: CryptoJS.mode.CBC,
                    padding: CryptoJS.pad.Pkcs7
                }
            ).toString()

            // Convert IV to Base64 to send with the request
            const ivBase64 = CryptoJS.enc.Base64.stringify(iv)
            console.log(ivBase64)
            const loginData = {
                username: loginForm.username,
                password: encryptedPassword, // Encrypted password
                iv: ivBase64 // IV sent as part of the payload
            }
            const loading = ElLoading.service({
                lock: true,
                text: '正在登录...',
                background: 'rgba(0, 0, 0, 0.7)'
            })
            console.log(apiBaseUrl)
            // Make the request to the backend
            axios
                .post(`${apiBaseUrl}/login`, loginData)
                .then((response) => {
                    const token = response.data.access_token
                    // Store the token in localStorage
                    localStorage.setItem('token', token)
                    localStorage.setItem('role', response.data.role)
                    localStorage.setItem('staffid', response.data.staffid)
                    console.log('Login successful!', response.data)
                    if (response.data.role === 14) {
                        window.location.href = '/humanresourcesdepartment'
                    } else if (response.data.role === 3) {
                        window.location.href = 'productionmanager'
                    } else if (response.data.role === 4) {
                        window.location.href = 'businessmanager'
                    } else if (response.data.role === 5) {
                        window.location.href = 'technicalmanager'
                    } else if (response.data.role === 6) {
                        window.location.href = 'productiongeneral'
                    } else if (response.data.role === 7) {
                        window.location.href = 'developmentmanager'
                    } else if (response.data.role === 8) {
                        window.location.href = 'headofwarehouse'
                    } else if (response.data.role === 9) {
                        window.location.href = 'logistics'
                    } 
                    else if (response.data.role === 10) {
                        window.location.href = 'financialManager'
                    }
                    else if (response.data.role === 11) {
                        window.location.href = 'fabriccutting'
                    } else if (response.data.role === 12) {
                        window.location.href = 'sewingmachine'
                    } else if (response.data.role === 13) {
                        window.location.href = 'molding'
                    } else if (response.data.role === 17) {
                        window.location.href = 'technicalclerk'
                    } else if (response.data.role === 18) {
                        window.location.href = 'usagecalculation'
                    } else if (response.data.role === 19) {
                        window.location.href = 'semifinishedwarehouse'
                    } else if (response.data.role === 20) {
                        window.location.href = 'finishedwarehouse'
                    } else if (response.data.role === 2) {
                        window.location.href = 'companymanager'
                    } else if (response.data.role === 21) {
                        window.location.href = 'businessmanager'
                    } else if (response.data.role === 22) {
                        window.location.href = 'productionclerk'
                    } else if (response.data.role === 23) {
                        window.location.href = 'warehouseclerk'
                    } else {
                        console.log('Invalid role!')
                    }
                    loading.close()
                })
                .catch((error) => {
                    ElMessageBox.alert('登录失败，请检查用户名和密码', '错误', {
                        confirmButtonText: '确定',
                        type: 'error'
                    })
                    
                    console.log('Login failed!')
                    loading.close()
                })
        } else {
            console.log('Validation error!')
            return false
        }
    })
}
</script>

<style scoped>
.login-form-container {
    width: 50vw;
    max-width: 800px;
    min-width: 300px;
    margin: 25vh auto;
    padding: 5vh 2vw;
    border: 1px solid #dcdcdc;
    border-radius: 4px;
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
    text-align: center;
    background-color: #fff;
}

.login-form-container h1 {
    margin-bottom: 3vh;
    font-size: 3vh;
}

.login-form {
    display: flex;
    flex-direction: column;
    align-items: center;
    width: 100%;
}
</style>
