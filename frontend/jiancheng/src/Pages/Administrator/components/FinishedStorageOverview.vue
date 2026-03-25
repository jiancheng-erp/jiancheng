<template>
    <div class="finished-storage-overview">
        <!-- 搜索栏 -->
        <el-form @submit.prevent="fetchOverview" class="search-bar">
            <el-form-item label="订单号">
                <el-input v-model="filters.orderRId" placeholder="订单号" clearable
                    style="width: 160px" @keyup.enter="fetchOverview" />
            </el-form-item>
            <el-form-item label="鞋型号">
                <el-input v-model="filters.shoeRId" placeholder="鞋型号" clearable
                    style="width: 160px" @keyup.enter="fetchOverview" />
            </el-form-item>
            <el-form-item label="客户">
                <el-input v-model="filters.customerName" placeholder="客户名称" clearable
                    style="width: 160px" @keyup.enter="fetchOverview" />
            </el-form-item>
            <el-form-item label="状态">
                <el-select v-model="filters.statusNum" placeholder="全部" clearable
                    style="width: 150px">
                    <el-option :value="0" label="未完成入库" />
                    <el-option :value="1" label="已完成入库" />
                    <el-option :value="2" label="已完成出库" />
                </el-select>
            </el-form-item>
            <el-form-item>
                <el-button type="primary" @click="fetchOverview">搜索</el-button>
                <el-button @click="resetFilters">重置</el-button>
            </el-form-item>
        </el-form>

        <!-- 统计卡片 -->
        <el-row :gutter="16" style="margin-bottom: 16px;">
            <el-col :span="6" v-for="card in statusCards" :key="card.status">
                <el-card shadow="hover" :body-style="{ padding: '16px' }"
                    @click="filterByStatus(card.status)"
                    style="cursor: pointer;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <div style="font-size: 13px; color: #909399;">{{ card.label }}</div>
                            <div style="font-size: 28px; font-weight: bold; margin-top: 4px;"
                                :style="{ color: card.color }">
                                {{ card.count }}
                            </div>
                        </div>
                        <el-icon :size="36" :color="card.color">
                            <component :is="card.icon" />
                        </el-icon>
                    </div>
                </el-card>
            </el-col>
        </el-row>

        <!-- 总览表格 -->
        <el-table :data="tableData" border stripe v-loading="loading"
            height="55vh" row-key="finishedShoeId">
            <el-table-column prop="orderRid" label="订单号" width="130" />
            <el-table-column prop="shoeRid" label="鞋型号" width="120" />
            <el-table-column prop="colorName" label="颜色" width="100" />
            <el-table-column prop="customerName" label="客户" min-width="120" />
            <el-table-column prop="customerProductName" label="客户款号" min-width="120" />
            <el-table-column prop="estimatedAmount" label="预计入库" width="90" align="center" />
            <el-table-column prop="actualAmount" label="实际入库" width="90" align="center" />
            <el-table-column prop="currentStock" label="当前库存" width="90" align="center">
                <template #default="{ row }">
                    <span :style="{ color: row.currentStock > 0 ? '#67c23a' : '#909399', fontWeight: 'bold' }">
                        {{ row.currentStock }}
                    </span>
                </template>
            </el-table-column>
            <el-table-column prop="statusLabel" label="状态" width="110" align="center">
                <template #default="{ row }">
                    <el-tag :type="statusTagType(row.status)" size="small">
                        {{ row.statusLabel }}
                    </el-tag>
                </template>
            </el-table-column>
            <el-table-column prop="updateTime" label="最近更新" width="150" />
            <el-table-column label="操作" width="120" fixed="right">
                <template #default="{ row }">
                    <el-button type="primary" link size="small"
                        @click="openRecords(row)">
                        入出库记录
                    </el-button>
                </template>
            </el-table-column>
        </el-table>

        <!-- 分页 -->
        <el-pagination
            v-model:current-page="pagination.page"
            v-model:page-size="pagination.pageSize"
            :total="pagination.total"
            :page-sizes="[20, 50, 100]"
            layout="total, sizes, prev, pager, next"
            style="margin-top: 12px; justify-content: flex-end;"
            @size-change="fetchOverview"
            @current-change="fetchOverview"
        />

        <!-- 入出库记录对话框 -->
        <el-dialog v-model="recordDialogVisible" destroy-on-close
            :title="recordDialogTitle" width="900px">
            <el-tabs v-model="activeRecordTab">
                <el-tab-pane label="入库记录" name="inbound">
                    <el-table :data="inboundRecords" border size="small"
                        v-loading="recordsLoading" max-height="400px">
                        <el-table-column prop="rid" label="入库单号" width="180" />
                        <el-table-column prop="amount" label="数量" width="80" align="center">
                            <template #default="{ row }">
                                <span :style="{ color: row.amount < 0 ? '#f56c6c' : '' }">
                                    {{ row.amount }}
                                </span>
                            </template>
                        </el-table-column>
                        <el-table-column prop="inboundTypeLabel" label="来源" width="80" align="center" />
                        <el-table-column prop="transactionTypeLabel" label="类型" width="80" align="center">
                            <template #default="{ row }">
                                <el-tag :type="row.transactionType === 1 ? 'success' : 'danger'" size="small">
                                    {{ row.transactionTypeLabel }}
                                </el-tag>
                            </template>
                        </el-table-column>
                        <el-table-column prop="datetime" label="时间" width="160" />
                        <el-table-column label="状态" width="80" align="center">
                            <template #default="{ row }">
                                <el-tag v-if="row.isDeleted" type="info" size="small">已撤回</el-tag>
                                <el-tag v-else-if="row.transactionType === 2" type="warning" size="small">撤回单</el-tag>
                                <el-tag v-else type="success" size="small">有效</el-tag>
                            </template>
                        </el-table-column>
                        <el-table-column label="操作" width="90" align="center">
                            <template #default="{ row }">
                                <el-button v-if="row.canRevert" type="danger" link size="small"
                                    @click="revertInbound(row)">
                                    撤回
                                </el-button>
                                <span v-else style="color: #c0c4cc; font-size: 12px;">—</span>
                            </template>
                        </el-table-column>
                    </el-table>
                </el-tab-pane>
                <el-tab-pane label="出库记录" name="outbound">
                    <el-table :data="outboundRecords" border size="small"
                        v-loading="recordsLoading" max-height="400px">
                        <el-table-column prop="rid" label="出库单号" width="180" />
                        <el-table-column prop="amount" label="数量" width="80" align="center" />
                        <el-table-column prop="picker" label="拣货人" width="100" />
                        <el-table-column prop="datetime" label="时间" width="160" />
                        <el-table-column prop="remark" label="备注" min-width="120" />
                        <el-table-column label="操作" width="90" align="center">
                            <template #default="{ row }">
                                <el-button type="danger" link size="small"
                                    @click="revertOutbound(row)">
                                    撤回
                                </el-button>
                            </template>
                        </el-table-column>
                    </el-table>
                </el-tab-pane>
            </el-tabs>
        </el-dialog>
    </div>
</template>

<script>
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Box, CircleCheck, Promotion, SuccessFilled } from '@element-plus/icons-vue'

export default {
    name: 'FinishedStorageOverview',
    components: { Box, CircleCheck, Promotion, SuccessFilled },
    data() {
        return {
            loading: false,
            tableData: [],
            filters: {
                orderRId: '',
                shoeRId: '',
                customerName: '',
                statusNum: null,
            },
            pagination: {
                page: 1,
                pageSize: 20,
                total: 0,
            },
            // 统计
            statusCounts: { 0: 0, 1: 0, 2: 0 },
            // 记录对话框
            recordDialogVisible: false,
            recordDialogTitle: '',
            activeRecordTab: 'inbound',
            currentStorageRow: null,
            inboundRecords: [],
            outboundRecords: [],
            recordsLoading: false,
        }
    },
    computed: {
        statusCards() {
            return [
                {
                    status: null,
                    label: '总记录',
                    count: this.pagination.total,
                    color: '#409eff',
                    icon: 'Box',
                },
                {
                    status: 0,
                    label: '未完成入库',
                    count: this.statusCounts[0],
                    color: '#e6a23c',
                    icon: 'Box',
                },
                {
                    status: 1,
                    label: '已完成入库',
                    count: this.statusCounts[1],
                    color: '#67c23a',
                    icon: 'CircleCheck',
                },
                {
                    status: 2,
                    label: '已完成出库',
                    count: this.statusCounts[2],
                    color: '#909399',
                    icon: 'SuccessFilled',
                },
            ]
        },
    },
    mounted() {
        this.fetchOverview()
        this.fetchStatusCounts()
    },
    methods: {
        async fetchOverview() {
            this.loading = true
            try {
                const params = {
                    page: this.pagination.page,
                    pageSize: this.pagination.pageSize,
                }
                if (this.filters.orderRId) params.orderRId = this.filters.orderRId
                if (this.filters.shoeRId) params.shoeRId = this.filters.shoeRId
                if (this.filters.customerName) params.customerName = this.filters.customerName
                if (this.filters.statusNum !== null && this.filters.statusNum !== '') {
                    params.statusNum = this.filters.statusNum
                }
                const res = await axios.get(
                    `${this.$apiBaseUrl}/admin/finished-storage-overview`,
                    { params }
                )
                this.tableData = res.data.result || []
                this.pagination.total = res.data.total || 0
            } catch (e) {
                console.error(e)
                ElMessage.error('获取成品库存概览失败')
            } finally {
                this.loading = false
            }
        },

        async fetchStatusCounts() {
            try {
                const counts = { 0: 0, 1: 0, 2: 0 }
                for (const s of [0, 1, 2]) {
                    const res = await axios.get(
                        `${this.$apiBaseUrl}/admin/finished-storage-overview`,
                        { params: { page: 1, pageSize: 1, statusNum: s } }
                    )
                    counts[s] = res.data.total || 0
                }
                this.statusCounts = counts
            } catch (e) {
                console.error(e)
            }
        },

        resetFilters() {
            this.filters = { orderRId: '', shoeRId: '', customerName: '', statusNum: null }
            this.pagination.page = 1
            this.fetchOverview()
            this.fetchStatusCounts()
        },

        filterByStatus(status) {
            this.filters.statusNum = status
            this.pagination.page = 1
            this.fetchOverview()
        },

        statusTagType(status) {
            const map = { 0: 'warning', 1: 'success', 2: 'info' }
            return map[status] || ''
        },

        async openRecords(row) {
            this.currentStorageRow = row
            this.recordDialogTitle = `入出库记录 - ${row.orderRid} / ${row.shoeRid} / ${row.colorName}`
            this.recordDialogVisible = true
            this.activeRecordTab = 'inbound'
            await this.fetchRecords(row.finishedShoeId)
        },

        async fetchRecords(finishedShoeId) {
            this.recordsLoading = true
            try {
                const [inRes, outRes] = await Promise.all([
                    axios.get(`${this.$apiBaseUrl}/admin/finished-storage-inbound-records`, {
                        params: { finishedShoeId },
                    }),
                    axios.get(`${this.$apiBaseUrl}/admin/finished-storage-outbound-records`, {
                        params: { finishedShoeId },
                    }),
                ])
                this.inboundRecords = inRes.data.result || []
                this.outboundRecords = outRes.data.result || []
            } catch (e) {
                console.error(e)
                ElMessage.error('获取入出库记录失败')
            } finally {
                this.recordsLoading = false
            }
        },

        async revertInbound(row) {
            try {
                await ElMessageBox.confirm(
                    `确认撤回入库记录 "${row.rid}"？\n入库数量: ${row.amount} 双\n撤回后将扣减库存，此操作不可逆。`,
                    '撤回入库',
                    { confirmButtonText: '确认撤回', cancelButtonText: '取消', type: 'warning' }
                )
            } catch {
                return
            }
            try {
                const res = await axios.delete(
                    `${this.$apiBaseUrl}/admin/revert-finished-inbound`,
                    { params: { detailId: row.detailId } }
                )
                ElMessage.success(res.data.message || '撤回成功')
                await this.fetchRecords(this.currentStorageRow.finishedShoeId)
                this.fetchOverview()
                this.fetchStatusCounts()
            } catch (e) {
                console.error(e)
                const msg = e.response?.data?.error || '撤回失败'
                ElMessage.error(msg)
            }
        },

        async revertOutbound(row) {
            try {
                await ElMessageBox.confirm(
                    `确认撤回出库记录 "${row.rid}"？\n出库数量: ${row.amount} 双\n撤回后将恢复库存，此操作不可逆。`,
                    '撤回出库',
                    { confirmButtonText: '确认撤回', cancelButtonText: '取消', type: 'warning' }
                )
            } catch {
                return
            }
            try {
                const res = await axios.delete(
                    `${this.$apiBaseUrl}/admin/revert-finished-outbound`,
                    { params: { detailId: row.detailId } }
                )
                ElMessage.success(res.data.message || '撤回成功')
                await this.fetchRecords(this.currentStorageRow.finishedShoeId)
                this.fetchOverview()
                this.fetchStatusCounts()
            } catch (e) {
                console.error(e)
                const msg = e.response?.data?.error || '撤回失败'
                ElMessage.error(msg)
            }
        },
    },
}
</script>

<style scoped>
.finished-storage-overview {
    padding: 16px;
}

.search-bar {
    margin-bottom: 12px;
    display: flex !important;
    flex-direction: row !important;
    flex-wrap: wrap;
    align-items: center;
    gap: 12px 16px;
}

.search-bar :deep(.el-form-item) {
    display: flex !important;
    flex-direction: row !important;
    align-items: center;
    margin-bottom: 0;
    margin-right: 0;
}

.search-bar :deep(.el-form-item__label) {
    padding-right: 4px;
    flex-shrink: 0;
}

.search-bar :deep(.el-form-item__content) {
    flex-wrap: nowrap;
}
</style>
