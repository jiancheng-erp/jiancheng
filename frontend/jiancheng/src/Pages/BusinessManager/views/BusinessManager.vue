<template>
  <el-container class="app-shell">
    <!-- 头部 -->
    <el-header class="app-header">
      <AllHeader />
    </el-header>

    <!-- 身体：侧栏 + 主区 -->
    <el-container class="app-body">
      <!-- 侧栏（头像区 + 内部滚动菜单） -->
      <el-aside class="app-aside">
        <div class="aside-brand">
          <div class="aside-brand-badge"><el-icon><Menu /></el-icon></div>
          <div class="aside-brand-text">
            <span class="aside-brand-title">功能导航</span>
            <span class="aside-brand-sub">业务管理</span>
          </div>
        </div>

        <el-menu
          :default-active="defaultActive"
          class="app-menu"
          :unique-opened="true"
        >
          <el-menu-item index="2" @click="handleMenuClick(2)">
            <el-icon><ShoppingCart /></el-icon>
            <span>订单管理</span>
          </el-menu-item>
          <el-menu-item index="15" @click="handleMenuClick(15)">
            <el-icon><DataBoard /></el-icon>
            <span>业务统计看板</span>
          </el-menu-item>
          <el-menu-item index="13" @click="handleMenuClick(13)">
            <el-icon><TrendCharts /></el-icon>
            <span>预报单管理</span>
          </el-menu-item>
          <el-menu-item index="10" @click="handleMenuClick(10)">
            <el-icon><SoldOut /></el-icon>
            <span>订单出库</span>
          </el-menu-item>
          <el-menu-item index="11" @click="handleMenuClick(11)">
            <el-icon><Finished /></el-icon>
            <span>历史（已完成）订单</span>
          </el-menu-item>
          <el-menu-item index="3" @click="handleMenuClick(3)">
            <el-icon><OfficeBuilding /></el-icon>
            <span>客户/配码管理</span>
          </el-menu-item>
          <el-menu-item index="4" @click="handleMenuClick(4)">
            <el-icon><Goods /></el-icon>
            <span>鞋型管理</span>
          </el-menu-item>
          <el-menu-item index="5" @click="handleMenuClick(5)">
            <el-icon><Management /></el-icon>
            <span>码段管理</span>
          </el-menu-item>
          <el-menu-item index="6" @click="handleMenuClick(6)">
            <el-icon><Download /></el-icon>
            <span>订单导出</span>
          </el-menu-item>
          <el-menu-item index="14" @click="handleMenuClick(14)">
            <el-icon><Odometer /></el-icon>
            <span>生产进度</span>
          </el-menu-item>
          <el-menu-item index="12" @click="handleMenuClick(12)">
            <el-icon><Memo /></el-icon>
            <span>成品出库单详情</span>
          </el-menu-item>
          <el-menu-item index="8" @click="handleMenuClick(8)">
            <el-icon><User /></el-icon>
            <span>个人信息</span>
          </el-menu-item>
        </el-menu>
      </el-aside>

      <!-- 主内容（内部滚动） -->
      <el-main class="app-main">
        <component :is="currentComponent" v-bind="currentProps" />
      </el-main>
    </el-container>
  </el-container>
</template>

<script>
import AllHeader from '@/components/AllHeader.vue'
import { UserFilled, Menu, ShoppingCart, DataBoard, TrendCharts, SoldOut, Finished, OfficeBuilding, Goods, Management, Download, Odometer, Memo, User } from '@element-plus/icons-vue'
import OrderManagement from '../components/OrderManagement.vue';
import ForecastManagement from '../components/ForecastManagement.vue';
import CustomerManagement from '../components/CustomerManagement.vue';
import PersonalInfo from '@/components/PersonalInfo.vue';
import axios from 'axios'
import ShoeTypeManagement from '@/components/ShoeTypeManagement.vue';
import BatchInfoTypeManagement from '../components/BatchInfoTypeManagement.vue';
import OrderExport from '../components/OrderExport.vue';
import OutboundProduct from '@/Pages/TotalWarehouse/FinishedWarehouse/components/OutboundProduct.vue';
import HistoryOrder from '../components/HistoryOrder.vue';
import OutboundRecordsDownload from '@/Pages/TotalWarehouse/FinishedWarehouse/components/OutboundRecordsDownload.vue';
import OrderProgress from '../components/OrderProgress.vue';
import BusinessStatistics from '../components/BusinessStatistics.vue';
export default {
    components: {
        AllHeader,
        Menu,
        ShoppingCart,
        DataBoard,
        TrendCharts,
        SoldOut,
        Finished,
        OfficeBuilding,
        Goods,
        Management,
        Download,
        Odometer,
        Memo,
        User,
        OrderManagement,
        BusinessStatistics,
        ForecastManagement,
        CustomerManagement,
        ShoeTypeManagement,
        BatchInfoTypeManagement,
        PersonalInfo,
        OrderExport,
        OutboundProduct,
        HistoryOrder,
        OutboundRecordsDownload,
        OrderProgress
    },
    data() {
        return {
            UserFilled,
            currentComponent: 'OrderManagement',
            userName: '',
            currentProps: {}
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
            this.currentProps = {}
            switch (index) {
                case 1:
                    this.currentComponent = 'Dashboard'
                    break
                case 2:
                    this.currentComponent = 'OrderManagement'
                    break
                case 13:
                    this.currentComponent = 'ForecastManagement'
                    break
                case 3:
                    this.currentComponent = 'CustomerManagement'
                    break
                case 4:
                    this.currentComponent = 'ShoeTypeManagement'
                    break
                case 5:
                    this.currentComponent = "BatchInfoTypeManagement"
                    break
                case 6:
                    this.currentComponent = "OrderExport"
                    break
                case 8:
                    this.currentComponent = 'PersonalInfo'
                    break
                case 12:
                    this.currentComponent = 'OutboundRecordsDownload'
                    break
                case 9:
                    this.$router.push('/')
                    break
                case 10:
                    this.currentComponent = 'OutboundProduct'
                    this.currentProps = { editable: false }
                    break
                case 11:
                    this.currentComponent = 'HistoryOrder'
                    this.currentProps = { editable: false }
                    break
                case 14:
                    this.currentComponent = 'OrderProgress'
                    break
                case 15:
                    this.currentComponent = 'BusinessStatistics'
                    break
            }
        },
        async logout() {
            this.$router.push('/login')
            await this.$axios.post(`${this.$apiBaseUrl}/logout`)
            localStorage.removeItem('token')
            localStorage.removeItem('role')
        }
    }
}
</script>