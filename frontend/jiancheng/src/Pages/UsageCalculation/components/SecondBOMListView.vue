<template>
    <el-row :gutter="20">
        <el-col :span="24" :offset="0" style="font-size: xx-large; text-align: center;">二次BOM填写</el-col>
    </el-row>
    <component :is="components[currentDash]" :pendingTaskData="pendingData" :inProgressTaskData="inProgressData" @backToList="changeToList"
    @changeToPend="changeToPend" @changeToProgress="changeToProgress">
    </component>
</template>


<script setup>
import {onMounted, ref, getCurrentInstance} from 'vue';
import axios from 'axios';

import { Grid, Memo } from '@element-plus/icons-vue'
import SecondBOMList from './SecondBOMCreate/SecondBOMList.vue'
import SecondOrderPend from './SecondBOMCreate/SecondBOMListPend.vue'
import SecondOrderProgress from './SecondBOMCreate/SecondBOMListProgress.vue'

const proxy = getCurrentInstance()
const apiBaseUrl = proxy.appContext.config.globalProperties.$apiBaseUrl
const components = {
    SecondBOMList,
    SecondOrderPend,
    SecondOrderProgress
}
const pendingData = ref([])
const inProgressData = ref([])
onMounted(()=> {
    const params = {
        orderstatus: 9,
        ordershoestatus: 11
    };
    axios.get(`${apiBaseUrl}/order/getprodordershoebystatus`, { params }).then(response => {
        const fetchPending = response.data.pendingOrders
        const fetchInProgress = response.data.inProgressOrders
        fetchPending.forEach(element => {
            element['taskName'] = "生产BOM用量填写"
            pendingData.value.push(element)
        });
        fetchInProgress.forEach(element => {
            element['taskName'] = "生产BOM用量填写"
            inProgressData.value.push(element)
        });
    })

})

const currentDash = ref('SecondBOMList')

const changeToList = () => {
    currentDash.value = 'SecondBOMList'
}
const changeToPend = () => {
    currentDash.value = 'SecondOrderPend'
}
const changeToProgress = ()=> {
    currentDash.value = 'SecondOrderProgress'
}

</script>

<style></style>