<template>
    <el-row :gutter="20">
        <el-col :span="4" :offset="0" style="white-space: nowrap;">
            <el-input v-model="orderNumberSearch" placeholder="请输入订单号" clearable @keypress.enter="getTableData()"
                @clear="getTableData" />
        </el-col>
        <el-col :span="4" :offset="0" style="white-space: nowrap;">
            <el-input v-model="customerNameSearch" placeholder="请输入客户名称" clearable @keypress.enter="getTableData()"
                @clear="getTableData" />
        </el-col>
        <el-col :span="4" :offset="0" style="white-space: nowrap;">
            <el-input v-model="orderCIdSearch" placeholder="请输入客户订单号" clearable @keypress.enter="getTableData()"
                @clear="getTableData" />
        </el-col>
        <el-col :span="4" :offset="0" style="white-space: nowrap;">
            <el-input v-model="customerBrandSearch" placeholder="请输入客户商标" clearable @keypress.enter="getTableData()"
                @clear="getTableData" />
        </el-col>
        <el-col :span="4" :offset="0" style="white-space: nowrap;">
            <el-select v-model="selectedStatus" placeholder="请选择审核状态" clearable @change="getTableData">
                <el-option v-for="item in statusOptions" :key="item.value" :label="item.label" :value="item.value" />
            </el-select>
        </el-col>
    </el-row>
    <el-row :gutter="20">
        <el-col :span="8" :offset="0">
            <el-button-group v-if="role == 20">
                <el-button v-if="isMultipleSelection" @click="openOperationDialog(1)">
                    批量出库
                </el-button>
                <el-button @click="toggleSelectionMode">
                    {{ isMultipleSelection ? "退出" : "选择成品出库" }}
                </el-button>
            </el-button-group>
            <el-button-group v-else>
                <el-button v-if="isMultipleSelection" @click="approveOutbound">
                    批准出库
                </el-button>
                <el-button @click="toggleSelectionMode">
                    {{ isMultipleSelection ? "退出" : "选择订单" }}
                </el-button>
            </el-button-group>
        </el-col>
    </el-row>
    <el-row :gutter="20">
        <el-col :span="24" :offset="0">
            <el-table :data="tableData" border stripe @selection-change="handleSelectionChange">
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
                <el-table-column label="允许出库">
                    <template #default="{ row }">
                        <el-tag v-if="row.isOutboundAllowed == 0" type="warning">业务部审核</el-tag>
                        <el-tag v-else-if="row.isOutboundAllowed == 1" type="warning">总经理审核</el-tag>
                        <el-tag v-else-if="row.isOutboundAllowed == 2" type="success">已批准</el-tag>
                    </template>
                </el-table-column>
                <el-table-column label="详细库存">
                    <template #default="{ row }">
                        <el-button type="primary" size="small" @click="openShoeSizeDialog(row)">打开</el-button>
                    </template>
                </el-table-column>
            </el-table>
        </el-col>
    </el-row>
    <el-row :gutter="20">
        <el-col :span="12" :offset="14">
            <el-pagination @size-change="handleSizeChange" @current-change="handlePageChange"
                :current-page="currentPage" :page-sizes="[10, 20, 30, 40]" :page-size="pageSize"
                layout="total, sizes, prev, pager, next, jumper" :total="totalRows" />
        </el-col>
    </el-row>
    <el-dialog :title="operationLabels.dialogTitle[currentOperation]" v-model="isOutboundDialogVisible" width="70%">
        <el-tabs v-model="clientTab">
            <el-tab-pane v-for="(client, index1) in operationForm.groupedSelectedRows" :key="client.orderCId"
                :label="`客户${client.customerName} - 客户订单${client.orderCId}`" :name="client.orderCId">
                <el-tabs v-model="activeTab">
                    <el-tab-pane v-for="(group, index2) in client.orderTable" :key="group.orderId"
                        :label="`订单${group.orderRId}`" :name="group.orderId">
                        <el-form :model="group" :rules="rules" :ref="'operationForm' + index1 + '-' + index2">
                            <el-form-item prop="timestamp" :label="operationLabels.timestamp[currentOperation]"
                                required>
                                <el-date-picker v-model="group.timestamp" type="datetime" placeholder="选择日期时间"
                                    style="width: 50%" value-format="YYYY-MM-DD HH:mm:ss" :default-value="new Date()"
                                    @change="syncTimestamp(group)">
                                </el-date-picker>
                            </el-form-item>
                            <el-form-item prop="orderShoeTable" label="成品" required>
                                <el-table :data="group.orderShoeTable" style="width: 100%" border stripe>
                                    <el-table-column prop="shoeRId" label="工厂型号" />
                                    <el-table-column prop="colorName" label="颜色" />
                                    <el-table-column prop="operationQuantity" label="总数量" />
                                    <el-table-column :label="operationLabels.operationAmount[currentOperation]">
                                        <template #default="scope">
                                            <el-button type="primary"
                                                @click="openQuantityDialog(scope.row)">打开</el-button>
                                        </template>
                                    </el-table-column>
                                    <el-table-column prop="remark" label="备注">
                                        <template #default="scope">
                                            <el-input v-model="scope.row.remark" :maxlength="40" show-word-limit
                                                size="small">
                                            </el-input>
                                        </template>
                                    </el-table-column>
                                </el-table>
                            </el-form-item>
                        </el-form>
                    </el-tab-pane>
                </el-tabs>
            </el-tab-pane>
        </el-tabs>
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
export default {
    data() {
        return {
            formItemTemplate: {
                inboundDate: null,
                inboundAmount: 0,
                operationPurpose: 0,
                selectedOutsource: null,
                outsourceInfo: [],
                picker: null,
            },
            operationForm: {
                groupedSelectedRows: [],
            },
            currentPage: 1,
            pageSize: 10,
            tableData: [],
            totalRows: 0,
            orderNumberSearch: '',
            orderCIdSearch: '',
            customerNameSearch: '',
            customerBrandSearch: '',
            currentRow: {},
            rules: {
                timestamp: [
                    { required: true, message: '此项为必填项', trigger: 'change' },
                ],
                orderShoeTable: [
                    {
                        required: true,
                        validator: (rule, value, callback) => {
                            let flag = true;
                            for (let row of value) {
                                if (row.operationQuantity == 0) {
                                    flag = false;
                                    break;
                                }
                            }
                            if (!flag) {
                                callback(new Error("出库数量不能零"));
                            } else {
                                callback();
                            }
                        },
                        trigger: "change",
                    },
                ],
            },
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
            statusOptions: [
                { value: 0, label: "业务部审核" },
                { value: 1, label: "总经理审核" },
                { value: 2, label: "已批准" },
            ],
            selectedStatus: null,
            isOpenShoeSizeDialogVisible: false,
            activeStockTab: null,
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
    mounted() {
        this.getTableData()
    },
    methods: {
        async approveOutbound() {
            if (this.selectedRows.length == 0) {
                ElMessage.error("未选择订单")
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
            let groupedData = []
            let selectedRowsCopy = JSON.parse(JSON.stringify(this.selectedRows))
            for (let item of selectedRowsCopy) {
                item["timeStamp"] = new Date()
                let response = await this.getShoeSizeColumnsForOrder(row)
                let targetedStorageStock = response.data
                for (let i = 0; i < item.orderShoeTable.length; i++) {
                    let shoeSizeColumns = []
                    item.orderShoeTable[i]["operationQuantity"] = 0
                    item.orderShoeTable[i]["remark"] = ""
                    item.orderShoeTable[i]["shoesOutboundTable"] = targetedStorageStock[item.orderShoeTable[i].storageId]
                    console.log(item.orderShoeTable[i]["shoesOutboundTable"])
                    for (let j = 0; j < item.orderShoeTable[i]["shoesOutboundTable"].length; j++) {
                        let element = item.orderShoeTable[i]["shoesOutboundTable"][j]
                        item.orderShoeTable[i]["shoesOutboundTable"][j]["operationQuantity"] = element.currentQuantity
                        item.orderShoeTable[i][`amount${j}`] = element.currentQuantity
                        item.orderShoeTable[i]["operationQuantity"] += Number(element.currentQuantity)
                    }
                    item.orderShoeTable[i]["shoesOutboundTable"].forEach((element, index) => {
                        // for display
                        if (element.predictQuantity > 0) {
                            shoeSizeColumns.push({
                                "prop": `amount${index}`,
                                "label": element.shoeSizeName
                            })
                        }
                        item.orderShoeTable[i]["shoeSizeColumns"] = shoeSizeColumns
                    })
                }
                let group = groupedData.find((group) => group.orderCId == item.orderCId)
                if (group) {
                    group.orderTable.push(item)
                } else {
                    groupedData.push({
                        "orderCId": item.orderCId,
                        "customerName": item.customerName,
                        "orderTable": [item]
                    })
                }
            }
            this.operationForm.groupedSelectedRows = groupedData;
            this.clientTab = groupedData[0].orderCId
            this.activeTab = groupedData[0]["orderTable"][0].orderId
        },
        async getTableData() {
            const params = {
                "page": this.currentPage,
                "pageSize": this.pageSize,
                "orderRId": this.orderNumberSearch,
                "orderCId": this.orderCIdSearch,
                "customerName": this.customerNameSearch,
                "customerBrand": this.customerBrandSearch,
                "approvalStatus": this.selectedStatus
            }
            const response = await axios.get(`${this.$apiBaseUrl}/warehouse/getproductoverview`, { params })
            this.tableData = response.data.result
            this.totalRows = response.data.total
        },
        async submitOperationForm() {
            let isValid = true;
            try {
                for (let index1 = 0; index1 < this.operationForm.groupedSelectedRows.length; index1++) {
                    let subtable = this.operationForm.groupedSelectedRows[index1].orderTable
                    for (let index2 = 0; index2 < subtable.length; index2++) {
                        await this.$refs[`operationForm${index1}-${index2}`][0].validate();
                    }
                }
            } catch (error) {
                isValid = false;
            }

            if (isValid) {
                let data = []
                for (let customer of this.operationForm.groupedSelectedRows) {
                    for (let row of customer.orderTable) {
                        let obj = {
                            "orderId": row.orderId,
                            "timestamp": row.timestamp,
                            "items": []
                        }
                        for (let item of row.orderShoeTable) {
                            let amountList = []
                            for (let i = 0; i < item.shoesOutboundTable.length; i++) {
                                amountList.push(item[`amount${i}`])
                            }
                            let detail = {
                                "storageId": item.storageId,
                                "operationQuantity": item.operationQuantity,
                                "remark": item.remark,
                                "amountList": amountList
                            }
                            obj.items.push(detail)
                        }
                        data.push(obj)
                    }
                }
                try {
                    console.log(data)
                    await axios.patch(`${this.$apiBaseUrl}/warehouse/warehousemanager/outboundfinished`, data)
                    ElMessage.success("出库成功")
                }
                catch (error) {
                    console.log(error)
                    ElMessage.error("操作异常")
                }
                this.isOutboundDialogVisible = false
                this.getTableData()
            } else {
                console.log("Form has validation errors.");
            }
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
