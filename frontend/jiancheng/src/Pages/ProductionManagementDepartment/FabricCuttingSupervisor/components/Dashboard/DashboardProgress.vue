<template>
    <el-row :gutter="0">
        <el-col :span="12" :offset="0">
            <h1>全部处理中任务：</h1>
        </el-col>
    </el-row>
    <el-row :gutter="20">
        <el-col :span="4" :offset="19"><el-input v-model="searchOrder" placeholder="请输入订单号" size="default"
                :suffix-icon="Search" clearable @input="filterData"></el-input>
        </el-col>
    </el-row>
    <el-row :gutter="20" style="margin-top: 20px;">
        <el-col :span="24">
            <el-table :data="displayData" style="height: 500px" @row-dblclick="handleRowClick">
                <el-table-column prop="taskName" label="任务名称"></el-table-column>
                <el-table-column prop="orderId" label="订单号"></el-table-column>
                <el-table-column prop="createTime" label="订单创建时间"></el-table-column>
            </el-table>

        </el-col>
    </el-row>
</template>

<script setup>
import { Search } from '@element-plus/icons-vue'
import { ref } from 'vue'
import { handleRowClick } from '@/Pages/ProductionManagementDepartment/utils';
const props = defineProps(['inProgressTaskData'])
const searchOrder = ref("")
const displayData = ref(props.inProgressTaskData)
const emit = defineEmits(['backGrid', 'changeToPend', 'changeToProgress'])
const backToAll = () => {
    emit('backGrid')
}
const filterData = () => {
    if (!searchOrder.value) {
        displayData.value = props.inProgressTaskData
    }
    displayData.value = props.inProgressTaskData.filter(task => task.orderId.includes(searchOrder.value));
}
</script>