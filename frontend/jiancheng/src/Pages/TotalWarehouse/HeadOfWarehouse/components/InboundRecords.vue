<template>
    <el-row :gutter="20">
        <el-col :span="6">
            <el-date-picker v-model="dateRange" type="daterange" range-separator="至" start-placeholder="开始日期"
                end-placeholder="结束日期" value-format="YYYY-MM-DD" @change="getInboundRecordsTable"
                @clear="getInboundRecordsTable" clearable>
            </el-date-picker>
        </el-col>
        <el-col :span="6" :offset="1">
            <el-input v-model="inboundRIdSearch" placeholder="请输入入库单号" @change="getInboundRecordsTable"
                @clear="getInboundRecordsTable" clearable>
            </el-input>
        </el-col>

    </el-row>
    <el-row :gutter="20">
        <el-col :span="24">
            <el-table :data="tableData" border>
                <el-table-column prop="inboundRId" label="入库单号"></el-table-column>
                <el-table-column prop="supplierName" label="供货单位"></el-table-column>
                <el-table-column label="入库类型">
                    <template #default="scope">
                        {{ determineInboundName(scope.row.inboundType) }}
                    </template>
                </el-table-column>
                <el-table-column prop="timestamp" label="操作时间"></el-table-column>
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

    <el-dialog title="入库单详情" v-model="dialogVisible" width="90%">
        <div id="printView">
            <h2 style="text-align: center;">健诚鞋业入库单</h2>
            <div style="display: flex; justify-content: flex-end; padding: 5px;">
                <span style="font-weight: bolder;font-size: 16px;">
                    单据编号：{{ currentRow.inboundRId }}
                </span>
            </div>
            <table class="table" border="0pm" cellspacing="0" align="left" width="100%"
                style="font-size: 16px;margin-bottom: 10px; table-layout:fixed;word-wrap:break-word;word-break:break-all">
                <tr>
                    <td style="padding:5px; width: 150px;" align="left">供应商:{{ currentRow.supplierName }}</td>
                    <td style="padding:5px; width: 300px;" align="left">入库时间:{{ currentRow.timestamp }}</td>
                    <td style="padding:5px; width: 150px;" align="left">入库方式:{{
                        determineInboundName(currentRow.inboundType)
                        }}</td>
                    <td style="padding:5px; width: 150px;" align="left">结算方式:{{currentRow.payMethod}}</td>
                </tr>
            </table>
            <table class="yk-table" border="1pm" cellspacing="0" align="center" width="100%"
                style="font-size: 16px; table-layout:fixed;word-wrap:break-word;word-break:break-all">
                <tr>
                    <th width="80">材料名</th>
                    <th width="80">型号</th>
                    <th width="200">规格</th>
                    <th width="60">颜色</th>
                    <th width="40">单位</th>
                    <th width="100">订单号</th>
                    <th v-if="currentRow.isSizedMaterial === 1" width="40"
                        v-for="(column, index) in filteredShoeSizeColumns" :key="index">{{ column.label }}</th>
                    <th v-else width="90">数量</th>
                    <th v-if="currentRow.inboundType != 2" width="60">单价</th>
                    <th v-if="currentRow.inboundType == 2" width="60">复合单价</th>
                    <th width="80">总价</th>
                    <th width="100">备注</th>
                </tr>
                <tr v-for="(item, index) in recordData.items" :key="index" align="center">
                    <td>{{ item.materialName }}</td>
                    <td>{{ item.materialModel }}</td>
                    <td>{{ item.materialSpecification }}</td>
                    <td>{{ item.colorName }}</td>
                    <td>{{ item.actualInboundUnit }}</td>
                    <td>{{ item.orderRId }}</td>
                    <td v-if="currentRow.isSizedMaterial === 1" v-for="(column, index) in filteredShoeSizeColumns"
                        :key="index">{{ item[column.prop] }}
                    </td>
                    <td v-else>{{ item.inboundQuantity }}</td>
                    <td v-if="currentRow.inboundType != 2">{{ item.unitPrice }}</td>
                    <td v-if="currentRow.inboundType == 2">{{ item.compositeUnitCost }}</td>
                    <td>{{ calculateTotalPrice(item) }}</td>
                    <td>{{ item.remark }}</td>
                </tr>
            </table>
            <div style="margin-top: 20px; font-size: 16px; font-weight: bold;">
                <div style="display: flex;">
                    <span style="padding-right: 10px;">合计数量: <span style="text-decoration: underline;">{{
                        calculateInboundTotal() }}</span></span>
                    <span style="padding-right: 10px;">合计金额: <span style="text-decoration: underline;">{{
                        calculateTotalPriceSum() }}</span></span>
                    <span style="padding-right: 10px;">备注: <span style="text-decoration: underline;">{{ currentRow.remark }}</span></span>
                </div>
            </div>
        </div>
        <template #footer>
            <el-button type="primary" @click="dialogVisible = false">返回</el-button>
            <el-button type="primary" v-print="'#printView'">打印</el-button>
            <el-button type="primary"
                @click="downloadPDF(`健诚鞋业入库单${currentRow.inboundRId}`, `printView`)">下载PDF</el-button>
        </template>
    </el-dialog>
</template>
<script>
import axios from 'axios'
import { ElMessage } from 'element-plus';
import htmlToPdf from '@/Pages/utils/htmlToPdf';
import print from 'vue3-print-nb'
export default {
    directives: {
        print
    },
    data() {
        return {
            printLoading: true,
            printObj: {
                id: 'printView', // 需要打印的区域id
                preview: true, // 打印预览
                previewTitle: '打印预览',
                popTitle: 'good print',
                extraHead: '<meta http-equiv="Content-Language"content="zh-cn"/>',
                beforeOpenCallback(vue) {
                    console.log('打开之前')
                },
                openCallback(vue) {
                    console.log('执行了打印')
                },
                closeCallback(vue) {
                    console.log('关闭了打印工具')
                }
            },
            currentPage: 1,
            pageSize: 10,
            tableData: [],
            total: 0,
            currentRow: {},
            recordData: {},
            dialogVisible: false,
            dateRange: [null, null],
            inboundRIdSearch: null
        }
    },
    mounted() {
        this.getInboundRecordsTable()
    },
    computed: {
        filteredShoeSizeColumns() {
            return this.recordData.shoeSizeColumns.filter(column =>
                this.recordData.items.some(row => row[column.prop] !== undefined && row[column.prop] !== null && row[column.prop] !== 0)
            )
        }
    },
    methods: {
        calculateInboundTotal() {
            // Calculate the total inbound quantity
            const number = this.recordData.items.reduce((total, item) => {
                return total + (Number(item.inboundQuantity) || 0);
            }, 0);
            return Number(number).toFixed(2);
        },
        calculateTotalPriceSum() {
            // Calculate the total price
            const total = this.recordData.items.reduce((total, item) => {
                return total + (Number(this.calculateTotalPrice(item)) || 0);
            }, 0);
            return Number(total).toFixed(2);
        },
        calculateTotalPrice(row) {
            let result = 0
            if (this.currentRow.inboundType != 2) {
                result = Number(row.inboundQuantity) * Number(row.unitPrice)
            } else {
                result = Number(row.inboundQuantity) * Number(row.compositeUnitCost)
            }
            return result.toFixed(2)
        },
        determineInboundName(type) {
            if (type == 0) {
                return '采购入库'
            } else if (type == 1) {
                return '生产剩余'
            } else if (type == 2) {
                return '复合入库'
            } else {
                return '未知'
            }
        },
        downloadPDF(title, domName) {
            htmlToPdf.getPdf(title, domName);
        },
        async getInboundRecordsTable() {
            if (this.dateRange === null) {
                this.dateRange = [null, null]
            }
            try {
                let params = {
                    page: this.currentPage,
                    pageSize: this.pageSize,
                    startDate: this.dateRange[0],
                    endDate: this.dateRange[1],
                    "inboundRId": this.inboundRIdSearch
                }
                let response = await axios.get(`${this.$apiBaseUrl}/warehouse/getmaterialinboundrecords`, { params })
                this.tableData = response.data.result
                this.total = response.data.total
            }
            catch (error) {
                console.log(error)
            }
        },
        handleSizeChange(val) {
            this.pageSize = val
            this.getInboundRecordsTable()
        },
        handlePageChange(val) {
            this.currentPage = val
            this.getInboundRecordsTable()
        },
        async handleView(row) {
            this.currentRow = row
            try {
                let params = { "inboundBatchId": row.inboundBatchId, "isSizedMaterial": row.isSizedMaterial }
                let response = await axios.get(`${this.$apiBaseUrl}/warehouse/getinboundrecordbybatchid`, { params })
                this.recordData["items"] = response.data
                console.log(this.recordData["items"])
                // if the purchase divide order type is S, then the inbound record is for shoe size
                if (row.isSizedMaterial == 1) {
                    let sizeColumns = []
                    let tempTable = []
                    let firstItem = this.recordData["items"][0]
                    sizeColumns = firstItem.shoeSizeColumns
                    for (let i = 0; i < sizeColumns.length; i++) {
                        let obj = { "label": sizeColumns[i], "prop": `amount${i}` }
                        tempTable.push(obj)
                    }
                    this.recordData["shoeSizeColumns"] = tempTable
                }
                console.log(this.recordData)
                this.dialogVisible = true
            }
            catch (error) {
                console.log(error)
                ElMessage.error('获取入库单详情失败')
            }
        }
    }
}
</script>
<style>
#printView {
    padding-left: 20px; 
    padding-right: 20px;
    color:black; 
    font-family: SimHei;
}
</style>