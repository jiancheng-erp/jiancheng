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
                <el-button v-if="isMultipleSelection" @click="openOperationDialog">
                    入库
                </el-button>
                <el-button type="primary" @click="toggleSelectionMode">
                    {{ isMultipleSelection ? "退出" : "选择鞋包入库" }}
                </el-button>
            </el-button-group>
        </el-col>
    </el-row>
    <el-row :gutter="20">
        <el-col :span="24" :offset="0">
            <el-table :data="tableData" border stripe @selection-change="handleSelectionChange" height="500">
                <el-table-column v-if="isMultipleSelection" type="selection" width="55" />
                <el-table-column prop="orderRId" label="订单号"></el-table-column>
                <el-table-column prop="shoeRId" label="工厂型号"></el-table-column>
                <el-table-column prop="customerName" label="客户号"></el-table-column>
                <el-table-column prop="customerProductName" label="客户型号"></el-table-column>
                <el-table-column prop="colorName" label="颜色"></el-table-column>
                <el-table-column prop="estimatedInboundAmount" label="计划入库数量"></el-table-column>
                <el-table-column prop="actualInboundAmount" label="实际入库数量"></el-table-column>
                <el-table-column prop="currentAmount" label="半成品库存"></el-table-column>
            </el-table>
        </el-col>
    </el-row>
    <el-row :gutter="20">
        <el-col>
            <el-pagination @size-change="handleSizeChange" @current-change="handlePageChange"
                :current-page="currentPage" :page-size="pageSize" layout="total, sizes, prev, pager, next, jumper"
                :total="totalRows" />
        </el-col>
    </el-row>
    <el-dialog :title="operationLabels.dialogTitle" v-model="isMultiInboundDialogVisible" width="70%"
        destroy-on-close>
        <el-form>
            <el-form-item prop="operationPurpose" label="入库类型">
                <el-radio-group v-model="inboundForm.operationPurpose">
                    <el-radio :value="0">自产</el-radio>
                    <el-radio :value="1">外包</el-radio>
                </el-radio-group>
            </el-form-item>
            <el-form-item prop="remark" label="备注">
                <el-input v-model="inboundForm.remark" type="textarea" show-word-limit :maxlength="commentLength"></el-input>
            </el-form-item>
            <el-form-item v-if="inboundForm.operationPurpose == 1" label="外包信息">
                <el-table :data="inboundForm.outsourceInfo" style="width: 100%" border stripe>
                    <el-table-column width="55">
                        <template #default="scope">
                            <el-radio v-model="inboundForm.selectedOutsource" :value="scope.row.outsourceInfoId" />
                        </template>
                    </el-table-column>
                    <el-table-column prop="outsourceFactory.value" label="工厂名称" />
                    <el-table-column prop="outsourceAmount" label="外包数量" />
                    <el-table-column prop="outsourceType" label="外包类型" />
                    <el-table-column label="操作">
                        <template #default="scope">
                            <el-button :disabled="inboundForm.selectedOutsource !== scope.row.outsourceInfoId"
                                type="warning" size="small" @click="finishOutsourceInbound(scope.row)">
                                完成外包入库
                            </el-button>
                        </template>
                    </el-table-column>
                </el-table>
            </el-form-item>
        </el-form>
        <el-tabs v-model="activeTab">
            <el-tab-pane v-for="(group, index) in inboundForm.orderShoeItems" :key="group.orderShoeId"
                :label="`订单鞋型 ${group.items[0].orderRId} - ${group.items[0].shoeRId}`" :name="group.orderShoeId">
                <el-table :data="group.items" style="width: 100%" border stripe>
                    <el-table-column prop="colorName" label="颜色" />
                    <el-table-column prop="operationQuantity" label="总数量" />
                    <el-table-column :label="operationLabels.operationAmount">
                        <template #default="scope">
                            <el-button type="primary" @click="openQuantityDialog(scope.row)">打开</el-button>
                        </template>
                    </el-table-column>
                    <el-table-column prop="remark" label="备注">
                        <template #default="scope">
                            <el-input v-model="scope.row.remark" :maxlength="commentLength" show-word-limit>
                            </el-input>
                        </template>
                    </el-table-column>
                </el-table>
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
                    <el-table-column :label="operationLabels.operationAmount">
                        <template #default="scope">
                            <el-input-number v-model="scope.row.operationQuantity"
                                size="small" :min="0" @change="updateSemiShoeTotal"></el-input-number>
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
import * as constants from '@/Pages/utils/constants'
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
                orderShoeItems: [],
                remark: null,
            },
            inboundForm: {},
            currentPage: 1,
            pageSize: 10,
            tableData: [],
            totalRows: 0,
            orderNumberSearch: '',
            shoeNumberSearch: '',
            customerNameSearch: '',
            currentRow: {},
            rules: {
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
            operationLabels: {
                "dialogTitle": "鞋包入库",
                "timestamp": "入库日期",
                "operationAmount": "入库数量",
            },
            commentLength: constants.BOUND_RECORD_COMMENT_LENGTH,
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
        this.getTableData()
    },
    methods: {
        updateSemiShoeTotal() {
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
        openOperationDialog() {
            if (this.selectedRows.length == 0) {
                ElMessage.error("未选择材料")
                return
            }
            this.groupSelectedRows();
            this.isMultiInboundDialogVisible = true
        },
        async groupSelectedRows() {
            let groupedData = []
            this.inboundForm = JSON.parse(JSON.stringify(this.formItemTemplate))
            for (let item of this.selectedRows) {
                let newItem = {}
                newItem = { ...item, operationQuantity: 0, remark: "", shoesInboundTable: [] };
                let shoeSizeColumns = []
                for (let i = 0; i < item.shoeSizeColumns.length; i++) {
                    let column = item.shoeSizeColumns[i];
                    if (column === '') {
                        break
                    }
                    newItem.shoesInboundTable.push({
                        "shoeSizeName": column,
                        "predictQuantity": item[`size${i + 34}EstimatedAmount`],
                        "actualQuantity": item[`size${i + 34}ActualAmount`],
                        "currentQuantity": item[`size${i + 34}Amount`],
                        "operationQuantity": item[`size${i + 34}EstimatedAmount`] - item[`size${i + 34}ActualAmount`]
                    });
                }
                newItem.shoesInboundTable.forEach((element, index) => {
                    newItem[`amount${index}`] = element.operationQuantity
                    newItem.operationQuantity += element.operationQuantity
                })
                const group = groupedData.find(g => g.orderShoeId === item.orderShoeId);
                if (group) {
                    group.items.push(newItem);
                } else {
                    groupedData.push({
                        orderShoeId: item.orderShoeId,
                        items: [newItem],
                    });
                }
            }
            this.inboundForm.orderShoeItems = groupedData
            this.activeTab = groupedData[0].orderShoeId
        },
        async getTableData() {
            const params = {
                "page": this.currentPage,
                "pageSize": this.pageSize,
                "orderRId": this.orderNumberSearch,
                "shoeRId": this.shoeNumberSearch,
                "customerName": this.customerNameSearch,
                "showAll": 0,
                "status": this.statusSearch
            }
            const response = await axios.get(`${this.$apiBaseUrl}/warehouse/getsemifinishedstorages`, { params })
            this.tableData = response.data.result
            this.totalRows = response.data.total
        },
        async submitOperationForm() {
            console.log(this.inboundForm)
            let data = {
                "operationPurpose": this.inboundForm.operationPurpose,
                "selectedOutsource": this.inboundForm.selectedOutsource,
                "remark": this.inboundForm.remark,
                "items": [],
            }
            for (let orderShoeItem of this.inboundForm.orderShoeItems) {
                for (let item of orderShoeItem.items) {
                    let obj = {
                        "storageId": item.storageId,
                        "operationQuantity": item.operationQuantity,
                        "remark": item.remark,
                    }
                    let amountList = []
                    for (let i = 0; i < item.shoesInboundTable.length; i++) {
                        amountList.push(item[`amount${i}`])
                    }
                    obj["amountList"] = amountList
                    data.items.push(obj)
                }
            }
            try {
                console.log(data)
                await axios.patch(`${this.$apiBaseUrl}/warehouse/warehousemanager/inboundsemifinished`, data)
                ElMessage.success("入库成功")
            }
            catch (error) {
                console.log(error)
                ElMessage.error("操作异常")
            }
            this.isMultiInboundDialogVisible = false
            this.getTableData()
        },
        async finishOutsourceInbound(row) {
            try {
                let data = { "outsourceInfoId": row.outsourceInfoId }
                await axios.patch(`${this.$apiBaseUrl}/warehouse/warehousemanager/finishoutsourceinbound`, data)
                ElMessage.success("外包入库成功")
                this.getOutsourceInfoForInbound()
            }
            catch (error) {
                console.log(error)
                ElMessage.error("外包入库失败")
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
        async getOutsourceInfoForInbound() {
            let params = { "orderShoeId": this.currentRow.orderShoeId }
            let response = await axios.get(`${this.$apiBaseUrl}/production/productionmanager/getordershoeoutsourceinfo`, { params })
            this.inboundForm.outsourceInfo = []
            response.data.forEach(element => {
                let length = element.outsourceType.length
                if (element.outsourceStatus == 5 || element.outsourceStatus == 6) {
                    if ((this.currentRow.object === '裁片' && element.outsourceType[length - 1] === '裁断') || (this.currentRow.object === '鞋包' && element.outsourceType[length - 1] === '针车')) {
                        this.inboundForm.outsourceInfo.push(element)
                    }
                }
            });
            if (this.inboundForm.outsourceInfo.length > 0) {
                this.inboundForm.selectedOutsource = this.inboundForm.outsourceInfo[0].outsourceInfoId
            }
        },
        finishInbound(row) {
            ElMessageBox.alert('提前完成半成品入库，是否继续？', '警告', {
                confirmButtonText: '确认',
                showCancelButton: true,
                cancelButtonText: '取消'
            }).then(async () => {
                const data = { "storageId": row.storageId }
                await axios.patch(`${this.$apiBaseUrl}/warehouse/warehousemanager/finishinboundsemifinished`, data)
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
