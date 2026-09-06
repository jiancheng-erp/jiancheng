<template>
    <div class="business-production-order">
        <template v-if="!selectedOrderId">
            <el-row :gutter="10" class="controls-row">
                <el-col :span="6">
                    <el-input v-model="filters.orderNumberSearch" placeholder="订单号" clearable @keypress.enter="applyFilters(true)" @clear="applyFilters(true)" />
                </el-col>
                <el-col :span="6">
                    <el-input v-model="filters.customerNameSearch" placeholder="客户名称" clearable @keypress.enter="applyFilters(true)" @clear="applyFilters(true)" />
                </el-col>
                <el-col :span="6">
                    <el-input v-model="filters.orderCIdSearch" placeholder="客户订单号" clearable @keypress.enter="applyFilters(true)" @clear="applyFilters(true)" />
                </el-col>
                <el-col :span="6">
                    <el-input v-model="filters.customerBrandSearch" placeholder="客户商标" clearable @keypress.enter="applyFilters(true)" @clear="applyFilters(true)" />
                </el-col>
            </el-row>

            <el-table
                :data="currentTableData"
                border
                stripe
                height="calc(100vh - var(--main-table-offset))"
                v-loading="loading"
                empty-text="暂无满足条件的生产订单"
            >
                <el-table-column prop="orderRid" label="订单号" />
                <el-table-column prop="orderCid" label="客户订单号" />
                <el-table-column prop="customerName" label="客户名称" />
                <el-table-column prop="customerBrand" label="客户商标" />
                <el-table-column prop="orderStartDate" label="开始日期" sortable />
                <el-table-column prop="orderEndDate" label="结束日期" sortable />
                <el-table-column prop="orderStatus" label="订单状态" />
                <el-table-column label="操作" width="280">
                    <template #default="scope">
                        <el-button type="primary" size="small" @click="viewOrder(scope.row)">查看</el-button>
                        <el-dropdown size="small" trigger="click" @command="(cmd) => downloadExcel(scope.row, cmd)">
                            <el-button type="success" size="small">下载Excel</el-button>
                            <template #dropdown>
                                <el-dropdown-menu>
                                    <el-dropdown-item command="notice">生产通知单</el-dropdown-item>
                                    <el-dropdown-item command="craft">工艺单</el-dropdown-item>
                                </el-dropdown-menu>
                            </template>
                        </el-dropdown>
                    </template>
                </el-table-column>
            </el-table>

            <el-row class="pagination-row">
                <el-pagination
                    @size-change="changeCurrentPageSize"
                    @current-change="changeCurrentPage"
                    :current-page="currentPage"
                    :page-sizes="[10, 20, 30, 40]"
                    :page-size="currentPageSize"
                    layout="total, sizes, prev, pager, next, jumper"
                    :total="currentTotalRows"
                />
            </el-row>
        </template>

        <BusinessProductionOrderSheet v-else :orderId="selectedOrderId" @back="selectedOrderId = null" />
    </div>
</template>

<script setup>
import { reactive, ref, onMounted, getCurrentInstance } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import BusinessProductionOrderSheet from './BusinessProductionOrderSheet.vue'
import { exportProductionOrderExcel, exportCraftSheetExcel } from './productionOrderExcel'

const apiBaseUrl = getCurrentInstance().appContext.config.globalProperties.$apiBaseUrl
const ORDER_IN_PRODUCTION_STATUS = 9

const tableData = ref([])
const filteredData = ref([])
const currentTableData = ref([])
const currentPage = ref(1)
const currentPageSize = ref(10)
const currentTotalRows = ref(0)
const loading = ref(false)
const selectedOrderId = ref(null)

const filters = reactive({
    orderNumberSearch: '',
    customerNameSearch: '',
    orderCIdSearch: '',
    customerBrandSearch: ''
})

onMounted(() => {
    fetchOrders()
})

async function fetchOrders() {
    loading.value = true
    try {
        const response = await axios.get(`${apiBaseUrl}/order/getallorders`)
        const allOrders = Array.isArray(response.data) ? response.data : []
        tableData.value = allOrders.filter((order) => Number(order.orderStatusVal) >= ORDER_IN_PRODUCTION_STATUS)
        applyFilters(true)
    } catch (error) {
        ElMessage.error('获取订单数据失败')
        tableData.value = []
        applyFilters(true)
    } finally {
        loading.value = false
    }
}

function changeCurrentPageSize(val) {
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
    const start = (currentPage.value - 1) * currentPageSize.value
    const end = start + currentPageSize.value
    currentTableData.value = filteredData.value.slice(start, end)
}

function applyFilters(resetPage = false) {
    let data = tableData.value
    if (filters.orderNumberSearch) {
        data = data.filter((order) => (order.orderRid || '').includes(filters.orderNumberSearch))
    }
    if (filters.customerNameSearch) {
        data = data.filter((order) => (order.customerName || '').includes(filters.customerNameSearch))
    }
    if (filters.orderCIdSearch) {
        data = data.filter((order) => (order.orderCid || '').includes(filters.orderCIdSearch))
    }
    if (filters.customerBrandSearch) {
        data = data.filter((order) => (order.customerBrand || '').includes(filters.customerBrandSearch))
    }
    filteredData.value = sortByStartDate(data)
    currentTotalRows.value = data.length
    if (resetPage) {
        currentPage.value = 1
    }
    dataCut()
}

function viewOrder(row) {
    if (!row?.orderDbId) {
        ElMessage.warning('订单信息不完整，无法查看')
        return
    }
    selectedOrderId.value = row.orderDbId
}

async function downloadExcel(row, type = 'notice') {
    if (!row?.orderDbId) {
        ElMessage.warning('订单信息不完整，无法下载')
        return
    }
    try {
        if (type === 'craft') {
            await exportCraftSheetExcel(apiBaseUrl, row.orderDbId)
        } else {
            await exportProductionOrderExcel(apiBaseUrl, row.orderDbId)
        }
    } catch (error) {
        ElMessage.error(type === 'craft' ? '导出工艺单 Excel 失败' : '导出生产通知单 Excel 失败')
    }
}

function sortByStartDate(data) {
    return [...data].sort((a, b) => {
        const aTime = Date.parse(a.orderStartDate || '') || 0
        const bTime = Date.parse(b.orderStartDate || '') || 0
        return aTime - bTime
    })
}
</script>

<style scoped>
.business-production-order {
    width: 100%;
}

.controls-row {
    margin-bottom: 20px;
}

.pagination-row {
    margin-top: 16px;
    justify-content: flex-end;
}
</style>
