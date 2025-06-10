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
        </el-col>
    </el-row>
    <el-row :gutter="20">
        <el-col :span="24">
            <el-table :data="tableData" border stripe height="500" show-summary :summary-method="getSummaries">
                <el-table-column prop="outboundRId" label="出库单号"></el-table-column>
                <el-table-column prop="timestamp" label="操作时间"></el-table-column>
                <el-table-column prop="orderRId" label="订单号"></el-table-column>
                <el-table-column prop="shoeRId" label="工厂鞋型"></el-table-column>
                <el-table-column prop="colorName" label="颜色"></el-table-column>
                <el-table-column prop="customerName" label="客户名称"></el-table-column>
                <el-table-column prop="orderCId" label="客户订单号"></el-table-column>
                <el-table-column prop="detailAmount" label="数量"></el-table-column>
            </el-table>
        </el-col>
    </el-row>
    <el-row :gutter="20">
        <el-col>
            <el-pagination @size-change="handleSizeChange" @current-change="handlePageChange"
                :current-page="currentPage" :page-sizes="pageSizes" :page-size="pageSize"
                layout="total, sizes, prev, pager, next, jumper" :total="total" />
        </el-col>
    </el-row>

    <el-dialog title="出库单详情" v-model="dialogVisible" width="80%">
        <el-descriptions>
            <template #title>
                <h2 style="text-align: center;">健诚鞋业出库单</h2>
            </template>
            <template #extra>
                <span style="font-weight: bolder;font-size: 16px;">
                    单据编号：{{ currentRow.outboundRId }}
                </span>
            </template>
            <el-descriptions-item label="订单号">{{ currentRow.orderRId }}</el-descriptions-item>
            <el-descriptions-item label="工厂型号">{{ currentRow.shoeRId }}</el-descriptions-item>
            <el-descriptions-item label="出库时间">{{ currentRow.timestamp }}</el-descriptions-item>
        </el-descriptions>
        <template #footer>
            <el-button type="primary" @click="dialogVisible = false">返回</el-button>
            <!-- <el-button type="primary" v-print="'#printView'">打印</el-button>
            <el-button type="primary"
                @click="downloadPDF(`健诚鞋业出库单${currentRow.outboundRId}`, `printView`)">下载PDF</el-button> -->
        </template>
    </el-dialog>
</template>
<script>
import axios from 'axios'
import { ElMessage } from 'element-plus';
import htmlToPdf from '@/Pages/utils/htmlToPdf';
import print from 'vue3-print-nb'
import { PAGESIZE, PAGESIZES, getSummaries } from '../../warehouseUtils';
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
            pageSize: PAGESIZE,
            pageSizes: PAGESIZES,
            tableData: [],
            total: 0,
            currentRow: {},
            recordData: {},
            dialogVisible: false,
            dateRange: [null, null],
            outboundRIdSearch: null,
            orderRIdSearch: null,
            shoeRIdSearch: null,
            getSummaries: getSummaries,
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
                    shoeRId: this.shoeRIdSearch
                }
                let response = await axios.get(`${this.$apiBaseUrl}/warehouse/getfinishedoutboundrecords`, { params })
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
                let response = await axios.get(`${this.$apiBaseUrl}/warehouse/getfinishedoutboundrecordbybatchid`, { params })
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