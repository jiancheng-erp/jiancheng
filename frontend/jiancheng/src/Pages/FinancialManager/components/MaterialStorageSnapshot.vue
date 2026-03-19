<template>
    <!-- 查询控制区 -->
    <div style="background: #fafafa; border: 1px solid #ebeef5; border-radius: 6px; padding: 14px 16px; margin-bottom: 12px;">
        <!-- 第一行：模式选择 -->
        <div style="display: flex; align-items: center; gap: 16px; margin-bottom: 10px;">
            <span style="font-size: 13px; color: #606266; white-space: nowrap;">查询方式</span>
            <el-radio-group v-model="queryMode" @change="onQueryModeChange" size="small">
                <el-radio-button label="snapshot">单日快照</el-radio-button>
                <el-radio-button label="period">区间变化</el-radio-button>
            </el-radio-group>
            <el-divider direction="vertical" />
            <span style="font-size: 13px; color: #606266; white-space: nowrap;">视图</span>
            <el-radio-group v-model="viewMode" @change="onViewModeChange" size="small">
                <el-radio-button label="detail">明细</el-radio-button>
                <el-radio-button label="grouped">按名称汇总</el-radio-button>
            </el-radio-group>
        </div>
        <!-- 第二行：日期 + 仓库 + 供应商 + 材料名称 -->
        <div style="display: flex; align-items: center; gap: 10px; flex-wrap: wrap; margin-bottom: 10px;">
            <el-date-picker v-if="queryMode === 'snapshot'" v-model="dateFilter" type="date" placeholder="选择日期" value-format="YYYY-MM-DD"
                :disabled-date="disableAfterYesterday" style="width: 160px;" />
            <el-date-picker v-if="queryMode === 'period'" v-model="dateRangeFilter" type="daterange"
                range-separator="至" start-placeholder="开始日期" end-placeholder="结束日期"
                value-format="YYYY-MM-DD" :disabled-date="disableAfterYesterday" style="width: 280px;" />
            <el-select v-model="currentWarehouse" clearable filterable placeholder="仓库" style="width: 160px;">
                <el-option v-for="item in warehouseOptions" :key="item.warehouseId" :label="item.warehouseName"
                    :value="item.warehouseId" />
            </el-select>
            <el-input v-model="supplierNameFilter" placeholder="供应商" clearable style="width: 150px;" />
            <el-input v-model="materialNameFilter" placeholder="材料名称" clearable style="width: 150px;" />
        </div>
        <!-- 第三行：明细模式额外筛选 -->
        <div v-if="viewMode === 'detail'" style="display: flex; align-items: center; gap: 10px; flex-wrap: wrap; margin-bottom: 10px;">
            <el-input v-model="materialModelFilter" placeholder="材料型号" clearable style="width: 140px;" />
            <el-input v-model="materialSpecificationFilter" placeholder="材料规格" clearable style="width: 140px;" />
            <el-input v-model="materialColorFilter" placeholder="材料颜色" clearable style="width: 140px;" />
            <el-input v-model="orderRidFilter" placeholder="订单号" clearable style="width: 140px;" />
            <el-input v-model="customerProductNameFilter" placeholder="客户鞋型号" clearable style="width: 140px;" />
            <el-input v-model="shoeRidFilter" placeholder="工厂型号" clearable style="width: 140px;" />
            <el-cascader v-if="queryMode === 'snapshot'" v-model="quantityFilters" :options="quantityFilterOptions" :props="cascaderProps"
                placeholder="数量筛选条件" clearable style="width: 280px;" />
        </div>
        <!-- 操作按钮 -->
        <div style="display: flex; align-items: center; gap: 10px;">
            <el-button type="primary" :loading="loading" @click="updateInventoryDisplay">查询</el-button>
            <el-button :loading="downloading" @click="createAndDownloadWarehouseExcel">导出 Excel</el-button>
        </div>
    </div>

    <!-- 数据表格 -->
    <template v-if="queryMode === 'snapshot'">
        <!-- 单日快照 - 明细 -->
        <el-table v-if="viewMode === 'detail'" :data="displayData" border stripe style="width: 100%;" height="60vh" v-loading="loading">
            <el-table-column prop="warehouseName" label="仓库" min-width="80" />
            <el-table-column prop="supplierName" label="供应商" min-width="100" />
            <el-table-column prop="materialType" label="材料类型" min-width="80" />
            <el-table-column prop="materialName" label="材料名称" min-width="100" />
            <el-table-column prop="materialModel" label="材料型号" min-width="80" />
            <el-table-column prop="materialSpecification" label="材料规格" min-width="80" />
            <el-table-column prop="materialColor" label="材料颜色" min-width="80" />
            <el-table-column prop="orderRId" label="订单号" min-width="80" />
            <el-table-column prop="customerProductName" label="客户鞋型号" min-width="100" />
            <el-table-column prop="shoeRId" label="工厂型号" min-width="80" />
            <el-table-column prop="pendingInbound" label="未审核入库数" min-width="90" />
            <el-table-column prop="pendingOutbound" label="未审核出库数" min-width="90" />
            <el-table-column prop="inboundAmount" label="采购入库数" min-width="90" />
            <el-table-column prop="outboundAmount" label="生产出库数" min-width="90" />
            <el-table-column prop="makeInventoryInbound" label="盘库入库数" min-width="90" />
            <el-table-column prop="makeInventoryOutbound" label="盘库出库数" min-width="90" />
            <el-table-column prop="currentAmount" label="库存数量" min-width="80" />
            <el-table-column prop="actualInboundUnit" label="入库单位" min-width="80" />
            <el-table-column label="最新采购单价" min-width="100">
                <template #default="{ row }">{{ fmtPrice(row.unitPrice) }}</template>
            </el-table-column>
            <el-table-column label="库存均价" min-width="90">
                <template #default="{ row }">{{ fmtPrice(row.averagePrice) }}</template>
            </el-table-column>
            <el-table-column label="库存总金额" min-width="100">
                <template #default="{ row }">{{ fmtPrice(row.currentItemTotalPrice) }}</template>
            </el-table-column>
        </el-table>
        <!-- 单日快照 - 按名称汇总 -->
        <el-table v-else :data="displayData" border stripe style="width: 100%;" height="60vh" v-loading="loading">
            <el-table-column prop="materialName" label="材料名称" min-width="120" />
            <el-table-column prop="pendingInbound" label="未审核入库数" min-width="100" />
            <el-table-column prop="pendingOutbound" label="未审核出库数" min-width="100" />
            <el-table-column prop="inboundAmount" label="采购入库数" min-width="100" />
            <el-table-column prop="outboundAmount" label="生产出库数" min-width="100" />
            <el-table-column prop="makeInventoryInbound" label="盘库入库数" min-width="100" />
            <el-table-column prop="makeInventoryOutbound" label="盘库出库数" min-width="100" />
            <el-table-column prop="currentAmount" label="库存数量" min-width="90" />
            <el-table-column label="加权均价" min-width="100">
                <template #default="{ row }">{{ fmtPrice(row.averagePrice) }}</template>
            </el-table-column>
            <el-table-column label="库存总金额" min-width="110">
                <template #default="{ row }">{{ fmtPrice(row.currentItemTotalPrice) }}</template>
            </el-table-column>
        </el-table>
    </template>

    <!-- 区间变化模式 -->
    <template v-else>
        <!-- 区间 - 明细 -->
        <el-table v-if="viewMode === 'detail'" :data="displayData" border stripe style="width: 100%;" height="60vh" v-loading="loading">
            <el-table-column prop="warehouseName" label="仓库" min-width="80" />
            <el-table-column prop="supplierName" label="供应商" min-width="100" />
            <el-table-column prop="materialType" label="材料类型" min-width="80" />
            <el-table-column prop="materialName" label="材料名称" min-width="100" />
            <el-table-column prop="materialModel" label="材料型号" min-width="80" />
            <el-table-column prop="materialSpecification" label="材料规格" min-width="80" />
            <el-table-column prop="materialColor" label="材料颜色" min-width="80" />
            <el-table-column prop="openingAmount" label="期初库存" min-width="80" />
            <el-table-column label="采购入库变化" min-width="100">
                <template #default="{ row }">
                    <span :style="{ color: row.periodInbound > 0 ? '#67c23a' : '' }">
                        {{ row.periodInbound > 0 ? `+${row.periodInbound}` : row.periodInbound }}
                    </span>
                </template>
            </el-table-column>
            <el-table-column label="生产出库变化" min-width="100">
                <template #default="{ row }">
                    <span :style="{ color: row.periodOutbound > 0 ? '#e6a23c' : '' }">
                        {{ row.periodOutbound > 0 ? `-${row.periodOutbound}` : row.periodOutbound }}
                    </span>
                </template>
            </el-table-column>
            <el-table-column label="盘库入库变化" min-width="100">
                <template #default="{ row }">
                    <span :style="{ color: row.periodMakeInbound > 0 ? '#67c23a' : '' }">
                        {{ row.periodMakeInbound > 0 ? `+${row.periodMakeInbound}` : row.periodMakeInbound }}
                    </span>
                </template>
            </el-table-column>
            <el-table-column label="盘库出库变化" min-width="100">
                <template #default="{ row }">
                    <span :style="{ color: row.periodMakeOutbound > 0 ? '#e6a23c' : '' }">
                        {{ row.periodMakeOutbound > 0 ? `-${row.periodMakeOutbound}` : row.periodMakeOutbound }}
                    </span>
                </template>
            </el-table-column>
            <el-table-column label="净变化" min-width="80">
                <template #default="{ row }">
                    <span :style="{ color: row.netChange > 0 ? '#67c23a' : row.netChange < 0 ? '#f56c6c' : '' }">
                        {{ row.netChange > 0 ? `+${row.netChange}` : row.netChange }}
                    </span>
                </template>
            </el-table-column>
            <el-table-column label="期末库存" min-width="80">
                <template #default="{ row }"><strong>{{ row.closingAmount }}</strong></template>
            </el-table-column>
            <el-table-column label="加权均价" min-width="90">
                <template #default="{ row }">{{ fmtPrice(row.averagePrice) }}</template>
            </el-table-column>
            <el-table-column label="期末总金额" min-width="100">
                <template #default="{ row }">{{ fmtPrice(row.closingTotalPrice) }}</template>
            </el-table-column>
        </el-table>
        <!-- 区间 - 按名称汇总 -->
        <el-table v-else :data="displayData" border stripe style="width: 100%;" height="60vh" v-loading="loading">
            <el-table-column prop="materialName" label="材料名称" min-width="120" />
            <el-table-column prop="openingAmount" label="期初库存" min-width="90" />
            <el-table-column label="采购入库变化" min-width="100">
                <template #default="{ row }">
                    <span :style="{ color: row.periodInbound > 0 ? '#67c23a' : '' }">
                        {{ row.periodInbound > 0 ? `+${row.periodInbound}` : row.periodInbound }}
                    </span>
                </template>
            </el-table-column>
            <el-table-column label="生产出库变化" min-width="100">
                <template #default="{ row }">
                    <span :style="{ color: row.periodOutbound > 0 ? '#e6a23c' : '' }">
                        {{ row.periodOutbound > 0 ? `-${row.periodOutbound}` : row.periodOutbound }}
                    </span>
                </template>
            </el-table-column>
            <el-table-column label="盘库入库变化" min-width="100">
                <template #default="{ row }">
                    <span :style="{ color: row.periodMakeInbound > 0 ? '#67c23a' : '' }">
                        {{ row.periodMakeInbound > 0 ? `+${row.periodMakeInbound}` : row.periodMakeInbound }}
                    </span>
                </template>
            </el-table-column>
            <el-table-column label="盘库出库变化" min-width="100">
                <template #default="{ row }">
                    <span :style="{ color: row.periodMakeOutbound > 0 ? '#e6a23c' : '' }">
                        {{ row.periodMakeOutbound > 0 ? `-${row.periodMakeOutbound}` : row.periodMakeOutbound }}
                    </span>
                </template>
            </el-table-column>
            <el-table-column label="净变化" min-width="80">
                <template #default="{ row }">
                    <span :style="{ color: row.netChange > 0 ? '#67c23a' : row.netChange < 0 ? '#f56c6c' : '' }">
                        {{ row.netChange > 0 ? `+${row.netChange}` : row.netChange }}
                    </span>
                </template>
            </el-table-column>
            <el-table-column label="期末库存" min-width="80">
                <template #default="{ row }"><strong>{{ row.closingAmount }}</strong></template>
            </el-table-column>
            <el-table-column label="加权均价" min-width="100">
                <template #default="{ row }">{{ fmtPrice(row.averagePrice) }}</template>
            </el-table-column>
            <el-table-column label="期末总金额" min-width="110">
                <template #default="{ row }">{{ fmtPrice(row.closingTotalPrice) }}</template>
            </el-table-column>
        </el-table>
    </template>

    <!-- 分页 -->
    <div style="margin-top: 8px;">
        <el-pagination @size-change="pageSizeChange" @current-change="pageCurrentChange" :current-page="currentPage"
            :page-sizes="[20, 40, 60, 100]" :page-size="pageSize" layout="total, sizes, prev, pager, next, jumper"
            :total="totalNum" />
    </div>
</template>

<script setup lang="ts">
import { ref, onMounted, getCurrentInstance, nextTick, computed } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'

const displayData = ref([])
const allColumns = ref([])
const checkedColumnValues = ref([])
const selectedColumns = ref([])
const currentPage = ref(1)
const pageSize = ref(20)
const totalNum = ref(0)
const currentWarehouse = ref('')
const supplierNameFilter = ref('')
const materialNameFilter = ref('')
const materialModelFilter = ref('')
const materialSpecificationFilter = ref('')
const materialColorFilter = ref('')
const orderRidFilter = ref('')
const customerProductNameFilter = ref('')
const shoeRidFilter = ref('')
const viewMode = ref('detail')
const queryMode = ref('snapshot')
const dateFilter = ref(null)
const dateRangeFilter = ref(null)
const loading = ref(false)
const downloading = ref(false)
const quantityFilters = ref([])
const filterConditions = [
    { value: 'eq_zero', label: '等于 0' },
    { value: 'neq_zero', label: '不等于 0' }
]
const quantityFilterOptions = [
    {
        value: 'pending_inbound',
        label: '未审核入库数',
        children: filterConditions
    },
    {
        value: 'pending_outbound',
        label: '未审核出库数',
        children: filterConditions
    },
    {
        value: 'inbound_amount',
        label: '采购入库数',
        children: filterConditions
    },
    {
        value: 'outbound_amount',
        label: '生产出库数',
        children: filterConditions
    },
    {
        value: 'current_amount',
        label: '库存数',
        children: filterConditions
    },
    {
        value: 'make_inventory_inbound',
        label: '盘库入库数',
        children: filterConditions
    },
    {
        value: 'make_inventory_outbound',
        label: '盘库出库数',
        children: filterConditions
    },
]

const cascaderProps = {
    multiple: true,        // 允许多选
    expandTrigger: 'hover',
    emitPath: true,        // 返回整条路径 ['pending_inbound','gt_zero']
    value: 'value',
    label: 'label',
    checkStrictly: false   // 只允许勾选叶子
}

// 把 Cascader 的值转换成更好用的结构，方便发给后端
const parsedQuantityFilters = computed(() => {
    return quantityFilters.value.map(path => {
        const [field, op] = path
        return { field, op }
    })
})

let warehouseOptions = ref([])

const $api_baseUrl = getCurrentInstance().appContext.config.globalProperties.$apiBaseUrl

const fmtPrice = (val: any) => val != null ? Number(val).toFixed(3) : ''

onMounted(async () => {
    getWarehouseInfo()
    await getSelectableColumns()
    selectAllColumns()
    setDateFilter()
    updateInventoryDisplay()
})

async function toggleDisplayZero() {
    updateInventoryDisplay()
}

function onViewModeChange() {
    currentPage.value = 1
    updateInventoryDisplay()
}

function onQueryModeChange() {
    currentPage.value = 1
    displayData.value = []
    updateInventoryDisplay()
}

const setDateFilter = () => {
    const yesterday = new Date()
    yesterday.setDate(yesterday.getDate() - 1)
    dateFilter.value = yesterday.toISOString().split('T')[0]

    // 区间默认为本月1日到昨天
    const now = new Date()
    const firstDay = new Date(now.getFullYear(), now.getMonth(), 1).toISOString().split('T')[0]
    dateRangeFilter.value = [firstDay, yesterday.toISOString().split('T')[0]]
}

const disableAfterYesterday = (date: Date) => {
    const endYesterday = new Date()
    endYesterday.setDate(endYesterday.getDate() - 1)
    endYesterday.setHours(23, 59, 59, 999)
    return date.getTime() > endYesterday.getTime()
}

async function getSelectableColumns() {
    const res = await axios.get($api_baseUrl + `/accounting/get_inventory_display_columns`)
    allColumns.value = res.data.selectableColumns
}

async function getWarehouseInfo() {
    const res = await axios.get($api_baseUrl + `/accounting/get_warehouse_info`)
    warehouseOptions.value = res.data.warehouseInfo
}

function deselectAllColumns() {
    checkedColumnValues.value = []
    updateCheckBox()
}

function selectAllColumns() {
    checkedColumnValues.value = allColumns.value.map((col) => col.id)
    updateCheckBox()
}

function updateCheckBox() {
    let temp = []
    allColumns.value.forEach(element => {
        checkedColumnValues.value.forEach(element2 => {
            if (element.id == element2) {
                temp.push(element)
            }
        });
    });
    selectedColumns.value = temp;
}

function pageSizeChange(newSize) {
    pageSize.value = newSize
    updateInventoryDisplay()
}

function pageCurrentChange(page) {
    currentPage.value = page
    updateInventoryDisplay()

}

async function updateInventoryDisplay() {
    loading.value = true
    try {
        if (queryMode.value === 'snapshot') {
            const apiParams = getCurrentPageInfo()
            const endpoint = viewMode.value === 'grouped'
                ? `/warehouse/getmaterialstoragebydate/grouped`
                : `/warehouse/getmaterialstroagebydate`
            const res = await axios.get($api_baseUrl + endpoint, { params: apiParams })
            totalNum.value = res.data.data.total
            displayData.value = res.data.data.items
        } else {
            // 区间变化模式
            if (!dateRangeFilter.value?.[0] || !dateRangeFilter.value?.[1]) {
                ElMessage.warning('请选择查询区间')
                loading.value = false
                return
            }
            const apiParams = getPeriodPageInfo()
            const endpoint = viewMode.value === 'grouped'
                ? `/warehouse/getmaterialstorageperiod/grouped`
                : `/warehouse/getmaterialstorageperiod`
            const res = await axios.get($api_baseUrl + endpoint, { params: apiParams })
            totalNum.value = res.data.data.total
            displayData.value = res.data.data.items
        }
    }
    catch (error) {
        console.log(error)
        const message = error?.response?.data?.message || error?.response?.data?.msg || '查询失败'
        ElMessage.error(message)
    }
    finally {
        loading.value = false
    }
}
function getCurrentPageInfo() {
    return {
        'page': currentPage.value,
        'pageSize': pageSize.value,
        'warehouseIdFilter': currentWarehouse.value,
        'supplierNameFilter': supplierNameFilter.value,
        'materialNameFilter': materialNameFilter.value,
        'materialModelFilter': materialModelFilter.value,
        'materialSpecificationFilter': materialSpecificationFilter.value,
        'materialColorFilter': materialColorFilter.value,
        'orderRidFilter': orderRidFilter.value,
        'customerProductNameFilter': customerProductNameFilter.value,
        'shoeRidFilter': shoeRidFilter.value,
        "snapshotDate": dateFilter.value,
        "quantityFilters": JSON.stringify(parsedQuantityFilters.value)
    }
}
function getPeriodPageInfo() {
    const [startDate, endDate] = dateRangeFilter.value || ['', '']
    return {
        'page': currentPage.value,
        'pageSize': pageSize.value,
        'warehouseIdFilter': currentWarehouse.value,
        'supplierNameFilter': supplierNameFilter.value,
        'materialNameFilter': materialNameFilter.value,
        'materialModelFilter': materialModelFilter.value,
        'materialSpecificationFilter': materialSpecificationFilter.value,
        'materialColorFilter': materialColorFilter.value,
        'orderRidFilter': orderRidFilter.value,
        'customerProductNameFilter': customerProductNameFilter.value,
        'shoeRidFilter': shoeRidFilter.value,
        'startDate': startDate,
        'endDate': endDate,
    }
}
async function createAndDownloadWarehouseExcel() {
    downloading.value = true
    try {
        let apiParams, endpoint, defaultFilename
        if (queryMode.value === 'snapshot') {
            apiParams = getCurrentPageInfo()
            endpoint = viewMode.value === 'grouped'
                ? `/warehouse/exportinventoryhistory/grouped`
                : `/warehouse/exportinventoryhistory`
            defaultFilename = viewMode.value === 'grouped'
                ? '财务部历史库存名称汇总.xlsx'
                : '财务部历史库存总单.xlsx'
        } else {
            if (!dateRangeFilter.value?.[0] || !dateRangeFilter.value?.[1]) {
                ElMessage.warning('请选择查询区间')
                downloading.value = false
                return
            }
            apiParams = getPeriodPageInfo()
            endpoint = viewMode.value === 'grouped'
                ? `/warehouse/exportmaterialstorageperiod/grouped`
                : `/warehouse/exportmaterialstorageperiod`
            defaultFilename = viewMode.value === 'grouped'
                ? '财务部历史库存区间名称汇总.xlsx'
                : '财务部历史库存区间明细.xlsx'
        }
        const res = await axios.get($api_baseUrl + endpoint, {
            params: apiParams,
            responseType: 'blob',
        });

        // Create a Blob from the response data
        const blob = new Blob([res.data], { type: res.headers['content-type'] });

        // Use the filename from the Content-Disposition header if available
        const disposition = res.headers['content-disposition'];
        let filename = defaultFilename;
        if (disposition && disposition.includes('filename=')) {
            const match = disposition.match(/filename="?(.+?)"?$/);
            if (match.length > 1) {
                filename = decodeURIComponent(match[1]);
            }
        }

        // Create a link and trigger the download
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(link.href);
    } catch (error) {
        console.error("Failed to download Excel:", error);
        ElMessage.error('导出失败')
    } finally {
        downloading.value = false
    }
}
</script>