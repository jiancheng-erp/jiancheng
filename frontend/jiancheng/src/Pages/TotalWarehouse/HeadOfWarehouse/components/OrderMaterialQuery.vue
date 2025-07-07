<template>
    <el-dialog title="材料查询" v-model="localVisible" fullscreen destroy-on-close>
        <el-tabs :v-model="currentTab">
            <el-tab-pane label="BOM材料查询" lazy>
                <BOMInfo></BOMInfo>
            </el-tab-pane>
            <el-tab-pane label="采购材料查询" lazy>
                <PurchaseOrderInfo></PurchaseOrderInfo>
            </el-tab-pane>
            <el-tab-pane label="订单状态查询" lazy>
                <GeneralOrderSearch></GeneralOrderSearch>
            </el-tab-pane>
        </el-tabs>

    </el-dialog>
</template>
<script>
import PurchaseOrderInfo from './PurchaseOrderInfo.vue';
import LogisticInfo from '@/Pages/ProductionManagementDepartment/ProductionManagementDepartmentGeneral/components/LogisticInfo.vue';
import BOMInfo from './BOMInfo.vue';
import GeneralOrderSearch from '@/components/GeneralOrderSearchForWarehouse.vue';
export default {
    components: {
        LogisticInfo,
        BOMInfo,
        PurchaseOrderInfo,
        GeneralOrderSearch
    },
    props: {
        visible: {
            type: Boolean,
            required: true,
        },
    },
    emits: ['update-visible'],
    data() {
        return {
            localVisible: this.visible,
            isOrderMaterialQueryVis: false,
            orderRIdSearch: '',
            orderMaterialData: [],
            currentTab: '1'
        }
    },
    watch: {
        visible(newVal) {
            this.localVisible = newVal;
        },
        localVisible(newVal) {
            this.$emit("update-visible", newVal);
        },

    },
    methods: {
        handleClose() {
            this.$emit("update-visible", false);
        },
    }
}
</script>