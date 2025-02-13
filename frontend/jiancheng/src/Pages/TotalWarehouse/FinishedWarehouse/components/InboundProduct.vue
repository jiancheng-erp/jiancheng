<template>
    <el-row :gutter="20">
        <el-col :span="4" :offset="0" style="white-space: nowrap;">
            <el-input v-model="orderNumberSearch" placeholder="请输入订单号" clearable @keypress.enter="getTableData()"
                @clear="getTableData" />
        </el-col>
        <el-col :span="4" :offset="0" style="white-space: nowrap;">
            <el-input v-model="shoeNumberSearch" placeholder="请输入鞋型号" clearable @keypress.enter="getTableData()"
                @clear="getTableData" />
        </el-col>
        <el-col :span="4" :offset="0" style="white-space: nowrap;">
            <el-input v-model="customerNameSearch" placeholder="请输入客户号" clearable @keypress.enter="getTableData()"
                @clear="getTableData" />
        </el-col>
    </el-row>
    <el-row :gutter="20">
        <el-col :span="8" :offset="0">
            <el-button-group>
                <el-button v-if="isMultipleSelection" @click="openOperationDialog(0)">
                    入库
                </el-button>
                <el-button @click="toggleSelectionMode">
                    {{ isMultipleSelection ? "退出" : "选择鞋包入库" }}
                </el-button>
            </el-button-group>
        </el-col>
    </el-row>
    <el-row :gutter="20">
        <el-col :span="24" :offset="0">
            <el-table :data="tableData" border stripe @selection-change="handleSelectionChange">
                <el-table-column v-if="isMultipleSelection" type="selection" width="55" />
                <el-table-column prop="orderRId" label="订单号"></el-table-column>
                <el-table-column prop="shoeRId" label="工厂型号"></el-table-column>
                <el-table-column prop="customerName" label="客户名称"></el-table-column>
                <el-table-column prop="customerProductName" label="客户鞋型号"></el-table-column>
                <el-table-column prop="colorName" label="颜色"></el-table-column>
                <el-table-column prop="estimatedInboundAmount" label="计划入库数量"></el-table-column>
                <el-table-column prop="actualInboundAmount" label="实际入库数量"></el-table-column>
                <el-table-column prop="currentAmount" label="成品库存"></el-table-column>
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
    <el-dialog :title="operationLabels.dialogTitle[currentOperation]" v-model="isMultiInboundDialogVisible" width="70%">
        <el-tabs v-model="activeTab">
            <el-tab-pane v-for="(group, index) in operationForm.groupedSelectedRows" :key="group.orderShoeId"
                :label="`订单鞋型 ${group.items[0].orderRId} - ${group.items[0].shoeRId}`" :name="group.orderShoeId">
                <el-form :model="group" :rules="rules" :ref="'operationForm' + index" :key="index">
                    <el-form-item prop="timestamp" :label="operationLabels.timestamp[currentOperation]" required>
                        <el-date-picker v-model="group.timestamp" type="datetime" placeholder="选择日期时间"
                            style="width: 50%" value-format="YYYY-MM-DD HH:mm:ss" :default-value="new Date()"
                            @change="syncTimestamp(group)">
                        </el-date-picker>
                    </el-form-item>
                    <el-form-item prop="items" label="鞋包" required>
                        <el-table :data="group.items" style="width: 100%" border stripe>
                            <el-table-column prop="colorName" label="颜色" />
                            <el-table-column prop="operationQuantity" label="总数量" />
                            <el-table-column :label="operationLabels.operationAmount[currentOperation]">
                                <template #default="scope">
                                    <el-button type="primary" @click="openQuantityDialog(scope.row)">打开</el-button>
                                </template>
                            </el-table-column>
                            <el-table-column prop="remark" label="备注">
                                <template #default="scope">
                                    <el-input v-model="scope.row.remark" :maxlength="40" show-word-limit size="small">
                                    </el-input>
                                </template>
                            </el-table-column>
                        </el-table>
                    </el-form-item>
                </el-form>
            </el-tab-pane>
        </el-tabs>
        <template #footer>
            <span>
                <el-button @click="isMultiInboundDialogVisible = false">返回</el-button>
                <el-button type="primary" @click="submitOperationForm">入库</el-button>
            </span>
        </template>
    </el-dialog>

    <el-dialog title="数量输入框" v-model="isOpenQuantityDialogVisible" width="60%">
        <el-form>
            <el-form-item>
                <el-table :data="filteredData" border stripe>
                    <el-table-column prop="shoeSizeName" label="鞋码"></el-table-column>
                    <el-table-column prop="predictQuantity" label="应入库数量"></el-table-column>
                    <el-table-column prop="actualQuantity" label="实入库数量"></el-table-column>
                    <el-table-column prop="currentQuantity" label="库存"></el-table-column>
                    <el-table-column :label="operationLabels.operationAmount[currentOperation]">
                        <template #default="scope">
                            <el-input-number v-model="scope.row.operationQuantity" size="small" :min="0"
                                @change="updateTotalShoes"></el-input-number>
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
            semiInboundDialogVisible: false,
            semiOutboundDialogVisible: false,
            tableData: [],
            totalRows: 0,
            orderNumberSearch: '',
            shoeNumberSearch: '',
            customerNameSearch: '',
            currentRow: {},
            rules: {
                timestamp: [
                    { required: true, message: '此项为必填项', trigger: 'change' },
                ],
                items: [
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
                                callback(new Error("入库数量不能零"));
                            } else {
                                callback();
                            }
                        },
                        trigger: "change",
                    },
                ],
                operationPurpose: [
                    { required: true, message: '此项为必填项', trigger: 'change' },
                ],
            },
            isMultipleSelection: false,
            selectedRows: [],
            isMultiInboundDialogVisible: false,
            activeTab: null,
            currentQuantityRow: null,
            isOpenQuantityDialogVisible: false,
            // 0: inbound, 1: outbound
            currentOperation: 0,
            operationLabels: {
                "dialogTitle": ["成品入库"],
                "timestamp": ["入库日期"],
                "operationAmount": ["入库数量"],
            },
            pickerOptions: []
        }
    },
    computed: {
        filteredData() {
            return this.currentQuantityRow.shoesInboundTable.filter((row) => {
                return (
                    row.predictQuantity > 0
                );
            });
        },
    },
    mounted() {
        this.getMoldingLines()
        this.getTableData()
    },
    methods: {
        async getMoldingLines() {
            let response = await axios.get(`${this.$apiBaseUrl}/production/getmoldinglines`)
            this.pickerOptions = response.data
        },
        syncTimestamp(source_group) {
            return this.operationForm.groupedSelectedRows.map(group => {
                group.timestamp = source_group.timestamp
            })
        },
        updateTotalShoes() {
            this.currentQuantityRow.shoesInboundTable.forEach((element, index) => {
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
            this.currentOperation = operation
            this.groupSelectedRows();
            this.isMultiInboundDialogVisible = true
        },
        async groupSelectedRows() {
            let groupedData = []
            for (let item of this.selectedRows) {
                let newItem = {}
                let recordItemObj = JSON.parse(JSON.stringify(this.formItemTemplate))
                newItem = { ...item, operationQuantity: 0, remark: "", shoesInboundTable: [] };
                let shoeSizeColumns = []
                let params = { "orderId": item.orderId, "storageId": item.storageId, "storageType": 1 }
                let response = await axios.get(`${this.$apiBaseUrl}/warehouse/getshoesizecolumns`, { params })
                newItem["shoesInboundTable"] = response.data
                newItem["shoesInboundTable"].forEach(row => {
                    row.operationQuantity = 0
                })
                newItem.shoesInboundTable.forEach((element, index) => {
                    newItem[`amount${index}`] = element.operationQuantity
                })
                // insert shoe size columns into current row
                newItem.shoesInboundTable.forEach((element, index) => {
                    // for display
                    if (element.predictQuantity > 0) {
                        shoeSizeColumns.push({
                            "prop": `amount${index}`,
                            "label": element.shoeSizeName
                        })
                    }
                })
                const group = groupedData.find(g => g.orderShoeId === item.orderShoeId);
                if (group) {
                    group.items.push(newItem);
                } else {
                    groupedData.push({
                        orderId: item.orderId,
                        orderShoeId: item.orderShoeId,
                        shoeSizeColumns: shoeSizeColumns,
                        items: [newItem],
                        ...recordItemObj
                    });
                }
            }
            this.operationForm.groupedSelectedRows = groupedData;
            this.activeTab = groupedData[0].orderShoeId
            console.log(this.operationForm.groupedSelectedRows)
        },
        async getTableData() {
            const params = {
                "page": this.currentPage,
                "pageSize": this.pageSize,
                "orderRId": this.orderNumberSearch,
                "shoeRId": this.shoeNumberSearch,
                "customerName": this.customerNameSearch,
                "showAll": 1,
                "status": this.statusSearch
            }
            const response = await axios.get(`${this.$apiBaseUrl}/warehouse/warehousemanager/getfinishedinoutoverview`, { params })
            this.tableData = response.data.result
            this.totalRows = response.data.total
        },
        async submitOperationForm() {
            let isValid = true;
            const validationPromises = this.operationForm.groupedSelectedRows.map((group, index) => {
                return new Promise((resolve) => {
                    this.$refs[`operationForm${index}`][0].validate((valid) => {
                        if (!valid) {
                            isValid = false;
                        }
                        resolve();
                    });
                });
            });
            Promise.all(validationPromises).then(async () => {
                if (isValid) {
                    let data = []
                    for (let row of this.operationForm.groupedSelectedRows) {
                        let obj = {
                            "orderId": row.orderId,
                            "orderShoeId": row.orderShoeId,
                            "outsourceInfoId": row.selectedOutsource,
                            "timestamp": row.timestamp,
                            "operationPurpose": row.operationPurpose,
                            "picker": row.picker,
                            "items": []
                        }
                        for (let item of row.items) {
                            let amountList = []
                            for (let i = 0; i < item.shoesInboundTable.length; i++) {
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
                    try {
                        console.log(data)
                        await axios.patch(`${this.$apiBaseUrl}/warehouse/warehousemanager/inboundfinished`, data)
                        ElMessage.success("入库成功")
                    }
                    catch (error) {
                        console.log(error)
                        ElMessage.error("操作异常")
                    }
                    // this.semiInboundDialogVisible = false
                    this.getTableData()
                } else {
                    console.log("Form has validation errors.");
                }
            });
        },
        handleSizeChange(val) {
            this.pageSize = val
            this.getTableData()
        },
        handlePageChange(val) {
            this.currentPage = val
            this.getTableData()
        },
        finishInbound(row) {
            ElMessageBox.alert('提前完成半成品入库，是否继续？', '警告', {
                confirmButtonText: '确认',
                showCancelButton: true,
                cancelButtonText: '取消'
            }).then(async () => {
                const data = { "storageId": row.storageId }
                await axios.patch(`${this.$apiBaseUrl}/warehouse/warehousemanager/completeinboundfinished`, data)
                try {
                    ElMessage.success("操作成功")
                }
                catch (error) {
                    console.log(error)
                    ElMessage.error("操作异常")
                }
                this.getTableData()
            })
        },
    }
}
</script>
