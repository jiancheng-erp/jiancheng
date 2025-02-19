<template>
    <el-row :gutter="20">
        <el-col :span="24" :offset="0" style="font-size: xx-large; text-align: center">批量采购订单生成及下发</el-col>
    </el-row>
    <el-row :gutter="20">
        <el-col :span="4" :offset="0" style="white-space: nowrap">
            采购订单号搜索：
            <el-input v-model="purchaseOrderSearch" placeholder="" size="default" :suffix-icon="Search" clearable
                @change="tableFilter"></el-input>
        </el-col>
        <el-col :span="4" :offset="2" style="white-space: nowrap">
            订单号搜索：
            <el-input v-model="OrderSearch" placeholder="" size="default" :suffix-icon="Search" clearable
                @change="tableFilter"></el-input>
        </el-col>
        <el-col :span="4" :offset="2" style="white-space: nowrap">
            厂家搜索：
            <el-input v-model="supplierSearch" placeholder="" size="default" :suffix-icon="Search" clearable
                @change="tableFilter"></el-input>
        </el-col>
    </el-row>
    <el-row :gutter="20">
        <el-col :span="24" :offset="0">
            <el-tabs v-model="currentTab" type="card" tab-position="top">
                <el-tab-pane label="总采购订单" name="1" height="500">
                    <el-radio-group v-model="statusFilter" @change="changeFinishedOrderFilterStatus">
                        <el-radio-button label="2" value="2">已下发总采购订单</el-radio-button>
                        <el-radio-button label="1" value="1">未下发总采购订单</el-radio-button>
                    </el-radio-group>

                    <el-table :data="paginatedFinishedPurchaseOrderData" border stripe height="450">
                        <el-table-column type="expand">
                            <template #default="scope">
                                <el-text>采购子订单</el-text>
                                <el-table :data="scope.row.purchaseDivideOrders" border stripe height="400">
                                    <el-table-column prop="purchaseDivideOrderId" label="采购子订单编号"></el-table-column>
                                    <el-table-column prop="orderRid" label="订单号"></el-table-column>
                                    <el-table-column prop="shoeRid" label="工厂型号"></el-table-column>
                                    <el-table-column prop="customerName" label="客户名"></el-table-column>
                                    <el-table-column label="操作">
                                        <template #default="scope">
                                            <el-button type="primary"
                                                @click="openPreviewDialog(scope.row)">查看详情</el-button>
                                        </template>
                                    </el-table-column>
                                </el-table>
                            </template>
                        </el-table-column>
                        <el-table-column prop="totalPurchaseOrderRid" label="总采购订单编号"></el-table-column>
                        <el-table-column prop="supplierName" label="供应厂商"></el-table-column>
                        <el-table-column label="操作">
                            <template #default="scope">
                                <el-button v-if="scope.row.totalPurchaseOrderStatus === '1'" type="primary"
                                    @click="openTotalPreviewDialog(scope.row, true)">查看详情并下发</el-button>
                                <el-button v-else type="success"
                                    @click="openTotalPreviewDialog(scope.row), false">查看详情</el-button>
                            </template>
                        </el-table-column>
                    </el-table>
                    <el-pagination style="margin-top: 10px" background layout="prev, pager, next"
                        :total="finishedPurchaseOrderData.length" :page-size="pageSize"
                        :current-page="finishedCurrentPage"
                        @current-change="(page) => handlePageChange('finished', page)"></el-pagination>
                </el-tab-pane>
                <el-tab-pane label="未下发分采购订单" name="0">
                    <el-row :gutter="20">
                        <el-col :span="12" :offset="0">
                            <el-button type="primary" @click="openIssueTotalPurchaseOrderDialog">下发总采购订单</el-button>
                        </el-col>
                        <el-col :span="12" :offset="0"></el-col>
                    </el-row>

                    <el-row :gutter="20">
                        <el-col :span="24" :offset="0">
                            <el-table :data="paginatedUnfinishedPurchaseOrderData" border stripe height="450">
                                <el-table-column prop="purchaseDivideOrderId" label="采购子订单编号"></el-table-column>
                                <el-table-column prop="supplierName" label="供应厂商"></el-table-column>
                                <el-table-column prop="orderRid" label="订单号"></el-table-column>
                                <el-table-column prop="shoeRid" label="工厂型号"></el-table-column>
                                <el-table-column prop="customerName" label="客户名"></el-table-column>
                                <el-table-column label="操作">
                                    <template #default="scope">
                                        <el-button type="primary" @click="openPreviewDialog(scope.row)">查看详情</el-button>
                                        <el-button type="success"
                                            @click="handleIssueTotalPurchaseOrder(scope.row)">下发</el-button>
                                    </template>
                                </el-table-column>
                            </el-table>
                            <el-pagination style="margin-top: 10px" background layout="prev, pager, next"
                                :total="unfinishedPurchaseOrderData.length" :page-size="pageSize"
                                :current-page="unfinishedCurrentPage"
                                @current-change="(page) => handlePageChange('unfinished', page)"></el-pagination>
                        </el-col>
                    </el-row>
                </el-tab-pane>
            </el-tabs>
        </el-col>
    </el-row>
    <el-dialog title="下发总采购订单" v-model="isIssueTotalPurchaseOrderDialogVisible" width="60%">
        <el-row :gutter="20">
            <el-col :span="3" :offset="0">请输入厂家名：</el-col>
            <el-col :span="4" :offset="0">
                <el-input v-model="SupplierInput" placeholder="" size="default" clearable
                    @change="handleSupplierChange"></el-input>
            </el-col>
        </el-row>
        <el-row :gutter="20">
            <el-col :span="24" :offset="0">
                <el-table :data="issuePageUnfinishedPurchaseOrderData" border stripe height="600"
                    @selection-change="handleIssueSelectionChange" ref="issueTable">
                    <el-table-column type="selection"></el-table-column>
                    <el-table-column prop="purchaseDivideOrderId" label="采购子订单编号"></el-table-column>
                    <el-table-column prop="supplierName" label="供应厂商"></el-table-column>
                    <el-table-column prop="orderRid" label="订单号"></el-table-column>
                    <el-table-column prop="shoeRid" label="工厂型号"></el-table-column>
                    <el-table-column prop="customerName" label="客户名"></el-table-column>
                    <el-table-column label="操作">
                        <template #default="scope">
                            <el-button type="primary" @click="openPreviewDialog(scope.row)">查看详情</el-button>
                        </template>
                    </el-table-column>
                </el-table>
            </el-col>
        </el-row>

        <template #footer>
            <span>
                <el-button @click="isIssueTotalPurchaseOrderDialogVisible = false">取消</el-button>
                <el-button type="primary" @click="createTotalPurchaseOrder">下发总采购订单</el-button>
            </span>
        </template>
    </el-dialog>
    <el-dialog title="采购订单详情" v-model="isPurchaseItemDetailDialogVisible" width="80%">
        <div style="height: 500px; overflow-y: scroll; overflow-x: hidden">
            <el-row v-for="purchaseDivideOrder in purchaseTestData" :key="purchaseDivideOrder" :gutter="20"
                style="margin-bottom: 20px">
                <el-col :span="23">
                    <h3>分采购订单编号 {{ purchaseDivideOrder.purchaseDivideOrderId }}</h3>
                    <h3>工厂名称: {{ purchaseDivideOrder.supplierName }}</h3>
                    <el-row :gutter="20">
                        <el-col :span="12" :offset="0"><span>订单备注：
                                {{ purchaseDivideOrder.remark }}
                            </span></el-col>
                        <el-col :span="12" :offset="0">
                            <span>环境要求：
                                {{ purchaseDivideOrder.evironmentalRequest }}
                            </span>
                        </el-col>
                    </el-row>
                    <el-row :gutter="20">
                        <el-col :span="12" :offset="0"><span>发货地址: {{ purchaseDivideOrder.shipmentAddress }}
                            </span></el-col>
                        <el-col :span="12" :offset="0">
                            <span>交货周期: {{ purchaseDivideOrder.shipmentDeadline }} </span>
                        </el-col>
                    </el-row>
                    <div v-if="factoryFieldJudge(purchaseDivideOrder.purchaseDivideOrderType)">
                        <el-table :data="purchaseDivideOrder.assetsItems" border style="width: 100%">
                            <el-table-column type="index" label="编号" />
                            <el-table-column prop="materialType" label="材料类型"></el-table-column>
                            <el-table-column prop="materialName" label="材料名称" />
                            <el-table-column prop="materialModel" label="材料型号" />
                            <el-table-column prop="materialSpecification" label="材料规格"></el-table-column>
                            <el-table-column prop="unit" label="单位" />

                            <el-table-column prop="purchaseAmount" label="采购数量" />
                            <el-table-column :label="`分码数量 (${currentShoeSizeType})`">
                                <el-table-column v-for="column in filteredColumns(
                                    purchaseDivideOrder.assetsItems
                                )" :key="column.prop" :prop="column.prop" :label="column.label"></el-table-column>
                            </el-table-column>
                        </el-table>
                    </div>
                    <div v-else>
                        <el-table :data="purchaseDivideOrder.assetsItems" border style="width: 100%">
                            <el-table-column type="index" label="编号" />
                            <el-table-column prop="materialType" label="材料类型"></el-table-column>
                            <el-table-column prop="materialName" label="材料名称" />
                            <el-table-column prop="materialModel" label="材料型号" />
                            <el-table-column prop="materialSpecification" label="材料规格"></el-table-column>
                            <el-table-column prop="color" label="颜色" />
                            <el-table-column prop="unit" label="单位" />
                            <el-table-column prop="purchaseAmount" label="采购数量" />
                            <el-table-column prop="remark" label="开发部备注" />
                        </el-table>
                    </div>
                </el-col>
            </el-row>
        </div>
        <template #footer>
            <span>
                <el-button @click="isPurchaseItemDetailDialogVisible = false">Cancel</el-button>
                <el-button type="primary" @click="isPurchaseItemDetailDialogVisible = false">OK</el-button>
            </span>
        </template>
    </el-dialog>
    <el-dialog title="采购订单创建页面" v-model="purchaseOrderCreateVis" width="80%" :close-on-click-modal="false">
        <span v-if="activeTab === ''"> 无需购买材料，推进流程即可。 </span>
        <el-tabs v-if="activeTab !== ''" v-model="activeTab" type="card" tab-position="top">
            <el-tab-pane v-for="item in tabPlaneData" :key="item.totalPurchaseOrderId"
                :label="item.totalPurchaseOrderRid + '    ' + item.supplierName" :name="item.totalPurchaseOrderId"
                style="min-height: 500px">
                <el-row :gutter="20">
                    <el-col :span="12" :offset="0"><span>订单备注：
                            <el-input :disabled="!modifiedMode" v-model="item.remark" placeholder="" type="textarea"
                                resize="none" clearable></el-input> </span></el-col>
                    <el-col :span="12" :offset="0">
                        <span>环境要求：
                            <el-input :disabled="!modifiedMode" v-model="item.environmentalRequest" placeholder=""
                                type="textarea" resize="none" clearable></el-input>
                        </span>
                    </el-col>
                </el-row>
                <el-row :gutter="20">
                    <el-col :span="12" :offset="0">
                        <span>发货地址：
                            <el-input :disabled="!modifiedMode" v-model="item.shipmentAddress" placeholder=""
                                type="textarea" resize="none" clearable></el-input>
                        </span>
                    </el-col>
                    <el-col :span="12" :offset="0">
                        <span>交货周期：
                            <el-input :disabled="!modifiedMode" v-model="item.shipmentDeadline" placeholder=""
                                type="textarea" resize="none" clearable></el-input>
                        </span>
                    </el-col>
                </el-row>
                <el-row :gutter="20" style="margin-top: 20px">
                    <el-col :span="24" :offset="0">
                        <div v-if="factoryFieldJudge(item.totalPurchaseOrderType)">
                            <el-table :data="item.assetsItems" border style="width: 100%" height="500">
                                <el-table-column type="index" label="编号" />
                                <el-table-column prop="materialType" label="材料类型"></el-table-column>
                                <el-table-column prop="materialName" label="材料名称" />
                                <el-table-column prop="materialModel" label="材料型号" />
                                <el-table-column prop="materialSpecification" label="材料规格"></el-table-column>
                                <el-table-column prop="unit" label="单位" />

                                <el-table-column prop="amount" label="采购数量" />
                                <el-table-column :label="`分码数量(${currentShoeSizeType})`">
                                    <el-table-column v-for="column in filteredColumns(item.assetsItems)"
                                        :key="column.prop" :prop="column.prop" :label="column.label"></el-table-column>
                                </el-table-column>
                            </el-table>
                        </div>
                        <div v-else>
                            <el-table :data="item.assetsItems" border stripe height="500" width="100%">
                                <el-table-column type="index"></el-table-column>
                                <el-table-column prop="materialType" label="材料类型"></el-table-column>
                                <el-table-column prop="materialName" label="材料名称" />
                                <el-table-column prop="materialModel" label="材料型号" />
                                <el-table-column prop="materialSpecification" label="材料规格"></el-table-column>
                                <el-table-column prop="color" label="颜色" />
                                <el-table-column prop="unit" label="单位" />
                                <el-table-column prop="approvalAmount" label="核定用量"></el-table-column>
                                <el-table-column prop="purchaseAmount" label="数量" />
                                <el-table-column prop="adjustPurchaseAmount" label="采购订单调整数量" width="150">
                                    <template #default="scope">
                                        <el-input-number :min="0" v-model="scope.row.adjustPurchaseAmount"
                                            :step="0.0001" size="small" :disabled="!modifiedMode">
                                        </el-input-number>
                                    </template>
                                </el-table-column>
                                <el-table-column prop="isInboundSperate" label="入库单位是否不同">
                                    <template #default="scope">
                                        <el-switch v-model="scope.row.isInboundSperate" :active-value="true"
                                            :inactive-value="false" :disabled="!modifiedMode">
                                        </el-switch>
                                    </template>
                                </el-table-column>
                                <el-table-column prop="materialInboundName" label="入库材料名称">
                                    <template #default="scope">
                                        <el-select v-model="scope.row.materialInboundName" filterable
                                            @change="handleMaterialNameSelect(scope.row, $event)"
                                            :disabled="!modifiedMode || !scope.row.isInboundSperate">
                                            <el-option v-for="item in filterByMaterialType(scope.row.materialTypeId)"
                                                :key="item.value" :value="item.value" :label="item.label">
                                            </el-option>
                                        </el-select>
                                    </template>
                                </el-table-column>
                                <el-table-column prop="materialInboundUnit" label="入库单位"></el-table-column>
                                <el-table-column prop="remark" label="开发部备注" />
                            </el-table>
                        </div>
                    </el-col>
                </el-row>
            </el-tab-pane>
        </el-tabs>

        <template #footer>
            <span>
                <el-button @click="purchaseOrderCreateVis = false">取消</el-button>
                <el-button type="primary" v-if="modifiedMode" @click="saveTotalPurchaseOrder">保存</el-button>
                <el-button type="success" v-if="modifiedMode" @click="submitTotalPurchaseOrder">提交</el-button>
            </span>
        </template>
    </el-dialog>
</template>

<script>
import { Search } from '@element-plus/icons-vue'
import axios from 'axios'
import { getShoeSizesName } from '@/Pages/utils/getShoeSizesName'

export default {
    data() {
        return {
            isIssueTotalPurchaseOrderDialogVisible: false,
            unfinishedPurchaseOrderData: [],
            finishedPurchaseOrderData: [],
            issuePageUnfinishedPurchaseOrderData: [],
            currentTab: '1',
            purchaseOrderSearch: '',
            OrderSearch: '',
            supplierSearch: '',
            Search,
            SupplierInput: '',
            isPurchaseItemDetailDialogVisible: false,
            purchaseTestData: [],
            previewBomId: '',
            shoeSizeColumns: [],
            getShoeSizesName,
            currentShoeSizeType: '',
            finishedCurrentPage: 1, // Separate current page for finished orders
            unfinishedCurrentPage: 1, // Separate current page for unfinished orders
            pageSize: 8,
            issueSelectedRows: [],
            purchaseOrderCreateVis: false,
            activeTab: '',
            tabPlaneData: [],
            statusFilter: '1',
            modifiedMode: false,
            materialNameOptions: []
        }
    },
    computed: {
        paginatedFinishedPurchaseOrderData() {
            // Filter based on totalPurchaseOrderStatus
            const filteredData = this.finishedPurchaseOrderData.filter(
                (order) => order.totalPurchaseOrderStatus === this.statusFilter
            )
            // Paginate the filtered data
            const start = (this.finishedCurrentPage - 1) * this.pageSize
            const end = start + this.pageSize
            return filteredData.slice(start, end)
        },
        // Paginated data for unfinished orders
        paginatedUnfinishedPurchaseOrderData() {
            const start = (this.unfinishedCurrentPage - 1) * this.pageSize
            const end = start + this.pageSize
            console.log(this.unfinishedCurrentPage)
            return this.unfinishedPurchaseOrderData.slice(start, end)
        }
    },
    mounted() {
        this.getAllTotalPurchaseOrder()
        this.getAllPurchaseDivideOrder()
        this.getAllMaterialName()
    },
    methods: {
        async getAllMaterialName() {
            const response = await axios.get(`${this.$apiBaseUrl}/logistics/getallmaterialname`, {
                params: {
                    department: '1'
                }
            })
            this.materialNameOptions = response.data
        },
        handleIssueSelectionChange(selectedRows) {
            if (selectedRows.length > 0) {
                // Get the supplier name of the first selected row
                const supplierName = selectedRows[0].supplierName

                // Check if all selected rows have the same supplier name
                const hasDifferentSupplier = selectedRows.some(
                    (row) => row.supplierName !== supplierName
                )

                if (hasDifferentSupplier) {
                    // Show an error message
                    this.$message.error('只能选择同一家供应商的订单！')

                    // Restore the previous selection
                    this.$refs.issueTable.clearSelection() // Clear all selections
                    this.issueSelectedRows.forEach((row) => {
                        this.$refs.issueTable.toggleRowSelection(row, true) // Re-select previously selected rows
                    })
                    return
                }
            }

            // Update the selected rows
            this.issueSelectedRows = selectedRows
        },
        handlePageChange(type, page) {
            if (type === 'finished') {
                this.finishedCurrentPage = page
            } else if (type === 'unfinished') {
                this.unfinishedCurrentPage = page
            }
        },
        async getAllTotalPurchaseOrder() {
            const res = await axios.get(`${this.$apiBaseUrl}/multiissue/getalltotalpurchaseorder`)
            this.finishedPurchaseOrderData = res.data
        },
        async getAllPurchaseDivideOrder() {
            const res = await axios.get(`${this.$apiBaseUrl}/multiissue/getallpurchasedivideorder`)
            this.unfinishedPurchaseOrderData = res.data
            this.issuePageUnfinishedPurchaseOrderData = res.data
        },
        openIssueTotalPurchaseOrderDialog() {
            this.isIssueTotalPurchaseOrderDialogVisible = true
        },
        async openPreviewDialog(row) {
            this.shoeSizeColumns = await getShoeSizesName(row.orderId)
            this.currentShoeSizeType = this.shoeSizeColumns[0].type
            this.previewBomId = row.purchaseOrderId
            this.purchaseTestData = []
            try {
                const response = await axios.get(
                    `${this.$apiBaseUrl}/multiissue/getsinglepurchasedivideorder`,
                    {
                        params: {
                            purchaseDivideOrderId: row.purchaseDivideOrderId
                        }
                    }
                )
                this.purchaseTestData = response.data
                this.isPurchaseItemDetailDialogVisible = true
            } catch (error) {
                console.error(error)
            }
        },
        factoryFieldJudge(field) {
            return field !== 'N'
        },
        filteredColumns(array) {
            return this.shoeSizeColumns.filter((column) =>
                array.some(
                    (row) =>
                        row[column.prop] !== undefined &&
                        row[column.prop] !== null &&
                        row[column.prop] !== 0
                )
            )
        },
        filterByMaterialType(materialTypeId) {
            return this.materialNameOptions.filter((option) => option.type == materialTypeId)
        },
        handleSupplierChange() {
            this.issuePageUnfinishedPurchaseOrderData = this.unfinishedPurchaseOrderData.filter(
                (order) => order.supplierName.includes(this.SupplierInput)
            )
        },
        async createTotalPurchaseOrder() {
            const res = await axios.post(
                `${this.$apiBaseUrl}/multiissue/createtotalpurchaseorder`,
                {
                    purchaseDivideOrders: this.issueSelectedRows
                }
            )
            if (res.status === 200) {
                this.$message.success('下发成功')
                this.getAllTotalPurchaseOrder()
                this.getAllPurchaseDivideOrder()
                this.isIssueTotalPurchaseOrderDialogVisible = false
            } else {
                this.$message.error('下发失败')
            }
        },
        async openTotalPreviewDialog(row, mode) {
            this.modifiedMode = mode
            this.purchaseOrderCreateVis = true
            const res = await axios.get(
                `${this.$apiBaseUrl}/multiissue/getsingletotalpurchaseorder`,
                {
                    params: {
                        totalPurchaseOrderId: row.totalPurchaseOrderId
                    }
                }
            )
            this.tabPlaneData = res.data
            this.activeTab = this.tabPlaneData[0].totalPurchaseOrderId
        },
        async saveTotalPurchaseOrder() {
            try {
                await axios.post(`${this.$apiBaseUrl}/multiissue/savetotalpurchaseorder`, {
                    totalPurchaseOrders: this.tabPlaneData.map((order) => ({
                        ...order,
                        assetsItems: order.assetsItems.map((material) => ({
                            ...material,
                            materialInboundId: material.materialInboundId || null,
                            materialInboundName: material.materialInboundName || null,
                            materialInboundUnit: material.materialInboundUnit || null,
                            adjustPurchaseAmount: material.adjustPurchaseAmount || 0
                        }))
                    }))
                })
                this.$message.success('保存成功')
                this.getAllTotalPurchaseOrder()
                this.getAllPurchaseDivideOrder()
                this.purchaseOrderCreateVis = false
            }
            catch (error) {
                console.log(error)
                this.$message.error('保存失败')
            }
        },
        async submitTotalPurchaseOrder() {
            try {
                await axios.post(`${this.$apiBaseUrl}/multiissue/submittotalpurchaseorder`, {
                    totalPurchaseOrderId: this.activeTab
                })
                this.$message.success('提交成功')
                this.getAllTotalPurchaseOrder()
                this.getAllPurchaseDivideOrder()
                this.purchaseOrderCreateVis = false
            }
            catch (error) {
                console.log(error)
                this.$message.error('提交失败')
            }
        },
        changeFinishedOrderFilterStatus() {
            // Reset the current page to 1 when the filter changes
            this.finishedCurrentPage = 1
        },
        async handleMaterialNameSelect(row, selectedItem) {
            const response = await axios.get(
                `${this.$apiBaseUrl}/devproductionorder/getmaterialdetail?materialName=${row.materialInboundName}`
            )
            row.materialInboundId = response.data.materialId
            row.materialInboundUnit = response.data.unit
        }
    }
}
</script>
