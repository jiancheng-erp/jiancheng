<template>
    <el-row :gutter="20">
        <el-col :span="24" :offset="0" style="font-size: xx-large; text-align: center"
            >材料管理</el-col
        >
    </el-row>
    <el-row :gutter="20">
        <el-col :span="24" :offset="0">
            <el-tabs
                v-model="tabName"
                type="border-card"
                class="demo-tabs"
                @tab-click="handleClick"
                style="height: 700px"
            >
                <el-tab-pane label="材料类型管理" name="材料类型管理">
                    <el-row :gutter="20" style="margin-top: 20px">
                        <el-col :span="6" :offset="0">
                            <div style="display: flex; align-items: center; white-space: nowrap">
                                材料名称查询：<el-input
                                    v-model="materialNameSearch"
                                    placeholder=""
                                    size="default"
                                    :suffix-icon="Search"
                                    clearable
                                    @change="filterMaterialType"
                                ></el-input>
                            </div>
                        </el-col>
                        <el-col :span="6" :offset="0">
                            <div style="display: flex; align-items: center; white-space: nowrap">
                                材料所属库查询：
                                <el-select
                                    v-model="warehouseNameSearch"
                                    value-key=""
                                    placeholder=""
                                    clearable
                                    filterable
                                    @change="filterMaterialType"
                                >
                                    <el-option
                                        v-for="item in warehouseOptions"
                                        :key="item.value"
                                        :label="item.label"
                                        :value="item.value"
                                    >
                                    </el-option>
                                </el-select>
                            </div>
                        </el-col>
                        <el-col :span="6" :offset="0">
                            <div style="display: flex; align-items: center; white-space: nowrap">
                                厂家名称查询：<el-input
                                    v-model="factoryNameSearch"
                                    placeholder=""
                                    size="default"
                                    :suffix-icon="Search"
                                    clearable
                                    @change="filterMaterialType"
                                ></el-input>
                            </div>
                        </el-col>
                        <el-col :span="6" :offset="0">
                            <div style="display: flex; align-items: center; white-space: nowrap">
                                材料类型查询：<el-input
                                    v-model="materialTypeSearch"
                                    placeholder=""
                                    size="default"
                                    :suffix-icon="Search"
                                    clearable
                                    @change="filterMaterialType"
                                ></el-input>
                            </div>
                        </el-col>
                    </el-row>

                    <el-row :gutter="20" style="margin-top: 20px">
                        <el-col :span="24" :offset="0">
                            <el-table
                                :data="materialTypeFilterData"
                                border
                                style="height: 500px"
                                v-loading="datafinished"
                            >
                                <el-table-column type="expand">
                                    <template #default="scope">
                                        <el-table :data="scope.row.factoryInfo" max-height="200">
                                            <el-table-column
                                                prop="materialModel"
                                                label="材料型号"
                                            >
                                            </el-table-column>
                                            <el-table-column
                                                prop="supplierName"
                                                label="厂家名称"
                                            >
                                            </el-table-column>
                                        </el-table>
                                    </template>
                                </el-table-column>
                                <el-table-column
                                    prop="warehouseName"
                                    label="仓库名称"
                                ></el-table-column>
                                <el-table-column
                                    prop="materialType"
                                    label="材料类型"
                                ></el-table-column>
                                <el-table-column
                                    prop="materialName"
                                    label="材料名称"
                                ></el-table-column>
                                <el-table-column prop="unit" label="单位"></el-table-column>
                                <el-table-column prop="addDate" label="添加日期"></el-table-column>
                                <el-table-column label="操作">
                                    <template #default="scope">
                                        <el-button
                                            type="primary"
                                            @click="openMaterialTypeEditDialog(scope.row)"
                                            >编辑</el-button
                                        >
                                        <!-- <el-button
                                            type="primary"
                                            @click="openPreviewDialog(scope.row)"
                                            >删除</el-button
                                        > -->
                                    </template></el-table-column
                                >
                            </el-table>
                        </el-col>
                    </el-row>
                    <el-row style="margin-top: 20px">
                        <el-col :span="6" :offset="0">
                            <el-pagination
                                :total="materialTotal"
                                :page-size="10"
                                :v-model:current-page="currentPage1"
                                @current-change="handleCurrentChange1"
                            >
                            </el-pagination>
                        </el-col>
                        <el-col :span="3" :offset="12"
                            ><el-button
                                type="primary"
                                size="default"
                                @click="openNewMaterialTypeDialog"
                                >添加新材料类型</el-button
                            >
                        </el-col>
                        <el-col :span="3" :offset="0"
                            ><el-button type="primary" size="default" @click="openNewMaterialDialog"
                                >添加新材料</el-button
                            >
                        </el-col>
                    </el-row>
                </el-tab-pane>
                <el-tab-pane label="材料库存查询" name="材料库存查询">
                    <el-row :gutter="20" style="margin-top: 20px">
                        <el-col :span="4">
                            <div style="display: flex; align-items: center; white-space: nowrap">
                                材料类型查询：<el-input
                                    v-model="materialTypeSearch"
                                    placeholder=""
                                    size="default"
                                    :suffix-icon="Search"
                                    clearable
                                    @change="filterMaterialStorage"
                                ></el-input>
                            </div>
                        </el-col>
                        <el-col :span="4" :offset="0">
                            <div style="display: flex; align-items: center; white-space: nowrap">
                                材料名称查询：<el-input
                                    v-model="materialNameSearch"
                                    placeholder=""
                                    size="default"
                                    :suffix-icon="Search"
                                    clearable
                                    @change="filterMaterialStorage"
                                ></el-input>
                            </div>
                        </el-col>
                        <el-col :span="4" :offset="0">
                            <div style="display: flex; align-items: center; white-space: nowrap">
                                材料规格查询：<el-input
                                    v-model="specificationNameSearch"
                                    placeholder=""
                                    size="default"
                                    :suffix-icon="Search"
                                    clearable
                                    @change="filterMaterialStorage"
                                ></el-input>
                            </div>
                        </el-col>
                        <el-col :span="4" :offset="0">
                            <div style="display: flex; align-items: center; white-space: nowrap">
                                材料所属库查询：
                                <el-select
                                    v-model="warehouseNameSearch"
                                    placeholder=""
                                    clearable
                                    filterable
                                    @change="filterMaterialStorage"
                                >
                                    <el-option
                                        v-for="item in warehouseOptions"
                                        :key="item.value"
                                        :label="item.label"
                                        :value="item.value"
                                    >
                                    </el-option>
                                </el-select>
                            </div>
                        </el-col>
                        <el-col :span="4" :offset="0">
                            <div style="display: flex; align-items: center; white-space: nowrap">
                                订单编号查询：<el-input
                                    v-model="orderRIdSearch"
                                    placeholder=""
                                    size="default"
                                    :suffix-icon="Search"
                                    clearable
                                    @change="filterMaterialStorage"
                                ></el-input>
                            </div>
                        </el-col>
                    </el-row>
                    <el-row :gutter="20" style="margin-top: 20px">
                        <el-col :span="4" :offset="0">
                            <div style="display: flex; align-items: center; white-space: nowrap">
                                鞋型编号查询：<el-input
                                    v-model="inheritIdSearch"
                                    placeholder=""
                                    size="default"
                                    :suffix-icon="Search"
                                    clearable
                                    @change="filterMaterialStorage"
                                ></el-input>
                            </div>
                        </el-col>
                    </el-row>
                    <el-row :gutter="20" style="margin-top: 20px">
                        <el-col :span="24" :offset="0">
                            <el-table
                                v-loading="datafinished"
                                :data="materialStorageData"
                                border
                                style="height: 450px"
                            >
                                <el-table-column
                                    prop="materialType"
                                    label="材料类型"
                                ></el-table-column>
                                <el-table-column
                                    prop="materialName"
                                    label="材料名称"
                                ></el-table-column>
                                <el-table-column
                                    prop="materialSpecification"
                                    label="材料规格"
                                ></el-table-column>
                                <el-table-column
                                    prop="warehouseName"
                                    label="仓库名称"
                                ></el-table-column>
                                <el-table-column
                                    prop="unit"
                                    label="单位"
                                    width="75"
                                ></el-table-column>
                                <el-table-column
                                    prop="amountRemain"
                                    label="剩余数量"
                                ></el-table-column>
                                <el-table-column
                                    prop="unitPrice"
                                    label="采购单价"
                                ></el-table-column>
                                <el-table-column
                                    prop="valueRemain"
                                    label="剩余价值"
                                ></el-table-column>
                                <el-table-column
                                    prop="factoryName"
                                    label="厂家名称"
                                ></el-table-column>
                                <el-table-column prop="OrderId" label="订单编号"></el-table-column>
                                <el-table-column
                                    prop="inheritId"
                                    label="鞋型编号"
                                ></el-table-column>
                            </el-table>
                        </el-col>
                    </el-row>
                    <el-row :gutter="20">
                        <el-col :span="12" :offset="10">
                            <el-pagination
                                :total="materialStorageTotal"
                                :page-size="10"
                                :v-model:current-page="currentPage2"
                                @current-change="handleCurrentChange2"
                            >
                            </el-pagination>
                        </el-col>
                    </el-row>
                </el-tab-pane> </el-tabs
        ></el-col>
    </el-row>
    <el-dialog title="添加新材料类型" v-model="isAddNewMaterialTypeDialogVisible" width="30%">
        <el-form :model="newMaterialTypeForm" label-width="80px">
            <el-form-item label="材料类型" required>
                <el-input
                    v-model="newMaterialTypeForm.materialType"
                    placeholder="请输入材料类型"
                ></el-input>
            </el-form-item>
            <el-form-item label="仓库名称" required>
                <el-select v-model="newMaterialTypeForm.warehouseName" placeholder="请选择仓库名称">
                    <el-option
                        v-for="item in warehouseOptions"
                        :key="item.value"
                        :label="item.label"
                        :value="item.value"
                    ></el-option>
                </el-select>
            </el-form-item>
        </el-form>
        <el-table :data="materialTypeData" border height="300" v-loading="materialTypeDataFinished">
            <el-table-column prop="materialType" label="材料类型"></el-table-column>
            <el-table-column prop="warehouseName" label="仓库名称"></el-table-column>
        </el-table>
        <template #footer>
            <span>
                <el-button @click="cancelCreateNewMaterialType">取消</el-button>
                <el-button type="primary" @click="confirmCreateNewMaterialType">确认</el-button>
            </span>
        </template>
    </el-dialog>

    <el-dialog title="批量添加新材料" v-model="newMaterialVis" width="90%">
        <el-table :data="newMaterialData" border>
            <el-table-column prop="warehouseName" label="仓库名称"> </el-table-column>
            <el-table-column label="材料类型">
                <template #default="scope">
                    <el-select
                        v-model="scope.row.materialType"
                        placeholder="请输入以查找材料类型"
                        clearable
                        filterable
                        @change="fillMaterialWarehouse(scope.row)"
                    >
                        <el-option
                            v-for="item in materialTypeSelectOption"
                            :key="item.value"
                            :label="item.label"
                            :value="item.value"
                        >
                        </el-option>
                    </el-select>
                </template>
            </el-table-column>
            <el-table-column label="材料名称">
                <template #default="scope">
                    <el-input
                        v-model="scope.row.materialName"
                        placeholder=""
                        size="default"
                        clearable
                        @input="scope.row.existenceStatus = 'unchecked'"
                    ></el-input>
                </template>
            </el-table-column>
            <el-table-column label="单位">
                <template #default="scope">
                    <el-input
                        v-model="scope.row.unit"
                        placeholder=""
                        size="default"
                        clearable
                    ></el-input> </template
            ></el-table-column>
            <el-table-column label="厂家名称">
                <template #default="scope">
                    <el-select
                        v-model="scope.row.factoryName"
                        placeholder=""
                        filterable
                        @change="scope.row.existenceStatus = 'unchecked'"
                    >
                        <el-option
                            v-for="item in factoryOptions"
                            :key="item.value"
                            :label="item.label"
                            :value="item.value"
                        >
                        </el-option>
                    </el-select>
                </template>
            </el-table-column>
            <el-table-column label="材料分类" width="150">
                <template #default="scope">
                    <el-select v-model="scope.row.materialCategory" placeholder="" filterable>
                        <el-option
                            v-for="item in materialCategoryOptions"
                            :key="item.value"
                            :label="item.label"
                            :value="item.value"
                        >
                        </el-option>
                    </el-select>
                </template>
            </el-table-column>
            <el-table-column label="操作">
                <template #default="scope">
                    <el-button
                        type="danger"
                        @click="deleteCurrentRow(scope.$index, newMaterialData)"
                        >删除</el-button
                    >
                    <el-button type="warning" @click="checkSimilarMaterials(scope.row)"
                        >相似材料检测</el-button
                    >
                </template></el-table-column
            >
            <el-table-column label="存在检验">
                <template #default="scope">
                    <el-icon
                        v-if="scope.row.existenceStatus === 'same'"
                        :size="20"
                        class="status-icon"
                    >
                        <Close />
                    </el-icon>
                    <el-icon
                        v-if="scope.row.existenceStatus === 'none'"
                        :size="20"
                        class="status-icon"
                    >
                        <Check />
                    </el-icon>
                    <el-button
                        v-if="scope.row.existenceStatus === 'similar'"
                        type="warning"
                        size="default"
                        @click="openRowSimilarMaterials(scope.row)"
                    >
                        相似材料
                    </el-button>
                    <el-button
                        v-if="scope.row.existenceStatus === 'similar'"
                        type="success"
                        size="default"
                        @click="
                            (scope.row.existenceStatus = 'none'), (scope.row.similiarMaterials = [])
                        "
                        >确认材料</el-button
                    >
                </template>
            </el-table-column>
        </el-table>
        <el-button type="primary" size="default" @click="addNewMaterial">添加新材料</el-button>

        <template #footer>
            <span>
                <el-button @click="cancelCreateNewMaterials">取消</el-button>
                <el-button type="primary" @click="addmaterialSubmit">确认</el-button>
            </span>
        </template>
    </el-dialog>
    <el-dialog title="相似材料" v-model="isSimilarMaterialDialogVisible" width="30%">
        <el-table :data="materialSimiliarData" border>
            <el-table-column prop="materialName" label="材料名称"></el-table-column>
            <el-table-column prop="factoryName" label="厂家名称"></el-table-column>
        </el-table>
        <template #footer>
            <span>
                <el-button @click="isSimilarMaterialDialogVisible = false">取消</el-button>
                <el-button type="primary" @click="isSimilarMaterialDialogVisible = false"
                    >确认</el-button
                >
            </span>
        </template>
    </el-dialog>
    <el-dialog title="编辑材料" v-model="isModifyMaterialTypeDialogVisible" width="20%">
        <el-form :model="editMaterialForm" size="normal">
            <el-form-item label="旧材料名称">
                <el-text>{{ editMaterialForm.materialOldName }}</el-text>
            </el-form-item>
            <el-form-item label="更改材料名称">
                <el-input v-model="editMaterialForm.materialName"></el-input>
            </el-form-item>
            <el-form-item label="更改材料单位">
                <el-input v-model="editMaterialForm.materialUnit"></el-input>
            </el-form-item>
            <el-form-item label="材料厂家">
                <el-text>{{ editMaterialForm.materialFactory }}</el-text>
            </el-form-item>
            <el-form-item label="">
                <el-button type="primary" size="default" @click="checkMaterialName"
                    >检查材料名称</el-button
                >

                <el-icon
                    v-if="editMaterialForm.existenceStatus === 'same'"
                    :size="20"
                    class="status-icon"
                >
                    <Close />
                </el-icon>
                <el-icon
                    v-if="editMaterialForm.existenceStatus === 'none'"
                    :size="20"
                    class="status-icon"
                >
                    <Check />
                </el-icon>
                <el-button
                    v-if="editMaterialForm.existenceStatus === 'similar'"
                    type="warning"
                    size="default"
                    @click="openRowSimilarMaterials(scope.row)"
                >
                    相似材料
                </el-button>
                <el-button
                    v-if="editMaterialForm.existenceStatus === 'similar'"
                    type="success"
                    size="default"
                    @click="
                        (editMaterialForm.existenceStatus = 'none'),
                            (editMaterialForm.similiarMaterials = [])
                    "
                    >确认材料</el-button
                >
            </el-form-item>
        </el-form>

        <template #footer>
            <span>
                <el-button @click="isModifyMaterialTypeDialogVisible = false">取消</el-button>
                <el-button type="primary" @click="editMaterialSubmit">确认</el-button>
            </span>
        </template>
    </el-dialog>
</template>

<script>
import { Check, Close, Search } from '@element-plus/icons-vue'
import axios from 'axios'
export default {
    data() {
        return {
            Check,
            Close,
            materialCategoryOptions: [
                { value: 0, label: '普通材料' },
                { value: 1, label: '分尺码材料' }
            ],
            materialTypeSelectOption: [],
            materialTypeData: [],
            materialTotal: 0,
            materialStorageTotal: 0,
            datafinished: true,
            materialTypeDataFinished: true,
            newMaterialTypeForm: {
                materialType: '',
                materialCategory: '',
                warehouseName: ''
            },
            editMaterialForm: {
                materialOldName: '',
                materialName: '',
                materialUnit: '',
                materialFactory: '',
                existenceStatus: 'unchecked'
            },
            isModifyMaterialTypeDialogVisible: false,
            isAddNewMaterialTypeDialogVisible: false,
            isSimilarMaterialDialogVisible: false,
            materialSimiliarData: [],
            materialTypeFilterData: [],
            materialTypeAllData: [],
            materialStorageData: [],
            materialStorageAllData: [],
            materialNameSearch: '',
            warehouseNameSearch: '',
            factoryNameSearch: '',
            materialTypeSearch: '',
            specificationNameSearch: '',
            Search,
            tabName: '材料类型管理',
            newMaterialVis: false,
            newMaterialData: [],
            warehouseOptions: [],
            factoryOptions: [],
            currentPage1: 1,
            currentPage2: 1
        }
    },
    async mounted() {
        await this.getMaterialTypeData()
        this.getAllFactoryName()
        this.getAllWarehouseName()
        this.handleTypeToOptions()
        this.getMaterialStorageData()
        this.handleCurrentChange1(1)
        this.handleCurrentChange2(1)
    },
    methods: {
        async checkMaterialName() {
            const response = await axios.post(`${this.$apiBaseUrl}/logistics/checkmaterial`, {
                materialname: this.editMaterialForm.materialName,
                factoryname: this.editMaterialForm.materialFactory
            })
            if (response.data.message === 'same') {
                this.$message({
                    type: 'success',
                    message: '该材料已存在'
                })
                this.editMaterialForm.existenceStatus = 'same'
            } else if (response.data.message === 'none') {
                this.$message({
                    type: 'success',
                    message: '该材料不存在'
                })
                this.editMaterialForm.existenceStatus = 'none'
            } else {
                this.$message({
                    type: 'success',
                    message: '该材料存在相似材料'
                })
                this.editMaterialForm.existenceStatus = 'similar'
                this.editMaterialForm.similiarMaterials = response.data.similarMaterials
            }
        },
        fillMaterialWarehouse(row) {
            const warehouseName = this.materialTypeSelectOption.find(
                (option) => option.value === row.materialType
            )?.warehouse
            if (warehouseName) {
                row.warehouseName = warehouseName
            }
        },
        async handleTypeToOptions() {
            await this.getAllMaterialType()
            this.materialTypeSelectOption = this.materialTypeData.map((item) => {
                return {
                    value: item.materialType,
                    label: item.materialType,
                    warehouse: item.warehouseName
                }
            })
            console.log(this.materialTypeSelectOption)
        },
        async getAllWarehouseName() {
            const response = await axios.get(`${this.$apiBaseUrl}/logistics/allwarehousenames`)
            this.warehouseOptions = response.data
        },
        async getAllFactoryName() {
            const response = await axios.get(`${this.$apiBaseUrl}/logistics/allfactorynames`)
            this.factoryOptions = response.data
        },
        async getAllMaterialType() {
            const response = await axios.get(`${this.$apiBaseUrl}/logistics/allmaterialtypes`)
            this.materialTypeData = response.data
            this.materialTypeDataFinished = false
        },
        async getMaterialTypeData() {
            this.datafinished = true
            const response = await axios.get(`${this.$apiBaseUrl}/logistics/allmaterial`)
            this.materialTypeFilterData = response.data.materials
            this.materialTypeAllData = response.data.materials
            this.materialTotal = response.data.amount
            this.datafinished = false
        },
        async getMaterialStorageData() {
            this.datafinished = true
            const response = await axios.get(`${this.$apiBaseUrl}/logistics/allmaterialstorage`)
            this.materialStorageData = response.data
            this.materialStorageAllData = response.data
            this.materialStorageTotal = response.data.length
            this.datafinished = false
        },
        openNewMaterialTypeDialog() {
            this.isAddNewMaterialTypeDialogVisible = true
            this.getAllMaterialType()
        },
        openNewMaterialDialog() {
            this.newMaterialVis = true
        },
        openMaterialTypeEditDialog(row) {
            this.isModifyMaterialTypeDialogVisible = true
            this.editMaterialForm.materialOldName = row.materialName
            this.editMaterialForm.materialName = row.materialName
            this.editMaterialForm.materialUnit = row.unit
            this.editMaterialForm.materialFactory = row.factoryName
        },
        async filterMaterialStorage() {
            this.datafinished = true
            const response = await axios.get(`${this.$apiBaseUrl}/logistics/allmaterialstorage`, {
                params: {
                    materialtype: this.materialTypeSearch,
                    materialname: this.materialNameSearch,
                    materialspec: this.specificationNameSearch,
                    warehousename: this.warehouseNameSearch,
                    factoryname: this.factoryNameSearch,
                    orderid: this.orderRIdSearch,
                    ordershoeid: this.inheritIdSearch
                }
            })
            this.materialStorageData = response.data
            this.materialStorageAllData = response.data
            this.materialStorageTotal = response.data.length
            this.datafinished = false
        },
        async filterMaterialType() {
            this.datafinished = true
            const response = await axios.get(`${this.$apiBaseUrl}/logistics/allmaterial`, {
                params: {
                    materialname: this.materialNameSearch,
                    warehousename: this.warehouseNameSearch,
                    factoryname: this.factoryNameSearch,
                    materialtype: this.materialTypeSearch
                }
            })
            this.materialTypeFilterData = response.data.materials
            this.materialTypeAllData = response.data.materials
            this.materialTotal = response.data.amount
            this.datafinished = false
        },
        async addNewMaterialType() {
            const response = await axios.post(
                `${this.$apiBaseUrl}/logistics/addmaterialtype`,
                this.newMaterialTypeForm
            )
            if (response.status === 200) {
                this.$message({
                    type: 'success',
                    message: '添加成功'
                })
                this.isAddNewMaterialTypeDialogVisible = false
                this.getMaterialTypeData()
            } else {
                this.$message({
                    type: 'error',
                    message: '添加失败'
                })
            }
        },
        async checkSimilarMaterials(row) {
            const response = await axios.post(`${this.$apiBaseUrl}/logistics/checkmaterial`, {
                materialname: row.materialName,
                factoryname: row.factoryName
            })
            if (response.data.message === 'same') {
                this.$message({
                    type: 'success',
                    message: '该材料已存在'
                })
                row.existenceStatus = 'same'
            } else if (response.data.message === 'none') {
                this.$message({
                    type: 'success',
                    message: '该材料不存在'
                })
                row.existenceStatus = 'none'
            } else {
                this.$message({
                    type: 'success',
                    message: '该材料存在相似材料'
                })
                row.existenceStatus = 'similar'
                row.similiarMaterials = response.data.similarMaterials
            }
        },
        confirmCreateNewMaterialType() {
            this.$confirm('确定添加新材料类型吗？', '提示', {
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                type: 'warning'
            })
                .then(() => {
                    this.addNewMaterialType()
                })
                .catch(() => {
                    this.$message({
                        type: 'info',
                        message: '已取消添加'
                    })
                })
        },
        cancelCreateNewMaterialType() {
            this.newMaterialTypeForm.materialType = ''
            this.newMaterialTypeForm.warehouseName = ''
            this.isAddNewMaterialTypeDialogVisible = false
        },
        cancelCreateNewMaterials() {
            this.newMaterialData = []
            this.newMaterialVis = false
        },
        async addNewMaterial() {
            // Validate that all existing rows have non-empty fields
            for (const row of this.newMaterialData) {
                if (!row.materialName || !row.warehouseName || !row.unit || !row.factoryName) {
                    this.$message({
                        type: 'warning',
                        message: '请填写所有字段'
                    })
                    return
                }
                if (row.existenceStatus === 'unchecked') {
                    await this.checkSimilarMaterials(row)
                }
                if (row.existenceStatus === 'same' || row.existenceStatus === 'similar') {
                    this.$message({
                        type: 'warning',
                        message: '存在相同或相似材料，请检查'
                    })
                    return
                }
            }
            // If validation passes, add a new row
            this.newMaterialData.push({
                materialName: '',
                warehouseName: '',
                materialType: '',
                unit: '',
                factoryName: '询价',
                existenceStatus: 'unchecked',
                materialCategory: 0,
                similiarMaterials: []
            })
        },
        openRowSimilarMaterials(row) {
            this.isSimilarMaterialDialogVisible = true
            this.materialSimiliarData = row.similiarMaterials
        },
        deleteCurrentRow(index, datafield) {
            this.$confirm('确定删除此行吗？', '提示', {
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                type: 'warning'
            })
                .then(() => {
                    datafield.splice(index, 1)
                    this.$message({
                        type: 'success',
                        message: '删除成功!'
                    })
                })
                .catch(() => {
                    this.$message({
                        type: 'info',
                        message: '已取消删除'
                    })
                })
        },
        async addmaterialSubmit() {
            for (const row of this.newMaterialData) {
                console.log(row)
                if (!row.materialName || !row.warehouseName || !row.unit || !row.factoryName) {
                    this.$message({
                        type: 'warning',
                        message: '请填写所有字段'
                    })
                    return
                }
                if (row.existenceStatus === 'unchecked') {
                    await this.checkSimilarMaterials(row)
                }
                if (row.existenceStatus === 'same' || row.existenceStatus === 'similar') {
                    this.$message({
                        type: 'warning',
                        message: '存在相同或相似材料，请检查'
                    })
                    return
                }
            }
            this.$confirm('确定添加新材料吗？', '提示', {
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                type: 'warning'
            })
                .then(async () => {
                    const response = await axios.post(`${this.$apiBaseUrl}/logistics/addmaterial`, {
                        materials: this.newMaterialData
                    })
                    console.log(response.status)
                    if (response.status === 200) {
                        this.$message({
                            type: 'success',
                            message: '添加成功'
                        })
                        this.newMaterialData = []
                        this.newMaterialVis = false
                        this.getMaterialTypeData()
                    } else {
                        this.$message({
                            type: 'error',
                            message: '添加失败'
                        })
                    }
                })
                .catch(() => {
                    this.$message({
                        type: 'info',
                        message: '已取消添加'
                    })
                })
        },
        async editMaterialSubmit() {
            if (!this.editMaterialForm.materialName || !this.editMaterialForm.materialUnit) {
                this.$message({
                    type: 'warning',
                    message: '请填写所有字段'
                })
                return
            }
            if (this.editMaterialForm.existenceStatus === 'unchecked') {
                await this.checkMaterialName()
            }
            if (
                this.editMaterialForm.existenceStatus === 'same' ||
                this.editMaterialForm.existenceStatus === 'similar'
            ) {
                this.$message({
                    type: 'warning',
                    message: '存在相同或相似材料，请检查'
                })
                return
            }
            this.$confirm('确定修改材料吗？', '提示', {
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                type: 'warning'
            })
                .then(async () => {
                    const response = await axios.patch(
                        `${this.$apiBaseUrl}/logistics/editmaterialtype`,
                        {
                            materialoldname: this.editMaterialForm.materialOldName,
                            materialname: this.editMaterialForm.materialName,
                            unit: this.editMaterialForm.materialUnit
                        }
                    )
                    if (response.status === 200) {
                        this.$message({
                            type: 'success',
                            message: '修改成功'
                        })
                        this.editMaterialForm.materialOldName = ''
                        this.editMaterialForm.materialName = ''
                        this.editMaterialForm.materialUnit = ''
                        this.editMaterialForm.materialFactory = ''
                        this.isModifyMaterialTypeDialogVisible = false
                        this.getMaterialTypeData()
                    } else {
                        this.$message({
                            type: 'error',
                            message: '修改失败'
                        })
                    }
                })
                .catch(() => {
                    this.$message({
                        type: 'info',
                        message: '已取消修改'
                    })
                })
        },
        handleCurrentChange1(val) {
            this.currentPage1 = val
            console.log(this.materialTypeAllData)
            this.materialTypeFilterData = this.materialTypeAllData.slice(
                (this.currentPage1 - 1) * 10,
                this.currentPage1 * 10
            )
        },
        handleCurrentChange2(val) {
            this.currentPage2 = val
            this.materialStorageData = this.materialStorageAllData.slice(
                (this.currentPage2 - 1) * 10,
                this.currentPage2 * 10
            )
        }
    }
}
</script>
