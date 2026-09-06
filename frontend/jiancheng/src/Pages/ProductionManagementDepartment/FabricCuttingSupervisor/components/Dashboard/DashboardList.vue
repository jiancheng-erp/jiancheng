<template><el-row :gutter="0">
        <el-col :span="12" :offset="0">
            <h1>待处理任务：</h1>
        </el-col>
    </el-row>
    <el-row class="u-mt-5" :gutter="20">
        <el-col :span="24">
            <el-table class="u-h-200" :data="pendingTaskData" @row-dblclick="handleRowClick">
                <el-table-column prop="taskName" label="任务名称"></el-table-column>
                <el-table-column prop="orderId" label="订单号"></el-table-column>
                <el-table-column prop="createTime" label="订单创建时间"></el-table-column>
            </el-table>

        </el-col>
    </el-row>
    <el-row class="u-mt-5" :gutter="0">
        <el-col :span="2" :offset="22">
            <el-button size="large" @click="displayPending">查看更多</el-button>

        </el-col>
    </el-row>
    <el-row class="u-mt-5" :gutter="0">
        <el-col :span="12" :offset="0">
            <h1>处理中任务：</h1>
        </el-col>
    </el-row>
    <el-row class="u-mt-5" :gutter="20">
        <el-col :span="24">
            <el-table class="u-h-200" :data="inProgressTaskData" @row-dblclick="handleRowClick">
                <el-table-column prop="taskName" label="任务名称"></el-table-column>
                <el-table-column prop="orderId" label="订单号"></el-table-column>
                <el-table-column prop="createTime" label="订单创建时间"></el-table-column>
            </el-table>

        </el-col>
    </el-row>
    <el-row class="u-mt-5" :gutter="0">
        <el-col :span="2" :offset="22">
            <el-button size="large" @click="displayProgress">查看更多</el-button>

        </el-col>
    </el-row>
</template>

<script setup>
import { handleRowClick } from '@/Pages/ProductionManagementDepartment/utils';
const props = defineProps({
    'pendingTaskData': Array, 'inProgressTaskData': Array
})
const emit = defineEmits(['backGrid', 'changeToPend', 'changeToProgress'])
const displayPending = () => {
    emit('changeToPend')
}
const displayProgress = () => {
    emit('changeToProgress')
}
</script>