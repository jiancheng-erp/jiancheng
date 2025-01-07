<template>
    <el-row :gutter="20">
        <el-col :span="24" :offset="0" style="font-size: xx-large; text-align: center"
            >投产指令单创建</el-col
        >
    </el-row>
    <component
        :is="components[currentDash]"
        :pendingTaskData="pendingData"
        :inProgressTaskData="inProgressData"
        @backToList="changeToList"
        @changeToPend="changeToPend"
        @changeToProgress="changeToProgress"
    >
    </component>
</template>

<script setup>
import { onMounted, ref, getCurrentInstance } from 'vue'
import axios from 'axios'

import { Grid, Memo } from '@element-plus/icons-vue'
import ProductionOrderCreateList from './ProductionOrderCreate/ProductionOrderCreateList.vue'
import ProductionOrderCreatePend from './ProductionOrderCreate/ProductionOrderCreatePend.vue'
import ProductionOrderCreateProgress from './ProductionOrderCreate/ProductionOrderCreateProgress.vue'

const components = {
    ProductionOrderCreateList,
    ProductionOrderCreatePend,
    ProductionOrderCreateProgress
}
const proxy = getCurrentInstance()
const apiBaseUrl = proxy.appContext.config.globalProperties.$apiBaseUrl
const pendingData = ref([])
const inProgressData = ref([])
onMounted(() => {
    const params = {
        orderstatus: 9,
        ordershoestatus: 0
    }
    axios.get(`${apiBaseUrl}/order/getdevordershoebystatus`, { params }).then((response) => {
        const fetchPending = response.data.pendingOrders
        const fetchInProgress = response.data.inProgressOrders
        console.log('fetchPending is ')
        console.log(response.data.pendingData)
        fetchPending.forEach((element) => {
            element['taskName'] = '投产指令单创建'
            pendingData.value.push(element)
        })
        console.log(pendingData.value)
        console.log(5)
        fetchInProgress.forEach((element) => {
            element['taskName'] = '投产指令单创建'
            inProgressData.value.push(element)
        })
    })
})

const currentDash = ref('ProductionOrderCreateList')

const changeToList = () => {
    currentDash.value = 'ProductionOrderCreateList'
}
const changeToPend = () => {
    currentDash.value = 'ProductionOrderCreatePend'
}
const changeToProgress = () => {
    currentDash.value = 'ProductionOrderCreateProgress'
}
</script>
