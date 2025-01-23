<template>
    <el-row :gutter="20">
        <el-col :span="24" :offset="0" style="font-size: xx-large; text-align: center; color: black;">成型工序填报</el-col>
    </el-row>
    <el-row :gutter="20" style="margin-top: 20px">
        <el-col :span="4" :offset="0" style="white-space: nowrap;">
            订单号筛选：
            <el-input v-model="orderRIdSearch" placeholder="请输入订单号" clearable @keypress.enter="getOrderTableData()"
                @clear="getOrderTableData" />
        </el-col>
        <el-col :span="4" :offset="2" style="white-space: nowrap;">
            鞋型号筛选：
            <el-input v-model="shoeRIdSearch" placeholder="请输入鞋型号" clearable @keypress.enter="getOrderTableData()"
                @clear="getOrderTableData()" />
        </el-col>
    </el-row>
    <el-table :data="taskData" border stripe>
        <el-table-column prop="orderRId" label="订单号"></el-table-column>
        <el-table-column prop="shoeRId" label="鞋型号"></el-table-column>
        <el-table-column prop="customerName" label="客户名称"></el-table-column>
        <el-table-column prop="productionStartDate" label="工段开始日期"></el-table-column>
        <el-table-column prop="productionEndDate" label="工段结束日期"></el-table-column>
        <el-table-column prop="statusName" label="状态">
            <template v-slot="scope">
                <el-tooltip v-if="scope.row.statusName === '被驳回'" effect="dark" :content="scope.row.rejectionReason">
                    <span class="rejected">{{ scope.row.statusName }}</span>
                </el-tooltip>
                <span v-else>{{ scope.row.statusName }}</span>
            </template>
        </el-table-column>
        <el-table-column label="操作">
            <template #default="scope">
                <el-button type="primary" @click="handleView(scope.row)">查看</el-button>
            </template>
        </el-table-column>
    </el-table>
    <el-row :gutter="20">
        <el-col :span="12" :offset="15">
            <el-pagination v-model:current-page="currentPage" v-model:page-size="pageSize"
                :page-sizes="[10, 20, 30, 40]" layout="total, sizes, prev, pager, next, jumper" :total="totalPages"
                @size-change="handleSizeChange" @current-change="handlePageChange" />
        </el-col>
    </el-row>
</template>
<script setup>
import { onMounted, ref, getCurrentInstance } from 'vue';
import axios from 'axios';
const proxy = getCurrentInstance()
const apiBaseUrl = proxy.appContext.config.globalProperties.$apiBaseUrl
const taskData = ref([])
const orderRIdSearch = ref('')
const shoeRIdSearch = ref('')
const currentPage = ref(1)
const pageSize = ref(10)
const totalPages = ref(0)
onMounted(() => {
    getOrderTableData()
})
const handlePageChange = (val) => {
    currentPage.value = val
    getOrderTableData()
}
const handleSizeChange = (val) => {
    pageSize.value = val
    getOrderTableData()
}
const getOrderTableData = async () => {
    const params = {
        "page": currentPage.value,
        "pageSize": pageSize.value,
        "orderRId": orderRIdSearch.value,
        "shoeRId": shoeRIdSearch.value,
        "team": "成型"
    }
    const response = await axios.get(`${apiBaseUrl}/production/getnewpricereports`, { params })
    taskData.value = response.data.result
    totalPages.value = response.data.totalLength
}
const handleView = (row) => {
    let url = ""
    let params = {"orderId": row.orderId, "orderShoeId": row.orderShoeId, 'teams': ['成型']}
    const queryString = new URLSearchParams(params).toString();
    url = `${window.location.origin}/molding/pricereport?${queryString}`;
    window.open(url, '_blank');
}
</script>
