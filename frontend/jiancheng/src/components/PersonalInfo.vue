<template>
    <el-row :gutter="20">
        <el-col :span="24" :offset="0" style="font-size: xx-large; text-align: center">
            个人信息
        </el-col>
    </el-row>
    <el-row :gutter="20" style="margin-top: 20px">
        <el-col :span="12" :offset="6">
            <el-form :model="passwordForm" :rules="rules" ref="passwordForm" label-width="120px">
                <el-form-item label="当前密码" prop="currentPassword">
                    <el-input
                        v-model="passwordForm.currentPassword"
                        type="password"
                        placeholder="请输入当前密码"
                    ></el-input>
                </el-form-item>
                <el-form-item label="新密码" prop="newPassword">
                    <el-input
                        v-model="passwordForm.newPassword"
                        type="password"
                        placeholder="请输入新密码"
                    ></el-input>
                </el-form-item>
                <el-form-item label="确认新密码" prop="confirmPassword">
                    <el-input
                        v-model="passwordForm.confirmPassword"
                        type="password"
                        placeholder="请再次输入新密码"
                    ></el-input>
                </el-form-item>
                <el-form-item>
                    <el-button type="primary" @click="submitPasswordChange">提交</el-button>
                    <el-button @click="resetForm">重置</el-button>
                </el-form-item>
            </el-form>
        </el-col>
    </el-row>
</template>

<script>
import axios from 'axios'
import CryptoJS from 'crypto-js'
export default {
    data() {
        return {
            passwordForm: {
                currentPassword: '',
                newPassword: '',
                confirmPassword: ''
            },
            rules: {
                currentPassword: [{ required: true, message: '请输入当前密码', trigger: 'blur' }],
                newPassword: [
                    { required: true, message: '请输入新密码', trigger: 'blur' },
                    { min: 4, message: '密码长度至少4位', trigger: 'blur' }
                ],
                confirmPassword: [
                    {
                        required: true,
                        message: '请确认新密码',
                        trigger: 'blur'
                    },
                    {
                        validator: (rule, value, callback) => {
                            if (value !== this.passwordForm.newPassword) {
                                callback(new Error('两次输入的密码不一致'))
                            } else {
                                callback()
                            }
                        },
                        trigger: 'blur'
                    }
                ]
            }
        }
    },
    methods: {
        async submitPasswordChange() {
            const staffId = localStorage.getItem('staffid') // Get the staff ID from local storage
            const secretKey = '6f8e6f9178b12c08dce94bcf57b8df22' // The secret key you generated
            this.$refs.passwordForm.validate(async (valid) => {
                if (valid) {
                    try {
                        const iv = CryptoJS.lib.WordArray.random(16)
                        const ivBase64 = CryptoJS.enc.Base64.stringify(iv); // Base64 encode the IV
                        console.log('iv:', iv.toString())

                        // Encrypt the password with CBC mode and the random IV
                        const encryptedCurrentPassword = CryptoJS.AES.encrypt(
                            this.passwordForm.currentPassword,
                            CryptoJS.enc.Utf8.parse(secretKey),
                            {
                                iv: iv,
                                mode: CryptoJS.mode.CBC,
                                padding: CryptoJS.pad.Pkcs7
                            }
                        ).toString()
                        const encryptedNewPassword = CryptoJS.AES.encrypt(
                            this.passwordForm.newPassword,
                            CryptoJS.enc.Utf8.parse(secretKey),
                            {
                                iv: iv,
                                mode: CryptoJS.mode.CBC,
                                padding: CryptoJS.pad.Pkcs7
                            }
                        ).toString()
                        await axios.post(
                            `${this.$apiBaseUrl}/user/changepassword`,
                            {
                                currentPassword: encryptedCurrentPassword,
                                newPassword: encryptedNewPassword,
                                iv: ivBase64,
                                staffId: staffId
                            }
                        )
                        this.$message.success('密码修改成功')
                        this.resetForm()
                        this.$router.push('/login')
                    } catch (error) {
                        this.$message.error('修改失败，请检查当前密码或稍后再试')
                        console.error('Error updating password:', error)
                    }
                }
            })
        },
        resetForm() {
            this.$refs.passwordForm.resetFields()
        }
    }
}
</script>

<style scoped>
/* Optional custom styles */
</style>
