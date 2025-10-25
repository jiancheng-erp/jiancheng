<template>
    <el-tabs style="">
        <el-tab-pane label="总仓库存">
        <el-tabs>
            <el-tab-pane label="实时库存">
                <Inventory />
            </el-tab-pane>
            <el-tab-pane label="历史库存">
                <MaterialStorageSnapshot />
            </el-tab-pane>
        </el-tabs>
        </el-tab-pane>
        <el-tab-pane label="半成品仓库库存">
            <SemifinishedInOutHistory />
        </el-tab-pane>
        <el-tab-pane label="成品仓库库存">
            <FinishedInOutHistory />
        </el-tab-pane>
        <el-tab-pane label="成品仓库库存型号视图">
            <FinishedInherit />
        </el-tab-pane>
        <el-tab-pane label="成品仓库入出库明细">
            <FinishedDetail />
        </el-tab-pane>
        <el-tab-pane label="成品仓库型号入出库明细">
            <FinishedInheritDetail />
        </el-tab-pane>
    </el-tabs>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { ref, onMounted, getCurrentInstance } from 'vue'
import axios from 'axios'
import useSetAxiosToken from '../hooks/useSetAxiosToken'
import { ElRow } from 'element-plus'
import Inventory from './FinancialInventory.vue'
import OutboundRecords from './OutboundDetail.vue'
import SemifinishedInOutHistory from '@/Pages/TotalWarehouse/SemifinishedWarehouse/components/SemifinishedInOutHistory.vue'
import FinishedInOutHistory from '@/Pages/TotalWarehouse/FinishedWarehouse/components/FinishedInOutHistory.vue'
import FinishedInherit from '@/Pages/TotalWarehouse/FinishedWarehouse/components/FinishedInherit.vue'
import FinishedDetail from '@/Pages/TotalWarehouse/FinishedWarehouse/components/FinishedDetail.vue'
import FinishedInheritDetail from '@/Pages/TotalWarehouse/FinishedWarehouse/components/FinishedInheritDetail.vue'
import MaterialStorageSnapshot from './MaterialStorageSnapshot.vue'
const { setAxiosToken } = useSetAxiosToken()
const router = useRouter()

// const shortcuts: [
//                 {
//                     text: '过去一周',
//                     value: () => {
//                         const end = new Date()
//                         const start = new Date()
//                         start.setTime(start.getTime() - 3600 * 1000 * 24 * 7)
//                         return [start, end]
//                     }
//                 },
//                 {
//                     text: '过去一月',
//                     value: () => {
//                         const end = new Date()
//                         const start = new Date()
//                         start.setTime(start.getTime() - 3600 * 1000 * 24 * 30)
//                         return [start, end]
//                     }
//                 }
//             ]
interface WarehouseEntity{
    warehouseId:number
    warehouseName:string
}


const $api_baseUrl = getCurrentInstance().appContext.config.globalProperties.$apiBaseUrl

onMounted(() => {
})

</script>
<style>

    
</style>


