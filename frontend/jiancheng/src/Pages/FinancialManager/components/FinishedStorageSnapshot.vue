<template>
    <div class="panel">
        <div class="filters">
            <el-row :gutter="5" style="width: 100%; margin-bottom: 12px">
                <el-col :span="3" :offset="0">
                    <el-date-picker v-model="dateFilter" type="date" placeholder="选择日期" value-format="YYYY-MM-DD" :disabled-date="disableAfterYesterday" @change="loadTable" />
                </el-col>
                <el-col :span="3" :offset="0">
                    <el-input v-model="orderRid" placeholder="订单号" clearable @change="loadTable" />
                </el-col>
                <el-col :span="3" :offset="0">
                    <el-input v-model="shoeRid" placeholder="工厂型号" clearable @change="loadTable" />
                </el-col>
                <el-col :span="3" :offset="0">
                    <el-input v-model="customerName" placeholder="客户名称" clearable @change="loadTable" />
                </el-col>
                <el-col :span="3" :offset="0">
                    <el-input v-model="customerBrand" placeholder="客户品牌" clearable @change="loadTable" />
                </el-col>
                <el-col :span="3" :offset="0">
                    <el-input v-model="colorName" placeholder="颜色" clearable @change="loadTable" />
                </el-col>
                <el-col :span="2" :offset="0">
                    <el-checkbox v-model="displayZeroInventory" @change="loadTable">显示零库存</el-checkbox>
                </el-col>
                <el-col :span="2" :offset="0">
                    <el-button type="primary" :loading="loading" @click="loadTable">查询</el-button>
                    <el-button @click="downloadExcel" :loading="downloading">导出 Excel</el-button>
                </el-col>
            </el-row>
        </div>

        <el-table :data="rows" border stripe height="60vh" v-loading="loading">
            <el-table-column prop="orderRId" label="订单号" />
            <el-table-column prop="shoeRId" label="工厂型号" />
            <el-table-column prop="customerName" label="客户名称" />
            <el-table-column prop="customerBrand" label="品牌" />
            <el-table-column prop="customerProductName" label="客户鞋型" />
            <el-table-column prop="colorName" label="颜色" />
            <el-table-column prop="finishedEstimatedAmount" label="计划入库" />
            <el-table-column prop="finishedActualAmount" label="实际入库" />
            <el-table-column prop="finishedAmount" label="当前库存" />
            <el-table-column prop="finishedStatusLabel" label="状态" />
            <!-- <el-table-column label="尺码分布">
                <template #default="{ row }">
                    <div class="size-chip" v-for="item in row.sizeBreakdown" :key="item.size">
                        {{ item.size }}: {{ item.amount }}
                    </div>
                </template>
            </el-table-column> -->
        </el-table>

        <div class="pager">
            <el-pagination
                @size-change="onPageSizeChange"
                @current-change="onPageChange"
                :current-page="page"
                :page-sizes="[20, 40, 60, 100]"
                :page-size="pageSize"
                layout="total, sizes, prev, pager, next, jumper"
                :total="total"
            />
        </div>
    </div>
</template>

<script setup lang="ts">
import { ref, getCurrentInstance, onMounted } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'

const { appContext } = getCurrentInstance()
const $apiBaseUrl = appContext.config.globalProperties.$apiBaseUrl

const rows = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const dateFilter = ref<string | null>(null)
const orderRid = ref('')
const shoeRid = ref('')
const customerName = ref('')
const customerBrand = ref('')
const colorName = ref('')
const displayZeroInventory = ref(false)
const loading = ref(false)
const downloading = ref(false)

onMounted(() => {
    presetDate()
    loadTable()
})

function presetDate() {
    const yesterday = new Date()
    yesterday.setDate(yesterday.getDate() - 1)
    dateFilter.value = yesterday.toISOString().split('T')[0]
}

function disableAfterYesterday(date: Date) {
    const endYesterday = new Date()
    endYesterday.setDate(endYesterday.getDate() - 1)
    endYesterday.setHours(23, 59, 59, 999)
    return date.getTime() > endYesterday.getTime()
}

function onPageSizeChange(val: number) {
    pageSize.value = val
    loadTable()
}

function onPageChange(val: number) {
    page.value = val
    loadTable()
}

function buildQuery() {
    return {
        page: page.value,
        pageSize: pageSize.value,
        snapshotDate: dateFilter.value,
        orderRId: orderRid.value,
        shoeRId: shoeRid.value,
        customerName: customerName.value,
        customerBrand: customerBrand.value,
        colorName: colorName.value,
        displayZeroInventory: displayZeroInventory.value
    }
}

async function loadTable() {
    loading.value = true
    try {
        const params = buildQuery()
        const { data } = await axios.get(`${$apiBaseUrl}/warehouse/getfinishedinventoryhistory`, { params })
        rows.value = normalizeRows(data.data.items || [])
        total.value = data.data.total || 0
    } catch (err: any) {
        const message = err?.response?.data?.message || '查询失败'
        ElMessage.error(message)
    } finally {
        loading.value = false
    }
}

function normalizeRows(rawRows: any[]) {
    return rawRows.map((r) => {
        const sizeBreakdown = (r.sizeColumns || []).map((s) => ({
            size: s.label || s.size || s.sizeValue,
            amount: s.amount ?? s.currentAmount ?? 0
        }))
        return {
            ...r,
            sizeBreakdown
        }
    })
}

async function downloadExcel() {
    downloading.value = true
    try {
        const params = buildQuery()
        const res = await axios.get(`${$apiBaseUrl}/warehouse/export/finished-inventory-history`, {
            params,
            responseType: 'blob'
        })
        const blob = new Blob([res.data], { type: res.headers['content-type'] })
        const disposition = res.headers['content-disposition']
        let filename = '成品仓历史库存.xlsx'
        if (disposition && disposition.includes('filename=')) {
            const match = disposition.match(/filename="?(.+?)"?$/)
            if (match && match[1]) {
                filename = decodeURIComponent(match[1])
            }
        }
        const link = document.createElement('a')
        link.href = URL.createObjectURL(blob)
        link.download = filename
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        URL.revokeObjectURL(link.href)
    } catch (err: any) {
        const message = err?.response?.data?.message || '导出失败'
        ElMessage.error(message)
    } finally {
        downloading.value = false
    }
}
</script>

<style scoped>
.panel {
    display: flex;
    flex-direction: column;
    gap: 12px;
}
.filters {
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
    align-items: center;
}
.size-chip {
    display: inline-block;
    padding: 2px 6px;
    margin: 2px;
    border-radius: 6px;
    background: #f5f7fa;
    border: 1px solid #ebeef5;
    font-size: 12px;
    color: #606266;
}
.pager {
    display: flex;
    justify-content: flex-end;
}
</style>
