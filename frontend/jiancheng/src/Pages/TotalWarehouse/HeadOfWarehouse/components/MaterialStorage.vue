<template>
    <el-row :gutter="20">
        <el-col :span="24" :offset="0">
            <el-button type="primary" @click="isMaterialDialogVisible = true">搜索条件设置</el-button>
            <el-button type="success" @click="confirmOrderShoesToOutbound">
                出库
            </el-button>
        </el-col>
        <MaterialSearchDialog :visible="isMaterialDialogVisible" :materialSupplierOptions="materialSupplierOptions"
            :materialTypeOptions="materialTypeOptions" :material-name-options="materialNameOptions"
            :searchForm="searchForm" @update-visible="updateDialogVisible" @confirm="handleSearch" />
    </el-row>
    <el-table :data="tableData" border stripe height="650px" @selection-change="handleSelectionChange">
        <el-table-column type="selection" width="55" />
        <el-table-column prop="orderRId" label="生产订单号"></el-table-column>
        <el-table-column prop="shoeRId" label="工厂鞋型号"></el-table-column>
        <el-table-column prop="materialType" label="材料类型"></el-table-column>
        <el-table-column prop="materialName" label="材料名称" width="100">
            <template #default="scope">
                <el-tooltip effect="dark" :content="scope.row.materialName" placement="bottom">
                    <span class="truncate-text">
                        {{ scope.row.materialName }}
                    </span>
                </el-tooltip>
            </template>
        </el-table-column>
        <el-table-column prop="materialModel" label="型号"></el-table-column>
        <el-table-column prop="materialSpecification" label="规格"></el-table-column>
        <el-table-column prop="colorName" label="颜色"></el-table-column>
        <el-table-column prop="actualInboundUnit" label="单位"></el-table-column>
        <el-table-column prop="estimatedInboundAmount" label="应入库数量"></el-table-column>
        <el-table-column prop="actualInboundAmount" label="实入库数量"></el-table-column>
        <el-table-column prop="currentAmount" label="库存"></el-table-column>
        <el-table-column prop="supplierName" label="供应商"></el-table-column>
        <el-table-column fixed="right" label="操作" width="150">
            <template #default="scope">
                <el-button-group>
                    <el-button v-if="scope.row.materialCategory == 1" type="primary" size="small"
                        @click="viewSizeMaterialStock(scope.row)">查看多鞋码库存</el-button>
                    <el-button type="primary" size="small" @click="viewRecords(scope.row)">入/出库记录</el-button>
                </el-button-group>
            </template>
        </el-table-column>
    </el-table>
    <el-row :gutter="20">
        <el-col :span="12" :offset="14">
            <el-pagination @size-change="handleSizeChange" @current-change="handlePageChange"
                :current-page="currentPage" :page-sizes="[20, 40, 60, 100]" :page-size="pageSize"
                layout="total, sizes, prev, pager, next, jumper" :total="totalRows" />
        </el-col>
    </el-row>

    <el-dialog title="材料入库/出库记录" v-model="isRecordDialogVisible" width="60%">
        <el-descriptions border size="default" title="材料信息">
            <el-descriptions-item label="材料名称">
                {{ currentRow.materialName }}
            </el-descriptions-item>
            <el-descriptions-item label="材料型号">
                {{ currentRow.materialModel }}
            </el-descriptions-item>
            <el-descriptions-item label="材料规格">
                {{ currentRow.materialSpecification }}
            </el-descriptions-item>
            <el-descriptions-item label="颜色">
                {{ currentRow.colorName }}
            </el-descriptions-item>
            <el-descriptions-item label="材料供应商">
                {{ currentRow.supplierName }}
            </el-descriptions-item>
            <el-descriptions-item label="材料单位">
                {{ currentRow.materialUnit }}
            </el-descriptions-item>
            <el-descriptions-item label="材料库存">
                {{ currentRow.currentAmount }}
            </el-descriptions-item>

        </el-descriptions>
        <el-tabs>
            <el-tab-pane label="入库记录">
                <el-table v-if="currentRow.materialCategory == 0" :data="materialInboundRecordData" border stripe>
                    <el-table-column prop="inboundRId" label="入库单号"></el-table-column>
                    <el-table-column prop="inboundType" label="用途"></el-table-column>
                    <el-table-column prop="timestamp" label="时间"></el-table-column>
                    <el-table-column prop="inboundAmount" label="数量"></el-table-column>
                    <el-table-column prop="remark" label="备注"></el-table-column>
                </el-table>
                <el-table v-if="currentRow.materialCategory == 1" :data="sizeMaterialInboundRecordData" border stripe>
                    <el-table-column prop="inboundRId" label="入库单号"></el-table-column>
                    <el-table-column prop="inboundType" label="用途"></el-table-column>
                    <el-table-column prop="timestamp" label="时间"></el-table-column>
                    <el-table-column v-for="column in shoeSizeColumns" :key="column.prop" :prop="column.prop"
                        :label="column.label"></el-table-column>
                    <el-table-column prop="remark" label="备注"></el-table-column>
                </el-table>
            </el-tab-pane>
            <el-tab-pane label="出库记录">
                <el-table v-if="currentRow.materialCategory == 0" :data="materialOutboundRecordData" border stripe>
                    <el-table-column prop="outboundRId" label="出库单号"></el-table-column>
                    <el-table-column prop="outboundType" label="用途"></el-table-column>
                    <el-table-column prop="timestamp" label="时间"></el-table-column>
                    <el-table-column prop="outboundAmount" label="数量"></el-table-column>
                    <el-table-column prop="outboundDestination" label="出库至"></el-table-column>
                    <el-table-column prop="picker" label="领料人"></el-table-column>
                    <el-table-column prop="outboundAddress" label="出库地址"></el-table-column>
                    <el-table-column prop="remark" label="备注"></el-table-column>
                </el-table>
                <el-table v-if="currentRow.materialCategory == 1" :data="sizeMaterialOutboundRecordData" border stripe>
                    <el-table-column prop="outboundRId" label="出库单号"></el-table-column>
                    <el-table-column prop="outboundType" label="用途"></el-table-column>
                    <el-table-column prop="timestamp" label="时间"></el-table-column>
                    <el-table-column v-for="column in shoeSizeColumns" :key="column.prop" :prop="column.prop"
                        :label="column.label"></el-table-column>
                    <el-table-column prop="outboundDestination" label="出库至"></el-table-column>
                    <el-table-column prop="picker" label="领料人"></el-table-column>
                    <el-table-column prop="outboundAddress" label="出库地址"></el-table-column>
                    <el-table-column prop="remark" label="备注"></el-table-column>
                </el-table>
            </el-tab-pane>
        </el-tabs>
    </el-dialog>
    <el-dialog title="尺码材料库存" v-model="isViewSizeMaterialStockOpen" width="60%">
        <el-table :data="filteredSizeMaterialStock" border stripe>
            <el-table-column prop="shoeSizeName" label="鞋码"></el-table-column>
            <el-table-column prop="currentQuantity" label="材料数量"></el-table-column>
        </el-table>
    </el-dialog>

    <OutboundDialog :visible="isConfirmOrderShoesDialogOpen" :outboundForm="outboundForm"
        @update-visible="updateConfirmOrderShoesDialogVis" @get-material-table-data="getMaterialTableData"
        :selectedRows="selectedRowsCopy" />
</template>
<script>
import axios from 'axios'
import MaterialSearchDialog from './MaterialSearchDialog.vue';
import OutboundDialog from './OutboundDialog.vue';
import { ElMessage } from 'element-plus';
export default {
    components: {
        MaterialSearchDialog,
        OutboundDialog
    },
    computed: {
        filteredSizeMaterialStock() {
            return this.sizeMaterialStockData.filter(item => item.predictQuantity > 0)
        }
    },
    data() {
        return {
            isRecordDialogVisible: false,
            isSizeRecordDialogVisible: false,
            isMaterialDialogVisible: false,
            searchForm: {
                orderNumberSearch: '',
                shoeNumberSearch: '',
                materialTypeSearch: '',
                materialNameSearch: '',
                materialSpecificationSearch: '',
                materialSupplierSearch: '',
                totalPurchaseOrderRIdSearch: '',
            },
            materialTypeOptions: [],
            materialSupplierOptions: [],
            pageSize: 20,
            currentPage: 1,
            recordData: [],
            sizeRecordData: [],
            tableData: [],
            columns: [],
            totalRows: 0,
            currentRow: {},
            isViewSizeMaterialStockOpen: false,
            sizeMaterialStockData: [],
            materialInboundRecordData: [],
            sizeMaterialInboundRecordData: [],
            materialOutboundRecordData: [],
            sizeMaterialOutboundRecordData: [],
            shoeSizeColumns: [],
            selectedRows: [],
            selectedRowsCopy: [],
            outboundForm: {
                // groupedSelectedRows contains formItemTemplate,
                // selectedOrderShoeId, selectedOrderId, selectedOrderRId, and selectedShoeId
                // because some materials don't have orderId or orderShoeId
                groupedSelectedRows: [],
                assetRows: [],
                outsourceInfo: [],
            },
            formItemTemplate: {
                timestamp: null,
                outboundType: null,
                outboundQuantity: 0,
                section: null,
                receiver: null,
                outboundAddress: null,
                deadlineDate: null,
                outsourceInfoId: null,
                outsourceInfo: [],
                selectedOutsourceId: '',
                selectedOutsourceFactory: '',
                materials: [],
                selectedCompositeSupplier: null,
            },
            isConfirmOrderShoesDialogOpen: false,
            materialNameOptions: [],
        }
    },
    mounted() {
        this.getAllMaterialTypes()
        this.getAllSuppliers()
        this.getMaterialNameOptions()
        this.getMaterialTableData()
    },
    methods: {
        async getMaterialNameOptions() {
            const params = { department: 0 }
            const response = await axios.get(`${this.$apiBaseUrl}/logistics/getallmaterialname`, { params })
            this.materialNameOptions = response.data
        },
        updateConfirmOrderShoesDialogVis(newVal) {
            this.isConfirmOrderShoesDialogOpen = newVal
        },
        openSizeMaterialQuantityDialog(row) {
            this.currentSizeMaterialQuantityRow = row
            this.isOpenSizeMaterialQuantityDialogVisible = true
        },
        handleSelectionChange(selection) {
            this.selectedRows = selection;
        },
        async confirmOrderShoesToOutbound() {
            if (this.selectedRows.length == 0) {
                ElMessage.error("未选择材料")
                return
            }
            this.selectedRowsCopy = JSON.parse(JSON.stringify(this.selectedRows))
            // collect all orderShoeId that are null
            this.selectedRowsCopy.forEach(row => {
                row["selectedOrderShoeId"] = row.orderShoeId
                row["selectedOrderId"] = row.orderId
                row["selectedShoeRId"] = row.shoeRId
                row["selectedOrderRId"] = row.orderRId
            })
            this.isConfirmOrderShoesDialogOpen = true
        },
        async viewSizeMaterialStock(row) {
            let params = { "sizeMaterialStorageId": row.materialStorageId, orderId: row.orderId, purchaseDivideOrderId: row.purchaseDivideOrderId }
            let response = await axios.get(`${this.$apiBaseUrl}/warehouse/warehousemanager/getsizematerialbyid`, { params })
            this.sizeMaterialStockData = response.data
            this.isViewSizeMaterialStockOpen = true
        },
        updateDialogVisible(newVal) {
            this.isMaterialDialogVisible = newVal
        },
        handleSearch(values) {
            this.searchForm = { ...values }
            this.getMaterialTableData()
        },
        async getAllMaterialTypes() {
            const response = await axios.get(`${this.$apiBaseUrl}/warehouse/warehousemanager/getallmaterialtypes`)
            this.materialTypeOptions = response.data
        },
        async getAllSuppliers() {
            const response = await axios.get(`${this.$apiBaseUrl}/warehouse/warehousemanager/getallsuppliernames`)
            this.materialSupplierOptions = response.data
        },
        async getMaterialTableData(sortColumn, sortOrder) {
            const params = {
                "page": this.currentPage,
                "pageSize": this.pageSize,
                "materialType": this.searchForm.materialTypeSearch,
                "materialName": this.searchForm.materialNameSearch,
                "materialSpec": this.searchForm.materialSpecificationSearch,
                "supplier": this.searchForm.materialSupplierSearch,
                "orderRId": this.searchForm.orderNumberSearch,
                "shoeRId": this.searchForm.shoeNumberSearch,
                "purchaseOrderRId": this.searchForm.totalPurchaseOrderRIdSearch,
                "sortColumn": sortColumn,
                "sortOrder": sortOrder
            }
            const response = await axios.get(`${this.$apiBaseUrl}/warehouse/warehousemanager/getallmaterialinfo`, { params })
            this.tableData = response.data.result
            this.totalRows = response.data.total
        },
        formatDecimal(row, column, cellValue, index) {
            return Number(cellValue).toFixed(2)
        },
        handleSizeChange(val) {
            this.pageSize = val
            this.getMaterialTableData()
        },
        handlePageChange(val) {
            this.currentPage = val
            this.getMaterialTableData()
        },
        async viewRecords(row) {
            this.currentRow = row
            let tempShoeSizeColumns = []
            if (row.materialCategory == 1) {
                let params = { "storageId": row.materialStorageId }
                let response = await axios.get(`${this.$apiBaseUrl}/warehouse/getinboundrecordsforsizematerial`, { params })
                this.sizeMaterialInboundRecordData = response.data

                let sizeResponse = await axios.get(`${this.$apiBaseUrl}/warehouse/getoutboundrecordsforsizematerial`, { params })
                this.sizeMaterialOutboundRecordData = sizeResponse.data

                let params1 = { "sizeMaterialStorageId": row.materialStorageId, orderId: row.orderId, purchaseDivideOrderId: row.purchaseDivideOrderId }
                let response1 = await axios.get(`${this.$apiBaseUrl}/warehouse/warehousemanager/getsizematerialbyid`, { params: params1 })
                response1.data.forEach((element, index) => {
                    let obj = {
                        "prop": `amount${index}`,
                        "label": element.shoeSizeName
                    }
                    tempShoeSizeColumns.push(obj)
                });
                this.shoeSizeColumns = [...tempShoeSizeColumns]
                this.isRecordDialogVisible = true
            } else {
                let params = { "storageId": row.materialStorageId }
                let response = await axios.get(`${this.$apiBaseUrl}/warehouse/getinboundrecordsformaterial`, { params })
                this.materialInboundRecordData = response.data

                let response1 = await axios.get(`${this.$apiBaseUrl}/warehouse/getoutboundrecordsformaterial`, { params })
                this.materialOutboundRecordData = response1.data
                this.isRecordDialogVisible = true
            }
        },
    }
}
</script>