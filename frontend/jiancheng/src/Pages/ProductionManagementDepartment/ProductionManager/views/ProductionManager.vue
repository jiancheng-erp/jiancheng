<template>
  <el-container>
    <el-header>
      <AllHeader></AllHeader>
    </el-header>
    <!--引用header-->
    <el-container>
      <el-aside>
        <div>
          <el-avatar :icon="UserFilled" :size="100" />
        </div>
        <div style="font-size: x-large">{{ userName }}</div>

        <div class="aside-menu" style="width: 100%; margin-top: 50px">
          <el-menu
            default-active="2"
            class="el-menu-vertical-demo"
          >
            <el-menu-item index="1" @click="handleMenuClick(1)">
              <span>主页看板</span>
            </el-menu-item>
            <el-menu-item index="2" @click="handleMenuClick(2)">
              <span>生产排期表</span>
            </el-menu-item>
            <el-menu-item index="3" @click="handleMenuClick(3)">
              <span>物料信息</span>
            </el-menu-item>
            <el-menu-item index="5" @click="handleMenuClick(5)">
              <span>外包审批</span>
            </el-menu-item>
            <el-menu-item index="6" @click="handleMenuClick(6)">
              <span>工价审批</span>
            </el-menu-item>
            <el-menu-item index="9" @click="handleMenuClick(9)">
              <span>退回订单统计</span>
            </el-menu-item>
            <el-menu-item index="8" @click="handleMenuClick(8)">
              <span>个人信息</span>
            </el-menu-item>
            <el-menu-item index="7" @click="logout">
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
import Dashboard from '../components/TodoTasksView.vue'
import { UserFilled } from '@element-plus/icons-vue'
import ProductionSchedulingDialogue from '../components/ProductionSchedulingDialogue.vue'
import LogisticInfo from '../components/LogisticInfo.vue'
import OutSourceApproval from '../components/OutSourceApproval.vue'
import WagesApproval from '../components/WagesApproval.vue'
import OrderProgress from '../components/OrderProgress.vue'
import PersonalInfo from '@/components/PersonalInfo.vue'
import MainBoardPage from '@/Pages/CompanyManger/components/MainBoardPage.vue'
import RevertEventAnalyse from '@/Pages/CompanyManger/components/RevertEventAnalyse/RevertEventAnalyse.vue'
import axios from 'axios'
import { logout } from '@/Pages/utils/logOut'
export default {
  components: {
    UserFilled,
    AllHeader,
    Dashboard,
    ProductionSchedulingDialogue,
    LogisticInfo,
    OutSourceApproval,
    WagesApproval,
    OrderProgress,
    PersonalInfo,
    MainBoardPage,
    RevertEventAnalyse
  },
  data() {
    return {
      userName: '',
      currentComponent: 'OrderProgress',
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
      console.log(index)
      switch (index) {
        case 1:
          this.currentComponent = 'MainBoardPage'
          break
        case 2:
          this.currentComponent = 'OrderProgress'
          break
        case 3:
          this.currentComponent = 'LogisticInfo'
          break
        case 4:
          this.currentComponent = 'ProductionInfo'
          break
        case 5:
          this.currentComponent = 'OutSourceApproval'
          break
        case 6:
          this.currentComponent = 'WagesApproval'
          break
        case 9:
          this.currentComponent = 'RevertEventAnalyse'
          break
        case 8:
          this.currentComponent = 'PersonalInfo'
          break
      }
    }
  }
}
</script>
