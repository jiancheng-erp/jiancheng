<!-- eslint-disable vue/valid-v-for -->
<template><el-row :gutter="0">
        <el-col :span="12" :offset="0">
            <h1>待处理任务：</h1>
        </el-col>
    </el-row>
    <el-row class="u-mt-5" :gutter="20">
        <el-col :span="6" :offset="0" v-for="colIndex in 4">
            <el-card shadow="always" :body-style="{ padding: '10px' }" v-if="getPendingItem(colIndex)"
                @click="handleRowClick(getPendingItem(colIndex))">
                <template #header>
                    <div class="u-text-center">
                        {{ getPendingItem(colIndex).taskName }}
                    </div>
                </template>
                <div>订单号：{{ getPendingItem(colIndex).orderId }}</div>
                <div>订单创建时间：{{ getPendingItem(colIndex).createTime }}</div>
                <div>客户：{{ getPendingItem(colIndex).customerName }}</div>
            </el-card>

        </el-col>
    </el-row>
    <el-row class="u-mt-5" :gutter="0">
        <el-col :span="2" :offset="22">
            <el-button size="large" @click="displayPending">查看更多</el-button>

        </el-col>
    </el-row>
    <el-row :gutter="0">
        <el-col :span="12" :offset="0">
            <h1>处理中任务：</h1>
        </el-col>
    </el-row>
    <el-row class="u-mt-5" :gutter="20">
        <el-col :span="6" :offset="0" v-for="colIndex in 4">
            <el-card shadow="always" :body-style="{ padding: '10px' }" v-if="getinProgressItem(colIndex)"
                @click="handleRowClick(getinProgressItem(colIndex))">
                <template #header>
                    <div class="u-text-center">
                        <span>{{ getinProgressItem(colIndex).taskName }}</span>
                    </div>
                </template>
                <div>订单号：{{ getinProgressItem(colIndex).orderRId }}</div>
                <div>订单创建时间：{{ getinProgressItem(colIndex).createTime }}</div>
                <div>客户：{{ getinProgressItem(colIndex).customerName }}</div>
            </el-card>

        </el-col>
    </el-row>
    <el-row class="u-mt-5" :gutter="0">
        <el-col :span="2" :offset="22">
            <el-button size="large" @click="displayProgress">查看更多</el-button>

        </el-col>
    </el-row></template>
<script setup>
import { ref } from 'vue';
import { handleRowClick } from '@/Pages/ProductionManagementDepartment/utils';
const props = defineProps({
    'pendingTaskData': Array, 'inProgressTaskData': Array
})
console.log(props.inProgressTaskData)
const emit = defineEmits(['backGrid', 'changeToPend', 'changeToProgress'])

const getPendingItem = (colIndex) => {
    const index = colIndex - 1
    return index <= props.pendingTaskData.length ? props.pendingTaskData[index] : null
}

const getinProgressItem = (colIndex) => {
    const index = colIndex - 1
    return index < props.inProgressTaskData.length ? props.inProgressTaskData[index] : null
}

const displayPending = () => {
    emit('changeToPend')
}

const displayProgress = () => {
    emit('changeToProgress')
}

</script>