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
            <span class="aside-brand-sub">成品仓管理</span>
          </div>
        </div>

        <!-- 菜单（内部滚动） -->
        <el-menu
          :default-active="activeIndex"
          class="app-menu"
          :unique-opened="true"
        >
          <el-menu-item index="1" @click="handleMenuClick(1)">
            <el-icon><Box /></el-icon>
            <span>成品入库</span>
          </el-menu-item>
          <el-menu-item index="7" @click="handleMenuClick(7)">
            <el-icon><Sell /></el-icon>
            <span>发起出库</span>
          </el-menu-item>
          <el-menu-item index="8" @click="handleMenuClick(8)">
            <el-icon><Tickets /></el-icon>
            <span>出库申请记录</span>
          </el-menu-item>
          <el-menu-item index="9" @click="handleMenuClick(9)">
            <el-icon><ShoppingCart /></el-icon>
            <span>按订单出库（包材）</span>
          </el-menu-item>
          <el-menu-item index="10" @click="handleMenuClick(10)">
            <el-icon><SoldOut /></el-icon>
            <span>通用材料出库（包材）</span>
          </el-menu-item>
          <el-menu-item index="5" @click="handleMenuClick(5)">
            <el-icon><Memo /></el-icon>
            <span>入\出库单</span>
          </el-menu-item>
          <el-menu-item index="3" @click="handleMenuClick(3)">
            <el-icon><Goods /></el-icon>
            <span>库存</span>
          </el-menu-item>
          <el-menu-item index="2" @click="handleMenuClick(2)">
            <el-icon><TrendCharts /></el-icon>
            <span>生产动态明细</span>
          </el-menu-item>
          <el-menu-item index="6" @click="handleMenuClick(6)">
            <el-icon><User /></el-icon>
            <span>个人信息</span>
          </el-menu-item>
        </el-menu>
      </el-aside>

      <!-- 主内容（内部滚动） -->
      <el-main class="app-main">
        <component :is="currentComponent" />
      </el-main>
    </el-container>
  </el-container>
</template>

<script>
import AllHeader from '@/components/AllHeader.vue'
import InboundProduct from '../components/InboundProduct.vue'
import FinishedInventoryPanel from '../components/FinishedInventoryPanel.vue'
import { UserFilled, Menu, Box, Sell, Tickets, ShoppingCart, SoldOut, Memo, Goods, TrendCharts, User } from '@element-plus/icons-vue'
import axios from 'axios'
import { logout } from '@/Pages/utils/logOut'
import OrderProgress from '@/Pages/ProductionManagementDepartment/ProductionSharedPages/OrderProgress.vue'
import InOutboundRecords from '../components/InOutboundRecords.vue'
import PersonalInfo from '@/components/PersonalInfo.vue'
import OutboundProduct from '../components/OutboundProduct.vue'
import OutboundFinishedNew from '../components/OutboundFinishedNew.vue'
import OutboundByOrder from '../../HeadOfWarehouse/components/OutboundByOrder.vue'
import GeneralMaterialOutbound from '../../HeadOfWarehouse/components/GeneralMaterialOutbound.vue'
export default {
    components: {
        AllHeader,
        InboundProduct,
      FinishedInventoryPanel,
        OrderProgress,
        InOutboundRecords,
        PersonalInfo,
        OutboundProduct,
        OutboundFinishedNew,
        OutboundByOrder,
        GeneralMaterialOutbound,
        Menu,
        Box,
        Sell,
        Tickets,
        ShoppingCart,
        SoldOut,
        Memo,
        Goods,
        TrendCharts,
        User
    },
    data() {
        return {
            UserFilled,
            currentComponent:'InboundProduct',
            userName: '',
            logout
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
        handleMenuClick(index){
            switch(index) {
                case 1:
                    this.currentComponent = 'InboundProduct'
                    break
                case 2:
                    this.currentComponent = 'OrderProgress'
                    break
                case 3:
                  this.currentComponent = 'FinishedInventoryPanel'
                    break
                case 5:
                    this.currentComponent = 'InOutboundRecords'
                    break
                case 6:
                    this.currentComponent = 'PersonalInfo'
                    break
                case 7:
                    this.currentComponent = 'OutboundProduct'
                    break
                case 8:
                    this.currentComponent = 'OutboundFinishedNew'
                    break
                case 9:
                    this.currentComponent = 'OutboundByOrder'
                    break
                case 10:
                    this.currentComponent = 'GeneralMaterialOutbound'
                    break
            }
        }
    }
}
</script>