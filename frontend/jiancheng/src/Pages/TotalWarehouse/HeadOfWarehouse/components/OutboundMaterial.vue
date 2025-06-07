<template>
    <el-row :gutter="20">
        <el-col :span="24">
            <el-button type="primary" @click="addRow">新增一行</el-button>
            <el-button type="warning" @click="copyRows">批量复制</el-button>
            <el-button type="danger" @click="deleteRows">批量删除</el-button>
            <el-button type="success" @click="confirmAndProceed">确认出库</el-button>
            <el-button type="warning" @click="loadReject">加载驳回出库单</el-button>
            <el-input v-if="outboundForm.outboundRecordId" v-model="outboundForm.outboundRId" disabled
                style="width:250px">
                <template #append>
                    <el-button @click="clearRejectRecord">取消编辑</el-button>
                </template>
            </el-input>
        </el-col>
    </el-row>
    <el-row :gutter="20">
        <el-col>
            <el-form :inline="true" :model="outboundForm" :rules="rules" ref="outboundForm">
                <el-form-item prop="outboundType" label="出库类型">
                    <el-select v-model="outboundForm.outboundType" filterable clearable @change="handleOutboundType">
                        <el-option v-for="item in outboundOptions" :key="item.value" :value="item.value"
                            :label="item.label"></el-option>
                    </el-select>
                </el-form-item>
                <el-form-item prop="materialTypeId" label="材料类型">
                    <el-select v-model="outboundForm.materialTypeId" filterable clearable @change="getWarehouseName">
                        <el-option v-for="item in materialTypeOptions" :key="item.materialTypeId"
                            :value="item.materialTypeId" :label="item.materialTypeName"></el-option>
                    </el-select>
                </el-form-item>
                <el-form-item v-if="outboundForm.outboundType == 0" prop="departmentId"
                    label="部门">
                    <el-select v-model="outboundForm.departmentId" filterable clearable>
                        <el-option v-for="item in departmentOptions" :label="item.label"
                            :value="item.value"></el-option>
                    </el-select>
                </el-form-item>
                <el-form-item v-if="[2, 3, 4].includes(outboundForm.outboundType)"
                    prop="supplierName" label="出库厂家">
                    <el-autocomplete v-model="outboundForm.supplierName" :fetch-suggestions="querySuppliers" clearable
                        @select="handleSupplierSelect" />
                </el-form-item>
                <el-form-item prop="picker" label="领料人">
                    <el-input v-model="outboundForm.picker"></el-input>
                </el-form-item>
                <el-form-item prop="remark" label="备注">
                    <el-input v-model="outboundForm.remark"></el-input>
                </el-form-item>
            </el-form>
        </el-col>

    </el-row>
    <el-row :gutter="20">
        <el-col :span="24">
            <vxe-table :data="materialTableData" ref="outboundTableRef" border
                :edit-config="{ mode: 'cell', trigger: 'click' }" :row-config="{ keyField: 'id', isHover: true }"
                :column-config="{ resizable: true }" :keyboard-config="{
                    isEdit: true,
                    isArrow: true,
                    isEnter: true,
                    isTab: true,
                    isDel: true,
                    isBack: true,
                    isEsc: true,
                    editMode: 'insert',
                    enterMethod: customeEnterMethod,
                }" :mouse-config="{ selected: true }" @keydown="handleKeydown" show-overflow height="500">
                <vxe-column type="checkbox" width="50"></vxe-column>
                <vxe-column field="orderRId" title="生产订单号" width="150"></vxe-column>
                <vxe-column field="shoeRId" title="工厂鞋型" width="150"></vxe-column>
                <vxe-column title="材料名称" field="materialName" width="150"></vxe-column>
                <vxe-column field="materialModel" title="材料型号" width="150"></vxe-column>
                <vxe-column field="materialSpecification" title="材料规格" width="200"></vxe-column>
                <vxe-column field="materialColor" title="颜色" width="150"></vxe-column>
                <vxe-column field="actualInboundUnit" title="计量单位" :edit-render="{ autoFocus: true }"
                    width="120"></vxe-column>
                <vxe-column field="outboundQuantity" title="出库数量" :edit-render="{ autoFocus: 'input' }" width="120">
                    <template #edit="{ row }">
                        <vxe-number-input v-model="row.outboundQuantity" :digits="3" :step="0.001" :min="0"
                            @blur="updateTotalPrice(row)"></vxe-number-input>
                    </template>
                </vxe-column>
                <vxe-column field="unitPrice" title="采购单价" :edit-render="{ autoFocus: 'input' }" width="120">
                    <template #edit="{ row }">
                        <vxe-number-input v-model="row.unitPrice" type="amount" :min="0" :step="0.0001" :digits="4"
                            @blur="updateTotalPrice(row)" :disabled="outboundForm.outboundType != 4"></vxe-number-input>
                    </template>
                </vxe-column>
                <vxe-column field="itemTotalPrice" title="采购金额" :edit-render="{ autoFocus: 'input' }" width="120">
                    <template #edit="{ row }">
                        <vxe-number-input v-model="row.itemTotalPrice" type="amount" :min="0" :step="0.0001"
                            :digits="4" :disabled="outboundForm.outboundType != 4"></vxe-number-input>
                    </template>
                </vxe-column>
                <vxe-column field="remark" title="备注" :edit-render="{ autoFocus: 'input' }" width="200">
                    <template #edit="{ row }">
                        <vxe-input v-model="row.remark" clearable></vxe-input>
                    </template>
                </vxe-column>
                <vxe-column v-for="item in shoeSizeColumns" :field="item.prop" :title="item.label"
                    :edit-render="{ autoFocus: 'input' }" width="120">
                    <template #edit="{ row }">
                        <vxe-number-input v-model="row[item.prop]" type="integer" clearable
                            @change="updateTotalShoes(row)" :min="0"></vxe-number-input>
                    </template>
                </vxe-column>
                <vxe-column title="操作" fixed="right" width="100">
                    <template #default="scope">
                        <vxe-button status="primary" @click="handleSearchMaterial(scope)">搜索材料</vxe-button>
                    </template>
                </vxe-column>
            </vxe-table>
        </el-col>
    </el-row>

    <el-dialog title="搜索材料" v-model="isMaterialSelectDialogVis" fullscreen destroy-on-close @close="handleCloseDialog">
        <MaterialStorage :readonly="false" ref="materialStorageRef"
            :input-search-params="{ materialSupplierSearch: outboundForm.supplierName, materialTypeSearch: outboundForm.materialTypeId }" />
        <template #footer>
            <el-button type="primary" @click="confirmUpdateData">确认选择</el-button>
        </template>
    </el-dialog>

    <el-dialog title="出库预览" v-model="isPreviewDialogVis" width="90%" :close-on-click-modal="false" destroy-on-close
        @closed="closePreviewDialog">
        <div id="printView">
            <table style="width:100%; border-collapse: collapse;">
                <thead>
                    <tr>
                        <td>
                            <div style="position: relative; padding: 5px;">
                                <h2 style="margin: 0; text-align: center; font-size: 24px;">健诚鞋业出库单</h2>
                                <span
                                    style="position: absolute; right: 0; top: 50%; transform: translateY(-50%); font-weight: bolder; font-size: 16px;">
                                    单据编号:{{ previewOutboundForm.outboundRId }}
                                </span>
                            </div>
                            <table class="table" border="0pm" cellspacing="0" align="left" width="100%"
                                style="font-size: 16px;margin-bottom: 10px; table-layout:fixed;word-wrap:break-word;word-break:break-all">
                                <tr>
                                    <td style="padding:5px; width: 150px;" align="left">供应商:{{
                                        previewOutboundForm.supplierName }}</td>
                                    <td style="padding:5px; width: 150px;" align="left">仓库名称:{{
                                        previewOutboundForm.warehouseName }}</td>
                                    <td style="padding:5px; width: 300px;" align="left">出库时间:{{
                                        previewOutboundForm.timestamp }}
                                    </td>
                                    <td style="padding:5px; width: 300px;" align="left">出库类型:{{
                                        convertOutboundType(previewOutboundForm.outboundType) }}
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                </thead>

                <tbody>
                    <tr>
                        <td>
                            <table class="inner-table" border="1" cellspacing="0" align="center" width="100%"
                                style="border-collapse: collapse; border-spacing: 0; table-layout: fixed; word-wrap: break-word; word-break: break-all;">
                                <thead>
                                    <tr>
                                        <th width="100">材料名</th>
                                        <th width="100">型号</th>
                                        <th width="180">规格</th>
                                        <th width="80">颜色</th>
                                        <th width="55">单位</th>
                                        <th width="100">订单号</th>
                                        <th width="100">工厂鞋型</th>
                                        <th width="90">数量</th>
                                        <th width="90">单价</th>
                                        <th width="100">金额</th>
                                        <th>备注</th>
                                    </tr>
                                </thead>
                                <tr v-for="(item, index) in previewData" :key="index" align="center">
                                    <td>{{ item.materialName }}</td>
                                    <td>{{ item.materialModel }}</td>
                                    <td>{{ item.materialSpecification }}</td>
                                    <td>{{ item.materialColor }}</td>
                                    <td>{{ item.actualInboundUnit }}</td>
                                    <td>{{ item.orderRId }}</td>
                                    <td>{{ item.shoeRId }}</td>
                                    <td>{{ item.outboundQuantity }}</td>
                                    <td>{{ item.unitPrice }}</td>
                                    <td>{{ item.itemTotalPrice }}</td>
                                    <td>{{ item.remark }}</td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                </tbody>
                <tfoot>
                    <tr>
                        <td>
                            <div style="margin-top: 20px; font-size: 16px; font-weight: bold;display: flex;">
                                <span style="padding-right: 10px;">合计数量: <span style="text-decoration: underline;">{{
                                    calculateOutboundTotal }}</span></span>
                                <span style="padding-right: 10px;">合计金额: <span style="text-decoration: underline;">{{
                                    calculateTotalPriceSum }}</span></span>
                                <span style="padding-right: 10px;">备注: <span style="text-decoration: underline;">{{
                                    previewOutboundForm.remark }}</span></span>
                            </div>
                        </td>
                    </tr>
                </tfoot>
            </table>
        </div>
        <template #footer>
            <el-button type="primary" v-print="'#printView'">打印</el-button>
            <el-button v-if="isOutbounded == 0 && outboundForm.outboundRecordId" type="primary"
                @click="submitOutboundForm">确认修改</el-button>
            <el-button v-else-if="isOutbounded == 0" type="primary" @click="submitOutboundForm">出库</el-button>
        </template>
    </el-dialog>

    <el-dialog title="选择出库单" v-model="rejectedPage" fullscreen destroy-on-close>
        <OutboundRecords :material-supplier-options="materialSupplierOptions" :warehouse-options="warehouseOptions"
            :load-reject="true" @update-selected-row="onUpdateSelectedRow" />
        <template #footer>
            <span>
                <el-button type="primary" @click="rejectedPage = false">返回</el-button>
                <el-button type="primary" @click="loadRejectRecord">确认</el-button>
            </span>
        </template>
    </el-dialog>
</template>
<script>
import axios from 'axios';
import { ElMessage, ElMessageBox } from 'element-plus';
import MaterialSearchDialog from './MaterialSearchDialog.vue';
import { updateTotalPriceHelperForOutbound } from '@/Pages/utils/warehouseFunctions';
import MaterialSelectDialog from './MaterialSelectDialog.vue';
import OrderMaterialQuery from './OrderMaterialQuery.vue';
import OrderMaterialsPage from '@/Pages/ProductionManagementDepartment/ProductionSharedPages/OrderMaterialsPage.vue';
import { debounce, reject, update } from 'lodash';
import OrderStatusPage from './OrderStatusPage.vue';
import OutboundRecords from './OutboundRecords.vue';
import SizeMaterialSelectDialog from './SizeMaterialSelectDialog.vue';
import XEUtils from 'xe-utils'
import MaterialStorage from './MaterialStorage.vue';
export default {
    components: {
        MaterialSearchDialog,
        MaterialSelectDialog,
        OrderMaterialQuery,
        OrderMaterialsPage,
        OrderStatusPage,
        OutboundRecords,
        SizeMaterialSelectDialog,
        MaterialStorage
    },
    data() {
        return {
            materialTableData: [],
            previewOutboundForm: {},
            outboundForm: {},
            outboundFormTemplate: {
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
            rowTemplate: {
                materialName: '',
                materialModel: '',
                materialSpecification: '',
                materialColor: '',
                materialCraftName: '',
                outboundQuantity: 0,
                unitPrice: 0,
                materialModel: '',
                materialSpecification: '',
                orderRId: null,
                shoeRId: null
            },
            isMaterialSelectDialogVis: false,
            isSizeMaterialSelectDialogVis: false,
            searchedMaterials: [],
            searchedSizeMaterials: [],
            currentKeyDownRow: null,
            currentIndex: -1,
            isPreviewDialogVis: false,
            rules: {
                outboundType: [{ required: true, message: '请选择出库类型', trigger: 'change' }],
                supplierName: [{ required: true, message: '请输入出库厂家', trigger: 'change' }],
                departmentId: [{ required: true, message: '请选择部门', trigger: 'change' }],
                materialTypeId: [{ required: true, message: '请选择材料类型', trigger: 'change' }],
            },
            isOutbounded: 0, // 0: 未出库, 1: 已出库
            outboundOptions: [
                { label: '工厂使用', value: 0 },
                { label: '废料处理', value: 1 },
                { label: '外包发货', value: 2 },
                { label: '外发复合', value: 3 },
                { label: '材料退回', value: 4 },
            ],
            shoeSizeColumns: [],
            previewData: [],
            materialNameOptions: [],
            filteredOrders: [],
            materialTypeOptions: [],
            materialSupplierOptions: [],
            unitOptions: [],
            activeOrderShoes: [],
            currentRow: {},
            rejectedPage: false,
            rejectedRecordId: null,
            rejectRecordData: [],
            warehouseOptions: [],
            searchParams: {
                orderId: null,
                materialName: null,
                materialSpec: null,
                materialModel: null,
                materialColor: null,
                supplier: null
            },
            showMaterialSelectDialog: false,
        }
    },
    async mounted() {
        this.getMaterialNameOptions()
        this.getWarehouseOptions()
        this.getMaterialTypeOptions();
        this.getMaterialSupplierOptions();
        this.getUnitOptions();
        this.getActiveOrderShoes();
        this.loadLocalStorageData()
    },
    watch: {
        outboundForm: {
            handler() {
                this.updateCache();
            },
            deep: true
        },
        materialTableData: {
            handler() {
                this.updateCache();
            },
            deep: true
        }
    },
    computed: {
        calculateOutboundTotal() {
            // Calculate the total outbound quantity
            const number = this.previewData.reduce((total, item) => {
                return total + (Number(item.outboundQuantity) || 0);
            }, 0);
            return Number(number).toFixed(2);
        },
        calculateTotalPriceSum() {
            // Calculate the total price
            const total = this.previewData.reduce((total, item) => {
                return total + (Number(item.itemTotalPrice) || 0);
            }, 0);
            return Number(total).toFixed(4);
        },
        filteredMaterialNameOptions() {
            return this.materialNameOptions.filter(item => item.type == this.outboundForm.materialTypeId)
        },
    },
    methods: {
        convertOutboundType(value) {
            switch (value) {
                case 0:
                    return '工厂使用';
                case 1:
                    return '废料处理';
                case 2:
                    return '外包发货';
                case 3:
                    return '外发复合';
                case 4:
                    return '材料退回';
                default:
                    return '工厂使用';
            }
        },
        updateCache: debounce(function () {
            const record = {
                outboundForm: this.outboundForm,
                materialTableData: this.materialTableData,
                shoeSizeColumns: this.shoeSizeColumns
            };
            localStorage.setItem('outboundRecord', JSON.stringify(record));
        }, 300),
        loadLocalStorageData() {
            let outboundRecord = localStorage.getItem('outboundRecord')
            if (outboundRecord) {
                outboundRecord = JSON.parse(outboundRecord)
                this.outboundForm = { ...outboundRecord.outboundForm }
                this.materialTableData = [...outboundRecord.materialTableData]
                this.shoeSizeColumns = [...outboundRecord.shoeSizeColumns]
            } else {
                this.outboundForm = { ...this.outboundFormTemplate }
                this.materialTableData = []
                this.shoeSizeColumns = []
            }
        },
        clearRejectRecord() {
            this.rejectedRecordId = null
            this.outboundForm = { ...this.outboundFormTemplate }
            this.materialTableData = []
            this.shoeSizeColumns = []
        },
        onUpdateSelectedRow(selectedRow) {
            this.rejectedRecordId = selectedRow
        },
        async loadRejectRecord() {
            try {
                let params = { "outboundRecordId": this.rejectedRecordId }
                let response = await axios.get(`${this.$apiBaseUrl}/warehouse/getoutboundrecordbyid`, { params })
                console.log(response.data)
                this.outboundForm = response.data.metadata
                this.materialTableData = response.data.items
                let firstItem = response.data.items[0]
                let sizeColumns = []
                for (let i = 0; i < firstItem.shoeSizeColumns.length; i++) {
                    let obj = { "label": firstItem.shoeSizeColumns[i], "prop": `amount${i}` }
                    sizeColumns.push(obj)
                }
                this.shoeSizeColumns = sizeColumns
            }
            catch (error) {
                console.log(error)
                ElMessage.error('获取出库单详情失败')
            }
            this.rejectedPage = false
            console.log(this.rejectedRecordId)
        },
        async getWarehouseOptions() {
            const response = await axios.get(`${this.$apiBaseUrl}/logistics/allwarehousenames`)
            this.warehouseOptions = response.data
        },
        loadReject() {
            this.rejectedPage = true
        },
        handleKeydown($event) {
            // let activeCell = this.$refs.outboundTableRef.getEditRecord()
            // if ($event.key === 'F4' && activeCell && activeCell.row) {
            //     if (!activeCell.row.orderRId) {
            //         ElMessage.warning("未输出订单号")
            //         return false
            //     }
            //     this.currentRow = activeCell.row
            //     this.isMaterialLogisticVis = true
            // }
        },
        customeEnterMethod(params) {
            const rowIndex = params.rowIndex;
            const column = params.column;
            if (rowIndex == this.materialTableData.length - 1) {
                this.addRow()
                // Assume you have a ref to the table
                const $table = this.$refs.outboundTableRef;

                // Get current active cell
                this.$nextTick(() => {
                    const nextRow = $table.getData()[rowIndex + 1];
                    $table.setEditCell(nextRow, column);
                    $table.clearEdit();
                });
                return false
            }
        },
        async getMaterialTypeOptions() {
            const response = await axios.get(`${this.$apiBaseUrl}/logistics/getallmaterialtypes`)
            this.materialTypeOptions = response.data
        },
        async getMaterialSupplierOptions() {
            const response = await axios.get(`${this.$apiBaseUrl}/warehouse/warehousemanager/getallsuppliernames`)
            this.materialSupplierOptions = response.data
        },
        async getUnitOptions() {
            const response = await axios.get(`${this.$apiBaseUrl}/logistics/getallunit`)
            this.unitOptions = response.data
        },
        async getActiveOrderShoes() {
            const response = await axios.get(`${this.$apiBaseUrl}/order/getactiveordershoes`)
            this.activeOrderShoes = response.data
        },
        handleOrderRIdSelect(row, value) {
            // console.log(value)
            const resultShoeRIds = this.activeOrderShoes.filter(item => item.orderRId == value)
            if (resultShoeRIds.length == 0) {
                row.shoeRId = null
                return
            }
            row.orderId = resultShoeRIds[0].orderId
            row.shoeRId = resultShoeRIds[0].shoeRId
        },
        // handleShoeRIdSelect(row, value) {
        //     if (value == null || value == '') {
        //         this.filteredOrders = [...this.activeOrderShoes]
        //         return
        //     }
        //     this.filteredOrders = this.activeOrderShoes.filter(item => item.shoeRId.includes(value))
        // },
        // getFilteredShoes(row, event) {
        //     if (row.shoeRId == null || row.shoeRId == '') {
        //         this.filteredOrders = [...this.activeOrderShoes]
        //         return
        //     }
        //     this.filteredOrders = this.activeOrderShoes.filter(item => item.shoeRId.includes(row.shoeRId))
        // },
        handleCloseDialog() {
            this.isMaterialSelectDialogVis = false;
        },
        confirmUpdateData() {
            const data = this.$refs.materialStorageRef.getSelectedData?.();
            this.materialTableData = data;
            console.log("Selected data:", data);
            this.handleCloseDialog();
        },
        updateMaterialTableData(value) {
            let temp = JSON.parse(JSON.stringify(this.materialTableData))
            temp.push(...value)
            temp.splice(this.currentIndex, 1)
            this.materialTableData = JSON.parse(JSON.stringify(temp))
            this.currentIndex = null
        },
        updateSizeMaterialTableData(value) {
            // deep copy materialTableData and append value
            let temp = JSON.parse(JSON.stringify(this.materialTableData))
            temp.push(...value)
            temp.splice(this.currentIndex, 1)
            this.materialTableData = JSON.parse(JSON.stringify(temp))
            this.currentIndex = null
            let firstAutoAssignItem = value[0]
            let sizeColumns = []
            for (let i = 0; i < firstAutoAssignItem.shoeSizeColumns.length; i++) {
                let obj = { "label": firstAutoAssignItem.shoeSizeColumns[i], "prop": `amount${i}` }
                sizeColumns.push(obj)
            }
            this.shoeSizeColumns = sizeColumns
        },
        updateDialogVisible(value) {
            this.showMaterialSelectDialog = value
            this.isMaterialSelectDialogVis = value
        },
        updateSizeMaterialDialogVisible(value) {
            this.isSizeMaterialSelectDialogVis = value
        },
        handleOutboundType(value) {
            this.outboundForm.outboundType = value
            if (value == 1) {
                this.rules.supplierName = []
            } else {
                this.rules.supplierName = [
                    { required: true, message: '此项为必填项', trigger: 'change' },
                ]
            }
        },
        async getMaterialNameOptions() {
            let response = await axios.get(`${this.$apiBaseUrl}/logistics/getallmaterialname`)
            this.materialNameOptions = response.data
        },
        async getWarehouseName() {
            let params = {
                materialTypeId: this.outboundForm.materialTypeId,
            }
            let response = await axios.get(`${this.$apiBaseUrl}/logistics/getwarehousebymaterialtypeid`, { params })
            this.outboundForm.warehouseName = response.data.warehouseName
            this.outboundForm.warehouseId = response.data.warehouseId
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
        updateTotalShoes(row) {
            let total = 0
            for (let i = 0; i < this.shoeSizeColumns.length; i++) {
                if (row[this.shoeSizeColumns[i].prop] === undefined) {
                    row[this.shoeSizeColumns[i].prop] = 0
                }
                total += Number(row[this.shoeSizeColumns[i].prop])
            }
            row.outboundQuantity = total
            row.itemTotalPrice = (total * row.unitPrice).toFixed(4)
        },
        addRow() {
            const newRow = { "id": XEUtils.uniqueId(), ...JSON.parse(JSON.stringify(this.rowTemplate)) };
            this.materialTableData.push(newRow)
        },
        copyRows() {
            const selectedRows = this.$refs.outboundTableRef.getCheckboxRecords();
            const clones = selectedRows.map(row => {
                const { id, ...rest } = row
                return { ...rest, id: XEUtils.uniqueId() }
            })
            this.materialTableData.push(...clones)
        },
        deleteRows() {
            const selectedRows = this.$refs.outboundTableRef.getCheckboxRecords();
            if (selectedRows.length === 0) {
                ElMessage.warning('请先选择要删除的行');
                return;
            }
            ElMessageBox.confirm('确定要删除选中的行吗？', '提示', {
                type: 'warning',
                showCancelButton: true,
                cancelButtonText: '取消',
                confirmButtonText: '确定',
            }).then(() => {
                this.materialTableData = this.materialTableData.filter(row => !selectedRows.includes(row));
                ElMessage.success('删除成功');
            }).catch(() => {
                ElMessage.info('已取消删除');
            });
        },
        updateTotalPrice(row) {
            row.itemTotalPrice = updateTotalPriceHelperForOutbound(row)
        },
        async handleSearchMaterial(scope) {
            this.currentKeyDownRow = scope.row; // Store the current row
            this.currentIndex = scope.rowIndex; // Store the current row index
            if (this.outboundForm.materialTypeId == 7 || this.outboundForm.materialTypeId == 16) {
                await this.fetchSizeMaterialData()
                this.isSizeMaterialSelectDialogVis = true
            }
            else {
                this.fetchMaterialData()
                this.showMaterialSelectDialog = true
                this.isMaterialSelectDialogVis = true
            }
        },
        async fetchMaterialData() {
            const params = {
                "orderRId": this.currentKeyDownRow.orderRId,
                "materialName": this.currentKeyDownRow.materialName,
                "materialSpec": this.currentKeyDownRow.materialSpecification,
                "materialModel": this.currentKeyDownRow.materialModel,
                "materialColor": this.currentKeyDownRow.materialColor,
                "supplier": this.outboundForm.supplierName,
            }
            this.searchParams = params; // Update search parameters
        },
        async fetchSizeMaterialData() {
            const params = {
                "materialName": this.currentKeyDownRow.materialName,
                "materialSpec": this.currentKeyDownRow.materialSpecification,
                "materialModel": this.currentKeyDownRow.materialModel,
                "materialColor": this.currentKeyDownRow.materialColor,
                "supplier": this.outboundForm.supplierName,
            }
            const response = await axios.get(`${this.$apiBaseUrl}/warehouse/getsizematerials`, { params })
            this.searchedSizeMaterials = response.data
            // add unique id to each row
            this.searchedSizeMaterials.forEach(item => {
                item.id = XEUtils.uniqueId()
            })
        },
        async handleMaterialNameSelect(row, value) {
            if (value == null || value == '') {
                return
            }
            let temp = this.materialNameOptions.filter(item => item.value == value)[0]
            row.actualInboundUnit = temp.unit
            row.materialCategory = temp.materialCategory
        },
        async submitOutboundForm() {
            for (let i = 0; i < this.materialTableData.length; i++) {
                if (this.materialTableData[i].shoeSizeColumns == null) {
                    this.materialTableData[i].shoeSizeColumns = this.materialTableData[0].shoeSizeColumns
                }
            }
            const params = {
                outboundRecordId: this.outboundForm.outboundRecordId,
                outboundType: this.outboundForm.outboundType,
                supplierName: this.outboundForm.supplierName,
                warehouseId: this.outboundForm.warehouseId,
                remark: this.outboundForm.remark,
                items: this.materialTableData,
                materialTypeId: this.outboundForm.materialTypeId,
            }
            try {
                let response = null
                if (this.outboundForm.outboundRecordId) {
                    response = await axios.put(`${this.$apiBaseUrl}/warehouse/updateoutboundrecord`, params)
                }
                else {
                    response = await axios.post(`${this.$apiBaseUrl}/warehouse/outboundmaterial`, params)
                }
                this.previewOutboundForm.timestamp = response.data.outboundTime
                this.previewOutboundForm.outboundRId = response.data.outboundRId
                this.isOutbounded = 1
                ElMessage.success('出库成功')
            } catch (error) {
                if (error.response) {
                    // Flask returns error in JSON format
                    this.errorMessage = error.response.data.message || "An error occurred";
                } else {
                    this.errorMessage = "服务器异常";
                }
                ElMessage.error(this.errorMessage)
                console.error("API Error:", error);
            }
        },
        async confirmAndProceed() {
            let duplicateCheck = false
            let seen = new Set()
            for (const obj of this.materialTableData) {
                let string = `${obj.orderRId}-${obj.materialName}-${obj.materialModel}-${obj.materialSpecification}-${obj.materialColor}-${obj.actualInboundUnit}-${obj.unitPrice}`
                if (seen.has(string)) {
                    duplicateCheck = true
                    break
                }
                seen.add(string)
            }
            if (duplicateCheck) {
                try {
                    await ElMessageBox.confirm('有材料信息重复，是否继续？', '确认', {
                        confirmButtonText: '是',
                        cancelButtonText: '否',
                        type: 'warning'
                    });

                    this.openPreviewDialog();

                } catch (error) {
                    console.log('User cancelled. Stop here.');
                }
            }
            else {
                // Proceed to next code block
                this.openPreviewDialog();
            }
        },
        openPreviewDialog() {
            this.$refs.outboundForm.validate((valid) => {
                if (this.materialTableData.length == 0) {
                    ElMessage.warning('请至少添加一行材料')
                    return
                }
                for (let i = 0; i < this.materialTableData.length; i++) {
                    if (this.materialTableData[i].materialName == null || this.materialTableData[i].materialName == '') {
                        ElMessage.warning('请填写所有必填项')
                        return
                    }
                }
                if (valid) {
                    this.previewData = JSON.parse(JSON.stringify(this.materialTableData))
                    this.previewOutboundForm = JSON.parse(JSON.stringify(this.outboundForm))
                    for (let i = 0; i < this.previewData.length; i++) {
                        let item = this.previewData[i]
                        // trim and upper the orderRId
                        if (item.orderRId != null) {
                            item.orderRId = item.orderRId.trim().toUpperCase();
                        }
                        if (item.shoeRId != null) {
                            item.shoeRId = item.shoeRId.trim().toUpperCase();
                        }
                        if (item.materialModel != null) {
                            item.materialModel = item.materialModel.trim();
                        }
                        if (item.materialSpecification != null) {
                            item.materialSpecification = item.materialSpecification.trim();
                        }
                        if (item.materialColor != null) {
                            item.materialColor = item.materialColor.trim();
                        }
                    }
                    this.isPreviewDialogVis = true;
                } else {
                    ElMessage.warning('请填写所有必填项')
                }
            })
        },
        closePreviewDialog() {
            this.previewData = []
            if (this.isOutbounded == 1) {
                this.isOutbounded = 0
                this.materialTableData = []
                localStorage.removeItem('outboundRecord')
                this.outboundForm = JSON.parse(JSON.stringify(this.outboundFormTemplate))
                this.shoeSizeColumns = []
                this.isPreviewDialogVis = false;
                window.location.reload()
            }
        },
    },
}
</script>
