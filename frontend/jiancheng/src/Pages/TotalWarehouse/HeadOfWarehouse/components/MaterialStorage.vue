<template>
    <el-row :gutter="20">
        <el-col :span="24" :offset="0">
            <el-button type="primary" @click="isMaterialDialogVisible = true">搜索条件设置</el-button>
            <el-button v-if="role == 23" type="success" @click="confirmOrderShoesToOutbound">
                出库
            </el-button>
        </el-col>
        <MaterialSearchDialog :visible="isMaterialDialogVisible" :materialSupplierOptions="materialSupplierOptions"
            :materialTypeOptions="materialTypeOptions" :material-name-options="materialNameOptions" :warehouse-options="warehouseOptions"
            :searchForm="searchForm" @update-visible="updateDialogVisible" @confirm="handleSearch" />
    </el-row>
    <el-row :gutter="20">
        <el-col>
            <el-form :inline="true" :model="outboundForm" class="demo-form-inline" :rules="rules" ref="outboundForm">
                <el-form-item v-if="role == 23" prop="currentDateTime" label="日期">
                    <el-date-picker v-model="outboundForm.currentDateTime" type="datetime"
                        value-format="YYYY-MM-DD HH:mm:ss" clearable />
                </el-form-item>
                <el-form-item v-if="role == 23" prop="outboundType" label="出库类型">
                    <el-select v-model="outboundForm.outboundType" filterable clearable @change="handleOutboundType">
                        <el-option v-for="item in outboundOptions" :key="item.value" :value="item.value"
                            :label="item.label"></el-option>
                    </el-select>
                </el-form-item>
                <el-form-item v-if="outboundForm.outboundType == 0 && role == 23" prop="departmentId" label="部门">
                    <el-select v-model="outboundForm.departmentId" filterable clearable>
                        <el-option v-for="item in departmentOptions" :label="item.label"
                            :value="item.value"></el-option>
                    </el-select>
                </el-form-item>
                <el-form-item v-if="[2, 3].includes(outboundForm.outboundType) && role == 23" prop="supplierName"
                    label="出库厂家">
                    <el-autocomplete v-model="outboundForm.supplierName" :fetch-suggestions="querySuppliers" clearable
                        @select="handleSupplierSelect" />
                </el-form-item>
                <el-form-item v-if="role == 23" prop="picker" label="领料人">
                    <el-input v-model="outboundForm.picker"></el-input>
                </el-form-item>
                <el-form-item v-if="role == 23" prop="remark" label="备注">
                    <el-input v-model="outboundForm.remark"></el-input>
                </el-form-item>
            </el-form>
        </el-col>

    </el-row>
    <div class="transfer-tables">
        <!-- Top Table -->
        <el-table v-if="role == 23" ref="topTableData" :data="topTableData"
            style="width: 100%; margin-bottom: 20px; height: 20vh" @selection-change="handleTopSelectionChange" border
            stripe>
            <el-table-column type="selection" width="55" />
            <el-table-column prop="orderRId" label="订单号"></el-table-column>
            <el-table-column prop="shoeRId" label="工厂鞋型"></el-table-column>
            <el-table-column prop="materialType" label="类型"></el-table-column>
            <el-table-column prop="materialName" label="名称" width="100">
                <template #default="scope">
                    <el-tooltip effect="dark" :content="scope.row.materialName" placement="bottom">
                        <span class="truncate-text">
                            {{ scope.row.materialName }}
                        </span>
                    </el-tooltip>
                </template>
            </el-table-column>
            <el-table-column prop="materialModel" label="型号"></el-table-column>
            <el-table-column prop="materialSpecification" label="规格"></el-table-column>
            <el-table-column prop="colorName" label="颜色"></el-table-column>
            <el-table-column prop="actualInboundUnit" label="单位"></el-table-column>
            <el-table-column prop="estimatedInboundAmount" label="采购数量"></el-table-column>
            <el-table-column prop="actualInboundAmount" label="入库数量"></el-table-column>
            <el-table-column prop="currentAmount" label="库存"></el-table-column>
            <el-table-column prop="supplierName" label="供应商"></el-table-column>
        </el-table>

        <!-- Control Buttons -->
        <div v-if="role == 23" class="transfer-buttons" style="text-align: center; margin-bottom: 20px;">
            <el-button type="primary" @click="moveUp" :disabled="bottomSelected.length === 0">
                选择 <el-icon>
                    <Top />
                </el-icon>
            </el-button>
            <el-button type="primary" @click="moveDown" :disabled="topSelected.length === 0" style="margin-left: 20px;">
                <el-icon>
                    <Bottom />
                </el-icon> 移除
            </el-button>
        </div>
    </div>
    <el-table ref="bottomTableData" :data="bottomTableData" border stripe style="height: 60vh; width: 100%"
        @selection-change="handleBottomSelectionChange">
        <el-table-column v-if="role == 23" type="selection" width="55" />
        <el-table-column prop="orderRId" label="订单号"></el-table-column>
        <el-table-column prop="shoeRId" label="工厂鞋型"></el-table-column>
        <el-table-column prop="materialType" label="类型"></el-table-column>
        <el-table-column prop="materialName" label="名称" width="100">
            <template #default="scope">
                <el-tooltip effect="dark" :content="scope.row.materialName" placement="bottom">
                    <span class="truncate-text">
                        {{ scope.row.materialName }}
                    </span>
                </el-tooltip>
            </template>
        </el-table-column>
        <el-table-column prop="materialModel" label="型号"></el-table-column>
        <el-table-column prop="materialSpecification" label="规格"></el-table-column>
        <el-table-column prop="colorName" label="颜色"></el-table-column>
        <el-table-column prop="actualInboundUnit" label="单位"></el-table-column>
        <el-table-column prop="averagePrice" label="平均价" ></el-table-column>
        <el-table-column prop="estimatedInboundAmount" label="采购数量"></el-table-column>
        <el-table-column prop="actualInboundAmount" label="入库数量"></el-table-column>
        <el-table-column prop="currentAmount" label="库存"></el-table-column>
        <el-table-column prop="supplierName" label="供应商"></el-table-column>
        <el-table-column fixed="right" label="操作" width="120">
            <template #default="scope">
                <el-button-group>
                    <el-button v-if="scope.row.materialCategory == 1" type="primary" size="small"
                        @click="viewSizeMaterialStock(scope.row)">查看多鞋码库存</el-button>
                    <el-button type="primary" size="small" @click="viewRecords(scope.row)">入/出库记录</el-button>
                </el-button-group>
            </template>
        </el-table-column>
    </el-table>
    <el-row :gutter="20">
        <el-col :span="12" :offset="14">
            <el-pagination @size-change="handleSizeChange" @current-change="handlePageChange"
                :current-page="currentPage" :page-sizes="[20, 40, 60, 100]" :page-size="pageSize"
                layout="total, sizes, prev, pager, next, jumper" :total="totalRows" />
        </el-col>
    </el-row>

    <el-dialog title="材料入库/出库记录" v-model="isRecordDialogVisible" width="80%">
        <el-descriptions border size="default" title="材料信息">
            <el-descriptions-item label="材料名称">
                {{ currentRow.materialName }}
            </el-descriptions-item>
            <el-descriptions-item label="材料型号">
                {{ currentRow.materialModel }}
            </el-descriptions-item>
            <el-descriptions-item label="材料规格">
                {{ currentRow.materialSpecification }}
            </el-descriptions-item>
            <el-descriptions-item label="颜色">
                {{ currentRow.colorName }}
            </el-descriptions-item>
            <el-descriptions-item label="材料供应商">
                {{ currentRow.supplierName }}
            </el-descriptions-item>
            <el-descriptions-item label="材料单位">
                {{ currentRow.materialUnit }}
            </el-descriptions-item>
            <el-descriptions-item label="材料库存">
                {{ currentRow.currentAmount }}
            </el-descriptions-item>

        </el-descriptions>
        <el-tabs>
            <el-tab-pane label="入库记录">
                <el-table v-if="currentRow.materialCategory == 0" :data="materialInboundRecordData" border stripe>
                    <el-table-column prop="inboundRId" label="入库单号"></el-table-column>
                    <el-table-column prop="inboundType" label="用途"></el-table-column>
                    <el-table-column prop="timestamp" label="时间"></el-table-column>
                    <el-table-column prop="unitPrice" label="单价"></el-table-column>
                    <el-table-column prop="inboundAmount" label="数量"></el-table-column>
                    <el-table-column prop="itemTotalPrice" label="金额"></el-table-column>
                    <el-table-column prop="remark" label="备注"></el-table-column>
                </el-table>
                <el-table v-if="currentRow.materialCategory == 1" :data="sizeMaterialInboundRecordData" border stripe>
                    <el-table-column prop="inboundRId" label="入库单号"></el-table-column>
                    <el-table-column prop="inboundType" label="用途"></el-table-column>
                    <el-table-column prop="timestamp" label="时间"></el-table-column>
                    <el-table-column prop="unitPrice" label="单价"></el-table-column>
                    <el-table-column prop="inboundAmount" label="数量"></el-table-column>
                    <el-table-column prop="itemTotalPrice" label="金额"></el-table-column>
                    <el-table-column v-for="column in shoeSizeColumns" :key="column.prop" :prop="column.prop"
                        :label="column.label"></el-table-column>
                    <el-table-column prop="remark" label="备注"></el-table-column>
                </el-table>
            </el-tab-pane>
            <el-tab-pane label="出库记录">
                <el-table v-if="currentRow.materialCategory == 0" :data="materialOutboundRecordData" border stripe>
                    <el-table-column prop="outboundRId" label="出库单号"></el-table-column>
                    <el-table-column prop="outboundType" label="用途"></el-table-column>
                    <el-table-column prop="timestamp" label="时间"></el-table-column>
                    <el-table-column prop="unitPrice" label="平均价"></el-table-column>
                    <el-table-column prop="outboundAmount" label="数量"></el-table-column>
                    <el-table-column prop="itemTotalPrice" label="金额"></el-table-column>
                    <el-table-column prop="outboundDestination" label="出库至"></el-table-column>
                    <el-table-column prop="picker" label="领料人"></el-table-column>
                    <el-table-column prop="remark" label="备注"></el-table-column>
                </el-table>
                <el-table v-if="currentRow.materialCategory == 1" :data="sizeMaterialOutboundRecordData" border stripe>
                    <el-table-column prop="outboundRId" label="出库单号"></el-table-column>
                    <el-table-column prop="outboundType" label="用途"></el-table-column>
                    <el-table-column prop="timestamp" label="时间"></el-table-column>
                    <el-table-column v-for="column in shoeSizeColumns" :key="column.prop" :prop="column.prop"
                        :label="column.label"></el-table-column>
                    <el-table-column prop="outboundDestination" label="出库至"></el-table-column>
                    <el-table-column prop="picker" label="领料人"></el-table-column>
                    <el-table-column prop="remark" label="备注"></el-table-column>
                </el-table>
            </el-tab-pane>
        </el-tabs>
    </el-dialog>
    <el-dialog title="尺码材料库存" v-model="isViewSizeMaterialStockOpen" width="60%">
        <el-table :data="sizeMaterialStockData" border stripe>
            <el-table-column prop="shoeSizeName" label="鞋码"></el-table-column>
            <el-table-column prop="predictQuantity" label="采购数量"></el-table-column>
            <el-table-column prop="actualQuantity" label="入库数量"></el-table-column>
            <el-table-column prop="currentQuantity" label="库存"></el-table-column>
        </el-table>
    </el-dialog>

    <OutboundDialog :visible="isConfirmOrderShoesDialogOpen" :parentOutboundForm="outboundForm"
        @update-visible="updateConfirmOrderShoesDialogVis" :selectedRows="selectedRowsCopy"
        @update-outbound-form="updateOutboundForm"
        :outboundOptions="outboundOptions" :departmentOptions="departmentOptions" />
</template>
<script>
import axios from 'axios'
import MaterialSearchDialog from './MaterialSearchDialog.vue';
import OutboundDialog from './OutboundDialog.vue';
import { ElMessage } from 'element-plus';
export default {
    components: {
        MaterialSearchDialog,
        OutboundDialog
    },
    data() {
        return {
            role: localStorage.getItem('role'),
            isRecordDialogVisible: false,
            isSizeRecordDialogVisible: false,
            isMaterialDialogVisible: false,
            searchForm: {
                isNonOrderMaterial: 0,
                orderNumberSearch: '',
                shoeNumberSearch: '',
                materialTypeSearch: '',
                materialNameSearch: '',
                materialModelSearch: '',
                materialColorSearch: '',
                materialSpecificationSearch: '',
                materialSupplierSearch: '',
                totalPurchaseOrderRIdSearch: '',
            },
            materialTypeOptions: [],
            materialSupplierOptions: [],
            warehouseOptions: [],
            departmentOptions: [],
            pageSize: 20,
            currentPage: 1,
            recordData: [],
            sizeRecordData: [],
            bottomTableData: [],
            columns: [],
            totalRows: 0,
            currentRow: {},
            isViewSizeMaterialStockOpen: false,
            sizeMaterialStockData: [],
            materialInboundRecordData: [],
            sizeMaterialInboundRecordData: [],
            materialOutboundRecordData: [],
            sizeMaterialOutboundRecordData: [],
            shoeSizeColumns: [],
            selectedRows: [],
            selectedRowsCopy: [],
            outboundForm: {},
            formItemTemplate: {
                currentDateTime: new Date((new Date()).getTime() - (new Date()).getTimezoneOffset() * 60000).toISOString().slice(0, 19).replace('T', ' '),
                outboundType: 0,
                outboundQuantity: 0,
                departmentId: null,
                picker: null,
                outboundAddress: null,
                deadlineDate: null,
                outsourceInfoId: null,
                outsourceInfo: [],
                selectedOutsourceId: '',
                selectedOutsourceFactory: '',
                items: [],
                selectedCompositeSupplier: null,
                // groupedSelectedRows contains formItemTemplate,
                // selectedOrderShoeId, selectedOrderId, selectedOrderRId, and selectedShoeId
                // because some materials don't have orderId or orderShoeId
                outsourceInfo: [],
                warehouseId: null,
            },
            isConfirmOrderShoesDialogOpen: false,
            materialNameOptions: [],
            outboundOptions: [
                { label: '工厂使用', value: 0 },
                { label: '废料处理', value: 1 },
                { label: '外包发货', value: 2 },
                { label: '外发复合', value: 3 },
            ],
            rules: {
                currentDateTime: [{ required: true, message: '请选择日期', trigger: 'blur' }],
                outboundType: [{ required: true, message: '请选择出库类型', trigger: 'blur' }],
                supplierName: [{ required: true, message: '请输入出库厂家', trigger: 'blur' }],
                departmentId: [{ required: true, message: '请选择部门', trigger: 'blur' }],
            },
            topTableData: [],
            topSelected: [],
            bottomTableData: [],
            bottomSelected: [],
        }
    },
    mounted() {
        this.getAllMaterialTypes()
        this.getAllSuppliers()
        this.getMaterialNameOptions()
        this.getMaterialTableData()
        this.getWarehouseOptions()
        this.getDepartmentOptions()
        this.outboundForm = { ...this.formItemTemplate }
    },
    methods: {
        // Move selected items from bottom to top
        moveUp() {
            this.topTableData = this.topTableData.concat(this.bottomSelected);
            this.bottomTableData = this.bottomTableData.filter(
                item => !this.bottomSelected.includes(item)
            );
            this.$refs.bottomTableData.clearSelection();
            this.bottomSelected = [];
        },
        // Move selected items from top to bottom
        moveDown() {
            this.bottomTableData = this.bottomTableData.concat(this.topSelected);
            this.topTableData = this.topTableData.filter(
                item => !this.topSelected.includes(item)
            );
            this.$refs.topTableData.clearSelection();
            this.topSelected = [];
        },
        querySuppliers(queryString, callback) {
            const results = this.materialSupplierOptions
                .filter((item) => item.toLowerCase().includes(queryString.toLowerCase()))
                .map((item) => ({ value: item }));

            callback(results);
        },
        handleSupplierSelect(item) {
            this.outboundForm.supplierName = item.value;
        },
        async handleOutboundType(value) {
            this.outboundForm.outboundType = value
        },
        async getWarehouseOptions() {
            const response = await axios.get(`${this.$apiBaseUrl}/logistics/allwarehouses`)
            this.warehouseOptions = response.data
        },
        async getMaterialNameOptions() {
            const params = { department: 0 }
            const response = await axios.get(`${this.$apiBaseUrl}/logistics/getallmaterialname`, { params })
            this.materialNameOptions = response.data
        },
        updateOutboundForm(newVal) {
            this.outboundForm = { ...newVal }
        },
        updateConfirmOrderShoesDialogVis(newVal) {
            this.isConfirmOrderShoesDialogOpen = newVal
            this.topSelected = []
            this.bottomSelected = []
            this.topTableData = []
            this.bottomTableData = []
            this.outboundForm = { ...this.formItemTemplate }
            this.outboundForm.currentDateTime = new Date((new Date()).getTime() - (new Date()).getTimezoneOffset() * 60000).toISOString().slice(0, 19).replace('T', ' ')
            this.getMaterialTableData()
        },
        openSizeMaterialQuantityDialog(row) {
            this.currentSizeMaterialQuantityRow = row
            this.isOpenSizeMaterialQuantityDialogVisible = true
        },
        handleTopSelectionChange(selection) {
            this.topSelected = selection;
        },
        handleBottomSelectionChange(selection) {
            this.bottomSelected = selection;
        },
        async confirmOrderShoesToOutbound() {
            this.$refs.outboundForm.validate(async (valid) => {
                if (valid) {
                    if (this.topTableData.length == 0) {
                        ElMessage.error("未选择材料")
                        return
                    }
                    this.selectedRowsCopy = JSON.parse(JSON.stringify(this.topTableData))
                    // collect all orderShoeId that are null
                    this.selectedRowsCopy.forEach(row => {
                        row["selectedOrderShoeId"] = row.orderShoeId
                        row["selectedOrderId"] = row.orderId
                        row["selectedShoeRId"] = row.shoeRId
                        row["selectedOrderRId"] = row.orderRId
                    })
                    this.isConfirmOrderShoesDialogOpen = true
                }
                else {
                    ElMessage.error("请检查表单")
                    return
                }
            })
        },
        async viewSizeMaterialStock(row) {
            let params = { "storageId": row.materialStorageId }
            let response = await axios.get(`${this.$apiBaseUrl}/warehouse/getsizematerialstoragebystorageid`, { params })
            let temp = []
            for (let i=0; i < response.data.shoeSizeColumns.length; i++) {
                let obj = {
                    "shoeSizeName": response.data.shoeSizeColumns[i],
                    "predictQuantity": response.data[`estimatedInboundAmount${i}`],
                    "actualQuantity": response.data[`actualInboundAmount${i}`],
                    "currentQuantity": response.data[`currentAmount${i}`],
                }
                temp.push(obj)
            }
            this.sizeMaterialStockData = temp
            this.isViewSizeMaterialStockOpen = true
        },
        updateDialogVisible(newVal) {
            this.isMaterialDialogVisible = newVal
        },
        handleSearch(values) {
            this.searchForm = { ...values }
            this.getMaterialTableData()
        },
        async getDepartmentOptions() {
            const response = await axios.get(`${this.$apiBaseUrl}/general/getalldepartments`)
            this.departmentOptions = response.data
        },
        async getAllMaterialTypes() {
            const response = await axios.get(`${this.$apiBaseUrl}/warehouse/warehousemanager/getallmaterialtypes`)
            this.materialTypeOptions = response.data
        },
        async getAllSuppliers() {
            const response = await axios.get(`${this.$apiBaseUrl}/warehouse/warehousemanager/getallsuppliernames`)
            this.materialSupplierOptions = response.data
        },
        async getMaterialTableData() {
            const params = {
                "page": this.currentPage,
                "pageSize": this.pageSize,
                "materialType": this.searchForm.materialTypeSearch,
                "materialName": this.searchForm.materialNameSearch,
                "materialModel": this.searchForm.materialModelSearch,
                "materialSpec": this.searchForm.materialSpecificationSearch,
                "materialColor": this.searchForm.materialColorSearch,
                "supplier": this.searchForm.materialSupplierSearch,
                "craftName": this.searchForm.craftNameSearch,
                "orderRId": this.searchForm.orderNumberSearch,
                "shoeRId": this.searchForm.shoeNumberSearch,
                "purchaseOrderRId": this.searchForm.totalPurchaseOrderRIdSearch,
                "warehouseId": this.searchForm.warehouseId,
                "isNonOrderMaterial": this.searchForm.isNonOrderMaterial,
            }
            const response = await axios.get(`${this.$apiBaseUrl}/warehouse/warehousemanager/getallmaterialinfo`, { params })
            this.bottomTableData = response.data.result
            this.totalRows = response.data.total
        },
        formatDecimal(row, column, cellValue, index) {
            return Number(cellValue).toFixed(2)
        },
        handleSizeChange(val) {
            this.pageSize = val
            this.getMaterialTableData()
        },
        handlePageChange(val) {
            this.currentPage = val
            this.getMaterialTableData()
        },
        async viewRecords(row) {
            this.currentRow = row
            let tempShoeSizeColumns = []
            if (row.materialCategory == 1) {
                let params = { "storageId": row.materialStorageId }
                let response = await axios.get(`${this.$apiBaseUrl}/warehouse/getinboundrecordsforsizematerial`, { params })
                this.sizeMaterialInboundRecordData = response.data

                let sizeResponse = await axios.get(`${this.$apiBaseUrl}/warehouse/getoutboundrecordsforsizematerial`, { params })
                this.sizeMaterialOutboundRecordData = sizeResponse.data

                this.shoeSizeColumns = this.currentRow.shoeSizeColumns.map((item, index) => {
                    return {
                        prop: `amount${index}`,
                        label: item,
                    }
                })
                this.isRecordDialogVisible = true
            } else {
                let params = { "storageId": row.materialStorageId }
                let response = await axios.get(`${this.$apiBaseUrl}/warehouse/getinboundrecordsformaterial`, { params })
                this.materialInboundRecordData = response.data

                let response1 = await axios.get(`${this.$apiBaseUrl}/warehouse/getoutboundrecordsformaterial`, { params })
                this.materialOutboundRecordData = response1.data
                this.isRecordDialogVisible = true
            }
        },
    }
}
</script>