<template>
  <el-container class="app-shell">
    <!-- 顶部 -->
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
            <span class="aside-brand-sub">物控管理</span>
          </div>
        </div>

        <!-- 菜单（内部滚动） -->
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
            <el-icon><ShoppingCart /></el-icon>
            <span>一次采购订单创建</span>
          </el-menu-item>
          <el-menu-item index="3" @click="handleMenuClick(3)">
            <el-icon><Refresh /></el-icon>
            <span>退回任务列表</span>
          </el-menu-item>

          <el-menu-item index="11" @click="handleMenuClick(11)">
            <el-icon><Box /></el-icon>
            <span>总仓库存</span>
          </el-menu-item>
          <el-menu-item index="5" @click="handleMenuClick(5)">
            <el-icon><Management /></el-icon>
            <span>材料管理</span>
          </el-menu-item>
          <el-menu-item index="12" @click="handleMenuClick(12)">
            <el-icon><List /></el-icon>
            <span>入/出库记录</span>
          </el-menu-item>
          <el-menu-item index="13" @click="handleMenuClick(13)">
            <el-icon><ShoppingCartFull /></el-icon>
            <span>采购订单信息</span>
          </el-menu-item>
          <el-menu-item index="14" @click="handleMenuClick(14)">
            <el-icon><EditPen /></el-icon>
            <span>缺失材料补采采购量录入</span>
          </el-menu-item>

          <el-menu-item index="6" @click="handleMenuClick(6)">
            <el-icon><House /></el-icon>
            <span>仓库管理</span>
          </el-menu-item>
          <el-menu-item index="7" @click="handleMenuClick(7)">
            <el-icon><OfficeBuilding /></el-icon>
            <span>供货商管理</span>
          </el-menu-item>
          <el-menu-item index="10" @click="handleMenuClick(10)">
            <el-icon><Grid /></el-icon>
            <span>码段管理</span>
          </el-menu-item>
          <el-menu-item index="8" @click="handleMenuClick(8)">
            <el-icon><Search /></el-icon>
            <span>订单查询</span>
          </el-menu-item>
          <el-menu-item index="15" @click="handleMenuClick(15)">
            <el-icon><Document /></el-icon>
            <span>生产通知单及工艺单</span>
          </el-menu-item>
          <el-menu-item index="9" @click="handleMenuClick(9)">
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
import Dashboard from '../components/LogisticsManagerDashboard.vue'
import FirstPurchase from '../components/FirstPurchaseListView.vue'
import SecondPurchase from '../components/SecondPurchaseListView.vue'
import FixedAssets from '../components/FixedAssetsConsumablesView.vue'
import MaterialManagement from '../components/MaterialManagementView.vue'
import WarehouseManagement from '../components/WarehouseManagementView.vue'
import SupplierManagement from '../components/SupplierManagementView.vue'
import MultiPurchaseIssue from '../components/MultiPurchaseIssue.vue'
import OrderSearch from '../components/OrderSearch.vue'
import PersonalInfo from '@/components/PersonalInfo.vue'
import LogisticsBatchTypeManagement from '@/components/LogisticsBatchInfoTypeManagement.vue'
import RevertDashboard from '@/components/RevertDashboard.vue'
import TestPage from '../components/TestPage.vue'
import MaterialStorage from '@/Pages/TotalWarehouse/HeadOfWarehouse/components/MaterialStorage.vue'
import { UserFilled, Menu, DataBoard, ShoppingCart, Refresh, Box, Management, List, ShoppingCartFull, EditPen, House, OfficeBuilding, Grid, Search, Document, User } from '@element-plus/icons-vue'
import FinancialWarehouseDetail from '@/Pages/FinancialManager/components/FinancialWarehouseDetail.vue'
import PurchaseOrderInfo from '@/Pages/TotalWarehouse/HeadOfWarehouse/components/PurchaseOrderInfo.vue'
import MissingPurchaseAmountInput from '../components/MissingPurchaseAmountInput.vue'
import BusinessProductionOrder from '../components/BusinessProductionOrderView.vue'
export default {
    components: {
        AllHeader,
        Menu,
        DataBoard,
        ShoppingCart,
        Refresh,
        Box,
        Management,
        List,
        ShoppingCartFull,
        EditPen,
        House,
        OfficeBuilding,
        Grid,
        Search,
        Document,
        User,
        Dashboard,
        FirstPurchase,
        SecondPurchase,
        FixedAssets,
        MaterialManagement,
        WarehouseManagement,
        SupplierManagement,
        TestPage,
        OrderSearch,
        PersonalInfo,
        LogisticsBatchTypeManagement,
        MultiPurchaseIssue,
        RevertDashboard,
        MaterialStorage,
        FinancialWarehouseDetail,
        PurchaseOrderInfo,
        MissingPurchaseAmountInput,
        BusinessProductionOrder
    },
    data() {
        return {
            UserFilled,
            currentComponent:'Dashboard',
            userName: '',
            departmentId: '3'
        }
    },
    mounted() {
        this.$setAxiosToken()
        this.getUserAndCharacter()
    },
    methods: {
        async getUserAndCharacter() {
            const response = await this.$axios.get(`${this.$apiBaseUrl}/general/getcurrentstaffandcharacter`)
            this.userName = response.data.staffName + '-' + response.data.characterName
        },
        handleMenuClick(index){
            console.log(index)
            switch(index) {
                case 1:
                    this.currentComponent = 'Dashboard'
                    break
                case 2:
                    this.currentComponent = 'FirstPurchase'
                    break
                case 3:
                    this.currentComponent = 'RevertDashboard'
                    break
                case 5:
                    this.currentComponent = 'MaterialManagement'
                    break
                case 6:
                    this.currentComponent = 'WarehouseManagement'
                    break
                case 7:
                    this.currentComponent = 'SupplierManagement'
                    break
                case 8:
                    this.currentComponent = 'OrderSearch'
                    break
                case 9:
                    this.currentComponent = 'PersonalInfo'
                    break
                case 10:
                    this.currentComponent = 'LogisticsBatchTypeManagement' 
                    break
                case 11:
                    this.currentComponent = 'MaterialStorage'
                    break
                case 12:
                    this.currentComponent = 'FinancialWarehouseDetail'
                    break
                case 13:
                    this.currentComponent = 'PurchaseOrderInfo'
                    break
                case 14:
                    this.currentComponent = 'MissingPurchaseAmountInput'
                    break
                case 15:
                    this.currentComponent = 'BusinessProductionOrder'
                    break
            }
        },
        async logout() {
            await this.$axios.post(`${this.$apiBaseUrl}/logout`)
            this.$router.push('/login')
            localStorage.removeItem('token')
            localStorage.removeItem('role')
        }
    },
}
</script>