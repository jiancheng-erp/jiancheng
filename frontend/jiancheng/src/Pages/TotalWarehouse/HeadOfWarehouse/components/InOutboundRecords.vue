<template>
    <el-tabs style="">
        <el-tab-pane label="入库记录">
            <InboundRecords :materialSupplierOptions="materialSupplierOptions"/>
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
        }
    },
    mounted() {
        this.getMaterialSupplierOptions()
    },
    methods: {
        async getMaterialSupplierOptions() {
            const response = await axios.get(`${this.$apiBaseUrl}/warehouse/warehousemanager/getallsuppliernames`)
            this.materialSupplierOptions = response.data
        },
    },
}
</script>