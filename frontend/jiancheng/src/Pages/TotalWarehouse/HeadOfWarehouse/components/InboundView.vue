<template>
    <el-tabs v-model="activeTab" tab-position="top" style="width: 100%;">
        <el-tab-pane label="原材料" name="原材料">
            <MaterialInbound :material-supplier-options="materialSupplierOptions"
                :material-type-options="materialTypeOptions" :materialNameOptions="materialNameOptions">
            </MaterialInbound>
        </el-tab-pane>
        <el-tab-pane label="复合材料" name="复合材料">
            <CompositeMaterialInbound :material-supplier-options="materialSupplierOptions"
            :material-type-options="materialTypeOptions" :materialNameOptions="materialNameOptions">
            </CompositeMaterialInbound>
        </el-tab-pane>
    </el-tabs>
</template>
<script>
import axios from 'axios';
import { ElMessage, ElMessageBox } from 'element-plus';
import MaterialInbound from './MaterialInbound.vue';
import CompositeMaterialInbound from './CompositeMaterialInbound.vue';
export default {
    components: {
        MaterialInbound,
        CompositeMaterialInbound
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