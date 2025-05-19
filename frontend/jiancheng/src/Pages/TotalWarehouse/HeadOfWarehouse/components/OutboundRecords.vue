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
        </el-col>
    </el-row>
    <el-row :gutter="20">
        <el-col :span="24">
            <el-table :data="tableData" border stripe>
                <el-table-column prop="outboundRId" label="出库单号"></el-table-column>
                <el-table-column prop="timestamp" label="操作时间"></el-table-column>
                <el-table-column prop="outboundType" label="出库类型">
                </el-table-column>
                <el-table-column prop="destination" label="出库至">
                </el-table-column>
                <el-table-column label="查看">
                    <template #default="scope">
                        <el-button type="primary" @click="handleView(scope.row)">查看</el-button>
                    </template>
                </el-table-column>
            </el-table>
        </el-col>
    </el-row>
    <el-row :gutter="20">
        <el-col :span="12" :offset="14">
            <el-pagination @size-change="handleSizeChange" @current-change="handlePageChange"
                :current-page="currentPage" :page-sizes="[10, 20, 30, 40]" :page-size="pageSize"
                layout="total, sizes, prev, pager, next, jumper" :total="total" />
        </el-col>
    </el-row>

    <el-dialog title="出库单详情" v-model="dialogVisible" width="80%">
        <!-- <el-descriptions border>
            <template #extra>
                <span style="font-weight: bolder;font-size: 16px;">
                    单据编号：{{ currentRow.outboundRId }}
                </span>
            </template>
            <el-descriptions-item label="出库类型">{{ currentRow.outboundType
            }}</el-descriptions-item>
            <el-descriptions-item label="出库至">{{
                }}</el-descriptions-item>
            <el-descriptions-item label="出库时间">{{ currentRow.timestamp }}</el-descriptions-item>
        </el-descriptions>
        <el-table :data="recordData" border stripe>
            <el-table-column type="expand">
                <template #default="props">
                    <el-table :data="props.row['displayShoeSizes']" border stripe style="width: 100%">
                        <el-table-column label="鞋码" prop="shoeSizeColumns"></el-table-column>
                        <el-table-column label="数量" prop="outboundAmount"></el-table-column>
                    </el-table>
                </template>

            </el-table-column>
            <el-table-column prop="orderRId" label="订单号"></el-table-column>
            <el-table-column prop="shoeRId" label="工厂鞋型"></el-table-column>
            <el-table-column prop="materialName" label="名称"></el-table-column>
            <el-table-column prop="materialModel" label="型号"></el-table-column>
            <el-table-column prop="materialSpecification" label="规格"></el-table-column>
            <el-table-column prop="colorName" label="颜色"></el-table-column>
            <el-table-column prop="actualInboundUnit" label="单位"></el-table-column>
            <el-table-column prop="unitPrice" label="平均价"></el-table-column>
            <el-table-column prop="outboundQuantity" label="数量"></el-table-column>
            <el-table-column prop="itemTotalPrice" label="金额"></el-table-column>
        </el-table> -->
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
                                    <td style="padding:5px; width: 150px;" align="left">领料人: {{
                                        currentRow.picker }}
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
                            <div style="margin-top: 20px; font-size: 16px; font-weight: bold; display: flex;">
                                <span style="padding-right: 10px;">合计金额: <span style="text-decoration: underline;">{{
                                    currentRow.totalPrice
                                        }}</span></span>
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
</template>
<script>
import axios from 'axios'
import { ElMessage } from 'element-plus';
export default {
    data() {
        return {
            currentPage: 1,
            pageSize: 10,
            tableData: [],
            total: 0,
            currentRow: {},
            recordData: [],
            dialogVisible: false,
            dateRange: [null, null],
            outboundRIdSearch: null,
        }
    },
    mounted() {
        this.getOutboundRecordsTable()
    },
    methods: {
        async getOutboundRecordsTable() {
            console.log(this.dateRange)
            if (this.dateRange === null) {
                this.dateRange = [null, null]
            }
            try {
                let params = {
                    page: this.currentPage,
                    pageSize: this.pageSize,
                    startDate: this.dateRange[0],
                    endDate: this.dateRange[1],
                    outboundRId: this.outboundRIdSearch
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
        }
    }
}
</script>