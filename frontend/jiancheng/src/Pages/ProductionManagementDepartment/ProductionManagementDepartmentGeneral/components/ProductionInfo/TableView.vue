<template>
	<el-row class="u-mt-5" :gutter="20">
		<el-col class="u-nowrap" :span="4" :offset="0">
			<el-input v-model="orderRIdSearch" placeholder="请输入订单号" clearable @keypress.enter="handleSearch"
				@clear="handleSearch" />
		</el-col>
		<el-col class="u-nowrap" :span="4" :offset="0">
			<el-input v-model="customerNameSearch" placeholder="请输入客户名称" clearable @keypress.enter="handleSearch"
				@clear="handleSearch" />
		</el-col>
		<el-col class="u-nowrap" :span="4" :offset="0">
			<el-input v-model="customerBrandSearch" placeholder="请输入客户商标" clearable @keypress.enter="handleSearch"
				@clear="handleSearch" />
		</el-col>
	</el-row>
	<el-row class="u-mt-5" :gutter="20">
		<el-button v-if="isMultipleSelection" @click="openMultipleShoesDialog">
			排产
		</el-button>
		<el-button @click="toggleSelectionMode">
			{{ isMultipleSelection ? "退出" : "选择多个鞋型" }}
		</el-button>
	</el-row>
	<el-table :data="inProductionTableData" style="width: 100%; margin-bottom: 20px" row-key="id" border
		default-expand-all @selection-change="handleSelectionChange" ref="table">
		<el-table-column label="订单信息">
			<el-table-column type="selection" width="55"></el-table-column>
			<el-table-column prop="orderRId" label="订单编号" sortable />
			<el-table-column prop="customerName" label="客户名称" sortable />
			<el-table-column prop="customerBrand" label="客户商标" sortable />
			<el-table-column prop="orderTotalShoes" label="订单总数量" sortable />
			<el-table-column prop="finishedShoes" label="已生产数量" sortable />
			<el-table-column prop="startDate" label="生产开始日期" sortable />
			<el-table-column prop="endDate" label="预计完成时间" sortable />
			<el-table-column prop="orderEndDate" label="截止日期" sortable />
			<el-table-column label="操作">
				<template #default="scope">
					<el-button link type="primary" size="small" @click="openNewWindow(scope.row)">
						订单详情
					</el-button>
				</template>
			</el-table-column>
		</el-table-column>
	</el-table>
	<el-row :gutter="20">
		<el-col :span="12" :offset="14">
			<el-pagination @size-change="handleInProdSizeChange" @current-change="handleInProdPageChange"
				:current-page="inProdPage" :page-sizes="[10, 20, 30, 40]" :page-size="inProdPageSize"
				layout="total, sizes, prev, pager, next, jumper" :total="inproductionTotalRows" />
		</el-col>
	</el-row>
	<el-dialog title="多鞋型排产页面" v-model="isMultipleShoesDialogVis" width="80%">
		<el-row :gutter="20">
			已选中鞋型：{{ selectedRows.map(row => row.shoeRId).toString() }}
		</el-row>
		<el-row :gutter="20">
			<el-form v-model="multipleShoesScheduleForm">
				<el-form-item label="裁断线号选择">
					<el-select v-model="multipleShoesScheduleForm.cuttingLineNumbers" placeholder="" @change=""
						multiple>
						<el-option v-for="item in productionLines['裁断']" :key="item" :label="item" :value="item">
						</el-option>
					</el-select>
				</el-form-item>
				<el-form-item label="裁断生产周期">
					<el-date-picker v-model="multipleShoesScheduleForm.cuttingDateRange" type="daterange" size="default"
						range-separator="至" :disabled-date="disableDate" value-format="YYYY-MM-DD">
					</el-date-picker>
				</el-form-item>
				<el-form-item label="针车预备线号选择">
					<el-select v-model="multipleShoesScheduleForm.preSewingLineNumbers" placeholder="" @change=""
						multiple>
						<el-option v-for="item in productionLines['针车预备']" :key="item" :label="item" :value="item">
						</el-option>
					</el-select>
				</el-form-item>
				<el-form-item label="针车预备生产周期">
					<el-date-picker v-model="multipleShoesScheduleForm.preSewingDateRange" type="daterange"
						size="default" range-separator="至" :disabled-date="disableDate" value-format="YYYY-MM-DD">
					</el-date-picker>
				</el-form-item>
				<el-form-item label="针车线号选择">
					<el-select v-model="multipleShoesScheduleForm.sewingLineNumbers" placeholder="" @change="" multiple>
						<el-option v-for="item in productionLines['针车']" :key="item" :label="item" :value="item">
						</el-option>
					</el-select>
				</el-form-item>
				<el-form-item label="针车生产周期">
					<el-date-picker v-model="multipleShoesScheduleForm.sewingDateRange" type="daterange" size="default"
						range-separator="至" :disabled-date="disableDate" value-format="YYYY-MM-DD">
					</el-date-picker>
				</el-form-item>
				<el-form-item label="成型线号选择">
					<el-select v-model="multipleShoesScheduleForm.moldingLineNumbers" placeholder="" @change=""
						multiple>
						<el-option v-for="item in productionLines['成型']" :key="item" :label="item" :value="item">
						</el-option>
					</el-select>
				</el-form-item>
				<el-form-item label="成型生产周期">
					<el-date-picker v-model="multipleShoesScheduleForm.moldingDateRange" type="daterange" size="default"
						range-separator="至" :disabled-date="disableDate" value-format="YYYY-MM-DD">
					</el-date-picker>
				</el-form-item>
			</el-form>
		</el-row>
		<template #footer>
			<span>
				<el-button type="primary" @click="isMultipleShoesDialogVis = false">返回</el-button>
				<el-button type="primary" @click="saveMultipleSchedules">保存</el-button>
			</span>
		</template>
	</el-dialog>
</template>
<script>
import axios from 'axios'
export default {
	props: ["character"],
	data() {
		return {
			inProductionTableData: [],
			inproductionTotalRows: 0,
			inProdPage: 1,
			inProdPageSize: 10,
			orderRIdSearch: "",
			selectedRowIds: [],
			customerNameSearch: "",
			customerBrandSearch: "",
			isMultipleSelection: false,
			selectedRows: [],
			isMultipleShoesDialogVis: false,
			multipleShoesScheduleForm: {
				cuttingLineNumbers: [],
				cuttingDateRange: [],
				preSewingLineNumbers: [],
				preSewingDateRange: [],
				sewingLineNumbers: [],
				sewingDateRange: [],
				moldingLineNumbers: [],
				moldingDateRange: [],
			},
		}
	},
	mounted() {
		this.getInproductionTableData()
	},
	methods: {
		handleSelectionChange(selection) {
			this.selectedRowIds = selection.map(row => row.orderId);
		},
		handleSearch() {
			this.currentPage = 1
			this.getInproductionTableData()
		},
		async getInproductionTableData() {
			const params = {
				"page": this.inProdPage,
				"pageSize": this.inProdPageSize,
				"orderRId": this.orderRIdSearch,
				"customerName": this.customerNameSearch,
				"customerBrand": this.customerBrandSearch
			}
			const response = await axios.get(`${this.$apiBaseUrl}/production/productionmanager/getinprogressorders`, { params })
			this.inProductionTableData = response.data.result
			this.inproductionTotalRows = response.data.total
			this.restoreSelection();
		},
		restoreSelection() {
			// this.$refs.table.clearSelection();
			console.log(this.selectedRowIds)
			this.inProductionTableData.forEach(row => {
				if (this.selectedRowIds.includes(row.orderId)) {
					this.$refs.table.toggleRowSelection(row, true);
				}
			});
		},
		handleInProdSizeChange(val) {
			this.inProdPageSize = val
			this.getInproductionTableData()
		},
		handleInProdPageChange(val) {
			this.inProdPage = val
			this.getInproductionTableData()
		},
		openNewWindow(rowData) {
			let url = ""
			let params = {
				"orderId": rowData.orderId,
				"orderRId": rowData.orderRId
			}
			const queryString = new URLSearchParams(params).toString();
			url = `${window.location.origin}/productiongeneral/productiondetail?${queryString}`
			window.open(url, '_blank')
		},
		calculateDailyProduction(dateRange) {
			if (dateRange && dateRange.length === 2) {
				const startDate = new Date(dateRange[0]);
				const endDate = new Date(dateRange[1]);
				const timeDiff = Math.abs(endDate - startDate);
				const diffDays = Math.ceil(timeDiff / (1000 * 60 * 60 * 24)) + 1;
				return (5000 / diffDays).toFixed(2);
			}
			return 0;
		},
	}
}
</script>
