<template>
	<el-container>
		<el-header height="">
			<AllHeader></AllHeader>
		</el-header>
		<el-main height="">
			<el-row :gutter="20" style="text-align: center">
				<el-col :span="24" :offset="0" style="font-size: xx-large; text-align: center">订单生产动态明细</el-col>
			</el-row>
			<el-row :gutter="20">
				<el-col :span="24" :offset="0">
					<el-descriptions title="订单信息" :column="2" border>
						<el-descriptions-item label="客户名称">{{
							orderInfo.customerName
						}}</el-descriptions-item>
						<el-descriptions-item label="订单编号">{{
							$props.orderRId
						}}</el-descriptions-item>
						<el-descriptions-item label="订单创建日期">{{
							orderInfo.orderStartDate
						}}</el-descriptions-item>
						<el-descriptions-item label="订单截止日期">{{
							orderInfo.orderEndDate
						}}</el-descriptions-item>
						<el-descriptions-item label="订单总数量">{{
							orderInfo.orderTotalShoes
						}}</el-descriptions-item>
						<el-descriptions-item label="订单总完成度百分比">{{
							orderPercentageText
						}}</el-descriptions-item>
					</el-descriptions>
				</el-col>
			</el-row>
			<el-button v-if="isMultipleSelection" @click="openMultipleShoesDialog">
				排产
			</el-button>
			<el-button @click="toggleSelectionMode">
				{{ isMultipleSelection ? "退出" : "选择多个鞋型" }}
			</el-button>
			<el-row :gutter="20" style="margin-top: 20px">
				<el-col :span="24" :offset="0">
					<el-table :data="orderShoeDataTable" border style="height: 800px"
						@selection-change="handleSelectionChange">
						<el-table-column v-if="isMultipleSelection" type="selection" width="55" />
						<el-table-column type="expand" label="展开">
							<template #default="props">
								<h3>鞋型详情</h3>
								<el-table :data="props.row.detail"
									:span-method="(params) => orderShoeDataTableSpanMethod(params, props.row.detail)"
									border>
									<el-table-column label="颜色" prop="colorName" />
									<el-table-column label="订单总数" prop="batchAmount" />
									<el-table-column label="裁断完成数量" prop="cuttingAmount" />
									<el-table-column label="预备完成数量" prop="preSewingAmount" />
									<el-table-column label="针车完成数量" prop="sewingAmount" />
									<el-table-column label="成型完成数量" prop="moldingAmount" />
								</el-table>
							</template>
						</el-table-column>
						<el-table-column prop="shoeRId" label="公司编号" width="100"></el-table-column>
						<el-table-column prop="customerProductName" label="客户型号" width="100"></el-table-column>
						<el-table-column prop="a" label="物料到货情况" width="110">
							<template #default="scope">
								<el-button type="primary" size="small" @click="openLogisticsDialog(scope.row)">
									详情
								</el-button>
							</template>
						</el-table-column>
						<el-table-column prop="percentageText" label="生产状态百分比"></el-table-column>
						<el-table-column prop="totalShoes" label="当前鞋型订单总数"></el-table-column>
						<el-table-column prop="status" label="状态"></el-table-column>
						<el-table-column label="操作">
							<template #default="scope">
								<el-button type="primary" size="small" @click="viewProductionSchedule(scope.row)">查看排期
								</el-button>
								<el-button size="small" @click="downloadInstructionForm(scope.row)">
									工艺指令单
								</el-button>
							</template>
						</el-table-column>
					</el-table>
				</el-col>
			</el-row>
			<el-dialog title="修改排产信息" v-model="isScheduleModify" width="95%">
				<el-tabs v-model="activeTab" type="card" tab-position="top" @tab-click="">
					<el-tab-pane v-for="tab in tabs" :key="tab.name" :label="tab.label" :name="tab.name">
						<el-row :gutter="20">
							<el-col :span="10" :offset="0">
								<span style="white-space: nowrap">
									{{ tab.lineLabel }}：
									<el-select v-model="tab.lineValue" placeholder="" @change="" multiple>
										<el-option v-for="item in productionLines[tab.name]" :key="item" :label="item"
											:value="item">
										</el-option>
									</el-select>
								</span>
							</el-col>
							<el-col :span="8" :offset="6">
								<el-descriptions title="" border>
									<el-descriptions-item label="外包状态">
										<div v-if="tab.isOutsourced == 0">
											未设置外包
										</div>
										<div v-else>
											已设置外包
										</div>
									</el-descriptions-item>
									<el-descriptions-item label="操作">
										<el-button v-if="tab.isOutsourced == 0" type="primary" size="default"
											@click="openOutsourceFlow()">启动外包流程</el-button>
										<el-button-group v-else>
											<el-button type="primary" size="default"
												@click="openOutsourceFlow()">查看外包流程</el-button>
										</el-button-group>
									</el-descriptions-item>
								</el-descriptions>
							</el-col>
						</el-row>
						<el-row :gutter="20">
							<el-col :span="10" :offset="0">
								<span>
									{{ tab.dateLabel }}：
									<el-date-picker v-model="tab.dateValue" type="daterange" size="default"
										range-separator="-" :disabled-date="disableDate" value-format="YYYY-MM-DD">
									</el-date-picker>
								</span>
							</el-col>
							<el-col :span="5" :offset="0">
								<el-button type="primary" size="default" @click="checkDateProductionStatus(tab)">{{
									tab.isDateStatusTableVis ? '关闭表格' : '查看工期内排产情况' }}</el-button>
							</el-col>
							<el-col :span="5" :offset="0">预计每天生产数量：{{ calculateDailyProduction(currentRow.totalShoes,
								tab.dateValue)
								}}</el-col>
						</el-row>
						<el-row :gutter="20">
							<el-table v-if="tab.isDateStatusTableVis" :data="tab.dateStatusTable" border stripe>
								<el-table-column type="expand">
									<template #default="props">
										<el-table :data="props.row.detail" border stripe>
											<el-table-column type="index" />
											<el-table-column label="订单号" prop="orderRId" />
											<el-table-column label="工厂型号" prop="shoeRId" />
											<el-table-column label="鞋型总数量" prop="totalAmount" />
											<el-table-column label="工段生产开始" prop="productionStartDate" />
											<el-table-column label="工段生产结束" prop="productionEndDate" />
											<el-table-column label="平均每天数量" prop="averageAmount" />
										</el-table>
									</template>
								</el-table-column>

								<el-table-column prop="date" label="日期"> </el-table-column>
								<el-table-column prop="orderShoeCount" label="已排产鞋型数"> </el-table-column>
								<el-table-column prop="predictAmount" label="预计当日现有生产量"> </el-table-column>
							</el-table>
						</el-row>
						<el-row>
							计划自产数量
						</el-row>
						<el-row :gutter="20">
							<el-col>
								<el-table :data="tab.productionAmountTable" border stripe :max-height="500">
									<el-table-column prop="colorName" label="颜色"></el-table-column>
									<el-table-column prop="size34" label="34">
										<template v-slot="scope">
											<el-input v-model="scope.row.size34" />
										</template>
									</el-table-column>
									<el-table-column prop="size35" label="35">
										<template v-slot="scope">
											<el-input v-model="scope.row.size35" />
										</template>
									</el-table-column>
									<el-table-column prop="size36" label="36">
										<template v-slot="scope">
											<el-input v-model="scope.row.size36" />
										</template>
									</el-table-column>
									<el-table-column prop="size37" label="37">
										<template v-slot="scope">
											<el-input v-model="scope.row.size37" />
										</template>
									</el-table-column>
									<el-table-column prop="size38" label="38">
										<template v-slot="scope">
											<el-input v-model="scope.row.size38" />
										</template>
									</el-table-column>
									<el-table-column prop="size39" label="39">
										<template v-slot="scope">
											<el-input v-model="scope.row.size39" />
										</template>
									</el-table-column>
									<el-table-column prop="size40" label="40">
										<template v-slot="scope">
											<el-input v-model="scope.row.size40" />
										</template>
									</el-table-column>
									<el-table-column prop="size41" label="41">
										<template v-slot="scope">
											<el-input v-model="scope.row.size41" />
										</template>
									</el-table-column>
									<el-table-column prop="size42" label="42">
										<template v-slot="scope">
											<el-input v-model="scope.row.size42" />
										</template>
									</el-table-column>
									<el-table-column prop="size43" label="43">
										<template v-slot="scope">
											<el-input v-model="scope.row.size43" />
										</template>
									</el-table-column>
									<el-table-column prop="size44" label="44">
										<template v-slot="scope">
											<el-input v-model="scope.row.size44" />
										</template>
									</el-table-column>
									<el-table-column prop="size45" label="45">
										<template v-slot="scope">
											<el-input v-model="scope.row.size45" />
										</template>
									</el-table-column>
									<el-table-column prop="size46" label="46">
										<template v-slot="scope">
											<el-input v-model="scope.row.size46" />
										</template>
									</el-table-column>
									<el-table-column prop="pairAmount" label="双数"></el-table-column>
									<el-table-column prop="totalAmount" label="颜色总数"></el-table-column>
								</el-table>
							</el-col>
						</el-row>
					</el-tab-pane>
				</el-tabs>
				<el-row :gutter="20" style="margin-top: 20px">
					<el-col :span="24" :offset="0">
						鞋型配码信息
						<el-table :data="shoeBatchInfo" :span-method="spanMethod" border stripe :max-height="500">
							<el-table-column prop="colorName" label="颜色"></el-table-column>
							<el-table-column prop="batchName" label="配码编号"></el-table-column>
							<el-table-column prop="size34" label="34"></el-table-column>
							<el-table-column prop="size35" label="35"></el-table-column>
							<el-table-column prop="size36" label="36"></el-table-column>
							<el-table-column prop="size37" label="37"></el-table-column>
							<el-table-column prop="size38" label="38"></el-table-column>
							<el-table-column prop="size39" label="39"></el-table-column>
							<el-table-column prop="size40" label="40"></el-table-column>
							<el-table-column prop="size41" label="41"></el-table-column>
							<el-table-column prop="size42" label="42"></el-table-column>
							<el-table-column prop="size43" label="43"></el-table-column>
							<el-table-column prop="size44" label="44"></el-table-column>
							<el-table-column prop="size45" label="45"></el-table-column>
							<el-table-column prop="size46" label="46"></el-table-column>
							<el-table-column prop="pairAmount" label="双数"></el-table-column>
							<el-table-column prop="totalAmount" label="颜色总数"></el-table-column>
						</el-table>
					</el-col>
				</el-row>
				<template #footer>
					<span>
						<el-button @click="isScheduleModify = false">取消</el-button>
						<el-button type="primary" @click="modifyProductionSchedule">保存</el-button>
						<el-button v-if="currentRow.status === '未排产'" type="success"
							@click="startProduction">开始生产</el-button>
					</span>
				</template>
			</el-dialog>
			<el-dialog title="鞋型所有材料物流信息" v-model="isMaterialLogisticVis" width="80%">
				<el-row :gutter="20">
					<el-col :span="24" :offset="0">
						<el-table :data="logisticsMaterialData" border stripe>
							<el-table-column prop="materialType" label="材料类型"></el-table-column>
							<el-table-column prop="materialName" label="材料名称"></el-table-column>
							<el-table-column prop="colorName" label="颜色"></el-table-column>
							<el-table-column prop="estimatedInboundAmount" label="核定用量"></el-table-column>
							<el-table-column prop="actualInboundAmount" label="采购数量"></el-table-column>
							<el-table-column prop="supplierName" label="供应商名称"></el-table-column>
							<el-table-column prop="materialArrivalDate" label="材料预计到达日期"></el-table-column>
							<el-table-column prop="status" label="材料状态"></el-table-column>
						</el-table>
					</el-col>
				</el-row>
				<el-row :gutter="20">
					<el-col :span="12" :offset="15">
						<el-pagination @size-change="handleSizeChange" @current-change="handlePageChange"
							:current-page="currentPage" :page-sizes="[10, 20, 30, 40]" :page-size="pageSize"
							layout="total, sizes, prev, pager, next, jumper" :total="logisticsRows" />
					</el-col>
				</el-row>
				<template #footer>
					<span>
						<el-button type="primary" @click="isMaterialLogisticVis = false">返回</el-button>
					</span>
				</template>
			</el-dialog>
			<el-dialog title="多鞋型排产页面" v-model="isMultipleShoesDialogVis" width="80%">
				<el-row :gutter="20">
					已选中鞋型：{{ selectedRows.map(row => row.shoeRId).toString() }}
				</el-row>
				<el-row :gutter="20">
					<el-form v-model="multipleShoesScheduleForm">
						<el-form-item label="裁断线号选择">
							<el-select v-model="multipleShoesScheduleForm.cuttingLineNumbers" placeholder="" @change=""
								multiple>
								<el-option v-for="item in productionLines['裁断']" :key="item" :label="item"
									:value="item">
								</el-option>
							</el-select>
						</el-form-item>
						<el-form-item label="裁断生产周期">
							<el-date-picker v-model="multipleShoesScheduleForm.cuttingDateRange" type="daterange"
								size="default" range-separator="至" :disabled-date="disableDate"
								value-format="YYYY-MM-DD">
							</el-date-picker>
						</el-form-item>
						<el-form-item label="针车预备线号选择">
							<el-select v-model="multipleShoesScheduleForm.preSewingLineNumbers" placeholder=""
								@change="" multiple>
								<el-option v-for="item in productionLines['针车预备']" :key="item" :label="item"
									:value="item">
								</el-option>
							</el-select>
						</el-form-item>
						<el-form-item label="针车预备生产周期">
							<el-date-picker v-model="multipleShoesScheduleForm.preSewingDateRange" type="daterange"
								size="default" range-separator="至" :disabled-date="disableDate"
								value-format="YYYY-MM-DD">
							</el-date-picker>
						</el-form-item>
						<el-form-item label="针车线号选择">
							<el-select v-model="multipleShoesScheduleForm.sewingLineNumbers" placeholder="" @change=""
								multiple>
								<el-option v-for="item in productionLines['针车']" :key="item" :label="item"
									:value="item">
								</el-option>
							</el-select>
						</el-form-item>
						<el-form-item label="针车生产周期">
							<el-date-picker v-model="multipleShoesScheduleForm.sewingDateRange" type="daterange"
								size="default" range-separator="至" :disabled-date="disableDate"
								value-format="YYYY-MM-DD">
							</el-date-picker>
						</el-form-item>
						<el-form-item label="成型线号选择">
							<el-select v-model="multipleShoesScheduleForm.moldingLineNumbers" placeholder="" @change=""
								multiple>
								<el-option v-for="item in productionLines['成型']" :key="item" :label="item"
									:value="item">
								</el-option>
							</el-select>
						</el-form-item>
						<el-form-item label="成型生产周期">
							<el-date-picker v-model="multipleShoesScheduleForm.moldingDateRange" type="daterange"
								size="default" range-separator="至" :disabled-date="disableDate"
								value-format="YYYY-MM-DD">
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
		</el-main>
	</el-container>
</template>

<script>
import AllHeader from '@/components/AllHeader.vue'
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus';
import { shoeBatchInfoTableSpanMethod } from '../../utils';
export default {
	props: ['orderId', 'orderRId'],
	components: {
		AllHeader
	},
	data() {
		return {
			orderPercentageText: '',
			orderShoeDataTable: [],
			isPreviewDialogVisible: false,
			isScheduleModify: false,
			isShoeScheduleVis: false,
			// schedule production
			activeTab: '裁断',
			cuttingLine: 1,
			cuttingDatePicker: '',
			sewPreLine: 1,
			sewPreDatePicker: '',
			dialogOrderSearch: '',
			isShoeScheduleVis: false,
			isScheduleVis: false,
			isScheduleModify: false,
			orderInfo: {
				customerName: '',
				orderRId: '',
				orderStartDate: '',
				orderEndDate: '',
				orderTotalShoes: ''
			},
			// index 0: 裁断，1：预备，2：针车，3：成型
			tabs: [
				{
					name: '裁断',
					label: '裁断排产',
					lineLabel: '裁断线号选择',
					dateLabel: '裁断工期选择',
					lineValue: [],
					dateValue: [],
					dateStatusTable: [],
					isOutsourced: 0,
					isDateStatusTableVis: false,
					productionAmountTable: [],
					productionSpanMethod: null,
					team: 0
				},
				{
					name: '针车预备',
					label: '针车预备排产',
					lineLabel: '针车预备线号选择',
					dateLabel: '针车预备工期选择',
					lineValue: [],
					dateValue: [],
					dateStatusTable: [],
					isOutsourced: 0,
					isDateStatusTableVis: false,
					productionAmountTable: [],
					productionSpanMethod: null,
					team: 1
				},
				{
					name: '针车',
					label: '针车排产',
					lineLabel: '针车线号选择',
					dateLabel: '针车工期选择',
					lineValue: [],
					dateValue: [],
					dateStatusTable: [],
					isOutsourced: 0,
					isDateStatusTableVis: false,
					productionAmountTable: [],
					productionSpanMethod: null,
					team: 1
				},
				{
					name: '成型',
					label: '成型排产',
					lineLabel: '成型线号选择',
					dateLabel: '成型工期选择',
					lineValue: [],
					dateValue: [],
					dateStatusTable: [],
					isOutsourced: 0,
					isDateStatusTableVis: false,
					productionAmountTable: [],
					productionSpanMethod: null,
					team: 2
				}
			],
			productionLines: {},
			currentRow: {},
			shoeBatchInfo: [],
			spanMethod: null,
			logisticsMaterialData: [],
			logisticsRows: 0,
			isMaterialLogisticVis: false,
			logisticsCurrentPage: 1,
			logisticsPageSize: 10,
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
		this.getOrderInfo()
		this.getProductionLineOptions()
	},
	methods: {
		async saveMultipleSchedules() {
			this.multipleShoesScheduleForm.cuttingStartDate = null
			this.multipleShoesScheduleForm.cuttingEndDate = null
			if (this.multipleShoesScheduleForm.cuttingDateRange.length == 2) {
				this.multipleShoesScheduleForm.cuttingStartDate = this.multipleShoesScheduleForm.cuttingDateRange[0]
				this.multipleShoesScheduleForm.cuttingEndDate = this.multipleShoesScheduleForm.cuttingDateRange[1]
			}
			this.multipleShoesScheduleForm.preSewingStartDate = null
			this.multipleShoesScheduleForm.preSewingEndDate = null
			if (this.multipleShoesScheduleForm.preSewingDateRange.length == 2) {
				this.multipleShoesScheduleForm.preSewingStartDate = this.multipleShoesScheduleForm.preSewingDateRange[0]
				this.multipleShoesScheduleForm.preSewingEndDate = this.multipleShoesScheduleForm.preSewingDateRange[1]
			}
			this.multipleShoesScheduleForm.sewingStartDate = null
			this.multipleShoesScheduleForm.sewingEndDate = null
			if (this.multipleShoesScheduleForm.sewingDateRange.length == 2) {
				this.multipleShoesScheduleForm.sewingStartDate = this.multipleShoesScheduleForm.sewingDateRange[0]
				this.multipleShoesScheduleForm.sewingEndDate = this.multipleShoesScheduleForm.sewingDateRange[1]
			}
			this.multipleShoesScheduleForm.moldingStartDate = null
			this.multipleShoesScheduleForm.moldingEndDate = null
			if (this.multipleShoesScheduleForm.moldingDateRange.length == 2) {
				this.multipleShoesScheduleForm.moldingStartDate = this.multipleShoesScheduleForm.moldingDateRange[0]
				this.multipleShoesScheduleForm.moldingEndDate = this.multipleShoesScheduleForm.moldingDateRange[1]
			}
			try {
				let data = {
					"orderShoeIdArr": this.selectedRows.map(row => row.orderShoeId),
					"scheduleForm": this.multipleShoesScheduleForm
				}
				await axios.patch(`${this.$apiBaseUrl}/production/productionmanager/savemultipleschedules`, data)
				ElMessage.success("保存成功")
			}
			catch (error) {
				ElMessage.error(error)
			}
		},
		openMultipleShoesDialog() {
			this.isMultipleShoesDialogVis = true
		},
		toggleSelectionMode() {
			this.isMultipleSelection = !this.isMultipleSelection;
		},
		handleSelectionChange(selection) {
			this.selectedRows = selection; // Stores selected rows
			console.log(this.selectedRows)
		},
		downloadInstructionForm(row) {

		},
		openLogisticsDialog(rowData) {
			this.logisticsCurrentPage = 1
			this.viewLogisticDetail(rowData)
			this.isMaterialLogisticVis = true
		},
		async viewLogisticDetail(row) {
			const params = {
				"page": this.logisticsCurrentPage,
				"pageSize": this.logisticsPageSize,
				"orderRId": row.orderRId,
				"shoeRId": row.shoeRId
			}
			const response = await axios.get(`${this.$apiBaseUrl}/warehouse/warehousemanager/getallmaterialinfo`, { params })
			this.logisticsMaterialData = response.data.result
			this.logisticsRows = response.data.total
		},
		handleLogisticsPageChange(val) {
			this.logisticsCurrentPage = val
			this.viewLogisticDetail()
		},
		handleLogisticsPageChange(val) {
			this.logisticsPageSize = val
			this.viewLogisticDetail()
		},
		async getOrderInfo() {
			let params = { orderId: this.$props.orderId }
			let response = await axios.get(`${this.$apiBaseUrl}/production/productionmanager/getorderinfo`, { params })
			this.orderInfo = response.data
			response = await axios.get(`${this.$apiBaseUrl}/production/productionmanager/getorderamount`, { params })
			this.orderInfo.orderTotalShoes = response.data.orderTotalShoes
			this.getOrderShoeTableData()
		},
		async getProductionLineOptions() {
			const response = await axios.get(`${this.$apiBaseUrl}/production/productionmanager/getproductionlines`)
			this.productionLines = response.data
		},
		async getOrderShoeTableData() {
			const params = { "orderId": this.$props.orderId }
			const response = await axios.get(`${this.$apiBaseUrl}/production/productionmanager/getorderproductiondetail`, { params })
			this.orderShoeDataTable = response.data
			let totalCuttingAmount = 0, totalSewingAmount = 0, totalMoldingAmount = 0
			let cuttingAmount = 0, sewingAmount = 0, moldingAmount = 0
			this.orderShoeDataTable.forEach(row => {
				let totalShoes = Number(row.totalShoes)
				cuttingAmount = 0, sewingAmount = 0, moldingAmount = 0
				row.detail.forEach(subRow => {
					cuttingAmount += Number(subRow.cuttingAmount)
					sewingAmount += Number(subRow.sewingAmount)
					moldingAmount += Number(subRow.moldingAmount)
				})
				let cuttingPercent = Math.round(cuttingAmount / totalShoes * 100)
				let sewingPercent = Math.round(sewingAmount / totalShoes * 100)
				let moldingPercent = Math.round(moldingAmount / totalShoes * 100)
				row.percentageText = `裁断:${cuttingPercent.toString()}% 针车:${sewingPercent.toString()}% 成型:${moldingPercent.toString()}%`
				totalCuttingAmount += cuttingAmount
				totalSewingAmount += sewingAmount
				totalMoldingAmount += moldingAmount
			})
			let orderTotalShoes = Number(this.orderInfo.orderTotalShoes)
			let totalCuttingPercent = Math.round(totalCuttingAmount / orderTotalShoes * 100)
			let totalSewingPercent = Math.round(totalSewingAmount / orderTotalShoes * 100)
			let totalMoldingPercent = Math.round(totalMoldingAmount / orderTotalShoes * 100)
			console.log(orderTotalShoes)
			this.orderPercentageText = `裁断:${totalCuttingPercent.toString()}% 针车:${totalSewingPercent.toString()}% 成型:${totalMoldingPercent.toString()}%`
		},
		async viewProductionSchedule(rowData) {
			this.isScheduleModify = true
			this.currentRow = rowData
			let params = { "orderShoeId": rowData.orderShoeId }
			let response = await axios.get(`${this.$apiBaseUrl}/production/productionmanager/getordershoescheduleinfo`, { params })
			this.tabs[0].lineValue = response.data.cuttingLineNumbers
			this.tabs[0].dateValue = [response.data.cuttingStartDate, response.data.cuttingEndDate]
			this.tabs[0].isOutsourced = response.data.isCuttingOutsourced

			this.tabs[1].lineValue = response.data.preSewingLineNumbers
			this.tabs[1].dateValue = [response.data.preSewingStartDate, response.data.preSewingEndDate]
			this.tabs[1].isOutsourced = response.data.isSewingOutsourced

			this.tabs[2].lineValue = response.data.sewingLineNumbers
			this.tabs[2].dateValue = [response.data.sewingStartDate, response.data.sewingEndDate]
			this.tabs[2].isOutsourced = response.data.isSewingOutsourced

			this.tabs[3].lineValue = response.data.moldingLineNumbers
			this.tabs[3].dateValue = [response.data.moldingStartDate, response.data.moldingEndDate]
			this.tabs[3].isOutsourced = response.data.isMoldingOutsourced
			this.getOrderShoeBatchInfo()
			this.getOrderShoeBatchEstimatedAmount()
		},
		async getOrderShoeBatchInfo() {
			const params = { "orderShoeId": this.currentRow.orderShoeId }
			const response = await axios.get(`${this.$apiBaseUrl}/production/getordershoebatchinfo`, { params })
			this.shoeBatchInfo = response.data
			this.spanMethod = shoeBatchInfoTableSpanMethod(this.shoeBatchInfo);
		},
		async getOrderShoeBatchEstimatedAmount() {
			const params = { "orderShoeId": this.currentRow.orderShoeId }
			const response = await axios.get(`${this.$apiBaseUrl}/production/productionmanager/getordershoebatchestimatedamount`, { params })
			let temp = []
			this.tabs.forEach(row => {
				if (response.data[row.team] === undefined) {
					row.productionAmountTable = []
					let color_totals = {}
					this.shoeBatchInfo.forEach(batchInfo => {
						console.log(batchInfo)
						if (!(batchInfo.colorName in color_totals)) {
							color_totals[batchInfo.colorName] = { ...batchInfo }
						}
						else {
							for (let i = 34; i < 47; i++) {
								color_totals[batchInfo.colorName][`size${i}`] += batchInfo[`size${i}`]
							}
							color_totals[batchInfo.colorName][`pairAmount`] += batchInfo[`pairAmount`]
						}
					})
					console.log(color_totals)
					for (let color_key in color_totals) {
						row.productionAmountTable.push(color_totals[color_key])
					}
				}
				else {
					row.productionAmountTable = response.data[row.team]
				}
				// row.productionSpanMethod = shoeBatchInfoTableSpanMethod(row.productionAmountTable)
				console.log(row.productionAmountTable)
			})
			this.tabs[1].productionAmountTable = this.tabs[2].productionAmountTable
		},
		async modifyProductionSchedule() {
			try {
				let data = {
					"orderShoeId": this.currentRow.orderShoeId,
					"cuttingInfo": {
						"lineValue": this.tabs[0].lineValue.join(","),
						"isOutsourced": this.tabs[0].isOutsourced,
						"startDate": this.tabs[0].dateValue[0],
						"endDate": this.tabs[0].dateValue[1]
					},
					"preSewingInfo": {
						"lineValue": this.tabs[1].lineValue.join(","),
						"isOutsourced": this.tabs[2].isOutsourced,
						"startDate": this.tabs[1].dateValue[0],
						"endDate": this.tabs[1].dateValue[1]
					},
					"sewingInfo": {
						"lineValue": this.tabs[2].lineValue.join(","),
						"isOutsourced": this.tabs[2].isOutsourced,
						"startDate": this.tabs[2].dateValue[0],
						"endDate": this.tabs[2].dateValue[1]
					},
					"moldingInfo": {
						"lineValue": this.tabs[3].lineValue.join(","),
						"isOutsourced": this.tabs[3].isOutsourced,
						"startDate": this.tabs[3].dateValue[0],
						"endDate": this.tabs[3].dateValue[1]
					}
				}
				await axios.patch(`${this.$apiBaseUrl}/production/productionmanager/editproductionschedule`, data)
				let temp_data = [this.tabs[0].productionAmountTable, this.tabs[2].productionAmountTable, this.tabs[3].productionAmountTable]
				data = []
				temp_data.forEach((table, index) => {
					table.forEach(row => {
						let obj = {
							"productionAmountId": row.productionAmountId,
							"orderShoeTypeId": row.orderShoeTypeId,
							"productionTeam": index,
						}
						for (let i = 34; i < 47; i++) {
							obj[`size${i}`] = row[`size${i}`]
						}
						data.push(obj)
					})
				})
				await axios.patch(`${this.$apiBaseUrl}/production/productionmanager/saveproductionamount`, data)
				ElMessage.success("修改成功")
			}
			catch (error) {
				ElMessage.error("修改失败")
			}
			this.isScheduleModify = false
		},
		async startProduction() {
			ElMessageBox.alert('点击确认后，你仍可修改排期，但推进流程操作不可撤回', '警告', {
				confirmButtonText: '确认',
				showCancelButton: true,
				cancelButtonText: '取消'
			}).then(async () => {
				try {
					await this.modifyProductionSchedule()
					const data = { "orderId": this.$props.orderId, "orderShoeId": this.currentRow.orderShoeId }
					await axios.patch(`${this.$apiBaseUrl}/production/productionmanager/startproduction`, data)
					ElMessage.success("生产开始")
					this.isScheduleModify = false
					this.getOrderShoeTableData()
				}
				catch (error) {
					console.log(error)
					ElMessage.error("排期异常")
				}
				this.isScheduleModify = false
				this.getOrderShoeTableData()
			})
		},
		async checkDateProductionStatus(tab) {
			if (tab.isDateStatusTableVis === true) {
				tab.isDateStatusTableVis = false
			}
			else {
				const params = { "startDate": tab.dateValue[0], "endDate": tab.dateValue[1], "team": tab.name }
				const response = await axios.get(`${this.$apiBaseUrl}/production/productionmanager/checkdateproductionstatus`, { params })
				tab.dateStatusTable = response.data
				tab.dateStatusTable.forEach(element => {
					let amount = 0
					element.detail.forEach(row => {
						row.averageAmount = this.calculateDailyProduction(row.totalAmount, [row.productionStartDate, row.productionEndDate])
						amount += Number(row.averageAmount)
					})
					element.predictAmount = amount;
				})
				tab.isDateStatusTableVis = true
			}
		},
		openOutsourceFlow() {
			const params = {
				"orderId": this.$props.orderId,
				"orderRId": this.$props.orderRId,
				"orderShoeId": this.currentRow.orderShoeId,
				"shoeRId": this.currentRow.shoeRId,
			}
			const queryString = new URLSearchParams(params).toString();
			const url = `${window.location.origin}/productiongeneral/productionoutsource?${queryString}`
			window.open(url, '_blank')
		},
		calculateDailyProduction(totalShoes, dateRange) {
			if (dateRange && dateRange.length === 2) {
				const startDate = new Date(dateRange[0]);
				const endDate = new Date(dateRange[1]);
				const timeDiff = Math.abs(endDate - startDate);
				const diffDays = Math.ceil(timeDiff / (1000 * 60 * 60 * 24)) + 1;
				return (Number(totalShoes) / diffDays).toFixed(2);
			}
			return 0;
		},
		disableDate(time) {
			let startDate = new Date(this.$props.orderStartDate)
			startDate.setDate(startDate.getDate() - 1)
			let endDate = new Date(this.$props.orderEndDate)
			return time.getTime() < startDate || time.getTime() > endDate.getTime();
		},
		statusJudge({ row, column, rowIndex, columnIndex }) {
			const progressColumns = ['fabricCuttingProgress', 'preproductionProgress', 'sewingProgress', 'moldingProgress'];
			const columnProperty = column.property;
			let style = {
				background: '',
				color: '#fff',
				opacity: 0.8
			};
			if (progressColumns.includes(columnProperty)) {
				const [current, total] = row[columnProperty].split('/').map(Number);
				if (current === total) {
					style.background = 'rgba(0, 128, 0, 0.8)'; // Green background for complete progress
					return style
				}

			}
			if (row[columnProperty].includes('已定')) {
				style.background = 'rgba(255, 255, 0, 0.8)'; // Yellow background for "已定"
				style.color = '#000'
				return style
			} else if (row[columnProperty].includes('已到')) {
				style.background = 'rgba(0, 128, 0, 0.8)'; // Green background for "已到"
				return style
			}
			if (columnProperty === 'productionStatus' && row.productionStatus === '100%') {
				style.background = 'rgba(0, 128, 0, 0.8)'; // Green background for 100% completion
				return style
			}
		},
		orderShoeDataTableSpanMethod({ row, column, rowIndex, columnIndex }, tableData) {
			// Merging 'colorName'
			if (columnIndex === 0) {
				const currentColor = tableData[rowIndex].colorName;
				// Skip rows already merged
				if (rowIndex > 0 && tableData[rowIndex - 1].colorName === currentColor) {
					return [0, 0]; // Skip this cell
				}

				// Calculate the rowspan for the current 'colorName'
				let rowspan = 1;
				for (let i = rowIndex + 1; i < tableData.length; i++) {
					if (tableData[i].colorName === currentColor) {
						rowspan++;
					} else {
						break;
					}
				}

				return [rowspan, 1]; // Set the rowspan for merging, and colspan = 1
			}
		}
	}
}
</script>
