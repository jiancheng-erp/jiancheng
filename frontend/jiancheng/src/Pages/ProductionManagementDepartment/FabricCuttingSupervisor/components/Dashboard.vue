<template>
    <el-row :gutter="20">
        <el-col :span="24" :offset="0" style="font-size: xx-large; text-align: center;">任务看板</el-col>
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
import { onMounted, ref } from 'vue';
import axios from 'axios';
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
const textData = ref([])
const textData2 = ref([])

onMounted(() => {
    let params = { ordershoestatus: 20 };
    axios.get("http://localhost:8000/order/getordersinproduction", { params }).then(response => {
        const newOrders = response.data.newOrders
        const progressOrders = response.data.progressOrders
        newOrders.forEach(element => {
            textData.value.push(element)
        });
        progressOrders.forEach(element => {
            textData2.value.push(element)
        });
        console.log(textData2)
    })
    params = { ordershoestatus: 23 };
    axios.get("http://localhost:8000/order/getordersinproduction", { params }).then(response => {
        const newOrders = response.data.newOrders
        const progressOrders = response.data.progressOrders
        newOrders.forEach(element => {
            textData.value.push(element)
        });
        progressOrders.forEach(element => {
            textData2.value.push(element)
        });
    })
})

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
