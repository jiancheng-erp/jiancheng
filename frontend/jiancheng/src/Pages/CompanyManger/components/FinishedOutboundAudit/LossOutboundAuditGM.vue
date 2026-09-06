<template>
  <div class="loss-outbound-audit">
    <!-- 筛选 -->
    <el-form :inline="true" class="mb-2">
      <el-form-item label="状态">
        <el-select class="u-w-140" v-model="filters.status" @change="onSearch">
          <el-option label="待审批" :value="1" />
          <el-option label="已通过" :value="4" />
          <el-option label="已驳回" :value="2" />
          <el-option label="全部" :value="null" />
        </el-select>
      </el-form-item>
      <el-form-item label="订单号">
        <el-input class="u-w-160" v-model="filters.orderRId" placeholder="订单号" clearable />
      </el-form-item>
      <el-form-item label="申请单号">
        <el-input class="u-w-180" v-model="filters.applyRId" placeholder="申请单号" clearable />
      </el-form-item>
      <el-form-item label="客户名称">
        <el-input class="u-w-160" v-model="filters.customerName" placeholder="客户名称" clearable />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="onSearch">查询</el-button>
        <el-button @click="resetFilters">重置</el-button>
      </el-form-item>
    </el-form>

    <el-table :data="tableData" border stripe size="small" style="width: 100%">
      <el-table-column label="明细" width="80" fixed="left">
        <template #default="{ row }">
          <el-button type="primary" link @click="openDetailDialog(row)">查看</el-button>
        </template>
      </el-table-column>
      <el-table-column prop="applyRId" label="申请单号" width="200" />
      <el-table-column prop="createTime" label="申请时间" width="170" />
      <el-table-column prop="orderRId" label="订单号" width="140" />
      <el-table-column prop="orderCId" label="客户订单号" width="140" />
      <el-table-column prop="customerName" label="客户名称" min-width="140" />
      <el-table-column prop="totalPairs" label="损失双数" width="110" />
      <el-table-column prop="statusLabel" label="状态" width="120" />
      <el-table-column prop="actualOutboundTime" label="出库时间" width="170" />
      <el-table-column prop="remark" label="备注" min-width="160" show-overflow-tooltip />
      <el-table-column label="操作" width="170" fixed="right">
        <template #default="{ row }">
          <template v-if="row.status === 1">
            <el-button type="success" size="small" @click="openAudit(row, 'approve')">通过</el-button>
            <el-button type="danger" size="small" @click="openAudit(row, 'reject')">驳回</el-button>
          </template>
          <span v-else style="color: var(--color-text-3);">—</span>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination
      class="pagination"
      background
      layout="total, prev, pager, next, sizes"
      :total="total"
      :page-size="pageSize"
      :current-page="currentPage"
      :page-sizes="[20, 50, 100]"
      @current-change="handlePageChange"
      @size-change="handleSizeChange"
    />

    <!-- 明细对话框 -->
    <el-dialog :title="`损失出库明细 - ${currentDetailRow?.applyRId || ''}`" v-model="detailDialogVisible" width="70%">
      <el-table v-loading="detailLoading" :data="currentDetailRow?.details || []" border stripe size="small">
        <el-table-column prop="shoeRId" label="工厂型号" min-width="130" />
        <el-table-column prop="customerProductName" label="客户型号" min-width="130" />
        <el-table-column prop="colorName" label="颜色" width="90" />
        <el-table-column prop="batchName" label="配码名称" min-width="110" />
        <el-table-column prop="pairsPerCarton" label="每箱双数" width="100" align="center" />
        <el-table-column prop="cartonCount" label="箱数" width="90" align="center" />
        <el-table-column prop="totalPairs" label="损失双数" width="100" align="center" />
        <el-table-column prop="currentStock" label="当前库存" width="100" align="center" />
        <el-table-column prop="remark" label="备注" min-width="120" show-overflow-tooltip />
      </el-table>
      <template #footer>
        <el-button @click="detailDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- 审批对话框 -->
    <el-dialog
      v-model="auditDialogVisible"
      :title="auditAction === 'approve' ? '通过损失出库申请' : '驳回损失出库申请'"
      width="460px"
    >
      <p v-if="auditAction === 'approve'" style="margin-bottom: 10px; color: var(--color-warning);">
        通过后将立即执行损失出库并扣减库存，操作不可逆。
      </p>
      <el-form :model="auditForm" label-width="80px">
        <el-form-item label="审批意见">
          <el-input v-model="auditForm.remark" type="textarea" :rows="3" placeholder="选填：审批意见" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="auditDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="auditSubmitting" @click="submitAudit">确认</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import axios from 'axios'
import { ElMessage } from 'element-plus'

export default {
  name: 'LossOutboundAuditGM',
  data() {
    return {
      filters: {
        status: 1,
        orderRId: '',
        applyRId: '',
        customerName: ''
      },
      tableData: [],
      total: 0,
      currentPage: 1,
      pageSize: 20,

      detailDialogVisible: false,
      detailLoading: false,
      currentDetailRow: null,

      auditDialogVisible: false,
      auditSubmitting: false,
      auditAction: 'approve',
      auditRow: null,
      auditForm: { remark: '' }
    }
  },
  mounted() {
    this.loadTable()
  },
  methods: {
    async loadTable() {
      const params = {
        page: this.currentPage,
        pageSize: this.pageSize,
        status: this.filters.status,
        orderRId: this.filters.orderRId || undefined,
        applyRId: this.filters.applyRId || undefined,
        customerName: this.filters.customerName || undefined
      }
      try {
        const res = await axios.get(`${this.$apiBaseUrl}/warehouse/loss-outbound/list`, { params })
        this.tableData = (res.data.result || []).map((item) => ({
          ...item,
          detailLoaded: false,
          details: []
        }))
        this.total = res.data.total || 0
      } catch (e) {
        console.error(e)
        ElMessage.error(e.response?.data?.message || '获取损失出库申请失败')
      }
    },
    onSearch() {
      this.currentPage = 1
      this.loadTable()
    },
    resetFilters() {
      this.filters = { status: 1, orderRId: '', applyRId: '', customerName: '' }
      this.currentPage = 1
      this.loadTable()
    },
    handlePageChange(p) {
      this.currentPage = p
      this.loadTable()
    },
    handleSizeChange(s) {
      this.pageSize = s
      this.currentPage = 1
      this.loadTable()
    },
    async openDetailDialog(row) {
      this.currentDetailRow = row
      this.detailDialogVisible = true
      if (row.detailLoaded) return
      this.detailLoading = true
      try {
        const res = await axios.get(`${this.$apiBaseUrl}/warehouse/outbound-apply/detail`, {
          params: { applyId: row.applyId }
        })
        row.details = res.data.details || []
        row.detailLoaded = true
      } catch (e) {
        console.error(e)
        ElMessage.error(e.response?.data?.message || '加载明细失败')
      } finally {
        this.detailLoading = false
      }
    },
    openAudit(row, action) {
      this.auditRow = row
      this.auditAction = action
      this.auditForm.remark = ''
      this.auditDialogVisible = true
    },
    async submitAudit() {
      if (!this.auditRow) return
      this.auditSubmitting = true
      try {
        const res = await axios.post(`${this.$apiBaseUrl}/warehouse/loss-outbound/audit`, {
          applyId: this.auditRow.applyId,
          action: this.auditAction,
          remark: this.auditForm.remark
        })
        ElMessage.success(res.data.message || '操作成功')
        this.auditDialogVisible = false
        this.loadTable()
      } catch (e) {
        console.error(e)
        ElMessage.error(e.response?.data?.message || '操作失败')
      } finally {
        this.auditSubmitting = false
      }
    }
  }
}
</script>

<style scoped>
.mb-2 {
  margin-bottom: 8px;
}
.pagination {
  margin-top: 12px;
  justify-content: flex-end;
}
</style>
