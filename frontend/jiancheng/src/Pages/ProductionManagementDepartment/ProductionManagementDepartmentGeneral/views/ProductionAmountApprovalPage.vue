<template>
    <el-container>
        <el-header class="app-header">
            <AllHeader></AllHeader>
        </el-header>
        <el-main height="">
            <el-row :gutter="20" style="text-align: center">
                <el-col :span="24" :offset="0" style="font-size: xx-large; text-align: center">订单鞋型数量审批页面</el-col>
            </el-row>
            <el-row :gutter="20">
                <el-col :span="24" :offset="0">
                    <el-descriptions title="订单及鞋型信息" border column="2">
                        <el-descriptions-item label="订单号">{{ orderInfo.orderRId }}</el-descriptions-item>
                        <el-descriptions-item label="鞋型号">{{ orderInfo.shoeRId }}</el-descriptions-item>
                        <el-descriptions-item label="客户型号">{{ orderInfo.customerProductName }}</el-descriptions-item>
                        <el-descriptions-item label="订单截止日期">{{ orderInfo.orderEndDate }}</el-descriptions-item>
                    </el-descriptions>
                </el-col>
            </el-row>
            <el-row :gutter="20">
                <el-col :span="12" :offset="0">
                    数量单日期范围限制：
                    <el-date-picker v-model="datePeriod" type="daterange" value-format="YYYY-MM-DD" clearable
                        start-placeholder="起始日期" end-placeholder="截止日期" @change="getAmountListData"
                        @clear="getAmountListData">
                    </el-date-picker>
                </el-col>
                <el-col :span="4" :offset="0" style="white-space: nowrap">
                    工段选择：
                    <el-select v-model="departSelect" value-key="" placeholder="" clearable filterable
                        @change="getAmountListData" @clear="getAmountListData">
                        <el-option v-for="item in ['全部', '裁断', '针车预备', '针车', '成型']" :key="item" :label="item"
                            :value="item">
                        </el-option>
                    </el-select>
                </el-col>
            </el-row>
            <el-row :gutter="20">
                <el-col :span="24" :offset="0">
                    <el-table :data="amountListData" border stripe>
                        <el-table-column prop="creationDate" label="数量单日期"></el-table-column>
                        <el-table-column prop="submissionDate" label="提交日期"></el-table-column>
                        <el-table-column prop="team" label="工段"></el-table-column>
                        <el-table-column prop="startDate" label="生产起始日期"></el-table-column>
                        <el-table-column prop="endDate" label="生产结束日期"></el-table-column>
                        <el-table-column prop="reportAmount" label="上报数量"></el-table-column>
                        <el-table-column prop="reportStatus" label="状态"></el-table-column>
                        <el-table-column label="操作">
                            <template #default="scope">
                                <el-button v-if="scope.row.reportStatus === '未审批'" type="primary" size="default"
                                    @click="openApprovalDialog(scope.row)">审批</el-button>
                                <el-button
                                    v-else-if="scope.row.reportStatus === '已审批' || scope.row.reportStatus === '被驳回'"
                                    type="primary" size="default" @click="openApprovalDialog(scope.row)">查看</el-button>
                            </template>
                        </el-table-column>
                    </el-table>
                </el-col>
            </el-row>
            <el-row :gutter="20">
                <el-col :span="12" :offset="15">
                    <el-pagination @size-change="handleSizeChange" @current-change="handlePageChange"
                        :current-page="currentPage" :page-sizes="[10, 20, 30, 40]" :page-size="pageSize"
                        layout="total, sizes, prev, pager, next, jumper" :total="totalRows" />
                </el-col>
            </el-row>
        </el-main>
    </el-container>
    <el-dialog title="数量审批界面" v-model="isAmountApprovalVis" width="50%">
        <QuantityReportTable v-model:tableData="quantityReportData" :orderShoeId="$props.orderShoeId"
            :editable="false" />
        <template #footer>
            <span>
                <el-button @click="isAmountApprovalVis = false">返回</el-button>
                <el-button v-if="this.currentRow.reportStatus === '未审批'" type="danger"
                    @click="openRefusalDialog">驳回请求</el-button>
                <el-button v-if="this.currentRow.reportStatus === '未审批'" type="primary"
                    @click="openConfirmDialog">审批通过</el-button>
            </span>
        </template>
    </el-dialog>
    <el-dialog title="驳回审批请求" v-model="isRefuseApprovalVis" width="30%">
        <el-row :gutter="20">
            <el-col :span="24" :offset="0">
                请填写驳回原因（不超过20字）：
                <el-input v-model="refuseReason" type="textarea" placeholder="" resize="none" clearable
                    @change=""></el-input>

            </el-col>
        </el-row>
        <template #footer>
            <span>
                <el-button @click="isRefuseApprovalVis = false">取消</el-button>
                <el-button type="success" @click="confirmRefusal">确认</el-button>
            </span>
        </template>
    </el-dialog>
</template>
<script>
import AllHeader from '@/components/AllHeader.vue'
import axios from 'axios'
import { ElMessage } from 'element-plus';
import QuantityReportTable from '../../ProductionSharedPages/QuantityReportPages/QuantityReportTable.vue';
export default {
    props: ['orderShoeId', 'orderId'],
    components: {
        AllHeader,
        QuantityReportTable
    },
    data() {
        return {
            currentPage: 1,
            pageSize: 10,
            totalRows: 0,
            isRefuseApprovalVis: false,
            isAmountApprovalVis: false,
            refuseReason: '',
            datePeriod: [],
            departSelect: '',
            amountListData: [],
            currentRow: {},
            quantityReportData: [],
            orderInfo: {},
        }
    },
    mounted() {
        this.getOrderInfo()
        this.getAmountListData()
    },
    methods: {
        async getOrderInfo() {
            let params = { "orderId": this.$props.orderId, "orderShoeId": this.$props.orderShoeId }
            let response = await axios.get(`${this.$apiBaseUrl}/production/productionmanager/getorderinfo`, { params })
            this.orderInfo = response.data
        },
        async getAmountListData() {
            let startDate = null, endDate = null
            if (this.datePeriod) {
                startDate = this.datePeriod[0]
                endDate = this.datePeriod[1]
            }
            const params = {
                "page": this.currentPage,
                "pageSize": this.pageSize,
                "orderShoeId": this.$props.orderShoeId,
                "searchStartDate": startDate,
                "searchEndDate": endDate,
                "team": this.departSelect,
            }
            const response = await axios.get(`${this.$apiBaseUrl}/production/productionmanager/getsubmittedquantityreports`, { params })
            this.amountListData = response.data.result
            this.totalRows = response.data.totalLength
        },
        handleSizeChange(val) {
            this.pageSize = val
            this.getAmountListData()
        },
        handlePageChange(val) {
            this.currentPage = val
            this.getAmountListData()
        },
        async openApprovalDialog(rowData) {
            let teamId = -1
            if (rowData.team == "裁断")
                teamId = 0
            else if (rowData.team == "针车预备")
                teamId = 1
            else if (rowData.team == "针车")
                teamId = 2
            else if (rowData.team == "成型")
                teamId = 3
            this.currentRow = rowData
            let params = { reportId: rowData.reportId, team: teamId }
            let response = await axios.get(`${this.$apiBaseUrl}/production/getquantityreportdetail`, { params })
            this.quantityReportData = []
            response.data.forEach(row => {
                row["toDateAmount"] = 0
                row.productionLinesAmount.forEach(amountObj => {
                    row["toDateAmount"] += amountObj.reportAmount
                })
                this.quantityReportData.push(row)
            })
            this.isAmountApprovalVis = true
        },
        async openConfirmDialog() {
            try {
                const data = { "reportId": this.currentRow.reportId, "orderId": this.$props.orderId, "orderShoeId": this.$props.orderShoeId }
                console.log(data)
                await axios.patch(`${this.$apiBaseUrl}/production/productionmanager/approvequantityreport`, data)
                ElMessage({
                    type: 'success',
                    message: '审批成功!'
                });
                this.isAmountApprovalVis = false
                this.getAmountListData()
            }
            catch {
                ElMessage({
                    type: 'warning',
                    message: '软件异常!'
                });
            }
        },
        openRefusalDialog() {
            this.isRefuseApprovalVis = true
        },
        async confirmRefusal() {
            const data = { "reportId": this.currentRow.reportId, "rejectionReason": this.refuseReason }
            await axios.patch(`${this.$apiBaseUrl}/production/productionmanager/rejectquantityreport`, data)
            this.isRefuseApprovalVis = false
            this.isAmountApprovalVis = false
            ElMessage({
                type: 'success',
                message: '驳回成功!'
            });
            this.getAmountListData()
        }
    }
}
</script>
