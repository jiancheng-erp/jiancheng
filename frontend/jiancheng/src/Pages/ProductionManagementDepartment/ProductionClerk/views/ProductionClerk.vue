<template>
  <el-container class="app-shell">
    <!-- 头部固定 + 阴影 -->
    <el-header class="app-header">
      <AllHeader />
    </el-header>

    <!-- 身体：侧栏 + 主区 -->
    <el-container class="app-body">
      <el-aside class="app-aside">
        <div class="profile">
          <el-avatar :icon="UserFilled" :size="80" />
          <div class="profile-name">{{ userName }}</div>
        </div>

        <div class="aside-menu">
          <el-menu default-active="1" class="app-menu">
            <el-menu-item index="1" @click="handleMenuClick(1)">
              <span>数量填报</span>
            </el-menu-item>
            <el-menu-item index="2" @click="handleMenuClick(2)">
              <span>订单生产明细</span>
            </el-menu-item>
            <el-menu-item index="3" @click="handleMenuClick(3)">
              <span>组号名字管理</span>
            </el-menu-item>
            <el-menu-item index="4" @click="handleMenuClick(4)">
              <span>个人信息</span>
            </el-menu-item>
            <el-menu-item index="8" @click="logout()">
              <span>退出系统</span>
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
  import { UserFilled } from '@element-plus/icons-vue'
  import { ref } from 'vue'
  import axios from 'axios'
  import { logout } from '@/Pages/utils/logOut'
  
  export default {
    components: {
      AllHeader,
      QuantityReportOverview,
      OrderProgress,
      ProductionLinesManagement,
      PersonalInfo
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
        }
      },
    }
  }
  </script>
  
  