<template>
    <div class="panel">
        <div class="filters">
            <el-row :gutter="5" style="width: 100%; margin-bottom: 8px">
                <el-col :span="6">
                    <el-radio-group v-model="queryMode" @change="onModeChange">
                        <el-radio-button value="snapshot">单日快照</el-radio-button>
                        <el-radio-button value="period">区间变化（期初-变化-期末）</el-radio-button>
                    </el-radio-group>
                </el-col>
            </el-row>
            <el-row :gutter="5" style="width: 100%; margin-bottom: 12px">
                <!-- 单日快照模式 -->
                <el-col v-if="queryMode === 'snapshot'" :span="3">
                    <el-date-picker v-model="dateFilter" type="date" placeholder="选择日期" value-format="YYYY-MM-DD" :disabled-date="disableAfterYesterday" @change="loadTable" />
                </el-col>
                <!-- 区间变化模式 -->
                <el-col v-if="queryMode === 'period'" :span="6">
                    <el-date-picker
                        v-model="dateRangeFilter"
                        type="daterange"
                        range-separator="至"
                        start-placeholder="开始日期"
                        end-placeholder="结束日期"
                        value-format="YYYY-MM-DD"
                        :disabled-date="disableAfterToday"
                        @change="loadTable"
                    />
                </el-col>
                <el-col :span="3">
                    <el-input v-model="orderRid" placeholder="订单号" clearable @change="loadTable" />
                </el-col>
                <el-col :span="3">
                    <el-input v-model="shoeRid" placeholder="工厂型号" clearable @change="loadTable" />
                </el-col>
                <el-col :span="3">
                    <el-input v-model="customerName" placeholder="客户名称" clearable @change="loadTable" />
                </el-col>
                <el-col :span="3">
                    <el-input v-model="customerBrand" placeholder="客户品牌" clearable @change="loadTable" />
                </el-col>
                <el-col :span="3">
                    <el-input v-model="colorName" placeholder="颜色" clearable @change="loadTable" />
                </el-col>
                <el-col :span="2">
                    <el-checkbox v-model="displayZeroInventory" @change="loadTable">显示零库存</el-checkbox>
                </el-col>
                <el-col :span="2">
                    <el-button type="primary" :loading="loading" @click="loadTable">查询</el-button>
                    <el-button @click="downloadExcel" :loading="downloading">导出 Excel</el-button>
                </el-col>
            </el-row>
        </div>

        <!-- 单日快照表格 -->
        <el-table v-if="queryMode === 'snapshot'" :data="rows" border stripe height="60vh" v-loading="loading">
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
        </el-table>

        <!-- 区间变化表格：期初数-入库变化-出库变化-期末数 -->
        <el-table v-if="queryMode === 'period'" :data="rows" border stripe height="60vh" v-loading="loading">
            <el-table-column prop="orderRId" label="订单号" />
            <el-table-column prop="shoeRId" label="工厂型号" />
            <el-table-column prop="customerName" label="客户名称" />
            <el-table-column prop="customerBrand" label="品牌" />
            <el-table-column prop="customerProductName" label="客户鞋型" />
            <el-table-column prop="colorName" label="颜色" />
            <el-table-column prop="openingAmount" label="期初数" />
            <el-table-column prop="periodInbound" label="入库变化">
                <template #default="{ row }">
                    <span :style="{ color: row.periodInbound > 0 ? '#67c23a' : '' }">
                        {{ row.periodInbound > 0 ? `+${row.periodInbound}` : row.periodInbound }}
                    </span>
                </template>
            </el-table-column>
            <el-table-column prop="periodOutbound" label="出库变化">
                <template #default="{ row }">
                    <span :style="{ color: row.periodOutbound > 0 ? '#e6a23c' : '' }">
                        {{ row.periodOutbound > 0 ? `-${row.periodOutbound}` : row.periodOutbound }}
                    </span>
                </template>
            </el-table-column>
            <el-table-column label="净变化">
                <template #default="{ row }">
                    <span :style="{ color: (row.periodInbound - row.periodOutbound) > 0 ? '#67c23a' : (row.periodInbound - row.periodOutbound) < 0 ? '#f56c6c' : '' }">
                        {{ row.periodInbound - row.periodOutbound > 0 ? `+${row.periodInbound - row.periodOutbound}` : row.periodInbound - row.periodOutbound }}
                    </span>
                </template>
            </el-table-column>
            <el-table-column prop="closingAmount" label="期末数">
                <template #default="{ row }">
                    <strong>{{ row.closingAmount }}</strong>
                </template>
            </el-table-column>
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

const rows = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)

// 查询模式：snapshot（单日快照）或 period（区间变化）
const queryMode = ref('snapshot')

// 单日快照用
const dateFilter = ref(null)
// 区间变化用
const dateRangeFilter = ref(null)

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

    // 区间默认为本月1日到昨天
    const now = new Date()
    const firstDay = new Date(now.getFullYear(), now.getMonth(), 1).toISOString().split('T')[0]
    dateRangeFilter.value = [firstDay, yesterday.toISOString().split('T')[0]]
}

function disableAfterYesterday(date) {
    const endYesterday = new Date()
    endYesterday.setDate(endYesterday.getDate() - 1)
    endYesterday.setHours(23, 59, 59, 999)
    return date.getTime() > endYesterday.getTime()
}

function disableAfterToday(date) {
    const endToday = new Date()
    endToday.setHours(23, 59, 59, 999)
    return date.getTime() > endToday.getTime()
}

function onModeChange() {
    page.value = 1
    rows.value = []
    loadTable()
}

function onPageSizeChange(val) {
    pageSize.value = val
    loadTable()
}

function onPageChange(val) {
    page.value = val
    loadTable()
}

function buildSnapshotQuery() {
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

function buildPeriodQuery() {
    const [startDate, endDate] = dateRangeFilter.value || ['', '']
    return {
        page: page.value,
        pageSize: pageSize.value,
        startDate,
        endDate,
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
        if (queryMode.value === 'snapshot') {
            const params = buildSnapshotQuery()
            const { data } = await axios.get(`${$apiBaseUrl}/warehouse/getfinishedinventoryhistory`, { params })
            rows.value = normalizeSnapshotRows(data.data.items || [])
            total.value = data.data.total || 0
        } else {
            if (!dateRangeFilter.value?.[0] || !dateRangeFilter.value?.[1]) {
                ElMessage.warning('请选择查询区间')
                loading.value = false
                return
            }
            const params = buildPeriodQuery()
            const { data } = await axios.get(`${$apiBaseUrl}/warehouse/getfinishedinventoryperiod`, { params })
            rows.value = data.data.items || []
            total.value = data.data.total || 0
        }
    } catch (err) {
        const message = err?.response?.data?.message || '查询失败'
        ElMessage.error(message)
    } finally {
        loading.value = false
    }
}

function normalizeSnapshotRows(rawRows) {
    return rawRows.map((r) => {
        const sizeBreakdown = (r.sizeColumns || []).map((s) => ({
            size: s.label || s.size || s.sizeValue,
            amount: s.amount ?? s.currentAmount ?? 0
        }))
        return { ...r, sizeBreakdown }
    })
}

async function downloadExcel() {
    downloading.value = true
    try {
        let url: string
        let params: Record<string, any>
        if (queryMode.value === 'snapshot') {
            url = `${$apiBaseUrl}/warehouse/export/finished-inventory-history`
            params = buildSnapshotQuery()
        } else {
            if (!dateRangeFilter.value?.[0] || !dateRangeFilter.value?.[1]) {
                ElMessage.warning('请先选择查询区间')
                downloading.value = false
                return
            }
            url = `${$apiBaseUrl}/warehouse/export/finished-inventory-period`
            params = buildPeriodQuery()
        }
        const res = await axios.get(url, {
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
    } catch (err) {
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
