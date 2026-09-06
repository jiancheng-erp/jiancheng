<template>
  <el-container class="app-shell">
    <!-- 头部 -->
    <el-header class="app-header">
      <AllHeader />
    </el-header>

    <!-- 身体：侧栏 + 主区 -->
    <el-container class="app-body">
      <!-- 侧栏 -->
      <el-aside class="app-aside">
        <div class="aside-brand">
          <div class="aside-brand-badge"><el-icon><Menu /></el-icon></div>
          <div class="aside-brand-text">
            <span class="aside-brand-title">功能导航</span>
            <span class="aside-brand-sub">用量核算</span>
          </div>
        </div>

        <!-- 菜单（侧栏内部滚动，由全局 main.css 控制） -->
        <el-menu
          :default-active="activeIndex"
          class="app-menu"
          :unique-opened="true"
        >
          <el-menu-item index="1" @click="handleMenuClick(1)">
            <el-icon><DataBoard /></el-icon>
            <span>任务看板</span>
          </el-menu-item>
          <el-menu-item index="2" @click="handleMenuClick(2)">
            <el-icon><DataAnalysis /></el-icon>
            <span>用量计算</span>
          </el-menu-item>
          <el-menu-item index="10" @click="handleMenuClick(10)">
            <el-icon><Refresh /></el-icon>
            <span>退回任务列表</span>
          </el-menu-item>
          <el-menu-item index="4" @click="handleMenuClick(4)">
            <el-icon><Tickets /></el-icon>
            <span>生产BOM用量填写</span>
          </el-menu-item>
          <el-menu-item index="5" @click="handleMenuClick(5)">
            <el-icon><EditPen /></el-icon>
            <span>总仓订单缺失材料用量填写</span>
          </el-menu-item>
          <el-menu-item index="11" @click="handleMenuClick(11)">
            <el-icon><Edit /></el-icon>
            <span>用量修改</span>
          </el-menu-item>
          <el-menu-item index="3" @click="handleMenuClick(3)">
            <el-icon><Search /></el-icon>
            <span>订单查询</span>
          </el-menu-item>
          <el-menu-item index="6" @click="handleMenuClick(6)">
            <el-icon><Coin /></el-icon>
            <span>材料单价查询</span>
          </el-menu-item>
          <el-menu-item index="7" @click="handleMenuClick(7)">
            <el-icon><Box /></el-icon>
            <span>物控入/出库</span>
          </el-menu-item>
          <el-menu-item index="8" @click="handleMenuClick(8)">
            <el-icon><User /></el-icon>
            <span>个人信息</span>
          </el-menu-item>
        </el-menu>
      </el-aside>

      <!-- 主区（内部滚动） -->
      <el-main class="app-main">
        <component :is="currentComponent" :departmentId="departmentId" />
      </el-main>
    </el-container>
  </el-container>
</template>

<script>
import AllHeader from '@/components/AllHeader.vue'
import { UserFilled, Menu, DataBoard, DataAnalysis, Refresh, Tickets, EditPen, Edit, Search, Coin, Box, User } from '@element-plus/icons-vue'
import Dashboard from '../components/UsageCalculationDashboard.vue';
import UsageCaculationView from '../components/UsageCalculationView.vue'
import OrderSearch from '../components/OrderSearch.vue';
import PersonalInfo from '@/components/PersonalInfo.vue';
import SecondBOMListView from '../components/SecondBOMListView.vue';
import RevertDashboard from '@/components/RevertDashboard.vue';
import MissingPurchaseUsageInput from '../components/MissingPurchaseUsageInput.vue';
import UsageModificationView from '../components/UsageModificationView.vue';
import MaterialPriceView from '../components/MaterialPriceView.vue';
import FinancialWarehouseDetail from '@/Pages/FinancialManager/components/FinancialWarehouseDetail.vue'
import axios from 'axios'


export default {
    components: {
        AllHeader,
        Menu,
        DataBoard,
        DataAnalysis,
        Refresh,
        Tickets,
        EditPen,
        Edit,
        Search,
        Coin,
        Box,
        User,
        Dashboard,
        UsageCaculationView,
        OrderSearch,
        PersonalInfo,
        SecondBOMListView,
        RevertDashboard,
        MissingPurchaseUsageInput,
        UsageModificationView,
        MaterialPriceView,
        FinancialWarehouseDetail
    },
    data() {
        return {
            UserFilled,
            currentComponent: 'Dashboard',
            userName: '',
            departmentId: '14'
        }
    },
    mounted() {
        this.$setAxiosToken()
        this.getUserAndCharacter()
    },
    methods: {
        async getUserAndCharacter() {
            const response = await axios.get(`${this.$apiBaseUrl}/general/getcurrentstaffandcharacter`)
            this.userName = response.data.staffName + '-' + response.data.characterName
        },
        handleMenuClick(index) {
            switch (index) {
                case 1:
                    this.currentComponent = 'Dashboard'
                    break
                case 2:
                    this.currentComponent = 'UsageCaculationView'
                    break
                case 3:
                    this.currentComponent = 'OrderSearch'
                    break
                case 4:
                    this.currentComponent = 'SecondBOMListView'
                    break
                case 5:
                    this.currentComponent = 'MissingPurchaseUsageInput'
                    break
                case 6:
                    this.currentComponent = 'MaterialPriceView'
                    break
                case 7:
                    this.currentComponent = 'FinancialWarehouseDetail'
                    break
                case 8:
                    this.currentComponent = 'PersonalInfo'
                    break
                case 10:
                    this.currentComponent = 'RevertDashboard'
                    break
                case 11:
                    this.currentComponent = 'UsageModificationView'
                    break
            }
        },
        async logout() {
            await this.$axios.post(`${this.$apiBaseUrl}/logout`)
            localStorage.removeItem('token')
            localStorage.removeItem('role')
            this.$router.push('/login')
        }
    }
}
</script>