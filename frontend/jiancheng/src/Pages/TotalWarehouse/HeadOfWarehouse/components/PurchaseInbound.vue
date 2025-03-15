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
                    <el-select v-model="inboundForm.inboundType" filterable clearable>
                        <el-option v-for="item in inboundOptions" :key="item.value" :value="item.value"
                            :label="item.label"></el-option>
                    </el-select>
                </el-form-item>
                <!-- <el-form-item label="仓库名称">
                    <el-input v-model="inboundForm.warehouseName"></el-input>
                </el-form-item> -->
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
                        <el-option v-for="item in ['应付账款', '现金']" :key="item" :value="item"
                            :label="item"></el-option>
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
                        <vxe-input v-model="scope.row.orderRId" clearable
                            @keydown="(event) => handleKeydown(event, scope)"></vxe-input>
                    </template>
                </vxe-column>
                <vxe-column title="材料名称" field="materialName" width="150" :edit-render="{}">
                    <template #default="{ row }">
                        <span>{{ row.materialName }}</span>
                    </template>
                    <template #edit="scope">
                        <el-select v-model="scope.row.materialName"
                            @change="handleMaterialNameSelect(scope.row, $event)" filterable clearable>
                            <el-option v-for="item in materialNameOptions" :key="item.value" :value="item.value"
                                :label="item.label"></el-option>
                        </el-select>
                    </template>
                </vxe-column>
                <vxe-column field="materialModel" title="材料型号" :edit-render="{ autoFocus: 'input' }" width="150">
                    <template #edit="scope">
                        <vxe-input v-model="scope.row.materialModel" clearable
                            @keydown="(event) => handleKeydown(event, scope)"></vxe-input>
                    </template>
                </vxe-column>
                <vxe-column field="materialSpecification" title="材料规格" :edit-render="{ autoFocus: 'input' }"
                    width="150">
                    <template #edit="scope">
                        <vxe-input v-model="scope.row.materialSpecification" clearable
                            @keydown="(event) => handleKeydown(event, scope)"></vxe-input>
                    </template>
                </vxe-column>
                <vxe-column field="materialColor" title="颜色" :edit-render="{ autoFocus: 'input' }" width="150">
                    <template #edit="{ row }">
                        <vxe-input v-model="row.materialColor" clearable></vxe-input>
                    </template>
                </vxe-column>
                <vxe-column field="actualInboundUnit" title="计量单位" width="80"></vxe-column>
                <vxe-column field="inboundQuantity" title="入库数量" :edit-render="{ autoFocus: 'input' }" width="120">
                    <template #edit="{ row }">
                        <vxe-number-input v-model="row.inboundQuantity" clearable :digits="3" :step="0.001" :min="0"
                            @change="updateTotalPrice(row)" :disabled="row.materialCategory == 1"></vxe-number-input>
                    </template>
                </vxe-column>
                <vxe-column field="unitPrice" title="采购单价" :edit-render="{ autoFocus: 'input' }" width="120">
                    <template #edit="{ row }">
                        <vxe-number-input v-model="row.unitPrice" type="amount" clearable :min="0"
                            @change="updateTotalPrice(row)"></vxe-number-input>
                    </template>
                </vxe-column>
                <vxe-column field="totalPrice" title="采购金额" width="100">
                </vxe-column>
                <vxe-column field="remark" title="备注" :edit-render="{ autoFocus: 'input' }" width="150">
                    <template #edit="{ row }">
                        <vxe-input v-model="row.remark" clearable></vxe-input>
                    </template>
                </vxe-column>
                <vxe-column v-for="item in shoeSizeColumns" :field="item.prop" :title="item.label"
                    :edit-render="{ autoFocus: 'input' }" width="150">
                    <template #edit="{ row }">
                        <vxe-number-input v-model="row[item.prop]" type="integer" clearable
                            @change="updateTotalShoes(row)" :min="0"></vxe-number-input>
                    </template>
                </vxe-column>
            </vxe-table>
        </el-col>
    </el-row>
    <el-dialog title="选择材料" v-model="isMaterialSelectDialogVis" width="80%">
        <el-table :data="searchedMaterials" border stripe>
            <el-table-column label="选择" align="center" width="65">
                <template #default="scope">
                    <el-radio :label="scope.$index" v-model="selectionIndex" @change="handleSelectMaterials(scope.row)"
                        class="radio-class"></el-radio>
                </template>
            </el-table-column>
            <el-table-column prop="orderRId" label="生产订单号"></el-table-column>
            <el-table-column prop="materialName" label="材料名称"></el-table-column>
            <el-table-column prop="materialModel" label="材料型号"></el-table-column>
            <el-table-column prop="materialSpecification" label="材料规格"></el-table-column>
            <el-table-column prop="materialColor" label="颜色"></el-table-column>
            <el-table-column prop="unitPrice" label="单价"></el-table-column>
            <el-table-column prop="actualInboundUnit" label="计量单位"></el-table-column>
            <el-table-column prop="estimatedInboundAmount" label="采购数量"></el-table-column>
            <el-table-column prop="actualInboundAmount" label="已入库数量"></el-table-column>

        </el-table>
        <template #footer>
            <el-button @click="confirmSelection">确定</el-button>
        </template>
    </el-dialog>

    <el-dialog title="入库预览" v-model="isPreviewDialogVis" width="90%" :close-on-click-modal="false"
        @closed="closePreviewDialog">
        <div id="printView">
            <h2 style="text-align: center;">健诚鞋业入库单</h2>
            <div style="display: flex; justify-content: flex-end; padding: 5px;">
                <span style="font-weight: bolder;font-size: 16px;">
                    单据编号：{{ previewInboundForm.inboundRId }}
                </span>
            </div>
            <table class="table" border="0pm" cellspacing="0" align="left" width="100%"
                style="font-size: 16px;margin-bottom: 10px; table-layout:fixed;word-wrap:break-word;word-break:break-all">
                <tr>
                    <!-- <td style="padding:5px; width: 300px;" align="left">采购订单号:{{ inboundForm.totalPurchaseOrderRId }}
                    </td> -->
                    <td style="padding:5px; width: 150px;" align="left">供应商:{{ previewInboundForm.supplierName }}</td>
                    <td style="padding:5px; width: 300px;" align="left">入库时间:{{ previewInboundForm.currentDateTime }}</td>
                    <td style="padding:5px; width: 150px;" align="left">入库方式:{{
                        determineInboundName(previewInboundForm.inboundType)
                        }}</td>
                    <td style="padding:5px; width: 150px;" align="left">结算方式:{{previewInboundForm.payMethod}}</td>
                </tr>
            </table>
            <table class="yk-table" border="1pm" cellspacing="0" align="center" width="100%"
                style="font-size: 16px; table-layout:fixed;word-wrap:break-word;word-break:break-all">
                <tr>
                    <th width="100">材料名</th>
                    <th width="100">型号</th>
                    <th width="200">规格</th>
                    <th width="80">颜色</th>
                    <th width="55">单位</th>
                    <th>订单号</th>
                    <th v-if="previewData.length > 0 && previewData[0].materialCategory == 0" width="100">数量</th>
                    <th v-else width="50" v-for="(column, index) in filteredShoeSizeColumns" :key="index">{{
                        column.label }}
                    </th>
                    <th v-if="previewInboundForm.inboundType != 2" width="80">单价</th>
                    <th v-if="previewInboundForm.inboundType == 2" width="80">复合单价</th>
                    <th width="80">总价</th>
                    <th>备注</th>
                </tr>
                <tr v-for="(item, index) in previewData" :key="index" align="center">
                    <td>{{ item.materialName }}</td>
                    <td>{{ item.materialModel }}</td>
                    <td>{{ item.materialSpecification }}</td>
                    <td>{{ item.materialColor }}</td>
                    <td>{{ item.actualInboundUnit }}</td>
                    <td>{{ item.orderRId }}</td>
                    <td v-if="previewData.length > 0 && previewData[0].materialCategory == 0">{{ item.inboundQuantity }}
                    </td>
                    <td v-else v-for="(column, index) in filteredShoeSizeColumns" :key="index">{{ item[column.prop] }}
                    </td>
                    <td>{{ item.unitPrice }}</td>
                    <td>{{ item.totalPrice }}</td>
                    <td>{{ item.remark }}</td>
                </tr>
            </table>
            <div style="margin-top: 20px; font-size: 16px; font-weight: bold;">
                <div style="display: flex;">
                    <span style="padding-right: 10px;">合计数量: <span style="text-decoration: underline;">{{
                        calculateInboundTotal }}</span></span>
                    <span style="padding-right: 10px;">合计金额: <span style="text-decoration: underline;">{{
                        calculateTotalPriceSum }}</span></span>
                    <span style="padding-right: 10px;">备注: <span style="text-decoration: underline;">{{ previewInboundForm.remark }}</span></span>
                </div>
            </div>
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
import print from 'vue3-print-nb'
export default {
    components: {
        MaterialSearchDialog,
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
        materialNameOptions: {
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
                supplierName: '询价',
                warehouseName: '',
                inboundType: 0,
                inboundRId: '',
                remark: '',
                shoeSize: null,
                payMethod: '',
            },
            rowTemplate: {
                materialName: '',
                materialModel: '',
                materialSpecification: '',
                materialColor: '',
                materialCraftName: '',
                inboundQuantity: 0,
                unitPrice: 0,

            },
            isMaterialSelectDialogVis: false,
            materialSelection: {},
            searchedMaterials: [],
            currentKeyDownRow: null,
            currentIndex: -1,
            selectionIndex: null,
            isPreviewDialogVis: false,
            rules: {
                currentDateTime: [
                    { required: true, message: '此项为必填项', trigger: 'change' },
                ],
                supplierName: [
                    { required: true, message: '此项为必填项', trigger: 'change' },
                ],
                inboundType: [
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
            logisticsShoeSizes: []
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
                return total + (Number(item.inboundQuantity) * Number(item.unitPrice) || 0);
            }, 0);
            return Number(total).toFixed(2);
        },
        filteredShoeSizeColumns() {
            return this.shoeSizeColumns.filter(column =>
                this.previewData.some(row => row[column.prop] !== undefined && row[column.prop] !== null && row[column.prop] !== 0)
            )
        }
    },
    methods: {
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
            row.totalPrice = (total * row.unitPrice).toFixed(2)
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
            if (row.inboundQuantity && row.unitPrice) {
                row.totalPrice = (row.inboundQuantity * row.unitPrice).toFixed(2); // Ensure two decimal places
            } else {
                row.totalPrice = 0
            }
        },
        handleKeydown(event, scope) {
            if (event.code === 'Enter') {
                event.preventDefault(); // Prevent default Enter key behavior
                this.currentKeyDownRow = scope.row; // Store the current row
                this.currentIndex = scope.rowIndex; // Store the current row index
                this.fetchMaterialData()
                this.isMaterialSelectDialogVis = true; // Show the material selection dialog
            }
        },
        async fetchMaterialData() {
            const params = {
                "materialName": this.currentKeyDownRow.materialName,
                "materialSpec": this.currentKeyDownRow.materialSpecification,
                "materialModel": this.currentKeyDownRow.materialModel,
                "materialColor": this.currentKeyDownRow.materialColor,
                "supplier": this.inboundForm.supplierName,
                "orderRId": this.currentKeyDownRow.orderRId,
            }
            const response = await axios.get(`${this.$apiBaseUrl}/warehouse/getmaterials`, { params })
            this.searchedMaterials = response.data
            console.log(this.searchedMaterials)
        },
        handleSelectMaterials(row) {
            console.log(row)
            this.materialSelection = row;
        },
        async handleMaterialNameSelect(row, value) {
            const response = await axios.get(
                `${this.$apiBaseUrl}/devproductionorder/getmaterialdetail?materialName=${row.materialName}`
            )
            row.actualInboundUnit = response.data.unit
            row.materialCategory = response.data.materialCategory
        },
        confirmSelection() {
            this.materialTableData[this.currentIndex] = JSON.parse(JSON.stringify(this.materialSelection));
            this.materialTableData = [...this.materialTableData]
            let sizeColumns = []
            let tempTable = []
            if (this.materialTableData[0].materialCategory == 1) {
                sizeColumns = this.materialTableData[0].shoeSizeColumns
                for (let i = 0; i < sizeColumns.length; i++) {
                    let obj = { "label": sizeColumns[i], "prop": `amount${i}` }
                    tempTable.push(obj)
                    let estimatedInboundAmount = this.materialTableData[this.currentIndex][`estimatedInboundAmount${i}`]
                    let actualInboundAmount = this.materialTableData[this.currentIndex][`actualInboundAmount${i}`]
                    this.materialTableData[this.currentIndex]["amount" + i] = estimatedInboundAmount - actualInboundAmount
                }
                this.materialTableData[this.currentIndex].inboundQuantity = this.materialTableData[this.currentIndex].estimatedInboundAmount - this.materialTableData[this.currentIndex].actualInboundAmount
                this.materialTableData[this.currentIndex].totalPrice = (this.materialTableData[this.currentIndex].inboundQuantity * this.materialTableData[this.currentIndex].unitPrice).toFixed(2)
                this.shoeSizeColumns = tempTable
            }
            else if (this.materialTableData[0].materialCategory == 0) {
                this.materialTableData[this.currentIndex].inboundQuantity = this.materialTableData[this.currentIndex].estimatedInboundAmount - this.materialTableData[this.currentIndex].actualInboundAmount
                this.materialTableData[this.currentIndex].totalPrice = (this.materialTableData[this.currentIndex].inboundQuantity * this.materialTableData[this.currentIndex].unitPrice).toFixed(2)
            }
            this.materialSelection = {};
            this.selectionIndex = null;
            this.isMaterialSelectDialogVis = false;
        },
        async submitInboundForm() {
            const params = {
                inboundType: this.inboundForm.inboundType,
                currentDateTime: this.inboundForm.currentDateTime,
                supplierName: this.inboundForm.supplierName,
                remark: this.inboundForm.remark,
                items: this.materialTableData,
                batchInfoTypeId: this.inboundForm.shoeSize,
                payMethod: this.inboundForm.payMethod,
            }
            try {
                const response = await axios.post(`${this.$apiBaseUrl}/warehouse/inboundmaterial`, params)
                this.previewInboundForm.inboundRId = response.data.inboundRId
                this.isInbounded = 1
                this.materialTableData = []
                this.inboundForm = JSON.parse(JSON.stringify(this.inboundFormTemplate))
                ElMessage.success('入库成功')
            } catch (error) {
                console.error(error)
                ElMessage.error('入库失败')
            }
        },
        openPreviewDialog() {
            this.$refs.inboundForm.validate((valid) => {
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

<style media="print">
@page {
    size: 241mm 93mm;
    margin: 3mm;
}

html {
    background-color: #ffffff;
    margin: 0px;
}

body {
    border: solid 1px #ffffff;
}
</style>

<style scoped>
#printView {
    padding-left: 20px; 
    padding-right: 20px;
    color:black; 
    font-family: SimHei;
}
</style>
