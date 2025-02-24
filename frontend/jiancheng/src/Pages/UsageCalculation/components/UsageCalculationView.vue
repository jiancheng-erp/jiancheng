<template>
    <el-row :gutter="20">
        <el-col :span="24" :offset="0" style="font-size: xx-large; text-align: center;">面料用量计算</el-col>
    </el-row>
    <component :is="components[currentDash]" :pendingTaskData="pendingData" :inProgressTaskData="inProgressData" @backToList="changeToList"
    @changeToPend="changeToPend" @changeToProgress="changeToProgress">
    </component>
</template>



<script setup>
import { onMounted, ref, getCurrentInstance} from 'vue';

import { Grid, Memo } from '@element-plus/icons-vue'
import UsageCalculationList from './UsageCalculation/UsageCalculationList.vue';
import UsageCalculationPend from './UsageCalculation/UsageCalculationPend.vue'
import UsageCalculationProgress from './UsageCalculation/UsageCalculationProgress.vue'
import axios from 'axios'

const components = {
    UsageCalculationList,
    UsageCalculationPend,
    UsageCalculationProgress
}

const pendingData = ref([])
const inProgressData = ref([])
onMounted(()=> {
    const proxy = getCurrentInstance()
    const apiBaseUrl = proxy.appContext.config.globalProperties.$apiBaseUrl
    const setAxiosToken = proxy.appContext.config.globalProperties.$setAxiosToken
    const params = {
        orderstatus: 9,
        ordershoestatus: 4
    };
    axios.get(`${apiBaseUrl}/order/getprodordershoebystatus`, { params }).then(response => {
        const fetchPending = response.data.pendingOrders
        const fetchInProgress = response.data.inProgressOrders
        fetchPending.forEach(element => {
            element['taskName'] = "面料用量计算"
            pendingData.value.push(element)
        });
        fetchInProgress.forEach(element => {
            element['taskName'] = "面料用量计算"
            inProgressData.value.push(element)
        });
    })

})

const currentDash = ref('UsageCalculationList')

const changeToList = () => {
    currentDash.value = 'UsageCalculationList'
}
const changeToPend = () => {
    currentDash.value = 'UsageCalculationPend'
}
const changeToProgress = ()=> {
    currentDash.value = 'UsageCalculationProgress'
}

</script>
