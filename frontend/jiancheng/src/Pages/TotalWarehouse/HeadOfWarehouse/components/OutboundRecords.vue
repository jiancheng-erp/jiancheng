<template>
    <el-row :gutter="20">
        <el-col>
            <el-date-picker v-model="dateRange" type="daterange" range-separator="至" start-placeholder="开始日期"
                end-placeholder="结束日期" value-format="YYYY-MM-DD" @change="getOutboundRecordsTable"
                @clear="getOutboundRecordsTable" clearable style="width: 300px;">
            </el-date-picker>
            <el-input v-model="outboundRIdSearch" placeholder="请输入出库单号" @change="getOutboundRecordsTable"
                @clear="getOutboundRecordsTable" clearable style="width: 200px; margin-left: 20px;">
            </el-input>
            <!-- <el-select v-model="warehouseNameSearch" @change="getOutboundRecordsTable" placeholder="仓库名称搜索"
                @clear="getOutboundRecordsTable" filterable clearable style="width: 200px; margin-left: 20px;">
                <el-option v-for="(item, index) in warehouseOptions" :key="index" :label="item.label"
                    :value="item.value"></el-option>
            </el-select> -->
            <el-input v-model="destinationSearch" placeholder="出库目的地搜索" @change="getOutboundRecordsTable"
                @clear="getOutboundRecordsTable" clearable style="width: 200px; margin-left: 20px;">
            </el-input>
            <el-select v-model="outboundTypeSearch" placeholder="出库类型搜索" @change="getOutboundRecordsTable"
                @clear="getOutboundRecordsTable" clearable style="width: 200px; margin-left: 20px;">
                <el-option label="生产出库" :value="0"></el-option>
                <el-option label="废料处理" :value="1"></el-option>
                <el-option label="外包出库" :value="2"></el-option>
                <el-option label="复合出库" :value="3"></el-option>
                <el-option label="材料退回" :value="4"></el-option>
                <el-option label="盘库出库" :value="5"></el-option>
            </el-select>
            <el-select v-if="loadReject == false" v-model="statusSearch" @change="getOutboundRecordsTable"
                @clear="getOutboundRecordsTable" clearable style="width: 200px; margin-left: 20px;">
                <el-option label="全部" :value="-1"></el-option>
                <el-option label="待审核" :value="0"></el-option>
                <el-option label="已批准" :value="1"></el-option>
                <el-option label="已驳回" :value="2"></el-option>
            </el-select>
        </el-col>
    </el-row>
    <el-row :gutter="20">
        <el-col :span="24">
            <el-table :data="tableData" border stripe height="600">
                <el-table-column v-if="loadReject" width="55">
                    <template #default="scope">
                        <el-radio v-model="selectedRow" :label="scope.row.outboundRecordId"
                            @change="() => handleRowClick(scope.row.outboundRecordId)">
                        </el-radio>
                    </template>
                </el-table-column>
                <el-table-column prop="outboundRId" label="出库单号"></el-table-column>
                <el-table-column prop="timestamp" label="操作时间"></el-table-column>
                <el-table-column prop="destination" label="出库至">
                </el-table-column>
                <el-table-column prop="outboundType" label="出库类型">
                </el-table-column>
                <el-table-column prop="picker" label="领料人"></el-table-column>
                <el-table-column prop="remark" label="备注"></el-table-column>
                <el-table-column prop="rejectReason" label="驳回原因"></el-table-column>
                <el-table-column label="查看">
                    <template #default="scope">
                        <el-button-group>
                            <el-button type="primary" @click="handleView(scope.row)">查看</el-button>
                            <el-button v-if="role == 24 && scope.row.approvalStatus === 0" type="success"
                                @click="handleApproval(scope.row)">批准</el-button>
                            <el-button v-if="role == 24 && scope.row.approvalStatus === 0" type="warning"
                                @click="openRejectDialog(scope.row)">驳回</el-button>
                        </el-button-group>
                    </template>
                </el-table-column>
            </el-table>
        </el-col>
    </el-row>
    <el-row :gutter="20">
        <el-col>
            <el-pagination @size-change="handleSizeChange" @current-change="handlePageChange"
                :current-page="currentPage" :page-sizes="[10, 20, 30, 40]" :page-size="pageSize"
                layout="total, sizes, prev, pager, next, jumper" :total="total" />
        </el-col>
    </el-row>

    <el-dialog title="出库单详情" v-model="dialogVisible" width="80%">
        <div id="printView" v-show="true">
            <table style="width:100%; border-collapse: collapse;">
                <!-- Header repeated on each page -->
                <thead>
                    <tr>
                        <td>
                            <div style="position: relative; padding: 5px;">
                                <h1 style="margin: 0; text-align: center;">健诚鞋业出库单</h1>
                                <span
                                    style="position: absolute; right: 0; top: 50%; transform: translateY(-50%); font-weight: bolder; font-size: 16px;">
                                    单据编号: {{ currentRow.outboundRId }}
                                </span>
                            </div>
                            <table class="table" border="0" cellspacing="0" align="left" width="100%"
                                style="font-size: 16px; margin-bottom: 10px; table-layout: fixed; word-wrap: break-word; word-break: break-all;">
                                <tr>
                                    <td style="padding:5px; width: 150px;" align="left">出库至: {{
                                        currentRow.destination }}</td>
                                    <td style="padding:5px; width: 300px;" align="left">出库时间: {{
                                        currentRow.timestamp }}
                                    </td>
                                    <td style="padding:5px; width: 150px;" align="left">出库类型: {{
                                        currentRow.outboundType }}
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                </thead>

                <!-- Main body content -->
                <tbody>
                    <tr>
                        <td>
                            <table class="yk-table" border="1" cellspacing="0" align="center" width="100%"
                                style="max-height:360px; table-layout: fixed; word-wrap: break-word; word-break: break-all;">
                                <thead>
                                    <tr>
                                        <th width="100">材料名</th>
                                        <th width="100">型号</th>
                                        <th width="180">规格</th>
                                        <th width="80">颜色</th>
                                        <th width="55">单位</th>
                                        <th width="100">订单号</th>
                                        <th width="100">工厂鞋型</th>
                                        <th width="100">数量</th>
                                        <th width="100">单价</th>
                                        <th width="100">金额</th>
                                        <th>备注</th>
                                    </tr>
                                </thead>

                                <tr v-for="(item, index) in recordData" :key="index" align="center">
                                    <td>{{ item.materialName }}</td>
                                    <td>{{ item.materialModel }}</td>
                                    <td>{{ item.materialSpecification }}</td>
                                    <td>{{ item.materialColor }}</td>
                                    <td>{{ item.actualInboundUnit }}</td>
                                    <td>{{ item.orderRId }}</td>
                                    <td>{{ item.shoeRId }}</td>
                                    <td>{{ item.outboundQuantity }}</td>
                                    <td>{{ item.unitPrice }}</td>
                                    <td>{{ item.itemTotalPrice }}</td>
                                    <td>{{ item.remark }}</td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                </tbody>

                <!-- Footer repeated on each page -->
                <tfoot>
                    <tr>
                        <td>
                            <div style="margin-top: 20px; font-size: 16px; font-weight: bold;display: flex;">
                                <span style="padding-right: 10px;">合计数量: <span style="text-decoration: underline;">{{
                                    calculateOutboundTotal() }}</span></span>
                                <span style="padding-right: 10px;">合计金额: <span style="text-decoration: underline;">{{
                                    currentRow.totalPrice }}</span></span>
                                <span style="padding-right: 10px; width: 150px;">领料人: <span style="text-decoration: underline;">{{
                                    currentRow.picker }}</span></span>
                                <span style="padding-right: 10px;">备注: <span style="text-decoration: underline;">{{
                                    currentRow.remark }}</span></span>
                            </div>
                        </td>
                    </tr>
                </tfoot>
            </table>
        </div>
        <template #footer>
            <el-button type="primary" @click="dialogVisible = false">返回</el-button>
            <el-button type="primary" v-print="'#printView'">打印</el-button>
        </template>
    </el-dialog>
    <el-dialog title="驳回确认" v-model="rejectDialogVisible" width="40%">
        <!-- Textarea with character limit -->
        <el-input type="textarea" v-model="rejectText" :maxlength="255" show-word-limit>
        </el-input>
        <template #footer>
            <el-button @click="rejectDialogVisible = false">返回</el-button>
            <el-button type="primary" @click="handleReject()">驳回</el-button>
        </template>
    </el-dialog>
</template>
<script>
import axios from 'axios'
import { ElMessage } from 'element-plus';
import print from 'vue3-print-nb'
export default {
    directives: {
        print
    },
    props: {
        materialSupplierOptions: {
            type: Array,
            required: true
        },
        warehouseOptions: {
            type: Array,
            required: true
        },
        loadReject: {
            type: Boolean,
            default: false
        }
    },
    data() {
        return {
            role: localStorage.getItem('role'),
            currentPage: 1,
            pageSize: 10,
            tableData: [],
            total: 0,
            currentRow: {},
            recordData: [],
            dialogVisible: false,
            dateRange: [null, null],
            outboundRIdSearch: null,
            destinationSearch: null,
            outboundTypeSearch: null,
            statusSearch: this.loadReject ? 2 : 0,
            rejectDialogVisible: false,
            rejectText: '',
            selectedRow: null,
        }
    },
    emits: ['update-selected-row'],
    mounted() {
        this.getOutboundRecordsTable()
    },
    methods: {
        calculateOutboundTotal() {
            // Calculate the total inbound quantity
            console.log(this.recordData)
            const number = this.recordData.reduce((total, item) => {
                return total + (Number(item.outboundQuantity) || 0);
            }, 0);
            return Number(number).toFixed(2);
        },
        handleRowClick(row) {
            this.selectedRow = row
            this.$emit('update-selected-row', row)
        },
        async getOutboundRecordsTable() {
            if (this.dateRange === null) {
                this.dateRange = [null, null]
            }
            try {
                let params = {
                    page: this.currentPage,
                    pageSize: this.pageSize,
                    startDate: this.dateRange[0],
                    endDate: this.dateRange[1],
                    outboundRId: this.outboundRIdSearch,
                    destination: this.destinationSearch,
                    outboundType: this.outboundTypeSearch,
                    status: this.statusSearch
                }
                let response = await axios.get(`${this.$apiBaseUrl}/warehouse/getmaterialoutboundrecords`, { params })
                this.tableData = response.data.result
                this.total = response.data.total
            }
            catch (error) {
                console.log(error)
            }
        },
        handleSizeChange(val) {
            this.pageSize = val
            this.getOutboundRecordsTable()
        },
        handlePageChange(val) {
            this.currentPage = val
            this.getOutboundRecordsTable()
        },
        async handleView(row) {
            this.currentRow = row
            try {
                let params = { "outboundRecordId": row.outboundRecordId }
                let response = await axios.get(`${this.$apiBaseUrl}/warehouse/getoutboundrecordbyrecordid`, { params })
                this.recordData = response.data
                for (let i = 0; i < this.recordData.length; i++) {
                    let tempColumns = this.recordData[i].shoeSizeColumns
                    this.recordData[i]["displayShoeSizes"] = []
                    for (let j = 0; j < tempColumns.length; j++) {
                        let obj = {
                            "outboundAmount": this.recordData[i][`amount${j}`],
                            "shoeSizeColumns": tempColumns[j]
                        }
                        this.recordData[i]["displayShoeSizes"].push(obj)
                    }
                }
                this.dialogVisible = true
            }
            catch (error) {
                console.log(error)
                ElMessage.error('获取出库单详情失败')
            }
        },
        async handleApproval(row) {
            this.$confirm('是否批准该出库单？', '提示', {
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                type: 'warning'
            }).then(async () => {
                try {
                    let params = { "outboundRecordId": row.outboundRecordId }
                    await axios.patch(`${this.$apiBaseUrl}/accounting/approveoutboundrecord`, params)
                    ElMessage.success('批准成功')
                    this.getOutboundRecordsTable()
                } catch (error) {
                    if (error.response) {
                        // Flask returns error in JSON format
                        this.errorMessage = error.response.data.message || "An error occurred";
                    } else {
                        this.errorMessage = "服务器异常";
                    }
                    ElMessage.error(this.errorMessage)
                    console.error("API Error:", error);
                }
            }).catch(() => {
                ElMessage.info('已取消批准')
            })
        },
        openRejectDialog(row) {
            this.currentRow = row
            this.rejectDialogVisible = true
        },
        handleReject() {
            this.$confirm('是否驳回该出库单？', '提示', {
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                type: 'warning'
            }).then(async () => {
                try {
                    let params = { "outboundRecordId": this.currentRow.outboundRecordId, "rejectReason": this.rejectText }
                    await axios.patch(`${this.$apiBaseUrl}/accounting/rejectoutboundrecord`, params)
                    ElMessage.success('驳回成功')
                    this.rejectDialogVisible = false
                    this.rejectText = ''
                    this.getOutboundRecordsTable()
                } catch (error) {
                    if (error.response) {
                        // Flask returns error in JSON format
                        this.errorMessage = error.response.data.message || "An error occurred";
                    } else {
                        this.errorMessage = "服务器异常";
                    }
                    ElMessage.error(this.errorMessage)
                    console.error("API Error:", error);
                }
            }).catch(() => {
                ElMessage.info('已取消驳回')
            })
        },
    }
}
</script>