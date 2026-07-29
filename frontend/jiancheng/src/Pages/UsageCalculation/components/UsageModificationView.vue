<template>
    <div class="usage-modification">
        <!-- 订单列表 -->
        <template v-if="!currentOrder">
            <el-card shadow="never" class="header-card">
                <div class="page-title">用量修改</div>
                <el-alert type="info" :closable="false" show-icon
                    title="仅显示已完成一次采购订单创建与二次采购订单创建的订单。修改用量后，采购用量也可在此处修改。"
                    style="margin-bottom: 12px" />
                <el-form :inline="true" @submit.prevent>
                    <el-form-item label="搜索">
                        <el-input v-model="orderKeyword" placeholder="订单号 / 客户名称" clearable :prefix-icon="Search"
                            style="width: 280px" @keyup.enter="fetchOrders" @clear="fetchOrders" />
                    </el-form-item>
                    <el-form-item>
                        <el-button type="primary" :loading="orderLoading" @click="fetchOrders">查询</el-button>
                        <el-button @click="resetOrderSearch">重置</el-button>
                    </el-form-item>
                </el-form>
            </el-card>

            <el-card shadow="never" class="table-card">
                <template #header>
                    <div class="card-header">
                        <span>可修改用量订单（共 {{ orderList.length }} 条）</span>
                    </div>
                </template>
                <el-table :data="pagedOrderList" border stripe v-loading="orderLoading" style="width: 100%">
                    <el-table-column type="index" label="序号" width="70" align="center"
                        :index="orderIndexMethod" />
                    <el-table-column prop="orderRid" label="订单编号" align="center" />
                    <el-table-column prop="customerName" label="客户名称" align="center" />
                    <el-table-column prop="createTime" label="订单创建时间" align="center" />
                    <el-table-column prop="deadlineTime" label="预计截止日期" align="center" />
                    <el-table-column label="操作" align="center" width="160">
                        <template #default="scope">
                            <el-button type="primary" @click="openOrder(scope.row)">查看鞋型</el-button>
                        </template>
                    </el-table-column>
                </el-table>
                <div class="pagination-bar">
                    <el-pagination background layout="total, sizes, prev, pager, next, jumper"
                        :total="orderList.length" :current-page="orderPage" :page-size="orderPageSize"
                        :page-sizes="[10, 20, 50, 100]" @current-change="onOrderPageChange"
                        @size-change="onOrderPageSizeChange" />
                </div>
            </el-card>
        </template>

        <!-- 鞋型列表 -->
        <template v-else>
            <el-card shadow="never" class="table-card">
                <template #header>
                    <div class="card-header">
                        <div>
                            <el-button :icon="Back" @click="backToOrders">返回订单列表</el-button>
                            <span style="margin-left: 16px; font-weight: bold; font-size: larger">
                                订单 {{ currentOrder.orderRid }} - {{ currentOrder.customerName }}
                            </span>
                        </div>
                    </div>
                </template>
                <el-table :data="shoeList" border stripe v-loading="shoeLoading" style="width: 100%">
                    <el-table-column type="index" label="序号" width="70" align="center" />
                    <el-table-column prop="inheritId" label="工厂型号" align="center" />
                    <el-table-column prop="customerId" label="客户型号" align="center" />
                    <el-table-column prop="color" label="颜色" align="center" />
                    <el-table-column prop="designer" label="设计员" align="center" />
                    <el-table-column prop="editter" label="调版员" align="center" />
                    <el-table-column label="操作" align="center" width="160">
                        <template #default="scope">
                            <el-button type="primary" @click="openShoe(scope.row)">修改用量</el-button>
                        </template>
                    </el-table-column>
                </el-table>
            </el-card>
        </template>

        <!-- 用量修改对话框 -->
        <el-dialog :title="`用量修改 - ${currentShoe.inheritId || ''}${currentShoe.color ? ' / ' + currentShoe.color : ''}`" v-model="editDialogVisible" width="90%"
            :close-on-click-modal="false" fullscreen>
            <el-table :data="bomItems" border stripe v-loading="bomLoading" style="width: 100%" height="70vh">
                <el-table-column type="index" label="序号" width="60" fixed="left" />
                <el-table-column prop="materialType" label="材料类型" width="100" fixed="left" />
                <el-table-column prop="materialName" label="材料名称" min-width="140" fixed="left" />
                <el-table-column prop="materialModel" label="材料型号" min-width="120" />
                <el-table-column prop="materialSpecification" label="材料规格" min-width="120" />
                <el-table-column prop="color" label="颜色" width="90" />
                <el-table-column label="工艺" min-width="160">
                    <template #default="scope">
                        <span style="white-space: pre-wrap">{{ scope.row.craftName }}</span>
                    </template>
                </el-table-column>
                <el-table-column prop="unit" label="单位" width="80" />
                <el-table-column label="单位用量" width="150">
                    <template #default="scope">
                        <el-input-number v-model="scope.row.unitUsage" :min="0" :controls="false" size="small"
                            style="width: 120px" @change="onUnitUsageChange(scope.row)" />
                    </template>
                </el-table-column>
                <el-table-column label="核定用量" width="180">
                    <template #default="scope">
                        <el-input-number v-if="scope.row.materialCategory == 0" v-model="scope.row.approvalUsage"
                            :min="0" :controls="false" size="small" style="width: 120px" disabled />
                        <el-button v-else type="primary" size="small" @click="openSizeDialog(scope.row)">
                            分码用量({{ sumSizeApproval(scope.row) }})
                        </el-button>
                    </template>
                </el-table-column>
                <el-table-column label="采购用量" width="180">
                    <template #default="scope">
                        <template v-if="scope.row.purchaseOrderItemId">
                            <el-input-number v-if="scope.row.materialCategory == 0" v-model="scope.row.purchaseAmount"
                                :min="0" :controls="false" size="small" style="width: 120px" />
                            <el-button v-else type="warning" size="small" @click="openSizeDialog(scope.row)">
                                分码采购({{ sumSizePurchase(scope.row) }})
                            </el-button>
                        </template>
                        <span v-else class="muted">未生成采购项</span>
                    </template>
                </el-table-column>
            </el-table>
            <template #footer>
                <el-button @click="editDialogVisible = false">取消</el-button>
                <el-button type="primary" :loading="saving" @click="saveModification">保存</el-button>
            </template>
        </el-dialog>

        <!-- 分码用量 / 采购量填写 -->
        <el-dialog title="分码用量 / 采购量填写" v-model="sizeDialogVisible" width="60%" :close-on-click-modal="false">
            <el-table :data="sizeData" border stripe>
                <el-table-column prop="size" label="尺码" align="center" />
                <el-table-column label="核定用量" align="center">
                    <template #default="scope">
                        <el-input-number v-model="scope.row.approvalAmount" :min="0" :controls="false" size="small"
                            disabled />
                    </template>
                </el-table-column>
                <el-table-column label="采购用量" align="center">
                    <template #default="scope">
                        <el-input-number v-model="scope.row.purchaseAmount" :min="0" :controls="false" size="small"
                            :disabled="!currentSizeRow || !currentSizeRow.purchaseOrderItemId" />
                    </template>
                </el-table-column>
            </el-table>
            <template #footer>
                <el-button @click="sizeDialogVisible = false">取消</el-button>
                <el-button type="primary" @click="confirmSizeData">确认</el-button>
            </template>
        </el-dialog>
    </div>
</template>

<script>
import axios from 'axios'
import { Search, Back } from '@element-plus/icons-vue'
import { markRaw } from 'vue'

export default {
    name: 'UsageModificationView',
    data() {
        return {
            Search: markRaw(Search),
            Back: markRaw(Back),
            orderKeyword: '',
            orderList: [],
            orderLoading: false,
            orderPage: 1,
            orderPageSize: 20,
            currentOrder: null,
            shoeList: [],
            shoeLoading: false,
            currentShoe: {},
            editDialogVisible: false,
            bomItems: [],
            bomLoading: false,
            saving: false,
            sizeDialogVisible: false,
            sizeData: [],
            currentSizeRow: null
        }
    },
    mounted() {
        this.$setAxiosToken()
        this.fetchOrders()
    },
    computed: {
        pagedOrderList() {
            const start = (this.orderPage - 1) * this.orderPageSize
            return this.orderList.slice(start, start + this.orderPageSize)
        }
    },
    methods: {
        orderIndexMethod(index) {
            return (this.orderPage - 1) * this.orderPageSize + index + 1
        },
        onOrderPageChange(page) {
            this.orderPage = page
        },
        onOrderPageSizeChange(size) {
            this.orderPageSize = size
            this.orderPage = 1
        },
        resetOrderSearch() {
            this.orderKeyword = ''
            this.fetchOrders()
        },
        async fetchOrders() {
            this.orderLoading = true
            try {
                const response = await axios.get(`${this.$apiBaseUrl}/usagemodification/orders`, {
                    params: { keyword: this.orderKeyword }
                })
                this.orderList = response.data
                this.orderPage = 1
            } catch (error) {
                console.log(error)
                this.$message.error('获取订单列表失败')
            } finally {
                this.orderLoading = false
            }
        },
        async openOrder(row) {
            this.currentOrder = row
            await this.fetchShoeList()
        },
        backToOrders() {
            this.currentOrder = null
            this.shoeList = []
        },
        async fetchShoeList() {
            this.shoeLoading = true
            try {
                const response = await axios.get(`${this.$apiBaseUrl}/usagemodification/ordershoes`, {
                    params: { orderId: this.currentOrder.orderId }
                })
                this.shoeList = response.data
            } catch (error) {
                console.log(error)
                this.$message.error('获取鞋型列表失败')
            } finally {
                this.shoeLoading = false
            }
        },
        async openShoe(row) {
            this.currentShoe = row
            this.editDialogVisible = true
            await this.fetchBomItems(row)
        },
        async fetchBomItems(row) {
            this.bomLoading = true
            try {
                const response = await axios.get(`${this.$apiBaseUrl}/usagemodification/bomitems`, {
                    params: { orderShoeTypeId: row.orderShoeTypeId, orderId: this.currentOrder.orderId }
                })
                this.bomItems = response.data.map((item) => ({
                    ...item,
                    unitUsage: item.unitUsage != null ? Number(item.unitUsage) : 0,
                    approvalUsage: item.approvalUsage != null ? Number(item.approvalUsage) : 0,
                    purchaseAmount: item.purchaseAmount != null ? Number(item.purchaseAmount) : 0,
                    orderTotalPairs: Number(item.orderTotalPairs) || 0,
                    sizeInfo: (item.sizeInfo || []).map((s) => ({
                        size: s.size,
                        approvalAmount: Number(s.approvalAmount) || 0,
                        purchaseAmount: Number(s.purchaseAmount) || 0,
                        orderPairs: Number(s.orderPairs) || 0
                    }))
                }))
            } catch (error) {
                console.log(error)
                this.$message.error('获取材料明细失败')
            } finally {
                this.bomLoading = false
            }
        },
        sumSizeApproval(row) {
            return (row.sizeInfo || []).reduce((total, s) => total + (Number(s.approvalAmount) || 0), 0)
        },
        sumSizePurchase(row) {
            return (row.sizeInfo || []).reduce((total, s) => total + (Number(s.purchaseAmount) || 0), 0)
        },
        onUnitUsageChange(row) {
            const unit = Number(row.unitUsage) || 0
            if (row.materialCategory == 0) {
                // 非分码：核定用量 = 单位用量 × 订单总双数
                row.approvalUsage = Number((unit * (Number(row.orderTotalPairs) || 0)).toFixed(3))
            } else {
                // 分码：各码核定用量 = 单位用量 × 该码下单双数
                ;(row.sizeInfo || []).forEach((s) => {
                    s.approvalAmount = Math.ceil(unit * (Number(s.orderPairs) || 0))
                })
                row.approvalUsage = this.sumSizeApproval(row)
            }
        },
        openSizeDialog(row) {
            this.currentSizeRow = row
            // 深拷贝，确认后再写回
            this.sizeData = (row.sizeInfo || []).map((s) => ({
                size: s.size,
                approvalAmount: Number(s.approvalAmount) || 0,
                purchaseAmount: Number(s.purchaseAmount) || 0
            }))
            this.sizeDialogVisible = true
        },
        confirmSizeData() {
            if (this.currentSizeRow) {
                this.currentSizeRow.sizeInfo = this.sizeData.map((s) => ({ ...s }))
                // 同步核定/采购总量
                this.currentSizeRow.approvalUsage = this.sumSizeApproval(this.currentSizeRow)
                if (this.currentSizeRow.purchaseOrderItemId) {
                    this.currentSizeRow.purchaseAmount = this.sumSizePurchase(this.currentSizeRow)
                }
            }
            this.sizeDialogVisible = false
        },
        async saveModification() {
            this.saving = true
            try {
                const items = this.bomItems.map((item) => ({
                    bomItemId: item.bomItemId,
                    purchaseOrderItemId: item.purchaseOrderItemId,
                    materialCategory: item.materialCategory,
                    unitUsage: item.unitUsage,
                    approvalUsage: item.approvalUsage,
                    purchaseAmount: item.purchaseAmount,
                    sizeInfo: item.sizeInfo
                }))
                await axios.post(`${this.$apiBaseUrl}/usagemodification/save`, { items })
                this.$message.success('保存成功')
                this.editDialogVisible = false
            } catch (error) {
                console.log(error)
                this.$message.error('保存失败')
            } finally {
                this.saving = false
            }
        }
    }
}
</script>

<style scoped>
.usage-modification {
    padding: 12px;
}

.header-card {
    margin-bottom: 12px;
}

.page-title {
    font-size: 22px;
    font-weight: 600;
    text-align: center;
    margin-bottom: 12px;
}

.table-card {
    margin-bottom: 12px;
}

.card-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    font-weight: 600;
}

.pagination-bar {
    display: flex;
    justify-content: flex-end;
    margin-top: 12px;
}

.muted {
    color: #909399;
}
</style>
