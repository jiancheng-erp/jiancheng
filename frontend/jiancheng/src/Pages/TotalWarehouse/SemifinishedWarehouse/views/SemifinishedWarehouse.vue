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
        <div class="profile">
          <el-avatar :icon="UserFilled" :size="80" />
          <div class="profile-name">{{ userName }}</div>
        </div>

        <!-- 菜单（侧栏内部滚动，由全局 main.css 控制） -->
        <el-menu
          :default-active="activeIndex"
          class="app-menu"
          :unique-opened="true"
        >
          <el-menu-item index="1" @click="handleMenuClick(1)">
            <span>半成品入库</span>
          </el-menu-item>
          <el-menu-item index="5" @click="handleMenuClick(5)">
            <span>入\出库记录</span>
          </el-menu-item>
          <el-menu-item index="3" @click="handleMenuClick(3)">
            <span>库存</span>
          </el-menu-item>
          <el-menu-item index="2" @click="handleMenuClick(2)">
            <span>生产动态明细</span>
          </el-menu-item>
          <el-menu-item index="6" @click="handleMenuClick(6)">
            <span>个人信息</span>
          </el-menu-item>
          <el-menu-item index="4" @click="logout">
            <span>退出系统</span>
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
import SemiInboundOutbound from '../components/SemiInboundOutbound.vue'
import SemifinishedInOutHistory from '../components/SemifinishedInOutHistory.vue'
import OrderProgress from '@/Pages/ProductionManagementDepartment/ProductionSharedPages/OrderProgress.vue'
import { UserFilled } from '@element-plus/icons-vue'
import axios from 'axios'
import { logout } from '@/Pages/utils/logOut'
import InOutboundRecords from '../components/InOutboundRecords.vue'
import PersonalInfo from '@/components/PersonalInfo.vue'
export default {
    components: {
        AllHeader,
        SemiInboundOutbound,
        SemifinishedInOutHistory,
        OrderProgress,
        InOutboundRecords
    },
    data() {
        return {
            UserFilled,
            currentComponent:'SemiInboundOutbound',
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
                    this.currentComponent = 'SemiInboundOutbound'
                    break
                case 2:
                    this.currentComponent = 'OrderProgress'
                    break
                case 3:
                    this.currentComponent = 'SemifinishedInOutHistory'
                    break
                case 5:
                    this.currentComponent = 'InOutboundRecords'
                    break
                case 6:
                    this.currentComponent = 'PersonalInfo'
                    break
            }
        }
    }
}
</script>