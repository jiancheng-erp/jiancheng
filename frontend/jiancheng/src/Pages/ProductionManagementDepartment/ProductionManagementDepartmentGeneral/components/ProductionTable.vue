<template>
    <el-table :data="data" style="width: 100%" v-loading="loading" element-loading-text="Loading..." border default-expand-all>
        <el-table-column type="expand" width="65" v-if="reportType === 'productionAmount'">
            <template #default="meta">
                <el-table :data="meta.row.productionLines" border stripe style="width: 100%">
                    <el-table-column width="55"></el-table-column>
                    <el-table-column align="center" prop="productionLineName" label="车间线号" />
                    <el-table-column align="center" :label="productionAmountLabel" prop="productionLineAmount"/>
                </el-table>
            </template>
        </el-table-column>
        <el-table-column align="center" :prop="productionTeamProp" :label="productionTeamLabel"></el-table-column>
        <el-table-column align="center" prop="outsourceStatus" label="状态" v-if="reportType === 'outsourceAmount'"></el-table-column>
        <el-table-column align="center" :prop="productionTotalAmountProp" label="产量"></el-table-column>
    </el-table>
</template>

<script>
import { computed } from 'vue';
import { ElTable, ElTableColumn } from 'element-plus';

export default {
    name: 'ProductionTable',
    components: {
        ElTable,
        ElTableColumn,
    },
    props: {
        data: {
            type: Array,
            required: true,
        },
        loading: {
            type: Boolean,
            default: false,
        },
        reportType: {
            type: String,
            required: true,
        },
    },
    setup(props) {

        const productionAmountLabel = computed(() => {
            if (props.reportType === 'productionAmount') return '日期范围产量';
            return 'Production Amount';
        });

        const productionTeamLabel = computed(() => {
            if (props.reportType === 'productionAmount') return '车间';
            if (props.reportType === 'outsourceAmount') return '外包工厂';
            return 'Production Amount';
        });

        const productionTeamProp = computed(() => {
            if (props.reportType === 'productionAmount') return 'team';
            if (props.reportType === 'outsourceAmount') return 'outsourceFactory';
            return 'Production Amount';
        });

        const productionTotalAmountProp = computed(() => {
            if (props.reportType === 'productionAmount') return 'totalAmount';
            if (props.reportType === 'outsourceAmount') return 'outsourceAmount';
            return 'Production Amount';
        });

        return {
            productionAmountLabel,
            productionTeamLabel,
            productionTeamProp,
            productionTotalAmountProp,
        };
    },
};
</script>

<style scoped>
/* Add any specific styles if needed */
</style>