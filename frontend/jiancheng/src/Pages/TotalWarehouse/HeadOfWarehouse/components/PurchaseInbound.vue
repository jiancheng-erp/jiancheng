<template>
    <el-row :gutter="20">
        <el-col :span="24">
            <el-button type="primary" @click="addRow">新增一行</el-button>
            <el-button type="warning" @click="copyRows">批量复制</el-button>
            <el-button type="danger" @click="deleteRows">批量删除</el-button>
            <el-button type="success" @click="confirmAndProceed">确认入库</el-button>
            <el-button type="primary" @click="openOrderMaterialQuery">订单材料查询</el-button>
            <el-button type="warning" @click="loadReject">加载驳回入库单</el-button>
            <el-input v-if="inboundForm.inboundRecordId" v-model="inboundForm.inboundRId" disabled style="width:250px">
                <template #append>
                    <el-button @click="clearRejectRecord">取消编辑</el-button>
                </template>
            </el-input>
        </el-col>
    </el-row>
    <el-row :gutter="20">
        <el-col>
            <el-form :inline="true" :model="inboundForm" class="demo-form-inline" :rules="rules" ref="inboundForm">
                <el-form-item prop="supplierName" label="厂家名称">
                    <el-autocomplete v-model="inboundForm.supplierName" :fetch-suggestions="querySuppliers" clearable
                        @select="handleSupplierSelect" />
                </el-form-item>
                <el-form-item prop="inboundType" label="入库类型">
                    <el-select v-model="inboundForm.inboundType" filterable clearable @change="handleInboundType">
                        <el-option v-for="item in inboundOptions" :key="item.value" :value="item.value"
                            :label="item.label"></el-option>
                    </el-select>
                </el-form-item>
                <el-form-item prop="materialTypeId" label="材料类型">
                    <el-select v-model="inboundForm.materialTypeId" filterable clearable @change="getWarehouseName">
                        <el-option v-for="item in materialTypeOptions" :key="item.materialTypeId"
                            :value="item.materialTypeId" :label="item.materialTypeName"></el-option>
                    </el-select>
                </el-form-item>
                <el-form-item prop="remark" label="备注">
                    <el-input v-model="inboundForm.remark"></el-input>
                </el-form-item>
                <el-form-item prop="shoeSizes" label="码段">
                    <el-select v-model="inboundForm.shoeSizes" filterable clearable @change="insertShoeSizeColumns">
                        <el-option v-for="item in logisticsShoeSizes" :key="item.batchInfoTypeId"
                            :value="item.batchInfoTypeId" :label="item.batchInfoTypeName">
                        </el-option>
                    </el-select>
                </el-form-item>
                <el-form-item prop="payMethod" label="结算方式">
                    <el-select v-model="inboundForm.payMethod" filterable clearable>
                        <el-option v-for="item in ['应付账款', '现金']" :key="item" :value="item" :label="item"></el-option>
                    </el-select>
                </el-form-item>
            </el-form>
        </el-col>

    </el-row>
    <el-row :gutter="20">
        <el-col :span="24">
            <vxe-table :data="materialTableData" ref="tableRef" border :edit-config="{ mode: 'cell', trigger: 'click' }"
                :row-config="{ keyField: 'id', isHover: true }" :column-config="{ resizable: true }" :keyboard-config="{
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
                <vxe-column field="orderRId" title="生产订单号" :edit-render="{ autoFocus: true }" width="150">
                    <template #edit="scope">
                        <el-select v-model="scope.row.orderRId" @change="handleOrderRIdSelect(scope.row, $event)"
                            filterable clearable>
                            <el-option v-for="item in activeOrderShoes" :key="item.orderId" :value="item.orderRId"
                                :label="item.orderRId"></el-option>
                        </el-select>
                    </template>
                </vxe-column>
                <vxe-column field="shoeRId" title="工厂鞋型" :edit-render="{ autoFocus: 'input' }" width="150">
                    <template #edit="scope">
                        <vxe-input v-model="scope.row.shoeRId" clearable></vxe-input>
                    </template>
                </vxe-column>
                <vxe-column title="材料名称" field="materialName" width="150" :edit-render="{ autoFocus: true }">
                    <template #default="{ row }">
                        <span>{{ row.materialName }}</span>
                    </template>
                    <template #edit="scope">
                        <el-select v-model="scope.row.materialName"
                            @change="handleMaterialNameSelect(scope.row, $event)" filterable clearable>
                            <el-option v-for="item in filteredMaterialNameOptions" :key="item.value" :value="item.value"
                                :label="item.label"></el-option>
                        </el-select>
                    </template>
                </vxe-column>
                <vxe-column field="inboundModel" title="材料型号" :edit-render="inboundModelRender" width="150">

                </vxe-column>
                <!-- <vxe-column field="inboundModel" title="材料型号" :edit-render="{ autoFocus: 'input' }" width="150">
                    <template #edit="scope">
                        <vxe-input v-model="scope.row.inboundModel" clearable></vxe-input>
                    </template>
                </vxe-column> -->
                <vxe-column field="inboundSpecification" title="材料规格" :edit-render="{ autoFocus: 'input' }" width="200">
                    <template #edit="scope">
                        <vxe-input v-model="scope.row.inboundSpecification" clearable></vxe-input>
                    </template>
                </vxe-column>
                <vxe-column field="materialColor" title="颜色" :edit-render="{ autoFocus: 'input' }" width="150">
                    <template #edit="scope">
                        <vxe-input v-model="scope.row.materialColor" clearable></vxe-input>
                    </template>
                </vxe-column>
                <vxe-column field="actualInboundUnit" title="计量单位" :edit-render="{ autoFocus: true }" width="120">
                    <template #default="{ row }">
                        <span>{{ row.actualInboundUnit }}</span>
                    </template>
                    <template #edit="scope">
                        <el-select v-model="scope.row.actualInboundUnit" filterable clearable>
                            <el-option v-for="item in unitOptions" :key="item.value" :value="item.value"
                                :label="item.label"></el-option>
                        </el-select>
                    </template>
                </vxe-column>
                <vxe-column field="inboundQuantity" title="入库数量" :edit-render="{ autoFocus: 'input' }" width="120">
                    <template #edit="{ row }">
                        <vxe-number-input v-model="row.inboundQuantity" :digits="3" :step="0.001" :min="0"
                            @blur="updateTotalPrice(row)"></vxe-number-input>
                    </template>
                </vxe-column>
                <vxe-column field="unitPrice" title="采购单价" :edit-render="{ autoFocus: 'input' }" width="120">
                    <template #edit="{ row }">
                        <vxe-number-input v-model="row.unitPrice" type="amount" :min="0" :step="0.0001" :digits="4"
                            :disabled="inboundForm.inboundType == 1" @blur="updateTotalPrice(row)"></vxe-number-input>
                    </template>
                </vxe-column>
                <vxe-column field="itemTotalPrice" title="采购金额" :edit-render="{ autoFocus: 'input' }" width="120">
                    <template #edit="{ row }">
                        <vxe-number-input v-model="row.itemTotalPrice" type="amount" :min="0" :step="0.0001" :digits="4"
                            :disabled="inboundForm.inboundType == 1"></vxe-number-input>
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

    <MaterialSelectDialog :visible="isMaterialSelectDialogVis" :searchedMaterials="searchedMaterials"
        @confirm="updateMaterialTableData" @update-visible="updateDialogVisible" />

    <SizeMaterialSelectDialog :visible="isSizeMaterialSelectDialogVis"
        :searched-size-materials="searchedSizeMaterials"
        @confirm="updateSizeMaterialTableData" @update-visible="updateSizeMaterialDialogVisible" />

    <el-dialog title="入库预览" v-model="isPreviewDialogVis" width="90%" :close-on-click-modal="false" destroy-on-close
        @closed="closePreviewDialog">
        <div id="printView">
            <table style="width:100%; border-collapse: collapse;">
                <thead>
                    <tr>
                        <td>
                            <div style="position: relative; padding: 5px;">
                                <h2 style="margin: 0; text-align: center; font-size: 24px;">健诚鞋业入库单</h2>
                                <span
                                    style="position: absolute; right: 0; top: 50%; transform: translateY(-50%); font-weight: bolder; font-size: 16px;">
                                    单据编号:{{ previewInboundForm.inboundRId }}
                                </span>
                            </div>
                            <table class="table" border="0pm" cellspacing="0" align="left" width="100%"
                                style="font-size: 16px;margin-bottom: 10px; table-layout:fixed;word-wrap:break-word;word-break:break-all">
                                <tr>
                                    <td style="padding:5px; width: 150px;" align="left">供应商:{{
                                        previewInboundForm.supplierName }}</td>
                                    <td style="padding:5px; width: 150px;" align="left">仓库名称:{{
                                        previewInboundForm.warehouseName }}</td>
                                    <td style="padding:5px; width: 300px;" align="left">入库时间:{{
                                        previewInboundForm.timestamp }}
                                    </td>
                                    <td style="padding:5px; width: 150px;" align="left">结算方式:{{
                                        previewInboundForm.payMethod
                                    }}</td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                </thead>

                <tbody>
                    <tr>
                        <td>
                            <table class="yk-table" border="1pm" cellspacing="0" align="center" width="100%"
                                style="max-height: 360px; font-size: 16px; table-layout:fixed;word-wrap:break-word;word-break:break-all">
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
                                    <td>{{ item.inboundModel }}</td>
                                    <td>{{ item.inboundSpecification }}</td>
                                    <td>{{ item.materialColor }}</td>
                                    <td>{{ item.actualInboundUnit }}</td>
                                    <td>{{ item.orderRId }}</td>
                                    <td>{{ item.shoeRId }}</td>
                                    <td>{{ item.inboundQuantity }}</td>
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
                                    calculateInboundTotal }}</span></span>
                                <span style="padding-right: 10px;">合计金额: <span style="text-decoration: underline;">{{
                                    calculateTotalPriceSum }}</span></span>
                                <span style="padding-right: 10px;">备注: <span style="text-decoration: underline;">{{
                                    previewInboundForm.remark }}</span></span>
                            </div>
                        </td>
                    </tr>
                </tfoot>
            </table>
        </div>
        <template #footer>
            <el-button type="primary" v-print="'#printView'">打印</el-button>
            <!-- <el-button type="primary"
                @click="downloadPDF(`健诚鞋业入库单${inboundForm.inboundRId}`, `printView`)">下载PDF</el-button> -->
            <el-button v-if="isInbounded == 0 && inboundForm.inboundRecordId" type="primary"
                @click="submitInboundForm">确认修改</el-button>
            <el-button v-else-if="isInbounded == 0" type="primary" @click="submitInboundForm">入库</el-button>
        </template>
    </el-dialog>
    <OrderMaterialQuery :visible="isOrderMaterialQueryVis" @update-visible="updateOrderMaterialQueryVis" />
    <el-dialog :title="`${currentRow.orderRId}材料数量信息`" v-model="isMaterialLogisticVis" fullscreen destroy-on-close>
        <OrderStatusPage :order-info="{ 'orderRId': currentRow.orderRId, 'shoeRId': currentRow.shoeRId }" />
        <OrderMaterialsPage :current-row="{ 'orderRId': currentRow.orderRId, 'shoeRId': currentRow.shoeRId }" />
        <template #footer>
            <span>
                <el-button type="primary" @click="isMaterialLogisticVis = false">返回</el-button>
            </span>
        </template>
    </el-dialog>

    <el-dialog title="选择入库单" v-model="rejectedPage" fullscreen destroy-on-close>
        <InboundRecords :material-supplier-options="materialSupplierOptions" :warehouse-options="warehouseOptions"
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
import htmlToPdf from '@/Pages/utils/htmlToPdf';
import { updateTotalPriceHelper } from '@/Pages/utils/warehouseFunctions';
import MaterialSelectDialog from './MaterialSelectDialog.vue';
import OrderMaterialQuery from './OrderMaterialQuery.vue';
import OrderMaterialsPage from '@/Pages/ProductionManagementDepartment/ProductionSharedPages/OrderMaterialsPage.vue';
import { debounce, reject, update } from 'lodash';
import OrderStatusPage from './OrderStatusPage.vue';
import InboundRecords from './InboundRecords.vue';
import SizeMaterialSelectDialog from './SizeMaterialSelectDialog.vue';
import XEUtils from 'xe-utils'
export default {
    components: {
        MaterialSearchDialog,
        MaterialSelectDialog,
        OrderMaterialQuery,
        OrderMaterialsPage,
        OrderStatusPage,
        InboundRecords,
        SizeMaterialSelectDialog
    },
    data() {
        return {
            materialTableData: [],
            previewInboundForm: {},
            inboundForm: {},
            inboundFormTemplate: {
                supplierName: null,
                materialTypeId: null,
                inboundType: 0,
                inboundRId: '',
                remark: '',
                shoeSizes: null,
                payMethod: '应付账款',
                warehouseName: null,
                warehouseId: null,
            },
            rowTemplate: {
                materialName: '',
                materialModel: '',
                materialSpecification: '',
                materialColor: '',
                materialCraftName: '',
                inboundQuantity: 0,
                unitPrice: 0,
                inboundModel: '',
                inboundSpecification: '',
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
                supplierName: [
                    {
                        required: true,
                        validator: (rule, value, callback) => {
                            if ((value === undefined || value === null || value.trim() === '') && this.inboundForm.inboundType != 1) {
                                callback(new Error('此项为必填项'));
                            } else {
                                callback();
                            }
                        },
                        trigger: 'change'
                    },
                ],
                inboundType: [
                    { required: true, message: '此项为必填项', trigger: 'change' },
                ],
                materialTypeId: [
                    { required: true, message: '此项为必填项', trigger: 'change' },
                ],
            },
            isInbounded: 0, // 0: 未入库, 1: 已入库
            inboundOptions: [
                { label: '采购入库', value: 0 },
                { label: '生产剩余', value: 1 },
            ],
            shoeSizeColumns: [],
            previewData: [],
            logisticsShoeSizes: [],
            materialNameOptions: [],
            filteredOrders: [],
            isOrderMaterialQueryVis: false,
            materialTypeOptions: [],
            materialSupplierOptions: [],
            unitOptions: [],
            activeOrderShoes: [],
            isMaterialLogisticVis: false,
            currentRow: {},
            rejectedPage: false,
            rejectedRecordId: null,
            rejectRecordData: [],
            warehouseOptions: [],
            inboundModelRender: {
                name: 'ElAutocomplete',
                props: {
                    fetchSuggestions: async function (queryString, cb) {
                        let params = {
                            materialModel: queryString,
                        }
                        const response = await axios.get(`${this.$apiBaseUrl}/warehouse/getallmaterialmodels`, { params });
                        cb(response.data);
                    }.bind(this)
                },
                events: {
                    change: function (row, selected) {
                        row.inboundModel = selected;
                    }
                }
            }
        }
    },
    // beforeUnmount() {
    //     window.removeEventListener('keydown', this.handleKeydown)
    // },
    async mounted() {
        // window.addEventListener('keydown', this.handleKeydown)
        this.getMaterialNameOptions()
        this.getWarehouseOptions()
        this.loadLocalStorageData()
        this.getMaterialTypeOptions();
        this.getMaterialSupplierOptions();
        this.getUnitOptions();
        this.getActiveOrderShoes();
        await this.getLogisticsShoeSizes()
    },
    watch: {
        inboundForm: {
            handler() {
                this.updateCache();
                this.clearShoeSizeColumns();
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
        calculateInboundTotal() {
            // Calculate the total inbound quantity
            const number = this.previewData.reduce((total, item) => {
                return total + (Number(item.inboundQuantity) || 0);
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
            return this.materialNameOptions.filter(item => item.type == this.inboundForm.materialTypeId)
        },
    },
    methods: {
        clearShoeSizeColumns() {
            if (!(this.inboundForm.materialTypeId == 7 && this.inboundForm.materialTypeId == 16)) {
                this.shoeSizeColumns = []
            }
        },
        clearRejectRecord() {
            this.rejectedRecordId = null
            this.inboundForm = { ...this.inboundFormTemplate }
            this.materialTableData = []
            this.shoeSizeColumns = []
        },
        onUpdateSelectedRow(selectedRow) {
            this.rejectedRecordId = selectedRow
        },
        async loadRejectRecord() {
            try {
                let params = { "inboundRecordId": this.rejectedRecordId }
                let response = await axios.get(`${this.$apiBaseUrl}/warehouse/getinboundrecordbyid`, { params })
                console.log(response.data)
                this.inboundForm = response.data.metadata
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
                ElMessage.error('获取入库单详情失败')
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
            let activeCell = this.$refs.tableRef.getEditRecord()
            if ($event.key === 'F4' && activeCell && activeCell.row) {
                if (!activeCell.row.orderRId) {
                    ElMessage.warning("未输入订单号")
                    return false
                }
                this.currentRow = activeCell.row
                this.isMaterialLogisticVis = true
            }
        },
        customeEnterMethod(params) {
            const rowIndex = params.rowIndex;
            const column = params.column;
            if (rowIndex == this.materialTableData.length - 1) {
                this.addRow()
                // Assume you have a ref to the table
                const $table = this.$refs.tableRef;

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
        openOrderMaterialQuery() {
            this.isOrderMaterialQueryVis = true
        },
        updateOrderMaterialQueryVis(value) {
            this.isOrderMaterialQueryVis = value
        },
        updateCache: debounce(function () {
            const record = {
                inboundForm: this.inboundForm,
                materialTableData: this.materialTableData,
                shoeSizeColumns: this.shoeSizeColumns
            };
            localStorage.setItem('inboundRecord', JSON.stringify(record));
        }, 300),
        loadLocalStorageData() {
            let inboundRecord = localStorage.getItem('inboundRecord')
            if (inboundRecord) {
                inboundRecord = JSON.parse(inboundRecord)
                this.inboundForm = { ...inboundRecord.inboundForm }
                this.materialTableData = [...inboundRecord.materialTableData]
                this.shoeSizeColumns = [...inboundRecord.shoeSizeColumns]
            } else {
                this.inboundForm = { ...this.inboundFormTemplate }
                this.materialTableData = []
                this.shoeSizeColumns = []
            }
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
        updateMaterialTableData(value) {
            this.searchedMaterials = []
            let temp = [...this.materialTableData, ...value]
            temp.splice(this.currentIndex, 1)
            this.materialTableData = [...temp]
            this.currentIndex = null
        },
        updateSizeMaterialTableData(value) {
            this.searchedSizeMaterials = []
            let temp = [...this.materialTableData, ...value]
            temp.splice(this.currentIndex, 1)
            this.materialTableData = [...temp]
            this.currentIndex = null
            let firstItem = this.materialTableData[0]
            let sizeColumns = []
            for (let i = 0; i < firstItem.shoeSizeColumns.length; i++) {
                let obj = { "label": firstItem.shoeSizeColumns[i], "prop": `amount${i}` }
                sizeColumns.push(obj)
            }
            this.shoeSizeColumns = sizeColumns
        },
        updateDialogVisible(value) {
            this.isMaterialSelectDialogVis = value
        },
        updateSizeMaterialDialogVisible(value) {
            this.isSizeMaterialSelectDialogVis = value
        },
        handleInboundType(value) {
            this.inboundForm.inboundType = value
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
                materialTypeId: this.inboundForm.materialTypeId,
            }
            let response = await axios.get(`${this.$apiBaseUrl}/logistics/getwarehousebymaterialtypeid`, { params })
            this.inboundForm.warehouseName = response.data.warehouseName
            this.inboundForm.warehouseId = response.data.warehouseId
        },
        querySuppliers(queryString, callback) {
            const results = this.materialSupplierOptions
                .filter((item) => item.toLowerCase().includes(queryString.toLowerCase()))
                .map((item) => ({ value: item }));

            callback(results);
        },
        handleSupplierSelect(item) {
            this.inboundForm.supplierName = item.value;
        },
        async getLogisticsShoeSizes() {
            const response = await axios.get(`${this.$apiBaseUrl}/batchtype/getallbatchtypeslogistics`)
            this.logisticsShoeSizes = response.data.batchDataTypes
        },
        insertShoeSizeColumns() {
            let selectedShoeSize = this.logisticsShoeSizes.filter((item) => item.batchInfoTypeId == this.inboundForm.shoeSizes)[0]
            let tempTable = []

            if (selectedShoeSize) {
                let length = Object.keys(selectedShoeSize).filter(key => key.startsWith("size")).length;
                for (let i = 0; i < length; i++) {
                    let db_size = i + 34
                    let size_name = selectedShoeSize[`size${db_size}Name`]
                    if (size_name === null) {
                        break
                    }
                    let obj = {
                        "label": size_name,
                        "prop": `amount${i}`
                    }
                    tempTable.push(obj)

                }
            }

            this.shoeSizeColumns = [...tempTable]
        },
        updateTotalShoes(row) {
            let total = 0
            for (let i = 0; i < this.shoeSizeColumns.length; i++) {
                if (row[this.shoeSizeColumns[i].prop] === undefined) {
                    row[this.shoeSizeColumns[i].prop] = 0
                }
                total += Number(row[this.shoeSizeColumns[i].prop])
            }
            row.inboundQuantity = total
            row.itemTotalPrice = (total * row.unitPrice).toFixed(4)
        },
        determineInboundName(type) {
            if (type == 0) {
                return '采购入库'
            } else if (type == 1) {
                return '生产剩余'
            } else if (type == 2) {
                return '复合入库'
            } else {
                return '未知'
            }
        },
        addRow() {
            const newRow = { "id": XEUtils.uniqueId(), ...JSON.parse(JSON.stringify(this.rowTemplate)) };
            this.materialTableData.push(newRow)
        },
        copyRows() {
            const selectedRows = this.$refs.tableRef.getCheckboxRecords();
            const clones = selectedRows.map(row => {
                const { id, ...rest } = row
                return { ...rest, id: XEUtils.uniqueId() }
            })
            this.materialTableData.push(...clones)
        },
        deleteRows() {
            const selectedRows = this.$refs.tableRef.getCheckboxRecords();
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
            row.itemTotalPrice = updateTotalPriceHelper(row)
        },
        async handleSearchMaterial(scope) {
            if (this.inboundForm.inboundType != 1 && this.inboundForm.supplierName == null) {
                ElMessage.warning('请填写厂家名称')
                return
            }
            if (this.inboundForm.materialTypeId == null) {
                ElMessage.warning('请填写材料类型')
                return
            }
            this.currentKeyDownRow = scope.row; // Store the current row
            this.currentIndex = scope.rowIndex; // Store the current row index
            if (this.inboundForm.materialTypeId == 7 || this.inboundForm.materialTypeId == 16) {
                await this.fetchSizeMaterialData()
                this.isSizeMaterialSelectDialogVis = true
            }
            else {
                this.fetchMaterialData()
                this.isMaterialSelectDialogVis = true
            }
        },
        async fetchMaterialData() {
            const params = {
                "materialName": this.currentKeyDownRow.materialName,
                "materialSpec": this.currentKeyDownRow.inboundSpecification,
                "materialModel": this.currentKeyDownRow.inboundModel,
                "materialColor": this.currentKeyDownRow.materialColor,
                "supplier": this.inboundForm.supplierName,
            }
            const response = await axios.get(`${this.$apiBaseUrl}/warehouse/getmaterials`, { params })
            this.searchedMaterials = response.data
            // add unique id to each row
            this.searchedMaterials.forEach(item => {
                item.id = XEUtils.uniqueId()
            })
        },
        async fetchSizeMaterialData() {
            const params = {
                "materialName": this.currentKeyDownRow.materialName,
                "materialSpec": this.currentKeyDownRow.inboundSpecification,
                "materialModel": this.currentKeyDownRow.inboundModel,
                "materialColor": this.currentKeyDownRow.materialColor,
                "supplier": this.inboundForm.supplierName,
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
            if (!(row.materialName === '大底')) {
                this.shoeSizeColumns = []
            }
        },
        async submitInboundForm() {
            for (let i = 0; i < this.materialTableData.length; i++) {
                if (this.materialTableData[i].shoeSizeColumns == null) {
                    this.materialTableData[i].shoeSizeColumns = this.materialTableData[0].shoeSizeColumns
                }
            }
            const params = {
                inboundRecordId: this.inboundForm.inboundRecordId,
                inboundType: this.inboundForm.inboundType,
                supplierName: this.inboundForm.supplierName,
                warehouseId: this.inboundForm.warehouseId,
                remark: this.inboundForm.remark,
                items: this.materialTableData,
                batchInfoTypeId: this.inboundForm.shoeSizes,
                payMethod: this.inboundForm.payMethod,
                materialTypeId: this.inboundForm.materialTypeId,
            }
            try {
                let response = null
                if (this.inboundForm.inboundRecordId) {
                    response = await axios.put(`${this.$apiBaseUrl}/warehouse/updateinboundrecord`, params)
                }
                else {
                    response = await axios.post(`${this.$apiBaseUrl}/warehouse/inboundmaterial`, params)
                }
                this.previewInboundForm.timestamp = response.data.inboundTime
                this.previewInboundForm.inboundRId = response.data.inboundRId
                this.isInbounded = 1
                ElMessage.success('入库成功')
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
                let string = `${obj.orderRId}-${obj.materialName}-${obj.inboundModel}-${obj.inboundSpecification}-${obj.materialColor}-${obj.actualInboundUnit}-${obj.unitPrice}`
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
            this.$refs.inboundForm.validate((valid) => {
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
                    this.previewInboundForm = JSON.parse(JSON.stringify(this.inboundForm))
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
            if (this.isInbounded == 1) {
                this.isInbounded = 0
                this.materialTableData = []
                localStorage.removeItem('inboundRecord')
                this.inboundForm = JSON.parse(JSON.stringify(this.inboundFormTemplate))
                this.shoeSizeColumns = []
                this.isPreviewDialogVis = false;
                window.location.reload()
            }
        },
        downloadPDF(title, domName) {
            htmlToPdf.getPdf(title, domName);
        },
    },
}
</script>
<style>
.demo-form-inline .el-input {
    --el-input-width: 220px;
}

.demo-form-inline .el-select {
    --el-select-width: 220px;
}

.radio-class .el-radio__label {
    display: none;
}
</style>

<style>
/* 确保表头固定和分页逻辑 */
/* Print styles */
@media print {
    @page {
        margin: 20mm;
    }

    thead {
        display: table-header-group;
    }

    tfoot {
        display: table-footer-group;
    }

    /* Optional: Avoid breaking inside rows */
    tr {
        page-break-inside: avoid;
    }
}
</style>

<style scoped>
#printView {
    padding-left: 20px;
    padding-right: 20px;
    color: black;
    font-family: SimHei;
}
</style>
