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
                    <el-select v-model="outboundForm.outboundType" filterable clearable @change="handleOutboundType" :disabled="lockOutboundType">
                        <el-option v-for="item in outboundOptions" :key="item.value" :value="item.value"
                            :label="item.label"></el-option>
                    </el-select>
                </el-form-item>
                <el-form-item prop="departmentId" label="部门">
                    <el-select v-model="outboundForm.departmentId" filterable clearable>
                        <el-option v-for="item in departmentOptions" :label="item.label"
                            :value="item.value"></el-option>
                    </el-select>
                </el-form-item>
                <el-form-item v-if="[2, 3, 4].includes(outboundForm.outboundType)" prop="supplierName" label="出库厂家">
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
                }" :mouse-config="{ selected: true }" @keydown="handleKeydown" show-overflow style="height: 65vh">
                <vxe-column type="checkbox" width="50"></vxe-column>
                <vxe-column field="warehouseName" title="仓库名" :edit-render="{ autoFocus: true }" width="150">
                    <template #default="{ row }">
                        <span>{{ row.warehouseName }}</span>
                    </template>
                    <template #edit="scope">
                        <el-select v-model="scope.row.warehouseName" filterable clearable :disabled="scope.row.locked">
                            <el-option v-for="item in warehouseOptions" :key="item.orderId" :value="item.value"
                                :label="item.label"></el-option>
                        </el-select>
                    </template>
                </vxe-column>
                <vxe-column v-if="!hideOrderFields" field="orderRId" title="生产订单号" :edit-render="{ autoFocus: true }" width="150">
                    <template #edit="scope">
                        <el-select v-model="scope.row.orderRId" @change="handleOrderRIdSelect(scope.row, $event)"
                            :disabled="scope.row.locked" filterable clearable>
                            <el-option v-for="item in activeOrderShoes" :key="item.orderId" :value="item.orderRId"
                                :label="item.orderRId"></el-option>
                        </el-select>
                    </template>
                </vxe-column>
                <vxe-column v-if="!hideOrderFields" field="shoeRId" title="工厂鞋型" width="150"></vxe-column>
                <vxe-column title="材料名称" field="materialName" width="150" :edit-render="{ autoFocus: true }">
                    <template #default="{ row }">
                        <span>{{ row.materialName }}</span>
                    </template>
                    <template #edit="scope">
                        <el-select v-model="scope.row.materialName" :disabled="scope.row.locked"
                            @change="handleMaterialNameSelect(scope.row, $event)" filterable clearable>
                            <el-option v-for="item in materialNameOptions" :key="item.value" :value="item.value"
                                :label="item.label"></el-option>
                        </el-select>
                    </template>
                </vxe-column>
                <vxe-column field="materialModel" title="材料型号" :edit-render="{ autofocus: '.el-input__inner' }"
                    width="150">
                    <template #edit="{ row }">
                        <el-autocomplete v-model="row.materialModel" :fetch-suggestions="fetchMaterialModels"
                            :disabled="isMaterialModelDisabled(row)" placeholder="输入型号搜索"
                            @change="val => row.materialModel = val" />
                    </template>
                </vxe-column>
                <vxe-column field="materialSpecification" title="材料规格" :edit-render="{ autoFocus: 'input' }"
                    width="200">
                    <template #edit="scope">
                        <vxe-input v-model="scope.row.materialSpecification" clearable
                            :disabled="scope.row.locked"></vxe-input>
                    </template>
                </vxe-column>
                <vxe-column field="materialColor" title="颜色" :edit-render="{ autoFocus: 'input' }" width="150">
                    <template #edit="scope">
                        <vxe-input v-model="scope.row.materialColor" clearable :disabled="scope.row.locked"></vxe-input>
                    </template>
                </vxe-column>
                <vxe-column field="actualInboundUnit" title="计量单位" width="120">
                </vxe-column>
                <vxe-column field="outboundQuantity" title="出库数量" :edit-render="{ autoFocus: 'input' }" width="120">
                    <template #edit="{ row }">
                        <vxe-number-input v-model="row.outboundQuantity" :digits="3" :step="0.001" :min="0"
                            @blur="updateTotalPrice(row)"></vxe-number-input>
                    </template>
                </vxe-column>
                <vxe-column field="unitPrice" title="单价" :edit-render="{ autoFocus: 'input' }" width="120">
                    <template #edit="{ row }">
                        <vxe-number-input v-model="row.unitPrice" type="amount" :min="0" :step="0.0001" :digits="4"
                            @blur="updateTotalPrice(row)" :disabled="outboundForm.outboundType != 4"></vxe-number-input>
                    </template>
                </vxe-column>
                <vxe-column field="itemTotalPrice" title="金额" :edit-render="{ autoFocus: 'input' }" width="120">
                    <template #edit="{ row }">
                        <vxe-number-input v-model="row.itemTotalPrice" type="amount" :min="0" :step="0.0001" :digits="4"
                            :disabled="outboundForm.outboundType != 4"></vxe-number-input>
                    </template>
                </vxe-column>
                <vxe-column field="remark" title="备注" :edit-render="{ autoFocus: 'input' }" width="200">
                    <template #edit="{ row }">
                        <vxe-input v-model="row.remark" clearable></vxe-input>
                    </template>
                </vxe-column>
                <vxe-column title="操作" fixed="right" width="120">
                    <template #default="scope">
                        <vxe-button status="primary" @click="handleSearchMaterial(scope)">搜索材料</vxe-button>
                    </template>
                </vxe-column>
                <vxe-column title="调整鞋码数量" fixed="right" width="120">
                    <template #default="scope">
                        <vxe-button status="primary" @click="openShoeSizesDialog(scope)" :disabled="scope.row.materialType
                            !== '底材' && scope.row.materialType !== '烫底'">打开</vxe-button>
                    </template>
                </vxe-column>
            </vxe-table>
        </el-col>
    </el-row>

        <el-dialog title="搜索材料" v-model="isMaterialSelectDialogVis" fullscreen destroy-on-close @close="handleCloseDialog">
        <MaterialStorage :readonly="false" ref="materialStorageRef" :input-search-params="searchParams" />
        <template #footer>
            <el-button type="primary" @click="confirmUpdateData">确认选择</el-button>
        </template>
    </el-dialog>

    <el-dialog title="出库预览" v-model="isPreviewDialogVis" width="90%" :close-on-click-modal="false" destroy-on-close
        @closed="closePreviewDialog">
        <div id="printView" class="record-print-style">
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
                                <thead>
                                <tr>
                                    <td style="padding:5px; width: 150px;" align="left">供应商:{{
                                        previewOutboundForm.supplierName }}</td>
                                    <td style="padding:5px; width: 300px;" align="left">出库部门:{{
                                        determineDepartment(previewOutboundForm.departmentId) }}
                                    </td>
                                    <td style="padding:5px; width: 300px;" align="left">出库时间:{{
                                        previewOutboundForm.timestamp }}
                                    </td>
                                    <td style="padding:5px; width: 300px;" align="left">出库类型:{{
                                        convertOutboundType(previewOutboundForm.outboundType) }}
                                    </td>
                                </tr>
                                </thead>
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
                                        <th v-if="!hideOrderFields" width="100">订单号</th>
                                        <th v-if="!hideOrderFields" width="100">工厂鞋型</th>
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
                                    <td v-if="!hideOrderFields">{{ item.orderRId }}</td>
                                    <td v-if="!hideOrderFields">{{ item.shoeRId }}</td>
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
                                <span style="padding-right: 10px; width: 150px;">领料人: <span
                                        style="text-decoration: underline;">{{
                                            previewOutboundForm.picker }}</span></span>
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

    <el-dialog title="调整鞋码数量" v-model="isShoeSizeDialogVis" width="80%" destroy-on-close>
        <el-table :data="currentKeyDownRow.shoeSizeTableData" border striped width="100%">
            <el-table-column prop="shoeSizeName" label="鞋码"></el-table-column>
            <el-table-column prop="currentAmount" label="库存"></el-table-column>
            <el-table-column prop="allowedOutboundAmount" label="可出库数量"></el-table-column>
            <el-table-column label="出库数量">
                <template #default="{ row }">
                    <el-input-number v-model="row.outboundQuantity" @change="updateTotalShoes(currentKeyDownRow)"
                        :max="row.allowedOutboundAmount" :min="0"></el-input-number>
                </template>
            </el-table-column>
        </el-table>
        <template #footer>
            <el-button type="primary" @click="isShoeSizeDialogVis = false">确认</el-button>
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
    props: {
        fixedOutboundType: {
            type: Number,
            default: null
        },
        lockOutboundType: {
            type: Boolean,
            default: false
        },
        adminOutboundOnly: {
            type: Boolean,
            default: false
        },
        hideOrderFields: {
            type: Boolean,
            default: false
        }
    },
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
            staffId: localStorage.getItem('staffid'),
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
                warehouseName: '',
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
            isShoeSizeDialogVis: false,
            searchedMaterials: [],
            searchedSizeMaterials: [],
            currentKeyDownRow: null,
            currentIndex: -1,
            isPreviewDialogVis: false,
            rules: {
                outboundType: [{ required: true, message: '请选择出库类型', trigger: 'change' }],
                supplierName: [{ required: true, message: '请输入出库厂家', trigger: 'change' }],
                departmentId: [{ required: true, message: '请选择部门', trigger: 'change' }],
            },
            isOutbounded: 0, // 0: 未出库, 1: 已出库
            outboundOptions: [
                { label: '生产出库', value: 0 },
                { label: '废料处理', value: 1 },
                { label: '外包出库', value: 2 },
                // { label: '复合出库', value: 3 }, # 暂时取消复合出库
                { label: '材料退回', value: 4 },
                { label: '行政出库', value: 6 },
            ],
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
            searchParams: {},
            showMaterialSelectDialog: false,
            departmentOptions: [],
        }
    },
    async mounted() {
        this.getDepartmentOptions()
        this.getMaterialNameOptions()
        this.getWarehouseOptions()
        this.getMaterialTypeOptions();
        this.getMaterialSupplierOptions();
        this.getUnitOptions();
        this.getActiveOrderShoes();
        this.loadLocalStorageData()
        if (this.fixedOutboundType !== null && this.fixedOutboundType !== undefined) {
            this.outboundForm.outboundType = this.fixedOutboundType
        }
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
    },
    methods: {
        async fetchMaterialModels(queryString, cb) {
            const params = { materialModel: queryString }
            const res = await axios.get(`${this.$apiBaseUrl}/warehouse/getallmaterialmodels`, { params })
            cb(res.data)
        },
        isMaterialModelDisabled(row) {
            // 自定义你的禁用条件
            return row.status === '已审核' || row.locked === true
        },
        filterWarehouse() {
            // 面料仓文员
            if (this.staffId == 40) {
                return '面料仓'
            }
            // 底材仓文员
            else if (this.staffId == 41) {
                return '底材仓'
            }
            // 包材仓文员
            else if (this.staffId == 42) {
                return '包材仓'
            }
            return null
        },
        determineDepartment(departmentId) {
            const department = this.departmentOptions.find(item => item.value === departmentId);
            return department ? department.label : '';
        },
        async getDepartmentOptions() {
            const response = await axios.get(`${this.$apiBaseUrl}/general/getalldepartments`)
            this.departmentOptions = response.data
        },
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
                case 5:
                    return '盘库出库';
                case 6:
                    return '行政出库';
                default:
                    return '工厂使用';
            }
        },
        updateCache: debounce(function () {
            const record = {
                outboundForm: this.outboundForm,
                materialTableData: this.materialTableData,
            };
            localStorage.setItem('outboundRecord', JSON.stringify(record));
        }, 300),
        loadLocalStorageData() {
            let outboundRecord = localStorage.getItem('outboundRecord')
            if (outboundRecord) {
                outboundRecord = JSON.parse(outboundRecord)
                this.outboundForm = { ...outboundRecord.outboundForm }
                this.materialTableData = [...outboundRecord.materialTableData]
            } else {
                this.outboundForm = { ...this.outboundFormTemplate }
                this.materialTableData = []
            }
        },
        clearRejectRecord() {
            this.rejectedRecordId = null
            this.outboundForm = { ...this.outboundFormTemplate }
            this.materialTableData = []
        },
        onUpdateSelectedRow(selectedRow) {
            this.rejectedRecordId = selectedRow
        },
        async loadRejectRecord() {
            try {
                let params = { "outboundRecordId": this.rejectedRecordId }
                let response = await axios.get(`${this.$apiBaseUrl}/warehouse/getoutboundrecordbyid`, { params })
                this.outboundForm = response.data.metadata
                this.materialTableData = response.data.items
                console.log(this.materialTableData)
                // insert shoeSizeTableData into newData
                this.createShoeSizeTable(this.materialTableData, 1)
                console.log(this.materialTableData)
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
            // Ctrl + Shift + X to add a new row
            if (event.ctrlKey && event.shiftKey && event.key === 'X') {
                this.addRow()
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
        handleWarehouseIdSelect(row, value) {
            console.log(value)
            row.warehouseName = value
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
        createShoeSizeTable(data, type) {
            // create shoe size table data
            for (let i = 0; i < data.length; i++) {
                let row = data[i]
                let shoeSizeTableData = []
                for (let j = 0; j < row.shoeSizeColumns.length; j++) {
                    let shoeSizeName = row.shoeSizeColumns[j]
                    let outboundQuantity = row[`allowedOutboundAmount${j}`] || 0
                    // if type 1, rejected by accounting
                    if (type == 1) {
                        outboundQuantity = row[`amount${j}`] || 0
                    }
                    let obj = { "shoeSizeName": shoeSizeName, "currentAmount": row[`currentAmount${j}`], "allowedOutboundAmount": outboundQuantity, "outboundQuantity": outboundQuantity }
                    shoeSizeTableData.push(obj)
                }
                row.shoeSizeTableData = shoeSizeTableData
            }
        },
        confirmUpdateData() {
            let temp = JSON.parse(JSON.stringify(this.materialTableData))
            const data = this.$refs.materialStorageRef.getSelectedData?.();
            for (let row of data) {
                row.outboundQuantity = row.allowedOutboundAmount
            }
            let newData = data.map(item => {
                let newItem = { ...item }
                newItem.id = XEUtils.uniqueId()
                newItem.itemTotalPrice = (newItem.outboundQuantity * newItem.unitPrice).toFixed(4)
                return newItem
            })
            // insert shoeSizeTableData into newData
            this.createShoeSizeTable(newData, 0)
            temp.push(...newData)
            temp.splice(this.currentIndex, 1)
            this.materialTableData = JSON.parse(JSON.stringify(temp))
            // 遍历table，把有materialStorageId的行锁定
            for (let i = 0; i < this.materialTableData.length; i++) {
                let row = this.materialTableData[i]
                if (row.materialStorageId) {
                    row.locked = true
                } else {
                    row.locked = false
                }
            }
            this.handleCloseDialog();
        },
        openShoeSizesDialog(scope) {
            this.currentKeyDownRow = scope.row
            this.isShoeSizeDialogVis = true
        },
        handleOutboundType(value) {
            this.outboundForm.outboundType = value
            if (value == 0) {
                this.rules.departmentId = [{ required: true, message: '此项为必填项', trigger: 'change' }]
                this.rules.supplierName = []
            }
            else if (value == 6) {
                this.rules.departmentId = []
                this.rules.supplierName = []
            }
            else {
                this.rules.departmentId = []
                this.rules.supplierName = [
                    { required: true, message: '此项为必填项', trigger: 'change' },
                ]
            }
        },
        async getMaterialNameOptions() {
            let response = await axios.get(`${this.$apiBaseUrl}/logistics/getallmaterialname`)
            this.materialNameOptions = response.data
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
            let table = row.shoeSizeTableData
            for (let i = 0; i < table.length; i++) {
                let element = table[i]
                if (element.outboundQuantity === undefined || element.outboundQuantity === null) {
                    element.outboundQuantity = 0
                }
                total += Number(element.outboundQuantity)
            }
            row.outboundQuantity = total
            row.itemTotalPrice = (total * row.unitPrice).toFixed(4)
        },
        addRow() {
            const newRow = { "id": XEUtils.uniqueId(), ...JSON.parse(JSON.stringify(this.rowTemplate)) };
            newRow.warehouseName = this.filterWarehouse()
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
            this.fetchMaterialData()
            this.showMaterialSelectDialog = true
            this.isMaterialSelectDialogVis = true
        },
        async fetchMaterialData() {
            const params = {
                "warehouseNameSearch": this.currentKeyDownRow.warehouseName,
                "orderRIdSearch": this.hideOrderFields ? null : this.currentKeyDownRow.orderRId,
                "materialNameSearch": this.currentKeyDownRow.materialName,
                "materialSpecSearch": this.currentKeyDownRow.materialSpecification,
                "materialModelSearch": this.currentKeyDownRow.materialModel,
                "materialColorSearch": this.currentKeyDownRow.materialColor,
                "supplierNameSearch": this.outboundForm.supplierName,
            }
            if (this.adminOutboundOnly) {
                params.adminInboundOnly = 1
                params.isNonOrderMaterial = 1
            }
            this.searchParams = params; // Update search parameters
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
            // create amount{i}, amount0 means the first shoe size, amount1 means the second shoe size
            for (let i = 0; i < this.materialTableData.length; i++) {
                let row = this.materialTableData[i]
                for (let j = 0; j < row.shoeSizeTableData.length; j++) {
                    row[`amount${j}`] = row.shoeSizeTableData[j].outboundQuantity
                }
                if (this.hideOrderFields) {
                    row.orderRId = null
                    row.shoeRId = null
                }
            }
            const params = {
                outboundRecordId: this.outboundForm.outboundRecordId,
                outboundType: this.outboundForm.outboundType,
                supplierName: this.outboundForm.supplierName,
                remark: this.outboundForm.remark,
                items: this.materialTableData,
                departmentId: this.outboundForm.departmentId,
                picker: this.outboundForm.picker,
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
                this.isPreviewDialogVis = false;
                window.location.reload()
            }
        },
    },
}
</script>
