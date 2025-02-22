<template>
    <el-row :gutter="10" style="margin-top: 20px">
        <el-col :span="2" :offset="0">
            <el-button size="default" type="primary" @click="exportOrder" style="margin-bottom: 20px;">订单导出</el-button>
        </el-col>
        <el-col :span="4" :offset="0" style="white-space: nowrap;">
            <el-input v-model="filters.orderNumberSearch" placeholder="请输入订单号" clearable @keypress.enter="filterOrders()"
                @clear="filterOrders" />
        </el-col>
        <el-col :span="4" :offset="0" style="white-space: nowrap;">
            <el-input v-model="filters.customerNameSearch" placeholder="请输入客户名称" clearable @keypress.enter="filterOrders()"
                @clear="filterOrders" />
        </el-col>
        <el-col :span="4" :offset="0" style="white-space: nowrap;">
            <el-input v-model="filters.orderCIdSearch" placeholder="请输入客户订单号" clearable @keypress.enter="filterOrders()"
                @clear="filterOrders" />
        </el-col>
        <el-col :span="4" :offset="0" style="white-space: nowrap;">
            <el-input v-model="filters.customerBrandSearch" placeholder="请输入客户商标" clearable @keypress.enter="filterOrders()"
                @clear="filterOrders" />
        </el-col>
    </el-row>
    <el-table :data="currentTableData" border stripe height="600" @selection-change="handleSelection">
        <el-table-column type="selection" width="55" />
        <el-table-column prop="orderRid" label="订单号" />
        <el-table-column prop="orderCid" label="客户订单号" />
        <el-table-column prop="customerName" label="客户名" />
        <el-table-column prop="customerBrand" label="客户商标" />
        <el-table-column prop="orderStartDate" label="订单开始日期" sortable />
        <el-table-column prop="orderEndDate" label="订单结束日期" sortable />
        <el-table-column prop="orderStatus" label="订单状态" />
    </el-table>
    <el-row :gutter="20" style="justify-content: end; width: 100%">
        <el-pagination @size-change="chageCurrentPageSize" @current-change="changeCurrentPage"
            :current-page="currentPage" :page-sizes="[10, 20, 30, 40]" :page-size="currentPageSize"
            layout="total, sizes, prev, pager, next, jumper" :total="currentTotalRows" />
    </el-row>
</template>

<script setup lang="js">
import { ref, onMounted, getCurrentInstance, reactive } from 'vue'
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'

const apiBaseUrl = getCurrentInstance().appContext.config.globalProperties.$apiBaseUrl
let currentTableData = ref([])
let tableData = ref([])
let currentPage = ref(1)
let currentPageSize = ref(10)
let currentTotalRows = ref(0)
let selectData = ref([])
let staffId = localStorage.getItem('staffid')
let role = localStorage.getItem('role')

const filters = reactive({
    orderNumberSearch: '',
    customerNameSearch: '',
    orderCIdSearch: '',
    customerBrandSearch: ''
})

onMounted(() => {
    getAllOrders()
})

async function filterOrders() {
    let filteredData = tableData.value
    if (filters.orderNumberSearch) {
        filteredData = filteredData.filter(order => order.orderRid.includes(filters.orderNumberSearch))
    }
    if (filters.customerNameSearch) {
        filteredData = filteredData.filter(order => order.customerName.includes(filters.customerNameSearch))
    }
    if (filters.orderCIdSearch) {
        filteredData = filteredData.filter(order => order.orderCid.includes(filters.orderCIdSearch))
    }
    if (filters.customerBrandSearch) {
        filteredData = filteredData.filter(order => order.customerBrand.includes(filters.customerBrandSearch))
    }
    currentTableData.value = filteredData
    currentTotalRows.value = filteredData.length
}

async function getAllOrders() {
    let response
    if (role == 21) {
        response = await axios.get(`${apiBaseUrl}/order/getbusinessdisplayorderbyuser`, {
            currentStaffId: staffId
        })
    }
    if (role == 4) {
        response = await axios.get(`${apiBaseUrl}/order/getallorders`)
    }
    tableData.value = response.data
    currentTableData.value = response.data
    currentTotalRows.value = response.data.length
    dataCut()
}

function handleSelection(value) {
    selectData.value = value
}
function chageCurrentPageSize(val) {
    if (currentPageSize.value !== val) {
        currentPageSize.value = val
        dataCut()
    }
}

function changeCurrentPage(val) {
    if (currentPage.value !== val) {
        currentPage.value = val
        dataCut()
    }
}
function dataCut() {
    currentTableData.value = tableData.value.slice(
        (currentPage.value - 1) * currentPageSize.value,
        currentPageSize.value * currentPage.value
    )
}

function exportOrder() {
    if (selectData.value.length === 0) {
        ElMessage.warning('请选择要导出的订单')
    } else {
        ElMessageBox.alert('请确认选择订单为同一个客户订单', '', {
            confirmButtonText: '确认',
            cancelButtonText: '取消',
            callback: async (action) => {
                if (action === 'confirm') {
                    // get order db id from selectData
                    const exportOrderIds = selectData.value.map(order => order.orderDbId)
                    window.open(
                        `${apiBaseUrl}/order/exportorder?orderIds=${exportOrderIds.toString()}`
                    )
                }
            }
        })
    }
}
</script>
