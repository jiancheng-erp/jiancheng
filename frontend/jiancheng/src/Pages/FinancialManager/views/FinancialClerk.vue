<template>
    <el-container class="app-shell">
        <el-header class="app-header">
            <AllHeader />
        </el-header>

        <el-main class="app-main">
            <!-- 顶部用户信息栏 -->
            <div class="user-info">
                <em class="logout" @click="logout">退出登录</em>
                <span class="username">{{ userName }}</span>
                <el-avatar :icon="UserFilled" :size="30" />
            </div>

            <!-- 左侧标签页 -->
            <el-tabs tab-position="left" type="border-card" class="finance-tabs tabs-elegant">
                <el-tab-pane label="明细展示">
                    <FinancialDetailsDisplay />
                </el-tab-pane>

                <el-tab-pane label="入库待审核">
                    <InOutboundRecords />
                </el-tab-pane>

                <el-tab-pane label="入库明细">
                    <InboundDetails />
                </el-tab-pane>

                <el-tab-pane label="应收记录">
                    <FinancialRecievableDetail />
                </el-tab-pane>
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
import InOutboundRecords from '@/Pages/TotalWarehouse/HeadOfWarehouse/components/InOutboundRecords.vue'
import InboundDetails from '../components/FinancialWarehouseDetail.vue'
import FinancialPayableDetail from '../components/FinancialPayableDetail.vue'
import FinancialRecievableDetail from '../components/FinancialRecievableDetail.vue'
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
/* 使用 main.css 定义的主题变量 */
:root {
    --brand: #2193b0;
    --header-grad-a: #6dd5ed;
    --header-grad-b: #2193b0;
    --border-color: #e5e7eb;
    --shadow-soft: 0 6px 16px rgba(0, 0, 0, 0.08);
    --radius-lg: 12px;
}

.user-info {
    display: flex;
    justify-content: flex-end;
    align-items: center;
    gap: 12px;
    margin-bottom: 16px;
    padding: 8px 20px;
    background: #ffffff;
    border-radius: var(--radius-lg);
    box-shadow: var(--shadow-soft);
    transition: box-shadow 0.2s ease;
}

.user-info:hover {
    box-shadow: 0 8px 20px rgba(0, 0, 0, 0.08);
}

.logout {
    color: var(--brand);
    cursor: pointer;
    font-style: normal;
    font-weight: 500;
    transition: color 0.2s ease;
}
.logout:hover {
    color: color-mix(in srgb, var(--brand) 80%, black);
}

.username {
    font-weight: 600;
    color: #1e293b;
}


/* 高度自适应主内容 */
.app-main {
    background-color: #f5f7fa;
    padding: 24px;
}

</style>
