<template>
    <el-container>
        <el-header>
            <AllHeader></AllHeader>
        </el-header> <!--引用header-->
        <el-container>
            <el-aside width="280px"><!--引用aside-->
                <div>
                    <el-avatar :icon="UserFilled" :size="100" />
                </div>
                <div style="font-size: x-large;">
                    {{ userName }}
                </div>
                <div class="aside-menu" style="width: 100%; margin-top: 50px;">
                    <el-menu default-active="10" class="el-menu-vertical-demo">
                        <el-menu-item index="10" @click="handleMenuClick(10)">
                            <span>二次（总仓）采购订单创建</span>
                        </el-menu-item>
                        <el-menu-item index="13" @click="handleMenuClick(13)">
                            <span>订单查询</span>
                        </el-menu-item>
                        <!-- <el-menu-item index="11" @click="handleMenuClick(11)">
                            <span>批量采购订单生成及下发</span>
                        </el-menu-item> -->
                        <!-- <el-menu-item index="1" @click="handleMenuClick(1)">
                            <span>多码采购入库</span>
                        </el-menu-item>
                        <el-menu-item index="2" @click="handleMenuClick(2)">
                            <span>材料待出库</span>
                        </el-menu-item> -->
                        <el-menu-item index="9" @click="handleMenuClick(9)">
                            <span>出入库记录</span>
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
                        <!-- <el-menu-item index="6" @click="handleMenuClick(6)">
                            <span>独立采购</span>
                        </el-menu-item> -->
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
                        <el-menu-item index="14" @click="logout">
                            <span>退出系统</span>
                        </el-menu-item>
                    </el-menu>
                </div>
            </el-aside>
            <el-main> <!--引用main-->
                <component :is="currentComponent"></component>
            </el-main>
        </el-container>
    </el-container>

</template>

<script>
import AllHeader from '@/components/AllHeader.vue'
import MaterialInbound from '../components/MaterialInbound.vue'
import InboundOutboundHistory from '../components/InboundOutboundHistory.vue'
import MaterialOutbound from '../components/MaterialOutbound.vue'
import FileDownload from '../components/FileDownload.vue'
import OrderProgress from '@/Pages/ProductionManagementDepartment/ProductionSharedPages/OrderProgress.vue'
import { UserFilled } from '@element-plus/icons-vue'
import axios from 'axios'
import { logout } from '@/Pages/utils/logOut'
import InboundView from '../components/InboundView.vue'
import OutboundView from '../components/OutboundView.vue'
import FixedAssetsConsumablesView from '@/Pages/LogisticsControlDepartment/LogisticsControlManager/components/FixedAssetsConsumablesView.vue'
import LogisticsBatchTypeManagement from '@/components/LogisticsBatchInfoTypeManagement.vue'
import SecondPurchaseListView from '@/Pages/LogisticsControlDepartment/LogisticsControlManager/components/SecondPurchaseListView.vue'
import InOutboundRecords from '../components/InOutboundRecords.vue'
import MultiPurchaseIssue from '@/Pages/LogisticsControlDepartment/LogisticsControlManager/components/MultiPurchaseIssue.vue'
import PersonalInfo from '@/components/PersonalInfo.vue'
import OrderSearch from '@/Pages/LogisticsControlDepartment/LogisticsControlManager/components/OrderSearch.vue'
import MaterialManagementView from '@/Pages/LogisticsControlDepartment/LogisticsControlManager/components/MaterialManagementView.vue'
import SupplierManagement from '@/Pages/LogisticsControlDepartment/LogisticsControlManager/components/SupplierManagementView.vue'

export default {
    components: {
        AllHeader,
        MaterialInbound,
        MaterialOutbound,
        InboundOutboundHistory,
        FileDownload,
        OrderProgress,
        InboundView,
        OutboundView,
        FixedAssetsConsumablesView,
        LogisticsBatchTypeManagement,
        SecondPurchaseListView,
        InOutboundRecords,
        MultiPurchaseIssue,
        PersonalInfo,
        OrderSearch,
        MaterialManagementView,
        SupplierManagement
    },
    data() {
        return {
            UserFilled,
            currentComponent:'SecondPurchaseListView',
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
        handleMenuClick(index){
            switch(index) {
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
                    this.currentComponent = 'FixedAssetsConsumablesView'
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
                case 15:
                    this.currentComponent = 'SupplierManagement'
                    break
            }
        }
    }
}
</script>