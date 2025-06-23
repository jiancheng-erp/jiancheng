<template>
    <el-container>
        <el-header height="">
            <AllHeader></AllHeader>
        </el-header>
        <el-main height="">
            <el-row :gutter="20" style="text-align: center">
                <el-col :span="24" :offset="0" style="font-size: xx-large; text-align: center">订单鞋型工价审批页面</el-col>
            </el-row>
            <el-row :gutter="20">
                <el-col :span="24" :offset="0">
                    <el-descriptions title="订单信息" border>
                        <el-descriptions-item label="订单号">{{ orderInfo.orderRId }}</el-descriptions-item>
                        <el-descriptions-item label="鞋型号">{{ orderInfo.shoeRId }}</el-descriptions-item>
                        <el-descriptions-item label="客户名称">{{ orderInfo.customerName }}</el-descriptions-item>
                        <el-descriptions-item label="客户鞋型">{{ orderInfo.customerProductName }}</el-descriptions-item>
                        <el-descriptions-item label="开始日期">{{ orderInfo.orderStartDate }}</el-descriptions-item>
                        <el-descriptions-item label="截止日期">{{ orderInfo.orderEndDate }}</el-descriptions-item>
                    </el-descriptions>
                </el-col>
            </el-row>
            <el-row :gutter="20" style="margin-top: 20px">
                <el-col :span="24" :offset="0">
                    订单鞋双数量
                    <el-table :data="shoeInfo" border stripe :max-height="500">
                        <el-table-column prop="colorName" label="颜色"></el-table-column>
                        <el-table-column prop="totalAmount" label="颜色总数"></el-table-column>
                    </el-table>
                </el-col>
            </el-row>
            <el-row :gutter="20">
                <el-col :span="24" :offset="0">
                    鞋型工价表
                    <el-table :data="priceReports" border stripe>
                        <el-table-column prop="team" label="车间"></el-table-column>
                        <el-table-column prop="productionStartDate" label="生产开始日期"></el-table-column>
                        <el-table-column prop="productionEndDate" label="生产结束日期"></el-table-column>
                        <el-table-column prop="reportStatus" label="状态"></el-table-column>
                        <el-table-column label="操作">
                            <template #default="scope">
                                <el-button type="primary" @click="getReportDetail(scope.row)">
                                    <span v-if="scope.row.reportStatus === '未审核'">
                                        审核
                                    </span>
                                    <span v-else>
                                        查看
                                    </span>
                                </el-button>
                            </template>
                        </el-table-column>
                    </el-table>
                </el-col>
            </el-row>
        </el-main>
    </el-container>
    <el-dialog title="工价审核界面" v-model="isWagesApprovalVis" width="80%">
        <el-table :data="reportDetail" border stripe max-height="500" :summary-method="summaryMethod" show-summary>
            <el-table-column prop="rowId" label="序号"></el-table-column>
            <el-table-column v-if="currentRow.team === '成型'" prop="productionSection" label="工段"></el-table-column>
            <el-table-column prop="procedure" label="工序名称"></el-table-column>
            <el-table-column v-if="currentRow.team !== '成型'" prop="price" label="工价"></el-table-column>
            <el-table-column prop="note" label="备注"></el-table-column>
        </el-table>
        <template #footer>
            <span>
                <el-button @click="isWagesApprovalVis = false">关闭</el-button>
                <el-button
                    v-if="(role == 3 && currentRow.reportStatus === '生产副总审核中') || (role == 2 && currentRow.reportStatus === '总经理审核中')"
                    type="danger" @click="openRefusalDialog">驳回请求</el-button>
                <el-button
                    v-if="(role == 3 && currentRow.reportStatus === '生产副总审核中') || (role == 2 && currentRow.reportStatus === '总经理审核中')"
                    type="primary" @click="approveReport">审批通过</el-button>
            </span>
        </template>
    </el-dialog>
    <el-dialog title="驳回审批请求" v-model="isRefuseApprovalVis" width="30%">
        <el-row :gutter="20">
            <el-col :span="24" :offset="0">
                请填写驳回原因（不超过20字）：
                <el-input v-model="rejectionReason" type="textarea" placeholder="" resize="none" clearable
                    @change=""></el-input>
            </el-col>
        </el-row>
        <template #footer>
            <span>
                <el-button @click="isRefuseApprovalVis = false">取消</el-button>
                <el-button type="success" @click="rejectReport">确认</el-button>
            </span>
        </template>
    </el-dialog>
</template>
<script>
import axios from 'axios'
import AllHeader from '@/components/AllHeader.vue'
import { ElMessage, ElMessageBox } from 'element-plus'
export default {
    components: {
        AllHeader
    },
    props: ["orderShoeId", "orderId"],
    data() {
        return {
            role: localStorage.getItem('role'),
            rejectionReason: '',
            isRefuseApprovalVis: false,
            reportDetail: [],
            shoeInfo: [],
            priceReports: [],
            isWagesApprovalVis: false,
            currentRow: {},
            orderInfo: [],
        }
    },
    async mounted() {
        this.getOrderInfo()
        this.getOrderShoeBatchInfo()
        this.getPriceReportInfo()
    },
    methods: {
        summaryMethod(param) {
            const { columns, data } = param;
            const sums = [];
            columns.forEach((column, index) => {
                if (column.property === 'price') {
                    const total = data.reduce((sum, row) => {
                        const value = Number(row.price);
                        return sum + (isNaN(value) ? 0 : value);
                    }, 0);
                    sums[index] = total;
                } else {
                    sums[index] = index === 0 ? '合计' : '';
                }
            });

            return sums;
        },
        async getOrderInfo() {
            let params = { "orderId": this.$props.orderId, "orderShoeId": this.$props.orderShoeId }
            let response = await axios.get(`${this.$apiBaseUrl}/production/productionmanager/getorderinfo`, { params })
            this.orderInfo = response.data
        },
        async getOrderShoeBatchInfo() {
            try {
                const params = { "orderShoeId": this.$props.orderShoeId }
                const response = await axios.get(`${this.$apiBaseUrl}/production/getordershoebatchinfo`, { params })
                this.shoeInfo = response.data
            }
            catch (error) {
                console.log(error)
            }
        },
        async getPriceReportInfo() {
            const params = { "orderShoeId": this.$props.orderShoeId }
            const response = await axios.get(`${this.$apiBaseUrl}/production/productionmanager/getallpricereportsforordershoe`, { params })
            this.priceReports = response.data
        },
        async getReportDetail(rowData) {
            this.currentRow = rowData
            const params = { "reportId": rowData.reportId }
            const response = await axios.get(`${this.$apiBaseUrl}/production/getpricereportdetail`, { params })
            this.reportDetail = response.data
            this.isWagesApprovalVis = true
        },
        async approveReport() {
            ElMessageBox.confirm(
                '此操作无法撤回，是否通过？',
                '提示',
            ).then(async () => {
                const data = { "orderId": this.$props.orderId, "orderShoeId": this.$props.orderShoeId, "reportId": this.currentRow.reportId }
                try {
                    if (this.role == 2) {
                        await axios.patch(`${this.$apiBaseUrl}/headmanager/approvepricereportbyheadmanager`, data)
                    }
                    else if (this.role == 3) {
                        await axios.patch(`${this.$apiBaseUrl}/production/productionmanager/approvepricereport`, data)
                    }
                    ElMessage.success('审批成功')
                }
                catch (error) {
                    console.log(error)
                    ElMessage.error('驳回失败')
                }
                this.isWagesApprovalVis = false
                this.getPriceReportInfo()
            }).catch(() => {
                ElMessage.info('撤销操作')
            })
        },
        openRefusalDialog() {
            this.isRefuseApprovalVis = true
        },
        async rejectReport() {
            ElMessageBox.confirm(
                '此操作无法撤回，是否驳回？',
                '提示',
            ).then(async () => {
                let reportIdArr = []
                if (this.currentRow.team === '针车预备' || this.currentRow.team === '针车') {
                    this.priceReports.forEach(row => {
                        if (row.team === '针车预备' || row.team === '针车') {
                            reportIdArr.push(row.reportId)
                        }
                    })
                }
                else {
                    reportIdArr = [this.currentRow.reportId]
                }
                const data = { "orderId": this.$props.orderId, "orderShoeId": this.$props.orderShoeId, "reportIdArr": reportIdArr, "rejectionReason": this.rejectionReason }
                try {
                    if (this.role == 2) {
                        await axios.patch(`${this.$apiBaseUrl}/headmanager/rejectpricereportbyheadmanager`, data)
                    }
                    else if (this.role == 3) {
                        await axios.patch(`${this.$apiBaseUrl}/production/productionmanager/rejectpricereport`, data)
                    }
                    ElMessage.success('驳回成功')
                }
                catch (error) {
                    console.log(error)
                    ElMessage.error('驳回失败')
                }
                this.isRefuseApprovalVis = false
                this.isWagesApprovalVis = false
                this.getPriceReportInfo()
            }).catch(() => {
                ElMessage.info('撤销操作')
            })
        },
    }
}
</script>
