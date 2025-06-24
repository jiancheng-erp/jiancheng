<template>
    <el-tabs style="">
        <!-- 如果character不是总仓文员，或者总仓文员身份是出入库文员，则可以查询自己的入库记录 -->
        <el-tab-pane v-if="role !== '23' || (role === '23' && ['35', '39'].includes(staffId))" label="入库记录"> 
            <InboundRecords :materialSupplierOptions="materialSupplierOptions" :warehouseOptions="warehouseOptions"/>
        </el-tab-pane>
        <el-tab-pane label="出库记录">
            <OutboundRecords :materialSupplierOptions="materialSupplierOptions" :warehouseOptions="warehouseOptions"/>
        </el-tab-pane>
    </el-tabs>
</template>
<script>
import InboundRecords from './InboundRecords.vue'
import OutboundRecords from './OutboundRecords.vue'
import axios from 'axios'
export default {
    components: {
        InboundRecords,
        OutboundRecords
    },
    data() {
        return {
            materialSupplierOptions: [],
            warehouseOptions: [],
            role: localStorage.getItem('role'),
            staffId: localStorage.getItem('staffid'),
        }
    },
    mounted() {
        this.getMaterialSupplierOptions()
        this.getWarehouseOptions()
    },
    methods: {
        async getMaterialSupplierOptions() {
            const response = await axios.get(`${this.$apiBaseUrl}/warehouse/warehousemanager/getallsuppliernames`)
            this.materialSupplierOptions = response.data
        },
        async getWarehouseOptions() {
            const response = await axios.get(`${this.$apiBaseUrl}/logistics/allwarehousenames`)
            this.warehouseOptions = response.data
        },
    },
}
</script>