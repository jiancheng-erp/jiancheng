<template>
    <div>
        <el-row :gutter="20">
            <el-col :span="19" :offset="0">
                <FinishedSearchBar :searchFilters="searchFilters" @confirm="confirmTableData" />
                <el-select v-model="category" clearable placeholder="鞋类型" style="width: 140px; margin-left: 8px" @change="getTableData">
                    <el-option label="男鞋" value="男鞋" />
                    <el-option label="女鞋" value="女鞋" />
                    <el-option label="童鞋" value="童鞋" />
                    <el-option label="其它" value="其它" />
                </el-select>
                <!-- 状态切换 -->
                <el-radio-group v-model="storageStatusNum" @change="getTableData" class="mr-2">
                    <el-radio-button v-for="option in storageStatusOptions" :key="option.value" :label="option.value" v-model="storageStatusNum">
                        {{ option.label }}
                    </el-radio-button>
                </el-radio-group>
            </el-col>
            <el-col :span="6" :offset="0">
                <el-form-item label="仅显示有库存订单" style="display: inline-block; margin-left: 12px">
                    <el-switch v-model="showOnlyInStock" @change="getTableData" />
                </el-form-item>
            </el-col>
        </el-row>

        <el-row :gutter="20" style="margin-top: 10px">
            <el-col>
                <span>成品仓库存：{{ totalStock }}</span>
            </el-col>
        </el-row>

        <el-table :data="tableData" border stripe height="500">
            <el-table-column prop="orderRId" label="订单号" width="120" />
            <el-table-column prop="shoeRId" label="工厂型号" width="180" />
            <el-table-column prop="batchType" label="类型" width="100" />
            <el-table-column prop="customerName" label="客户名称" />
            <el-table-column prop="orderCId" label="客户订单号" width="150" />
            <el-table-column prop="customerProductName" label="客户鞋型" width="150" />
            <el-table-column prop="customerBrand" label="客户商标" width="150" />
            <el-table-column prop="designer" label="设计师" />
            <el-table-column prop="adjuster" label="调版师" />
            <el-table-column prop="colorName" label="颜色" width="120" />
            <el-table-column prop="estimatedInboundAmount" label="计划入库数量" />
            <el-table-column prop="actualInboundAmount" label="实际入库数量" />
            <el-table-column prop="currentAmount" label="鞋型库存" />
            <el-table-column prop="storageStatusLabel" label="状态" width="100" />
            <el-table-column prop="finishedTime" label="完成时间" width="110" />
        </el-table>

        <el-row :gutter="20">
            <el-col>
                <el-pagination
                    @size-change="handleSizeChange"
                    @current-change="handlePageChange"
                    :current-page="currentPage"
                    :page-sizes="pageSizes"
                    :page-size="pageSize"
                    layout="total, sizes, prev, pager, next, jumper"
                    :total="totalRows"
                />
            </el-col>
        </el-row>

        <el-dialog title="成品入库/出库记录" v-model="isRecordDialogVisible" width="80%">
            <el-descriptions title="入库记录"></el-descriptions>
            <el-table :data="recordData.inboundRecords" border stripe style="margin-bottom: 1ch">
                <el-table-column prop="shoeInboundRId" label="入库编号" width="170" />
                <el-table-column prop="timestamp" label="操作时间" />
                <el-table-column prop="amount" label="入库数量" />
                <el-table-column prop="subsequentStock" label="入库后库存" />
                <el-table-column prop="remark" label="备注" />
            </el-table>

            <el-descriptions title="出库记录"></el-descriptions>
            <el-table :data="recordData.outboundRecords" border stripe>
                <el-table-column prop="shoeOutboundRId" label="出库编号" width="170" />
                <el-table-column prop="timestamp" label="操作时间" />
                <el-table-column prop="amount" label="出库数量" />
                <el-table-column prop="subsequentStock" label="出库后库存" />
                <el-table-column label="出库至">
                    <template #default="scope">
                        <span v-if="scope.row.productionType == 0">{{ scope.row.picker }}</span>
                        <span v-else>{{ scope.row.destination }}</span>
                    </template>
                </el-table-column>
                <el-table-column prop="remark" label="备注" />
            </el-table>
        </el-dialog>

        <el-dialog :title="`订单${currentRow.orderRId}/鞋型${currentRow.shoeRId}库存`" v-model="isOpenQuantityDialogVisible" width="60%">
            <el-form>
                <el-form-item>
                    <el-table :data="filteredData" border stripe>
                        <el-table-column prop="shoeSizeName" label="鞋码" />
                        <el-table-column prop="currentQuantity" label="库存" />
                    </el-table>
                </el-form-item>
            </el-form>
            <template #footer>
                <el-button type="primary" @click="isOpenQuantityDialogVisible = false">确认</el-button>
            </template>
        </el-dialog>
    </div>
</template>

<script>
import axios from 'axios'
import { PAGESIZE, PAGESIZES } from '../../warehouseUtils'
import FinishedSearchBar from './FinishedSearchBar.vue'

export default {
    components: { FinishedSearchBar },
    data() {
        return {
            isRecordDialogVisible: false,
            searchFilters: {
                orderRIdSearch: null,
                shoeRIdSearch: null,
                customerNameSearch: null,
                customerProductNameSearch: null,
                orderCIdSearch: null,
                customerBrandSearch: null
            },
            // 新增：两个本页筛选
            category: '', // 男鞋 / 女鞋 / 童鞋 / 其它（空=全部）
            showOnlyInStock: false, // 仅显示有库存

            pageSize: PAGESIZE,
            pageSizes: PAGESIZES,
            currentPage: 1,
            tableData: [],
            totalRows: 0,
            mapping: { 0: '自产', 1: '外包' },
            isOpenQuantityDialogVisible: false,
            shoeStockTable: [],
            currentRow: {},
            totalStock: 0,
            storageStatusOptions: [],
            storageStatusNum: null,
            FINISHED_STORAGE_STATUS_ENUM: {},
            recordData: { inboundRecords: [], outboundRecords: [] }
        }
    },
    computed: {
        filteredData() {
            return (this.shoeStockTable || []).filter((row) => Number(row.predictQuantity || 0) > 0)
        }
    },
    async mounted() {
        await this.getStorageStatusOptions()
        this.storageStatusNum = this.FINISHED_STORAGE_STATUS_ENUM.ALL
        this.getTableData()
    },
    methods: {
        async getStorageStatusOptions() {
            const response = await axios.get(`${this.$apiBaseUrl}/product/getstoragestatusoptions`)
            this.storageStatusOptions = response.data.storageStatusOptions
            this.FINISHED_STORAGE_STATUS_ENUM = response.data.storageStatusEnum
        },
        confirmTableData(filters) {
            this.searchFilters = { ...filters }
            this.currentPage = 1
            this.getTableData()
        },
        async viewStock(row) {
            const params = { orderId: row.orderId, storageId: row.storageId, storageType: 1 }
            const response = await axios.get(`${this.$apiBaseUrl}/warehouse/getshoesizecolumns`, { params })
            this.shoeStockTable = response.data
            this.currentRow = row
            this.isOpenQuantityDialogVisible = true
        },
        handleSizeChange(val) {
            this.pageSize = val
            this.currentPage = 1
            this.getTableData()
        },
        handlePageChange(val) {
            this.currentPage = val
            this.getTableData()
        },
        async getTableData() {
            const params = {
                page: this.currentPage,
                pageSize: this.pageSize,
                orderRId: this.searchFilters.orderRIdSearch,
                shoeRId: this.searchFilters.shoeRIdSearch,
                customerName: this.searchFilters.customerNameSearch,
                customerProductName: this.searchFilters.customerProductNameSearch,
                orderCId: this.searchFilters.orderCIdSearch,
                customerBrand: this.searchFilters.customerBrandSearch,
                storageStatusNum: this.storageStatusNum,
                // 新增：两个筛选参数透传后端
                ...(this.category ? { category: this.category } : {}),
                showAll: this.showOnlyInStock ? 1 : 0
            }
            const response = await axios.get(`${this.$apiBaseUrl}/warehouse/getfinishedstorages`, { params })
            this.tableData = response?.data?.result || []
            this.totalRows = Number(response?.data?.total || 0)

            const response2 = await axios.get(`${this.$apiBaseUrl}/warehouse/gettotalstockoffinishedstorage`)
            this.totalStock = Number(response2?.data?.totalStock || 0)
        },
        async viewRecords(row) {
            const params = { storageId: row.storageId }
            const response = await axios.get(`${this.$apiBaseUrl}/warehouse/warehousemanager/getfinishedinoutboundrecords`, { params })
            this.recordData = response.data || { inboundRecords: [], outboundRecords: [] }
            this.isRecordDialogVisible = true
        }
    }
}
</script>

<style scoped>
.mb-2 {
    margin-bottom: 12px;
}
.mt-2 {
    margin-top: 12px;
}
.mr-2 {
    margin-right: 8px;
}
</style>
