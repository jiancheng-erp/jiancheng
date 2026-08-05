<template>
    <div class="purchase-approval-adjust">
        <el-alert type="info" :closable="false" show-icon style="margin-bottom: 12px;">
            <div>
                筛选「实际采购数量远大于核定用量」的采购明细。实际下单量取
                <strong>调整数量优先、否则原采购数量</strong>。请人工复核后调整。
            </div>
        </el-alert>

        <div class="toolbar">
            <el-form inline @submit.prevent="search">
                <el-form-item label="订单号/工厂型号">
                    <el-input v-model="query.keyword" placeholder="模糊搜索" clearable style="width: 200px"
                        @keyup.enter="search" />
                </el-form-item>
                <el-form-item label="倍数阈值">
                    <el-input-number v-model="query.ratio" :min="1" :step="0.5" :precision="1"
                        controls-position="right" style="width: 120px" />
                </el-form-item>
                <el-form-item label="最小差值">
                    <el-input-number v-model="query.minExcess" :min="0" :step="10"
                        controls-position="right" style="width: 120px" />
                </el-form-item>
                <el-form-item label="核定下限">
                    <el-input-number v-model="query.minApproval" :min="0" :step="10"
                        controls-position="right" style="width: 120px" />
                </el-form-item>
                <el-form-item>
                    <el-checkbox v-model="query.includeZeroApproval">含无核定却采购</el-checkbox>
                </el-form-item>
                <el-form-item>
                    <el-button type="primary" @click="search" :loading="loading">查询</el-button>
                </el-form-item>
                <el-form-item>
                    <span class="stats">共 {{ total }} 条</span>
                </el-form-item>
            </el-form>
        </div>

        <el-table :data="rows" border stripe v-loading="loading" height="60vh" size="small">
            <el-table-column prop="orderRid" label="订单号" min-width="110" show-overflow-tooltip />
            <el-table-column prop="shoeRid" label="工厂型号" min-width="100" show-overflow-tooltip />
            <el-table-column prop="customerProductName" label="客户款号" min-width="100" show-overflow-tooltip />
            <el-table-column prop="purchaseOrderRid" label="采购单号" min-width="140" show-overflow-tooltip />
            <el-table-column prop="purchaseType" label="类型" width="90" />
            <el-table-column prop="materialName" label="材料" min-width="100" show-overflow-tooltip />
            <el-table-column prop="supplierName" label="供应商" min-width="110" show-overflow-tooltip />
            <el-table-column prop="materialModel" label="型号" min-width="80" show-overflow-tooltip />
            <el-table-column prop="materialSpecification" label="规格" min-width="90" show-overflow-tooltip />
            <el-table-column prop="color" label="颜色" min-width="70" show-overflow-tooltip />
            <el-table-column prop="inboundUnit" label="单位" width="60" />
            <el-table-column prop="approvalAmount" label="核定用量" width="90" />
            <el-table-column prop="purchaseAmount" label="采购数量" width="90" />
            <el-table-column prop="adjustPurchaseAmount" label="调整数量" width="90" />
            <el-table-column prop="effectiveAmount" label="实际下单" width="90" />
            <el-table-column label="倍数" width="80">
                <template #default="{ row }">
                    <el-tag v-if="row.ratio != null" type="danger" size="small">
                        {{ row.ratio.toFixed(1) }}×
                    </el-tag>
                    <el-tag v-else type="warning" size="small">∞</el-tag>
                </template>
            </el-table-column>
            <el-table-column prop="reason" label="原因" width="120" />
            <el-table-column label="操作" width="90" fixed="right">
                <template #default="{ row }">
                    <el-button type="primary" link @click="openAdjust(row)">调整</el-button>
                </template>
            </el-table-column>
        </el-table>

        <el-pagination class="pager" background layout="total, sizes, prev, pager, next, jumper"
            :total="total" :page-size="pageSize" :current-page="page"
            :page-sizes="[10, 20, 50, 100]"
            @size-change="handleSizeChange" @current-change="handlePageChange" />

        <el-dialog v-model="dialogVisible" title="调整采购明细" width="460px" append-to-body>
            <div v-if="editingRow" class="edit-body">
                <el-descriptions :column="1" border size="small" style="margin-bottom: 12px;">
                    <el-descriptions-item label="订单/型号">
                        {{ editingRow.orderRid }} / {{ editingRow.shoeRid }}
                    </el-descriptions-item>
                    <el-descriptions-item label="材料">
                        {{ editingRow.materialName }}
                        <span v-if="editingRow.materialModel">/ {{ editingRow.materialModel }}</span>
                        <span v-if="editingRow.materialSpecification">/ {{ editingRow.materialSpecification }}</span>
                    </el-descriptions-item>
                    <el-descriptions-item label="采购单号">{{ editingRow.purchaseOrderRid }}</el-descriptions-item>
                    <el-descriptions-item label="原采购数量">{{ editingRow.purchaseAmount }}</el-descriptions-item>
                </el-descriptions>
                <el-form label-width="110px">
                    <el-form-item label="核定用量">
                        <el-input-number v-model="editForm.approvalAmount" :min="0" :step="1"
                            controls-position="right" style="width: 220px" />
                    </el-form-item>
                    <el-form-item label="调整采购数量">
                        <el-input-number v-model="editForm.adjustPurchaseAmount" :min="0" :step="1"
                            controls-position="right" style="width: 220px" />
                        <div class="hint">留空/为 0 时以原采购数量生效</div>
                    </el-form-item>
                </el-form>
            </div>
            <template #footer>
                <el-button @click="dialogVisible = false">取消</el-button>
                <el-button type="primary" @click="saveAdjust" :loading="saving">保存</el-button>
            </template>
        </el-dialog>
    </div>
</template>

<script>
import axios from 'axios'
import { ElMessage } from 'element-plus'

export default {
    name: 'PurchaseApprovalAdjust',
    data() {
        return {
            query: {
                keyword: '',
                ratio: 3,
                minExcess: 0,
                minApproval: 0,
                includeZeroApproval: true
            },
            rows: [],
            total: 0,
            loading: false,
            page: 1,
            pageSize: 20,
            dialogVisible: false,
            saving: false,
            editingRow: null,
            editForm: {
                approvalAmount: 0,
                adjustPurchaseAmount: 0
            }
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
                const { data } = await axios.get(`${this.$apiBaseUrl}/purchaseadjust/list`, {
                    params: {
                        keyword: this.query.keyword || undefined,
                        ratio: this.query.ratio,
                        minExcess: this.query.minExcess,
                        minApproval: this.query.minApproval,
                        includeZeroApproval: this.query.includeZeroApproval ? 1 : 0,
                        page: this.page,
                        pageSize: this.pageSize
                    }
                })
                this.rows = data?.result || []
                this.total = data?.total || 0
            } catch (e) {
                console.error(e)
                ElMessage.error('查询失败')
            } finally {
                this.loading = false
            }
        },
        search() {
            this.page = 1
            this.fetchList()
        },
        handlePageChange(p) {
            this.page = p
            this.fetchList()
        },
        handleSizeChange(size) {
            this.pageSize = size
            this.page = 1
            this.fetchList()
        },
        openAdjust(row) {
            this.editingRow = row
            this.editForm.approvalAmount = Number(row.approvalAmount || 0)
            this.editForm.adjustPurchaseAmount = Number(row.adjustPurchaseAmount || 0)
            this.dialogVisible = true
        },
        async saveAdjust() {
            if (!this.editingRow) return
            this.saving = true
            try {
                await axios.post(`${this.$apiBaseUrl}/purchaseadjust/adjust`, {
                    purchaseOrderItemId: this.editingRow.purchaseOrderItemId,
                    approvalAmount: this.editForm.approvalAmount,
                    adjustPurchaseAmount: this.editForm.adjustPurchaseAmount
                })
                ElMessage.success('已保存')
                this.dialogVisible = false
                await this.fetchList()
            } catch (e) {
                console.error(e)
                ElMessage.error(e?.response?.data?.message || '保存失败')
            } finally {
                this.saving = false
            }
        }
    }
}
</script>

<style scoped>
.toolbar {
    margin-bottom: 8px;
}
.stats {
    color: #909399;
    font-size: 13px;
}
.pager {
    margin-top: 12px;
    justify-content: flex-end;
}
.hint {
    color: #909399;
    font-size: 12px;
    margin-left: 8px;
}
</style>
