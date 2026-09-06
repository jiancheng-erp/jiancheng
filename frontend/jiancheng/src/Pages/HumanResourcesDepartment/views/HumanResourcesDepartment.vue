<template>
  <el-container class="app-shell">
    <!-- 顶部 -->
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
            <span class="aside-brand-sub">人事管理</span>
          </div>
        </div>

        <!-- 菜单（内部滚动） -->
        <el-menu
          :default-active="activeIndex"
          class="app-menu"
          :unique-opened="true"
        >
          <el-menu-item index="2" @click="handleMenuClick(2)">
            <el-icon><User /></el-icon>
            <span>用户管理</span>
          </el-menu-item>
          <el-menu-item index="4" @click="handleMenuClick(4)">
            <el-icon><Avatar /></el-icon>
            <span>人员管理</span>
          </el-menu-item>
          <el-menu-item index="5" @click="handleMenuClick(5)">
            <el-icon><OfficeBuilding /></el-icon>
            <span>部门管理</span>
          </el-menu-item>
          <el-menu-item index="3" @click="handleMenuClick(3)">
            <el-icon><Postcard /></el-icon>
            <span>个人页面</span>
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
import { UserFilled, Menu, User, Avatar, OfficeBuilding, Postcard } from '@element-plus/icons-vue'
import UserManagementView from '../components/UserManagementView.vue';
import StaffManagementView from '../components/StaffManagementView.vue';
import DepartmentManagementView from '../components/DepartmentManagementView.vue';
import PersonalInfo from '@/components/PersonalInfo.vue';
import axios from 'axios'



export default {
    components: {
        AllHeader,
        Menu,
        User,
        Avatar,
        OfficeBuilding,
        Postcard,
        UserManagementView,
        StaffManagementView,
        DepartmentManagementView,
        PersonalInfo
    },
    data() {
        return {
            UserFilled,
            currentComponent: 'UserManagementView',
            userName: ''
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
                    this.currentComponent = 'UserManagementView'
                    break
                case 3:
                    this.currentComponent = 'PersonalInfo'
                    break
                case 4:
                    this.currentComponent = 'StaffManagementView'
                    break
                case 5:
                    this.currentComponent = 'DepartmentManagementView'
                    break
                case 9:
                    this.Logout()
                    break
            }
        },
        async Logout() {
            await axios.post(`${this.$apiBaseUrl}/logout`)
                .then(response => {
                    this.$router.push({name: 'login'})
                    localStorage.removeItem('token')
                    localStorage.removeItem('role')
                })
        }
    }
}
</script>