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
                    <el-avatar :icon="UserFilled" :size="80" class="profile-avatar" />
                    <div class="profile-name">{{ userName }}</div>
                </div>

                <!-- 菜单：自动密度，自身滚动 -->
                <el-menu default-active="10" class="app-menu" :unique-opened="true">
                    <el-menu-item index="10" @click="handleMenuClick(10)">
                        <span>二次（总仓）采购订单创建</span>
                    </el-menu-item>
                    <el-menu-item index="13" @click="handleMenuClick(13)">
                        <span>订单查询</span>
                    </el-menu-item>
                    <el-menu-item index="14" @click="handleMenuClick(14)">
                        <span>按订单出库</span>
                    </el-menu-item>
                    <el-menu-item index="9" @click="handleMenuClick(9)">
                        <span>出入库审核</span>
                    </el-menu-item>
                    <el-menu-item index="16" @click="handleMenuClick(16)">
                        <span>出入库明细</span>
                    </el-menu-item>
                    <el-menu-item index="17" @click="handleMenuClick(17)">
                        <span>采购订单信息</span>
                    </el-menu-item>
                    <el-menu-item index="5" @click="handleMenuClick(5)">
                        <span>库存</span>
                    </el-menu-item>
                    <el-menu-item index="3" @click="handleMenuClick(3)">
                        <span>生产动态明细</span>
                    </el-menu-item>
                    <el-menu-item index="4" @click="handleMenuClick(4)">
                        <span>文件下载</span>
                    </el-menu-item>
                    <el-menu-item index="6" @click="handleMenuClick(6)">
                        <span>盘库功能</span>
                    </el-menu-item>
                    <el-menu-item index="18" @click="handleMenuClick(18)">
                        <span>缺失材料补采采购量录入</span>
                    </el-menu-item>
                    <el-menu-item index="15" @click="handleMenuClick(15)">
                        <span>供货商管理</span>
                    </el-menu-item>
                    <el-menu-item index="8" @click="handleMenuClick(8)">
                        <span>材料管理</span>
                    </el-menu-item>
                    <el-menu-item index="7" @click="handleMenuClick(7)">
                        <span>码段管理</span>
                    </el-menu-item>
                    <el-menu-item index="12" @click="handleMenuClick(12)">
                        <span>个人信息</span>
                    </el-menu-item>
                    <el-menu-item index="99" @click="logout()">
                        <span>退出系统</span>
                    </el-menu-item>
                </el-menu>
            </el-aside>

            <!-- 主内容 -->
            <el-main class="app-main">
                <component :is="currentComponent"></component>
            </el-main>
        </el-container>
    </el-container>
</template>

<script>
import AllHeader from '@/components/AllHeader.vue'
import InboundOutboundHistory from '../components/InboundOutboundHistory.vue'
import FileDownload from '../components/FileDownload.vue'
import OrderProgress from '@/Pages/ProductionManagementDepartment/ProductionSharedPages/OrderProgress.vue'
import { UserFilled } from '@element-plus/icons-vue'
import axios from 'axios'
import { logout } from '@/Pages/utils/logOut'
import FixedAssetsConsumablesView from '@/Pages/LogisticsControlDepartment/LogisticsControlManager/components/FixedAssetsConsumablesView.vue'
import LogisticsBatchTypeManagement from '@/components/LogisticsBatchInfoTypeManagement.vue'
import SecondPurchaseListView from '@/Pages/LogisticsControlDepartment/LogisticsControlManager/components/SecondPurchaseListView.vue'
import InOutboundRecords from '../components/InOutboundRecords.vue'
import MultiPurchaseIssue from '@/Pages/LogisticsControlDepartment/LogisticsControlManager/components/MultiPurchaseIssue.vue'
import PersonalInfo from '@/components/PersonalInfo.vue'
import OrderSearch from '@/Pages/LogisticsControlDepartment/LogisticsControlManager/components/OrderSearch.vue'
import MaterialManagementView from '@/Pages/LogisticsControlDepartment/LogisticsControlManager/components/MaterialManagementView.vue'
import SupplierManagement from '@/Pages/LogisticsControlDepartment/LogisticsControlManager/components/SupplierManagementView.vue'
import FinancialWarehouseDetail from '@/Pages/FinancialManager/components/FinancialWarehouseDetail.vue'
import MakeInventory from '../components/MakeInventory.vue'
import PurchaseOrderInfo from '../components/PurchaseOrderInfo.vue'
import OutboundByOrder from '../components/OutboundByOrder.vue'
import MissingPurchaseAmountInput from '@/Pages/LogisticsControlDepartment/LogisticsControlManager/components/MissingPurchaseAmountInput.vue'

export default {
    components: {
        AllHeader,
        InboundOutboundHistory,
        FileDownload,
        OrderProgress,
        FixedAssetsConsumablesView,
        LogisticsBatchTypeManagement,
        SecondPurchaseListView,
        InOutboundRecords,
        MultiPurchaseIssue,
        PersonalInfo,
        OrderSearch,
        MaterialManagementView,
        SupplierManagement,
        FinancialWarehouseDetail,
        MakeInventory,
        PurchaseOrderInfo,
        OutboundByOrder,
        MissingPurchaseAmountInput
    },
    data() {
        return {
            UserFilled,
            currentComponent: 'SecondPurchaseListView',
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
                case 10:
                    this.currentComponent = 'SecondPurchaseListView'
                    break
                case 11:
                    this.currentComponent = 'MultiPurchaseIssue'
                    break
                case 1:
                    this.currentComponent = 'InboundView'
                    break
                case 2:
                    this.currentComponent = 'OutboundView'
                    break
                case 3:
                    this.currentComponent = 'OrderProgress'
                    break
                case 4:
                    this.currentComponent = 'FileDownload'
                    break
                case 5:
                    this.currentComponent = 'InboundOutboundHistory'
                    break
                case 6:
                    this.currentComponent = 'MakeInventory'
                    break
                case 7:
                    this.currentComponent = 'LogisticsBatchTypeManagement'
                    break
                case 8:
                    this.currentComponent = 'MaterialManagementView'
                    break
                case 9:
                    this.currentComponent = 'InOutboundRecords'
                    break
                case 12:
                    this.currentComponent = 'PersonalInfo'
                    break
                case 13:
                    this.currentComponent = 'OrderSearch'
                    break
                case 14:
                    this.currentComponent = 'OutboundByOrder'
                    break
                case 15:
                    this.currentComponent = 'SupplierManagement'
                    break
                case 16:
                    this.currentComponent = 'FinancialWarehouseDetail'
                    break
                case 17:
                    this.currentComponent = 'PurchaseOrderInfo'
                    break
                case 18:
                    this.currentComponent = 'MissingPurchaseAmountInput'
                    break
            }
        }
    }
}
</script>
