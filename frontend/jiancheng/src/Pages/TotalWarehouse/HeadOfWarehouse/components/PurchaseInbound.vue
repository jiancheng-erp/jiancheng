<template>
    <el-row :gutter="20">
        <el-col :span="24">
            <el-button type="primary" @click="addRow">新增一行</el-button>
            <el-button type="danger" @click="deleteRows">批量删除</el-button>
            <el-button type="success" @click="openPreviewDialog">确认入库</el-button>
        </el-col>
    </el-row>
    <el-row :gutter="20">
        <el-col>
            <el-form :inline="true" :model="inboundForm" class="demo-form-inline" :rules="rules" ref="inboundForm">
                <el-form-item prop="currentDateTime" label="日期">
                    <el-date-picker v-model="inboundForm.currentDateTime" type="datetime"
                        value-format="YYYY-MM-DD HH:mm:ss" clearable />
                </el-form-item>
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
                    <el-select v-model="inboundForm.materialTypeId" filterable clearable
                        @change="getMaterialNameOptions">
                        <el-option v-for="item in materialTypeOptions" :key="item.materialTypeId"
                            :value="item.materialTypeId" :label="item.materialTypeName"></el-option>
                    </el-select>
                </el-form-item>
                <el-form-item prop="remark" label="备注">
                    <el-input v-model="inboundForm.remark"></el-input>
                </el-form-item>
                <!-- <el-form-item prop="shoeSize" label="码段">
                    <el-select v-model="inboundForm.shoeSize" filterable clearable @change="insertShoeSizeColumns">
                        <el-option v-for="item in logisticsShoeSizes" :key="item.batchInfoTypeId"
                            :value="item.batchInfoTypeId" :label="item.batchInfoTypeName">
                        </el-option>
                    </el-select>
                </el-form-item> -->
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
            <vxe-table :data="materialTableData" ref="tableRef" border :edit-config="{ mode: 'row', trigger: 'click' }"
                :column-config="{ resizable: true }" :row-config="{ resizable: true, isHover: true }" show-overflow>
                <vxe-column type="checkbox" width="50"></vxe-column>
                <vxe-column field="orderRId" title="生产订单号" :edit-render="{ autoFocus: 'input' }" width="150">
                    <template #edit="scope">
                        <vxe-input v-model="scope.row.orderRId" clearable :disabled="scope.row.disableEdit"
                            @keydown="(event) => handleKeydown(event, scope)"></vxe-input>
                    </template>
                </vxe-column>
                <vxe-column field="shoeRId" title="工厂鞋型" :edit-render="{ autoFocus: 'input' }" width="150">
                    <template #edit="scope">
                        <vxe-input v-model="scope.row.shoeRId" clearable :disabled="scope.row.disableEdit"
                            @keydown="(event) => handleKeydown(event, scope)"></vxe-input>
                    </template>
                </vxe-column>
                <vxe-column title="材料名称" field="materialName" width="150" :edit-render="{}">
                    <template #default="{ row }">
                        <span>{{ row.materialName }}</span>
                    </template>
                    <template #edit="scope">
                        <el-select v-model="scope.row.materialName" :disabled="scope.row.disableEdit"
                            @change="handleMaterialNameSelect(scope.row, $event)" filterable clearable>
                            <el-option v-for="item in materialNameOptions" :key="item.value" :value="item.value"
                                :label="item.label"></el-option>
                        </el-select>
                    </template>
                </vxe-column>
                <vxe-column field="inboundModel" title="材料型号" :edit-render="{ autoFocus: 'input' }" width="150">
                    <template #edit="scope">
                        <vxe-input v-model="scope.row.inboundModel" clearable
                            @keydown="(event) => handleKeydown(event, scope)"></vxe-input>
                    </template>
                </vxe-column>
                <vxe-column field="inboundSpecification" title="材料规格" :edit-render="{ autoFocus: 'input' }" width="200">
                    <template #edit="scope">
                        <vxe-input v-model="scope.row.inboundSpecification" clearable
                            @keydown="(event) => handleKeydown(event, scope)"></vxe-input>
                    </template>
                </vxe-column>
                <vxe-column field="materialColor" title="颜色" :edit-render="{ autoFocus: 'input' }" width="150">
                    <template #edit="scope">
                        <vxe-input v-model="scope.row.materialColor" clearable
                            :disabled="scope.row.disableEdit"></vxe-input>
                    </template>
                </vxe-column>
                <vxe-column field="actualInboundUnit" title="计量单位" :edit-render="{ autoFocus: 'input' }" width="120">
                    <template #default="{ row }">
                        <span>{{ row.actualInboundUnit }}</span>
                    </template>
                    <template #edit="scope">
                        <el-select v-model="scope.row.actualInboundUnit" filterable clearable
                            :disabled="scope.row.disableEdit">
                            <el-option v-for="item in unitOptions" :key="item.value" :value="item.value"
                                :label="item.label"></el-option>
                        </el-select>
                    </template>
                </vxe-column>
                <vxe-column field="inboundQuantity" title="入库数量" :edit-render="{ autoFocus: 'input' }" width="120">
                    <template #edit="{ row }">
                        <vxe-number-input v-model="row.inboundQuantity" :digits="3" :step="0.001" :min="0"
                            @blur="updateTotalPrice(row)" :disabled="row.materialName === '大底'"></vxe-number-input>
                    </template>
                </vxe-column>
                <vxe-column field="unitPrice" title="采购单价" :edit-render="{ autoFocus: 'input' }" width="120">
                    <template #edit="{ row }">
                        <vxe-number-input v-model="row.unitPrice" type="amount" :min="0" :step="0.001" :digits="3"
                            :disabled="inboundForm.inboundType == 1" @blur="updateTotalPrice(row)"></vxe-number-input>
                    </template>
                </vxe-column>
                <vxe-column field="itemTotalPrice" title="采购金额" :edit-render="{ autoFocus: 'input' }" width="120">
                    <template #edit="{ row }">
                        <vxe-number-input v-model="row.itemTotalPrice" type="amount" :min="0" :step="0.001" :digits="3"
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
            </vxe-table>
        </el-col>
    </el-row>

    <MaterialSelectDialog :visible="isMaterialSelectDialogVis" :searchedMaterials="searchedMaterials"
        @confirm="updateMaterialTableData" @update-visible="updateDialogVisible" />

    <el-dialog title="选择材料" v-model="isSizeMaterialSelectDialogVis" width="80%">
        <span>搜索订单号：</span>
        <el-input v-model="orderRIdSearch" @change="searchRecordByOrderRId"
            style="width: 200px; margin-bottom: 10px;"></el-input>
        <el-table ref="searchedSizeMaterials" :data="searchedSizeMaterials" border stripe
            @selection-change="handleSizeMaterialSelect" height="600">
            <el-table-column type="selection" width="55"></el-table-column>
            <el-table-column prop="orderRId" label="生产订单号"></el-table-column>
            <el-table-column prop="shoeRId" label="工厂鞋型"></el-table-column>
            <el-table-column prop="materialName" label="材料名称"></el-table-column>
            <el-table-column prop="materialModel" label="材料型号"></el-table-column>
            <el-table-column prop="materialSpecification" label="材料规格"></el-table-column>
            <el-table-column prop="materialColor" label="颜色"></el-table-column>
            <el-table-column prop="unitPrice" label="单价"></el-table-column>
            <el-table-column prop="actualInboundUnit" label="计量单位"></el-table-column>
            <el-table-column prop="estimatedInboundAmount" label="采购数量"></el-table-column>
            <el-table-column prop="actualInboundAmount" label="已入库数量"></el-table-column>
            <el-table-column prop="currentAmount" label="库存"></el-table-column>
        </el-table>
        <template #footer>
            <el-button @click="confirmSelection">确定</el-button>
        </template>
    </el-dialog>
    <el-dialog title="入库预览" v-model="isPreviewDialogVis" width="90%" :close-on-click-modal="false"
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
                                        previewInboundForm.currentDateTime }}
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
            <el-button type="primary"
                @click="downloadPDF(`健诚鞋业入库单${inboundForm.inboundRId}`, `printView`)">下载PDF</el-button>
            <el-button v-if="isInbounded == 0" type="primary" @click="submitInboundForm">入库</el-button>
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
export default {
    components: {
        MaterialSearchDialog,
        MaterialSelectDialog,
    },
    props: {
        materialTypeOptions: {
            type: Array,
            required: true,
        },
        materialSupplierOptions: {
            type: Array,
            required: true
        },
        unitOptions: {
            type: Array,
            required: true
        },
    },
    data() {
        return {
            materialTableData: [],
            previewInboundForm: {},
            inboundForm: {},
            inboundFormTemplate: {
                currentDateTime: new Date((new Date()).getTime() - (new Date()).getTimezoneOffset() * 60000).toISOString().slice(0, 19).replace('T', ' '),
                supplierName: null,
                materialTypeId: null,
                inboundType: 0,
                inboundRId: '',
                remark: '',
                shoeSize: null,
                payMethod: '',
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
                disableEdit: false,
                inboundModel: '',
                inboundSpecification: '',
            },
            isMaterialSelectDialogVis: false,
            isSizeMaterialSelectDialogVis: false,
            searchedMaterials: [],
            searchedSizeMaterials: [],
            orriginalSizeMaterials: [],
            currentKeyDownRow: null,
            currentIndex: -1,
            isPreviewDialogVis: false,
            rules: {
                currentDateTime: [
                    { required: true, message: '此项为必填项', trigger: 'change' },
                ],
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
                { label: '复合入库', value: 2 }
            ],
            shoeSizeColumns: [],
            previewData: [],
            logisticsShoeSizes: [],
            materialNameOptions: [],
            selectedSizeMaterials: [],
            orderRIdSearch: '',
        }
    },
    async mounted() {
        this.inboundForm = JSON.parse(JSON.stringify(this.inboundFormTemplate))
        await this.getLogisticsShoeSizes()
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
            return Number(total).toFixed(3);
        },
        filteredShoeSizeColumns() {
            return this.shoeSizeColumns.filter(column =>
                this.previewData.some(row => row[column.prop] !== undefined && row[column.prop] !== null && row[column.prop] !== 0)
            )
        }
    },
    methods: {
        updateMaterialTableData(value) {
            this.searchedMaterials = []
            let seen = new Set()
            let temp = [...this.materialTableData, ...value]
            temp.splice(this.currentIndex, 1)
            for (const obj of temp) {
                if (!obj.orderRId) {
                    continue
                }
                // create tuple of name, spec, model, color, and orderRId
                let storageId = obj.storageId || ''
                if (storageId !== '' && seen.has(obj.orderRId)) {
                    ElMessage.error("入库单不能有重复数据")
                    // 去掉新创建行
                    this.currentIndex = null
                    return
                }
                seen.add(obj.orderRId)
            }
            this.materialTableData = [...temp]
            this.currentIndex = null
        },
        updateDialogVisible(value) {
            this.isMaterialSelectDialogVis = value
        },
        handleSizeMaterialSelect(value) {
            this.selectedSizeMaterials = value
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
            let params = {
                materialTypeId: this.inboundForm.materialTypeId,
            }
            let response = await axios.get(`${this.$apiBaseUrl}/logistics/getallmaterialname`, { params })
            this.materialNameOptions = response.data

            response = await axios.get(`${this.$apiBaseUrl}/logistics/getwarehousebymaterialtypeid`, { params })
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
            let selectedShoeSize = this.logisticsShoeSizes.filter((item) => item.batchInfoTypeId == this.inboundForm.shoeSize)[0]
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
            console.log(this.shoeSizeColumns)
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
            row.itemTotalPrice = (total * row.unitPrice).toFixed(3)
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
            const newRow = JSON.parse(JSON.stringify(this.rowTemplate));
            this.materialTableData.push(newRow)
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
        handleKeydown(event, scope) {
            if (event.code === 'Enter') {
                if (this.inboundForm.inboundType != 1 && this.inboundForm.supplierName == null) {
                    ElMessage.warning('请填写厂家名称')
                    return
                }
                if (this.inboundForm.materialTypeId == null) {
                    ElMessage.warning('请填写材料类型')
                    return
                }
                event.preventDefault(); // Prevent default Enter key behavior
                this.currentKeyDownRow = scope.row; // Store the current row
                this.currentIndex = scope.rowIndex; // Store the current row index
                if (['大底', '中底'].includes(this.currentKeyDownRow.materialName)) {
                    this.fetchSizeMaterialData()
                    this.isSizeMaterialSelectDialogVis = true
                }
                else {
                    this.fetchMaterialData()
                    this.isMaterialSelectDialogVis = true
                }
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
        },
        searchRecordByOrderRId(queryString) {
            this.$refs.searchedSizeMaterials.clearSelection()
            this.searchedSizeMaterials = [...this.orriginalSizeMaterials]
            if (queryString) {
                this.searchedSizeMaterials = this.searchedSizeMaterials.filter(item => item.orderRId.includes(queryString))
            }
        },
        async fetchSizeMaterialData() {
            const params = {
                "materialName": this.currentKeyDownRow.materialName,
                "materialSpec": this.currentKeyDownRow.inboundSpecification,
                "materialModel": this.currentKeyDownRow.inboundModel,
                "materialColor": this.currentKeyDownRow.materialColor,
                "supplier": this.inboundForm.supplierName,
                "orderRId": this.currentKeyDownRow.orderRId,
            }
            const response = await axios.get(`${this.$apiBaseUrl}/warehouse/getsizematerials`, { params })
            this.orriginalSizeMaterials = response.data
            this.searchedSizeMaterials = response.data
        },
        confirmSelection() {
            if (this.selectedSizeMaterials.length == 0) {
                ElMessage.warning('请至少选择一行材料')
                return
            }
            if (this.selectedSizeMaterials[0].materialName === '大底') {
                let firstOrderRId = this.selectedSizeMaterials[0].orderRId
                for (let i = 0; i < this.selectedSizeMaterials.length; i++) {
                    console.log(firstOrderRId, this.selectedSizeMaterials[i].orderRId)
                    if (this.selectedSizeMaterials[i].orderRId != firstOrderRId) {
                        ElMessage.warning('请确保选择的材料属于同一生产订单')
                        return
                    }
                }
            }
            let tempTable = []
            this.materialTableData.splice(this.currentIndex, 1)
            for (let i = 0; i < this.selectedSizeMaterials.length; i++) {
                let selectedMaterial = this.selectedSizeMaterials[i]
                selectedMaterial.inboundModel = selectedMaterial.materialModel
                selectedMaterial.inboundSpecification = selectedMaterial.materialSpecification
                let sizeColumns = selectedMaterial.shoeSizeColumns
                for (let j = 0; j < sizeColumns.length; j++) {
                    if (i == 0 && selectedMaterial.materialName === '大底') {
                        let obj = { "label": sizeColumns[j], "prop": `amount${j}` }
                        tempTable.push(obj)

                    }
                    let estimatedInboundAmount = selectedMaterial[`estimatedInboundAmount${j}`]
                    let actualInboundAmount = selectedMaterial[`actualInboundAmount${j}`]
                    selectedMaterial["amount" + j] = estimatedInboundAmount - actualInboundAmount
                }
                selectedMaterial.inboundQuantity = selectedMaterial.estimatedInboundAmount - selectedMaterial.actualInboundAmount
                selectedMaterial.itemTotalPrice = (selectedMaterial.inboundQuantity * selectedMaterial.unitPrice).toFixed(3)
                this.materialTableData.push(selectedMaterial)
            }

            this.shoeSizeColumns = tempTable
            this.materialTableData = [...this.materialTableData]
            this.isSizeMaterialSelectDialogVis = false
        },
        async handleMaterialNameSelect(row, value) {
            const response = await axios.get(
                `${this.$apiBaseUrl}/devproductionorder/getmaterialdetail?materialName=${row.materialName}`
            )
            row.actualInboundUnit = response.data.unit
            row.materialCategory = response.data.materialCategory
            if (!(row.materialName === '大底')) {
                this.shoeSizeColumns = []
            }
        },
        async submitInboundForm() {
            const params = {
                inboundType: this.inboundForm.inboundType,
                currentDateTime: this.inboundForm.currentDateTime,
                supplierName: this.inboundForm.supplierName,
                warehouseId: this.inboundForm.warehouseId,
                remark: this.inboundForm.remark,
                items: this.materialTableData,
                batchInfoTypeId: this.inboundForm.shoeSize,
                payMethod: this.inboundForm.payMethod,
                materialTypeId: this.inboundForm.materialTypeId,
            }
            try {
                const response = await axios.post(`${this.$apiBaseUrl}/warehouse/inboundmaterial`, params)
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
            this.isInbounded = 0
            this.materialTableData = []
            this.inboundForm = JSON.parse(JSON.stringify(this.inboundFormTemplate))
            this.inboundForm.currentDateTime = new Date((new Date()).getTime() - (new Date()).getTimezoneOffset() * 60000).toISOString().slice(0, 19).replace('T', ' ')
            this.shoeSizeColumns = []
            this.isPreviewDialogVis = false;
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
