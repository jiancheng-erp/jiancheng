<template>
	<div class="order-approval-overview">
		<el-tabs v-model="activeTab" @tab-change="onTabChange">
			<el-tab-pane v-for="tab in tabs" :key="tab.name" :name="tab.name">
				<template #label>
					<span>{{ tab.label }}</span>
					<el-badge :value="counts[tab.name]" :max="999" :type="tab.badgeType" class="tab-badge" />
				</template>
			</el-tab-pane>
		</el-tabs>

		<el-alert :title="currentTab.description" type="info" :closable="false" show-icon class="tab-desc" />

		<el-row :gutter="10" class="controls-row">
			<el-col :span="6">
				<el-input v-model="filters.orderRid" placeholder="订单号" clearable @keypress.enter="search" @clear="search" />
			</el-col>
			<el-col :span="6">
				<el-input v-model="filters.customerName" placeholder="客户名称" clearable @keypress.enter="search" @clear="search" />
			</el-col>
			<el-col :span="6">
				<el-input v-model="filters.orderCid" placeholder="客户订单号" clearable @keypress.enter="search" @clear="search" />
			</el-col>
			<el-col :span="4">
				<el-input v-model="filters.customerBrand" placeholder="客户商标" clearable @keypress.enter="search" @clear="search" />
			</el-col>
			<el-col :span="2">
				<el-button type="primary" @click="search">查询</el-button>
			</el-col>
		</el-row>

		<el-table
			:key="activeTab"
			v-loading="loading"
			:data="orders"
			border
			stripe
			height="560"
			empty-text="暂无符合条件的订单"
		>
			<el-table-column prop="orderRid" label="订单号" min-width="110" />
			<el-table-column prop="orderCid" label="客户订单号" min-width="110" />
			<el-table-column label="鞋型号" min-width="140">
				<template #default="scope">
					<div>{{ (scope.row.shoeRIds || []).join('、') }}</div>
					<div class="sub-text">{{ (scope.row.customerProductNames || []).join('、') }}</div>
				</template>
			</el-table-column>
			<el-table-column prop="customerName" label="客户名称" min-width="90" />
			<el-table-column prop="customerBrand" label="客户商标" min-width="90" />
			<el-table-column prop="orderTotalPairs" label="总双数" width="80" />
			<el-table-column prop="orderSalesman" label="业务员" width="95" />
			<el-table-column prop="orderSupervisor" label="审批人" width="95" />
			<el-table-column prop="orderStartDate" label="开始日期" width="100" />
			<el-table-column prop="orderEndDate" label="结束日期" width="100" />
			<el-table-column label="订单状态" min-width="150">
				<template #default="scope">
					<div class="status-text">{{ scope.row.orderStatus }}</div>
					<div class="sub-text">{{ scope.row.updateTime }}</div>
				</template>
			</el-table-column>
			<el-table-column v-if="showActions" label="操作" width="110" align="center">
				<template #default="scope">
					<div v-if="Number(scope.row.orderStatusVal) >= ORDER_IN_PRODUCTION_STATUS" class="action-cell">
						<el-button link type="primary" size="small" @click="exportProduction(scope.row, 0)">配码导出</el-button>
						<el-button link type="primary" size="small" @click="exportProduction(scope.row, 1)">数量导出</el-button>
						<el-button link type="success" size="small" @click="downloadPackaging(scope.row)">包装资料</el-button>
					</div>
				</template>
			</el-table-column>
		</el-table>

		<el-row class="pagination-row">
			<el-pagination
				@size-change="onPageSizeChange"
				@current-change="onPageChange"
				:current-page="page"
				:page-sizes="[10, 20, 50, 100]"
				:page-size="pageSize"
				layout="total, sizes, prev, pager, next, jumper"
				:total="total"
			/>
		</el-row>
	</div>
</template>

<script setup>
import { reactive, ref, computed, onMounted, getCurrentInstance } from 'vue'
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'

const apiBaseUrl = getCurrentInstance().appContext.config.globalProperties.$apiBaseUrl

const tabs = [
	{
		name: 'unsubmitted',
		label: '业务未提交',
		badgeType: 'danger',
		description: '订单已创建，业务员尚未提交。'
	},
	{
		name: 'pendingGm',
		label: '已提交，总经理未审核',
		badgeType: 'warning',
		description: '业务已提交，正在文员补充单价 / 业务经理审批，或等待总经理审核，尚未下发。'
	},
	{
		name: 'issued',
		label: '总经理已审核，已下发',
		badgeType: 'success',
		description: '总经理已审核通过并下发，订单已进入生产流程（不含已完成订单）。可导出生产订单、下载包装资料。'
	},
	{
		name: 'completed',
		label: '已完成订单',
		badgeType: 'info',
		description: '已完成的历史订单。可导出生产订单、下载包装资料。'
	}
]

const ORDER_IN_PRODUCTION_STATUS = 9

const activeTab = ref('unsubmitted')
const orders = ref([])
const counts = reactive({ unsubmitted: 0, pendingGm: 0, issued: 0, completed: 0 })
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)
const loading = ref(false)
const filters = reactive({
	orderRid: '',
	customerName: '',
	orderCid: '',
	customerBrand: ''
})

const currentTab = computed(() => tabs.find((tab) => tab.name === activeTab.value))
const showActions = computed(() => ['issued', 'completed'].includes(activeTab.value))

onMounted(() => {
	fetchOrders()
})

async function fetchOrders() {
	loading.value = true
	try {
		const response = await axios.get(`${apiBaseUrl}/order/getorderapprovaloverview`, {
			params: {
				category: activeTab.value,
				page: page.value,
				pageSize: pageSize.value,
				...filters
			}
		})
		orders.value = response.data.orders || []
		total.value = response.data.total || 0
		Object.assign(counts, response.data.counts || {})
	} catch (error) {
		ElMessage.error('获取订单数据失败')
		orders.value = []
		total.value = 0
	} finally {
		loading.value = false
	}
}

function onTabChange() {
	page.value = 1
	fetchOrders()
}

function search() {
	page.value = 1
	fetchOrders()
}

function onPageChange(val) {
	page.value = val
	fetchOrders()
}

function onPageSizeChange(val) {
	pageSize.value = val
	page.value = 1
	fetchOrders()
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
</script>

<style scoped>
.order-approval-overview {
	width: 100%;
}

.tab-badge {
	margin-left: 6px;
}

.tab-desc {
	margin-bottom: 16px;
}

.controls-row {
	margin-bottom: 16px;
}

.status-text {
	white-space: pre-line;
}

.sub-text {
	color: #909399;
	font-size: 12px;
}

.action-cell {
	display: flex;
	flex-direction: column;
	align-items: center;
}

.action-cell :deep(.el-button + .el-button) {
	margin-left: 0;
}

.pagination-row {
	margin-top: 16px;
	justify-content: flex-end;
}
</style>
