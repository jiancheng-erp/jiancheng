<template>
    <el-row :gutter="20">
        <el-col :span="24">
            <el-button type="primary" @click="addRow">新增一行</el-button>
            <el-button type="warning" @click="copyRows">批量复制</el-button>
            <el-button type="danger" @click="deleteRows">批量删除</el-button>
            <el-button type="primary" @click="openOrderMaterialQuery">订单材料查询</el-button>
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
                <el-form-item prop="shoeSize" label="码段">
                    <el-select v-model="inboundForm.shoeSize" filterable clearable @change="insertShoeSizeColumns">
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
            <vxe-table :data="inboundForm.items" ref="tableRef" border :edit-config="{ mode: 'cell', trigger: 'click' }"
                :row-config="{ keyField: 'id', isHover: true }" :column-config="{ resizable: true }" :keyboard-config="{
                    isEdit: true,
                    isArrow: true,
                    isEnter: true,
                    isTab: true,
                    isDel: true,
                    isBack: true,
                    isEsc: true,
                    isLastEnterAppendRow: true,
                    editMode: 'insert'
                }" :mouse-config="{ selected: true }" show-overflow>
                <vxe-column type="checkbox" width="50"></vxe-column>
                <vxe-column field="orderRId" title="生产订单号" :edit-render="{ autoFocus: true }" width="150">
                    <template #edit="scope">
                        <el-select v-model="scope.row.orderRId" :disabled="scope.row.disableEdit"
                            @change="handleOrderRIdSelect(scope.row, $event)"
                            @focus="getFilteredShoes(scope.row, $event)" filterable clearable>
                            <el-option v-for="item in filteredOrders" :key="item.orderId" :value="item.orderRId"
                                :label="item.orderRId"></el-option>
                        </el-select>
                    </template>
                </vxe-column>
                <vxe-column field="shoeRId" title="工厂鞋型" :edit-render="{ autoFocus: 'input' }" width="150">
                    <template #edit="scope">
                        <vxe-input v-model="scope.row.shoeRId" clearable
                            @change="(event) => handleShoeRIdSelect(scope.row, event.value)"></vxe-input>
                    </template>
                </vxe-column>
                <vxe-column title="材料名称" field="materialName" width="150" :edit-render="{ autoFocus: true }">
                    <template #default="{ row }">
                        <span>{{ row.materialName }}</span>
                    </template>
                    <template #edit="scope">
                        <el-select v-model="scope.row.materialName" :disabled="scope.row.disableEdit"
                            @change="handleMaterialNameSelect(scope.row, $event)" filterable clearable>
                            <el-option v-for="item in filteredMaterialNameOptions" :key="item.value" :value="item.value"
                                :label="item.label"></el-option>
                        </el-select>
                    </template>
                </vxe-column>
                <vxe-column field="inboundModel" title="材料型号" :edit-render="{ autoFocus: 'input' }" width="150">
                    <template #edit="scope">
                        <vxe-input v-model="scope.row.inboundModel" clearable></vxe-input>
                    </template>
                </vxe-column>
                <vxe-column field="inboundSpecification" title="材料规格" :edit-render="{ autoFocus: 'input' }" width="200">
                    <template #edit="scope">
                        <vxe-input v-model="scope.row.inboundSpecification" clearable></vxe-input>
                    </template>
                </vxe-column>
                <vxe-column field="materialColor" title="颜色" :edit-render="{ autoFocus: 'input' }" width="150">
                    <template #edit="scope">
                        <vxe-input v-model="scope.row.materialColor" clearable
                            :disabled="scope.row.disableEdit"></vxe-input>
                    </template>
                </vxe-column>
                <vxe-column field="actualInboundUnit" title="计量单位" :edit-render="{ autoFocus: true }" width="120">
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

    <el-dialog title="选择材料" v-model="isSizeMaterialSelectDialogVis" width="80%" destroy-on-close>
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
    <OrderMaterialQuery :visible="isOrderMaterialQueryVis" @update-visible="updateOrderMaterialQueryVis" />
</template>
<script>
import axios from 'axios';
import { ElMessage, ElMessageBox } from 'element-plus';
import MaterialSearchDialog from './MaterialSearchDialog.vue';
import htmlToPdf from '@/Pages/utils/htmlToPdf';
import { updateTotalPriceHelper } from '@/Pages/utils/warehouseFunctions';
import MaterialSelectDialog from './MaterialSelectDialog.vue';
import OrderMaterialQuery from './OrderMaterialQuery.vue';
import { debounce } from 'lodash';
import XEUtils from 'xe-utils'
export default {
    components: {
        MaterialSearchDialog,
        MaterialSelectDialog,
        OrderMaterialQuery,
    },
    props: {
        inputInboundForm: {
            type: Object,
            required: true
        },
    },
    emits: ['updateInboundForm'],
    watch: {
        inboundForm: {
            handler(newVal) {
                this.$emit('updateInboundForm', newVal);
            },
            deep: true,
        },
    },
    data() {
        return {
            previewInboundForm: {},
            inboundForm: {},
            inboundFormTemplate: {
                supplierName: null,
                materialTypeId: null,
                inboundType: 0,
                inboundRId: '',
                remark: '',
                shoeSize: null,
                payMethod: '应付账款',
                warehouseName: null,
                warehouseId: null,
                items: [],
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
            selectedSizeMaterials: [],
            orderRIdSearch: '',
            filteredOrders: [],
            isOrderMaterialQueryVis: false,
            materialTypeOptions: [],
            materialSupplierOptions: [],
            unitOptions: [],
            activeOrderShoes: [],
        }
    },
    async mounted() {
        console.log(this.inputInboundForm)
        this.inboundForm = JSON.parse(JSON.stringify(this.inputInboundForm))
        if (this.inboundForm.items[0].shoeSizeColumns) {
            for (let i = 0; i < this.inboundForm.items[0].shoeSizeColumns.length; i++) {
                let obj = {
                    "label": this.inboundForm.items[0].shoeSizeColumns[i],
                    "prop": `amount${i}`
                }
                this.shoeSizeColumns.push(obj)
            }
        }

        console.log(this.shoeSizeColumns)
        this.getMaterialNameOptions()
        this.getMaterialTypeOptions();
        this.getMaterialSupplierOptions();
        this.getUnitOptions();
        this.getActiveOrderShoes();
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
        },
        filteredMaterialNameOptions() {
            return this.materialNameOptions.filter(item => item.type == this.inboundForm.materialTypeId)
        },
    },
    methods: {
        async getMaterialTypeOptions() {
            const response = await axios.get(`${this.$apiBaseUrl}/logistics/getallmaterialtypes`)
            this.materialTypeOptions = response.data
            console.log(this.materialTypeOptions)
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
        handleOrderRIdSelect(row, value) {
            // console.log(value)
            const resultShoeRIds = this.activeOrderShoes.filter(item => item.orderRId == value)
            if (resultShoeRIds.length == 0) {
                row.shoeRId = null
                return
            }
            row.shoeRId = resultShoeRIds[0].shoeRId
        },
        handleShoeRIdSelect(row, value) {
            if (value == null || value == '') {
                this.filteredOrders = [...this.activeOrderShoes]
                return
            }
            this.filteredOrders = this.activeOrderShoes.filter(item => item.shoeRId.includes(value))
        },
        getFilteredShoes(row, event) {
            if (row.shoeRId == null || row.shoeRId == '') {
                this.filteredOrders = [...this.activeOrderShoes]
                return
            }
            this.filteredOrders = this.activeOrderShoes.filter(item => item.shoeRId.includes(row.shoeRId))
        },
        updateMaterialTableData(value) {
            this.searchedMaterials = []
            let seen = new Set()
            let temp = [...this.inboundForm.items, ...value]
            temp.splice(this.currentIndex, 1)
            this.inboundForm.items = [...temp]
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

            this.inboundForm.items.forEach(item => {
                item.materialName = null
            })
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
            const newRow = { "id": XEUtils.uniqueId(), ...JSON.parse(JSON.stringify(this.rowTemplate)) };
            this.inboundForm.items.push(newRow)
        },
        copyRows() {
            const selectedRows = this.$refs.tableRef.getCheckboxRecords();
            const clones = selectedRows.map(row => {
                const { id, ...rest } = row
                return { ...rest, id: XEUtils.uniqueId() }
            })
            this.inboundForm.items.push(...clones)
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
                this.inboundForm.items = this.inboundForm.items.filter(row => !selectedRows.includes(row));
                ElMessage.success('删除成功');
            }).catch(() => {
                ElMessage.info('已取消删除');
            });
        },
        updateTotalPrice(row) {
            row.itemTotalPrice = updateTotalPriceHelper(row)
        },
        handleSearchMaterial(scope) {
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
                this.fetchSizeMaterialData()
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
                    if (this.selectedSizeMaterials[i].orderRId != firstOrderRId) {
                        ElMessage.warning('请确保选择的材料属于同一生产订单')
                        return
                    }
                }
            }
            let tempTable = []
            this.inboundForm.items.splice(this.currentIndex, 1)
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
                this.inboundForm.items.push(selectedMaterial)
            }

            this.shoeSizeColumns = tempTable
            this.inboundForm.items = [...this.inboundForm.items]
            this.isSizeMaterialSelectDialogVis = false
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
