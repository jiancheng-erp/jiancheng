<template>
    <div class="login-form-container">
        <h1>健诚集团ERP</h1>
        <el-form :model="loginForm" ref="loginFormRef" :rules="rules" class="login-form">
            <el-form-item prop="username">
                <el-input v-model="loginForm.username" autocomplete="off" placeholder="用户名" :prefix-icon="Avatar" class="input-large"></el-input>
            </el-form-item>
            <el-form-item prop="password">
                <el-input type="password" v-model="loginForm.password" autocomplete="off" placeholder="密码" :prefix-icon="Lock" class="input-large"></el-input>
            </el-form-item>
            <el-button type="primary" @click="handleSubmit" class="button-large">登录</el-button>
        </el-form>
    </div>
</template>

<script setup>
import { reactive, ref } from 'vue';
import { Avatar, Lock } from '@element-plus/icons-vue';

const loginForm = reactive({ username: '', password: '' });
const rules = reactive({
    username: [
        { required: true, message: '请输入用户名', trigger: 'blur' }
    ],
    password: [
        { required: true, message: '请输入密码', trigger: 'blur' }
    ]
});
const loginFormRef = ref(null);
const handleSubmit = () => {
    loginFormRef.value.validate((valid) => {
        if (valid) {
            console.log('Submit!', loginForm);
        } else {
            console.log('Error!');
            return false;
        }
    });
};
</script>

<style scoped>
.login-form-container {
    width: 50vw;
    max-width: 500px;
    min-width: 300px;
    margin: 10vh auto;
    padding: 5vh 2vw;
    border: 1px solid #dcdcdc;
    border-radius: 4px;
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
    text-align: center;
}

.login-form-container h1 {
    margin-bottom: 3vh;
    font-size: 5vh;
}

.login-form {
    display: flex;
    flex-direction: column;
    align-items: center;
    width: 100%;
}

</style>
