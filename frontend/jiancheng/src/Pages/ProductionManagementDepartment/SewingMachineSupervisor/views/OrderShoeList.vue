<template>
    <el-container>
        <el-header height="">
            <AllHeader></AllHeader>
        </el-header>
        <el-main>
            <el-row :gutter="20" style="text-align: center;">
                <el-col :span="24" :offset="0" style="font-size: xx-large; text-align: center;">针车及预备数量填报</el-col>
            </el-row>
            <el-row :gutter="20">
                <el-col :span="24" :offset="0">
                    <el-descriptions title="订单信息" :column="3" border>
                        <el-descriptions-item label="订单编号">{{ props.orderRId }}</el-descriptions-item>
                        <el-descriptions-item label="订单创建时间">{{ props.createTime }}</el-descriptions-item>
                        <el-descriptions-item label="客户">{{ props.customerName }}</el-descriptions-item>
                    </el-descriptions></el-col>
            </el-row>
            <el-table :data="taskData" border>
                <el-table-column prop="shoeRId" label="鞋型号"></el-table-column>
                <el-table-column prop="team" label="工组"></el-table-column>
                <el-table-column prop="status" label="状态"></el-table-column>
                <el-table-column label="操作">
                    <template #default="scope">
                        <el-button type="primary" @click="handleClick(scope.row)">查看</el-button>
                    </template>
                </el-table-column>
            </el-table>
        </el-main>
    </el-container>
</template>

<script setup>
import { onMounted, ref } from 'vue';
import AllHeader from '@/components/AllHeader.vue';
import axios from 'axios';
const props = defineProps({
    'orderId': String,
    'orderRId': String,
    'createTime': String,
    'customerName': String,
    'taskName': String
})
const taskData = ref([])
onMounted(async () => {
    let params = {
        "orderId": props.orderId,
        "team": "针车预备"
    }
    let response = await axios.get("http://localhost:8000/production/getallordershoesquantityreports", { params })
    for (const key in response.data) {
        let value = response.data[key]
        let obj = { "orderShoeId": key, "shoeRId": value.shoeRId, "status": value.status, "team": "针车预备" }
        taskData.value.push(obj)
    }

    params = {
        "orderId": props.orderId,
        "team": "针车"
    }
    response = await axios.get("http://localhost:8000/production/getallordershoesquantityreports", { params })
    for (const key in response.data) {
        let value = response.data[key]
        let obj = { "orderShoeId": key, "shoeRId": value.shoeRId, "status": value.status, "team": "针车" }
        taskData.value.push(obj)
    }
})
const handleClick = (rowData) => {
    let url = ""
    rowData["orderId"] = props.orderId
    rowData["orderRId"] = props.orderRId
    rowData["createTime"] = props.createTime
    rowData["customerName"] = props.customerName
    rowData["team"] = rowData.team
    const queryString = new URLSearchParams(rowData).toString();
    url = `${window.location.origin}/sewingmachine/ordershoelist/amountreportlist?${queryString}`;
    if (url) {
        window.open(url, '_blank');
    }
}
</script>
