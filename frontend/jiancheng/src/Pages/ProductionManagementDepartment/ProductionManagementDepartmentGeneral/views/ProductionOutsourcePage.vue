<template>
	<el-container>
		<el-header class="app-header">
			<AllHeader></AllHeader>
		</el-header>
		<el-main height="">
			<el-row :gutter="20" style="text-align: center">
				<el-col :span="24" :offset="0" style="font-size: xx-large; text-align: center">订单鞋型外包页面</el-col>
			</el-row>
			<el-row :gutter="20">
				<el-col :span="24" :offset="0">
					<el-descriptions title="订单信息" :column="3" border>
						<el-descriptions-item label="客户名称">{{ orderInfo.customerName }}</el-descriptions-item>
						<el-descriptions-item label="鞋型号">{{ orderInfo.shoeRId }}</el-descriptions-item>
						<el-descriptions-item label="订单编号">{{ orderInfo.orderRId }}</el-descriptions-item>
						<el-descriptions-item label="订单创建日期">{{ orderInfo.orderStartDate }}</el-descriptions-item>
						<el-descriptions-item label="订单截止日期">{{ orderInfo.orderEndDate }}</el-descriptions-item>
					</el-descriptions>
				</el-col>
			</el-row>
			<el-row :gutter="20" style="margin-top: 20px">
				<el-col :span="24" :offset="0">
					订单鞋型数量
					<el-table :data="shoeInfo" :span-method="shoeBatchInfoTableSpanMethod" border stripe
						:max-height="500">
						<el-table-column prop="colorName" label="颜色"></el-table-column>
						<el-table-column prop="totalAmount" label="颜色总数"></el-table-column>
						<el-table-column v-for="column in filteredColumns" :key="column.prop" :prop="column.prop"
							:label="column.label"></el-table-column>
					</el-table>
				</el-col>
			</el-row>
			<el-row :gutter="20">
				现有外包流程
				<el-table :data="outsourceInfo" border stripe scrollbar-always-on>
					<el-table-column prop="outsourceType" label="外包类型"></el-table-column>
					<el-table-column prop="outsourceFactory.value" label="外包厂家"></el-table-column>
					<el-table-column prop="outsourceAmount" label="外包数量"></el-table-column>
					<el-table-column prop="outsourceStartDate" label="外包开始日期"></el-table-column>
					<el-table-column prop="outsourceEndDate" label="外包结束日期"></el-table-column>
					<el-table-column prop="outsourceStatus" label="状态">
						<template v-slot="scope">
							<el-tooltip v-if="scope.row.outsourceStatus === '被驳回'" effect="dark"
								:content="scope.row.rejectionReason">
								<span class="rejected">{{ scope.row.outsourceStatus }}</span>
							</el-tooltip>
							<span v-else>{{ scope.row.outsourceStatus }}</span>
						</template>
					</el-table-column>
					<el-table-column label="操作" fixed="right" width="180">
						<template #default="scope">
							<el-button-group>
								<el-button v-if="outsourceOutboundStatus.includes(scope.row.outsourceStatus)"
									type="primary" size="small" @click="checkOutboundInfo(scope.row)">出库情况</el-button>
								<el-button v-if="outsourceReadOnlyStatus.includes(scope.row.outsourceStatus)"
									type="primary" size="small" @click="editRow(scope.row, 0)">查看</el-button>
								<el-button v-if="outsourceEditStatus.includes(scope.row.outsourceStatus)" type="primary"
									size="small" @click="editRow(scope.row, 1)">编辑</el-button>
								<el-button v-if="outsourceEditStatus.includes(scope.row.outsourceStatus)" type="warning"
									size="small" @click="submitOutsourceInfo(scope.row)">提交</el-button>
								<el-button v-if="outsourceEditStatus.includes(scope.row.outsourceStatus)" size="small"
									type="danger" @click="deleteRow(scope.row)">删除</el-button>
							</el-button-group>
						</template>
					</el-table-column>
				</el-table>
			</el-row>
			<el-row :gutter="20">
				<el-col :span="6" :offset="0">
					<el-button type="primary" size="default" @click="editRow(null, 1)">新建外包流程</el-button>
				</el-col>
			</el-row>
		</el-main>
	</el-container>
	<el-dialog title="外包编辑页面" v-model="showOutsourceEditPage" width="80%">
		<el-form :model="outsourceForm" :rules="rules" ref="outsourceForm" class="custom-form">
			<el-form-item label="外包类型" prop="outsourceType">
				<el-select v-model="outsourceForm.outsourceType"  filterable
					clearable v-if="!this.readOnly">
					<el-option v-for="item in ['裁断+针车', '针车']" :key="item" :label="item" :value="item">
					</el-option>
				</el-select>
				<span v-if="this.readOnly">{{ outsourceForm.outsourceType }}</span>
			</el-form-item>
			<el-form-item label="外包厂家" prop="selectedOutsourceValue">
				<template #default="scope">
					<div style="display: flex; align-items: center; gap: 10px;">
						<el-autocomplete v-model="outsourceForm.selectedOutsourceValue" :fetch-suggestions="querySearch"
							placeholder="" clearable  v-if="!this.readOnly" value-key="value" @select="onProductSelect">
						</el-autocomplete>
						<el-input v-model="outsourceForm.selectedOutsourceValue" readonly v-if="this.readOnly"></el-input>
						<el-button @click="addOutsourceFactory(outsourceForm.selectedOutsourceValue)">添加厂家</el-button>
					</div>
				</template>
			</el-form-item>
			<el-form-item label="外包周期" prop="outsourcePeriodArr">
				<el-date-picker v-model="outsourceForm.outsourcePeriodArr" :disabled="readOnly" type="daterange"
					value-format="YYYY-MM-DD" response range-separator="至">
				</el-date-picker>
			</el-form-item>
			<el-form-item label="外发材料" prop="materialRequired">
				<el-radio-group v-model="outsourceForm.materialRequired" :disabled="readOnly">
					<el-radio :value="true">是</el-radio>
					<el-radio :value="false">否</el-radio>
				</el-radio-group>
			</el-form-item>
			<el-form-item label="材料出货日期" prop="materialEstimatedOutboundDate">
				<el-date-picker v-model="outsourceForm.materialEstimatedOutboundDate" type="date"
					value-format="YYYY-MM-DD" response :disabled="outsourceForm.materialRequired == false || readOnly"
					placeholder="选择日期时间">
				</el-date-picker>
			</el-form-item>
			<el-form-item label="外发半成品" prop="semifinishedRequired">
				<el-radio-group v-model="outsourceForm.semifinishedRequired" :disabled="readOnly">
					<el-radio :value="true">是</el-radio>
					<el-radio :value="false">否</el-radio>
				</el-radio-group>
			</el-form-item>
			<el-form-item label="半成品发货日期" prop="semifinishedEstimatedOutboundDate">
				<el-date-picker v-model="outsourceForm.semifinishedEstimatedOutboundDate" type="date"
					value-format="YYYY-MM-DD" response
					:disabled="outsourceForm.semifinishedRequired == false || readOnly" placeholder="选择日期时间">
				</el-date-picker>
			</el-form-item>
			<el-form-item label="最迟交货日期" prop="deadlineDate">
				<el-date-picker v-model="outsourceForm.deadlineDate" :disabled="readOnly" type="date"
					value-format="YYYY-MM-DD" response placeholder="选择日期时间">
				</el-date-picker>
			</el-form-item>
		</el-form>
		<el-row :gutter="20" style="margin-top: 20px">
			<el-col :span="24" :offset="0">
				订单鞋型数量
				<el-table :data="shoeInfo" :span-method="shoeBatchInfoTableSpanMethod" border stripe :max-height="500">
					<el-table-column prop="colorName" label="颜色"></el-table-column>
					<el-table-column prop="totalAmount" label="颜色总数"></el-table-column>
					<el-table-column v-for="column in filteredColumns" :key="column.prop" :prop="column.prop"
						:label="column.label"></el-table-column>
				</el-table>
			</el-col>
		</el-row>
		<el-row :gutter="20">
			<el-col :span="24">
				外包数量
				<el-table :data="outsourceForm.outsourceShoeBatchInfo"
					:span-method="outsourceShoeBatchInfoTableSpanMethod" border stripe :max-height="500">
					<el-table-column prop="colorName" label="颜色"></el-table-column>
					<el-table-column prop="totalAmount" label="颜色总数"></el-table-column>
					<el-table-column v-for="column in filteredColumns" :key="column.prop" :prop="column.prop"
						:label="column.label">
						<template v-slot="scope">
							<el-input v-model="scope.row[column.prop]" :disabled="readOnly" />
						</template>
					</el-table-column>
				</el-table>
			</el-col>
		</el-row>
		<template #footer>
			<span>
				<el-button type="" @click="showOutsourceEditPage = false">退出</el-button>
				<el-button v-if="!readOnly" type="primary" @click="saveOutsourceInfo">保存</el-button>
			</span>
		</template>
	</el-dialog>
	<el-dialog title="外包物料发货情况查询" v-model="isOutsourceLogistic" width="80%">
		<el-row :gutter="20">
			<el-col :span="24" :offset="0"> 半成品发货状态： </el-col>
			<el-table :data="semifinishedLogisticData" border stripe>
				<el-table-column prop="semifinishedAmount" label="发货数量"></el-table-column>
				<el-table-column prop="semifinishedStatus" label="发货状态"></el-table-column>
				<el-table-column prop="outboundDatetime" label="发货日期"></el-table-column>
				<el-table-column prop="semifinishedEstimatedOutboundDate" label="预计发货日期"></el-table-column>
			</el-table>
		</el-row>
		<el-row :gutter="20">
			<el-col :span="24" :offset="0"> 材料发货状态： </el-col>
			<el-table :data="materialLogisticData" border stripe>
				<el-table-column prop="materialType" label="材料类型" />
				<el-table-column prop="materialName" label="材料名称" />
				<el-table-column prop="colorName" label="颜色" />
				<el-table-column prop="materialUnit" label="单位" />
				<el-table-column prop="outboundAmount" label="发货数量" />
				<el-table-column prop="outsourceStatus" label="发货状态" />
				<el-table-column prop="outboundDatetime" label="发货日期"></el-table-column>
				<el-table-column prop="materialEstimateOutboundDate" label="预计发货日期"></el-table-column>
			</el-table>
		</el-row>
		<template #footer>
			<span>
				<el-button type="primary" @click="isOutsourceLogistic = false">确认</el-button>
			</span>
		</template>
	</el-dialog>
</template>

<script>
import AllHeader from '@/components/AllHeader.vue'
import axios from 'axios'
import { ElMessage } from 'element-plus';
import { shoeBatchInfoTableSpanMethod, outsourceReadOnlyStatus, outsourceOutboundStatus, outsourceEditStatus } from '../../utils';
export default {
	props: ['orderId', 'orderShoeId'],
	components: {
		AllHeader
	},
	data() {
		return {
			currentRow: [],
			readOnly: false,
			outsourceReadOnlyStatus,
			outsourceOutboundStatus,
			outsourceEditStatus,
			isOutsourceLogistic: false,
			isOutsourcePreviewVis: false,
			showOutsourceEditPage: false,
			factoryOptions: [],
			semifinishedLogisticData: [],
			materialLogisticData: [],
			outsourceInfo: [],
			shoeInfo: [],
			productionDepartments: [],
			totalShoes: 0,
			template: {
				outsourceInfoId: null,
				outsourceType: null,
				outsourceFactory: null,
				outsourcePeriodArr: null,
				semifinishedRequired: false,
				semifinishedEstimatedOutboundDate: null,
				deadlineDate: null,
				materialEstimatedOutboundDate: null,
				materialRequired: false,
				outsourceShoeBatchInfo: [],
			},
			outsourceForm: {},
			outsourceShoeBatchInfoTableSpanMethod: null,
			shoeBatchInfoTableSpanMethod: null,
			orderInfo: {
				customerName: '',
				orderRId: '',
				orderStartDate: '',
				orderEndDate: '',
				orderTotalShoes: '',
			},
			shoeSizeColumns: [],
			showError: false,
			rules: {
				outsourceType: [
					{ required: true, message: '此项为必填项', trigger: 'change' },
				],
				selectedOutsourceValue: [
					{ required: true, message: '此项为必填项', trigger: 'change' },
				],
				outsourcePeriodArr: [
					{ required: true, message: '此项为必填项', trigger: 'change' },
				],
				materialRequired: [
					{ required: true, message: '此项为必填项', trigger: 'change' },
				],
				materialEstimatedOutboundDate: [
					{
						validator: (rule, value, callback) => {
							// If field1 is "Yes", make field2 required
							if (this.outsourceForm.materialRequired === true && !value) {
								callback(new Error('此项为必填项'));
							} else {
								callback();
							}
						},
						trigger: 'blur'
					}
				],
				semifinishedRequired: [
					{ required: true, message: '此项为必填项', trigger: 'change' },
				],
				semifinishedEstimatedOutboundDate: [
					{
						validator: (rule, value, callback) => {
							// If field1 is "Yes", make field2 required
							if (this.outsourceForm.semifinishedRequired === true && !value) {
								callback(new Error('此项为必填项'));
							} else {
								callback();
							}
						},
						trigger: 'blur'
					}
				],
				deadlineDate: [
					{ required: true, message: '此项为必填项', trigger: 'change' },
				],
			},
		}
	},
	mounted() {
		this.getShoeSizesName()
		this.getOrderShoeInfo()
		this.getProductionDepartments()
		this.getOrderShoeBatchInfo()
		this.getOutsourceInfo()
	},
	computed: {
		filteredColumns() {
			return this.shoeSizeColumns.filter(column =>
				this.shoeInfo.some(row => row[column.prop] !== undefined && row[column.prop] !== null && row[column.prop] !== 0)
			);
		}
	},
	methods: {
		onProductSelect(item) {
			this.outsourceForm.selectedOutsourceId = item.id
			this.outsourceForm.selectedOutsourceValue = item.value
		},
		querySearch(queryString, cb) {
			let result = []
			if (queryString === "null" || queryString === '') {
				this.factoryOptions.forEach(factory => {result.push({id: factory.id, value: factory.value})})
				cb(result);
			}
			else {
				const matchObj = queryString
					? this.factoryOptions.filter(factory =>
						factory.value.toLowerCase().indexOf(queryString.toLowerCase()) === 0
					)
					: []
				matchObj.forEach(row => {
					result.push({ id: row.id, value: row.value })
				})
				cb(result)
			}
		},
		async addOutsourceFactory(name) {
            try {
				let data = {"name": name}
                const response = await axios.post(`${this.$apiBaseUrl}/general/addnewoutsourcefactory`, data)
                ElMessage.success(response.data.message)
				this.outsourceForm.selectedOutsourceId = response.data.factoryId
				this.getAllOutsourceFactories()
            }
            catch (error) {
                ElMessage.error(error.response.data.message)
            }
		},
		async getShoeSizesName() {
			let params = { "orderId": this.$props.orderId }
			let response = await axios.get(`${this.$apiBaseUrl}/batchtype/getorderbatchtype`, { params })
			this.shoeSizeColumns = response.data
		},
		async getOrderShoeInfo() {
			let params = { "orderId": this.$props.orderId, "orderShoeId": this.$props.orderShoeId }
			let response = await axios.get(`${this.$apiBaseUrl}/production/productionmanager/getorderinfo`, { params })
			this.orderInfo = response.data
			response = await axios.get(`${this.$apiBaseUrl}/production/productionmanager/getorderamount`, { params })
			this.orderInfo.orderTotalShoes = response.data.orderTotalShoes
		},
		async editRow(rowData, number) {
			this.getAllOutsourceFactories()
			// 0: read only, 1: edit
			if (rowData === null) {
				this.outsourceForm = { ...this.template, selectedOutsourceId: null, selectedOutsourceValue: null }
				this.outsourceForm.outsourceShoeBatchInfo = JSON.parse(JSON.stringify(this.shoeInfo));
				this.readOnly = false
				// this.outsourceForm.outsourceShoeBatchInfo.forEach(row => {
				// 	for (let i = 34; i < 47; i++) {
				// 		row[`size${i}Amount`] = 0
				// 	}
				// 	row["totalAmount"] = 0
				// })
			}
			else {
				this.outsourceForm = {...rowData, selectedOutsourceId: rowData.outsourceFactory.id, selectedOutsourceValue: rowData.outsourceFactory.value}
				let params = { "orderShoeId": this.$props.orderShoeId, "outsourceInfoId": rowData.outsourceInfoId }
				let response = await axios.get(`${this.$apiBaseUrl}/production/productionmanager/getoutsourcebatchinfo`, { params })
				this.outsourceForm.outsourceShoeBatchInfo = response.data
				if (number == 0) {
					this.readOnly = true
				}
				else {
					this.readOnly = false
				}
			}
			this.currentRow = rowData
			this.showOutsourceEditPage = true
		},
		async deleteRow(rowData) {
			const params = { "orderShoeId": this.$props.orderShoeId, "outsourceInfoId": rowData.outsourceInfoId }
			try {
				await axios.delete(`${this.$apiBaseUrl}/production/productionmanager/deleteoutsourceinfo`, { params })
				ElMessage.success("删除成功")
			}
			catch (error) {
				console.log(error)
				ElMessage.error("删除失败")
			}
			this.getOutsourceInfo()
		},
		async getAllOutsourceFactories() {
			const response = await axios.get(`${this.$apiBaseUrl}/general/getalloutsourcefactories`)
			this.factoryOptions = response.data
		},
		async getProductionDepartments() {
			const response = await axios.get(`${this.$apiBaseUrl}/production/productionmanager/getproductiondepartments`)
			this.productionDepartments = response.data
		},
		async getOrderShoeBatchInfo() {
			let params = { "orderShoeId": this.$props.orderShoeId }
			let response = await axios.get(`${this.$apiBaseUrl}/production/productionmanager/getordershoetypeamount`, { params })
			this.shoeInfo = response.data
			this.shoeBatchInfoTableSpanMethod = shoeBatchInfoTableSpanMethod(this.shoeInfo)
		},
		async getOutsourceInfo() {
			const params = { "orderShoeId": this.$props.orderShoeId }
			const response = await axios.get(`${this.$apiBaseUrl}/production/productionmanager/getordershoeoutsourceinfo`, { params })
			this.outsourceInfo = response.data
			this.outsourceInfo.forEach(row => {
				row.outsourcePeriodArr = [row.outsourceStartDate, row.outsourceEndDate]
			})
		},
		async checkOutboundInfo(rowData) {
			const params = { "outsource_info_id": rowData.outsourceInfoId }
			let response = await axios.get(`${this.$apiBaseUrl}/production/productionmanager/getoutsourcesemifinishedshipping`, { params })
			this.semifinishedLogisticData = response.data
			response = await axios.get(`${this.$apiBaseUrl}/production/productionmanager/getoutsourcematerialshipping`, { params })
			this.materialLogisticData = response.data
			this.isOutsourceLogistic = true

		},
		async saveOutsourceInfo() {
			this.$refs.outsourceForm.validate(async (valid) => {
				if (valid) {
					console.log("Form is valid. Proceeding with submission.");
					console.log(this.outsourceForm.selectedOutsourceId)
					console.log(this.outsourceForm.selectedOutsourceValue)
					let element = {
						"outsourceInfoId": this.outsourceForm.outsourceInfoId,
						"type": this.outsourceForm.outsourceType,
						"factoryId": this.outsourceForm.selectedOutsourceId,
						"outsourceStartDate": this.outsourceForm.outsourcePeriodArr[0],
						"outsourceEndDate": this.outsourceForm.outsourcePeriodArr[1],
						"semifinishedRequired": this.outsourceForm.semifinishedRequired,
						"semifinishedEstimatedOutboundDate": this.outsourceForm.semifinishedEstimatedOutboundDate,
						"deadlineDate": this.outsourceForm.deadlineDate,
						"materialRequired": this.outsourceForm.materialRequired,
						"materialEstimatedOutboundDate": this.outsourceForm.materialEstimatedOutboundDate,
						"outsourceAmount": this.outsourceForm.outsourceShoeBatchInfo,
						"orderShoeId": this.$props.orderShoeId
					}
					try {
						await axios.put(`${this.$apiBaseUrl}/production/productionmanager/storeoutsourceforordershoe`, element)
						ElMessage.success("保存成功")
						this.showOutsourceEditPage = false
					}
					catch (error) {
						console.log(error)
						ElMessage.error("保存失败")
					}
					this.getOutsourceInfo()
				} else {
					console.log("Form has validation errors.");
				}
			})
		},
		async submitOutsourceInfo(row) {
			let inputData = { "outsourceInfoId": row.outsourceInfoId }
			try {
				await axios.patch(`${this.$apiBaseUrl}/production/productionmanager/submitoutsourceinfo`, inputData)
				ElMessage.success("提交成功")
			}
			catch (error) {
				console.log(error)
				ElMessage.error("提交失败")
			}
			this.getOutsourceInfo()
		},
	}
}
</script>
<style scoped>
.error-text {
	color: red;
	font-size: 12px;
}

.custom-form {
	width: 400px;
}
</style>