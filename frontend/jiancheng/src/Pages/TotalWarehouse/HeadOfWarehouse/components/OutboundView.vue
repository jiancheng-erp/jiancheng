<template>
    <el-tabs v-model="activeTab" tab-position="top" style="width: 100%;">
        <el-tab-pane label="原材料" name="原材料">
            <MaterialOutbound :material-supplier-options="materialSupplierOptions"
                :material-type-options="materialTypeOptions" :materialNameOptions="materialNameOptions">
            </MaterialOutbound>
        </el-tab-pane>
        <!-- <el-tab-pane label="复合材料" name="复合材料">
            <CompositeMaterialOutbound></CompositeMaterialOutbound>
        </el-tab-pane> -->
    </el-tabs>
</template>
<script>
import axios from 'axios';
import { ElMessage, ElMessageBox } from 'element-plus';
import MaterialOutbound from './MaterialOutbound.vue';
import CompositeMaterialOutbound from './CompositeMaterialOutbound.vue';
export default {
    components: {
        MaterialOutbound,
        CompositeMaterialOutbound
    },
    data() {
        return {
            activeTab: '原材料',
            tabs: [
                { label: "原材料", name: "原材料" },
                { label: "复合材料", name: "复合材料" }
            ],
            materialNameOptions: [],
            materialTypeOptions: [],
            materialSupplierOptions: []
        }
    },
    mounted() {
        this.getMaterialTypeOptions();
        this.getMaterialSupplierOptions();
        this.getMaterialNameOptions();
    },
    methods: {
        async getMaterialTypeOptions() {
            const response = await axios.get(`${this.$apiBaseUrl}/warehouse/warehousemanager/getallmaterialtypes`)
            this.materialTypeOptions = response.data
        },
        async getMaterialSupplierOptions() {
            const response = await axios.get(`${this.$apiBaseUrl}/warehouse/warehousemanager/getallsuppliernames`)
            this.materialSupplierOptions = response.data
        },
        async getMaterialNameOptions() {
            const params = { department: 0 }
            const response = await axios.get(`${this.$apiBaseUrl}/logistics/getallmaterialname`, { params })
            this.materialNameOptions = response.data
        },
    }
}
</script>