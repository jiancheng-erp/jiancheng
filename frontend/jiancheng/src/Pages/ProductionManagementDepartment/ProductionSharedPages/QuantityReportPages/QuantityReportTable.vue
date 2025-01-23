<template>
    <el-table :data="tableData" border :style="{ marginBottom: '20px' }" default-expand-all>
        <el-table-column type="expand">
            <template #default="meta">
                <el-table :data="meta.row.productionLinesAmount">
                    <el-table-column prop="productionLineName" label="线号"></el-table-column>
                    <el-table-column label="生产数量">
                        <template #default="scope">
                            <el-input-number v-if="props.editable" v-model="scope.row.reportAmount" :min="0"
                                :max="scope.row.remainAmount" />
                            <span v-else>{{ scope.row.reportAmount }}</span>
                        </template>
                    </el-table-column>
                </el-table>
            </template>
        </el-table-column>
        <el-table-column prop="colorName" label="颜色"></el-table-column>
        <el-table-column prop="toDateAmount" label="当日数量" />
        <el-table-column prop="producedAmount" label="已审批数量" />
        <el-table-column prop="totalAmount" label="目标数量" />
        <el-table-column prop="remainingAmount" label="剩余数量(目标数量-已审批数量)" />
    </el-table>
</template>

<script setup>
import { defineModel } from 'vue';
const props = defineProps(['orderShoeId', 'editable'])
const tableData = defineModel('tableData')
</script>