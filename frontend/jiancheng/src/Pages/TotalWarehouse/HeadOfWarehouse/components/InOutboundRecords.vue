<template>
    <el-tabs style="">
        <el-tab-pane label="入库记录">
            <InboundRecords :materialSupplierOptions="materialSupplierOptions" :warehouseOptions="warehouseOptions"/>
        </el-tab-pane>
        <el-tab-pane label="出库记录">
            <OutboundRecords />
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