<template>
    <el-container>
        <el-header>
            <AllHeader></AllHeader>
        </el-header> <!--引用header-->
        <el-container>
            <el-aside width="250px"><!--引用aside-->
                <div>
                    <el-avatar :icon="UserFilled" :size="100" />
                </div>
                <div style="font-size: x-middle;">
                    {{ userName }}
                </div>
                <div class="aside-menu" style="width: 100%; margin-top: 50px;">
                    <el-menu default-active="2" class="el-menu-vertical-demo">
                        <el-menu-item index="2" @click="handleMenuClick(2)">
                            <span>订单管理</span>
                        </el-menu-item>
                        <el-menu-item index="10" @click="handleMenuClick(10)">
                            <span>订单出库</span>
                        </el-menu-item>
                        <el-menu-item index="11" @click="handleMenuClick(11)">
                            <span>历史（已完成）订单</span>
                        </el-menu-item>
                        <el-menu-item index="3" @click="handleMenuClick(3)">
                            <span>客户/配码管理</span>
                        </el-menu-item>
                        <el-menu-item index="4" @click="handleMenuClick(4)">
                            <span>鞋型管理</span>
                        </el-menu-item>
                        <el-menu-item index="5" @click="handleMenuClick(5)">
                            <span>码段管理</span>
                        </el-menu-item>
                        <el-menu-item index="6" @click="handleMenuClick(6)">
                            <span>订单导出</span>
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
                <component :is="currentComponent" v-bind="currentProps"></component>
            </el-main>
        </el-container>
    </el-container>
</template>

<script>
import AllHeader from '@/components/AllHeader.vue'
import { UserFilled } from '@element-plus/icons-vue'
import OrderManagement from '../components/OrderManagement.vue';
import CustomerManagement from '../components/CustomerManagement.vue';
import PersonalInfo from '@/components/PersonalInfo.vue';
import axios from 'axios'
import ShoeTypeManagement from '@/components/ShoeTypeManagement.vue';
import BatchInfoTypeManagement from '../components/BatchInfoTypeManagement.vue';
import OrderExport from '../components/OrderExport.vue';
import OutboundProduct from '@/Pages/TotalWarehouse/FinishedWarehouse/components/OutboundProduct.vue';
import HistoryOrder from '../components/HistoryOrder.vue';
export default {
    components: {
        AllHeader,
        OrderManagement,
        CustomerManagement,
        ShoeTypeManagement,
        BatchInfoTypeManagement,
        PersonalInfo,
        OrderExport,
        OutboundProduct,
        HistoryOrder
    },
    data() {
        return {
            UserFilled,
            currentComponent: 'OrderManagement',
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
            switch (index) {
                case 1:
                    this.currentComponent = 'Dashboard'
                    break
                case 2:
                    this.currentComponent = 'OrderManagement'
                    break
                case 3:
                    this.currentComponent = 'CustomerManagement'
                    break
                case 4:
                    this.currentComponent = 'ShoeTypeManagement'
                    break
                case 5:
                    this.currentComponent = "BatchInfoTypeManagement"
                    break
                case 6:
                    this.currentComponent = "OrderExport"
                    break
                case 8:
                    this.currentComponent = 'PersonalInfo'
                    break
                case 9:
                    this.$router.push('/')
                    break
                case 10:
                    this.currentComponent = 'OutboundProduct'
                    this.currentProps = { editable: false }
                    break
                case 11:
                    this.currentComponent = 'HistoryOrder'
                    this.currentProps = { editable: false }
                    break
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