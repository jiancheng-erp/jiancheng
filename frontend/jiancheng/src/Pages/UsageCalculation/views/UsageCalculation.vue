<template>
    <el-container>
        <el-header>
            <AllHeader></AllHeader>
        </el-header> <!--引用header-->
        <el-container>
            <el-aside><!--引用aside-->
                <div>
                    <el-avatar :icon="UserFilled" :size="100" />
                </div>
                <div style="font-size: x-large;">
                    {{ userName }}
                </div>
                <div class="aside-menu" style="width: 100%; margin-top: 50px;">
                    <el-menu default-active="1" class="el-menu-vertical-demo">
                        <el-menu-item index="1" @click="handleMenuClick(1)">
                            <span>任务看板</span>
                        </el-menu-item>
                        <el-menu-item index="2" @click="handleMenuClick(2)">
                            <span>用量计算</span>
                        </el-menu-item>
                        <el-menu-item index="10" @click="handleMenuClick(10)">
                            <span>退回任务列表</span>
                        </el-menu-item>
                        <el-menu-item index="4" @click="handleMenuClick(4)">
                            <span>生产BOM用量填写</span>
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
                </div>
            </el-aside>
            <el-main> <!--引用main-->
                <component :is="currentComponent" :departmentId="departmentId"></component>
            </el-main>
        </el-container>
    </el-container>
</template>

<script>
import AllHeader from '@/components/AllHeader.vue'
import { UserFilled } from '@element-plus/icons-vue'
import Dashboard from '../components/UsageCalculationDashboard.vue';
import UsageCaculationView from '../components/UsageCalculationView.vue'
import OrderSearch from '../components/OrderSearch.vue';
import PersonalInfo from '@/components/PersonalInfo.vue';
import SecondBOMListView from '../components/SecondBOMListView.vue';
import RevertDashboard from '@/components/RevertDashboard.vue';
import axios from 'axios'


export default {
    components: {
        AllHeader,
        Dashboard,
        UsageCaculationView,
        OrderSearch,
        PersonalInfo,
        SecondBOMListView,
        RevertDashboard
    },
    data() {
        return {
            UserFilled,
            currentComponent: 'Dashboard',
            userName: '',
            departmentId: '14'
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
                    this.currentComponent = 'UsageCaculationView'
                    break
                case 3:
                    this.currentComponent = 'OrderSearch'
                    break
                case 4:
                    this.currentComponent = 'SecondBOMListView'
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