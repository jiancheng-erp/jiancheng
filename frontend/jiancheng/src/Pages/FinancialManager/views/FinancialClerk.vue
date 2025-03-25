<template>
    <el-container>
        <el-header>
            <AllHeader></AllHeader>
        </el-header>
        <!--引用header-->
        <el-main>
            <div class="userInfo" style="display: flex;justify-content: end;align-items: center;right: 50px;position: relative;">
                <em style="margin-right: 20px;color: dodgerblue;cursor: pointer;" @click="logout">退出登录</em>
                <span>{{ userName }}</span>
                <el-avatar :icon="UserFilled" :size="30" />
            </div>
            <el-tabs tab-position="left" style="height: 700px" class="demo-tabs" type="border-card">
                <el-tab-pane label="明细展示"><FinancialDetailsDisplay /></el-tab-pane>
                <el-tab-pane label="入库待审核"><InboundRecords /></el-tab-pane>
            </el-tabs>
        </el-main>
    </el-container>
</template>

<script setup lang="js">
import AllHeader from '@/components/AllHeader.vue'
import { UserFilled } from '@element-plus/icons-vue'
import axios from 'axios'
import { ref, onMounted, getCurrentInstance } from 'vue'

// import FinancialDetailsDisplay from '../components/FinancialDetailsDisplay.vue'
import InboundRecords from '@/Pages/TotalWarehouse/HeadOfWarehouse/components/InboundRecords.vue'
import useSetAxiosToken from '../hooks/useSetAxiosToken'
import { useRouter } from 'vue-router'

let userName = ref('财务部-审核')
const { setAxiosToken } = useSetAxiosToken()
const $api_baseUrl = getCurrentInstance().appContext.config.globalProperties.$apiBaseUrl
const router = useRouter()

onMounted(() => {
    setAxiosToken()
    getUserAndCharacter()
})

// 接口预留，请求后台获取当前登录用户信息
async function getUserAndCharacter() {
    const response = await axios.get(`${$api_baseUrl}/general/getcurrentstaffandcharacter`)
    userName.value = response.data.staffName + '-' + response.data.characterName
}

// 菜单选项切换函数
function handleMenuClick(value) {
    // currentComponent.value = value
}

// 退出登录
async function logout() {
    await axios.post(`${$api_baseUrl}/logout`)
    localStorage.removeItem('token')
    localStorage.removeItem('role')
    router.push('/login')
}
</script>
<style scoped>
.demo-tabs > .el-tabs__content {
    padding: 32px;
    color: #6b778c;
    font-size: 32px;
    font-weight: 600;
}

.el-tabs--right .el-tabs__content,
.el-tabs--left .el-tabs__content {
    height: 100%;
}
.demo-tabs > .el-tabs__item{
  margin-right: 50px;
}
</style>
