<template>
    <el-row :gutter="20">
        <el-col :span="8" :offset="0">
            <el-button-group>
                <el-button type="primary" size="default" @click="isMaterialDialogVisible = true">搜索条件设置</el-button>
                <el-button v-if="isMultipleSelection" @click="openMultipleInboundDialog">
                入库
            </el-button>
            <el-button v-if="isMultipleSelection" @click="openFinishOutboundDialog">
                完成入库
            </el-button>
            <el-button @click="toggleSelectionMode">
                {{ isMultipleSelection ? "退出" : "选择材料" }}
            </el-button>
            </el-button-group>
        </el-col>
        <MaterialSearchDialog :visible="isMaterialDialogVisible" :materialSupplierOptions="materialSupplierOptions"
            :materialTypeOptions="materialTypeOptions" :searchForm="searchForm" @update-visible="updateDialogVisible"
            @confirm="handleSearch" />
    </el-row>
    <el-row :gutter="20">
        <el-col :span="24">
            <el-table :data="materialTableData" border stripe height="600" @sort-change="sortData"
                @selection-change="handleSelectionChange">
                <el-table-column v-if="isMultipleSelection" type="selection" width="55" :selectable="isSelectable" />
                <el-table-column prop="purchaseOrderIssueDate" label="采购订单日期" width="120"
                    sortable="custom"></el-table-column>
                <el-table-column label="采购订单号" width="100">
                    <template #default="scope">
                        <el-tooltip effect="dark" :content="scope.row.purchaseDivideOrderRId" placement="bottom">
                            <span class="truncate-text">
                                {{ scope.row.purchaseDivideOrderRId }}
                            </span>
                        </el-tooltip>
                    </template>
                </el-table-column>
                <el-table-column prop="materialType" label="材料类型"></el-table-column>
                <el-table-column prop="materialName" label="材料名称"></el-table-column>
                <el-table-column prop="materialModel" label="材料型号"></el-table-column>
                <el-table-column prop="materialSpecification" label="材料规格"></el-table-column>
                <el-table-column prop="craftName" label="复合工艺" width="120">
                    <template #default="scope">
                        <el-tooltip effect="dark" :content="scope.row.craftName" placement="bottom">
                            <span class="truncate-text">
                                {{ scope.row.craftName }}
                            </span>
                        </el-tooltip>
                    </template>
                </el-table-column>
                <el-table-column prop="colorName" label="颜色"></el-table-column>
                <el-table-column prop="materialUnit" label="材料单位"></el-table-column>
                <el-table-column prop="estimatedInboundAmount" label="材料应入库数量"
                    :formatter="formatDecimal"></el-table-column>
                <el-table-column prop="actualInboundAmount" label="材料实入库数量"
                    :formatter="formatDecimal"></el-table-column>
                <el-table-column prop="currentAmount" label="材料库存" :formatter="formatDecimal"></el-table-column>
                <el-table-column prop="unitPrice" label="材料单价" :formatter="formatDecimal"></el-table-column>
                <el-table-column prop="totalPrice" label="材料总价" :formatter="formatDecimal"></el-table-column>
                <el-table-column prop="supplierName" label="材料供应商"></el-table-column>
                <el-table-column prop="orderRId" label="材料订单号"></el-table-column>
                <el-table-column prop="shoeRId" label="材料鞋型号"></el-table-column>
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

    <!-- 新增入库对话框 -->
    <el-dialog title="多选材料入库" v-model="isMultiInboundDialogVisible" width="80%">
        <el-form :model="inboundForm" :rules="rules" ref="inboundForm">
            <el-form-item prop="date" label="入库日期">
                <el-date-picker v-model="inboundForm.date" type="datetime" placeholder="选择日期时间" style="width: 100%"
                    value-format="YYYY-MM-DD HH:mm:ss"></el-date-picker>
            </el-form-item>
            <el-form-item prop="inboundType" label="入库类型">
                <el-radio-group v-model="inboundForm.inboundType">
                    <el-radio :value="0">采购入库</el-radio>
                    <el-radio :value="1">生产剩余</el-radio>
                </el-radio-group>
            </el-form-item>
            <el-form-item prop="groupedSelectedRows" label="入库材料">
                <div v-for="(group, index) in inboundForm.groupedSelectedRows" :key="index" style="width: 100%;">
                    <el-card :header="`采购订单号: ${group.purchaseDivideOrderRId} - 供应商: ${group.supplierName}`">
                        <el-table :data="group.items" border stripe width="100%">
                            <el-table-column prop="materialName" label="材料名称"></el-table-column>
                            <el-table-column prop="materialModel" label="材料型号"></el-table-column>
                            <el-table-column prop="materialSpecification" label="材料规格"></el-table-column>
                            <el-table-column prop="colorName" label="颜色" width="80"></el-table-column>
                            <el-table-column prop="materialUnit" label="单位" width="80"></el-table-column>
                            <el-table-column prop="orderRId" label="订单号"></el-table-column>
                            <el-table-column label="入库数量" width="150">
                                <template #default="scope">
                                    <el-input-number v-if="scope.row.materialCategory == 0"
                                        v-model="scope.row.inboundQuantity" :min="0" size="small"></el-input-number>
                                    <el-button v-else type="primary"
                                        @click="openSizeMaterialQuantityDialog(scope.row)">打开</el-button>
                                </template>
                            </el-table-column>
                            <el-table-column label="单价" width="150">
                                <template #default="scope">
                                    <el-input-number v-model="scope.row.unitPrice" :min="0" :precision="2" size="small"
                                        :step="0.01"></el-input-number>
                                </template>
                            </el-table-column>
                            <el-table-column label="总价" width="100">
                                <template #default="scope">
                                    {{ scope.row.inboundQuantity * scope.row.unitPrice }}
                                </template>
                            </el-table-column>
                            <el-table-column label="备注">
                                <template #default="scope">
                                    <el-input v-model="scope.row.remark" placeholder="请输入备注" type="textarea"></el-input>
                                </template>
                            </el-table-column>
                        </el-table>
                    </el-card>
                </div>
            </el-form-item>
        </el-form>
        <template #footer>
            <el-button @click="isMultiInboundDialogVisible = false">取消</el-button>
            <el-button type="primary" @click="openReceiptDialog">入库</el-button>
        </template>
    </el-dialog>

    <el-dialog title="入库预览" v-model="isReceiptDialogVisible" width="80%">
        <div v-for="(group, index) in inboundForm.groupedSelectedRows" :key="index">
            <div :id="`inboundRecipt${index}`" style="padding:10px;background-color:#fff;">
                <el-card>
                    <h2 style="text-align: center; margin-bottom: 10px">健诚鞋业入库单</h2>
                    <el-descriptions :column="4" border>
                        <el-descriptions-item label="采购订单号">{{ group.purchaseDivideOrderRId }}</el-descriptions-item>
                        <el-descriptions-item label="供应商">{{ group.supplierName }}</el-descriptions-item>
                        <el-descriptions-item label="入库时间">{{ inboundForm.date }}</el-descriptions-item>
                        <el-descriptions-item label="入库方式">{{ inboundForm.inboundType == 0 ? "采购入库" : "生产剩余"
                            }}</el-descriptions-item>
                    </el-descriptions>
                    <el-table v-if="group.purchaseDivideOrderType == 'N'" :data="group.items" border>
                        <el-table-column prop="materialName" label="材料名称"></el-table-column>
                        <el-table-column prop="materialModel" label="材料型号"></el-table-column>
                        <el-table-column prop="materialSpecification" label="材料规格"></el-table-column>
                        <el-table-column prop="colorName" label="颜色"></el-table-column>
                        <el-table-column prop="materialUnit" label="单位"></el-table-column>
                        <el-table-column prop="orderRId" label="订单号"></el-table-column>
                        <el-table-column prop="inboundQuantity" label="入库数量">
                        </el-table-column>
                        <el-table-column prop="unitPrice" label="单价">
                        </el-table-column>
                        <el-table-column label="总价" width="100">
                            <template #default="scope">
                                {{ scope.row.inboundQuantity * scope.row.unitPrice }}
                            </template>
                        </el-table-column>
                        <el-table-column prop="remark" label="备注">
                        </el-table-column>
                    </el-table>
                    <el-table v-else :data="group.items" border>
                        <el-table-column prop="materialName" label="材料名称"></el-table-column>
                        <el-table-column prop="materialModel" label="材料型号"></el-table-column>
                        <el-table-column prop="materialSpecification" label="材料规格"></el-table-column>
                        <el-table-column prop="colorName" label="颜色"></el-table-column>
                        <el-table-column prop="materialUnit" label="单位"></el-table-column>
                        <el-table-column prop="orderRId" label="订单号"></el-table-column>
                        <el-table-column :label="`分码数量`" header-align="center">
                            <el-table-column v-for="column in group.shoeSizeColumns" :key="column.prop"
                                :prop="column.prop" :label="column.label" width="55">
                            </el-table-column>
                        </el-table-column>
                        <el-table-column prop="unitPrice" label="单价">
                        </el-table-column>
                        <el-table-column label="总价" width="100">
                            <template #default="scope">
                                {{ scope.row.inboundQuantity * scope.row.unitPrice }}
                            </template>
                        </el-table-column>
                        <el-table-column prop="remark" label="备注">
                        </el-table-column>
                    </el-table>
                </el-card>
            </div>
        </div>
        <template #footer>
            <el-button @click="goBackToInboundDialog">返回</el-button>
            <el-button type="primary" @click="submitInboundForm">确认入库</el-button>
        </template>
    </el-dialog>

    <el-dialog title="多鞋码入库对话框" v-model="isOpenSizeMaterialQuantityDialogVisible" width="50%">
        <el-table :data="filteredData" border stripe>
            <el-table-column prop="shoeSizeName" label="鞋码" width="100"></el-table-column>
            <el-table-column prop="predictQuantity" label="预计数量"></el-table-column>
            <el-table-column prop="actualQuantity" label="实际数量"></el-table-column>
            <el-table-column prop="currentQuantity" label="库存"></el-table-column>
            <el-table-column prop="inboundQuantity" label="入库数量">
                <template #default="scope">
                    <el-input-number v-model="scope.row.inboundQuantity" size="small" :min="0"
                        @change="updateSizeMaterialTotal"></el-input-number>
                </template>
            </el-table-column>
        </el-table>
        <template #footer>
            <span>
                <el-button @click="confirmSizeMaterialQuantity">确定</el-button>
            </span>
        </template>
    </el-dialog>

    <el-dialog title="推进入库流程" v-model="isFinishInboundDialogOpen" width="50%">
        <el-descriptions title="已选择订单鞋型" style="margin-top: 20px;">
        </el-descriptions>
        <el-table :data="selectedRows" border stripe>
            <el-table-column prop="orderRId" label="订单号">
            </el-table-column>
            <el-table-column prop="shoeRId" label="鞋型号">
            </el-table-column>
            <el-table-column prop="materialName" label="材料名称">
            </el-table-column>
            <el-table-column prop="materialModel" label="材料型号">
            </el-table-column>
            <el-table-column prop="materialSpecification" label="材料规格">
            </el-table-column>
            <el-table-column prop="colorName" label="颜色">
            </el-table-column>
            <el-table-column prop="supplierName" label="厂家名称">
            </el-table-column>
        </el-table>
        <template #footer>
            <el-button @click="isFinishInboundDialogOpen = false">返回</el-button>
            <el-button @click="finishInbound">完成入库</el-button>
        </template>
    </el-dialog>
</template>
<script>
import axios from 'axios';
import { ElMessage, ElMessageBox } from 'element-plus';
import MaterialSearchDialog from './MaterialSearchDialog.vue';
import { getShoeSizesName } from '@/Pages/utils/getShoeSizesName';
export default {
    components: {
        MaterialSearchDialog,
    },
    data() {
        return {
            isMultiInboundDialogVisible: false,
            searchForm: {
                orderNumberSearch: '',
                shoeNumberSearch: '',
                materialTypeSearch: '',
                materialNameSearch: '',
                materialModelSearch: '',
                materialSpecificationSearch: '',
                materialSupplierSearch: '',
                purchaseDivideOrderRIdSearch: "",
            },
            materialTypeOptions: [],
            materialSupplierOptions: [],
            isMaterialDialogVisible: false,
            pageSize: 10,
            currentPage: 1,
            inboundFormTemplate: {
                date: '',
                inboundType: null,
                // contains inboundQuantity, unitPrice, remark, sizeMaterialInboundTable
                groupedSelectedRows: [],
            },
            inboundForm: {},
            materialTableData: [],
            currentRow: {},
            totalRows: 0,
            isMultipleSelection: false,
            selectedRows: [],
            isFinishInboundDialogOpen: false,
            isReceiptDialogVisible: false,
            rules: {
                date: [
                    { required: true, message: '此项为必填项', trigger: 'change' },
                ],
                inboundType: [
                    { required: true, message: '此项为必填项', trigger: 'change' },
                ],
                groupedSelectedRows: [
                    {
                        required: true,
                        validator: (rule, value, callback) => {
                            value.forEach(group => {
                                group.items.forEach(row => {
                                    if (row.inboundQuantity == 0) {
                                        callback(new Error("入库数量不能零"));
                                    } else {
                                        callback();
                                    }
                                });
                            });
                        },
                        trigger: "change",
                    },
                ],
            },
            isOpenSizeMaterialQuantityDialogVisible: false,
            currentSizeMaterialQuantityRow: {},
            getShoeSizesName
        }
    },
    mounted() {
        this.getAllMaterialTypes()
        this.getAllSuppliers()
        this.getMaterialTableData()
    },
    computed: {
        filteredData() {
            return this.currentSizeMaterialQuantityRow.sizeMaterialInboundTable.filter((row) => {
                return (
                    row.predictQuantity > 0
                );
            });
        },
    },
    methods: {
        goBackToInboundDialog() {
            this.isReceiptDialogVisible = false
            this.isMultiInboundDialogVisible = true
        },
        confirmSizeMaterialQuantity() {
            this.isOpenSizeMaterialQuantityDialogVisible = false
        },
        updateSizeMaterialTotal() {
            this.currentSizeMaterialQuantityRow.sizeMaterialInboundTable.forEach((element, index) => {
                this.currentSizeMaterialQuantityRow[`amount${index}`] = element.inboundQuantity
            })
            this.currentSizeMaterialQuantityRow.inboundQuantity = this.filteredData.reduce((acc, row) => {
                return acc + row.inboundQuantity;
            }, 0);
        },
        openSizeMaterialQuantityDialog(row) {
            this.currentSizeMaterialQuantityRow = row
            this.isOpenSizeMaterialQuantityDialogVisible = true
        },
        openMultipleInboundDialog() {
            if (this.selectedRows.length == 0) {
                ElMessage.error("未选择材料")
                return
            }
            this.isMultiInboundDialogVisible = true
        },
        updateDialogVisible(newVal) {
            this.isMaterialDialogVisible = newVal

        },
        handleSearch(values) {
            this.searchForm = { ...values }
            this.getMaterialTableData()
        },
        isSelectable(row) {
            return row.status === "未完成入库"
        },
        handleSelectionChange(selection) {
            this.selectedRows = selection;
            this.groupSelectedRows();
        },
        async groupSelectedRows() {
            let groupedData = []
            for (let item of this.selectedRows) {
                let newItem = {}
                newItem = { ...item, inboundQuantity: 0, unitPrice: Number(item.unitPrice), remark: "", sizeMaterialInboundTable: [] };
                let shoeSizeColumns = []
                if (item.materialCategory == 1) {
                    let params = { "sizeMaterialStorageId": item.materialStorageId, "orderId": item.orderId, "purchaseDivideOrderId": item.purchaseDivideOrderId }
                    let response = await axios.get(`${this.$apiBaseUrl}/warehouse/warehousemanager/getsizematerialbyid`, { params })
                    newItem["sizeMaterialInboundTable"] = response.data
                    newItem["sizeMaterialInboundTable"].forEach(row => {
                        row.inboundQuantity = 0
                    })
                    newItem.sizeMaterialInboundTable.forEach((element, index) => {
                        newItem[`amount${index}`] = element.inboundQuantity
                    })
                    // insert shoe size columns into current row
                    newItem.sizeMaterialInboundTable.forEach((element, index) => {
                        // for display
                        if (element.predictQuantity > 0) {
                            shoeSizeColumns.push({
                                "prop": `amount${index}`,
                                "label": element.shoeSizeName
                            })
                        }
                    })
                }
                const group = groupedData.find(g => g.purchaseDivideOrderRId === item.purchaseDivideOrderRId);
                if (group) {
                    group.items.push(newItem);
                } else {
                    groupedData.push({
                        purchaseDivideOrderRId: item.purchaseDivideOrderRId,
                        supplierName: item.supplierName,
                        purchaseDivideOrderType: item.purchaseDivideOrderType,
                        shoeSizeColumns: shoeSizeColumns,
                        items: [newItem]
                    });
                }
            }
            this.inboundForm.groupedSelectedRows = groupedData;
            console.log(this.inboundForm.groupedSelectedRows)
        },
        openFinishOutboundDialog() {
            if (this.selectedRows.length == 0) {
                ElMessage.error("未选择材料")
                return
            }
            this.isFinishInboundDialogOpen = true
        },
        toggleSelectionMode() {
            this.isMultipleSelection = !this.isMultipleSelection;
        },
        async getAllMaterialTypes() {
            const response = await axios.get(`${this.$apiBaseUrl}/warehouse/warehousemanager/getallmaterialtypes`)
            this.materialTypeOptions = response.data
        },
        async getAllSuppliers() {
            const response = await axios.get(`${this.$apiBaseUrl}/warehouse/warehousemanager/getallsuppliernames`)
            this.materialSupplierOptions = response.data
        },
        async getMaterialTableData(sortColumn, sortOrder) {
            const params = {
                "page": this.currentPage,
                "pageSize": this.pageSize,
                "opType": 1,
                "materialType": this.searchForm.materialTypeSearch,
                "materialName": this.searchForm.materialNameSearch,
                "materialModel": this.searchForm.materialModelSearch,
                "materialSpec": this.searchForm.materialSpecificationSearch,
                "supplier": this.searchForm.materialSupplierSearch,
                "orderRId": this.searchForm.orderNumberSearch,
                "shoeRId": this.searchForm.shoeNumberSearch,
                "purchaseDivideOrderRId": this.searchForm.purchaseDivideOrderRIdSearch,
                "sortColumn": sortColumn,
                "sortOrder": sortOrder
            }
            const response = await axios.get(`${this.$apiBaseUrl}/warehouse/warehousemanager/getallmaterialinfo`, { params })
            this.materialTableData = response.data.result
            this.totalRows = response.data.total
        },
        openReceiptDialog() {
            this.$refs.inboundForm.validate(async (valid) => {
                if (valid) {
                    this.isMultiInboundDialogVisible = false;
                    this.isReceiptDialogVisible = true;
                }
                else {
                    console.log("validation error")
                }
            })

        },
        async submitInboundForm() {
            try {
                console.log(this.selectedRows)
                console.log(this.inboundForm.groupedSelectedRows)
                let data = []
                for (let row of this.inboundForm.groupedSelectedRows) {
                    let obj = {
                        inboundTimestamp: this.inboundForm.date,
                        inboundType: this.inboundForm.inboundType,
                        items: []
                    }
                    for (let item of row.items) {
                        let detail = {
                            materialStorageId: item.materialStorageId,
                            inboundQuantity: item.inboundQuantity,
                            unitPrice: item.unitPrice,
                            materialCategory: item.materialCategory,
                            remark: item.remark,
                            materialCategory: item.materialCategory,
                        }
                        for (let i = 0; i < item.sizeMaterialInboundTable.length; i++) {
                            detail[`amount${i}`] = item[`amount${i}`]
                        }
                        obj.items.push(detail)
                    }
                    data.push(obj)
                }
                console.log(data)
                await axios.patch(`${this.$apiBaseUrl}/warehouse/warehousemanager/inboundmaterial`, data);
                ElMessage.success("入库成功");
                this.getMaterialTableData()
                this.isReceiptDialogVisible = false;
            } catch (error) {
                ElMessage.error("入库失败");
            }
        },
        handleSizeChange(val) {
            this.pageSize = val
            this.getMaterialTableData()
        },
        handlePageChange(val) {
            this.currentPage = val
            this.getMaterialTableData()
        },

        formatDecimal(row, column, cellValue, index) {
            return Number(cellValue).toFixed(2)
        },
        async finishInbound() {
            ElMessageBox.alert('完成入库后材料将从待入库页面移除。你仍可在仓库页面进行入库。', '警告', {
                confirmButtonText: '确认',
                showCancelButton: true,
                cancelButtonText: '取消'
            }).then(async () => {
                try {
                    let data = []
                    this.selectedRows.forEach(row => {
                        data.push({ "orderId": row.orderId, "storageId": row.materialStorageId, "materialCategory": row.materialCategory })
                    })
                    await axios.patch(`${this.$apiBaseUrl}/warehouse/warehousemanager/finishinboundmaterial`, data)
                    ElMessage.success("操作成功")
                }
                catch (error) {
                    console.log(error)
                    ElMessage.error("操作异常")
                }
                this.getMaterialTableData()
                this.isFinishInboundDialogOpen = false
            })
        },
        async sortData({ prop, order }) {
            await this.getMaterialTableData(prop, order)
        }
    }
}
</script>
