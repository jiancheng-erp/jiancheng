<template>
    <el-row :gutter="20">
        <el-col :span="24" :offset="0">
            <el-table :data="logisticsMaterialData" border stripe>
                <el-table-column prop="orderRId" label="订单号" width="100"></el-table-column>
                <!-- <el-table-column prop="materialType" label="材料类型"></el-table-column> -->
                <el-table-column prop="materialName" label="材料名称"></el-table-column>
                <el-table-column prop="materialModel" label="型号"></el-table-column>
                <el-table-column prop="materialSpecification" label="规格"></el-table-column>
                <el-table-column prop="colorName" label="颜色"></el-table-column>
                <el-table-column prop="materialUnit" label="材料单位"></el-table-column>
                <el-table-column prop="supplierName" label="供应商名称"></el-table-column>
                <el-table-column prop="estimatedInboundAmount" label="采购数量"></el-table-column>
                <el-table-column prop="actualInboundAmount" label="入库数量"></el-table-column>
                <el-table-column prop="currentAmount" label="库存"></el-table-column>
            </el-table>
        </el-col>
    </el-row>
    <el-row :gutter="20">
        <el-col :span="12">
            <el-pagination @size-change="handleLogisticsSizeChange" @current-change="handleLogisticsPageChange"
                :current-page="logisticsCurrentPage" :page-sizes="[10, 20, 30, 40]" :page-size="logisticsPageSize"
                layout="total, sizes, prev, pager, next, jumper" :total="logisticsRows" />
        </el-col>
    </el-row>
    <el-row :gutter="20">
        <el-col>
            <span style="font-weight: bold; color: red;">
                找不到材料？使用以下库存表格搜索材料。
            </span>
        </el-col>
    </el-row>
    <el-row :gutter="20">
        <el-col>
            <MaterialStorage />
        </el-col>
    </el-row>
</template>
<script>
import axios from 'axios'
import MaterialStorage from '@/Pages/TotalWarehouse/HeadOfWarehouse/components/MaterialStorage.vue'
export default {
    components: {
        MaterialStorage
    },
    props: {
        currentRow: {
            type: Object,
            required: true,
        },
    },
    data(){
        return {
            logisticsCurrentPage: 1,
            logisticsPageSize: 10,
            logisticsRows: 0,
            logisticsMaterialData: []
        }
    },
    async mounted() {
        this.viewLogisticDetail()
    },
    methods: {
        async viewLogisticDetail() {
            console.log(this.currentRow)
            const params = {
                "page": this.logisticsCurrentPage,
                "pageSize": this.logisticsPageSize,
                "orderRId": this.currentRow.orderRId,
                "shoeRId": this.currentRow.shoeRId
            }
            const response = await axios.get(`${this.$apiBaseUrl}/warehouse/warehousemanager/getallmaterialinfo`, { params })
            this.logisticsMaterialData = response.data.result
            this.logisticsRows = response.data.total
            console.log(this.logisticsMaterialData)
        },
        async handleLogisticsSizeChange(val) {
            this.logisticsPageSize = val
            await this.viewLogisticDetail()
        },
        async handleLogisticsPageChange(val) {
            this.logisticsCurrentPage = val
            await this.viewLogisticDetail()
        },
    },
}
</script>