<template>
  <el-container class="app-shell">
    <!-- 顶部栏 -->
    <el-header class="app-header">
      <AllHeader />
    </el-header>

    <el-container class="app-body">
      <!-- 侧栏 -->
      <el-aside class="app-aside">
        <div class="profile">
          <el-avatar :icon="UserFilled" :size="80" />
          <div class="profile-name">{{ userName }}</div>
        </div>

        <!-- 菜单（内部滚动） -->
        <el-menu
          :default-active="activeIndex"
          class="app-menu"
          :unique-opened="true"
        >
          <el-menu-item index="0" @click="handleMenuClick('MainBoardPage', '0')">
            <span>主页看板</span>
          </el-menu-item>

          <el-menu-item index="1" @click="handleMenuClick('CostCalcAndProfitAnalysis', '1')">
            <span>成本计算与盈利分析</span>
          </el-menu-item>

          <el-menu-item index="2" @click="handleMenuClick('OrderImportantStatus', '2')">
            <span>订单关键节点监控</span>
          </el-menu-item>

          <el-menu-item index="6" @click="handleMenuClick('RevertEventAnalyse', '6')">
            <span>退回情况记录统计</span>
          </el-menu-item>

          <el-menu-item index="3" @click="handleMenuClick('MaterialPricesAndCostTrends', '3')">
            <span>材料价格与成本趋势</span>
          </el-menu-item>

          <el-menu-item index="4" @click="handleMenuClick('FinancialStatusAndDepartmentalInput', '4')">
            <span>财务状态与部门输入</span>
          </el-menu-item>

          <el-menu-item index="5" @click="handleMenuClick('OrderConfirmation', '5')">
            <span>生产订单确认</span>
          </el-menu-item>

          <el-menu-item index="7" @click="handleMenuClick('FinancialRecievableDetail', '7')">
            <span>财务应收明细</span>
          </el-menu-item>

          <el-menu-item index="10" @click="handleMenuClick('OutboundProduct', '10')">
            <span>订单出库</span>
          </el-menu-item>
          <el-menu-item index="13" @click="handleMenuClick('CustomerAnalysis', '13')">
            <span>客户分析</span>
          </el-menu-item>

          <el-menu-item index="12" @click="handleMenuClick('WagesApproval', '12')">
            <span>工价审核</span>
          </el-menu-item>

          <el-menu-item index="11" @click="handleMenuClick('PersonalInfo', '11')">
            <span>个人信息</span>
          </el-menu-item>

          <el-menu-item index="99" @click="logout">
            <span>退出系统</span>
          </el-menu-item>
        </el-menu>
      </el-aside>

      <!-- 主体 -->
      <el-main class="app-main">
        <component :is="components[currentComponent]" />
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
import { useRouter } from "vue-router";

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
    CustomerAnalysis
}
let currentComponent = ref('MainBoardPage')
let userName = ref('')
const { setAxiosToken } = useSetAxiosToken()
const $api_baseUrl = getCurrentInstance().appContext.config.globalProperties.$apiBaseUrl
const router = useRouter();

onMounted(() => {
    setAxiosToken()
    getUserAndCharacter()
    handleMenuClick('MainBoardPage')
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
