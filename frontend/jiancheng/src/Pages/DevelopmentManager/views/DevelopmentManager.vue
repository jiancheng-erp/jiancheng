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
            <span class="aside-brand-sub">开发管理</span>
          </div>
        </div>

        <!-- 菜单（内部滚动） -->
        <el-menu :default-active="activeIndex" class="app-menu" :unique-opened="true">
          <el-menu-item index="1" @click="handleMenuClick(1)">
            <el-icon><DataBoard /></el-icon>
            <span>任务看板</span>
          </el-menu-item>
          <el-menu-item index="2" @click="handleMenuClick(2)">
            <el-icon><DocumentAdd /></el-icon>
            <span>投产指令单创建</span>
          </el-menu-item>
          <el-menu-item index="9" @click="handleMenuClick(9)">
            <el-icon><DocumentChecked /></el-icon>
            <span>色卡确认</span>
          </el-menu-item>
          <el-menu-item index="10" @click="handleMenuClick(10)">
            <el-icon><Refresh /></el-icon>
            <span>退回任务列表</span>
          </el-menu-item>
          <el-menu-item index="3" @click="handleMenuClick(3)">
            <el-icon><Goods /></el-icon>
            <span>鞋型管理</span>
          </el-menu-item>
          <el-menu-item index="4" @click="handleMenuClick(4)">
            <el-icon><Search /></el-icon>
            <span>订单查询</span>
          </el-menu-item>
          <el-menu-item index="5" @click="handleMenuClick(5)">
            <el-icon><Management /></el-icon>
            <span>物料管理</span>
          </el-menu-item>
          <el-menu-item index="6" @click="handleMenuClick(6)">
            <el-icon><OfficeBuilding /></el-icon>
            <span>供应商管理</span>
          </el-menu-item>
          <el-menu-item index="7" @click="handleMenuClick(7)">
            <el-icon><DataLine /></el-icon>
            <span>绩效查询</span>
          </el-menu-item>
          <el-menu-item index="8" @click="handleMenuClick(8)">
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
import { UserFilled, Menu, DataBoard, DocumentAdd, DocumentChecked, Refresh, Goods, Search, Management, OfficeBuilding, DataLine, User } from '@element-plus/icons-vue'
import Dashboard from '../components/DevelopmentManagerDashboard.vue'
import ProductionOrderCreate from '../components/ProductionOrderCreate.vue'
import ColorCardConfirmation from '../components/ColorCardConfirmation.vue'
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
        Menu,
        DataBoard,
        DocumentAdd,
        DocumentChecked,
        Refresh,
        Goods,
        Search,
        Management,
        OfficeBuilding,
        DataLine,
        User,
        Dashboard,
        ProductionOrderCreate,
        ColorCardConfirmation,
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
                case 9:
                  this.currentComponent = 'ColorCardConfirmation'
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