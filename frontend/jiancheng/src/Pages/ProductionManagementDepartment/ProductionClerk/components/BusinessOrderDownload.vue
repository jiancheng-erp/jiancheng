<template>
	<div class="business-order-download">
		<el-row :gutter="10" class="controls-row">
			<el-col :span="6">
				<el-input v-model="filters.orderNumberSearch" placeholder="订单号" clearable @keypress.enter="filterOrders" @clear="filterOrders" />
			</el-col>
			<el-col :span="6">
				<el-input v-model="filters.customerNameSearch" placeholder="客户名称" clearable @keypress.enter="filterOrders" @clear="filterOrders" />
			</el-col>
			<el-col :span="6">
				<el-input v-model="filters.orderCIdSearch" placeholder="客户订单号" clearable @keypress.enter="filterOrders" @clear="filterOrders" />
			</el-col>
			<el-col :span="6">
				<el-input v-model="filters.customerBrandSearch" placeholder="客户商标" clearable @keypress.enter="filterOrders" @clear="filterOrders" />
			</el-col>
		</el-row>

		<el-table
			:data="currentTableData"
			border
			stripe
			height="580"
			:loading="loading"
			empty-text="暂无满足条件的生产订单"
			:default-sort="{ prop: 'orderStartDate', order: 'ascending' }"
		>
			<el-table-column prop="orderRid" label="订单号" />
			<el-table-column prop="orderCid" label="客户订单号" />
			<el-table-column prop="customerName" label="客户名称" />
			<el-table-column prop="customerBrand" label="客户商标" />
			<el-table-column prop="orderStartDate" label="开始日期" sortable />
			<el-table-column prop="orderEndDate" label="结束日期" sortable />
			<el-table-column prop="orderStatus" label="订单状态" />
			<el-table-column label="操作" width="360">
				<template #default="scope">
					<el-button type="primary" size="small" @click="exportProduction(scope.row, 0)" :disabled="loading">
						配码导出
					</el-button>
					<el-button type="primary" size="small" @click="exportProduction(scope.row, 1)" :disabled="loading">
						数量导出
					</el-button>
					<el-button type="success" size="small" @click="downloadPackaging(scope.row)" :disabled="loading">
						包装资料
					</el-button>
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
	</div>
</template>

<script setup>
import { reactive, ref, onMounted, getCurrentInstance } from 'vue'
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'

const apiBaseUrl = getCurrentInstance().appContext.config.globalProperties.$apiBaseUrl
const ORDER_IN_PRODUCTION_STATUS = 9

const tableData = ref([])
const filteredData = ref([])
const currentTableData = ref([])
const currentPage = ref(1)
const currentPageSize = ref(10)
const currentTotalRows = ref(0)
const loading = ref(false)

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

function filterOrders() {
	applyFilters(true)
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


function exportProduction(row, outputType) {
	if (!row?.orderDbId) {
		ElMessage.warning('订单信息不完整，无法导出')
		return
	}
	ElMessageBox.confirm('确认导出该生产订单？', '提示', {
		confirmButtonText: '确认',
		cancelButtonText: '取消',
		type: 'warning'
	})
		.then(() => {
			window.open(`${apiBaseUrl}/order/exportproductionorder?orderIds=${row.orderDbId}&outputType=${outputType}&includePrice=0`)
		})
		.catch(() => {})
}

function downloadPackaging(row) {
	if (!row?.orderDbId) {
		ElMessage.warning('订单信息不完整，无法下载包装资料')
		return
	}
	window.open(`${apiBaseUrl}/order/downloadpackagingdoc?orderId=${row.orderDbId}`)
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
.business-order-download {
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
