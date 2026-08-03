<template>
    <el-row>
        <el-col>
            <el-select v-model="searchForm.warehouseNameSearch" filterable clearable placeholder="仓库名搜索" style="width: 200px;"
                @change="getMaterialTableData">
                <el-option v-for="item in warehouseOptions" :value="item.value" :label="item.label"></el-option>
            </el-select>
            <el-select v-model="searchForm.materialSupplierSearch" value-key="" placeholder="供应商搜索" clearable filterable
                @change="getMaterialTableData" style="width: 200px; margin-left: 20px;">
                <el-option v-for="item in materialSupplierOptions" :value="item" />
            </el-select>
            <el-select v-model="searchForm.materialNameSearch" value-key="" placeholder="材料名搜索" clearable filterable
                @change="getMaterialTableData" style="width: 200px; margin-left: 20px;">
                <el-option v-for="item in materialNameOptions" :value="item.value" :label="item.label" />
            </el-select>
            <el-input v-model="searchForm.materialModelSearch" placeholder="材料型号搜索" clearable
                @change="getMaterialTableData" style="width: 200px; margin-left: 20px;" />
            <el-input v-model="searchForm.materialSpecificationSearch" placeholder="材料规格搜索" clearable
                @change="getMaterialTableData" style="width: 200px; margin-left: 20px;" />
            <el-input v-model="searchForm.materialColorSearch" placeholder="材料颜色搜索" clearable
                @change="getMaterialTableData" style="width: 200px; margin-left: 20px;" />
            <el-input v-model="searchForm.orderRIdSearch" placeholder="订单号搜索" clearable
                @change="getMaterialTableData" style="width: 200px; margin-left: 20px;" />
            <el-input v-model="searchForm.shoeRIdSearch" placeholder="工厂型号搜索" clearable
                @change="getMaterialTableData" style="width: 200px; margin-left: 20px;" />
            <el-switch v-model="searchForm.showAllMaterials" inactive-text="有余量库存" active-text="所有库存"
                @change="getMaterialTableData" style="margin-left: 20px;" />
            <el-button type="success" :loading="exportLoading" style="margin-left: 20px;" @click="exportInventory('byOrder')">按订单导出</el-button>
            <el-button type="warning" :loading="exportLoading" style="margin-left: 10px;" @click="exportInventory('aggregate')">不按订单导出</el-button>
        </el-col>
    </el-row>
    <div class="transfer-tables">
        <!-- Top Table -->
        <el-table v-if="readonly === false" ref="topTableData" :data="topTableData"
            style="width: 100%; margin-bottom: 20px; height: 20vh" @selection-change="handleTopSelectionChange"
            @row-dblclick="handleTopRowDblClick" border
            stripe>
            <el-table-column type="selection" width="55" />
            <el-table-column prop="supplierName" label="供应商"></el-table-column>
            <el-table-column prop="warehouseName" label="仓库名"></el-table-column>
            <el-table-column prop="materialName" label="材料名称" width="100">
                <template #default="scope">
                    <el-tooltip effect="dark" :content="scope.row.materialName" placement="bottom">
                        <span class="truncate-text">
                            {{ scope.row.materialName }}
                        </span>
                    </el-tooltip>
                </template>
            </el-table-column>
            <el-table-column prop="materialModel" label="材料型号"></el-table-column>
            <el-table-column prop="materialSpecification" label="材料规格"></el-table-column>
            <el-table-column prop="colorName" label="材料颜色"></el-table-column>
            <el-table-column prop="orderRId" label="订单号"></el-table-column>
            <el-table-column prop="shoeRId" label="工厂鞋型"></el-table-column>
            <el-table-column prop="actualInboundUnit" label="单位"></el-table-column>
            <!-- <el-table-column prop="estimatedInboundAmount" label="采购数量"></el-table-column> -->
            <el-table-column prop="pendingInbound" label="未审核入库数"></el-table-column>
            <el-table-column prop="pendingOutbound" label="未审核出库数"></el-table-column>
            <el-table-column prop="actualInboundAmount" label="已审核入库数"></el-table-column>
            <el-table-column prop="outboundAmount" label="已审核出库数"></el-table-column>
            <el-table-column prop="currentAmount" label="库存"></el-table-column>
        </el-table>

        <!-- Control Buttons -->
        <div v-if="readonly === false" class="transfer-buttons" style="text-align: center; margin-bottom: 20px;">
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
    <el-table ref="bottomTableData" :data="bottomTableData" border stripe style="height: 70vh; width: 100%"
        @selection-change="handleBottomSelectionChange"
        @row-dblclick="handleBottomRowDblClick">
        <el-table-column v-if="readonly === false" type="selection" width="55" />
        <el-table-column prop="supplierName" label="供应商"></el-table-column>
        <el-table-column prop="warehouseName" label="仓库名" width="100"></el-table-column>
        <el-table-column prop="materialName" label="材料名称" width="100">
            <template #default="scope">
                <el-tooltip effect="dark" :content="scope.row.materialName" placement="bottom">
                    <span class="truncate-text">
                        {{ scope.row.materialName }}
                    </span>
                </el-tooltip>
            </template>
        </el-table-column>
        <el-table-column prop="materialModel" label="材料型号"></el-table-column>
        <el-table-column prop="materialSpecification" label="材料规格"></el-table-column>
        <el-table-column prop="colorName" label="材料颜色"></el-table-column>
        <el-table-column prop="orderRId" label="订单号"></el-table-column>
        <el-table-column prop="shoeRId" label="工厂鞋型"></el-table-column>
        <el-table-column prop="actualInboundUnit" label="单位"></el-table-column>
        <el-table-column prop="averagePrice" label="平均价"></el-table-column>
        <!-- <el-table-column prop="estimatedInboundAmount" label="采购数量"></el-table-column> -->
        <el-table-column prop="pendingInbound" label="未审核入库数"></el-table-column>
        <el-table-column prop="pendingOutbound" label="未审核出库数"></el-table-column>
        <el-table-column prop="actualInboundAmount" label="已审核入库数"></el-table-column>
        <el-table-column prop="outboundAmount" label="已审核出库数"></el-table-column>
        <el-table-column prop="currentAmount" label="库存"></el-table-column>
        <el-table-column fixed="right" label="操作" width="120">
            <template #default="scope">
                <el-button-group>
                    <el-button type="primary" size="small" @click="viewSizeMaterialStock(scope.row)">查看多鞋码库存</el-button>
                    <el-button type="primary" size="small" @click="viewRecords(scope.row)">入/出库记录</el-button>
                </el-button-group>
            </template>
        </el-table-column>
    </el-table>
    <el-row :gutter="20">
        <el-col>
            <el-pagination @size-change="handleSizeChange" @current-change="handlePageChange"
                :current-page="currentPage" :page-sizes="[20, 40, 60, 100]" :page-size="pageSize"
                layout="total, sizes, prev, pager, next, jumper" :total="totalRows" />
        </el-col>
    </el-row>

    <el-dialog title="材料入库/出库记录" v-model="isRecordDialogVisible" width="80%" :close="handleDialogClose">
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
                {{ currentRow.actualInboundUnit }}
            </el-descriptions-item>
            <el-descriptions-item label="材料库存">
                {{ currentRow.currentAmount }}
            </el-descriptions-item>

        </el-descriptions>
        <el-tabs>
            <el-tab-pane label="入库记录">
                <el-table :data="materialInboundRecordData" border stripe>
                    <el-table-column prop="inboundRId" label="入库单号"></el-table-column>
                    <el-table-column prop="inboundType" label="用途"></el-table-column>
                    <el-table-column prop="timestamp" label="时间"></el-table-column>
                    <el-table-column prop="unitPrice" label="单价"></el-table-column>
                    <el-table-column prop="inboundAmount" label="数量"></el-table-column>
                    <el-table-column prop="itemTotalPrice" label="金额"></el-table-column>
                    <el-table-column prop="remark" label="备注"></el-table-column>
                    <el-table-column v-for="column in shoeSizeColumns" :key="column.prop" :prop="column.prop"
                        :label="column.label"></el-table-column>
                </el-table>
            </el-tab-pane>
            <el-tab-pane label="出库记录">
                <el-table :data="materialOutboundRecordData" border stripe>
                    <el-table-column prop="outboundRId" label="出库单号"></el-table-column>
                    <el-table-column prop="outboundType" label="用途"></el-table-column>
                    <el-table-column prop="timestamp" label="时间"></el-table-column>
                    <el-table-column prop="unitPrice" label="平均价"></el-table-column>
                    <el-table-column prop="outboundAmount" label="数量"></el-table-column>
                    <el-table-column prop="itemTotalPrice" label="金额"></el-table-column>
                    <el-table-column prop="outboundDestination" label="出库至"></el-table-column>
                    <el-table-column prop="picker" label="领料人"></el-table-column>
                    <el-table-column prop="remark" label="备注"></el-table-column>
                    <el-table-column v-for="column in shoeSizeColumns" :key="column.prop" :prop="column.prop"
                        :label="column.label"></el-table-column>
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
        @update-outbound-form="updateOutboundForm" :outboundOptions="outboundOptions"
        :departmentOptions="departmentOptions" />
</template>
<script>
import axios from 'axios'
import OutboundDialog from './OutboundDialog.vue';
import { ElMessage } from 'element-plus';
import ExcelJS from 'exceljs';
import { saveAs } from 'file-saver';
export default {
    props: {
        readonly: {
            type: Boolean,
            default: true,
        },
        inputSearchParams: {
            type: Object,
            default: {},
        },
    },
    components: {
        OutboundDialog
    },
    data() {
        return {
            role: localStorage.getItem('role'),
            isRecordDialogVisible: false,
            isSizeRecordDialogVisible: false,
            isMaterialDialogVisible: false,
            exportLoading: false,
            searchForm: {
                adminInboundOnly: 0,
                isNonOrderMaterial: 0,
                orderRIdSearch: '',
                shoeRIdSearch: '',
                materialTypeSearch: '',
                materialNameSearch: '',
                materialModelSearch: '',
                materialColorSearch: '',
                materialSpecificationSearch: '',
                materialSupplierSearch: '',
                totalPurchaseOrderRIdSearch: '',
                showAllMaterials: false,
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
            materialOutboundRecordData: [],
            shoeSizeColumns: [],
            selectedRows: [],
            selectedRowsCopy: [],
            outboundForm: {},
            formItemTemplate: {
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
                { label: '材料退回', value: 4 },
                { label: '盘库出库', value: 5 },
            ],
            rules: {
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
    async mounted() {
        console.log("Mounted MaterialStorage")
        console.log("inputSearchParams", this.inputSearchParams)
        this.searchForm = { ...this.searchForm, ...this.inputSearchParams }
        this.getAllMaterialTypes()
        this.getAllSuppliers()
        this.getMaterialNameOptions()
        this.getWarehouseOptions()
        this.getDepartmentOptions()
        await this.getMaterialTableData()
        this.outboundForm = { ...this.formItemTemplate }
        console.log("searchForm", this.searchForm)
    },
    methods: {
        getSelectedData() {
            return this.topTableData;
        },
        // 双击下表某行：选择（移动到上表）
        handleBottomRowDblClick(row) {
            if (this.readonly !== false) return;
            this.topTableData = this.topTableData.concat([row]);
            this.bottomTableData = this.bottomTableData.filter(item => item !== row);
            this.$refs.bottomTableData?.clearSelection?.();
            this.bottomSelected = [];
        },
        // 双击上表某行：移除（移动到下表）
        handleTopRowDblClick(row) {
            if (this.readonly !== false) return;
            this.bottomTableData = this.bottomTableData.concat([row]);
            this.topTableData = this.topTableData.filter(item => item !== row);
            this.$refs.topTableData?.clearSelection?.();
            this.topSelected = [];
        },
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
            const response = await axios.get(`${this.$apiBaseUrl}/logistics/allwarehousenames`)
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
            if (response.data.shoeSizeColumns.length === 0) {
                ElMessage.warning("该材料没有尺码库存信息")
                return
            }
            for (let i = 0; i < response.data.shoeSizeColumns.length; i++) {
                console.log("response.data", response.data[`estimatedInboundAmount${i}`])
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
        handleSearch(values) {
            this.searchForm = { ...values }
            this.getMaterialTableData()
        },
        async getDepartmentOptions() {
            const response = await axios.get(`${this.$apiBaseUrl}/general/getalldepartments`)
            this.departmentOptions = response.data
        },
        async getAllMaterialTypes() {
            const response = await axios.get(`${this.$apiBaseUrl}/logistics/getallmaterialtypes`)
            this.materialTypeOptions = response.data
        },
        async getAllSuppliers() {
            const response = await axios.get(`${this.$apiBaseUrl}/warehouse/warehousemanager/getallsuppliernames`)
            this.materialSupplierOptions = response.data
        },
        async getMaterialTableData() {
            console.log("getMaterialTableData", this.searchForm)
            const params = {
                "page": this.currentPage,
                "pageSize": this.pageSize,
                "materialTypeId": this.searchForm.materialTypeSearch,
                "materialName": this.searchForm.materialNameSearch,
                "materialModel": this.searchForm.materialModelSearch,
                "materialSpec": this.searchForm.materialSpecificationSearch,
                "materialColor": this.searchForm.materialColorSearch,
                "supplier": this.searchForm.materialSupplierSearch,
                "craftName": this.searchForm.craftNameSearch,
                "orderRId": this.searchForm.orderRIdSearch,
                "shoeRId": this.searchForm.shoeRIdSearch,
                "purchaseOrderRId": this.searchForm.totalPurchaseOrderRIdSearch,
                "warehouseName": this.searchForm.warehouseNameSearch,
                "isNonOrderMaterial": this.searchForm.isNonOrderMaterial,
                "adminInboundOnly": this.searchForm.adminInboundOnly,
                "showAllMaterials": this.searchForm.showAllMaterials ? "true" : "false",
            }
            const response = await axios.get(`${this.$apiBaseUrl}/warehouse/warehousemanager/getallmaterialinfo`, { params })
            this.bottomTableData = response.data.result
            this.totalRows = response.data.total
        },
        // 拉取当前筛选条件下的全部库存数据（不分页）
        async fetchAllMaterialData() {
            const params = {
                "page": 1,
                "pageSize": this.totalRows && this.totalRows > 0 ? this.totalRows : 1000000,
                "materialTypeId": this.searchForm.materialTypeSearch,
                "materialName": this.searchForm.materialNameSearch,
                "materialModel": this.searchForm.materialModelSearch,
                "materialSpec": this.searchForm.materialSpecificationSearch,
                "materialColor": this.searchForm.materialColorSearch,
                "supplier": this.searchForm.materialSupplierSearch,
                "craftName": this.searchForm.craftNameSearch,
                "orderRId": this.searchForm.orderRIdSearch,
                "shoeRId": this.searchForm.shoeRIdSearch,
                "purchaseOrderRId": this.searchForm.totalPurchaseOrderRIdSearch,
                "warehouseName": this.searchForm.warehouseNameSearch,
                "isNonOrderMaterial": this.searchForm.isNonOrderMaterial,
                "adminInboundOnly": this.searchForm.adminInboundOnly,
                "showAllMaterials": this.searchForm.showAllMaterials ? "true" : "false",
            }
            const response = await axios.get(`${this.$apiBaseUrl}/warehouse/warehousemanager/getallmaterialinfo`, { params })
            return response.data.result || []
        },
        // mode: 'byOrder' 按订单导出（不汇集）；'aggregate' 不按订单导出（相同材料跨订单汇集）
        async exportInventory(mode) {
            this.exportLoading = true
            try {
                const rows = await this.fetchAllMaterialData()
                if (!rows.length) {
                    ElMessage.warning('无可导出的库存数据')
                    return
                }
                const numeric = ['pendingInbound', 'pendingOutbound', 'actualInboundAmount', 'outboundAmount', 'makeInventoryInbound', 'makeInventoryOutbound', 'currentAmount']
                const num = (v) => Number(v) || 0

                // 收集所有盘库(日期+方向)，每次盘库一列
                const miKeyMap = new Map()
                rows.forEach((r) => {
                    (r.makeInventoryRecords || []).forEach((rec) => {
                        if (!rec.date) return
                        const k = `${rec.direction}|${rec.date}`
                        if (!miKeyMap.has(k)) miKeyMap.set(k, { date: rec.date, direction: rec.direction })
                    })
                })
                const miList = Array.from(miKeyMap.values()).sort((a, b) => {
                    if (a.date !== b.date) return a.date < b.date ? -1 : 1
                    if (a.direction === b.direction) return 0
                    return a.direction === 'in' ? -1 : 1
                })
                const miColDefs = miList.map((c) => ({
                    prop: `mi_${c.direction}_${c.date}`,
                    label: `${c.direction === 'in' ? '盘库入库' : '盘库出库'}\n${c.date}`,
                    width: 13,
                    numeric: true,
                }))
                // 把每次盘库金额按(日期+方向)展开到一个对象
                const miAmounts = (records) => {
                    const m = {};
                    (records || []).forEach((rec) => {
                        if (!rec.date) return
                        const key = `mi_${rec.direction}_${rec.date}`
                        m[key] = (m[key] || 0) + num(rec.amount)
                    })
                    return m
                }

                const suffix = this.buildFilenameSuffix()
                const dateStr = new Date().toLocaleDateString()

                if (mode === 'byOrder') {
                    rows.forEach((r) => Object.assign(r, miAmounts(r.makeInventoryRecords)))
                    const columns = [
                        { prop: 'supplierName', label: '供应商', width: 16 },
                        { prop: 'warehouseName', label: '仓库名', width: 12 },
                        { prop: 'materialName', label: '材料名称', width: 16 },
                        { prop: 'materialModel', label: '材料型号', width: 12 },
                        { prop: 'materialSpecification', label: '材料规格', width: 12 },
                        { prop: 'colorName', label: '材料颜色', width: 10 },
                        { prop: 'orderRId', label: '订单号', width: 14 },
                        { prop: 'shoeRId', label: '工厂鞋型', width: 12 },
                        { prop: 'actualInboundUnit', label: '单位', width: 8 },
                        { prop: 'averagePrice', label: '平均价', width: 10, numeric: true, format: '#,##0.0000' },
                        { prop: 'pendingInbound', label: '未审核入库数', width: 12, numeric: true },
                        { prop: 'pendingOutbound', label: '未审核出库数', width: 12, numeric: true },
                        { prop: 'actualInboundAmount', label: '已审核入库数', width: 12, numeric: true },
                        { prop: 'outboundAmount', label: '已审核出库数', width: 12, numeric: true },
                        { prop: 'makeInventoryInbound', label: '盘库入库合计', width: 12, numeric: true },
                        { prop: 'makeInventoryOutbound', label: '盘库出库合计', width: 12, numeric: true },
                        ...miColDefs,
                        { prop: 'currentAmount', label: '库存', width: 12, numeric: true },
                    ]
                    await this.writeInventoryExcel('总仓库存表（按订单）', columns, rows, `总仓库存_按订单${suffix}_${dateStr}.xlsx`)
                } else {
                    const map = new Map()
                    rows.forEach((r) => {
                        const key = [r.supplierName, r.warehouseName, r.materialName, r.materialModel, r.materialSpecification, r.colorName, r.actualInboundUnit].join('|')
                        if (!map.has(key)) {
                            map.set(key, {
                                supplierName: r.supplierName,
                                warehouseName: r.warehouseName,
                                materialName: r.materialName,
                                materialModel: r.materialModel,
                                materialSpecification: r.materialSpecification,
                                colorName: r.colorName,
                                actualInboundUnit: r.actualInboundUnit,
                                pendingInbound: 0,
                                pendingOutbound: 0,
                                actualInboundAmount: 0,
                                outboundAmount: 0,
                                makeInventoryInbound: 0,
                                makeInventoryOutbound: 0,
                                currentAmount: 0,
                                _miRecords: [],
                                _priceWeight: 0,
                                _priceSum: 0,
                            })
                        }
                        const agg = map.get(key)
                        numeric.forEach((k) => (agg[k] += num(r[k])))
                        if (r.makeInventoryRecords && r.makeInventoryRecords.length) {
                            agg._miRecords.push(...r.makeInventoryRecords)
                        }
                        const w = num(r.actualInboundAmount)
                        agg._priceWeight += w
                        agg._priceSum += num(r.averagePrice) * w
                    })
                    const aggregated = Array.from(map.values()).map((a) => {
                        a.averagePrice = a._priceWeight > 0 ? Number((a._priceSum / a._priceWeight).toFixed(4)) : 0
                        Object.assign(a, miAmounts(a._miRecords))
                        delete a._miRecords
                        delete a._priceWeight
                        delete a._priceSum
                        return a
                    })
                    const columns = [
                        { prop: 'supplierName', label: '供应商', width: 16 },
                        { prop: 'warehouseName', label: '仓库名', width: 12 },
                        { prop: 'materialName', label: '材料名称', width: 16 },
                        { prop: 'materialModel', label: '材料型号', width: 12 },
                        { prop: 'materialSpecification', label: '材料规格', width: 12 },
                        { prop: 'colorName', label: '材料颜色', width: 10 },
                        { prop: 'actualInboundUnit', label: '单位', width: 8 },
                        { prop: 'averagePrice', label: '平均价', width: 10, numeric: true, format: '#,##0.0000' },
                        { prop: 'pendingInbound', label: '未审核入库数', width: 12, numeric: true },
                        { prop: 'pendingOutbound', label: '未审核出库数', width: 12, numeric: true },
                        { prop: 'actualInboundAmount', label: '已审核入库数', width: 12, numeric: true },
                        { prop: 'outboundAmount', label: '已审核出库数', width: 12, numeric: true },
                        { prop: 'makeInventoryInbound', label: '盘库入库合计', width: 12, numeric: true },
                        { prop: 'makeInventoryOutbound', label: '盘库出库合计', width: 12, numeric: true },
                        ...miColDefs,
                        { prop: 'currentAmount', label: '库存', width: 12, numeric: true },
                    ]
                    await this.writeInventoryExcel('总仓库存表（汇总）', columns, aggregated, `总仓库存_汇总${suffix}_${dateStr}.xlsx`)
                }
            } catch (error) {
                console.error(error)
                ElMessage.error('导出失败')
            } finally {
                this.exportLoading = false
            }
        },
        // 根据当前筛选条件生成文件名后缀（去除非法字符）
        buildFilenameSuffix() {
            const f = this.searchForm
            const parts = []
            if (f.warehouseNameSearch) parts.push(f.warehouseNameSearch)
            if (f.materialSupplierSearch) parts.push(f.materialSupplierSearch)
            if (f.materialNameSearch) parts.push(f.materialNameSearch)
            if (f.materialModelSearch) parts.push(f.materialModelSearch)
            if (f.materialSpecificationSearch) parts.push(f.materialSpecificationSearch)
            if (f.materialColorSearch) parts.push(f.materialColorSearch)
            if (f.orderRIdSearch) parts.push(f.orderRIdSearch)
            if (f.shoeRIdSearch) parts.push(f.shoeRIdSearch)
            if (f.totalPurchaseOrderRIdSearch) parts.push(f.totalPurchaseOrderRIdSearch)
            if (f.craftNameSearch) parts.push(f.craftNameSearch)
            const s = parts.join('_').replace(/[\\/:*?"<>|]/g, '').slice(0, 80)
            return s ? `_${s}` : ''
        },
        // 汇总当前筛选条件用于表头展示
        buildFilterSummary() {
            const f = this.searchForm
            const parts = []
            if (f.warehouseNameSearch) parts.push(`仓库:${f.warehouseNameSearch}`)
            if (f.materialSupplierSearch) parts.push(`供应商:${f.materialSupplierSearch}`)
            if (f.materialNameSearch) parts.push(`材料名称:${f.materialNameSearch}`)
            if (f.materialModelSearch) parts.push(`型号:${f.materialModelSearch}`)
            if (f.materialSpecificationSearch) parts.push(`规格:${f.materialSpecificationSearch}`)
            if (f.materialColorSearch) parts.push(`颜色:${f.materialColorSearch}`)
            if (f.orderRIdSearch) parts.push(`订单号:${f.orderRIdSearch}`)
            if (f.shoeRIdSearch) parts.push(`鞋型:${f.shoeRIdSearch}`)
            if (f.totalPurchaseOrderRIdSearch) parts.push(`采购单号:${f.totalPurchaseOrderRIdSearch}`)
            if (f.craftNameSearch) parts.push(`工艺:${f.craftNameSearch}`)
            parts.push(f.showAllMaterials ? '范围:所有库存' : '范围:有余量库存')
            return parts.length ? `筛选条件：${parts.join('  ')}` : '筛选条件：全部'
        },
        async writeInventoryExcel(title, columns, data, filename) {
            const workbook = new ExcelJS.Workbook()
            const sheet = workbook.addWorksheet('库存', {
                views: [{ state: 'frozen', ySplit: 3 }],
                pageSetup: { orientation: 'landscape', fitToPage: true, fitToWidth: 1, fitToHeight: 0 },
            })
            const colCount = columns.length
            sheet.columns = columns.map((c) => ({ key: c.prop, width: c.width || 12 }))

            const thin = { style: 'thin', color: { argb: 'FFB0B0B0' } }
            const allBorder = { top: thin, left: thin, bottom: thin, right: thin }

            // 标题行
            sheet.mergeCells(1, 1, 1, colCount)
            const titleCell = sheet.getCell('A1')
            titleCell.value = title
            titleCell.font = { name: '微软雅黑', size: 16, bold: true, color: { argb: 'FF1F3864' } }
            titleCell.alignment = { horizontal: 'center', vertical: 'middle' }
            sheet.getRow(1).height = 30

            // 副标题：筛选条件 + 导出时间 + 记录数
            sheet.mergeCells(2, 1, 2, colCount)
            const subCell = sheet.getCell('A2')
            subCell.value = `${this.buildFilterSummary()}          导出时间：${new Date().toLocaleString()}          记录数：${data.length}`
            subCell.font = { name: '微软雅黑', size: 10, italic: true, color: { argb: 'FF808080' } }
            subCell.alignment = { horizontal: 'left', vertical: 'middle' }
            sheet.getRow(2).height = 20

            // 表头行
            const headerRow = sheet.getRow(3)
            columns.forEach((c, i) => {
                const cell = headerRow.getCell(i + 1)
                cell.value = c.label
                cell.font = { name: '微软雅黑', size: 11, bold: true, color: { argb: 'FFFFFFFF' } }
                cell.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FF1F3864' } }
                cell.alignment = { horizontal: 'center', vertical: 'middle', wrapText: true }
                cell.border = allBorder
            })
            headerRow.height = 34

            // 数据行
            data.forEach((row, idx) => {
                const excelRow = sheet.getRow(idx + 4)
                columns.forEach((c, i) => {
                    const cell = excelRow.getCell(i + 1)
                    if (c.numeric) {
                        cell.value = Number(row[c.prop]) || 0
                        cell.numFmt = c.format || '#,##0.####'
                        cell.alignment = { horizontal: 'right', vertical: 'middle' }
                    } else {
                        cell.value = row[c.prop] == null ? '' : row[c.prop]
                        cell.alignment = { horizontal: 'left', vertical: 'middle' }
                    }
                    cell.font = { name: '微软雅黑', size: 10 }
                    cell.border = allBorder
                    if (idx % 2 === 1) {
                        cell.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FFF2F6FC' } }
                    }
                })
            })

            // 表头自动筛选
            sheet.autoFilter = { from: { row: 3, column: 1 }, to: { row: 3, column: colCount } }

            const buffer = await workbook.xlsx.writeBuffer()
            saveAs(new Blob([buffer], { type: 'application/octet-stream' }), filename)
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
            let params = { "storageId": row.materialStorageId }
            let response = await axios.get(`${this.$apiBaseUrl}/warehouse/getinboundrecordsformaterial`, { params })
            this.materialInboundRecordData = response.data
            let sizeResponse = await axios.get(`${this.$apiBaseUrl}/warehouse/getoutboundrecordsformaterial`, { params })
            this.materialOutboundRecordData = sizeResponse.data
            if (this.currentRow.shoeSizeColumns) {
                this.shoeSizeColumns = []
                for (let i = 0; i < this.currentRow.shoeSizeColumns.length; i++) {
                    this.shoeSizeColumns.push({
                        prop: `amount${i}`,
                        label: this.currentRow.shoeSizeColumns[i],
                    })
                }
            }
            this.isRecordDialogVisible = true
        },
        handleDialogClose() {
            this.isRecordDialogVisible = false
            this.shoeSizeColumns = []
            this.materialInboundRecordData = []
            this.materialOutboundRecordData = []
        },
    }
}
</script>