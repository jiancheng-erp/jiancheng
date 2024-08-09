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
                    物控经理-姓名
                </div>
                <div class="aside-menu" style="width: 100%; margin-top: 50px;">
                    <el-menu default-active="1" class="el-menu-vertical-demo">
                        <el-menu-item index="1" @click="handleMenuClick(1)">
                            <span>任务看板</span>
                        </el-menu-item>
                        <el-menu-item index="2" @click="handleMenuClick(2)">
                            <span>一次采购订单生成</span>
                        </el-menu-item>
                        <el-menu-item index="3" @click="handleMenuClick(3)">
                            <span>二次采购订单生成</span>
                        </el-menu-item>
                        <el-menu-item index="4" @click="handleMenuClick(4)">
                            <span>耗材/固定资产采购订单生成</span>
                        </el-menu-item>
                        <el-menu-item index="5" @click="handleMenuClick(5)">
                            <span>材料管理</span>
                        </el-menu-item>
                        <el-menu-item index="6" @click="handleMenuClick(6)">
                            <span>仓库管理</span>
                        </el-menu-item>
                        <el-menu-item index="7" @click="handleMenuClick(7)">
                            <span>供货商管理</span>
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
import Dashboard from '../components/LogisticsManagerDashboard.vue'
import FirstPurchase from '../components/FirstPurchaseListView.vue'
import SecondPurchase from '../components/SecondPurchaseListView.vue'
import FixedAssets from '../components/FixedAssetsConsumablesView.vue'
import MaterialManagement from '../components/MaterialManagementView.vue'
import WarehouseManagement from '../components/WarehouseManagementView.vue'
import SupplierManagement from '../components/SupplierManagementView.vue'
import TestPage from '../components/TestPage.vue'
import { UserFilled } from '@element-plus/icons-vue'
export default {
    components: {
        AllHeader,
        Dashboard,
        FirstPurchase,
        SecondPurchase,
        FixedAssets,
        MaterialManagement,
        WarehouseManagement,
        SupplierManagement,
        TestPage
    },
    data() {
        return {
            UserFilled,
            currentComponent:'Dashboard'
        }
    },
    methods: {
        handleMenuClick(index){
            console.log(index)
            switch(index) {
                case 1:
                    this.currentComponent = 'Dashboard'
                    break
                case 2:
                    this.currentComponent = 'FirstPurchase'
                    break
                case 3:
                    this.currentComponent = 'SecondPurchase'
                    break
                case 4:
                    this.currentComponent = 'FixedAssets'
                    break
                case 5:
                    this.currentComponent = 'MaterialManagement'
                    break
                case 6:
                    this.currentComponent = 'WarehouseManagement'
                    break
                case 7:
                    this.currentComponent = 'SupplierManagement'
                    break
                case 10:
                    this.currentComponent = 'TestPage' 
            }
        }
    }
}
</script>