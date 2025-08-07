<template>
    <el-row :gutter="20">
        <el-col :span="16" :offset="0">
            <el-input v-model="orderNumberSearch" placeholder="请输入订单号" clearable @keypress.enter="getTableData()"
                @clear="getTableData" class="search-input" />
            <el-input v-model="customerNameSearch" placeholder="请输入客户名称" clearable @keypress.enter="getTableData()"
                @clear="getTableData" class="search-input" />
            <el-input v-model="orderCIdSearch" placeholder="请输入客户订单号" clearable @keypress.enter="getTableData()"
                @clear="getTableData" class="search-input" />
            <el-input v-model="customerBrandSearch" placeholder="请输入客户商标" clearable @keypress.enter="getTableData()"
                @clear="getTableData" class="search-input" />
        </el-col>
    </el-row>
    <el-row>
        <el-col :span="12">
            <span>审核状态筛选：</span>
            <el-radio-group v-model="auditStatusNum" @change="getTableData">
                <el-radio-button v-for="option in auditStatusOptions" :label="option.value">
                    {{ option.label }}
                </el-radio-button>
            </el-radio-group>
        </el-col>
        <el-col :span="12">
            <span>仓库状态筛选：</span>
            <el-radio-group v-model="storageStatusNum" @change="getTableData">
                <el-radio-button v-for="option in storageStatusOptions" :label="option.value">
                    {{ option.label }}
                </el-radio-button>
            </el-radio-group>
        </el-col>
    </el-row>
    <el-row :gutter="20">
        <el-col :span="8" :offset="0">
            <el-button-group v-if="role == 20">
                <el-button type="warning" v-if="isMultipleSelection" @click="openOperationDialog(1)"
                    :disabled="storageStatusNum === FINISHED_STORAGE_STATUS_ENUM.PRODUCT_OUTBOUND_FINISHED">
                    批量出库
                </el-button>
                <el-button type="primary" @click="toggleSelectionMode"
                    :disabled="storageStatusNum === FINISHED_STORAGE_STATUS_ENUM.PRODUCT_OUTBOUND_FINISHED">
                    {{ isMultipleSelection ? "退出" : "选择成品出库" }}
                </el-button>
            </el-button-group>
            <el-button-group v-else>
                <el-button type="warning" v-if="isMultipleSelection" @click="approveOutbound">
                    批准出库
                </el-button>
                <el-button type="primary" @click="toggleSelectionMode">
                    {{ isMultipleSelection ? "退出" : "选择订单" }}
                </el-button>
            </el-button-group>
        </el-col>
    </el-row>
    <el-row :gutter="20">
        <el-col :span="24" :offset="0">
            <el-table :data="tableData" border stripe @selection-change="handleSelectionChange" height="50vh">
                <el-table-column v-if="isMultipleSelection" type="selection" width="55" />
                <el-table-column type="expand">
                    <template #default="{ row }">
                        <el-table :data="row.orderShoeTable" border stripe>
                            <el-table-column prop="shoeRId" label="工厂型号" />
                            <el-table-column prop="customerProductName" label="客户鞋号" />
                            <el-table-column prop="colorName" label="颜色" />
                            <el-table-column prop="orderAmountPerColor" label="订单数量" />
                            <el-table-column prop="currentStock" label="库存" />
                            <el-table-column prop="outboundedAmount" label="已出库数量"></el-table-column>
                        </el-table>
                    </template>
                </el-table-column>
                <el-table-column prop="orderRId" label="订单号"></el-table-column>
                <el-table-column prop="customerName" label="客户名称"></el-table-column>
                <el-table-column prop="orderCId" label="客户订单号"></el-table-column>
                <el-table-column prop="customerBrand" label="客户商标"></el-table-column>
                <el-table-column prop="orderAmount" label="订单数量"></el-table-column>
                <el-table-column prop="currentStock" label="成品库存"></el-table-column>
                <el-table-column prop="outboundedAmount" label="已出库数量"></el-table-column>
                <el-table-column label="仓库状态">
                    <template #default="{ row }">
                        <el-tag v-if="row.storageStatusNum == FINISHED_STORAGE_STATUS_ENUM.PRODUCT_INBOUND_NOT_FINISHED"
                            type="warning" disable-transitions>{{ row.storageStatusLabel }}</el-tag>
                        <el-tag v-else-if="row.storageStatusNum == FINISHED_STORAGE_STATUS_ENUM.PRODUCT_INBOUND_FINISHED"
                            type="success" disable-transitions>{{ row.storageStatusLabel }}</el-tag>
                        <el-tag v-else-if="row.storageStatusNum == FINISHED_STORAGE_STATUS_ENUM.PRODUCT_OUTBOUND_FINISHED"
                            type="success" disable-transitions>{{ row.storageStatusLabel }}</el-tag>
                    </template>
                </el-table-column>
                <el-table-column label="审核状态">
                    <template #default="{ row }">
                        <el-tag
                            v-if="row.auditStatusNum == PRODUCT_OUTBOUND_AUDIT_STATUS_ENUM.PRODUCT_OUTBOUND_AUDIT_NOT_INIT"
                            type="warning" disable-transitions>{{ row.auditStatusLabel }}</el-tag>
                        <el-tag
                            v-else-if="row.auditStatusNum == PRODUCT_OUTBOUND_AUDIT_STATUS_ENUM.PRODUCT_OUTBOUND_AUDIT_ONGOING"
                            type="warning" disable-transitions>{{ row.auditStatusLabel }}</el-tag>
                        <el-tag
                            v-else-if="row.auditStatusNum == PRODUCT_OUTBOUND_AUDIT_STATUS_ENUM.PRODUCT_OUTBOUND_AUDIT_APPROVED"
                            type="success" disable-transitions>{{ row.auditStatusLabel }}</el-tag>
                    </template>
                </el-table-column>
            </el-table>
        </el-col>
    </el-row>
    <el-row :gutter="20">
        <el-col>
            <el-pagination @size-change="handleSizeChange" @current-change="handlePageChange"
                :current-page="currentPage" :page-sizes="pageSizes" :page-size="pageSize"
                layout="total, sizes, prev, pager, next, jumper" :total="totalRows" />
        </el-col>
    </el-row>
    <el-dialog :title="operationLabels.dialogTitle[currentOperation]" v-model="isOutboundDialogVisible" width="70%">
        <el-form v-model="outboundForm">
            <el-form-item prop="remark" label="备注">
                <el-input v-model="outboundForm.remark" :maxlength="40" show-word-limit size="small"></el-input>
            </el-form-item>
        </el-form>
        <el-table :data="outboundForm.items" style="width: 100%" border stripe>
            <el-table-column prop="orderRId" label="订单号" />
            <el-table-column prop="shoeRId" label="工厂型号" />
            <el-table-column prop="colorName" label="颜色" />
            <el-table-column prop="currentStock" label="总数量" />
            <el-table-column :label="operationLabels.operationAmount[currentOperation]">
                <template #default="scope">
                    <el-input-number v-model="scope.row.outboundQuantity" :min="0"></el-input-number>
                </template>
            </el-table-column>
            <el-table-column prop="remark" label="备注">
                <template #default="scope">
                    <el-input v-model="scope.row.remark" :maxlength="40" show-word-limit size="small">
                    </el-input>
                </template>
            </el-table-column>
        </el-table>
        <template #footer>
            <span>
                <el-button @click="isOutboundDialogVisible = false">返回</el-button>
                <el-button type="primary" @click="submitOperationForm">出库</el-button>
            </span>
        </template>
    </el-dialog>

    <el-dialog title="数量输入框" v-model="isOpenQuantityDialogVisible" width="60%">
        <el-form>
            <el-form-item>
                <el-table :data="filteredData" border stripe>
                    <el-table-column prop="shoeSizeName" label="鞋码"></el-table-column>
                    <el-table-column prop="predictQuantity" label="应出库数量"></el-table-column>
                    <el-table-column prop="outboundedQuantity" label="已出库数量"></el-table-column>
                    <el-table-column prop="currentQuantity" label="库存"></el-table-column>
                    <el-table-column :label="operationLabels.operationAmount[currentOperation]">
                        <template #default="scope">
                            <el-input-number v-model="scope.row.operationQuantity" size="small" :min="0"
                                :max="scope.row.currentQuantity" @change="updateTotalShoes"></el-input-number>
                        </template>
                    </el-table-column>
                </el-table>
            </el-form-item>
        </el-form>
        <template #footer>
            <el-button type="primary" @click="isOpenQuantityDialogVisible = false">
                确认
            </el-button>
        </template>
    </el-dialog>

    <el-dialog title="各鞋码生产进度" v-model="isOpenShoeSizeDialogVisible" width="80%">
        <el-tabs v-model="activeStockTab">
            <el-tab-pane v-for="(row, index) in currentRow.orderShoeTable" :key="row.orderShoeTypeId"
                :label="`${row.shoeRId}-${row.colorName}`" :name="row.orderShoeTypeId">
                <el-table :data="row.shoesOutboundTable" border stripe>
                    <el-table-column prop="shoeSizeName" label="鞋码"></el-table-column>
                    <el-table-column prop="predictQuantity" label="订单数量"></el-table-column>
                    <el-table-column prop="currentQuantity" label="库存"></el-table-column>
                    <el-table-column prop="outboundedQuantity" label="已出库数量"></el-table-column>
                </el-table>
            </el-tab-pane>
        </el-tabs>
        <template #footer>
            <el-button type="primary" @click="isOpenShoeSizeDialogVisible = false">
                确认
            </el-button>
        </template>
    </el-dialog>
</template>
<script>
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus';
import { PAGESIZE, PAGESIZES } from '../../warehouseUtils';
export default {
    data() {
        return {
            formItemTemplate: {
                picker: null,
                remark: null,
                items: [],
            },
            outboundForm: {},
            currentPage: 1,
            pageSize: PAGESIZE,
            pageSizes: PAGESIZES,
            tableData: [],
            totalRows: 0,
            orderNumberSearch: '',
            orderCIdSearch: '',
            customerNameSearch: '',
            customerBrandSearch: '',
            currentRow: {},
            isMultipleSelection: false,
            selectedRows: [],
            isOutboundDialogVisible: false,
            activeTab: null,
            currentQuantityRow: null,
            isOpenQuantityDialogVisible: false,
            // 0: inbound, 1: outbound
            currentOperation: 0,
            operationLabels: {
                "dialogTitle": ["成品入库", "成品出库"],
                "timestamp": ["入库日期", "出库日期"],
                "operationAmount": ["入库数量", "出库数量"],
            },
            clientTab: null,
            role: localStorage.getItem('role'),
            auditStatusOptions: [],
            storageStatusOptions: [],
            auditStatusNum: null,
            storageStatusNum: null,
            isOpenShoeSizeDialogVisible: false,
            activeStockTab: null,
            FINISHED_STORAGE_STATUS_ENUM: {},
            PRODUCT_OUTBOUND_AUDIT_STATUS_ENUM: {}
        }
    },
    computed: {
        filteredData() {
            return this.currentQuantityRow.shoesOutboundTable.filter((row) => {
                return (
                    row.predictQuantity > 0
                );
            });
        },
    },
    async mounted() {
        await this.getStorageStatusOptions()
        await this.getOutboundAuditStatusOptions()
        this.displayOrdersbyRole()
        this.getTableData()
    },
    methods: {
        jumpToAllForAuditStatus() {
            if (this.storageStatusNum == this.FINISHED_STORAGE_STATUS_ENUM.PRODUCT_OUTBOUND_FINISHED) {
                this.auditStatusNum = this.PRODUCT_OUTBOUND_AUDIT_STATUS_ENUM.ALL
            }
        },
        async getStorageStatusOptions() {
            const response = await axios.get(`${this.$apiBaseUrl}/product/getstoragestatusoptions`)
            this.storageStatusOptions = response.data.storageStatusOptions
            this.FINISHED_STORAGE_STATUS_ENUM = response.data.storageStatusEnum
        },
        async getOutboundAuditStatusOptions() {
            const response = await axios.get(`${this.$apiBaseUrl}/product/getoutboundauditstatusoptions`)
            this.auditStatusOptions = response.data.productOutboundAuditStatusOptions
            this.PRODUCT_OUTBOUND_AUDIT_STATUS_ENUM = response.data.productOutboundAuditStatusEnum
        },
        displayOrdersbyRole() {
            this.storageStatusNum = this.FINISHED_STORAGE_STATUS_ENUM.ALL
            this.auditStatusNum = this.PRODUCT_OUTBOUND_AUDIT_STATUS_ENUM.ALL
            if (this.role == 4 || this.role == 21) {
                this.auditStatusNum = this.PRODUCT_OUTBOUND_AUDIT_STATUS_ENUM.PRODUCT_OUTBOUND_AUDIT_NOT_INIT
            }
            else if (this.role == 2) {
                this.auditStatusNum = this.PRODUCT_OUTBOUND_AUDIT_STATUS_ENUM.PRODUCT_OUTBOUND_AUDIT_ONGOING
            }
            else if (this.role == 20) {
                this.auditStatusNum = this.PRODUCT_OUTBOUND_AUDIT_STATUS_ENUM.PRODUCT_OUTBOUND_AUDIT_APPROVED
            }
        },
        async checkOutboundPrequisite() {
            if (this.selectedRows.length == 0) {
                ElMessage.error("未选择订单")
                return false
            }
            let unfinishedOrders = this.selectedRows.filter(row => row.currentStock + row.outboundedAmount < row.orderAmount).map(row => row.orderRId)
            if (unfinishedOrders.length > 0) {
                try {
                    await ElMessageBox.alert(`以下订单未完成入库:${unfinishedOrders.toString()}, 是否继续`, '警告', {
                        confirmButtonText: '确认',
                        showCancelButton: true,
                        cancelButtonText: '取消'
                    });
                    return true
                }
                catch (error) {
                    ElMessage.info("操作已取消")
                    return false
                }
            }
            return true
        },
        async approveOutbound() {
            if (!await this.checkOutboundPrequisite()) {
                return
            }
            try {
                let params = this.selectedRows.map((row) => row.orderId)
                let response = null
                if (this.role == 4 || this.role == 21) {
                    response = await axios.patch(`${this.$apiBaseUrl}/order/approveoutboundbybusiness`, params)
                }
                else if (this.role == 2) {
                    response = await axios.patch(`${this.$apiBaseUrl}/order/approveoutboundbygeneralmanager`, params)
                }
                ElMessage.success(response.data.message)
                this.getTableData()
            }
            catch (error) {
                console.log(error)
                ElMessage.error("操作异常")
            }
        },
        syncTimestamp(source_group) {
            return this.operationForm.groupedSelectedRows.map(group => {
                group.timestamp = source_group.timestamp
            })
        },
        updateTotalShoes() {
            this.currentQuantityRow.shoesOutboundTable.forEach((element, index) => {
                this.currentQuantityRow[`amount${index}`] = element.operationQuantity
            })
            this.currentQuantityRow.operationQuantity = this.filteredData.reduce((acc, row) => {
                return acc + row.operationQuantity;
            }, 0);
        },
        openQuantityDialog(row) {
            this.currentQuantityRow = row
            this.isOpenQuantityDialogVisible = true
        },
        async openShoeSizeDialog(row) {
            this.currentRow = row
            let response = await this.getShoeSizeColumnsForOrder(row)
            let targetedStorageStock = response.data
            for (let i = 0; i < row.orderShoeTable.length; i++) {
                row.orderShoeTable[i]["shoesOutboundTable"] = targetedStorageStock[row.orderShoeTable[i].storageId]
            }
            this.activeStockTab = row.orderShoeTable[0].orderShoeTypeId
            this.isOpenShoeSizeDialogVisible = true
        },
        toggleSelectionMode() {
            this.isMultipleSelection = !this.isMultipleSelection;
        },
        handleSelectionChange(selection) {
            this.selectedRows = selection;
        },
        openOperationDialog(operation) {
            if (this.selectedRows.length == 0) {
                ElMessage.error("未选择材料")
                return
            }
            for (let row of this.selectedRows) {
                if (row.isOutboundAllowed != 2) {
                    ElMessage.error("存在不可出货订单")
                    return
                }
            }
            this.currentOperation = operation
            this.groupSelectedRows();
            this.isOutboundDialogVisible = true
        },
        async getShoeSizeColumnsForOrder(row) {
            let params = { "orderId": row.orderId }
            let response = await axios.get(`${this.$apiBaseUrl}/warehouse/getmultipleshoesizecolumns`, { params })
            return response
        },
        async groupSelectedRows() {
            let selectedRowsCopy = JSON.parse(JSON.stringify(this.selectedRows))
            this.outboundForm = JSON.parse(JSON.stringify(this.formItemTemplate))
            for (let i = 0; i < selectedRowsCopy.length; i++) {
                for (let j = 0; j < selectedRowsCopy[i].orderShoeTable.length; j++) {
                    let orderShoe = selectedRowsCopy[i].orderShoeTable[j]
                    orderShoe.outboundQuantity = orderShoe.currentStock
                    orderShoe.remark = null
                    this.outboundForm.items.push({
                        ...orderShoe,
                        orderRId: selectedRowsCopy[i].orderRId,
                        orderId: selectedRowsCopy[i].orderId,
                    })
                }
            }
            console.log(this.outboundForm)
        },
        async getTableData() {
            this.jumpToAllForAuditStatus();
            const params = {
                "page": this.currentPage,
                "pageSize": this.pageSize,
                "orderRId": this.orderNumberSearch,
                "orderCId": this.orderCIdSearch,
                "customerName": this.customerNameSearch,
                "customerBrand": this.customerBrandSearch,
                "auditStatusNum": this.auditStatusNum,
                "storageStatusNum": this.storageStatusNum
            }
            const response = await axios.get(`${this.$apiBaseUrl}/warehouse/getproductoverview`, { params })
            this.tableData = response.data.result
            this.totalRows = response.data.total
        },
        async submitOperationForm() {
            console.log(this.outboundForm)
            try {
                await axios.patch(`${this.$apiBaseUrl}/warehouse/warehousemanager/outboundfinished`, this.outboundForm)
                ElMessage.success("出库成功")
            }
            catch (error) {
                console.log(error)
                ElMessage.error("操作异常")
            }
            // this.isOutboundDialogVisible = false
            this.getTableData()
        },
        handleSizeChange(val) {
            this.pageSize = val
            this.getTableData()
        },
        handlePageChange(val) {
            this.currentPage = val
            this.getTableData()
        },
        finishOutbound(row) {
            ElMessageBox.alert('提前完成半成品出库，是否继续？', '警告', {
                confirmButtonText: '确认',
                showCancelButton: true,
                cancelButtonText: '取消'
            }).then(async () => {
                const data = { "storageId": row.storageId }
                await axios.patch(`${this.$apiBaseUrl}/warehouse/warehousemanager/finishoutboundsemifinished`, data)
                try {
                    ElMessage.success("操作成功")
                }
                catch (error) {
                    console.log(error)
                    ElMessage.error("操作异常")
                }
                this.getTableData()
            })
        }
    }
}
</script>
<style></style>
