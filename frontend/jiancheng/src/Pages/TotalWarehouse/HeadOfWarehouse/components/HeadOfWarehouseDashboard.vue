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
    <component :is="components[currentDash]" :pendingTaskData="pendingData" :inProgressTaskData="inProgressData" :datafinished="datafinished" @backGrid="changeToGrid"
    @changeToPend="changeToPend" @changeToProgress="changeToProgress">
    </component>
  </template>
  
  
  <script setup>
  
  import { getCurrentInstance, onMounted, ref } from 'vue';
  import axios from 'axios';
  
  import { Grid, Memo } from '@element-plus/icons-vue'
  import DashboardGrid from './Dashboard/DashboardGrid.vue';
  import DashboardList from './Dashboard/DashboardList.vue'
  import DashboardPend from './Dashboard/DashboardListPend.vue'
  import DashboardProgress from './Dashboard/DashboardListProgress.vue'
  
  
  
  const components = {
        DashboardGrid,
        DashboardList,
        DashboardPend,
        DashboardProgress
  }
  const pendingData = ref([])
  const inProgressData = ref([])
  const datafinished = ref(true)
  const proxy = getCurrentInstance()
  const apiBaseUrl = proxy.appContext.config.globalProperties.$apiBaseUrl
  
  onMounted(()=> {
    const firstBomStatus = 7
    const params = {
        ordershoestatus : firstBomStatus
    };
  
  
    axios.get(`${apiBaseUrl}/order/getprodordershoebystatus`, {params}).then(response => {
        const firstBomPending = response.data.pendingOrders
        const firstBomProgress = response.data.inProgressOrders
        firstBomPending.forEach(element => {
            element['taskName'] = "二次采购订单创建"
            pendingData.value.push(element)
        });
        firstBomProgress.forEach(element => {
            element['taskName'] = "二次采购订单创建"
            inProgressData.value.push(element)
        });
    })
    console.log(inProgressData)
    console.log(pendingData)
    datafinished.value = false
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
  
  
  
  