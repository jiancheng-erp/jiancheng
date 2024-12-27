<template>
    <el-row :gutter="20">
        <el-col :span="6" :offset="0">
            <el-button-group>
                <el-button type="primary" size="default" @click="isMaterialDialogVisible = true">搜索条件设置</el-button>
                <el-button v-if="isMultipleSelection" @click="confirmOrderShoesToOutbound">
                    出库
                </el-button>
                <!-- <el-button v-if="isMultipleSelection" @click="openFinishOutboundDialog">
            完成出库
        </el-button> -->
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
                <el-table-column v-if="isMultipleSelection" type="selection" width="55" />
                <el-table-column prop="purchaseOrderIssueDate" label="采购订单日期" width="120" sortable="custom">
                </el-table-column>
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
                <el-table-column prop="status" label="状态"></el-table-column>
            </el-table>
        </el-col>
    </el-row>
    <el-row :gutter="20">
        <el-col :span="12" :offset="14">
            <el-pagination @size-change="handleSizeChange" @current-change="handlePageChange"
                :current-page="currentPage" :page-sizes="[10, 20, 30, 40]" :page-size="pageSize"
                layout="total, sizes, prev, pager, next, jumper" :total="materialTableData.length" />
        </el-col>
    </el-row>

    <el-dialog title="多选材料出库" v-model="isMultiMaterialDialogOpen" width="70%">
        <el-tabs v-model="activeTab">
            <el-tab-pane v-for="group in outboundForm.groupedSelectedRows" :key="group.orderShoeId"
                :label="`订单鞋型 ${group.items[0].orderRId} - ${group.items[0].shoeRId}`" :name="group.orderShoeId">
                <el-form :model="group" :rules="rules" ref="outboundForm">
                    <el-form-item prop="timestamp" label="出库日期" :rules="rules">
                        <el-date-picker v-model="group.timestamp" type="datetime" placeholder="选择日期时间"
                            style="width: 50%" value-format="YYYY-MM-DD HH:mm:ss" :default-value="new Date()">
                        </el-date-picker>
                    </el-form-item>
                    <el-form-item prop="outboundType" label="出库类型">
                        <el-radio-group v-model="group.outboundType">
                            <el-radio :value="0">生产使用</el-radio>
                            <el-radio :value="3">外发复合</el-radio>
                            <el-radio :value="2">外包发货</el-radio>
                            <el-radio :value="1">废料处理</el-radio>
                        </el-radio-group>
                    </el-form-item>
                    <!-- 生产使用的form item -->
                    <div v-if="group.outboundType == 0">
                        <el-form-item prop="section" label="出库工段">
                            <el-select v-model="group.section" placeholder="请输入出库工段" style="width: 240px">
                                <el-option v-for="item in teamOptions" :label="item.label"
                                    :value="item.value"></el-option>
                            </el-select>
                        </el-form-item>
                        <el-form-item prop="receiver" label="领料人">
                            <el-input v-model="group.receiver" placeholder="请输入领料人"></el-input>
                        </el-form-item>
                    </div>
                    <!-- 外包发货的form item -->
                    <div v-else-if="group.outboundType == 2">
                        <el-form-item prop="selectedOutsource" label="现有外包">
                            <el-table border stripe :data="group.outsourceInfo" style="width: 100%">
                                <el-table-column width="55">
                                    <template #default="scope">
                                        <el-radio v-model="group.selectedOutsource"
                                            :value="scope.row.outsourceInfoId" />
                                    </template>
                                </el-table-column>
                                <el-table-column prop="outsourceFactory" label="工厂名称" />
                                <el-table-column prop="outsourceAmount" label="外包数量" />
                                <el-table-column prop="outsourceType" label="外包类型" />
                            </el-table>
                        </el-form-item>
                    </div>
                    <!-- 外发复合的form item -->
                    <div v-else-if="group.outboundType == 3">
                        <el-form-item prop="selectedCompositeSupplier" label="供应商">
                            <el-select v-model="group.selectedCompositeSupplier" clearable filterable>
                                <el-option v-for="item in compositeSuppliersOptions" :value="item.supplierId"
                                    :label="item.supplierName" />
                            </el-select>
                        </el-form-item>
                    </div>

                    <el-form-item prop="address" v-if="[2, 3].includes(group.outboundType)" label="发货地址">
                        <el-input v-model="group.address" placeholder="请输入发货地址"></el-input>
                    </el-form-item>
                    <el-form-item prop="items" label="出库数量" v-if="group.outboundType != 3">
                        <el-table :data="group.items" style="width: 100%" border stripe>
                            <el-table-column prop="materialName" label="材料名称" />
                            <el-table-column prop="materialModel" label="材料型号" />
                            <el-table-column prop="materialSpecification" label="材料规格" />
                            <el-table-column prop="colorName" label="颜色" />
                            <el-table-column prop="currentAmount" label="库存" />
                            <el-table-column prop="outboundAmount" label="出库数量">
                                <template #default="scope">
                                    <el-input-number v-if="scope.row.materialCategory == 0" size="small"
                                        v-model="scope.row.outboundAmount" :min="0" :precision="5"
                                        :step="0.00001"></el-input-number>
                                    <el-button v-else type="primary"
                                        @click="openSizeMaterialQuantityDialog(scope.row)">打开</el-button>
                                </template>
                            </el-table-column>
                        </el-table>
                    </el-form-item>
                    <el-form-item prop="items" label="选择材料" v-if="group.outboundType == 3">
                        <el-table :data="getCompositeMaterials(group.items)" style="width: 100%" border stripe
                            default-expand-all>
                            <el-table-column type="expand">
                                <template #default="props">
                                    <el-table :data="props.row.craftNameList" border stripe
                                        @selection-change="handleCompositeSelectionChange">
                                        <el-table-column prop="craftName" label="复合工艺" />
                                        <el-table-column prop="outboundAmount" label="出库数量">
                                            <template #default="scope">
                                                <el-input-number size="small" v-model="scope.row.outboundAmount"
                                                    :min="0" :max="Number(props.row.currentAmount)" :precision="5"
                                                    :step="0.00001"
                                                    @change="(newVal, oldVal) => handleCompositeAmountChange(newVal, oldVal, props.row)"></el-input-number>
                                            </template>
                                        </el-table-column>
                                    </el-table>
                                </template>
                            </el-table-column>
                            <el-table-column prop="materialName" label="材料名称" />
                            <el-table-column prop="materialModel" label="材料型号" />
                            <el-table-column prop="materialSpecification" label="材料规格" />
                            <el-table-column prop="colorName" label="颜色" />
                            <el-table-column prop="currentAmount" label="库存" />
                            <el-table-column prop="materialUnit" label="单位" />
                        </el-table>
                    </el-form-item>
                </el-form>
            </el-tab-pane>
        </el-tabs>
        <template #footer>
            <span>
                <el-button @click="isMultiMaterialDialogOpen = false">取消</el-button>
                <el-button type="primary" @click="submitOutboundForm">出库</el-button>
            </span>
        </template>
    </el-dialog>
    <el-dialog title="多鞋码材料出库数量" v-model="isSizeMaterialStockOpen" width="50%">
        <el-form :rules="rules" ref="">
            <el-form-item>
                <el-table :data="selectedSizeMaterialData.quantityList" border stripe :rules>
                    <el-table-column prop="shoeSizeName" label="鞋码"></el-table-column>
                    <el-table-column prop="currentQuantity" label="库存"></el-table-column>
                    <el-table-column label="出库数量">
                        <template #default="scope">
                            <el-input-number v-model.number="scope.row.outboundAmount" type="number" :min="0"
                                :max="Number(scope.row.currentQuantity)" @input="calculateSum()"></el-input-number>
                        </template>
                    </el-table-column>
                </el-table>
            </el-form-item>
        </el-form>
        <template #footer>
            <el-button type="primary" @click="isSizeMaterialStockOpen = false">
                确认
            </el-button>
        </template>
    </el-dialog>

    <el-dialog title="确认订单鞋型" v-model="isConfirmOrderShoesDialogOpen" width="50%">
        <el-table :data="filteredIndepentPurchase" border stripe>
            <el-table-column prop="orderRId" label="订单号"></el-table-column>
            <el-table-column prop="shoeRId" label="鞋型号"></el-table-column>
            <el-table-column prop="materialName" label="材料名称"></el-table-column>
            <el-table-column prop="materialSpecification" label="材料规格"></el-table-column>
            <el-table-column prop="materialModel" label="材料型号"></el-table-column>
            <el-table-column prop="colorName" label="颜色"></el-table-column>
            <el-table-column label="操作">
                <template #default="scope">
                    <el-button type="primary" size="small" @click="openSelectOrderDialog(scope.row)">选择订单</el-button>
                </template>
            </el-table-column>
        </el-table>
        <template #footer>
            <el-button @click="isConfirmOrderShoesDialogOpen = false">返回</el-button>
            <el-button type="primary" @click="openMultipleOutboundDialog">继续</el-button>
        </template>
    </el-dialog>

    <el-dialog title="选择订单" v-model="isSelectOrderDialogOpen" width="50%">
        <el-input v-model="shoeSearch"
            placeholder="搜索订单号或工厂型号" class="mb-2" clearable>
        </el-input>
        <el-table :data="filteredShoes(currentSelectedAssetRow.orderId)" border stripe>
            <el-table-column width="55">
                <template #default="scope">
                    <el-radio :value="scope.row.orderShoeId" v-model="currentSelectedAssetRow.orderShoeId">
                    </el-radio>
                </template>
            </el-table-column>
            <el-table-column prop="orderRId" label="订单号"></el-table-column>
            <el-table-column prop="shoeRId" label="工厂型号"></el-table-column>
        </el-table>
        <el-pagination :current-page="currentShoePage" :page-size="shoePageSize" :total="activeOrderShoes.length"
            @current-change="handleShoePageChange" layout="prev, pager, next"></el-pagination>
        <!-- <div v-else>
            <el-descriptions :column="2" border>
                <el-descriptions-item label="订单号"> {{ currentSelectedAssetRow.orderRId }}</el-descriptions-item>
                <el-descriptions-item label="工厂型号"> {{ currentSelectedAssetRow.shoeRId }}</el-descriptions-item>
            </el-descriptions>
        </div> -->
        <template #footer>
            <el-button @click="isSelectOrderDialogOpen = false">确定</el-button>
        </template>
    </el-dialog>

    <el-dialog title="推进出库流程" v-model="isFinishOutboundDialogOpen" width="50%">
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
            <el-button @click="isFinishOutboundDialogOpen = false">返回</el-button>
            <el-button @click="finishOutbound">完成出库</el-button>
        </template>
    </el-dialog>
</template>
<script>
import axios from 'axios';
import { ElMessage, ElMessageBox, formItemContextKey } from 'element-plus';
import { getShoeSizesName } from '@/Pages/utils/getShoeSizesName';
import MaterialSearchDialog from './MaterialSearchDialog.vue';
export default {
    components: {
        MaterialSearchDialog
    },
    data() {
        return {
            isMultiOutboundDialogVisible: false,
            searchForm: {
                orderNumberSearch: '',
                shoeNumberSearch: '',
                materialTypeSearch: '',
                materialNameSearch: '',
                materialSpecificationSearch: '',
                materialSupplierSearch: '',
                purchaseDivideOrderRIdSearch: '',
            },
            materialTypeOptions: [],
            materialSupplierOptions: [],
            outboundForm: {
                groupedSelectedRows: []
            },
            formItemTemplate: {
                timestamp: null,
                outboundType: null,
                outboundQuantity: 0,
                section: null,
                receiver: null,
                address: null,
                deadlineDate: null,
                outsourceInfoId: null,
                outsourceInfo: [],
                selectedOutsource: null,
                materials: [],
                compositeMaterials: [],
                selectedCompositeSupplier: null,
            },
            currentPage: 1,
            pageSize: 10,
            materialTableData: [],
            isMaterialDialogVisible: false,
            materialDialogData: {},
            // for example, {"value": 1, "label": "部门1"}
            teamOptions: [],
            totalRows: 0,
            currentRow: {},
            isMultipleSelection: false,
            selectedRows: [],
            isSelectedRowsEmpty: false,
            getShoeSizesName,
            isMultiMaterialDialogOpen: false,
            isSizeMaterialStockOpen: false,
            selectedSizeMaterialData: [],
            isFinishOutboundDialogOpen: false,
            uniqueSelectedRows: [],
            rules: {
                timestamp: [
                    { required: true, message: '此项为必填项', trigger: 'change' },
                ],
                outboundType: [
                    { required: true, message: '此项为必填项', trigger: 'change' },
                ],
                section: [
                    {
                        validator: (rule, value, callback) => {
                            if (this.outboundForm.outboundType == 0 && value === null) {
                                callback(new Error('此项为必填项'));
                            } else {
                                callback();
                            }
                        },
                        trigger: 'change'
                    }
                ],
                receiver: [
                    {
                        validator: (rule, value, callback) => {
                            if (this.outboundForm.outboundType == 0 && !value) {
                                callback(new Error('此项为必填项'));
                            } else {
                                callback();
                            }
                        },
                        trigger: 'change'
                    }
                ],
                address: [
                    {
                        validator: (rule, value, callback) => {
                            if ([2, 3].includes(this.outboundForm.outboundType) && !value) {
                                callback(new Error('此项为必填项'));
                            } else {
                                callback();
                            }
                        },
                        trigger: 'change'
                    }
                ],
                selectedOutsource: [
                    { required: true, message: '此项为必填项', trigger: 'change' },
                ],
                materials: [
                    {
                        validator: (rule, value, callback) => {
                            const invalidRows = value.filter((row) => !row.outboundAmount);
                            if (invalidRows.length > 0) {
                                callback(new Error("出库数量不能为空"));
                            } else {
                                callback();
                            }
                        },
                        trigger: "blur",
                    },
                    {
                        validator: (rule, value, callback) => {
                            const invalidRows = value.filter((row) => row.outboundAmount <= 0);
                            if (invalidRows.length > 0) {
                                callback(new Error("出库数量需为正数"));
                            } else {
                                callback();
                            }
                        },
                        trigger: "blur",
                    },
                ],
                sizeMaterials: [
                    {
                        validator: (rule, value, callback) => {
                            console.log(value)
                            const invalidRows = value.filter((row) => row.metaData.enteredAmount == 0);
                            if (invalidRows.length > 0) {
                                callback(new Error("出库数量不能为空"));
                            } else {
                                callback();
                            }
                        },
                        trigger: "change",
                    },
                ]
            },
            selectedCompositeRows: [],
            compositeSuppliersOptions: [],
            activeOrderShoes: [],
            currentShoePage: 1,
            shoePageSize: 5,
            shoeSearch: "",
            currentSelectedAssetRow: {},
            isSelectOrderDialogOpen: false,
            isConfirmOrderShoesDialogOpen: false,
            activeTab: null,
        }
    },
    computed: {
        filteredColumns() {
            return this.shoeSizeColumns.filter(column =>
                this.orderShoeBatchInfo.some(row => row[column.prop] !== undefined && row[column.prop] !== null && row[column.prop] !== 0)
            );
        },
        filteredIndepentPurchase() {
            return this.selectedRows.filter(row => row.orderShoeId === null)
        }
    },
    mounted() {
        this.getAllMaterialTypes()
        this.getAllSuppliers()
        this.getAllCompositeSuppliers(),
            this.getActiveOrderShoes()
        this.getMaterialTableData()
        this.getAllDeparments()
    },
    methods: {
        handleShoePageChange(val) {
            this.currentShoePage = val
        },
        getCompositeMaterials(items) {
            return items.filter(item => item.craftNameList.length > 0)
        },
        async getAllDeparments() {
            let response = await axios.get(`${this.$apiBaseUrl}/general/getalldepartments`)
            this.teamOptions = response.data
        },
        filteredShoes(orderId = null) {
            let filtered = []
            if (orderId === null) {
                filtered = this.activeOrderShoes.filter(shoe =>
                    shoe.orderRId.includes(this.shoeSearch) ||
                    shoe.shoeRId.includes(this.shoeSearch)
                )
            }
            else {
                filtered = this.activeOrderShoes.filter(shoe =>
                    shoe.shoeRId.includes(this.shoeSearch)
                );
            }
            const start = (this.currentShoePage - 1) * this.shoePageSize;
            return filtered.slice(start, start + this.shoePageSize);
        },
        openSelectOrderDialog(row) {
            this.currentSelectedAssetRow = row
            this.isSelectOrderDialogOpen = true
        },
        handleShoeSelection(selectedShoe) {
            this.outboundForm.orderShoeId = selectedShoe.orderShoeId;
        },
        async getActiveOrderShoes() {
            let response = await axios.get(`${this.$apiBaseUrl}/order/getactiveordershoes`)
            this.activeOrderShoes = response.data
        },
        updateDialogVisible(newVal) {
            this.isMaterialDialogVisible = newVal

        },
        handleSearch(values) {
            this.searchForm = { ...values }
            this.getMaterialTableData()
        },
        handleCompositeAmountChange(newVal, oldVal, rowData) {
            console.log(newVal, oldVal, rowData)
            rowData.currentAmount = Number((Number(rowData.currentAmount) - newVal + oldVal).toFixed(5))
        },
        handleCompositeSelectionChange(selection) {
            this.selectedCompositeRows = selection
        },
        isSelectable(row) {
            // return row.status !== '已完成入库'
        },
        calculateSum() {
            this.selectedSizeMaterialData.metaData["enteredAmount"] = this.selectedSizeMaterialData.quantityList.reduce((sum, row) => sum + (row.outboundAmount || 0), 0);
        },
        openSizeMaterialStockDialog(row) {
            console.log(row)
            this.selectedSizeMaterialData = row
            this.isSizeMaterialStockOpen = true
        },
        async confirmOrderShoesToOutbound() {
            if (this.selectedRows.length == 0) {
                ElMessage.error("未选择材料")
                return
            }
            if (this.selectedRows.some(row => row.orderShoeId === null)) {
                this.isConfirmOrderShoesDialogOpen = true
                return
            }
            this.openMultipleOutboundDialog()
        },
        async openMultipleOutboundDialog() {
            if (this.selectedRows.length == 0) {
                ElMessage.error("未选择材料")
                return
            }
            // await this.getOutsourceInfo()
            await this.groupSelectedRows()
            this.isMultiMaterialDialogOpen = true
        },
        toggleSelectionMode() {
            this.isMultipleSelection = !this.isMultipleSelection;
        },
        handleSelectionChange(selection) {
            this.selectedRows = selection
        },
        async groupSelectedRows() {
            let groupedData = [];
            for (let item of this.selectedRows) {
                let templateObj = JSON.parse(JSON.stringify(this.formItemTemplate))
                let craftNameList = item.craftName.split("@")
                let newItem = { ...item, outboundAmount: 0, remark: "", sizeMaterialOutboundTable: [], craftNameList: [] }
                craftNameList.forEach(craftName => {
                    newItem.craftNameList.push({ craftName: craftName, outboundAmount: 0 })
                })
                let shoeSizeColumns = []
                if (item.materialCategory == 1) {
                    let params = { "sizeMaterialStorageId": item.materialStorageId, "orderId": item.orderId, "purchaseDivideOrderId": item.purchaseDivideOrderId }
                    let response = await axios.get(`${this.$apiBaseUrl}/warehouse/warehousemanager/getsizematerialbyid`, { params })
                    newItem["sizeMaterialOutboundTable"] = response.data
                    newItem["sizeMaterialOutboundTable"].forEach(row => {
                        row.outboundQuantity = 0
                    })
                    newItem.sizeMaterialOutboundTable.forEach((element, index) => {
                        newItem[`amount${index}`] = element.outboundQuantity
                    })
                    // insert shoe size columns into current row
                    newItem.sizeMaterialOutboundTable.forEach((element, index) => {
                        // for display
                        if (element.predictQuantity > 0) {
                            shoeSizeColumns.push({
                                "prop": `amount${index}`,
                                "label": element.shoeSizeName
                            })
                        }
                    })
                }
                const group = groupedData.find(g => g.orderShoeId === item.orderShoeId);
                if (group) {
                    group.items.push(newItem);
                } else {
                    groupedData.push({
                        orderShoeId: item.orderShoeId,
                        shoeSizeColumns: shoeSizeColumns,
                        items: [newItem],
                        ...templateObj
                    });
                }
            }
            this.outboundForm.groupedSelectedRows = groupedData;
            this.activeTab = groupedData[0].orderShoeId
            console.log(this.outboundForm.groupedSelectedRows)
        },
        async getAllMaterialTypes() {
            const response = await axios.get(`${this.$apiBaseUrl}/warehouse/warehousemanager/getallmaterialtypes`)
            this.materialTypeOptions = response.data
        },
        async getAllSuppliers() {
            const response = await axios.get(`${this.$apiBaseUrl}/warehouse/warehousemanager/getallsuppliernames`)
            this.materialSupplierOptions = response.data
        },
        async getAllCompositeSuppliers() {
            const response = await axios.get(`${this.$apiBaseUrl}/warehouse/warehousemanager/getallcompositesuppliers`)
            this.compositeSuppliersOptions = response.data
        },
        async getMaterialTableData(sortColumn, sortOrder) {
            const params = {
                "page": this.currentPage,
                "pageSize": this.pageSize,
                "opType": 2,
                "materialType": this.searchForm.materialTypeSearch,
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
        async submitOutboundForm() {
            console.log(this.outboundForm)
            this.$refs.outboundForm.validate(async (valid) => {
                if (valid) {
                    console.log("Form is valid. Proceeding with submission.");
                    let materialOutboundList = []
                    if (this.outboundForm.outboundType != 3) {
                        this.outboundForm.materials.forEach(row => {
                            materialOutboundList.push({ "storageId": row.materialStorageId, "amount": row.outboundAmount })
                        })
                    }
                    else {
                        let amount = 0
                        this.outboundForm.compositeMaterials.forEach(row => {
                            let obj = { "storageId": row.materialStorageId, "craftNameList": row["craftNameList"], "amount": 0 }
                            row["craftNameList"].forEach(subRow => {
                                amount += subRow["outboundAmount"]
                            })
                            obj["amount"] = amount
                            materialOutboundList.push(obj)
                        })
                    }
                    let sizeMaterialOutboundList = []
                    this.outboundForm.sizeMaterials.forEach(row => {
                        let obj = { "storageId": row.metaData.materialStorageId, outboundAmounts: [] }
                        row.quantityList.forEach(shoeSizeInfo => {
                            obj.outboundAmounts.push({ shoeSizeName: shoeSizeInfo["shoeSizeName"], amount: shoeSizeInfo["outboundAmount"] })
                        })
                        sizeMaterialOutboundList.push(obj)
                    })
                    console.log(this.outboundForm.selectedCompositeSupplier)
                    let data = {
                        "materialOutboundList": materialOutboundList,
                        "sizeMaterialOutboundList": sizeMaterialOutboundList,
                        "timestamp": this.outboundForm.timestamp,
                        "type": this.outboundForm.outboundType,
                        "outboundDepartment": this.outboundForm.section,
                        "outboundAddress": this.outboundForm.address,
                        "picker": this.outboundForm.receiver,
                        "outsourceInfoId": null,
                        "compositeSupplierId": this.outboundForm.selectedCompositeSupplier
                    }
                    if (this.outboundForm.selectedOutsource) {
                        data["outsourceInfoId"] = this.outboundForm.selectedOutsource.outsourceInfoId
                    }
                    console.log(data)
                    try {
                        await axios.patch(`${this.$apiBaseUrl}/warehouse/warehousemanager/outboundmaterial`, data)
                        ElMessage.success("出库成功")
                    }
                    catch (error) {
                        console.log(error)
                        ElMessage.error(error.response.data.message)
                    }
                    this.isMultiMaterialDialogOpen = false
                    this.getMaterialTableData()
                } else {
                    console.log("invalid")
                }
            })
        },

        openFinishOutboundDialog() {
            if (this.selectedRows.length == 0) {
                ElMessage.error("未选择材料")
                return
            }
            this.isFinishOutboundDialogOpen = true
        },
        handleSizeChange(val) {
            this.pageSize = val
            this.getMaterialTableData()
        },
        handlePageChange(val) {
            this.page = val
            this.getMaterialTableData()
        },
        formatDecimal(row, column, cellValue, index) {
            return Number(cellValue).toFixed(2)
        },
        async getOutsourceInfo() {
            let params = { "orderShoeId": this.selectedRows[0].orderShoeId }
            let response = await axios.get(`${this.$apiBaseUrl}/production/productionmanager/getordershoeoutsourceinfo`, { params })
            this.outboundForm.outsourceInfo = []
            console.log(response.data)
            response.data.forEach(element => {
                if ((element.outsourceStatus == '已审批' || element.outsourceStatus == '材料出库') && element.materialRequired) {
                    this.outboundForm.outsourceInfo.push(element)
                }
            });
            console.log(this.outboundForm.outsourceInfo)
        },
        async finishOutsourceOutbound(row) {
            try {
                let data = { "outsourceInfoId": row.outsourceInfoId }
                await axios.patch(`${this.$apiBaseUrl}/warehouse/warehousemanager/finishoutsourceoutbound`, data)
                await this.getOutsourceInfo()
                ElMessage.success("外包出库成功")
            }
            catch (error) {
                console.log(error)
                ElMessage.error("外包出库失败")
            }
        },
        async finishOutbound() {
            ElMessageBox.alert('该操作完成对选择鞋型材料出库', '提示', {
                confirmButtonText: '确认',
                showCancelButton: true,
                cancelButtonText: '取消'
            }).then(async () => {
                let data = []
                this.selectedRows.forEach(row => {
                    data.push({ storageId: row.materialStorageId, materialCategory: row.materialCategory })
                })
                try {
                    await axios.patch(`${this.$apiBaseUrl}/warehouse/warehousemanager/finishoutboundmaterial`, data)
                    ElMessage.success("操作成功")
                }
                catch (error) {
                    console.log(error)
                    ElMessage.error("操作异常")
                }
                this.isFinishOutboundDialogOpen = false
                this.getMaterialTableData()
            })
        },
        async sortData({ prop, order }) {
            await this.getMaterialTableData(prop, order)
        }
    }
}
</script>
