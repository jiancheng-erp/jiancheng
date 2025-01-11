<template>
    <el-row :gutter="20">
        <el-col :span="6" :offset="0">
            <el-button-group>
                <el-button type="primary" size="default" @click="openSearchDialog">搜索条件设置</el-button>
            </el-button-group>
        </el-col>
        <MaterialSearchDialog :visible="isMaterialDialogVisible" :materialSupplierOptions="materialSupplierOptions"
            :materialTypeOptions="materialTypeOptions" :searchForm="searchForm" @update-visible="updateDialogVisible"
            @confirm="handleSearch" />
    </el-row>
    <el-row :gutter="20">
        <el-col :span="24">
            <el-button v-if="isMultipleSelection" @click="openInboundDialog">
                入库
            </el-button>
            <el-button v-if="isMultipleSelection" @click="openFinishInboundDialog">
                完成入库
            </el-button>
            <el-button @click="toggleSelectionMode">
                {{ isMultipleSelection ? "退出" : "选择材料" }}
            </el-button>
        </el-col>
    </el-row>
    <el-row :gutter="20">
        <el-col :span="24">
            <el-table :data="materialTableData" border stripe height="600" @sort-change="sortData"
                @selection-change="handleSelectionChange">
                <el-table-column v-if="isMultipleSelection" type="selection" width="55" :selectable="isSelectable" />
                <el-table-column prop="materialName" label="材料名称"></el-table-column>
                <el-table-column prop="materialModel" label="材料型号"></el-table-column>
                <el-table-column prop="materialSpecification" label="材料规格"></el-table-column>
                <el-table-column prop="colorName" label="颜色"></el-table-column>
                <el-table-column prop="materialUnit" label="材料单位"></el-table-column>
                <el-table-column prop="estimatedInboundAmount" label="材料应入库数量"
                    :formatter="formatDecimal"></el-table-column>
                <el-table-column prop="actualInboundAmount" label="材料实入库数量"
                    :formatter="formatDecimal"></el-table-column>
                <el-table-column prop="currentAmount" label="材料库存" :formatter="formatDecimal"></el-table-column>
                <el-table-column prop="compositeUnitCost" label="加工单价" :formatter="formatDecimal"></el-table-column>
                <el-table-column prop="compositeTotalPrice" label="加工总价" :formatter="formatDecimal"></el-table-column>
                <el-table-column prop="supplierName" label="复合供应商"></el-table-column>
                <el-table-column prop="orderRId" label="材料订单号"></el-table-column>
                <el-table-column prop="shoeRId" label="材料鞋型号"></el-table-column>
                <el-table-column prop="status" label="状态"></el-table-column>
                <el-table-column fixed="right" label="操作" width="80">
                    <template #default="scope">
                        <el-button-group>
                            <el-button type="primary" size="small" @click="editMaterial(scope.row)">入库</el-button>
                        </el-button-group>
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

    <el-dialog title="入库对话框" v-model="isInboundDialogVisible" width="80%">
        <el-form :model="inboundForm" :rules="rules" ref="inboundForm">
            <el-form-item prop="date" label="入库日期">
                <el-date-picker v-model="inboundForm.date" type="datetime" placeholder="选择日期时间" style="width: 100%"
                    value-format="YYYY-MM-DD HH:mm:ss"></el-date-picker>
            </el-form-item>
            <el-form-item prop="inboundType" label="入库类型">
                <el-radio-group v-model="inboundForm.inboundType">
                    <el-radio :value="2">复合入库</el-radio>
                </el-radio-group>
            </el-form-item>
            <el-form-item prop="groupedSelectedRows" label="入库材料">
                <div v-for="(group, index) in inboundForm.groupedSelectedRows" :key="index" style="width: 100%;">
                    <el-card :header="`供应商: ${group.supplierName}`">
                        <el-table :data="group.items" border stripe width="100%">
                            <el-table-column prop="materialName" label="材料名称"></el-table-column>
                            <el-table-column prop="materialModel" label="材料型号"></el-table-column>
                            <el-table-column prop="materialSpecification" label="材料规格"></el-table-column>
                            <el-table-column prop="colorName" label="颜色" width="80"></el-table-column>
                            <el-table-column prop="materialUnit" label="单位" width="80"></el-table-column>
                            <el-table-column prop="orderRId" label="订单号"></el-table-column>
                            <el-table-column prop="shoeRId" label="工厂型号"></el-table-column>
                            <el-table-column label="入库数量" width="150">
                                <template #default="scope">
                                    <el-input-number v-model="scope.row.inboundQuantity" :min="0" size="small">
                                    </el-input-number>
                                </template>
                            </el-table-column>
                            <el-table-column label="复合单价" width="150">
                                <template #default="scope">
                                    <el-input-number v-model="scope.row.compositeUnitCost" :min="0" :precision="2"
                                        size="small" :step="0.01"></el-input-number>
                                </template>
                            </el-table-column>
                            <el-table-column label="总价" width="100">
                                <template #default="scope">
                                    {{ scope.row.inboundQuantity * scope.row.compositeUnitCost }}
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
            <span>
                <el-button @click="isInboundDialogVisible = false">取消</el-button>
                <el-button type="primary" @click="openReceiptDialog">入库</el-button>
            </span>
        </template>
    </el-dialog>

    <el-dialog title="入库预览" v-model="isReceiptDialogVisible" width="80%">
        <div v-for="(group, index) in inboundForm.groupedSelectedRows" :key="index">
            <div :id="`inboundRecipt${index}`" style="padding:10px;background-color:#fff;">
                <el-card>
                    <h2 style="text-align: center; margin-bottom: 10px">健诚鞋业入库单</h2>
                    <el-descriptions :column="4" border>
                        <el-descriptions-item label="供应商">{{ group.supplierName }}</el-descriptions-item>
                        <el-descriptions-item label="入库时间">{{ inboundForm.date }}</el-descriptions-item>
                        <el-descriptions-item label="入库方式">复合入库</el-descriptions-item>
                    </el-descriptions>
                    <el-table :data="group.items" border>
                        <el-table-column prop="materialName" label="材料名称"></el-table-column>
                        <el-table-column prop="materialModel" label="材料型号"></el-table-column>
                        <el-table-column prop="materialSpecification" label="材料规格"></el-table-column>
                        <el-table-column prop="colorName" label="颜色"></el-table-column>
                        <el-table-column prop="materialUnit" label="单位"></el-table-column>
                        <el-table-column prop="orderRId" label="订单号"></el-table-column>
                        <el-table-column prop="inboundQuantity" label="入库数量">
                        </el-table-column>
                        <el-table-column prop="compositeUnitCost" label="复合单价">
                        </el-table-column>
                        <el-table-column label="总价" width="100">
                            <template #default="scope">
                                {{ scope.row.inboundQuantity * scope.row.compositeUnitCost }}
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
export default {
    components: {
        MaterialSearchDialog
    },
    data() {
        return {
            searchForm: {
                orderNumberSearch: '',
                shoeNumberSearch: '',
                materialTypeSearch: '',
                materialNameSearch: '',
                materialSpecificationSearch: '',
                materialSupplierSearch: '',
                purchaseDivideOrderRIdSearch: '',
            },
            isMultiInboundDialogVisible: false,
            isInboundDialogVisible: false,
            materialTypeOptions: [],
            materialSupplierOptions: [],
            isMaterialDialogVisible: false,
            pageSize: 10,
            currentPage: 1,
            inboundFormTemplate: {
                date: null,
                inboundType: 2,
                // contains inboundQuantity, remark, compositeUnitCost
                groupedSelectedRows: [],
            },
            inboundForm: {},
            materialTableData: [],
            currentRow: {},
            totalRows: 0,
            isMultipleSelection: false,
            selectedRows: [],
            selectedRowsCopy: [],
            isFinishInboundDialogOpen: false,
            rules: {
                date: [
                    { required: true, message: '此项为必填项', trigger: 'change' },
                ],
                inboundType: [
                    { required: true, message: '此项为必填项', trigger: 'change' },
                ],
                quantity: [
                    {
                        required: true,
                        validator: (rule, value, callback) => {
                            console.log(value)
                            if (!(value > 0)) {
                                callback(new Error("入库数量不能零"));
                            } else {
                                callback();
                            }
                        },
                        trigger: "change",
                    },
                ],
            },
            isReceiptDialogVisible: false,
        }
    },
    mounted() {
        this.getAllMaterialTypes()
        this.getAllSuppliers()
        this.getMaterialTableData()
    },
    methods: {
        openReceiptDialog() {
            this.isInboundDialogVisible = false
            this.isReceiptDialogVisible = true
        },
        goBackToInboundDialog() {
            this.isReceiptDialogVisible = false
            this.isInboundDialogVisible = true
        },
        getFormattedDateTime() {
            const now = new Date();
            const year = now.getFullYear();
            const month = String(now.getMonth() + 1).padStart(2, '0'); // Months are zero-based
            const day = String(now.getDate()).padStart(2, '0');
            const hours = String(now.getHours()).padStart(2, '0');
            const minutes = String(now.getMinutes()).padStart(2, '0');
            const seconds = String(now.getSeconds()).padStart(2, '0');
            return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
        },
        openInboundDialog() {
            if (this.selectedRows.length == 0) {
                ElMessage.error("未选择材料")
                return
            }
            this.groupSelectedRows()
            this.isInboundDialogVisible = true
        },
        groupSelectedRows() {
            this.inboundForm = { ...this.inboundFormTemplate }
            let groupedData = []
            this.selectedRowsCopy = JSON.parse(JSON.stringify(this.selectedRows))
            for (let item of this.selectedRowsCopy) {
                let newItem = { ...item, inboundQuantity: 0, remark: '', compositeUnitCost: Number(item.compositeUnitCost) }
                let group = groupedData.find(r => r.supplierName == item.supplierName)
                if (group) {
                    group.items.push(newItem)
                }
                else {
                    groupedData.push({ supplierName: item.supplierName, items: [newItem] })
                }
            }
            this.inboundForm.date = this.getFormattedDateTime()
            this.inboundForm.groupedSelectedRows = groupedData
        },
        openSearchDialog() {
            this.isMaterialDialogVisible = true
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
            this.selectedRows = selection
        },
        openFinishInboundDialog() {
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
                "opType": 3,
                "materialName": this.searchForm.materialNameSearch,
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
        async submitInboundForm() {
            this.$refs.inboundForm.validate(async (valid) => {
                if (valid) {
                    let data = []
                    for (let row of this.inboundForm.groupedSelectedRows) {
                        let obj = {
                            inboundTimestamp: this.inboundForm.date,
                            inboundType: this.inboundForm.inboundType,
                            items: []
                        }
                        for (let item of row.items) {
                            obj.items.push({
                                materialStorageId: item.materialStorageId,
                                materialCategory: item.materialCategory,
                                inboundQuantity: item.inboundQuantity,
                                compositeUnitCost: item.compositeUnitCost,
                                remark: item.remark
                            })
                        }
                        data.push(obj)
                    }
                    try {
                        console.log(data)
                        await axios.patch(`${this.$apiBaseUrl}/warehouse/warehousemanager/inboundmaterial`, data)
                        ElMessage.success("入库成功")
                    }
                    catch (error) {
                        console.log(error)
                        ElMessage.error("入库失败")
                    }
                    this.isInboundDialogVisible = false
                    this.getMaterialTableData()
                }
                else {
                    console.log("invalid")
                }
            })
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
        async editMaterial(row) {
            this.inboundForm = { ...this.inboundFormTemplate }
            this.inboundForm.unitPrice = row.unitPrice
            this.inboundForm.compositeUnitCost = row.compositeUnitCost
            this.isInboundDialogVisible = true
            this.currentRow = row
            console.log(this.inboundForm)
        },
        async finishInbound() {
            ElMessageBox.alert('该操作完成对选择鞋型材料入库，是否继续？', '警告', {
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
