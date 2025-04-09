<template>
    <el-tabs style="">
        <el-tab-pane label="入库记录">
            <InboundRecords />
        </el-tab-pane>
        <el-tab-pane label="出库记录">
            <OutboundRecords />
        </el-tab-pane>
    </el-tabs>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { ref, onMounted, getCurrentInstance } from 'vue'
import axios from 'axios'
import useSetAxiosToken from '../hooks/useSetAxiosToken'
import { ElRow } from 'element-plus'
import InboundRecords from './InboundDetail.vue'
import OutboundRecords from './OutboundDetail.vue'
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


