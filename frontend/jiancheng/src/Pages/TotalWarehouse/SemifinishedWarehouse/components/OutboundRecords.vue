<template>
    <el-row :gutter="20">
        <el-col>
            <el-date-picker v-model="dateRange" type="daterange" range-separator="至" start-placeholder="开始日期"
                end-placeholder="结束日期" value-format="YYYY-MM-DD" @change="getOutboundRecordsTable"
                @clear="getOutboundRecordsTable" clearable>
            </el-date-picker>
            <el-input v-model="outboundRIdSearch" placeholder="出库单号搜索" style="width: 200px;"
                @change="getOutboundRecordsTable" @clear="getOutboundRecordsTable" clearable>
            </el-input>
            <el-input v-model="orderRIdSearch" placeholder="订单号搜索" style="width: 200px;"
                @change="getOutboundRecordsTable" @clear="getOutboundRecordsTable" clearable>
            </el-input>
            <el-input v-model="shoeRIdSearch" placeholder="工厂型号搜索" style="width: 200px;"
                @change="getOutboundRecordsTable" @clear="getOutboundRecordsTable" clearable>
            </el-input>
            <el-input v-model="pickerSearch" placeholder="成型组搜索" style="width: 200px;"
                @change="getOutboundRecordsTable" @clear="getOutboundRecordsTable" clearable>
            </el-input>
        </el-col>
    </el-row>
    <el-row :gutter="20">
        <el-col :span="24">
            <el-table :data="tableData" border stripe height="500" show-summary :summary-method="getSummaries">
                <el-table-column prop="outboundRId" label="出库单号"></el-table-column>
                <el-table-column prop="timestamp" label="操作时间"></el-table-column>
                <el-table-column prop="orderRId" label="订单号"></el-table-column>
                <el-table-column prop="shoeRId" label="工厂型号"></el-table-column>
                <el-table-column prop="colorName" label="颜色"></el-table-column>
                <el-table-column prop="detailAmount" label="入库数量"></el-table-column>
                <el-table-column prop="picker" label="领料工组"></el-table-column>
                <el-table-column prop="remark" label="备注"></el-table-column>
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
        <div id="printView" style="padding-left: 20px; padding-right: 20px;color:black; font-family: SimSun;">
            <h2 style="text-align: center;">健诚鞋业出库单</h2>
            <div style="display: flex; justify-content: flex-end; padding: 5px;">
                <span style="font-weight: bolder;font-size: 16px;">
                    单据编号：{{ currentRow.outboundRId }}
                </span>
            </div>
            <table class="table" border="0pm" cellspacing="0" align="left" width="100%"
                style="font-size: 16px;margin-bottom: 10px; table-layout:fixed;word-wrap:break-word;word-break:break-all">
                <tr>
                    <td style="padding:5px; width: 150px;" align="left">订单号:{{ currentRow.orderRId }}</td>
                    <td style="padding:5px; width: 150px;" align="left">工厂型号:{{ currentRow.shoeRId }}</td>
                    <td style="padding:5px; width: 300px;" align="left">出库时间:{{ currentRow.timestamp }}</td>
                </tr>
            </table>
            <table class="yk-table" border="1pm" cellspacing="0" align="center" width="100%"
                style="font-size: 16px; table-layout:fixed;word-wrap:break-word;word-break:break-all">
                <tr>
                    <th width="55">序号</th>
                    <th width="80">颜色</th>
                    <th v-for="(column, index) in filteredShoeSizeColumns" :key="index">{{ column.label }}</th>
                    <th>总数量</th>
                    <th>备注</th>
                </tr>
                <tr v-for="(item, index) in recordData.items" :key="index" align="center">
                    <td>{{ index + 1 }}</td>
                    <td>{{ item.colorName }}</td>
                    <td v-for="(column, index) in filteredShoeSizeColumns"
                        :key="index">{{ item[column.prop] }}
                    </td>
                    <td>{{ calculateOutboundTotal() }}</td>
                    <td>{{ item.remark }}</td>
                </tr>
            </table>
            <div style="margin-top: 20px; font-size: 16px; font-weight: bold;">
                <div style="display: flex;">
                    <span style="padding-right: 10px;">合计数量: <span style="text-decoration: underline;">{{
                        calculateOutboundTotal() }}</span>
                    </span>
                    <span style="padding-right: 10px;">领料工组: <span style="text-decoration: underline;">{{
                        currentRow.picker }}</span>
                    </span>
                </div>
            </div>
        </div>
        <template #footer>
            <el-button type="primary" @click="dialogVisible = false">返回</el-button>
            <el-button type="primary" v-print="'#printView'">打印</el-button>
            <el-button type="primary"
                @click="downloadPDF(`健诚鞋业出库单${currentRow.outboundRId}`, `printView`)">下载PDF</el-button>
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
            outboundRIdSearch: null,
            orderRIdSearch: null,
            shoeRIdSearch: null,
            pickerSearch: null,
        }
    },
    mounted() {
        this.getOutboundRecordsTable()
    },
    computed: {
        filteredShoeSizeColumns() {
			return this.recordData.shoeSizeColumns.filter(column =>
				this.recordData.items.some(row => row[column.prop] !== undefined && row[column.prop] !== null && row[column.prop] !== 0)
			);
        }
    },
    methods: {
        getSummaries(param) {
            const { columns, data } = param;
            const sums = [];
            columns.forEach((column, index) => {
                if (column.property === 'detailAmount') {
                    const total = data.reduce((sum, row) => {
                        const value = Number(row.detailAmount);
                        return sum + (isNaN(value) ? 0 : value);
                    }, 0);
                    sums[index] = total;
                } else {
                    sums[index] = index === 0 ? '合计' : '';
                }
            });

            return sums;
        },
        calculateOutboundTotal() {
            // Calculate the total outbound quantity
            const number = this.recordData.items.reduce((total, item) => {
                return total + (Number(item.totalAmount) || 0);
            }, 0);
            return Number(number);
        },
        downloadPDF(title, domName) {
            htmlToPdf.getPdf(title, domName);
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
                    orderRId: this.orderRIdSearch,
                    shoeRId: this.shoeRIdSearch,
                    picker: this.pickerSearch
                }
                let response = await axios.get(`${this.$apiBaseUrl}/warehouse/getsemioutboundrecords`, { params })
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
            console.log(row)
            try {
                let params = { "orderId": this.currentRow.orderId, "outboundBatchId": row.outboundBatchId }
                let response = await axios.get(`${this.$apiBaseUrl}/warehouse/getsemioutboundrecordbybatchid`, { params })
                this.recordData = response.data

                console.log(response.data)
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
<style media="print">
@page {
    size: auto;
    margin: 3mm;
}

html {
    background-color: #ffffff;
    margin: 0px;
}

body {
    border: solid 1px #ffffff;
}
</style>

<style lang="scss" scoped>
@media print {
    #printView {
        display: block;
        width: 100%;
        overflow: hidden;
    }
}
</style>