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
          <el-avatar :icon="UserFilled" :size="100" />
          <div class="profile-name">{{ userName }}</div>
        </div>

        <!-- 菜单（内部滚动） -->
        <el-menu :default-active="activeIndex" class="app-menu" :unique-opened="true">
          <el-menu-item index="1" @click="handleMenuClick(1)">
            <span>任务看板</span>
          </el-menu-item>
          <el-menu-item index="2" @click="handleMenuClick(2)">
            <span>投产指令单创建</span>
          </el-menu-item>
          <el-menu-item index="10" @click="handleMenuClick(10)">
            <span>退回任务列表</span>
          </el-menu-item>
          <el-menu-item index="3" @click="handleMenuClick(3)">
            <span>鞋型管理</span>
          </el-menu-item>
          <el-menu-item index="4" @click="handleMenuClick(4)">
            <span>订单查询</span>
          </el-menu-item>
          <el-menu-item index="5" @click="handleMenuClick(5)">
            <span>物料管理</span>
          </el-menu-item>
          <el-menu-item index="6" @click="handleMenuClick(6)">
            <span>供应商管理</span>
          </el-menu-item>
          <el-menu-item index="7" @click="handleMenuClick(7)">
            <span>绩效查询</span>
          </el-menu-item>
          <el-menu-item index="8" @click="handleMenuClick(8)">
            <span>个人信息</span>
          </el-menu-item>
          <el-menu-item index="99" @click="logout">
            <span>退出系统</span>
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
import { UserFilled } from '@element-plus/icons-vue'
import Dashboard from '../components/DevelopmentManagerDashboard.vue'
import ProductionOrderCreate from '../components/ProductionOrderCreate.vue'
import ShoeManagement from '@/components/ShoeTypeManagement.vue'
import OrderSearch from '../components/OrderSearch.vue'
import MaterialManagement from '../components/MaterialManagementView.vue'
import SupplierManagement from '@/Pages/LogisticsControlDepartment/LogisticsControlManager/components/SupplierManagementView.vue'
import PersonalInfo from '@/components/PersonalInfo.vue'
import RevertDashboard from '@/components/RevertDashboard.vue'
import DevelopmentPerformanceManagement from '../components/DevelopmentPerformanceManagement.vue'
import axios from 'axios'


export default {
    components: {
        AllHeader,
        Dashboard,
        ProductionOrderCreate,
        ShoeManagement,
        OrderSearch,
        MaterialManagement,
        SupplierManagement,
        PersonalInfo,
        RevertDashboard,
        DevelopmentPerformanceManagement

    },
    data() {
        return {
            UserFilled,
            currentComponent: 'Dashboard',
            userName: '',
            departmentId: '7'
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
                    this.currentComponent = 'ProductionOrderCreate'
                    break
                case 3:
                    this.currentComponent = 'ShoeManagement'
                    break
                case 4:
                    this.currentComponent = 'OrderSearch'
                    break
                case 5:
                    this.currentComponent = 'MaterialManagement'
                    break
                case 6:
                    this.currentComponent = 'SupplierManagement'
                    break
                case 7:
                    this.currentComponent = 'DevelopmentPerformanceManagement'
                    break
                case 8:
                    this.currentComponent = 'PersonalInfo'
                    break
                case 10:
                    this.currentComponent = 'RevertDashboard'
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