<template>
    <el-row :gutter="20">
        <el-col :span="24" :offset="0" style="font-size: xx-large; text-align: center">统一入库界面</el-col>
    </el-row>
    <el-row :gutter="20">
        <el-col :span="6" :offset="0">
            <el-button-group>
                <el-button type="primary" size="default" @click="isMaterialDialogVisible = true">材料入库筛选</el-button>
            </el-button-group>
        </el-col>
        <el-col :span="4" :offset="2" style="white-space: nowrap;">
            订单号筛选：
            <el-input v-model="orderNumberSearch" placeholder="请输入订单号" clearable
                @keypress.enter="getMaterialTableData()" />
        </el-col>
        <el-col :span="4" :offset="2" style="white-space: nowrap;">
            鞋型号筛选：
            <el-input v-model="shoeNumberSearch" placeholder="请输入鞋型号" clearable
                @keypress.enter="getMaterialTableData()" />
        </el-col>
        <el-col :span="4" :offset="2" style="white-space: nowrap;">
            <el-button type="primary" @click="getMaterialTableData()">搜索</el-button>
        </el-col>
    </el-row>
    <el-row :gutter="20">
        <el-col :span="24" :offset="0">
            <el-table :data="materialTableData" border stripe height="500">
                <el-table-column prop="materialType" label="材料类型"></el-table-column>
                <el-table-column prop="materialName" label="材料名称"></el-table-column>
                <el-table-column prop="materialSpecification" label="材料规格"></el-table-column>
                <el-table-column prop="materialUnit" label="材料单位"></el-table-column>

                <el-table-column prop="estimatedInboundAmount" label="材料应入库数量"
                    :formatter="formatDecimal"></el-table-column>
                <el-table-column prop="actualInboundAmount" label="材料实入库数量"
                    :formatter="formatDecimal"></el-table-column>
                <el-table-column prop="currentAmount" label="材料库存" :formatter="formatDecimal"></el-table-column>
                <el-table-column prop="unitPrice" label="材料单价" :formatter="formatDecimal"></el-table-column>
                <el-table-column prop="totalPrice" label="材料总价" :formatter="formatDecimal"></el-table-column>
                <el-table-column prop="supplierName" label="材料供应商"></el-table-column>
                <el-table-column prop="orderRId" label="材料订单号"></el-table-column>
                <el-table-column prop="shoeRId" label="材料鞋型号"></el-table-column>
                <el-table-column prop="status" label="入库状态"></el-table-column>
                <el-table-column label="操作">
                    <template #default="scope">
                        <el-button type="primary" size="small" @click="editMaterial(scope.row)">入库</el-button>
                    </template>
                </el-table-column>
            </el-table>
            <el-row :gutter="20">
                <el-col :span="12" :offset="14">
                    <el-pagination @size-change="handleSizeChange" @current-change="handlePageChange"
                        :current-page="currentPage" :page-sizes="[10, 20, 30, 40]" :page-size="pageSize"
                        layout="total, sizes, prev, pager, next, jumper" :total="materialTableData.length" />
                </el-col>
            </el-row>
        </el-col>
    </el-row>
    <el-dialog title="材料入库筛选" v-model="isMaterialDialogVisible" width="30%">
        请选择材料类型：
        <el-select v-model="materialTypeSearch" value-key="" placeholder="" clearable filterable
            @keypress.enter="getMaterialTableData()">
            <el-option v-for="item in materialTypeOptions" :value="item" />
        </el-select>
        请选择材料名称：
        <el-input v-model="materialNameSearch" placeholder="" clearable @keypress.enter="getMaterialTableData()" />
        请选择材料规格：
        <el-input v-model="materialSpecificationSearch" placeholder="" clearable
            @keypress.enter="getMaterialTableData()" />
        请选择材料供应商：
        <el-select v-model="materialSupplierSearch" value-key="" placeholder="" clearable filterable
            @keypress.enter="getMaterialTableData()">
            <el-option v-for="item in materialSupplierOptions" :value="item" />
        </el-select>

        <template #footer>
            <span>
                <el-button type="primary" @click="isMaterialDialogVisible = false">返回</el-button>
            </span>
        </template>
    </el-dialog>
    <el-dialog title="入库对话框" v-model="isInboundDialogVisible" width="30%">
        <el-form-item label="入库数量">
            <el-input v-model="inboundForm.quantity" placeholder="请输入入库数量"></el-input>
        </el-form-item>
        <el-form-item label="入库日期">
            <el-date-picker v-model="inboundForm.date" type="date" placeholder="选择日期" value-format="YYYY-MM-DD"></el-date-picker>
        </el-form-item>
        <el-form-item label="入库类型">
            <el-radio-group v-model="inboundForm.inboundType">
                <el-radio label="1">采购入库</el-radio>
                <el-radio label="2">生产剩余</el-radio>
            </el-radio-group>
        </el-form-item>
        <template #footer>
            <span>
                <el-button @click="cancelInbound">取消</el-button>
                <el-button type="primary" @click="submitInboundForm">确定</el-button>
            </span>
        </template>
    </el-dialog>
    <el-dialog title="多鞋码入库对话框" v-model="isMultiInboundDialogVisible" width="50%">
        <el-table :data="multipleInboundForm" border stripe>
            <el-table-column prop="shoeSize" label="鞋码"></el-table-column>
            <el-table-column prop="internalSize" label="内码"></el-table-column>
            <el-table-column prop="externalSize" label="外显"></el-table-column>
            <el-table-column prop="predictQuantity" label="预计数量"></el-table-column>
            <el-table-column prop="actualQuantity" label="实际数量"></el-table-column>
            <el-table-column prop="currentQuantity" label="当前数量"></el-table-column>
            <el-table-column label="入库数量">
                <template #default="scope">
                    <el-input v-model="scope.row.inboundQuantity" placeholder="请输入入库数量"></el-input>
                </template>
            </el-table-column>
        </el-table>

        <el-form-item label="入库日期">
            <el-date-picker v-model="inboundForm.date" type="date" placeholder="选择日期" value-format="YYYY-MM-DD"></el-date-picker>
        </el-form-item>
        <el-form-item label="入库类型">
            <el-radio-group v-model="inboundForm.inboundType">
                <el-radio value="1">采购入库</el-radio>
                <el-radio value="2">生产剩余</el-radio>
            </el-radio-group>
        </el-form-item>
        <template #footer>
            <span>
                <el-button @click="cancelInbound">取消</el-button>
                <el-button type="primary" @click="submitSizeInboundForm">确定</el-button>
            </span>
        </template>
    </el-dialog>
</template>
<script>
import axios from 'axios';
export default {
    data() {
        return {
            isMultiInboundDialogVisible: false,
            isInboundDialogVisible: false,
            orderNumberSearch: '',
            shoeNumberSearch: '',
            materialTypeSearch: '',
            materialNameSearch: '',
            materialSpecificationSearch: '',
            materialSupplierSearch: '',
            multipleInboundForm: [],
            materialTypeOptions: [],
            materialSupplierOptions: [],
            isMaterialDialogVisible: false,
            pageSize: 10,
            currentPage: 1,
            inboundForm: {
                quantity: '',
                date: '',
                inboundType: ''
            },
            materialTableData: [],
            currentRow: {}
        }
    },
    mounted() {
        this.getAllMaterialTypes()
        this.getAllSuppliers()
        this.getMaterialTableData()
    },
    methods: {
        async getAllMaterialTypes() {
            const response = await axios.get("http://localhost:8000/warehouse/warehousemanager/getallmaterialtypes")
            this.materialTypeOptions = response.data
        },
        async getAllSuppliers() {
            const response = await axios.get("http://localhost:8000/warehouse/warehousemanager/getallsuppliernames")
            this.materialSupplierOptions = response.data
        },
        async getMaterialTableData() {
            const params = {
                "page": this.currentPage,
                "pageSize": this.pageSize,
                "materialType": this.materialTypeSearch,
                "materialName": this.materialNameSearch,
                "materialSpec": this.materialSpecificationSearch,
                "supplier": this.materialSupplierSearch,
                "orderRId": this.orderNumberSearch,
                "shoeRId": this.shoeNumberSearch
            }
            const response = await axios.get("http://localhost:8000/warehouse/warehousemanager/getmaterialinboundoverview", { params })
            this.materialTableData = response.data
        },
        async submitInboundForm() {
            let data = {
                "materialStorageId": this.currentRow.materialStorageId,
                "date": this.inboundForm.date,
                "amount": this.inboundForm.quantity,
                "type": this.inboundForm.inboundType
            }
            const response = await axios.patch("http://localhost:8000/warehouse/warehousemanager/inboundmatieral", data)
            console.log(response)
        },
        async submitSizeInboundForm() {
            let data = {
                "sizeMaterialStorageId": this.currentRow.materialStorageId,
                "date": this.inboundForm.date,
                "type": this.inboundForm.inboundType
            }
            this.multipleInboundForm.forEach(row => {
                if (row.inboundQuantity) {
                    data["size"+row.shoeSize+"Amount"] = row.inboundQuantity
                } else {
                    data["size"+row.shoeSize+"Amount"] = 0
                }
                
            })
            const response = await axios.patch("http://localhost:8000/warehouse/warehousemanager/inboundsizematieral", data)
            console.log(response)
        },
        handleSizeChange(val) {
            this.pageSize = val
            this.getMaterialTableData()
        },
        handlePageChange(val) {
            this.page = val
            this.getMaterialTableData()
        },

        formatDecimal(row, column, cellValue, index) {
            return Number(cellValue).toFixed(2)
        },
        async editMaterial(row) {
            if (row.materialCategory == 1) {
                const params = { "sizeMaterialStorageId": row.materialStorageId }
                const response = await axios.get("http://localhost:8000/warehouse/warehousemanager/getsizematerialbyid", { params })
                this.multipleInboundForm = response.data
                this.isMultiInboundDialogVisible = true
                this.currentRow = row
            } else {
                this.isInboundDialogVisible = true
                this.currentRow = row
            }
        },
    }
}
</script>
