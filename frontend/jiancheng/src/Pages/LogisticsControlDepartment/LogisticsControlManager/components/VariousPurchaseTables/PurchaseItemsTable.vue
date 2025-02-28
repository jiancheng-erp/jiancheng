<template>
    <el-select v-model="currentBatchInfoType" @change="changeBatchInfoType" placeholder="请选择鞋型尺码类型" v-if="batchInfoVisible">
        <el-option
            v-for="item in batchInfoTypeList"
            :key="item.batchInfoTypeId"
            :label="item.batchInfoTypeName"
            :value="item.batchInfoTypeId"
        >
        </el-option>
    </el-select>
    <el-table :data="localTableData" border height="350">
        <el-table-column prop="materialType" label="材料类型">
            <template #default="scope">
                <el-popover trigger="hover" placement="top">
                    <p>
                        {{ scope.row.materialType ? scope.row.materialType.materialTypeName : '' }}
                    </p>
                    <template #reference>
                        <el-select
                            v-model="scope.row.materialType"
                            @change="changeWarehouseName(scope.row)"
                            value-key="materialTypeId"
                        >
                            <el-option
                                v-for="item in materialTypeOptions"
                                :key="item.materialTypeId"
                                :value="item"
                                :label="item.materialTypeName"
                            >
                            </el-option>
                        </el-select>
                    </template>
                </el-popover>
            </template>
        </el-table-column>
        <el-table-column prop="warehouseName" label="所属仓库" />
        <el-table-column prop="supplierName" label="厂家名称">
            <template #default="scope">
                <el-autocomplete
                    v-model="scope.row.supplierName"
                    :fetch-suggestions="querySupplierNames"
                    placeholder="搜索厂家"
                    @select="handleSupplierNameSelect(scope.row, $event)"
                >
                </el-autocomplete>
            </template>
        </el-table-column>
        <el-table-column prop="materialName" label="材料名称">
            <template #default="scope">
                <el-select v-model="scope.row.materialName" filterable @change="
                    handleMaterialNameSelect(scope.row, $event)
                    ">
                    <el-option v-for="item in filterByTypes(materialNameOptions, typeLimit)
                    " :key="item.value" :value="item.value" :label="item.label">
                    </el-option>
                </el-select>
            </template>
        </el-table-column>
        <el-table-column prop="materialModel" label="材料型号">
            <template #default="scope">
                <el-input v-model="scope.row.materialModel" clearable type="textarea"> </el-input>
            </template>
        </el-table-column>
        <el-table-column label="材料规格">
            <template #default="scope">
                <el-input
                    v-model="scope.row.materialSpecification"
                    placeholder=""
                    type="textarea"
                    clearable
                ></el-input>
            </template>
        </el-table-column>
        <el-table-column label="工艺名称">
            <template #default="scope">
                <el-input
                    v-model="scope.row.craftName"
                    placeholder=""
                    type="textarea"
                    clearable
                ></el-input>
            </template>
        </el-table-column>
        <el-table-column label="颜色">
            <template #default="scope">
                <el-input v-model="scope.row.color" placeholder="" clearable> </el-input>
            </template>
        </el-table-column>
        <el-table-column prop="unit" label="单位">
        </el-table-column>
        <el-table-column prop="purchaseAmount" label="采购数量">
            
            <template #default="scope">
                
                <el-input-number
                    v-if="scope.row.materialCategory == 0"
                    v-model="scope.row.purchaseAmount"
                    :min="0"
                    :step="0.0001"
                    size="small"
                />
                <div v-if="scope.row.materialCategory == 1">
                    {{ scope.row.purchaseAmount }}
                    <el-button
                    
                    type="primary"
                    size="default"
                    @click="openSizeDialog(scope.row, scope.$index)"
                    >尺码用量填写</el-button
                >
                </div>

            </template>
        </el-table-column>
        <el-table-column label="备注">
            <template #default="scope">
                <el-input
                    v-model="scope.row.comment"
                    placeholder=""
                    size="default"
                    clearable
                    type="textarea"
                ></el-input>
            </template>
        </el-table-column>
        <el-table-column label="操作">
            <template #default="scope">
                <el-button size="small" type="danger" @click="deleteCurrentRow(scope.$index)"
                    >删除</el-button
                >
            </template>
        </el-table-column>
    </el-table>
    <el-button type="primary" @click="openNewMaterialDialog">添加新材料</el-button>
    <el-button type="primary" @click="manualAddMaterial">手动添加材料</el-button>

    <el-dialog
        title="添加新采购材料"
        v-model="newMaterialVis"
        width="60%"
        :close-on-click-modal="false"
    >
        <el-row :gutter="20">
            <el-col :span="6" :offset="0">
                <el-input
                    v-model="addMaterialDialogField.materialTypeSearch"
                    placeholder="输入材料类型"
                    size="default"
                    :suffix-icon="Search"
                    clearable
                    @change="getMaterialFilterData(currentCreateViewId)"
                ></el-input>
            </el-col>
            <el-col :span="6" :offset="0">
                <el-input
                    v-model="addMaterialDialogField.materialSearch"
                    placeholder="输入材料名称"
                    size="default"
                    :suffix-icon="Search"
                    clearable
                    @change="getMaterialFilterData(currentCreateViewId)"
                ></el-input>
            </el-col>
            <el-col :span="6" :offset="0">
                <el-input
                    v-model="addMaterialDialogField.factorySearch"
                    placeholder="输入厂家名称"
                    size="default"
                    :suffix-icon="Search"
                    clearable
                    @change="getMaterialFilterData(currentCreateViewId)"
                ></el-input>
            </el-col>
        </el-row>
        <el-row :gutter="20">
            <el-table
                :data="assetFilterTable"
                border
                ref="materialSelectTable"
                @selection-change="handleMaterialSelectionChange"
                style="height: 400px"
            >
                <el-table-column type="selection" width="55"></el-table-column>
                <el-table-column prop="materialType" label="材料类型" />
                <el-table-column prop="materialName" label="材料名称" />
                <el-table-column prop="warehouseName" label="所属仓库" />
                <el-table-column prop="unit" label="单位" />
                <el-table-column prop="supplierName" label="工厂名称" />
            </el-table>
        </el-row>
        <template #footer>
            <span>
                <el-button @click="newMaterialVis = false">取消</el-button>
                <el-button type="primary" @click="confirmNewMaterialAdd">确认</el-button>
            </span>
        </template>
    </el-dialog>
    <el-dialog
        title="尺码数量填写"
        v-model="isSizeDialogVisible"
        width="60%"
        :close-on-click-modal="false"
    >
        <span>{{ `尺码名称: ${currentShoeSizeType}` }}</span>
        <el-table :data="sizeData" border stripe>
            <el-table-column prop="size" label="尺码"></el-table-column>
            <el-table-column prop="purchaseAmount" label="采购数量">
                <template #default="scope">
                    <el-input-number v-model="scope.row.purchaseAmount" :min="0" size="small" />
                </template>
            </el-table-column>
        </el-table>

        <template #footer>
            <span>
                <el-button type="primary" @click="confirmSizeAmount()">确认</el-button>
            </span>
        </template>
    </el-dialog>
</template>
<script>
import axios from 'axios'
import { markRaw } from 'vue'
import { Search } from '@element-plus/icons-vue'
export default {
    props: ['materialTypeOptions', 'purchaseData', 'batchInfoVisible', 'typeLimit'],
    data() {
        return {
            Search: markRaw(Search),
            isSizeDialogVisible: false,
            isChooseOrderDialogOpen: false,
            isChooseOrderShoeDialogOpen: false,
            currentMaterialRow: {},
            selectedOrderId: null,
            localTableData: [],
            newItemTemplate: {
                materialName: null,
                materialType: null,
                supplierName: null,
                materialSpecification: null,
                materialModel: null,
                color: '',
                unit: '',
                craftName: '',
                purchaseAmount: 0,
                comment: '',
                sizeInfo: []
            },
            currentSizeIndex: 0,
            sizeData: [],
            currentShoeSizeType: '',
            // search material dialog variables
            addMaterialDialogField: {},
            addMaterialTemplate: {
                materialTypeSearch: '',
                materialSearch: '',
                factorySearch: ''
            },
            assetTable: [],
            assetFilterTable: [],
            newMaterialVis: false,
            materialSelectRow: {},
            batchInfoTypeList: [],
            currentBatchInfoType: null,
            materialNameOptions: [],
        }
    },
    watch: {
        purchaseData(newItems) {
            this.localTableData = [...newItems]
        }
    },
    emits: ['update-items', 'update-current-batch-info-type'],
    mounted() {
        this.getBatchTypeList()
        this.getAllMaterialName()
    },
    methods: {
        async getAllMaterialName() {
            const response = await axios.get(`${this.$apiBaseUrl}/logistics/getallmaterialname`, {
                params: {
                    department: '0'
                }
            })
            this.materialNameOptions = response.data
        },
        emitUpdate() {
            this.$emit('update-items', [...this.localTableData])
        },
        changeBatchInfoType() {
            // Clear the current size info
            this.newItemTemplate.sizeInfo = []

            // Find the selected batch info type
            const selectedBatchInfoType = this.batchInfoTypeList.find(
                (item) => item.batchInfoTypeId === this.currentBatchInfoType
            )

            // Update the current shoe size type
            this.currentShoeSizeType = selectedBatchInfoType.batchInfoTypeName
            this.$emit('update-current-batch-info-type', this.currentShoeSizeType);

            // Map the size slots into the desired format
            const sizeSlots = [
                { size: '34', slotName: 'size34Slot' },
                { size: '35', slotName: 'size35Slot' },
                { size: '36', slotName: 'size36Slot' },
                { size: '37', slotName: 'size37Slot' },
                { size: '38', slotName: 'size38Slot' },
                { size: '39', slotName: 'size39Slot' },
                { size: '40', slotName: 'size40Slot' },
                { size: '41', slotName: 'size41Slot' },
                { size: '42', slotName: 'size42Slot' },
                { size: '43', slotName: 'size43Slot' },
                { size: '44', slotName: 'size44Slot' },
                { size: '45', slotName: 'size45Slot' },
                { size: '46', slotName: 'size46Slot' }
            ]

            this.newItemTemplate.sizeInfo = sizeSlots
                .filter((slot) => selectedBatchInfoType[slot.slotName]) // Only include defined slots
                .map((slot) => ({
                    size: selectedBatchInfoType[slot.slotName], // Get the size name from the slot
                    purchaseAmount: 0 // Initialize purchase amount
                }))

            console.log(this.newItemTemplate.sizeInfo)
        },
        async getBatchTypeList() {
            const response = await axios.get(`${this.$apiBaseUrl}/shoe/getshoebatchinfotypelogistics`, {})
            console.log(response.data)
            this.batchInfoTypeList = response.data
        },
        async querySupplierNames(queryString, callback) {
            if (queryString.trim()) {
                await axios
                    .get(
                        `${this.$apiBaseUrl}/devproductionorder/getautofinishedsuppliername?supplierName=${queryString}`
                    )
                    .then((response) => {
                        const suggestions = response.data.map((item) => ({
                            value: item.name
                        }))
                        callback(suggestions)
                    })
                    .catch((error) => {
                        console.error('Failed to fetch material names:', error)
                    })
            } else {
                callback([])
            }
        },
        async getMaterialList() {
            const response = await axios.get(
                `${this.$apiBaseUrl}/logistics/getmaterialtypeandname`,
                {
                    params: {
                        materialcategory: 0
                    }
                }
            )
            this.assetTable = response.data
            this.assetFilterTable = this.assetTable
        },
        async openNewMaterialDialog() {
            this.newMaterialVis = true
            await this.getMaterialList()
            this.addMaterialDialogField = JSON.parse(JSON.stringify(this.addMaterialTemplate))
        },
        manualAddMaterial() {
            let newItem = JSON.parse(JSON.stringify(this.newItemTemplate))
            this.localTableData = [...this.localTableData, newItem]
            this.emitUpdate()
        },
        deleteCurrentRow(index) {
            this.localTableData.splice(index, 1)
            this.emitUpdate()
        },
        handleSupplierNameSelect(row, selectedItem) {
            row.supplierName = selectedItem.value
        },
        changeWarehouseName(row) {
            row.warehouseName = row.materialType.warehouseName
            if (row.materialType.materialTypeName === '底材' || row.materialType.materialTypeName === '楦头' || row.materialType.materialTypeName === '刀模') {
                row.materialCategory = 1
            } else {
                row.materialCategory = 0
            }
        },
        handleMaterialSelectionChange(selection) {
            if (selection.length > 1) {
                this.$refs.materialSelectTable.clearSelection()
                this.$refs.materialSelectTable.toggleRowSelection(
                    selection[selection.length - 1],
                    true
                )
            } else {
                this.materialSelectRow = selection[0]
            }
        },
        confirmNewMaterialAdd() {
            if (this.materialSelectRow === null) {
                ElMessageBox.alert('材料不能为空！', '警告', { confirmButtonText: '确认' })
                return
            }

            const isDuplicate = this.localTableData.some(
                (item) => item.materialName === this.materialSelectRow.materialName
            )

            if (isDuplicate) {
                ElMessageBox.alert('材料名称必须唯一！', '警告', { confirmButtonText: '确认' })
                return
            }
            let newItem = JSON.parse(JSON.stringify(this.newItemTemplate))
            newItem.materialName = this.materialSelectRow.materialName
            newItem.materialType = this.materialSelectRow.materialType
            newItem.warehouseName = this.materialSelectRow.warehouseName
            newItem.supplierName = this.materialSelectRow.supplierName
            newItem.materialCategory = this.materialSelectRow.materialCategory
            newItem.unit = this.materialSelectRow.unit
            this.localTableData = [...this.localTableData, newItem]
            this.newMaterialVis = false
            this.addMaterialDialogField = JSON.parse(JSON.stringify(this.addMaterialTemplate))
            this.emitUpdate()
        },
        confirmSizeAmount() {
            this.localTableData[this.currentSizeIndex].sizeInfo = this.sizeData
            const totalApprovalAmount = this.sizeData.reduce(
                (total, item) => total + item.purchaseAmount,
                0
            )
            this.localTableData[this.currentSizeIndex].purchaseAmount = totalApprovalAmount
            this.isSizeDialogVisible = false
        },
        openSizeDialog(row, index) {
            this.sizeData = row.sizeInfo
            console.log(this.sizeData)
            this.isSizeDialogVisible = true
            this.currentSizeIndex = index
        },
        async handleMaterialNameSelect(row, selectedItem) {
            const response = await axios.get(
                `${this.$apiBaseUrl}/devproductionorder/getmaterialdetail?materialName=${row.materialName}`
            )
            row.materialId = response.data.materialId
            row.unit = response.data.unit
            row.materialType = response.data.materialType
        },
        filterByTypes(options, types) {
            if (types.length === 1 && types[0] === 0) {
                return options
            }
            return options.filter((option) => types.includes(option.type))
        },
    }
}
</script>
