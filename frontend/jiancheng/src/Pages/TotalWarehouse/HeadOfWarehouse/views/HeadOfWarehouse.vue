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
                    总仓经理-姓名
                </div>
                <div class="aside-menu" style="width: 100%; margin-top: 50px;">
                    <el-menu default-active="1" class="el-menu-vertical-demo">
                        <el-menu-item index="1" @click="handleMenuClick(1)">
                            <span>材料统一入库</span>
                        </el-menu-item>
                        <el-menu-item index="2" @click="handleMenuClick(2)">
                            <span>出/入库历史</span>
                        </el-menu-item>
                        <el-menu-item index="3" @click="handleMenuClick(3)">
                            <span>材料出库</span>
                        </el-menu-item>
                        <el-menu-item index="4" @click="handleMenuClick(4)">
                            <span>半成品入库/出库</span>
                        </el-menu-item>
                        <el-menu-item index="5" @click="handleMenuClick(5)">
                            <span>成品仓入库/出库</span>
                        </el-menu-item>
                        <el-menu-item index="8">
                            <span>个人信息</span>
                        </el-menu-item>
                        <el-menu-item index="9">
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
import Dashboard from '../components/HeadOfWarehouseDashboard.vue'
import FirstWarehousing from '../components/FirstWarehousingListView.vue'
import SecondWarehousing from '../components/SecondPurchaseListView.vue'
import AllInstock from '../components/AllInstock.vue'
import InstockOutstockHistory from '../components/InstockOutstockHistory.vue'
import SemiInstockOutstock from '../components/SemiInstockOutstock.vue'
import FinishedInstockOutstock from '../components/FinishedInstockOutstock.vue'
import AllOutStock from '../components/AllOutStock.vue'
import { UserFilled } from '@element-plus/icons-vue'
export default {
    components: {
        AllHeader,
        Dashboard,
        FirstWarehousing,
        SecondWarehousing,
        AllInstock,
        AllOutStock,
        InstockOutstockHistory,
        SemiInstockOutstock,
        FinishedInstockOutstock
    },
    data() {
        return {
            UserFilled,
            currentComponent:'AllInstock'
        }
    },
    methods: {
        handleMenuClick(index){
            console.log(index)
            switch(index) {
                case 1:
                    this.currentComponent = 'AllInstock'
                    break
                case 2:
                    this.currentComponent = 'InstockOutstockHistory'
                    break
                case 3:
                    this.currentComponent = 'AllOutStock'
                    break
                case 4:
                    this.currentComponent = 'SemiInstockOutstock'
                    break
                case 5:
                    this.currentComponent = 'FinishedInstockOutstock'
                    break
                case 6:
                    this.currentComponent = 'WarehouseManagement'
                    break
                case 7:
                    this.currentComponent = 'SupplierManagement'
                    break
                case 8:
                    this.currentComponent = 'AllInstock'
                    break
                case 10:
                    this.currentComponent = 'TestPage' 
            }
        }
    }
}
</script>