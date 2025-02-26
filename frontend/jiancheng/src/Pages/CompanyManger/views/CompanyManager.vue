<template>
    <el-container>
        <el-header>
            <AllHeader></AllHeader>
        </el-header>
        <!--引用header-->
        <el-container>
            <el-aside
                ><!--引用aside-->
                <div>
                    <el-avatar :icon="UserFilled" :size="100" />
                </div>
                <div style="font-size: x-large">
                    {{ userName }}
                </div>
                <div class="aside-menu" style="width: 100%; margin-top: 50px">
                    <el-menu default-active="1" class="el-menu-vertical-demo">
                        <el-menu-item
                            index="1"
                            @click="handleMenuClick('CostCalcAndProfitAnalysis')"
                        >
                            <span>成本计算与盈利分析</span>
                        </el-menu-item>
                        <el-menu-item index="2" @click="handleMenuClick('OrderStatusMonitor')">
                            <span>订单状态监控</span>
                        </el-menu-item>
                        <el-menu-item
                            index="3"
                            @click="handleMenuClick('MaterialPricesAndCostTrends')"
                        >
                            <span>材料价格与成本趋势</span>
                        </el-menu-item>
                        <el-menu-item
                            index="4"
                            @click="handleMenuClick('FinancialStatusAndDepartmentalInput')"
                        >
                            <span>财务状态与部门输入</span>
                        </el-menu-item>
                        <el-menu-item index="5" @click="handleMenuClick('OrderConfirmation')">
                            <span>生产订单确认</span>
                        </el-menu-item>
                        <el-menu-item index="10" @click="handleMenuClick('OutboundProduct')">
                            <span>订单出库</span>
                        </el-menu-item>
                        <el-menu-item index="11" @click="handleMenuClick('PersonalInfo')">
                            <span>个人信息</span>
                        </el-menu-item>
                        <el-menu-item index="9" @click="logout">
                            <span>退出系统</span>
                        </el-menu-item>
                    </el-menu>
                </div>
            </el-aside>
            <el-main>
                <component :is="components[currentComponent]"></component>
            </el-main>
        </el-container>
    </el-container>
</template>

<script setup lang="js">
import AllHeader from '@/components/AllHeader.vue'
import { UserFilled } from '@element-plus/icons-vue'
import axios from 'axios'
import { ref, onMounted, getCurrentInstance } from 'vue'
import CostCalcAndProfitAnalysis from '../components/CostCalcAndProfitAnalysis/CostCalcAndProfitAnalysis.vue'
import OrderStatusMonitor from '../components/OrderStatusMonitor/OrderStatusMonitor.vue'
import MaterialPricesAndCostTrends from '../components/MaterialPricesAndCostTrends/MaterialPricesAndCostTrends.vue'
import FinancialStatusAndDepartmentalInput from '../components/FinancialStatusAndDepartmentalInput/FinancialStatusAndDepartmentalInput.vue'
import OrderConfirmation from '../components/OrderConfirmation/OrderConfirmation.vue'
import OutboundProduct from '@/Pages/TotalWarehouse/FinishedWarehouse/components/OutboundProduct.vue'
import useSetAxiosToken from '../hooks/useSetAxiosToken'
import PersonalInfo from '@/components/PersonalInfo.vue'
import { useRouter } from "vue-router";

const components = {
    CostCalcAndProfitAnalysis,
    OrderStatusMonitor,
    MaterialPricesAndCostTrends,
    FinancialStatusAndDepartmentalInput,
    OrderConfirmation,
    OutboundProduct,
    PersonalInfo
}
let currentComponent = ref('CostCalcAndProfitAnalysis')
let userName = ref('')
const { setAxiosToken } = useSetAxiosToken()
const $api_baseUrl = getCurrentInstance().appContext.config.globalProperties.$apiBaseUrl
const router = useRouter();

onMounted(() => {
    setAxiosToken()
    getUserAndCharacter()
    handleMenuClick('CostCalcAndProfitAnalysis')
})

// 接口预留，请求后台获取当前登录用户信息
async function getUserAndCharacter() {
    const response = await axios.get(`${$api_baseUrl}/general/getcurrentstaffandcharacter`)
    userName.value = response.data.staffName + '-' + response.data.characterName
}

// 菜单选项切换函数
function handleMenuClick(value) {
    currentComponent.value = value
}

// 退出登录
async function logout() {
    await axios.post(`${$api_baseUrl}/logout`)
    localStorage.removeItem('token')
    localStorage.removeItem('role')
    router.push('/login')
}
</script>
