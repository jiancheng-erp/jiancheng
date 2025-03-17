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
import DashboardGrid from '@/components/Dashboard/DashboardGrid.vue';
import DashboardList from '@/components/Dashboard/DashboardList.vue';
import DashboardListPend from '@/components/Dashboard/DashboardListPend.vue';
import DashboardListProgress from '@/components/Dashboard/DashboardListProgress.vue';

const proxy = getCurrentInstance()
const apiBaseUrl = proxy.appContext.config.globalProperties.$apiBaseUrl

const components = {
        DashboardGrid,
        DashboardList,
        DashboardListPend,
        DashboardListProgress
}
const pendingData = ref([])
const inProgressData = ref([])

onMounted(()=> {
    const firstBomStatus = 9
    const params = {
        ordershoestatus : firstBomStatus
    };


    axios.get(`${apiBaseUrl}/order/getprodordershoebystatus`, {params}).then(response => {
        const firstBomPending = response.data.pendingOrders
        const firstBomProgress = response.data.inProgressOrders
        firstBomPending.forEach(element => {
            element['taskName'] = "技术部调版分配"
            element['taskURL'] = `${window.location.origin}/processsheet/orderid=${element.orderId}`;
            pendingData.value.push(element)
        });
        firstBomProgress.forEach(element => {
            element['taskName'] = "技术部调版分配"
            element['taskURL'] = `${window.location.origin}/processsheet/orderid=${element.orderId}`;
            inProgressData.value.push(element)
        });
    })
})
const currentDash = ref('DashboardGrid')
const changeToGrid = () => {
    currentDash.value = 'DashboardGrid'
}
const changeToList = () => {
    currentDash.value = 'DashboardList'
}
const changeToPend = () => {
    currentDash.value = 'DashboardListPend'
}
const changeToProgress = () => {
    currentDash.value = 'DashboardListProgress'
}
</script>



