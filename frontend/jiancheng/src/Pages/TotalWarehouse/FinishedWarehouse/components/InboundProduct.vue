<template>
    <el-row :gutter="20">
        <el-col>
            <el-input v-model="orderNumberSearch" placeholder="订单号筛选" clearable @change="getTableData()" style="width: 200px; margin-right: 10px;"
                @clear="getTableData" />
            <el-input v-model="shoeNumberSearch" placeholder="鞋型号筛选" clearable @change="getTableData()" style="width: 200px; margin-right: 10px;"
                @clear="getTableData" />
            <el-input v-model="customerNameSearch" placeholder="客户号筛选" clearable @change="getTableData()" style="width: 200px; margin-right: 10px;"
                @clear="getTableData" />
            <el-input v-model="customerProductNameSearch" placeholder="客户鞋型筛选" clearable @change="getTableData()" style="width: 200px; margin-right: 10px;"
                @clear="getTableData" />
            <span style="color: red">成品总欠数: {{ this.totalRemainingAmount }}</span>
        </el-col>
    </el-row>
    <el-row :gutter="20">
        <el-col :span="8" :offset="0">
            <el-button-group>
                <el-button v-if="isMultipleSelection" @click="openOperationDialog">
                    入库
                </el-button>
                <el-button type="primary" @click="toggleSelectionMode">
                    {{ isMultipleSelection ? "退出" : "选择成品入库" }}
                </el-button>
            </el-button-group>
        </el-col>
    </el-row>
    <el-row :gutter="20">
        <el-col :span="24" :offset="0">
            <el-table :data="tableData" border stripe @selection-change="handleSelectionChange" height="500" :cell-style="getCellStyle">
                <el-table-column v-if="isMultipleSelection" type="selection" width="55" />
                <el-table-column prop="orderRId" label="订单号"></el-table-column>
                <el-table-column prop="shoeRId" label="工厂型号"></el-table-column>
                <el-table-column prop="customerName" label="客户号"></el-table-column>
                <el-table-column prop="customerProductName" label="客户鞋型"></el-table-column>
                <el-table-column prop="colorName" label="颜色"></el-table-column>
                <el-table-column prop="estimatedInboundAmount" label="计划入库数量"></el-table-column>
                <el-table-column prop="actualInboundAmount" label="实际入库数量"></el-table-column>
                <el-table-column prop="currentAmount" label="成品库存"></el-table-column>
                <el-table-column prop="remainingAmount" label="欠数"></el-table-column>
            </el-table>
        </el-col>
    </el-row>
    <el-row :gutter="20">
        <el-col>
            <el-pagination @size-change="handleSizeChange" @current-change="handlePageChange"
                :current-page="currentPage" :page-size="pageSize" layout="total, sizes, prev, pager, next, jumper"
                :total="totalRows" :page-sizes="pageSizes"/>
        </el-col>
    </el-row>
    <el-dialog :title="operationLabels.dialogTitle" v-model="isMultiInboundDialogVisible" width="70%"
        destroy-on-close>
        <el-form>
            <el-form-item prop="remark" label="备注">
                <el-input v-model="inboundForm.remark" type="textarea" show-word-limit :maxlength="commentLength"></el-input>
            </el-form-item>
        </el-form>
        <el-tabs v-model="activeTab">
            <el-tab-pane v-for="(group, index) in inboundForm.orderShoeItems" :key="group.orderShoeId"
                :label="`订单鞋型 ${group.items[0].orderRId} - ${group.items[0].shoeRId}`" :name="group.orderShoeId">
                <el-table :data="group.items" style="width: 100%" border stripe>
                    <el-table-column prop="colorName" label="颜色" />
                    <el-table-column prop="operationQuantity" label="待入库数量" />
                    <el-table-column :label="operationLabels.operationAmount">
                        <template #default="scope">
                            <el-input-number v-model="scope.row.inboundQuantity" :min="0"></el-input-number>
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
import { PAGESIZE, PAGESIZES } from '../../warehouseUtils';
export default {
    data() {
        return {
            formItemTemplate: {
                inboundAmount: 0,
                outsourceInfo: [],
                orderShoeItems: [],
                remark: null,
            },
            inboundForm: {},
            currentPage: 1,
            pageSize: PAGESIZE,
            pageSizes: PAGESIZES,
            tableData: [],
            totalRows: 0,
            orderNumberSearch: '',
            shoeNumberSearch: '',
            customerNameSearch: '',
            customerProductNameSearch: '',
            currentRow: {},
            isMultipleSelection: false,
            selectedRows: [],
            isMultiInboundDialogVisible: false,
            activeTab: null,
            currentQuantityRow: null,
            isOpenQuantityDialogVisible: false,
            operationLabels: {
                "dialogTitle": "成品入库",
                "timestamp": "入库日期",
                "operationAmount": "入库数量",
            },
            commentLength: constants.BOUND_RECORD_COMMENT_LENGTH,
            totalRemainingAmount: 0,
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
        getCellStyle({ row, column, rowIndex, columnIndex }) {
            if (column.property === 'remainingAmount') {
                return { color: 'red' }
            }
            return {}
        },
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
                newItem.operationQuantity = item.estimatedInboundAmount - item.actualInboundAmount
                newItem.inboundQuantity = newItem.operationQuantity
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
                "customerProductName": this.customerProductNameSearch,
                "showAll": 0,
                "status": this.statusSearch
            }
            const response = await axios.get(`${this.$apiBaseUrl}/warehouse/getfinishedstorages`, { params })
            this.tableData = response.data.result
            this.totalRows = response.data.total

            const response2 = await axios.get(`${this.$apiBaseUrl}/warehouse/getremainingamountoffinishedstorage`, { params })
            this.totalRemainingAmount = response2.data.remainingAmount
        },
        async submitOperationForm() {
            console.log(this.inboundForm)
            let data = {
                "remark": this.inboundForm.remark,
                "items": [],
            }
            for (let orderShoeItem of this.inboundForm.orderShoeItems) {
                for (let item of orderShoeItem.items) {
                    let obj = {
                        "storageId": item.storageId,
                        "inboundQuantity": item.inboundQuantity,
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
                await axios.patch(`${this.$apiBaseUrl}/warehouse/inboundfinished`, data)
                ElMessage.success("入库成功")
            }
            catch (error) {
                console.log(error)
                ElMessage.error("操作异常")
            }
            this.isMultiInboundDialogVisible = false
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
        finishInbound(row) {
            ElMessageBox.alert('提前完成半成品入库，是否继续？', '警告', {
                confirmButtonText: '确认',
                showCancelButton: true,
                cancelButtonText: '取消'
            }).then(async () => {
                const data = { "storageId": row.storageId }
                await axios.patch(`${this.$apiBaseUrl}/warehouse/warehousemanager/finishinboundfinished`, data)
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
