<template>
    <el-container class="app-shell">
        <el-header class="app-header">
            <AllHeader />
        </el-header>

        <el-container class="app-body">
            <el-aside class="app-aside">
                <div class="profile">
                    <el-avatar :icon="UserFilled" :size="80" class="profile-avatar" />
                    <div class="profile-name">{{ userName }}</div>
                </div>

                <!-- 这里增加 :class="menuDensityClass" -->
                <el-menu default-active="1" class="app-menu" :unique-opened="true" :class="menuDensityClass">
                    <el-menu-item index="1" @click="handleMenuClick(1)">任务看板</el-menu-item>
                    <el-menu-item index="2" @click="handleMenuClick(2)">调版分配与下发</el-menu-item>
                    <el-menu-item index="4" @click="handleMenuClick(4)">生产BOM用量填写审核</el-menu-item>
                    <el-menu-item index="5" @click="handleMenuClick(5)">退回任务列表</el-menu-item>
                    <el-menu-item index="3" @click="handleMenuClick(3)">订单查询</el-menu-item>
                    <el-menu-item index="8" @click="handleMenuClick(8)">个人信息</el-menu-item>
                    <el-menu-item index="9" @click="logout">退出系统</el-menu-item>
                </el-menu>
            </el-aside>

            <el-main class="app-main">
                <component :is="currentComponent" :departmentId="departmentId" />
            </el-main>
        </el-container>
    </el-container>
</template>

<script>
import AllHeader from '@/components/AllHeader.vue'
import { UserFilled } from '@element-plus/icons-vue'
import Dashboard from '../components/TechnicalManagerDashboard.vue'
import OrderSearch from '../components/OrderSearch.vue'
import PersonalInfo from '@/components/PersonalInfo.vue'
import AdjustList from '../components/AdjustList.vue'
import BOMReviewList from '../components/BOMReviewList.vue'
import RevertDashboard from '@/components/RevertDashboard.vue'
import axios from 'axios'
export default {
    components: {
        AllHeader,
        Dashboard,
        OrderSearch,
        PersonalInfo,
        AdjustList,
        BOMReviewList,
        RevertDashboard
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
