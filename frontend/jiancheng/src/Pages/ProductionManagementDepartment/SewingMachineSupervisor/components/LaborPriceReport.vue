<template>
    <el-row :gutter="20">
        <el-col :span="24" :offset="0" style="font-size: xx-large; text-align: center; color: black;">针车工价填报</el-col>
    </el-row>
    <el-row :gutter="20">
        <el-col :span="4" :offset="19"><el-input v-model="searchOrder" placeholder="请输入订单号" size="default"
                :suffix-icon="Search" clearable @input="filterData"></el-input>
        </el-col>
    </el-row>
    <el-row :gutter="20" style="margin-top: 20px;">
        <el-col :span="24">
            <component :is="components[currentDash]" :taskData="taskData">
            </component>
        </el-col>
    </el-row>
</template>
<script setup>
import OrderList from './LaborPriceReport/OrderList.vue'
import { onMounted, ref } from 'vue';
import axios from 'axios';
const components = {
    OrderList
}
const taskData = ref([])
onMounted(() => {
    const params = {
        ordershoestatus: 27
    };
    axios.get("http://localhost:8000/order/getordersinproduction", { params }).then(response => {
        const newOrders = response.data.newOrders
        const progressOrders = response.data.progressOrders
        newOrders.forEach(element => {
            element["orderStatus"] = "待处理"
            taskData.value.push(element)
        });
        progressOrders.forEach(element => {
            element["orderStatus"] = "处理中"
            taskData.value.push(element)
        });
    })
})
const currentDash = ref('OrderList')
</script>