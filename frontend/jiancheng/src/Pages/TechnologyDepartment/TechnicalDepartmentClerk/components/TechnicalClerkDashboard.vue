<template>
    <el-row :gutter="20">
        <el-col :span="24" :offset="0" style="font-size: xx-large; text-align: center;">任务看板</el-col>
    </el-row>

    <el-row :gutter="0">
        <el-col :span="5" :offset="20">
            <el-button-group>
                <el-button size="default" @click="changeToGrid" :icon="Grid">卡片显示</el-button>
                <el-button size="default" @click="changeToList" :icon="Memo">列表显示</el-button>
            </el-button-group>

        </el-col>


    </el-row>
    <component :is="components[currentDash]" :pendingTaskData="pendingData" :inProgressTaskData="inProgressData" @backGrid="changeToGrid"
    @changeToPend="changeToPend" @changeToProgress="changeToProgress">
    </component>
</template>


<script setup>

import { onMounted, ref, getCurrentInstance } from 'vue';
import axios from 'axios';

import { Grid, Memo } from '@element-plus/icons-vue'
import DashboardGrid from './Dashboard/DashboardGrid.vue';
import DashboardList from './Dashboard/DashboardList.vue'
import DashboardPend from './Dashboard/DashboardListPend.vue'
import DashboardProgress from './Dashboard/DashboardListProgress.vue'

const proxy = getCurrentInstance()
const apiBaseUrl = proxy.appContext.config.globalProperties.$apiBaseUrl

const components = {
        DashboardGrid,
        DashboardList,
        DashboardPend,
        DashboardProgress
}
const pendingData = ref([])
const inProgressData = ref([])

onMounted(()=> {
    const firstBomStatus = 2
    const secondBomStatus = 11
    const params = {
        ordershoestatus : firstBomStatus
    };


    axios.get(`${apiBaseUrl}/order/getprodordershoebystatus`, {params}).then(response => {
        const firstBomPending = response.data.pendingOrders
        const firstBomProgress = response.data.inProgressOrders
        firstBomPending.forEach(element => {
            element['taskName'] = "一次BOM填写"
            pendingData.value.push(element)
        });
        firstBomProgress.forEach(element => {
            element['taskName'] = "一次BOM填写"
            inProgressData.value.push(element)
        });
    })
    params['ordershoestatus']  = secondBomStatus
    axios.get(`${apiBaseUrl}/order/getprodordershoebystatus`, {params}).then(response => {
        const secondBomPending = response.data.pendingOrders
        const secondBomProgress = response.data.inProgressOrders
        secondBomPending.forEach(element => {
            element['taskName']  = "二次BOM填写"
            pendingData.value.push(element)
        });
        secondBomProgress.forEach(element => {
            element['taskName'] = "二次BOM填写"
            inProgressData.value.push(element)
        });
    })
    console.log(inProgressData)
    console.log(pendingData)
})
const currentDash = ref('DashboardGrid')
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



