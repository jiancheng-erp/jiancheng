<template>
    <div class="content">
        <el-row :gutter="20" style="margin-top: 20px;width: 100%;">
            <el-col :span="4" :offset="0"
                ><el-input
                    v-model="orderRidFilter"
                    placeholder="请输入订单号"
                    size="default"
                    :suffix-icon="Search"
                    clearable
                    @input="filterByRid()"
                ></el-input>
            </el-col>
            <el-col :span="4" :offset="0"
                ><el-input
                    v-model="orderCidFilter"
                    placeholder="请输入客户订单号"
                    size="default"
                    :suffix-icon="Search"
                    clearable
                    @input="filterByCid()"
                ></el-input>
            </el-col>
        </el-row>
        <el-row :gutter="20" style="margin-top: 20px;width: 100%;">
            <el-table :data="displayData" stripe height="530">
                <el-table-column type="index" width="50" />
                <el-table-column prop="orderRid" label="订单号" />
                <el-table-column prop="customerName" label="客户名" />
                <el-table-column prop="orderCid" label="客户订单号" />
                <el-table-column prop="orderStartDate" label="订单开始日期" sortable />
                <el-table-column prop="orderEndDate" label="订单结束日期" sortable />
                <el-table-column prop="orderStatus" label="订单状态" />
                <el-table-column label="操作" width="300">
                    <template #default="scope">
                        <el-button
                            type="primary"
                            @click="confirmOrder(scope.row.orderDbId)"
                            >确认订单</el-button
                        >
                    </template>
                </el-table-column>
            </el-table>
        </el-row>
        <el-row :gutter="20" style="justify-content: end; width: 100%">
            <el-pagination
                @size-change="chageCurrentPageSize"
                @current-change="changeCurrentPage"
                :current-page="currentPage"
                :page-sizes="[10, 20, 30, 40]"
                :page-size="currentPageSize"
                layout="total, sizes, prev, pager, next, jumper"
                :total="currentTotalRows"
            />
        </el-row>
    </div>
</template>
<script setup>
import { Search } from '@element-plus/icons-vue'
import axios from 'axios'
import { ref, onMounted, getCurrentInstance } from 'vue'
import { ElMessage } from 'element-plus'

let orderRidFilter = ref('')
let orderCidFilter = ref('')
let displayData = ref([])
let unfilteredData = ref([])
let filterData = ref([])
let allData = ref([])
let flagShow = ref(false)
let isFilter = ref(false)
const $api_baseUrl = getCurrentInstance().appContext.config.globalProperties.$apiBaseUrl

let currentPage = ref(1)
let currentPageSize = ref(10)
let currentTotalRows = ref(0)

onMounted(() => {
    getAllOrders()
})

async function getAllOrders() {
    const response = await axios.get(`${$api_baseUrl}`)
    allData.value = response.data
    unfilteredData.value = response.data
    displayData.value = unfilteredData.value
    currentTotalRows.value = displayData.value.length
}

function confirmOrder(orderId) {
}

function filterByRid() {
    if (!orderRidFilter.value) {
        if (!flagShow.value) {
            displayData.value = unfilteredData.value
        } else {
            displayData.value = allData.value
        }
    } else {
        if (flagShow.value) {
            filterData.value = allData.value.filter((task) => {
                const filterMatch = task.orderRid.includes(orderRidFilter.value)
                return filterMatch
            })
        } else {
            filterData.value = unfilteredData.value.filter((task) => {
                const filterMatch = task.orderRid.includes(orderRidFilter.value)
                return filterMatch
            })
        }
        isFilter.value = true
    }
    if (isFilter.value) {
        dataCut2()
    } else {
        dataCut()
    }
}
function filterByCid() {
    if (!orderCidFilter.value) {
        if (!flagShow.value) {
            displayData.value = unfilteredData.value
        } else {
            displayData.value = allData.value
        }
    } else {
        if (flagShow.value) {
            filterData.value = allData.value.filter((task) => {
                const filterMatch = task.orderCid.includes(orderCidFilter.value)
                return filterMatch
            })
        } else {
            filterData.value = unfilteredData.value.filter((task) => {
                const filterMatch = task.orderCid.includes(orderCidFilter.value)
                return filterMatch
            })
        }
        isFilter.value = true
    }
    if (isFilter.value) {
        dataCut2()
    } else {
        dataCut()
    }
}

function chageCurrentPageSize(val) {
    if (currentPageSize.value !== val) {
        currentPageSize.value = val
        if (isFilter.value) {
            dataCut2()
        } else {
            dataCut()
        }
    }
}

function changeCurrentPage(val) {
    if (currentPage.value !== val) {
        currentPage.value = val
        if (isFilter.value) {
            dataCut2()
        } else {
            dataCut()
        }
    }
}
function dataCut() {
    if (!flagShow.value) {
        displayData.value = unfilteredData.value.slice(
            (currentPage.value - 1) * currentPageSize.value,
            currentPageSize.value * currentPage.value
        )
    } else {
        displayData.value = allData.value.slice(
            (currentPage.value - 1) * currentPageSize.value,
            currentPageSize.value * currentPage.value
        )
    }
}
function dataCut2() {
    currentTotalRows.value = filterData.value.length
    displayData.value = filterData.value.slice(
        (currentPage.value - 1) * currentPageSize.value,
        currentPageSize.value * currentPage.value
    )
}
</script>
<style scoped>
.content {
    height: calc(100% - 40px);
}
</style>