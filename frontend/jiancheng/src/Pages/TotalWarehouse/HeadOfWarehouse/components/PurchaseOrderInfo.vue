<template>
    <el-row :gutter="20">
        <el-col :span="24" :offset="0" style="white-space: nowrap;">
            <div class="search-bar">
                <el-input v-model="orderRIdSearch" placeholder="订单号筛选" clearable @keypress.enter="getPurchaseOrderData()"
                    @clear="getPurchaseOrderData" />
                <el-input v-model="shoeRIdSearch" placeholder="鞋型号筛选" clearable @keypress.enter="getPurchaseOrderData()"
                    @clear="getPurchaseOrderData" />
                <el-input v-model="materialNameSearch" placeholder="材料名称筛选" clearable @keypress.enter="getPurchaseOrderData()"
                    @clear="getPurchaseOrderData" />
                <el-input v-model="materialModelSearch" placeholder="型号筛选" clearable @keypress.enter="getPurchaseOrderData()"
                    @clear="getPurchaseOrderData" />
                <el-input v-model="materialSpecSearch" placeholder="规格筛选" clearable @keypress.enter="getPurchaseOrderData()"
                    @clear="getPurchaseOrderData" />
                <el-input v-model="materialColorSearch" placeholder="颜色筛选" clearable @keypress.enter="getPurchaseOrderData()"
                    @clear="getPurchaseOrderData" />
                <el-input v-model="supplierNameSearch" placeholder="供应商筛选" clearable @keypress.enter="getPurchaseOrderData()"
                    @clear="getPurchaseOrderData" />
                <el-select v-model="statusSearch" placeholder="采购单状态筛选" filterable clearable @change="getPurchaseOrderData()"
                    @clear="getPurchaseOrderData">
                    <el-option v-for="item in ['未填写', '已保存', '已提交']"
                        :label="item" :value="item">
                    </el-option>
                </el-select>
            </div>
        </el-col>
    </el-row>
    <el-row :gutter="20" style="margin-top: 20px">
            <el-table :data="purchaseOrderData" border stripe height="500">
                <!-- <el-table-column prop="bomRId" label="BOM编号" width="100" show-overflow-tooltip></el-table-column> -->
                <el-table-column prop="purchaseOrderStatus" label="采购单状态"></el-table-column>
                <el-table-column prop="orderRId" label="订单号"></el-table-column>
                <el-table-column prop="shoeRId" label="鞋型号"></el-table-column>
                <el-table-column prop="supplierName" label="供应商"></el-table-column>
                <el-table-column prop="materialName" label="材料名称"></el-table-column>
                <el-table-column prop="materialModel" label="型号"></el-table-column>
                <el-table-column prop="materialSpecification" label="规格"></el-table-column>
                <el-table-column prop="materialColor" label="颜色"></el-table-column>
                <el-table-column prop="materialUnit" label="单位"></el-table-column>
                <el-table-column prop="purchaseAmount" label="采购数量"></el-table-column>
                <el-table-column prop="inboundAmount" label="已入库数量"></el-table-column>
                <el-table-column prop="currentAmount" label="当前数量"></el-table-column>
            </el-table>
    </el-row>
    <el-row :gutter="20">
        <el-col>
            <el-pagination @size-change="handleSizeChange" @current-change="handlePageChange"
                :current-page="currentPage" :page-size="pageSize" layout="total, sizes, prev, pager, next, jumper"
                :total="totalRows" />
        </el-col>
    </el-row>
</template>

<script>
import axios from 'axios'
export default {
    data() {
        return {
            isMaterialLogisticVis: false,
            isShoeLogisticVis: false,
            orderRIdSearch: '',
            statusFilter: '',
            shoeRIdSearch: '',
            materialNameSearch: null,
            materialModelSearch: null,
            materialSpecSearch: null,
            materialColorSearch: null,
            supplierNameSearch: null,
            statusSearch: null,
            logisticsShoeData: [],
            purchaseOrderData: [],
            logisticsMaterialData: [],
            totalRows: 0,
            currentPage: 1,
            pageSize: 10,
            logisticsRows: 0,
            currentLogisticsPage: 1,
            logisticsPageSize: 10,
            currentRow: {},
        }
    },
    mounted() {
        this.getPurchaseOrderData()
    },
    methods: {
        async getPurchaseOrderData() {
            const params = {
                "page": this.currentPage,
                "pageSize": this.pageSize,
                "orderRId": this.orderRIdSearch,
                "shoeRId": this.shoeRIdSearch,
                "materialName": this.materialNameSearch,
                "materialModel": this.materialModelSearch,
                "materialSpecification": this.materialSpecSearch,
                "materialColor": this.materialColorSearch,
                "supplierName": this.supplierNameSearch,
                "status": this.statusSearch,
            }
            const response = await axios.get(`${this.$apiBaseUrl}/logistics/getallpurchaseorderitems`, { params })
            this.purchaseOrderData = response.data.result
            this.totalRows = response.data.totalLength
        },
        handleSizeChange(val) {
            this.pageSize = val
            this.getPurchaseOrderData()
        },
        handlePageChange(val) {
            this.currentPage = val
            this.getPurchaseOrderData()
        },
        openLogisticsDialog(rowData) {
            this.currentRow = rowData
            this.isMaterialLogisticVis = true
        },
    }
}
</script>
<style>
.search-bar {
    width: 150px;
    margin-right: 20px;
}
</style>
