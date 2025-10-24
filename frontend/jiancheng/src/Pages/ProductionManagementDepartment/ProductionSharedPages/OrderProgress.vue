<template>
    <el-row :gutter="20">
        <el-col>
            <OrderProgressSearchDialog :customerNameOptions="customerNameOptions" :searchForm="searchForm"
            @updateSearchForm="handleSearch" />
        </el-col>
    </el-row>
    <el-row :gutter="20">
        <el-col>
            <el-table :data="orderTableData" stripe border style="height: 65vh">
                <el-table-column v-if="isMultipleSelection" type="selection" width="55" />
                <el-table-column width="80" label="展开" type="expand">
                    <template #default="prop">
                        <el-descriptions :column="4" border>
                            <el-descriptions-item label="裁断开始">{{ prop.row.cuttingStartDate }}</el-descriptions-item>
                            <el-descriptions-item label="裁断结束">{{ prop.row.cuttingEndDate }}</el-descriptions-item>
                            <el-descriptions-item label="预备开始">{{ prop.row.preSewingStartDate }}</el-descriptions-item>
                            <el-descriptions-item label="预备结束">{{ prop.row.preSewingEndDate }}</el-descriptions-item>
                            <el-descriptions-item label="针车开始">{{ prop.row.sewingStartDate }}</el-descriptions-item>
                            <el-descriptions-item label="针车结束">{{ prop.row.sewingEndDate }}</el-descriptions-item>
                            <el-descriptions-item label="成型开始">{{ prop.row.moldingStartDate }}</el-descriptions-item>
                            <el-descriptions-item label="成型结束">{{ prop.row.moldingEndDate }}</el-descriptions-item>
                        </el-descriptions>

                        <el-table :data="prop.row.orderShoeTypeInfo">
                            <el-table-column prop="colorName" label="颜色"></el-table-column>
                            <el-table-column prop="colorAmount" label="颜色数量"></el-table-column>
                            <el-table-column prop="cuttingAmount" label="裁断完成数"></el-table-column>
                            <el-table-column prop="preSewingAmount" label="预备完成数"></el-table-column>
                            <el-table-column prop="sewingAmount" label="针车完成数"></el-table-column>
                            <el-table-column prop="moldingAmount" label="成型完成数"></el-table-column>
                        </el-table>
                    </template>
                </el-table-column>
                <el-table-column prop="customerName" label="客户名"></el-table-column>
                <el-table-column prop="customerBrand" label="商标"></el-table-column>
                <el-table-column prop="orderRId" label="订单号"></el-table-column>
                <el-table-column prop="orderStartDate" label="订单开始"></el-table-column>
                <el-table-column prop="orderEndDate" label="出货日期"></el-table-column>
                <el-table-column prop="shoeRId" label="工厂型号"></el-table-column>
                <el-table-column prop="customerProductName" label="客户鞋型"></el-table-column>
                <el-table-column prop="status" label="生产状态"></el-table-column>
                <el-table-column prop="orderShoeTotal" label="数量"></el-table-column>
                <el-table-column label="车间生产进度" header-align="center">
                    <el-table-column prop="totalCuttingAmount" label="裁断"></el-table-column>
                    <el-table-column prop="totalPreSewingAmount" label="预备"></el-table-column>
                    <el-table-column prop="totalSewingAmount" label="针车"></el-table-column>
                    <el-table-column prop="totalMoldingAmount" label="成型"></el-table-column>
                </el-table-column>
                <el-table-column label="生产信息">
                    <template #default="scope">
                        <el-button type="primary" size="small" @click="openProdDetailDialog(scope.row)">
                            查看
                        </el-button>
                    </template>
                </el-table-column>
            </el-table>
        </el-col>
    </el-row>
    <el-row :gutter="20">
        <el-col>
            <el-pagination @size-change="handleSizeChange" @current-change="handlePageChange"
                :current-page="currentPage" :page-size="pageSize"
                layout="total, sizes, prev, pager, next, jumper" :total="orderTotalRows" />
        </el-col>
    </el-row>
    <el-dialog title="生产信息一览" v-model="isProdDetailDialogOpen" fullscreen @close="onDialogClose">
        <el-tabs v-model="currentProdDetailTab" tab-position="top">
            <el-tab-pane name="1" label="物料">
                <OrderMaterialsPage v-if="showChild" :current-row="currentRow" />
            </el-tab-pane>
            <el-tab-pane name="2" label="工艺单">
                <el-button v-if="currentRow.processSheetUploadStatus == 2" type="warning" size="small"
                    @click="openCraftSheet()">
                    已下发，用量未填写
                </el-button>
                <el-button v-else-if="currentRow.processSheetUploadStatus != 4" type="warning" size="small"
                    @click="openCraftSheet()">
                    未下发
                </el-button>
                <el-button v-else-if="currentRow.processSheetUploadStatus == 4" type="success" size="small"
                    @click="openCraftSheet()">
                    已下发
                </el-button>
            </el-tab-pane>
            <el-tab-pane name="3" label="装箱配码">
                <el-button type="primary" @click="downloadBatchInfo">下载配码</el-button>
            </el-tab-pane>
            <el-tab-pane name="4" label="包装资料">
                <el-button type="primary" size="small" @click="downloadPackagingInfo">
                    下载
                </el-button>
            </el-tab-pane>
            <el-tab-pane name="5" label="工价单">
                <el-tabs v-model="currentPriceReportTab" tab-position="top">
                    <el-tab-pane v-for="item in reportPanes" :key="item.key" :label="item.label" :name="item.key">
                        <el-row v-if="priceReportDict[item.key] === undefined">
                            尚未有工价单
                        </el-row>
                        <el-row v-else>
                            <el-table :data="priceReportDict[item.key]" border stripe max-height="500">
                                <el-table-column prop="rowId" label="序号" />
                                <el-table-column prop="procedure" label="工序"></el-table-column>
                                <el-table-column prop="price" label="单位价格"></el-table-column>
                                <el-table-column prop="note" label="备注"></el-table-column>
                            </el-table>
                        </el-row>
                    </el-tab-pane>
                </el-tabs>
            </el-tab-pane>
        </el-tabs>
    </el-dialog>
</template>
<script>
import AllHeader from '@/components/AllHeader.vue'
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus';
import { shoeBatchInfoTableSpanMethod, getShoeSizesName } from '../utils';
import OrderProgressSearchDialog from './OrderProgressSearchDialog.vue';
import MaterialStorage from '@/Pages/TotalWarehouse/HeadOfWarehouse/components/MaterialStorage.vue';
import OrderMaterialsPage from './OrderMaterialsPage.vue';
export default {
    components: {
        AllHeader,
        OrderProgressSearchDialog,
        MaterialStorage,
        OrderMaterialsPage
    },
    data() {
        return {
            customerNameOptions: [],
            searchForm: {
                orderDateRangeSearch: null,
                orderRIdSearch: null,
                shoeRIdSearch: null,
                customerProductNameSearch: null,
                statusNodeSearch: null,
                customerNameSearch: null,
                customerBrandSearch: null,
                sortCondition: null,
                mode: false
            },
            currentProdDetailTab: "1",
            isProdDetailDialogOpen: false,
            isPriceReportDialogOpen: false,
            currentPriceReportTab: 0,
            reportPanes: [
                {
                    label: '裁断',
                    key: 0
                },
                {
                    label: '针车预备',
                    key: 1
                },
                {
                    label: '针车',
                    key: 2
                },
                {
                    label: '成型',
                    key: 3
                }
            ],
            role: localStorage.getItem('role'),
            getShoeSizesName,
            currentPage: 1,
            pageSize: 10,
            orderTotalRows: 0,
            orderTableData: [],
            currentRow: {},
            shoeBatchInfo: [],
            spanMethod: null,
            isMultipleSelection: false,
            selectedRows: [],
            isMultipleShoesDialogVis: false,
            multipleShoesScheduleForm: {},
            isScheduleDialogOpen: false,
            shoeSizeColumns: [],
            activeTab: "cutting",
            tabs: [],
            // index 0: 裁断，1：预备，2：针车，3：成型
            tabsTemplate: [
                {
                    name: 'cutting',
                    label: '裁断排产',
                    lineLabel: '裁断线号',
                    dateLabel: '裁断工期',
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
                    name: 'preSewing',
                    label: '针车预备排产',
                    lineLabel: '针车预备线号',
                    dateLabel: '预备工期',
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
                    name: 'sewing',
                    label: '针车排产',
                    lineLabel: '针车线号',
                    dateLabel: '针车工期',
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
                    name: 'molding',
                    label: '成型排产',
                    lineLabel: '成型线号',
                    dateLabel: '成型工期',
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
            rules: {
                cuttingLineNumbers: [
                    { required: true, message: '此项为必填项', trigger: 'change' },
                ],
                cuttingDateRange: [
                    { required: true, message: '此项为必填项', trigger: 'change' },
                ],
                preSewingLineNumbers: [
                    { required: true, message: '此项为必填项', trigger: 'change' },
                ],
                preSewingDateRange: [
                    { required: true, message: '此项为必填项', trigger: 'change' },
                ],
                sewingDateRange: [
                    { required: true, message: '此项为必填项', trigger: 'change' },
                ],
                sewingDateRange: [
                    { required: true, message: '此项为必填项', trigger: 'change' },
                ],
                sewingLineNumbers: [
                    { required: true, message: '此项为必填项', trigger: 'change' },
                ],
                moldingLineNumbers: [
                    { required: true, message: '此项为必填项', trigger: 'change' },
                ],
                moldingDateRange: [
                    { required: true, message: '此项为必填项', trigger: 'change' },
                ],
            },
            isSelectedRowsEmpty: false,
            priceReportDict: {},
            isLoading: true,
            showChild: false,
        }
    },
    async mounted() {
        this.getAllCustomers()
        await this.getOrderDataTable()
    },
    methods: {
        async getAllCustomers() {
            const response = await axios.get(`${this.$apiBaseUrl}/customer/getallcustomers`)
            this.customerNameOptions = response.data
        },
        handleSearch(values) {
            this.searchForm = { ...values }
            this.getOrderDataTable()
        },
        openProdDetailDialog(row) {
            this.currentRow = row
            this.showChild = true
            this.isProdDetailDialogOpen = true
        },
        async viewPriceReport(row) {
            try {
                let teams = ["裁断", "针车预备", "针车", "成型"]
                teams.forEach(async (team, index) => {
                    let params = { "orderShoeId": row.orderShoeId, "team": team, "status": 2 }
                    let response = await axios.get(`${this.$apiBaseUrl}/production/getpricereportdetailbyordershoeid`, { params })
                    this.priceReportDict[index] = response.data.detail
                })
                this.currentPriceReportTab = 0
            }
            catch (error) {
                console.log(error)
            }
            this.isPriceReportDialogOpen = true
        },
        async handlePageChange(val) {
            this.currentPage = val
            this.getOrderDataTable()
        },
        async handleSizeChange(val) {
            this.pageSize = val
            this.getOrderDataTable()
        },
        downloadPackagingInfo() {
            window.open(
                `${this.$apiBaseUrl}/orderimport/downloadorderdoc?orderrid=${this.currentRow.orderRId}&filetype=2`
            )
        },
        downloadBatchInfo() {
            window.open(
                `${this.$apiBaseUrl}/production/downloadbatchinfo?orderId=${this.currentRow.orderId}&orderShoeId=${this.currentRow.orderShoeId}&orderRId=${this.currentRow.orderRId}&shoeRId=${this.currentRow.shoeRId}`
            )
        },
        async getOrderDataTable() {
            let startDate = null, endDate = null
            if (this.searchForm.orderDateRangeSearch) {
                startDate = this.searchForm.orderDateRangeSearch[0]
                endDate = this.searchForm.orderDateRangeSearch[1]
            }
            let params = {
                "page": this.currentPage,
                "pageSize": this.pageSize,
                "orderRId": this.searchForm.orderRIdSearch,
                "shoeRId": this.searchForm.shoeRIdSearch,
                "customerProductName": this.searchForm.customerProductNameSearch,
                "statusNode": this.searchForm.statusNodeSearch,
                "customerName": this.searchForm.customerNameSearch,
                "customerBrand": this.searchForm.customerBrandSearch,
                "orderStartDate": startDate,
                "orderEndDate": endDate,
                "sortCondition": this.searchForm.sortCondition,
                "mode": this.searchForm.mode
            }
            let response = await axios.get(`${this.$apiBaseUrl}/production/getallorderproductionprogress`, { params })
            this.orderTableData = response.data.result
            this.orderTotalRows = response.data.totalLength
        },
        openCraftSheet() {
            let url = ''
            url = `${window.location.origin}/processsheet/orderid=${this.currentRow.orderId}`
            window.open(url, '_blank')
        },
        onDialogClose() {
            // wait until dialog animation is done, then destroy child
            this.$nextTick(() => {
                this.showChild = false
            })
        }
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

.is-readonly .el-input__inner {
    cursor: not-allowed;
    background-color: #f5f5f5;
}

.is-readonly .el-input__suffix {
    display: none;
}

.filter-panel {
    margin-bottom: 20px;
}

.filters-container {
    padding: 10px;
}
</style>
