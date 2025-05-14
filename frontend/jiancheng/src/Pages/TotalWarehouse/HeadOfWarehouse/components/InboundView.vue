<template>
    <PurchaseInbound>
    </PurchaseInbound>
</template>
<script>
import axios from 'axios';
import { ElMessage, ElMessageBox } from 'element-plus';
import MaterialInbound from './MaterialInbound.vue';
import PurchaseInbound from './PurchaseInbound.vue';
import CompositeMaterialInbound from './CompositeMaterialInbound.vue';
export default {
    components: {
        MaterialInbound,
        CompositeMaterialInbound,
        PurchaseInbound
    },
    data() {
        return {
            activeTab: '原材料',
            tabs: [
                { label: "原材料", name: "原材料" },
                { label: "复合材料", name: "复合材料" }
            ],
            materialTypeOptions: [],
            materialSupplierOptions: [],
            unitOptions: [],
            activeOrderShoes: [],
        }
    },
    mounted() {
        this.getMaterialTypeOptions();
        this.getMaterialSupplierOptions();
        this.getUnitOptions();
        this.getActiveOrderShoes();
    },
    methods: {
        async getMaterialTypeOptions() {
            const response = await axios.get(`${this.$apiBaseUrl}/logistics/getallmaterialtypes`)
            this.materialTypeOptions = response.data
        },
        async getMaterialSupplierOptions() {
            const response = await axios.get(`${this.$apiBaseUrl}/warehouse/warehousemanager/getallsuppliernames`)
            this.materialSupplierOptions = response.data
        },
        async getUnitOptions() {
            const response = await axios.get(`${this.$apiBaseUrl}/logistics/getallunit`)
            this.unitOptions = response.data
        },
        async getActiveOrderShoes() {
            const response = await axios.get(`${this.$apiBaseUrl}/order/getactiveordershoes`)
            this.activeOrderShoes = response.data
        },
    }
}
</script>