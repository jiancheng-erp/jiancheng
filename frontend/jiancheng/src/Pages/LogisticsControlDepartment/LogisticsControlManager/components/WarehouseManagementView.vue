<template>
    <el-row :gutter="20">
        <el-col :span="24" :offset="0" style="font-size: xx-large; text-align: center"
            >材料仓库管理</el-col
        >
    </el-row>
    <el-row :gutter="20" style="margin-top: 20px">
        <el-col :span="24" :offset="0">
            <el-table :data="warehouseData" border style="height: 500px" v-loading="datafinished">
                <el-table-column prop="warehouseName" label="仓库名称"></el-table-column>
                <el-table-column prop="addDate" label="创建时间"></el-table-column>
            </el-table>
        </el-col>
    </el-row>
    <el-row :gutter="20" style="margin-top: 20px">
        <el-col :span="4" :offset="20"
            ><el-button type="primary" size="default" @click="openCreateDialog"
                >创建新仓库</el-button
            >
        </el-col>
    </el-row>

    <el-dialog title="创建新仓库" v-model="createVis" width="30%">
        <el-row :gutter="20">
            <el-col :span="3" :offset="0" style="white-space: nowrap">仓库名：</el-col>
            <el-col :span="12" :offset="0"
                ><el-input
                    v-model="warehouseName"
                    placeholder=""
                    size="default"
                    clearable
                ></el-input>
            </el-col>
        </el-row>
        <template #footer>
            <span>
                <el-button @click="cancelCreateWarehouse">取消</el-button>
                <el-button type="primary" @click="confirmSubmit">确认</el-button>
            </span>
        </template>
    </el-dialog>

</template>
<script>
import axios from 'axios'
import { ElMessageBox } from 'element-plus'
export default {
    data() {
        return {
            warehouseData: [],
            createVis: false,
            warehouseName: '',
            datafinished: true
        }
    },
    mounted() {
        this.getWarehouseData()
    },
    methods: {
        openCreateDialog() {
            this.createVis = true
        },
        async getWarehouseData() {
            const response = await axios.get('http://localhost:8000/logistics/allwarehouses')
            this.warehouseData = response.data
            this.datafinished = false
        },
        async createWarehouse() {
            this.datafinished = true
            const response = await axios.post('http://localhost:8000/logistics/addwarehouse', {
                warehouseName: this.warehouseName
            })
            console.log(response)
            this.createVis = false
            this.getWarehouseData()
        },
        cancelCreateWarehouse() {
            this.warehouseName = ''
            this.createVis = false
        },
        confirmSubmit() {
            ElMessageBox.confirm('确认提交吗?', '提示', {
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                type: 'warning'
            })
                .then(() => {
                    this.createWarehouse()
                })
                .catch(() => {
                    this.$message({
                        type: 'info',
                        message: '已取消提交'
                    })
                })
        }
    }
}
</script>
