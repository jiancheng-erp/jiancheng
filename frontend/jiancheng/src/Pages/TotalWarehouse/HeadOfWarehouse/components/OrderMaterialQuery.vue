<template>
    <el-dialog title="订单材料查询" v-model="localVisible" fullscreen destroy-on-close>
        <LogisticInfo></LogisticInfo>
    </el-dialog>
</template>
<script>
import LogisticInfo from '@/Pages/ProductionManagementDepartment/ProductionManagementDepartmentGeneral/components/LogisticInfo.vue';
export default {
    components: {
        LogisticInfo,
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
        searchMaterialByOrderRId() {
            console.log(this.orderRIdSearch);
        },
        handleClose() {
            this.$emit("update-visible", false);
        },
    }
}
</script>