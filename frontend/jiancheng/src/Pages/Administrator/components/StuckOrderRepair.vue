<template>
    <div class="stuck-order-repair">
        <el-alert type="warning" :closable="false" show-icon style="margin-bottom: 12px;">
            <div>
                检测「成品已全部出库，但订单主状态仍卡在生产/发货阶段、未推进到<strong>订单完成</strong>」的断链订单。
                常见成因：最后一批为<strong>损失出库</strong>，损失出库不会自动推进订单完成。
                请人工复核后点击「推进到订单完成」修复。
            </div>
        </el-alert>

        <div class="toolbar">
            <el-button type="primary" @click="fetchList" :loading="loading">刷新检测</el-button>
            <span class="stats">共 {{ total }} 个疑似断链订单</span>
        </div>

        <el-table :data="rows" border stripe v-loading="loading" height="60vh" size="small">
            <el-table-column type="index" label="序号" width="60" align="center" />
            <el-table-column prop="orderRId" label="订单号" min-width="120" show-overflow-tooltip />
            <el-table-column prop="orderCId" label="客户订单号" min-width="120" show-overflow-tooltip />
            <el-table-column prop="customerName" label="客户" min-width="120" show-overflow-tooltip />
            <el-table-column label="当前订单状态" min-width="140">
                <template #default="{ row }">
                    <el-tag type="danger" size="small">{{ row.currentStatusName }}（{{ row.currentStatus }}）</el-tag>
                </template>
            </el-table-column>
            <el-table-column prop="storageCount" label="成品库存记录数" width="120" align="center" />
            <el-table-column prop="estimatedAmount" label="核定总量" width="110" align="center" />
            <el-table-column label="操作" width="150" fixed="right">
                <template #default="{ row }">
                    <el-button type="success" link @click="advance(row)">推进到订单完成</el-button>
                </template>
            </el-table-column>
        </el-table>

        <el-empty v-if="!loading && rows.length === 0" description="未发现断链订单" />
    </div>
</template>

<script>
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'

export default {
    name: 'StuckOrderRepair',
    data() {
        return {
            rows: [],
            total: 0,
            loading: false
        }
    },
    mounted() {
        this.$setAxiosToken && this.$setAxiosToken()
        this.fetchList()
    },
    methods: {
        async fetchList() {
            this.loading = true
            try {
                const { data } = await axios.get(`${this.$apiBaseUrl}/warehouse/admin/stuckoutboundorders`)
                this.rows = data?.result || []
                this.total = data?.total || 0
            } catch (e) {
                console.error(e)
                ElMessage.error('检测失败')
            } finally {
                this.loading = false
            }
        },
        async advance(row) {
            try {
                await ElMessageBox.confirm(
                    `确认将订单 ${row.orderRId} 从「${row.currentStatusName}」强制推进到「订单完成」？此操作仅在成品已全部出库时可用。`,
                    '确认推进',
                    { confirmButtonText: '确认推进', cancelButtonText: '取消', type: 'warning' }
                )
            } catch {
                return
            }
            try {
                const { data } = await axios.post(`${this.$apiBaseUrl}/warehouse/admin/advancestuckorder`, {
                    orderId: row.orderId
                })
                ElMessage.success(data?.message || '订单已推进到订单完成')
                this.fetchList()
            } catch (e) {
                const msg = e?.response?.data?.message || '推进失败'
                ElMessage.error(msg)
            }
        }
    }
}
</script>

<style scoped>
.stuck-order-repair {
    width: 100%;
}

.toolbar {
    display: flex;
    align-items: center;
    gap: 16px;
    margin-bottom: 12px;
}

.stats {
    color: var(--color-text-3);
    font-size: 13px;
}
</style>
