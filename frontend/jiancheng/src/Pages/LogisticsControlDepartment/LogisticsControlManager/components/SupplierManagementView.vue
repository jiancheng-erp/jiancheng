<template>
    <el-row :gutter="20">
        <el-col :span="24" :offset="0" style="font-size: xx-large; text-align: center;">供应商管理</el-col>
    </el-row>
    <el-row :gutter="20" style="margin-top: 20px;">
        <el-col :span="24" :offset="0">
            <el-table :data="supplierData" border style="height: 500px;" v-loading="datafinished">
                <el-table-column prop="supplierName" label="供应商名称"></el-table-column>
                <el-table-column prop="supplierField" label="供应商供货类型"></el-table-column>
            </el-table>
        </el-col>
    </el-row>
    <el-row :gutter="20" style="margin-top: 20px;">
        <el-col :span="4" :offset="20"><el-button type="primary" size="default"
                @click="isCreateSupplierDialogVisible = true">创建新供应商</el-button>
        </el-col>
    </el-row>
    <el-dialog
        title="创建新供应商"
        v-model="isCreateSupplierDialogVisible"
        width="30%">
        <el-form>
            <el-form-item label="供应商名称: ">
                <el-input v-model="addSupplierData.supplierName"></el-input>
            </el-form-item>
            <el-form-item label="供应商供货类型: ">
                <el-select v-model="addSupplierData.supplierField" placeholder="请选择供货类型">
                    <el-option v-for="item in FieldData" :key="item.value" :label="item.label" :value="item.value">
                    </el-option>
                    </el-select>
            </el-form-item>
            </el-form>
        <template #footer>
        <span>
            <el-button @click="cancelCreateSupplier">取消</el-button>
            <el-button type="primary" @click="confirmSubmit">确认</el-button>
        </span>
        </template>
    </el-dialog>
    
</template>

<script>
import axios from 'axios'
import { ElMessageBox } from 'element-plus';
export default {
    data() {
        return {
            datafinished: true,
            isCreateSupplierDialogVisible: false,
            supplierData: [],
            addSupplierData: {
                supplierName: '',
                supplierField: ''
            },
            FieldData: [
                {
                    value: 'N',
                    label: '普通供货商'
                },
            ]
        }
    },
    mounted() {
        this.getSupplierData()
    },
    methods: {
        async getSupplierData() {
            const response = await axios.get('http://localhost:8000/logistics/allsuppliers')
            console.log(response)
            this.supplierData = response.data
            this.datafinished = false

        },
        async createSupplier() {
            this.datafinished = true
            const response = await axios.post('http://localhost:8000/logistics/createsupplier', this.addSupplierData)
            console.log(response)
            this.isCreateSupplierDialogVisible = false
            this.getSupplierData()
        },
        cancelCreateSupplier() {
            this.addSupplierData.supplierName = ''
            this.addSupplierData.supplierField = ''
            this.isCreateSupplierDialogVisible = false
        },
        confirmSubmit() {
            ElMessageBox.confirm('确认提交吗?', '提示', {
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                type: 'warning'
            }).then(() => {
                this.createSupplier()
            }).catch(() => {
                this.$message({
                    type: 'info',
                    message: '已取消提交'
                });
            });
        }
    }
}
</script>
