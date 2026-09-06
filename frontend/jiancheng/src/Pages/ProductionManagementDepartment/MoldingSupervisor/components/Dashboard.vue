<template>
    <el-row :gutter="20">
        <el-col class="u-page-title" :span="24" :offset="0">任务看板</el-col>
    </el-row>
    <el-row :gutter="0">
        <el-col :span="4" :offset="20">
            <el-button-group>
                <el-button size="default" @click="changeToGrid" :icon="Grid">卡片显示</el-button>
                <el-button size="default" @click="changeToList" :icon="Memo">列表显示</el-button>
            </el-button-group>
        </el-col>
    </el-row>
    <component :is="components[currentDash]" :pendingTaskData="textData" :inProgressTaskData="textData2"
        @backGrid="changeToGrid" @changeToPend="changeToPend" @changeToProgress="changeToProgress">
    </component>
</template>

<script setup>
import { ref } from 'vue';
import { Grid, Memo } from '@element-plus/icons-vue'
import DashboardGrid from './Dashboard/DashboardGrid.vue';
import DashboardList from './Dashboard/DashboardList.vue'
import DashboardPend from './Dashboard/DashboardPend.vue'
import DashboardProgress from './Dashboard/DashboardProgress.vue'
const currentDash = ref('DashboardGrid')
const components = {
    DashboardGrid,
    DashboardList,
    DashboardPend,
    DashboardProgress
}
const textData = [
    {
        taskName: "工价填报",
        orderId: "K24-024 2111620",
        createTime: "2024-06-10",
        prevTime: "2024-06-10 18:00:00",
        prevDepart: "技术部",
        prevUser: "XXX"
    },
    {
        taskName: "数量填写",
        orderId: "K24-025 2111622",
        createTime: "2024-06-10",
        prevTime: "2024-06-10 18:00:00",
        prevDepart: "技术部",
        prevUser: "XXX"
    },
    {
        taskName: "工价填报",
        orderId: "K24-021 2111620",
        createTime: "2024-06-10",
        prevTime: "2024-06-10 18:00:00",
        prevDepart: "技术部",
        prevUser: "XXX"
    },
    {
        taskName: "数量填写",
        orderId: "K24-021 2111620",
        createTime: "2024-06-10",
        prevTime: "2024-06-10 18:00:00",
        prevDepart: "技术部",
        prevUser: "XXX"
    },
    {
        taskName: "工价填报",
        orderId: "K24-021 2111620",
        createTime: "2024-06-10",
        prevTime: "2024-06-10 18:00:00",
        prevDepart: "技术部",
        prevUser: "XXX"
    },
    {
        taskName: "数量填写",
        orderId: "K24-021 2111620",
        createTime: "2024-06-10",
        prevTime: "2024-06-10 18:00:00",
        prevDepart: "技术部",
        prevUser: "XXX"
    },
]
const textData2 = [
    {
        taskName: "工价填报",
        orderId: "K24-021 2111628",
        createTime: "2024-06-10",
        prevTime: "2024-06-10 18:00:00",
        prevDepart: "技术部",
        prevUser: "XXX"
    },
    {
        taskName: "数量填写",
        orderId: "K24-021 2111620",
        createTime: "2024-06-10",
        prevTime: "2024-06-10 18:00:00",
        prevDepart: "技术部",
        prevUser: "XXX"
    },
]
const changeToGrid = () => {
    currentDash.value = 'DashboardGrid'
}
const changeToList = () => {
    currentDash.value = 'DashboardList'
}
const changeToPend = () => {
    currentDash.value = 'DashboardPend'
}
const changeToProgress = () => {
    currentDash.value = 'DashboardProgress'
}
</script>
