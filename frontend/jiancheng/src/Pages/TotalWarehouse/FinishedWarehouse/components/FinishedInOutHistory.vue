<template>
    <el-row :gutter="20">
        <el-col>
            <el-input v-model="orderNumberSearch" placeholder="订单号筛选" clearable @change="getTableData()" style="width: 200px; margin-right: 10px;"
                @clear="getTableData" />
            <el-input v-model="shoeNumberSearch" placeholder="鞋型号筛选" clearable @change="getTableData()" style="width: 200px; margin-right: 10px;"
                @clear="getTableData" />
            <el-input v-model="customerNameSearch" placeholder="客户号筛选" clearable @change="getTableData()" style="width: 200px; margin-right: 10px;"
                @clear="getTableData" />
            <el-input v-model="customerProductNameSearch" placeholder="客户鞋型筛选" clearable @change="getTableData()" style="width: 200px; margin-right: 10px;"
                @clear="getTableData" />
            <span>成品仓库存：{{ this.totalStock }}</span>
        </el-col>
    </el-row>
    <el-table :data="tableData" border stripe height="600">
        <el-table-column prop="orderRId" label="订单号"></el-table-column>
        <el-table-column prop="shoeRId" label="工厂型号"></el-table-column>
        <el-table-column prop="customerName" label="客户名称"></el-table-column>
        <el-table-column prop="customerProductName" label="客户鞋型"></el-table-column>
        <el-table-column prop="colorName" label="颜色"></el-table-column>
        <el-table-column prop="estimatedInboundAmount" label="计划入库数量"></el-table-column>
        <el-table-column prop="actualInboundAmount" label="实际入库数量"></el-table-column>
        <el-table-column prop="currentAmount" label="鞋型库存"></el-table-column>
        <el-table-column prop="storageStatus" label="状态"></el-table-column>

    </el-table>
    <el-row :gutter="20">
        <el-col>
            <el-pagination @size-change="handleSizeChange" @current-change="handlePageChange"
                :current-page="currentPage" :page-sizes="pageSizes" :page-size="pageSize"
                layout="total, sizes, prev, pager, next, jumper" :total="totalRows" />
        </el-col>
    </el-row>
    <el-dialog title="成品入库/出库记录" v-model="isRecordDialogVisible" width="80%">
        <el-descriptions title="入库记录"></el-descriptions>
        <el-table :data="recordData.inboundRecords" border stripe style="margin-bottom: 1ch;">
            <el-table-column prop="shoeInboundRId" label="入库编号" width="170"></el-table-column>
            <el-table-column prop="timestamp" label="操作时间"></el-table-column>
            <el-table-column prop="amount" label="入库数量"></el-table-column>
            <el-table-column prop="subsequentStock" label="入库后库存"></el-table-column>
            <el-table-column prop="remark" label="备注"></el-table-column>
        </el-table>

        <el-descriptions title="出库记录"></el-descriptions>
        <el-table :data="recordData.outboundRecords" border stripe>
            <el-table-column prop="shoeOutboundRId" label="出库编号" width="170"></el-table-column>
            <el-table-column prop="timestamp" label="操作时间"></el-table-column>
            <el-table-column prop="amount" label="出库数量"></el-table-column>
            <el-table-column prop="subsequentStock" label="出库后库存"></el-table-column>
            <el-table-column label="出库至">
                <template #default="scope">
                    <span v-if="scope.row.productionType == 0">{{ scope.row.picker }}</span>
                    <span v-else>{{ scope.row.destination }}</span>
                </template>
            </el-table-column>
            <el-table-column prop="remark" label="备注"></el-table-column>
        </el-table>
    </el-dialog>

    <el-dialog :title="`订单${currentRow.orderRId}/鞋型${currentRow.shoeRId}库存`" v-model="isOpenQuantityDialogVisible" width="60%">
        <el-form>
            <el-form-item>
                <el-table :data="filteredData" border stripe>
                    <el-table-column prop="shoeSizeName" label="鞋码"></el-table-column>
                    <el-table-column prop="currentQuantity" label="库存"></el-table-column>
                </el-table>
            </el-form-item>
        </el-form>
        <template #footer>
            <el-button type="primary" @click="isOpenQuantityDialogVisible = false">
                确认
            </el-button>
        </template>
    </el-dialog>
</template>
<script>
import axios from 'axios'
import { PAGESIZE, PAGESIZES } from '../../warehouseUtils';
export default {
    data() {
        return {
            isRecordDialogVisible: false,
            orderNumberSearch: null,
            shoeNumberSearch: null,
            customerNameSearch: null,
            customerProductNameSearch: null,
            pageSize: PAGESIZE,
            pageSizes: PAGESIZES,
            currentPage: 1,
            tableData: [],
            totalRows: 0,
            mapping: {
                0: "自产",
                1: "外包"
            },
            isOpenQuantityDialogVisible: false,
            shoeStockTable: [],
            currentRow: {},
            totalStock: 0,
        }
    },
    computed: {
        filteredData() {
            return this.shoeStockTable.filter((row) => {
                return (
                    row.predictQuantity > 0
                );
            });
        },
    },
    mounted() {
        this.getTableData()
    },
    methods: {
        async viewStock(row) {
            let params = { "orderId": row.orderId, "storageId": row.storageId, "storageType": 1 }
            let response = await axios.get(`${this.$apiBaseUrl}/warehouse/getshoesizecolumns`, { params })
            this.shoeStockTable = response.data
            this.currentRow = row
            this.isOpenQuantityDialogVisible = true
        },
        handleSizeChange(val) {
            this.pageSize = val
            this.getTableData()
        },
        handlePageChange(val) {
            this.currentPage = val
            this.getTableData()
        },
        async getTableData() {
            const params = {
                "page": this.currentPage,
                "pageSize": this.pageSize,
                "orderRId": this.orderNumberSearch,
                "shoeRId": this.shoeNumberSearch,
                "customerName": this.customerNameSearch,
                "customerProductName": this.customerProductNameSearch,
                "showAll": 1
            }
            const response = await axios.get(`${this.$apiBaseUrl}/warehouse/getfinishedstorages`, { params })
            this.tableData = response.data.result
            this.totalRows = response.data.total

            const response2 = await axios.get(`${this.$apiBaseUrl}/warehouse/gettotalstockoffinishedstorage`)
            this.totalStock = response2.data.totalStock
        },
        async viewRecords(row) {
            const params = { "storageId": row.storageId }
            const response = await axios.get(`${this.$apiBaseUrl}/warehouse/warehousemanager/getfinishedinoutboundrecords`, { params })
            this.recordData = response.data
            this.isRecordDialogVisible = true
        },
    }
}
</script>