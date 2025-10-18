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

        <!-- 菜单（内部滚动，由 main.css 的 .app-menu 控制） -->
        <el-menu
          :default-active="activeIndex"
          class="app-menu"
          :unique-opened="true"
        >
          <el-menu-item index="1" @click="handleMenuClick(1)">
            <span>任务看板</span>
          </el-menu-item>
          <el-menu-item index="2" @click="handleMenuClick(2)">
            <span>调版分配与下发</span>
          </el-menu-item>
          <el-menu-item index="6" @click="handleMenuClick(6)">
            <span>投产指令单创建</span>
          </el-menu-item>
          <el-menu-item index="7" @click="handleMenuClick(7)">
            <span>生产BOM用量填写</span>
          </el-menu-item>
          <el-menu-item index="10" @click="handleMenuClick(10)">
            <span>总仓订单缺失材料补采</span>
          </el-menu-item>
          <el-menu-item index="5" @click="handleMenuClick(5)">
            <span>退回任务列表</span>
          </el-menu-item>
          <el-menu-item index="3" @click="handleMenuClick(3)">
            <span>订单查询</span>
          </el-menu-item>
          <el-menu-item index="8" @click="handleMenuClick(8)">
            <span>个人信息</span>
          </el-menu-item>
          <el-menu-item index="9" @click="logout">
            <span>退出系统</span>
          </el-menu-item>
        </el-menu>
      </el-aside>

      <!-- 主区（内部滚动，由 .app-main 控制） -->
      <el-main class="app-main">
        <component :is="currentComponent" :departmentId="departmentId" />
      </el-main>
    </el-container>
  </el-container>
</template>

<script>
import AllHeader from '@/components/AllHeader.vue'
import { UserFilled } from '@element-plus/icons-vue'
import Dashboard from '@/Pages/TechnologyDepartment/TechnicalDepartmentClerk/components/TechnicalClerkDashboard.vue'
import OrderSearch from '../components/OrderSearch.vue';
import PersonalInfo from '@/components/PersonalInfo.vue';
import AdjustList from '../../TechnicalManager/components/AdjustList.vue';
import RevertDashboard from '@/components/RevertDashboard.vue';
import ProductionOrderCreate from '@/Pages/DevelopmentManager/components/ProductionOrderCreate.vue'
import SecondBOMListView from '@/Pages/UsageCalculation/components/SecondBOMListView.vue';
import WarehouseMissingMaterialPurchase from '../components/WarehouseMissingMaterialPurchase.vue';
import axios from 'axios'
export default {
    components: {
        AllHeader,
        Dashboard,
        OrderSearch,
        PersonalInfo,
        AdjustList,
        RevertDashboard,
        ProductionOrderCreate,
        SecondBOMListView,
        WarehouseMissingMaterialPurchase
    },
    data() {
        return {
            UserFilled,
            currentComponent: 'Dashboard',
            userName: '',
            departmentId: '13'
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
                    this.currentComponent = 'Dashboard'
                    break
                case 2:
                    this.currentComponent = 'AdjustList'
                    break
                case 3:
                    this.currentComponent = 'OrderSearch'
                    break
                case 4:
                    this.currentComponent = 'BOMReviewList'
                    break
                case 5:
                    this.currentComponent = 'RevertDashboard'
                    break
                case 6:
                    this.currentComponent = 'ProductionOrderCreate'
                    break
                case 7:
                    this.currentComponent = 'SecondBOMListView'
                    break
                case 10:
                    this.currentComponent = 'WarehouseMissingMaterialPurchase'
                    break
                case 8:
                    this.currentComponent = 'PersonalInfo'
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