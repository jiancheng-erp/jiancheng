<template>
    <el-row :gutter="20">
        <el-col>
            <OrderSchedulingSearchDialog :searchForm="searchForm" @updateSearchForm="handleSearch" />
        </el-col>
    </el-row>
    <el-row>
        <el-col>
            <el-button type="primary" v-if="role == 6" @click="openMultipleShoesDialog">
                多选鞋型排期
            </el-button>
        </el-col>
    </el-row>
    <el-row :gutter="20">
        <el-col :span="24" :offset="0">
            <el-table :data="orderTableData" stripe border style="height: 70vh"
                @selection-change="handleSelectionChange">
                <el-table-column type="selection" width="55"></el-table-column>
                <el-table-column prop="orderRid" label="订单号"></el-table-column>
                <el-table-column prop="shoeRid" label="工厂型号"></el-table-column>
                <el-table-column prop="cuttingStartDate" label="裁断开始"></el-table-column>
                <el-table-column prop="cuttingEndDate" label="裁断结束"></el-table-column>
                <el-table-column prop="preSewingStartDate" label="预备开始"></el-table-column>
                <el-table-column prop="preSewingEndDate" label="预备结束"></el-table-column>
                <el-table-column prop="sewingStartDate" label="针车开始"></el-table-column>
                <el-table-column prop="sewingEndDate" label="针车结束"></el-table-column>
                <el-table-column prop="moldingStartDate" label="成型开始"></el-table-column>
                <el-table-column prop="moldingEndDate" label="成型结束"></el-table-column>
                <el-table-column prop="schedulingStatus" label="排期状态"></el-table-column>
            </el-table>
        </el-col>
    </el-row>
    <el-row :gutter="20">
        <el-col>
            <el-pagination @size-change="handleSizeChange" @current-change="handlePageChange"
                :current-page="currentPage" :page-size="pageSize" layout="total, sizes, prev, pager, next, jumper"
                :total="orderTotalRows" />
        </el-col>
    </el-row>

    <el-dialog title="多选鞋型排期" v-model="isOrdersSchedulingDialogVis" fullscreen destroy-on-close @close="closeDialog">
        <el-row>
            <el-col>
                <el-date-picker v-model="uniformCuttingDateValue" type="daterange" size="default" range-separator="至"
                    value-format="YYYY-MM-DD" start-placeholder="裁断开始" end-placeholder="裁断结束" @change="test"/>
                <el-date-picker v-model="uniformPreSewingDateValue" type="daterange" size="default" range-separator="至"
                    value-format="YYYY-MM-DD" start-placeholder="预备开始" end-placeholder="预备结束" />
                <el-date-picker v-model="uniformSewingDateValue" type="daterange" size="default" range-separator="至"
                    value-format="YYYY-MM-DD" start-placeholder="针车开始" end-placeholder="针车结束" />
                <el-date-picker v-model="uniformMoldingDateValue" type="daterange" size="default" range-separator="至"
                    value-format="YYYY-MM-DD" start-placeholder="成型开始" end-placeholder="成型结束" />
                <el-button-group>
                    <el-button type="primary" @click="setDateValue">设置生产日期</el-button>
                    <el-button type="warning" @click="overwriteDateValue">覆盖生产日期</el-button>
                    <el-button type="danger" @click="clearDateValue">清空生产日期</el-button>
                </el-button-group>
            </el-col>
        </el-row>
        <el-row>
            <el-col>
                <el-date-picker v-model="schedulingStatusObj.dateValue" type="daterange" size="default"
                    range-separator="-" value-format="YYYY-MM-DD">
                </el-date-picker>
                <el-button type="primary" size="default" @click="checkDateProductionStatus()">{{
                    schedulingStatusObj.isDateStatusTableVis ? '关闭表格' : '查看工期内排期情况' }}</el-button>
            </el-col>
        </el-row>
        <el-table v-loading="schedulingStatusObj.isLoading" v-if="schedulingStatusObj.isDateStatusTableVis"
            :data="schedulingStatusObj.dateStatusTable" border stripe height="400px">
            <el-table-column type="expand">
                <template #default="props">
                    <el-table :data="props.row.detail" border stripe>
                        <el-table-column type="index" />
                        <el-table-column label="订单号" prop="orderRId" />
                        <el-table-column label="工厂型号" prop="shoeRId" />
                        <el-table-column label="裁断数量" prop="orderCuttingDayAmount" />
                        <el-table-column label="预备数量" prop="orderPreSewingDayAmount" />
                        <el-table-column label="针车数量" prop="orderSewingDayAmount" />
                        <el-table-column label="成型数量" prop="orderMoldingDayAmount" />
                    </el-table>
                </template>
            </el-table-column>

            <el-table-column prop="date" label="日期"> </el-table-column>
            <el-table-column prop="cuttingOrderShoeCount" label="裁断已排期订单数"> </el-table-column>
            <el-table-column prop="predictCuttingAmount" label="预计当日裁断生产量"> </el-table-column>
            <el-table-column prop="preSewingOrderShoeCount" label="预备已排期订单数"> </el-table-column>
            <el-table-column prop="predictPreSewingAmount" label="预计当日预备生产量"> </el-table-column>
            <el-table-column prop="sewingOrderShoeCount" label="针车已排期订单数"> </el-table-column>
            <el-table-column prop="predictSewingAmount" label="预计当日针车生产量"> </el-table-column>
            <el-table-column prop="moldingOrderShoeCount" label="成型已排期订单数"> </el-table-column>
            <el-table-column prop="predictMoldingAmount" label="预计当日成型生产量"> </el-table-column>
        </el-table>
        <el-row>
            <el-col>
                <el-table :data="selectedRows" stripe border style="height: 80vh">
                    <el-table-column type="expand" width="55">
                        <template #default="prop">
                            <el-table :data="prop.row.shoeBatchInfo" :span-method="prop.row.spanMethod" border stripe>
                                <el-table-column prop="colorName" label="颜色"></el-table-column>
                                <el-table-column prop="totalAmount" label="颜色总数"></el-table-column>
                                <el-table-column v-for="column in filteredColumns(prop.row)" :key="column.prop"
                                    :prop="column.prop" :label="column.label"></el-table-column>
                            </el-table>
                        </template>
                    </el-table-column>
                    <el-table-column prop="orderRid" label="订单号" width="120px"></el-table-column>
                    <el-table-column prop="shoeRid" label="工厂型号" width="120px"></el-table-column>
                    <el-table-column label="裁断排期">
                        <template #default="scope">
                            <el-date-picker v-model="scope.row.cuttingDateValue" type="daterange" size="default"
                                range-separator="至" value-format="YYYY-MM-DD" />
                        </template>
                    </el-table-column>
                    <el-table-column label="预备排期">
                        <template #default="scope">
                            <el-date-picker v-model="scope.row.preSewingDateValue" type="daterange" size="default"
                                range-separator="至" value-format="YYYY-MM-DD" />
                        </template>
                    </el-table-column>
                    <el-table-column label="针车排期">
                        <template #default="scope">
                            <el-date-picker v-model="scope.row.sewingDateValue" type="daterange" size="default"
                                range-separator="至" value-format="YYYY-MM-DD" />
                        </template>
                    </el-table-column>
                    <el-table-column label="成型排期">
                        <template #default="scope">
                            <el-date-picker v-model="scope.row.moldingDateValue" type="daterange" size="default"
                                range-separator="至" value-format="YYYY-MM-DD" />
                        </template>
                    </el-table-column>
                </el-table>
            </el-col>
        </el-row>
        <template #footer>
            <span class="dialog-footer">
                <el-button @click="closeDialog">取消</el-button>
                <el-button type="primary" @click="startProduction">下发排期</el-button>
            </span>
        </template>

    </el-dialog>

</template>
<script>
import AllHeader from '@/components/AllHeader.vue'
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus';
import { shoeBatchInfoTableSpanMethod } from '../../utils'
import OrderSchedulingSearchDialog from '../../ProductionSharedPages/OrderSchedulingSearchDialog.vue';
export default {
    components: {
        AllHeader,
        OrderSchedulingSearchDialog,
    },
    data() {
        return {
            role: localStorage.getItem('role'),
            isSearchDialogVisible: false,
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
            uniformCuttingDateValue: null,
            uniformPreSewingDateValue: null,
            uniformSewingDateValue: null,
            uniformMoldingDateValue: null,
            orderTableData: [],
            orderTotalRows: 0,
            currentPage: 1,
            pageSize: 10,
            selectedRows: [],
            isMultiOrders: false,
            isOrdersSchedulingDialogVis: false,
            schedulingStatusObj: {
                dateValue: null,
                dateStatusTable: [],
                isDateStatusTableVis: false,
                isLoading: false,
            }
        }
    },
    mounted() {
        this.getOrderDataTable()
    },
    methods: {
        test() {
            console.log(this.uniformCuttingDateValue, this.uniformPreSewingDateValue, this.uniformSewingDateValue, this.uniformMoldingDateValue)
        },
        async saveProductionSchedule() {
            try {
                let data = []
                for (let row of this.selectedRows) {
                    let obj = {
                        "orderShoeId": row.orderShoeId,
                        "cuttingDateValue": row.cuttingDateValue ? row.cuttingDateValue : [null, null],
                        "preSewingDateValue": row.preSewingDateValue ? row.preSewingDateValue : [null, null],
                        "sewingDateValue": row.sewingDateValue ? row.sewingDateValue : [null, null],
                        "moldingDateValue": row.moldingDateValue ? row.moldingDateValue : [null, null],
                    }
                    data.push(obj)
                }
                await axios.patch(`${this.$apiBaseUrl}/production/productionmanager/savemultipleschedules`, data)
                ElMessage.success("修改成功")
            }
            catch (error) {
                ElMessage.error("修改失败")
            }
        },
        async startProduction() {
            ElMessageBox.alert('确认下发排期吗？', '警告', {
                confirmButtonText: '确认',
                showCancelButton: true,
                cancelButtonText: '取消'
            }).then(async () => {
                try {
                    await this.saveProductionSchedule()
                    let data = []
                    for (let i = 0; i < this.selectedRows.length; i++) {
                        let obj = {
                            "orderId": this.selectedRows[i].orderId,
                            "orderShoeId": this.selectedRows[i].orderShoeId,
                        }
                        data.push(obj)
                    }
                    await axios.patch(`${this.$apiBaseUrl}/production/productionmanager/startproduction`, data)
                    ElMessage.success("操作成功")
                }
                catch (error) {
                    console.log(error)
                    ElMessage.error("操作失败")
                }
                this.getOrderDataTable()
                this.isOrdersSchedulingDialogVis = false
            })
        },
        setDateValue() {
            this.selectedRows.forEach(row => {
                if (row.cuttingDateValue == null) row.cuttingDateValue = this.uniformCuttingDateValue
                if (row.preSewingDateValue == null) {
                    row.preSewingDateValue = this.uniformPreSewingDateValue
                }
                if (!row.sewingDateValue) row.sewingDateValue = this.uniformSewingDateValue
                if (!row.moldingDateValue) row.moldingDateValue = this.uniformMoldingDateValue
            })
            ElMessage.success('已设置排期')
        },
        overwriteDateValue() {
            this.selectedRows.forEach(row => {
                row.cuttingDateValue = this.uniformCuttingDateValue ? this.uniformCuttingDateValue : row.cuttingDateValue
                row.preSewingDateValue = this.uniformPreSewingDateValue ? this.uniformPreSewingDateValue : row.preSewingDateValue
                row.sewingDateValue = this.uniformSewingDateValue ? this.uniformSewingDateValue : row.sewingDateValue
                row.moldingDateValue = this.uniformMoldingDateValue ? this.uniformMoldingDateValue : row.moldingDateValue
            })
            ElMessage.success('已覆盖排期')
        },
        clearDateValue() {
            this.selectedRows.forEach(row => {
                row.cuttingDateValue = null
                row.preSewingDateValue = null
                row.sewingDateValue = null
                row.moldingDateValue = null
            })
            ElMessage.success('已清空所有日期')
        },
        filteredColumns(table) {
            return table.shoeSizeColumns.filter(column =>
                table.shoeBatchInfo.some(row => row[column.prop] !== undefined && row[column.prop] !== null && row[column.prop] !== 0)
            );
        },
        async openMultipleShoesDialog() {
            if (this.selectedRows.length == 0) {
                ElMessage.warning('请至少选择一个订单进行排期')
                return
            }
            // get order batch info for selected rows
            let params = {
                orderShoeIds: this.selectedRows.map(row => row.orderShoeId).toString()
            }
            let response = await axios.get(`${this.$apiBaseUrl}/production/getamountfororders`, { params })
            let orderShoeAmountMap = response.data

            params = { orderIds: this.selectedRows.map(row => row.orderId).toString() }
            response = await axios.get(`${this.$apiBaseUrl}/batchtype/getbatchtypefororders`, { params })
            let orderShoeSizesMap = response.data
            // set date range values for selected rows
            for (let row of this.selectedRows) {
                row.cuttingDateValue = row.cuttingStartDate ? [row.cuttingStartDate, row.cuttingEndDate] : null
                row.preSewingDateValue = row.preSewingStartDate ? [row.preSewingStartDate, row.preSewingEndDate] :null
                row.sewingDateValue = row.sewingStartDate ? [row.sewingStartDate, row.sewingEndDate] : null
                row.moldingDateValue = row.moldingStartDate ? [row.moldingStartDate, row.moldingEndDate] : null
                row.shoeBatchInfo = orderShoeAmountMap[row.orderShoeId] || []
                row.shoeSizeColumns = orderShoeSizesMap[row.orderId] || []
                row.spanMethod = shoeBatchInfoTableSpanMethod(row.shoeBatchInfo)
            }
            this.isOrdersSchedulingDialogVis = true
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
                "statusNode": this.searchForm.statusNodeSearch,
            }
            let response = await axios.get(`${this.$apiBaseUrl}/production/getorderschedulingprogress`, { params })
            this.orderTableData = response.data.result
            this.orderTotalRows = response.data.totalLength
        },
        async checkDateProductionStatus() {
            if (this.schedulingStatusObj.dateValue[0] == null || this.schedulingStatusObj.dateValue[1] == null) {
                ElMessage.warning('请选择日期范围')
                return
            }
            if (this.schedulingStatusObj.isDateStatusTableVis) {
                this.schedulingStatusObj.isDateStatusTableVis = false
                return
            }
            this.schedulingStatusObj.isLoading = true
            this.schedulingStatusObj.isDateStatusTableVis = true
            try {
                let params_list = []
                for (const [index, name] of ['cutting', 'preSewing', 'sewing', 'molding'].entries()) {
                    params_list.push({
                        "startDate": this.schedulingStatusObj.dateValue[0],
                        "endDate": this.schedulingStatusObj.dateValue[1],
                        "team": name
                    })
                }
                let statusTableMap = {
                    'cutting': [],
                    'preSewing': [],
                    'sewing': [],
                    'molding': []
                }
                for (let index in params_list) {
                    let params = params_list[index]
                    let response = await axios.get(`${this.$apiBaseUrl}/production/productionmanager/checkdateproductionstatus`, { params })
                    statusTableMap[params.team] = response.data
                    statusTableMap[params.team].forEach(element => {
                        let amount = 0
                        element.detail.forEach(row => {
                            row.averageAmount = this.calculateDailyProduction(row.totalAmount, [row.productionStartDate, row.productionEndDate])
                            amount += Number(row.averageAmount)
                        })
                        element.predictAmount = amount;
                    })
                }
                console.log(statusTableMap)
                // construct the final date status table
                this.schedulingStatusObj.dateStatusTable = []
                for (let i = 0; i < statusTableMap['cutting'].length; i++) {
                    let dateStatus = {
                        date: statusTableMap['cutting'][i].date,
                        cuttingOrderShoeCount: statusTableMap['cutting'][i].orderShoeCount,
                        predictCuttingAmount: statusTableMap['cutting'][i].predictAmount,
                        preSewingOrderShoeCount: statusTableMap['preSewing'][i].orderShoeCount,
                        predictPreSewingAmount: statusTableMap['preSewing'][i].predictAmount,
                        sewingOrderShoeCount: statusTableMap['sewing'][i].orderShoeCount,
                        predictSewingAmount: statusTableMap['sewing'][i].predictAmount,
                        moldingOrderShoeCount: statusTableMap['molding'][i].orderShoeCount,
                        predictMoldingAmount: statusTableMap['molding'][i].predictAmount,
                        detail: []
                    }
                    // merge the details
                    // collect all orderRId
                    let orderRIds = new Set();
                    statusTableMap['cutting'][i].detail.forEach(detail => orderRIds.add(detail.orderRId));
                    statusTableMap['preSewing'][i].detail.forEach(detail => orderRIds.add(detail.orderRId));
                    statusTableMap['sewing'][i].detail.forEach(detail => orderRIds.add(detail.orderRId));
                    statusTableMap['molding'][i].detail.forEach(detail => orderRIds.add(detail.orderRId));
                    // turn orderRIds into an array and sort it
                    orderRIds = Array.from(orderRIds).sort((a, b) => a - b);
                    // loop through orderRIds and find the details in each stage
                    for (let orderRId of orderRIds) {
                        let teamDetail = {
                            orderRId: orderRId,
                            shoeRId: null,
                            orderCuttingDayAmount: 0,
                            orderPreSewingDayAmount: 0,
                            orderSewingDayAmount: 0,
                            orderMoldingDayAmount: 0,
                        }
                        // find the detail in each stage
                        for (let [index, name] of ['cutting', 'preSewing', 'sewing', 'molding'].entries()) {
                            let detail = statusTableMap[name][i].detail.find(d => d.orderRId === orderRId);
                            if (detail) {
                                teamDetail.shoeRId = detail.shoeRId || teamDetail.shoeRId;
                                teamDetail[`order${name.charAt(0).toUpperCase() + name.slice(1)}DayAmount`] = detail.averageAmount || 0;
                            }
                        }
                        dateStatus.detail.push(teamDetail)
                    }
                    this.schedulingStatusObj.dateStatusTable.push(dateStatus)
                }
            }
            catch (error) {
                console.log(error)
                ElMessage.error(error.responsee)
            }
            finally {
                this.schedulingStatusObj.isLoading = false
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
        handleSelectionChange(selection) {
            this.selectedRows = selection
        },
        handleSearch(values) {
            this.searchForm = { ...values }
            this.getOrderDataTable()
        },
        handlePageChange(val) {
            this.currentPage = val
            this.getOrderDataTable()
        },
        handleSizeChange(val) {
            this.pageSize = val
            this.getOrderDataTable()
        },
        closeDialog() {
            this.isOrdersSchedulingDialogVis = false
            this.selectedRows = []
            this.uniformCuttingDateValue = null
            this.uniformPreSewingDateValue = null
            this.uniformSewingDateValue = null
            this.uniformMoldingDateValue = null
        }
    },
}
</script>
