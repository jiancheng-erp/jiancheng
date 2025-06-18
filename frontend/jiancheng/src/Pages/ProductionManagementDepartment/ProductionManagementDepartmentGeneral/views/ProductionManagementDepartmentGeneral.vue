<template>
  <el-container>
    <el-header>
      <AllHeader></AllHeader>
    </el-header>
    <!--引用header-->
    <el-container>
      <!-- <el-menu default-active="1" 
                    class="el-menu-vertical-demo"
                    :collapse="isCollapse" 
                    @open="handleOpen" 
                    @close="handleClose">
                    <SideMenu></SideMenu>
            </el-menu> -->
      <el-aside>

        <div>
          <el-avatar :icon="UserFilled" :size="100" />
        </div>
        <div style="font-size: x-large">{{ userName }}</div>

        <div class="aside-menu" style="width: 100%; margin-top: 50px;">
          <el-menu
            default-active="2"
            class="el-menu-vertical-demo"
          >
            <el-menu-item index="2" @click="handleMenuClick(2)">
              <span>生产进度</span>
            </el-menu-item>
            <el-menu-item index="11" @click="handleMenuClick(11)">
              <span>订单排期</span>
            </el-menu-item>
            <el-menu-item index="9" @click="handleMenuClick(9)">
              <span>生产报表</span>
            </el-menu-item>
            <el-menu-item index="3" @click="handleMenuClick(3)">
              <span>物料信息</span>
            </el-menu-item>
            <!-- <el-menu-item index="4" @click="handleMenuClick(4)">
              <span>生产管理</span>
            </el-menu-item> -->
            <el-menu-item index="5" @click="handleMenuClick(5)">
              <span>外包信息</span>
            </el-menu-item>
            <el-menu-item index="6" @click="handleMenuClick(6)">
              <span>数量审批</span>
            </el-menu-item>
            <el-menu-item index="7" @click="handleMenuClick(7)">
              <span>外包厂家</span>
            </el-menu-item>
            <el-menu-item index="10" @click="handleMenuClick(10)">
              <span>个人信息</span>
            </el-menu-item>
            <el-menu-item index="8" @click="logout()">
              <span>退出系统</span>
            </el-menu-item>
          </el-menu>
        </div>
      </el-aside>
      <el-main>
        <component :is="currentComponent"></component>
      </el-main>
    </el-container>
  </el-container>
</template>

<script>
import AllHeader from '@/components/AllHeader.vue'
import SideMenu from '../components/sideMenu.vue'
import todotaskDashboard from '../components/TodoTasksView.vue'
import LogisticInfo from '../components/LogisticInfo.vue'
import ProductionInfo from '../components/ProductionInfo.vue'
import OutSourceInfo from '../components/OutSourceInfo.vue'
import ApprovalPage from '../components/ApprovalPage.vue'
import ProductionManagement from '../components/ProductionManagement.vue'
import OrderProgress from '../components/OrderProgress.vue'
import PersonalInfo from '@/components/PersonalInfo.vue'
import NewProductionScheduling from '../components/NewProductionScheduling.vue'
import { UserFilled } from '@element-plus/icons-vue'
import { ref } from 'vue'
import axios from 'axios'
import { logout } from '@/Pages/utils/logOut'
import OutsourceFactoryInfo from '../components/OutsourceFactoryInfo.vue'
import ProductionReport from '../components/ProductionReport.vue'

export default {
  components: {
    AllHeader,
    todotaskDashboard,
    ProductionInfo,
    SideMenu,
    LogisticInfo,
    OutSourceInfo,
    ApprovalPage,
    ProductionManagement,
    OrderProgress,
    OutsourceFactoryInfo,
    ProductionReport,
    PersonalInfo,
    NewProductionScheduling,
  },
  data() {
    return {
      UserFilled,
      currentComponent: 'OrderProgress',
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
        case 2:
          this.currentComponent = 'OrderProgress'
          break
        case 11:
          this.currentComponent = 'NewProductionScheduling'
          break
        case 3:
          this.currentComponent = 'LogisticInfo'
          break
        case 5:
          this.currentComponent = 'OutSourceInfo'
          break
        case 6:
          this.currentComponent = 'ApprovalPage'
          break
        case 7:
          this.currentComponent = 'OutsourceFactoryInfo'
          break
        case 10:
          this.currentComponent = 'PersonalInfo'
          break
        case 9:
          this.currentComponent = 'ProductionReport'
          break
      }
    },
  }
}
</script>

