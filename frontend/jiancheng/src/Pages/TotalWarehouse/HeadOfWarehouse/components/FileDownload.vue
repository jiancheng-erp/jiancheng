<template>
    <el-row :gutter="20">
        <el-col :span="4" :offset="0" style="white-space: nowrap;">
            <el-input v-model="orderRIdSearch" placeholder="请输入订单号" clearable @keypress.enter="getMaterialTableData()"
                @clear="getMaterialTableData()" />
        </el-col>
        <el-col :span="4" :offset="0" style="white-space: nowrap;">
            <el-input v-model="shoeRIdSearch" placeholder="请输入鞋型号" clearable @keypress.enter="getMaterialTableData()"
                @clear="getMaterialTableData()" />
        </el-col>
    </el-row>
    <el-row :gutter="20">
        <el-table :data="orderShoeTableData" border stripe height="600">
            <el-table-column prop="orderRId" label="订单号"></el-table-column>
            <el-table-column prop="shoeRId" label="鞋型号"></el-table-column>
            <el-table-column prop="orderStartDate" label="订单开始日期"></el-table-column>
            <el-table-column prop="orderEndDate" label="订单截止日期"></el-table-column>
            <el-table-column label="文件">
                <template #default="scope">
                    <el-button-group>
                        <el-button type="text" size="small" @click="downloadSecondBOM(scope.row)">生产BOM
                        </el-button>
                        <el-button type="text" size="small" @click="OpenCraftSheet(scope.row)">生产工艺单
                        </el-button>
                    </el-button-group>
                </template>
            </el-table-column>
        </el-table>
    </el-row>
</template>
<script>
import axios from 'axios';
import { ElMessage, ElMessageBox } from 'element-plus';
export default {
    data() {
        return {
            currentPage: 1,
            totalPages: 0,
            pageSize: 10,
            orderShoeTableData: [],
            orderRIdSearch: '',
            shoeRIdSearch: '',
        }
    },
    mounted() {
        this.getOrderShoeTableData()
    },
    methods: {
        async getOrderShoeTableData() {
            let params = {
                "page": this.currentPage,
                "pageSize": this.pageSize,
                "orderRId": this.orderRIdSearch,
                "shoeRId": this.shoeRIdSearch,
            }
            const response = await axios.get(`${this.$apiBaseUrl}/production/getallordershoeinfo`, { params })
            this.orderShoeTableData = response.data.result
            this.totalPages = response.data.length
            console.log(this.orderShoeTableData)
        },
        // downloadFirstBOM(row) {
        //     window.open(
        //         `${this.$apiBaseUrl}/firstbom/download?ordershoerid=${row.orderShoeId}&orderid=${row.orderId}`
        //     )
        // },
        downloadSecondBOM(row) {
            window.open(
                `${this.$apiBaseUrl}/secondbom/download?ordershoerid=${row.shoeRId}&orderid=${row.orderRId}`
            )
        },
        OpenCraftSheet(row) {
            let url = ''
            url = `${window.location.origin}/headofwarehouse/viewprocessheet/orderid=${row.orderId}`
            window.open(url, '_blank')
        },
        // downloadFirstMaterialSheet(row) {
        //     window.open(
        //         `${this.$apiBaseUrl}/firstpurchase/downloadmaterialstatistics?orderrid=${row.orderRId}&ordershoerid=${row.shoeRId}`
        //     )
        // },
        // downloadSecondMaterialSheet(row) {
        //     window.open(
        //         `${this.$apiBaseUrl}/secondpurchase/downloadmaterialstatistics?orderrid=${row.orderRId}&ordershoerid=${row.shoeRId}`
        //     )
        // }
    }
}
</script>
