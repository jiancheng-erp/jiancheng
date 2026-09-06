<template>
    <el-container class="app-shell">
        <!-- 顶部栏 -->
        <el-header class="app-header">
            <AllHeader />
        </el-header>

        <el-container class="app-body">
            <!-- 侧栏 -->
            <el-aside class="app-aside">
                <div class="aside-brand">
                    <div class="aside-brand-badge"><el-icon><Menu /></el-icon></div>
                    <div class="aside-brand-text">
                        <span class="aside-brand-title">功能导航</span>
                        <span class="aside-brand-sub">公司管理</span>
                    </div>
                </div>

                <!-- 菜单（内部滚动） -->
                <el-menu :default-active="activeIndex" class="app-menu" :unique-opened="true">
                    <el-menu-item index="0" @click="handleMenuClick('MainBoardPage', '0')">
                        <el-icon><DataBoard /></el-icon>
                        <span>主页看板</span>
                    </el-menu-item>

                    <el-menu-item index="1" @click="handleMenuClick('CostCalcAndProfitAnalysis', '1')">
                        <el-icon><DataAnalysis /></el-icon>
                        <span>成本计算与盈利分析</span>
                    </el-menu-item>

                    <el-menu-item index="2" @click="handleMenuClick('OrderImportantStatus', '2')">
                        <el-icon><Monitor /></el-icon>
                        <span>订单关键节点监控</span>
                    </el-menu-item>

                    <el-menu-item index="17" @click="handleMenuClick('OrderProgress', '17')">
                        <el-icon><Odometer /></el-icon>
                        <span>订单生产进度</span>
                    </el-menu-item>

                    <el-menu-item index="6" @click="handleMenuClick('RevertEventAnalyse', '6')">
                        <el-icon><Refresh /></el-icon>
                        <span>退回情况记录统计</span>
                    </el-menu-item>

                    <el-menu-item index="3" @click="handleMenuClick('MaterialPricesAndCostTrends', '3')">
                        <el-icon><TrendCharts /></el-icon>
                        <span>材料价格与成本趋势</span>
                    </el-menu-item>

                    <el-menu-item index="4" @click="handleMenuClick('FinancialStatusAndDepartmentalInput', '4')">
                        <el-icon><Coin /></el-icon>
                        <span>财务状态与部门输入</span>
                    </el-menu-item>

                    <el-menu-item index="5" @click="handleMenuClick('OrderConfirmation', '5')">
                        <el-icon><DocumentChecked /></el-icon>
                        <span>生产订单确认</span>
                    </el-menu-item>

                    <el-menu-item index="7" @click="handleMenuClick('FinancialRecievableDetail', '7')">
                        <el-icon><Money /></el-icon>
                        <span>财务应收明细</span>
                    </el-menu-item>

                    <el-menu-item index="10" @click="handleMenuClick('FinishedOutboundAuditGM', '10')">
                        <el-icon><SoldOut /></el-icon>
                        <span>订单出库</span>
                    </el-menu-item>
                    <el-menu-item index="16" @click="handleMenuClick('OrderSummary', '16')">
                        <el-icon><Files /></el-icon>
                        <span>订单汇总</span>
                    </el-menu-item>
                    <el-menu-item index="15" @click="handleMenuClick('LossOutboundAuditGM', '15')">
                        <el-icon><CircleCheck /></el-icon>
                        <span>损失出库审批</span>
                    </el-menu-item>
                    <el-menu-item index="14" @click="handleMenuClick('BusinessAnalysis', '14')">
                        <el-icon><PieChart /></el-icon>
                        <span>业务整体分析</span>
                    </el-menu-item>
                    <el-menu-item index="13" @click="handleMenuClick('CustomerAnalysis', '13')">
                        <el-icon><OfficeBuilding /></el-icon>
                        <span>客户分析</span>
                    </el-menu-item>
                    <el-menu-item index="12" @click="handleMenuClick('WagesApproval', '12')">
                        <el-icon><Checked /></el-icon>
                        <span>工价审核</span>
                    </el-menu-item>

                    <el-menu-item index="11" @click="handleMenuClick('PersonalInfo', '11')">
                        <el-icon><User /></el-icon>
                        <span>个人信息</span>
                    </el-menu-item>
                </el-menu>
            </el-aside>

            <!-- 主体 -->
            <el-main class="app-main">
                <component :is="components[currentComponent]" v-bind="currentProps" />
            </el-main>
        </el-container>
    </el-container>
</template>

<script setup lang="js">
import AllHeader from '@/components/AllHeader.vue'
import { UserFilled, Menu, DataBoard, DataAnalysis, Monitor, Odometer, Refresh, TrendCharts, Coin, DocumentChecked, Money, SoldOut, Files, CircleCheck, PieChart, OfficeBuilding, Checked, User } from '@element-plus/icons-vue'
import axios from 'axios'
import { ref, onMounted, getCurrentInstance } from 'vue'
import CostCalcAndProfitAnalysis from '../components/CostCalcAndProfitAnalysis/CostCalcAndProfitAnalysis.vue'
import OrderStatusMonitor from '../components/OrderStatusMonitor/OrderStatusMonitor.vue'
import OrderImportantStatus from '../components/OrderImortantStatus/OrderImportantStatus.vue'
import MaterialPricesAndCostTrends from '../components/MaterialPricesAndCostTrends/MaterialPricesAndCostTrends.vue'
import FinancialStatusAndDepartmentalInput from '../components/FinancialStatusAndDepartmentalInput/FinancialStatusAndDepartmentalInput.vue'
import OrderConfirmation from '../components/OrderConfirmation/OrderConfirmation.vue'
import OutboundProduct from '@/Pages/TotalWarehouse/FinishedWarehouse/components/OutboundProduct.vue'
import RevertEventAnalyse from '../components/RevertEventAnalyse/RevertEventAnalyse.vue'
import useSetAxiosToken from '../hooks/useSetAxiosToken'
import PersonalInfo from '@/components/PersonalInfo.vue'
import WagesApproval from '@/Pages/ProductionManagementDepartment/ProductionManager/components/WagesApproval.vue'
import MainBoardPage from '../components/MainBoardPage.vue'
import FinancialRecievableDetail from '@/Pages/FinancialManager/components/FinancialRecievableDetail.vue'
import CustomerAnalysis from '../components/CustomerAnalysis/CustomerAnalysis.vue'
import BusinessAnalysis from '../components/BusinessAnalysis/BusinessAnalysis.vue'
import FinishedOutboundAuditGM from '../components/FinishedOutboundAudit/FinishedOutboundAuditGM.vue'
import LossOutboundAuditGM from '../components/FinishedOutboundAudit/LossOutboundAuditGM.vue'
import OrderSummary from '../components/OrderSummary/OrderSummary.vue'
import OrderProgress from '@/Pages/ProductionManagementDepartment/ProductionSharedPages/OrderProgress.vue'
import { useRouter } from 'vue-router'
import { bus } from '../hooks/bus'

const components = {
    CostCalcAndProfitAnalysis,
    OrderStatusMonitor,
    MaterialPricesAndCostTrends,
    FinancialStatusAndDepartmentalInput,
    OrderConfirmation,
    OutboundProduct,
    PersonalInfo,
    OrderImportantStatus,
    RevertEventAnalyse,
    WagesApproval,
    MainBoardPage,
    FinancialRecievableDetail,
    CustomerAnalysis,
    BusinessAnalysis,
    FinishedOutboundAuditGM,
    LossOutboundAuditGM,
    OrderSummary,
    OrderProgress
}
let currentComponent = ref('MainBoardPage')
const currentProps = ref({})
let userName = ref('')
const { setAxiosToken } = useSetAxiosToken()
const $api_baseUrl = getCurrentInstance().appContext.config.globalProperties.$apiBaseUrl
const router = useRouter()

onMounted(() => {
    setAxiosToken()
    getUserAndCharacter()
    handleMenuClick('MainBoardPage')
    bus.on('nav:goto', ({ to, props }) => {
        currentComponent.value = to
        currentProps.value = props || {}
    })
})

// 接口预留，请求后台获取当前登录用户信息
async function getUserAndCharacter() {
    const response = await axios.get(`${$api_baseUrl}/general/getcurrentstaffandcharacter`)
    userName.value = response.data.staffName + '-' + response.data.characterName
}

// 菜单选项切换函数
function handleMenuClick(value) {
    currentComponent.value = value
    // 总经理的订单生产进度默认显示全部订单并按最新倒序排列
    currentProps.value = value === 'OrderProgress' ? { defaultShowAllOrders: true, defaultSortCondition: '最新' } : {}
}

// 退出登录
async function logout() {
    await axios.post(`${$api_baseUrl}/logout`)
    localStorage.removeItem('token')
    localStorage.removeItem('role')
    router.push('/login')
}
</script>
