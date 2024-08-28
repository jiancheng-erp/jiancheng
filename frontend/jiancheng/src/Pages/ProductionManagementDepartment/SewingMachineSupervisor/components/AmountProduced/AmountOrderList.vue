<template>
    <el-table :data="props.taskData">
        <el-table-column prop="orderId" label="订单号"></el-table-column>
        <el-table-column prop="customerName" label="客户"></el-table-column>
        <el-table-column prop="createTime" label="订单创建时间"></el-table-column>
        <el-table-column prop="orderStatus" label="状态"></el-table-column>
        <el-table-column label="操作"> 
            <template #default="{ row }">
                <el-button type="primary"
                    @click="handleView(row)">查看</el-button>
            </template>
        </el-table-column>
    </el-table>
</template>

<script setup>
const props = defineProps(["taskData"])
const handleView = (row) => {
    let url = ""
    const queryString = new URLSearchParams(row).toString();
    url = `${window.location.origin}/sewingmachine/ordershoelist?${queryString}`;
    if (url) {
        window.open(url, '_blank');
    }
}
</script>
