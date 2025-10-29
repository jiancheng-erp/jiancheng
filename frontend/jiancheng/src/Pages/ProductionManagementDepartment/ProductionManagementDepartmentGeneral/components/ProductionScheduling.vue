<template>
    <el-row :gutter="20" style="margin-top: 20px">
        <el-col>
            <OrderSchedulingSearchDialog :searchForm="searchForm"  @updateSearchForm="handleSearch" />
        </el-col>
    </el-row>
    <el-row>
        <el-col>
            <el-button type="primary" v-if="role == 6 && isMultipleSelection" @click="openMultipleShoesDialog">
                排期
            </el-button>
            <el-button type="primary" v-if="role == 6" @click="toggleSelectionMode">
                {{ isMultipleSelection ? "退出" : "多选鞋型排期" }}
            </el-button>
            <p v-if="isSelectedRowsEmpty">未选择鞋型</p>
        </el-col>
    </el-row>
    <el-row :gutter="20">
        <el-col :span="24" :offset="0">
            <el-table :data="orderTableData" stripe border style="height: 75vh"
                @selection-change="handleSelectionChange">
                <el-table-column type="selection" width="55"></el-table-column>
                <el-table-column prop="orderRid" label="订单号"></el-table-column>
                <el-table-column prop="shoeRid" label="工厂型号"></el-table-column>
                <el-table-column prop="startDate" label="订单开始"></el-table-column>
                <el-table-column prop="cuttingStartDate" label="裁断开始"></el-table-column>
                <el-table-column prop="cuttingEndDate" label="裁断结束"></el-table-column>
                <el-table-column prop="preSewingStartDate" label="预备开始"></el-table-column>
                <el-table-column prop="preSewingEndDate" label="预备结束"></el-table-column>
                <el-table-column prop="sewingStartDate" label="针车开始"></el-table-column>
                <el-table-column prop="sewingEndDate" label="针车结束"></el-table-column>
                <el-table-column prop="moldingStartDate" label="成型开始"></el-table-column>
                <el-table-column prop="moldingEndDate" label="成型结束"></el-table-column>
                <el-table-column prop="schedulingStatus" label="排期状态"></el-table-column>
                <el-table-column label="排期">
                    <template #default="scope">
                        <el-button type="primary" size="small" @click="openScheduleDialog(scope.row)">
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

    <el-dialog title="多鞋型排期页面" v-model="isMultipleShoesDialogVis" width="50%">
        <el-form :model="multipleShoesScheduleForm" :rules="rules" ref="multipleShoesScheduleForm" class="custom-form">
            <el-form-item label="裁断生产周期" prop="cuttingDateRange">
                <el-date-picker v-model="multipleShoesScheduleForm.cuttingDateRange" type="daterange" size="default"
                    range-separator="至" value-format="YYYY-MM-DD">
                </el-date-picker>
            </el-form-item>
            <el-form-item label="针车预备生产周期" prop="preSewingDateRange">
                <el-date-picker v-model="multipleShoesScheduleForm.preSewingDateRange" type="daterange" size="default"
                    range-separator="至" value-format="YYYY-MM-DD">
                </el-date-picker>
            </el-form-item>
            <el-form-item label="针车生产周期" prop="sewingDateRange">
                <el-date-picker v-model="multipleShoesScheduleForm.sewingDateRange" type="daterange" size="default"
                    range-separator="至" value-format="YYYY-MM-DD">
                </el-date-picker>
            </el-form-item>
            <el-form-item label="成型生产周期" prop="moldingDateRange">
                <el-date-picker v-model="multipleShoesScheduleForm.moldingDateRange" type="daterange" size="default"
                    range-separator="至" value-format="YYYY-MM-DD">
                </el-date-picker>
            </el-form-item>
        </el-form>
        <template #footer>
            <span>
                <el-button type="primary" @click="isMultipleShoesDialogVis = false">返回</el-button>
                <el-button type="primary" @click="saveMultipleSchedules">保存</el-button>
            </span>
        </template>
    </el-dialog>

    <el-dialog :title="`订单${currentRow.orderRId}-鞋型${currentRow.shoeRId}排期信息`" v-model="isScheduleDialogOpen"
        fullscreen>
        <el-tabs v-model="activeTab" tab-position="top" @tab-click="">
            <el-tab-pane v-for="tab in tabs" :key="tab.name" :label="tab.label" :name="tab.name"
                :disabled="disableTab(tab.name)">
                <el-row :gutter="20">
                    <el-col :span="4" v-for="subTab in tabs">
                        {{ `${subTab.dateLabel}: ${subTab.dateValue[0] ? subTab.dateValue[0] + '至' + subTab.dateValue[1]
                            :
                            '未设置'}` }}
                    </el-col>

                </el-row>
                <el-row :gutter="20">
                    <el-col :span="10" :offset="0">
                        <span>
                            {{ tab.dateLabel }}：
                            <el-date-picker v-model="tab.dateValue" type="daterange" size="default" range-separator="-"
                                value-format="YYYY-MM-DD" :readonly="!(role == 6)">
                            </el-date-picker>
                        </span>
                        <el-button type="primary" size="default" @click="checkDateProductionStatus(tab)">{{
                            tab.isDateStatusTableVis ? '关闭表格' : '查看工期内排期情况' }}</el-button>
                    </el-col>
                    <el-col :span="8" :offset="6">
                        <el-descriptions title="" border v-if="role == 6">
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
                    <el-col>
                        <el-table v-if="tab.isDateStatusTableVis" :data="tab.dateStatusTable" border stripe
                            height="400px">
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
                            <el-table-column prop="orderShoeCount" label="已排期鞋型数"> </el-table-column>
                            <el-table-column prop="predictAmount" label="预计当日现有生产量"> </el-table-column>
                        </el-table>
                    </el-col>
                </el-row>
                <el-row>
                    计划自产数量
                </el-row>
                <el-row :gutter="20">
                    <el-col>
                        <el-table v-loading="isLoading" :data="tab.productionAmountTable" border stripe
                            :max-height="500">
                            <el-table-column prop="colorName" label="颜色"></el-table-column>
                            <el-table-column prop="totalAmount" label="颜色总数"></el-table-column>
                            <!-- <el-table-column prop="" label="已设置外包数量"></el-table-column> -->
                            <el-table-column v-for="column in filteredColumns" :key="column.prop" :prop="column.prop"
                                :label="column.label">
                                <template v-slot="scope">
                                    <el-input-number v-model="scope.row[column.prop]" v-if="role == 6" :min="0"
                                        :step="1" />
                                    <span v-else>{{ scope.row[column.prop] }}</span>
                                </template>
                            </el-table-column>
                        </el-table>
                    </el-col>
                </el-row>
            </el-tab-pane>
        </el-tabs>
        <el-row :gutter="20" style="margin-top: 20px">
            <el-col :span="24" :offset="0">
                订单数量
                <el-table v-loading="isLoading" :data="shoeBatchInfo" :span-method="spanMethod" border stripe
                    :max-height="500">
                    <el-table-column prop="colorName" label="颜色"></el-table-column>
                    <el-table-column prop="totalAmount" label="颜色总数"></el-table-column>
                    <el-table-column v-for="column in filteredColumns" :key="column.prop" :prop="column.prop"
                        :label="column.label"></el-table-column>
                </el-table>
            </el-col>
        </el-row>
        <el-row :gutter="20" style="margin-top: 20px">
            <el-col :span="24" :offset="0">
                商务部工艺备注
                <el-input v-model="currentRow.technicalRemark" autosize type="textarea" readonly />
            </el-col>
        </el-row>
        <el-row :gutter="20" style="margin-top: 20px">
            <el-col :span="24" :offset="0">
                商务部材料备注
                <el-input v-model="currentRow.materialRemark" autosize type="textarea" readonly />
            </el-col>
        </el-row>
        <template #footer>
            <span>
                <el-button @click="isScheduleDialogOpen = false">取消</el-button>
                <el-button type="primary" @click="openProdDetailDialog(this.currentRow)">查看生产信息</el-button>
                <el-button v-if="role == 6"
                    type="success" @click="startProduction">下发排期</el-button>
            </span>
        </template>
    </el-dialog>
</template>
<script>
import AllHeader from '@/components/AllHeader.vue'
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus';
import { shoeBatchInfoTableSpanMethod, getShoeSizesName } from '../../utils'
import OrderSchedulingSearchDialog from '../../ProductionSharedPages/OrderSchedulingSearchDialog.vue';
export default {
    components: {
        AllHeader,
        OrderSchedulingSearchDialog,
    },
    data() {
        return {
            isSearchDialogVisible: false,
            customerNameOptions: [],
            searchForm: {
                orderDateRangeSearch: null,
                orderRIdSearch: null,
                shoeRIdSearch: null,
                customerProductNameSearch: null,
                statusNodeSearch: null,
                customerNameSearch: null,
                customerBrandSearch: null,
                sortCondition: null
            },
            currentProdDetailTab: "1",
            isProdDetailDialogOpen: false,
            showFilters: false,
            filters: [
                { label: 'Name', value: '', key: 'name' },
                { label: 'Age', value: '', key: 'age' },
                // Add more filters here
            ],
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
            logisticsMaterialData: [],
            logisticsRows: 0,
            isMaterialLogisticVis: false,
            logisticsCurrentPage: 1,
            logisticsPageSize: 10,
            instruction: false,
            specification: false,
            isMultipleSelection: false,
            selectedRows: [],
            isMultipleShoesDialogVis: false,
            multipleShoesScheduleForm: {},
            multiShoeFormTemplate: {
                cuttingLineNumbers: null,
                cuttingDateRange: null,
                preSewingLineNumbers: null,
                preSewingDateRange: null,
                sewingLineNumbers: null,
                sewingDateRange: null,
                moldingLineNumbers: null,
                moldingDateRange: null,
            },
            // productionLines,
            shoeSizes: [],
            isScheduleDialogOpen: false,
            shoeSizeColumns: [],
            activeTab: "cutting",
            tabs: [],
            // index 0: 裁断，1：预备，2：针车，3：成型
            tabsTemplate: [
                {
                    name: 'cutting',
                    label: '裁断排期',
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
                    label: '针车预备排期',
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
                    label: '针车排期',
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
                    label: '成型排期',
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
    computed: {
        filteredColumns() {
            return this.shoeSizeColumns.filter(column =>
                this.shoeBatchInfo.some(row => row[column.prop] !== undefined && row[column.prop] !== null && row[column.prop] !== 0)
            );
        }
    },
    methods: {
        determineActiveTab() {
            if (this.currentRow.schedulingStatus === '裁断未排期') {
                this.activeTab = 'cutting';
            }
            else if (this.currentRow.schedulingStatus === '预备未排期') {
                this.activeTab = 'preSewing';
            }
            else if (this.currentRow.schedulingStatus === '针车未排期') {
                this.activeTab = 'sewing';
            }
            else if (this.currentRow.schedulingStatus === '成型未排期') {
                this.activeTab = 'molding';
            }
        },
        disableTab(tabName) {
            if (tabName === 'cutting') {
                return false;
            }
            else if (tabName === 'preSewing' && this.currentRow.schedulingStatus !== '裁断未排期') {
                return false;
            }
            else if (tabName === 'sewing') {
                if (this.currentRow.schedulingStatus !== '裁断未排期' && this.currentRow.schedulingStatus !== '预备未排期') {
                    return false;
                }
            }
            else if (tabName === 'molding') {
                if (this.currentRow.schedulingStatus !== '裁断未排期' && this.currentRow.schedulingStatus !== '预备未排期' && this.currentRow.schedulingStatus !== '针车未排期') {
                    return false;
                }
            }
            return true;
        },
        async getAllCustomers() {
            const response = await axios.get(`${this.$apiBaseUrl}/customer/getallcustomers`)
            this.customerNameOptions = response.data
        },
        updateDialogVisible(newVal) {
            this.isSearchDialogVisible = newVal
        },
        handleSearch(values) {
            this.searchForm = { ...values }
            this.getOrderDataTable()
        },
        toggleFilters() {
            this.showFilters = !this.showFilters;
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
        async checkDateProductionStatus(tab) {
            if (tab.isDateStatusTableVis === true) {
                tab.isDateStatusTableVis = false
            }
            else {
                const params = { "startDate": tab.dateValue[0], "endDate": tab.dateValue[1], "team": tab.name }
                try {
                    const response = await axios.get(`${this.$apiBaseUrl}/production/productionmanager/checkdateproductionstatus`, { params })
                    tab.dateStatusTable = response.data
                    tab.dateStatusTable.forEach(element => {
                        let amount = 0
                        element.detail.forEach(row => {
                            row.averageAmount = this.calculateDailyProduction(row.totalAmount, [row.productionStartDate, row.productionEndDate])
                            amount += Number(row.averageAmount)
                        })
                        element.predictAmount = amount;
                        tab.isDateStatusTableVis = true
                    })
                }
                catch (error) {
                    ElMessage.error(error.response.data.message)
                }
            }
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
        openOutsourceFlow() {
            const params = {
                "orderId": this.currentRow.orderId,
                "orderRId": this.currentRow.orderRId,
                "orderShoeId": this.currentRow.orderShoeId,
                "shoeRId": this.currentRow.shoeRId,
            }
            const queryString = new URLSearchParams(params).toString();
            const url = `${window.location.origin}/productiongeneral/productionoutsource?${queryString}`
            window.open(url, '_blank')
        },
        async openScheduleDialog(row) {
            this.isLoading = true
            this.currentRow = row
            this.determineActiveTab()
            this.isScheduleDialogOpen = true
            this.shoeSizeColumns = await this.getShoeSizesName(row.orderId)
            this.tabs = JSON.parse(JSON.stringify(this.tabsTemplate))
            this.getOrderShoeScheduleInfo()
            await this.getOrderShoeBatchInfo()
            await this.getOutsourceAmount()
            await this.getOrderShoeProductionAmount()
            this.isLoading = false
        },
        async getOrderShoeScheduleInfo() {
            let params = { "orderShoeId": this.currentRow.orderShoeId }
            let response = await axios.get(`${this.$apiBaseUrl}/production/productionmanager/getordershoescheduleinfo`, { params })
            response.data.forEach((row, index) => {
                this.tabs[index].lineValue = row.lineGroup
                this.tabs[index].dateValue = [row.startDate, row.endDate]
                this.tabs[index].isOutsourced = row.isOutsourced
            })
        },
        async getOutsourceAmount() {
            let params = { "orderShoeId": this.currentRow.orderShoeId }
            let response = await axios.get(`${this.$apiBaseUrl}/production/productionmanager/getoutsourcebatchinfo`, { params })
            console.log(response.data)
        },
        async getOrderShoeBatchInfo() {
            this.shoeBatchInfo = []
            const params = { "orderShoeId": this.currentRow.orderShoeId }
            const response = await axios.get(`${this.$apiBaseUrl}/production/productionmanager/getordershoetypeamount`, { params })
            this.shoeBatchInfo = response.data
            console.log(this.shoeBatchInfo)
            this.spanMethod = shoeBatchInfoTableSpanMethod(this.shoeBatchInfo);
        },
        async getOrderShoeProductionAmount() {
            const params = { "orderShoeId": this.currentRow.orderShoeId }
            const response = await axios.get(`${this.$apiBaseUrl}/production/productionmanager/getordershoeproductionamount`, { params })
            this.tabs.forEach(row => {
                if (response.data[row.team] === undefined) {
                    row.productionAmountTable = []
                    let color_totals = {}
                    this.shoeBatchInfo.forEach(batchInfo => {
                        if (!(batchInfo.colorName in color_totals)) {
                            color_totals[batchInfo.colorName] = { ...batchInfo }
                        }
                        else {
                            for (let i = 34; i < 47; i++) {
                                color_totals[batchInfo.colorName][`size${i}Amount`] += batchInfo[`size${i}Amount`]
                            }
                            color_totals[batchInfo.colorName][`pairAmount`] += batchInfo[`pairAmount`]
                        }
                    })
                    for (let color_key in color_totals) {
                        row.productionAmountTable.push(color_totals[color_key])
                    }
                }
                else {
                    row.productionAmountTable = response.data[row.team]
                }
                // row.productionSpanMethod = shoeBatchInfoTableSpanMethod(row.productionAmountTable)
            })
            this.tabs[1].productionAmountTable = this.tabs[2].productionAmountTable
        },
        async saveMultipleSchedules() {
            this.$refs.multipleShoesScheduleForm.validate(async (valid) => {
                if (valid) {
                    try {
                        console.log(this.multipleShoesScheduleForm)
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
                    this.getOrderDataTable()
                    this.isMultipleShoesDialogVis = false
                }
                else {
                    console.log("testing2")
                }
            })
        },
        async modifyProductionSchedule() {
            try {
                let data = {
                    "orderShoeId": this.currentRow.orderShoeId,
                }
                let infoList = []
                this.tabs.forEach(row => {
                    let obj = {
                        "lineValue": row.lineValue.join(","),
                        "isOutsourced": row.isOutsourced,
                        "startDate": row.dateValue[0],
                        "endDate": row.dateValue[1]
                    }
                    infoList.push(obj)
                })
                data["productionInfoList"] = infoList
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
                            obj[`size${i}Amount`] = row[`size${i}Amount`]
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
            this.getOrderDataTable()
            this.isScheduleDialogOpen = false
        },
        async startProduction() {
            ElMessageBox.alert('请确认生产数量和外包数量', '警告', {
                confirmButtonText: '确认',
                showCancelButton: true,
                cancelButtonText: '取消'
            }).then(async () => {
                try {
                    await this.modifyProductionSchedule()
                    const data = { "orderId": this.currentRow.orderId, "orderShoeId": this.currentRow.orderShoeId }
                    await axios.patch(`${this.$apiBaseUrl}/production/productionmanager/startproduction`, data)
                    ElMessage.success("操作成功")
                }
                catch (error) {
                    console.log(error)
                    ElMessage.error("操作失败")
                }
                this.getOrderDataTable()
                this.isScheduleDialogOpen = false
            })
        },
        openMultipleShoesDialog() {
            if (this.selectedRows.length == 0) {
                this.isSelectedRowsEmpty = true
                return
            }
            this.multipleShoesScheduleForm = { ...this.multiShoeFormTemplate }
            this.isMultipleShoesDialogVis = true
            this.isSelectedRowsEmpty = false
        },
        toggleSelectionMode() {
            this.isMultipleSelection = !this.isMultipleSelection;
            this.isSelectedRowsEmpty = false
        },
        handleSelectionChange(selection) {
            this.selectedRows = selection
        },
        async handlePageChange(val) {
            this.currentPage = val
            await this.getOrderDataTable()
        },
        async handleSizeChange(val) {
            this.pageSize = val
            await this.getOrderDataTable()
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
            }
            let response = await axios.get(`${this.$apiBaseUrl}/production/getorderschedulingprogress`, { params })
            this.orderTableData = response.data.result
            this.orderTotalRows = response.data.totalLength
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
