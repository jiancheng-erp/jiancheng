<template>
  <div class="page p-4">
    <!-- ===== 筛选区 ===== -->
    <el-card shadow="never" class="mb-3">
      <el-form :inline="true" :model="filters" @keyup.enter="loadTable">
        <el-form-item label="客户">
          <el-input
            v-model="filters.customerName"
            placeholder="客户名称"
            clearable
          />
        </el-form-item>

        <el-form-item label="订单号">
          <el-input
            v-model="filters.orderRId"
            placeholder="订单号"
            clearable
          />
        </el-form-item>

        <el-form-item label="申请单号">
          <el-input
            v-model="filters.applyRId"
            placeholder="SOA 开头的申请单号"
            clearable
          />
        </el-form-item>

        <el-form-item label="状态">
          <el-select
            v-model="filters.status"
            clearable
            placeholder="全部"
            style="min-width: 140px"
          >
            <!-- 这里的 null 表示“全部清单” -->
            <el-option :value="null" label="全部" />
            <!-- 1=待总经理审核（默认值） -->
            <el-option :value="STATUS_ENUM.PENDING" label="待总经理审核" />
            <!-- 3=已通过，待仓库出库 -->
            <el-option :value="STATUS_ENUM.APPROVED" label="已通过(待仓库出库)" />
            <!-- 2=总经理驳回 -->
            <el-option :value="STATUS_ENUM.REJECTED" label="总经理已驳回" />
          </el-select>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="loadTable">查询</el-button>
          <el-button @click="resetFilters">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- ===== 操作区 ===== -->
    <el-row class="mb-2">
      <el-col :span="12">
        <el-button-group>
          <el-button
            type="success"
            :disabled="selectedRows.length === 0"
            @click="openApproveDialog('APPROVE')"
          >
            批量通过
          </el-button>
          <el-button
            type="danger"
            :disabled="selectedRows.length === 0"
            @click="openApproveDialog('REJECT')"
          >
            批量驳回
          </el-button>
        </el-button-group>
        <span style="margin-left: 12px; color: #999;">
          已选 {{ selectedRows.length }} 条申请
        </span>
      </el-col>
    </el-row>

    <!-- ===== 申请单列表（可展开查看明细） ===== -->
    <el-table
      :data="tableData"
      border
      stripe
      height="60vh"
      @selection-change="handleSelectionChange"
      row-key="applyId"
    >
      <!-- 多选 -->
      <el-table-column type="selection" width="50" />

      <!-- 展开明细 -->
      <el-table-column type="expand">
        <template #default="{ row }">
          <el-table
            v-if="row.detailLoaded"
            :data="row.details"
            border
            stripe
            size="small"
          >
            <el-table-column prop="shoeRId" label="工厂型号" width="140" />
            <el-table-column prop="customerProductName" label="客户鞋号" />
            <el-table-column prop="colorName" label="颜色" width="80" />
            <el-table-column prop="batchName" label="配码名称" width="120" />
            <el-table-column prop="packagingInfoName" label="包装方案" width="120" />
            <el-table-column prop="currentStock" label="当前库存(双)" width="120" />
            <el-table-column prop="pairsPerCarton" label="每箱双数" width="100" />
            <el-table-column prop="cartonCount" label="申请箱数" width="100" />
            <el-table-column prop="totalPairs" label="申请双数" width="100" />
            <el-table-column prop="remark" label="明细备注" min-width="150" />
          </el-table>

          <!-- 首次展开时异步加载 -->
          <div v-else style="padding: 12px;">
            <el-button type="primary" size="small" @click="loadDetail(row)">
              加载明细
            </el-button>
          </div>
        </template>
      </el-table-column>

      <el-table-column prop="applyRId" label="申请单号" width="180" />
      <el-table-column prop="createTime" label="申请时间" width="170" />
      <el-table-column prop="orderRId" label="订单号" width="140" />
      <el-table-column prop="orderCId" label="客户订单号" width="140" />
      <el-table-column prop="customerName" label="客户名称" min-width="140" />
      <el-table-column prop="customerBrand" label="客户商标" min-width="120" />
      <el-table-column prop="totalPairs" label="申请总双数" width="120" />

      <el-table-column label="状态" width="150">
        <template #default="{ row }">
          <el-tag v-if="row.status === STATUS_ENUM.PENDING" type="warning">
            {{ row.statusLabel }}
          </el-tag>
          <el-tag v-else-if="row.status === STATUS_ENUM.APPROVED" type="success">
            {{ row.statusLabel }}
          </el-tag>
          <el-tag v-else-if="row.status === STATUS_ENUM.REJECTED" type="danger">
            {{ row.statusLabel }}
          </el-tag>
          <el-tag v-else>
            {{ row.statusLabel || '未知' }}
          </el-tag>
        </template>
      </el-table-column>

      <el-table-column
        prop="remark"
        label="备注(含总经理审核记录)"
        min-width="220"
        show-overflow-tooltip
      />
    </el-table>

    <!-- ===== 分页 ===== -->
    <el-row class="mt-2">
      <el-col>
        <el-pagination
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
          :current-page="currentPage"
          :page-sizes="pageSizes"
          :page-size="pageSize"
          layout="total, sizes, prev, pager, next, jumper"
          :total="total"
        />
      </el-col>
    </el-row>

    <!-- ===== 审批对话框 ===== -->
    <el-dialog
      v-model="approveDialogVisible"
      :title="approveAction === 'APPROVE' ? '批量通过出库申请' : '批量驳回出库申请'"
      width="480px"
    >
      <p style="margin-bottom: 10px;">
        即将对 <strong>{{ selectedRows.length }}</strong> 条申请进行
        <strong>{{ approveAction === 'APPROVE' ? '通过' : '驳回' }}</strong> 操作。
      </p>

      <p
        style="margin-bottom: 10px; color: #f56c6c;"
        v-if="invalidSelectedCount > 0"
      >
        其中有 {{ invalidSelectedCount }} 条申请当前状态不为“待总经理审核”，将被自动忽略。
      </p>

      <el-form :model="approveForm" label-width="80px">
        <el-form-item label="审核意见">
          <el-input
            v-model="approveForm.remark"
            type="textarea"
            :rows="3"
            placeholder="选填：审核意见"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <span>
          <el-button @click="approveDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitApprove">确认</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import axios from 'axios'
import { ElMessage } from 'element-plus'

export default {
  name: 'FinishedOutboundApplyGM',
  data() {
    // 先定义本地常量，再作为 data 返回，方便默认值引用
    const STATUS_ENUM = {
      // 后端约定：
      // 0 草稿, 1 待总经理审核, 2 总经理驳回, 3 待仓库出库, 4 已完成出库
      PENDING: 1,
      APPROVED: 3,
      REJECTED: 2
    }

    return {
      STATUS_ENUM,

      // 默认：只看“待总经理审核”的出库申请
      filters: {
        customerName: '',
        orderRId: '',
        applyRId: '',
        status: STATUS_ENUM.PENDING
      },

      currentPage: 1,
      pageSize: 20,
      pageSizes: [10, 20, 50, 100],
      total: 0,

      tableData: [],
      selectedRows: [],

      approveDialogVisible: false,
      approveAction: 'APPROVE', // 或 'REJECT'
      approveForm: {
        remark: ''
      },

      invalidSelectedCount: 0
    }
  },
  mounted() {
    this.loadTable()
  },
  methods: {
    resetFilters() {
      // 重置回“默认视图”：只看待审核
      this.filters.customerName = ''
      this.filters.orderRId = ''
      this.filters.applyRId = ''
      this.filters.status = this.STATUS_ENUM.PENDING
      this.currentPage = 1
      this.loadTable()
    },

    async loadTable() {
      const params = {
        page: this.currentPage,
        pageSize: this.pageSize,
        customerName: this.filters.customerName || undefined,
        orderRId: this.filters.orderRId || undefined,
        applyRId: this.filters.applyRId || undefined,
        // status 为 null 时后端应视为“全部”；为 1/2/3 时则按对应状态过滤
        status: this.filters.status
      }

      const res = await axios.get(
        `${this.$apiBaseUrl}/warehouse/outbound-apply/list`,
        { params }
      )
      this.tableData = (res.data.result || []).map((item) => ({
        ...item,
        detailLoaded: false,
        details: []
      }))
      this.total = res.data.total || 0
      this.selectedRows = []
    },

    handleSizeChange(size) {
      this.pageSize = size
      this.currentPage = 1
      this.loadTable()
    },
    handlePageChange(page) {
      this.currentPage = page
      this.loadTable()
    },
    handleSelectionChange(selection) {
      this.selectedRows = selection
    },

    async loadDetail(row) {
      if (!row || !row.applyId) return
      const params = { applyId: row.applyId }
      const res = await axios.get(
        `${this.$apiBaseUrl}/warehouse/outbound-apply/detail`,
        { params }
      )
      row.details = res.data.details || []
      row.detailLoaded = true
    },

    openApproveDialog(action) {
      if (!this.selectedRows.length) {
        ElMessage.error('请先勾选需要审批的申请单')
        return
      }
      const pendingRows = this.selectedRows.filter(
        (r) => r.status === this.STATUS_ENUM.PENDING
      )
      this.invalidSelectedCount = this.selectedRows.length - pendingRows.length
      if (!pendingRows.length) {
        ElMessage.error('所选申请单中没有处于“待总经理审核”的记录')
        return
      }
      this.approveAction = action
      this.approveForm.remark = ''
      this.approveDialogVisible = true
    },

    async submitApprove() {
      const pendingRows = this.selectedRows.filter(
        (r) => r.status === this.STATUS_ENUM.PENDING
      )
      if (!pendingRows.length) {
        ElMessage.error('没有可操作的申请单')
        return
      }

      const action = this.approveAction === 'APPROVE' ? 'approve' : 'reject'
      const remark = this.approveForm.remark

      try {
        await Promise.all(
          pendingRows.map((row) =>
            axios.post(`${this.$apiBaseUrl}/warehouse/outbound-apply/audit`, {
              applyId: row.applyId,
              action,
              remark
            })
          )
        )
        ElMessage.success('审批操作已完成')
        this.approveDialogVisible = false
        this.loadTable()
      } catch (e) {
        console.error(e)
        const msg = e.response?.data?.message || '审批失败'
        ElMessage.error(msg)
      }
    }
  }
}
</script>

<style scoped>
.page {
  background: #f8f8f8;
}
.mb-2 {
  margin-bottom: 8px;
}
.mb-3 {
  margin-bottom: 12px;
}
.mt-2 {
  margin-top: 8px;
}
</style>
