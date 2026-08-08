<template>
    <el-container>
        <el-header class="app-header">
            <AllHeader></AllHeader>
        </el-header>
        <!--引用header-->
        <el-container class="app-body">
            <!-- 侧栏（头像区 + 内部滚动菜单） -->
            <el-aside class="app-aside">
                <div class="profile">
                    <el-avatar :icon="UserFilled" :size="80" />
                    <div class="profile-name">{{ userName }}</div>
                </div>

                <el-menu :default-active="defaultActive" class="app-menu" :unique-opened="true">
                    <el-menu-item index="order" @click="handleMenuClick('order')">
                        <span>订单查询</span>
                    </el-menu-item>
                    <el-menu-item index="orderShoeEdit" @click="handleMenuClick('orderShoeEdit')">
                        <span>订单鞋型修改</span>
                    </el-menu-item>
                    <el-menu-item index="lingerDashboard" @click="handleMenuClick('lingerDashboard')">
                        <span>滞留看板</span>
                    </el-menu-item>
                    <el-menu-item index="profile" @click="handleMenuClick('profile')">
                        <span>个人信息</span>
                    </el-menu-item>
                    <el-menu-item index="wechat" @click="handleMenuClick('wechat')">
                        <span>微信推送模板</span>
                    </el-menu-item>
                    <el-menu-item index="materialConsolidation" @click="handleMenuClick('materialConsolidation')">
                        <span>材料整改工具</span>
                    </el-menu-item>
                    <el-menu-item index="materialBatchEdit" @click="handleMenuClick('materialBatchEdit')">
                        <span>材料同步修改</span>
                    </el-menu-item>
                    <el-menu-item index="finishedStorageOverview" @click="handleMenuClick('finishedStorageOverview')">
                        <span>成品入出库概览</span>
                    </el-menu-item>
                    <el-menu-item index="stuckOrderRepair" @click="handleMenuClick('stuckOrderRepair')">
                        <span>断链订单修复</span>
                    </el-menu-item>
                    <el-menu-item index="usageModification" @click="handleMenuClick('usageModification')">
                        <span>用量修改</span>
                    </el-menu-item>
                    <el-menu-item index="purchaseApprovalAdjust" @click="handleMenuClick('purchaseApprovalAdjust')">
                        <span>采购核定差异调整</span>
                    </el-menu-item>
                    <el-menu-item index="userManagement" @click="handleMenuClick('userManagement')">
                        <span>用户管理</span>
                    </el-menu-item>
                    <el-menu-item index="staffManagement" @click="handleMenuClick('staffManagement')">
                        <span>人员管理</span>
                    </el-menu-item>
                    <el-menu-item index="departmentManagement" @click="handleMenuClick('departmentManagement')">
                        <span>部门管理</span>
                    </el-menu-item>
                    <el-menu-item index="logout" @click="logout">
                        <span>退出系统</span>
                    </el-menu-item>
                </el-menu>
            </el-aside>
            <el-main>
                <!--引用main-->
                <component :is="currentComponent" v-bind="currentProps"></component>
            </el-main>
        </el-container>
    </el-container>
</template>

<script>
import AllHeader from '@/components/AllHeader.vue'
import { UserFilled } from '@element-plus/icons-vue'
import axios from 'axios'
import OrderSearch from '../components/OrderSearch.vue'
import OrderShoeTypeManage from '../components/OrderShoeTypeManage.vue'
import LingerDashboard from '../components/LingerDashboard.vue'
import PersonalInfo from '@/components/PersonalInfo.vue'
import WechatTemplateManager from '@/Pages/System/WechatTemplateManager.vue'
import MaterialConsolidation from '../components/MaterialConsolidation.vue'
import MaterialBatchEdit from '../components/MaterialBatchEdit.vue'
import FinishedStorageOverview from '../components/FinishedStorageOverview.vue'
import StuckOrderRepair from '../components/StuckOrderRepair.vue'
import UsageModificationView from '@/Pages/UsageCalculation/components/UsageModificationView.vue'
import PurchaseApprovalAdjust from '../components/PurchaseApprovalAdjust.vue'
import UserManagementView from '@/Pages/HumanResourcesDepartment/components/UserManagementView.vue'
import StaffManagementView from '@/Pages/HumanResourcesDepartment/components/StaffManagementView.vue'
import DepartmentManagementView from '@/Pages/HumanResourcesDepartment/components/DepartmentManagementView.vue'
export default {
    components: {
        AllHeader,
        OrderSearch,
        OrderShoeTypeManage,
        LingerDashboard,
        PersonalInfo,
        WechatTemplateManager,
        MaterialConsolidation,
        MaterialBatchEdit,
        FinishedStorageOverview,
        StuckOrderRepair,
        UsageModificationView,
        PurchaseApprovalAdjust,
        UserManagementView,
        StaffManagementView,
        DepartmentManagementView
    },
    data() {
        return {
            UserFilled,
            currentComponent: 'OrderSearch',
            userName: '',
            currentProps: {}
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
            if (index === 'order') {
                this.currentComponent = 'OrderSearch'
            } else if (index === 'orderShoeEdit') {
                this.currentComponent = 'OrderShoeTypeManage'
            } else if (index === 'lingerDashboard') {
                this.currentComponent = 'LingerDashboard'
            } else if (index === 'profile') {
                this.currentComponent = 'PersonalInfo'
            } else if (index === 'wechat') {
                this.currentComponent = 'WechatTemplateManager'
            } else if (index === 'materialConsolidation') {
                this.currentComponent = 'MaterialConsolidation'
            } else if (index === 'materialBatchEdit') {
                this.currentComponent = 'MaterialBatchEdit'
            } else if (index === 'finishedStorageOverview') {
                this.currentComponent = 'FinishedStorageOverview'
            } else if (index === 'stuckOrderRepair') {
                this.currentComponent = 'StuckOrderRepair'
            } else if (index === 'usageModification') {
                this.currentComponent = 'UsageModificationView'
            } else if (index === 'purchaseApprovalAdjust') {
                this.currentComponent = 'PurchaseApprovalAdjust'
            } else if (index === 'userManagement') {
                this.currentComponent = 'UserManagementView'
            } else if (index === 'staffManagement') {
                this.currentComponent = 'StaffManagementView'
            } else if (index === 'departmentManagement') {
                this.currentComponent = 'DepartmentManagementView'
            }
        },
        async logout() {
            this.$router.push('/login')
            await this.$axios.post(`${this.$apiBaseUrl}/logout`)
            localStorage.removeItem('token')
            localStorage.removeItem('role')
        }
    }
}
</script>
