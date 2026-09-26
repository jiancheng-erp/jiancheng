<template>
    <el-row class="u-mt-5" :gutter="10">
        <el-col :span="8" :offset="0">
            <el-button-group>
                <el-button class="u-mb-5" size="default" type="primary" @click="exportOrder">配码订单导出</el-button>
                <el-button class="u-mb-5" size="default" type="primary" @click="exportAmountOrder">数量订单导出</el-button>
                <el-button class="u-mb-5" size="default" type="primary" @click="exportProductionOrder">配码生产订单导出</el-button>
                <el-button class="u-mb-5" size="default" type="primary" @click="exportProductionAmountOrder">数量生产订单导出</el-button>
            </el-button-group>        
        </el-col>
        <el-col class="u-nowrap" :span="4" :offset="0">
            <el-input v-model="filters.orderNumberSearch" placeholder="请输入订单号" clearable @keypress.enter="filterOrders()"
                @clear="filterOrders" />
        </el-col>
        <el-col class="u-nowrap" :span="4" :offset="0">
            <el-input v-model="filters.customerNameSearch" placeholder="请输入客户名称" clearable @keypress.enter="filterOrders()"
                @clear="filterOrders" />
        </el-col>
        <el-col class="u-nowrap" :span="4" :offset="0">
            <el-input v-model="filters.orderCIdSearch" placeholder="请输入客户订单号" clearable @keypress.enter="filterOrders()"
                @clear="filterOrders" />
        </el-col>
        <el-col class="u-nowrap" :span="4" :offset="0">
            <el-input v-model="filters.customerBrandSearch" placeholder="请输入客户商标" clearable @keypress.enter="filterOrders()"
                @clear="filterOrders" />
        </el-col>
    </el-row>
    <el-table :data="currentTableData" border stripe height="calc(100vh - var(--main-table-offset))" @selection-change="handleSelection">
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
// 业务部助理(role=27)导出的订单/生产订单不允许显示金额信息（服务端也会强制校验，此处仅为减少不必要的数据传输）
const includePriceParam = parseInt(role, 10) === 27 ? '&includePrice=0' : ''

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
        filteredData = filteredData.filter(order => order.orderRid.toLowerCase().includes(filters.orderNumberSearch.toLowerCase()))
    }
    if (filters.customerNameSearch) {
        filteredData = filteredData.filter(order => order.customerName.toLowerCase().includes(filters.customerNameSearch.toLowerCase()))
    }
    if (filters.orderCIdSearch) {
        filteredData = filteredData.filter(order => order.orderCid && order.orderCid.toLowerCase().includes(filters.orderCIdSearch.toLowerCase()))
    }
    if (filters.customerBrandSearch) {
        filteredData = filteredData.filter(order => order.customerBrand.toLowerCase().includes(filters.customerBrandSearch.toLowerCase()))
    }
    currentTableData.value = filteredData
    currentTotalRows.value = filteredData.length
}

async function getAllOrders() {
    let response
    if (role == 21 || role == 27) {
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

// 下载路由为免登录路由（服务端依赖 JWT 判断角色以决定是否包含金额），window.open 不会携带
// Authorization 请求头，导致服务端始终把调用方当作匿名用户处理、强制隐藏金额。
// 改用 axios（自动带上全局 Authorization 头）+ blob 下载，保证角色能被正确识别。
async function downloadFile(url, defaultFilename) {
    try {
        const response = await axios.get(url, { responseType: 'blob' })
        const blob = new Blob([response.data], {
            type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        })
        const disposition = response.headers['content-disposition'] || ''
        let filename = defaultFilename
        const match = disposition.match(/filename\*?=(?:UTF-8'')?["']?([^"';]+)/i)
        if (match && match[1]) {
            filename = decodeURIComponent(match[1])
        }
        const objectUrl = window.URL.createObjectURL(blob)
        const link = document.createElement('a')
        link.href = objectUrl
        link.download = filename
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        window.URL.revokeObjectURL(objectUrl)
    } catch (error) {
        console.error('导出失败', error)
        ElMessage.error('导出失败')
    }
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
                    downloadFile(
                        `${apiBaseUrl}/order/exportorder?orderIds=${exportOrderIds.toString()}&outputType=0${includePriceParam}`,
                        '导出配码订单.xlsx'
                    )
                }
            }
        })
    }
}

function exportAmountOrder() {
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
                    downloadFile(
                        `${apiBaseUrl}/order/exportorder?orderIds=${exportOrderIds.toString()}&outputType=1${includePriceParam}`,
                        '导出数量订单.xlsx'
                    )
                }
            }
        })
    }
}

function exportProductionOrder() {
    if (selectData.value.length === 0) {
        ElMessage.warning('请选择要导出的订单')
    } else {
        ElMessageBox.alert('注意只能选择一个订单', '', {
            confirmButtonText: '确认',
            cancelButtonText: '取消',
            callback: async (action) => {
                if (action === 'confirm') {
                    // get order db id from selectData
                    const exportOrderIds = selectData.value.map(order => order.orderDbId)
                    downloadFile(
                        `${apiBaseUrl}/order/exportproductionorder?orderIds=${exportOrderIds.toString()}&outputType=0${includePriceParam}`,
                        '导出配码生产订单.xlsx'
                    )
                }
            }
        })
    }
}

function exportProductionAmountOrder() {
    if (selectData.value.length === 0) {
        ElMessage.warning('请选择要导出的订单')
    } else {
        ElMessageBox.alert('注意只能选择一个订单', '', {
            confirmButtonText: '确认',
            cancelButtonText: '取消',
            callback: async (action) => {
                if (action === 'confirm') {
                    // get order db id from selectData
                    const exportOrderIds = selectData.value.map(order => order.orderDbId)
                    downloadFile(
                        `${apiBaseUrl}/order/exportproductionorder?orderIds=${exportOrderIds.toString()}&outputType=1${includePriceParam}`,
                        '导出数量生产订单.xlsx'
                    )
                }
            }
        })
    }
}
</script>
