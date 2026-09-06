<template>
  <el-container class="app-shell">
    <!-- 头部固定 + 阴影 -->
    <el-header class="app-header">
      <AllHeader />
    </el-header>

    <!-- 身体：侧栏 + 主区 -->
    <el-container class="app-body">
      <el-aside class="app-aside">
        <div class="aside-brand">
          <div class="aside-brand-badge"><el-icon><Menu /></el-icon></div>
          <div class="aside-brand-text">
            <span class="aside-brand-title">功能导航</span>
            <span class="aside-brand-sub">生产管理</span>
          </div>
        </div>

        <div class="aside-menu">
          <el-menu default-active="1" class="app-menu">
            <el-menu-item index="1" @click="handleMenuClick(1)">
              <el-icon><Histogram /></el-icon>
              <span>数量填报</span>
            </el-menu-item>
            <el-menu-item index="2" @click="handleMenuClick(2)">
              <el-icon><Memo /></el-icon>
              <span>订单生产明细</span>
            </el-menu-item>
            <el-menu-item index="3" @click="handleMenuClick(3)">
              <el-icon><Management /></el-icon>
              <span>组号名字管理</span>
            </el-menu-item>
            <el-menu-item index="5" @click="handleMenuClick(5)">
              <el-icon><Download /></el-icon>
              <span>业务生产订单下载</span>
            </el-menu-item>
            <el-menu-item index="6" @click="handleMenuClick(6)">
              <el-icon><Printer /></el-icon>
              <span>生产指令单下载</span>
            </el-menu-item>
            <el-menu-item index="4" @click="handleMenuClick(4)">
              <el-icon><User /></el-icon>
              <span>个人信息</span>
            </el-menu-item>
          </el-menu>
        </div>
      </el-aside>

      <el-main class="app-main">
        <component :is="currentComponent"></component>
      </el-main>
    </el-container>
  </el-container>
</template>
  
  <script>
  import AllHeader from '@/components/AllHeader.vue'
  import OrderProgress from '../../ProductionSharedPages/OrderProgress.vue'
  import QuantityReportOverview from '../components/QuantityReportOverview.vue'
  import ProductionLinesManagement from '../components/ProductionLinesManagement.vue'
  import PersonalInfo from '@/components/PersonalInfo.vue'
  import BusinessOrderDownload from '../components/BusinessOrderDownload.vue'
  import ProductionInstructionDownload from '../components/ProductionInstructionDownload.vue'
  import { UserFilled, Menu, Histogram, Memo, Management, Download, Printer, User } from '@element-plus/icons-vue'
  import { ref } from 'vue'
  import axios from 'axios'
  import { logout } from '@/Pages/utils/logOut'
  
  export default {
    components: {
      AllHeader,
      QuantityReportOverview,
      OrderProgress,
      ProductionLinesManagement,
      PersonalInfo,
      BusinessOrderDownload,
      ProductionInstructionDownload,
      Menu,
      Histogram,
      Memo,
      Management,
      Download,
      Printer,
      User
    },
    data() {
      return {
        UserFilled,
        currentComponent: 'QuantityReportOverview',
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
      handleMenuClick(index) {
        switch (index) {
          case 1:
            this.currentComponent = 'QuantityReportOverview'
            break
          case 2:
            this.currentComponent = 'OrderProgress'
            break
          case 3:
            this.currentComponent = 'ProductionLinesManagement'
            break
          case 4:
            this.currentComponent = 'PersonalInfo'
            break
          case 5:
            this.currentComponent = 'BusinessOrderDownload'
            break
          case 6:
            this.currentComponent = 'ProductionInstructionDownload'
            break
        }
      },
    }
  }
  </script>
  
  