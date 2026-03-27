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

    <!-- ===== 申请单列表 ===== -->
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

      <el-table-column label="明细" width="90" fixed="left">
        <template #default="{ row }">
          <el-button type="primary" link @click="openDetailDialog(row)">
            查看
          </el-button>
        </template>
      </el-table-column>

      <el-table-column prop="applyRId" label="申请单号" width="180" />
      <el-table-column prop="createTime" label="申请时间" width="170" />
      <el-table-column prop="orderRId" label="订单号" width="140" />
      <el-table-column prop="orderCId" label="客户订单号" width="140" />
      <el-table-column label="客户名称" min-width="160">
        <template #default="{ row }">
          <span>{{ row.customerName }}</span>
          <el-tooltip v-if="row.allCustomerNames && row.allCustomerNames !== row.customerName" placement="top" :teleported="false">
            <template #content>
              <div>涉及客户：{{ row.allCustomerNames }}</div>
              <div v-if="row.allOrderRIds">涉及订单：{{ row.allOrderRIds }}</div>
              <div v-if="row.allShoeRIds">涉及鞋型：{{ row.allShoeRIds }}</div>
            </template>
            <el-tag size="small" type="warning" style="margin-left:4px">多客户</el-tag>
          </el-tooltip>
        </template>
      </el-table-column>
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

    <!-- ===== 明细对话框（PACKING LIST 格式） ===== -->
    <el-dialog
      v-model="detailDialogVisible"
      :title="`出库申请明细 - ${currentDetailRow?.applyRId || ''}`"
      width="92%"
    >
      <el-descriptions :column="4" border size="small" style="margin-bottom: 12px">
        <el-descriptions-item label="订单号">{{ currentDetailRow?.allOrderRIds || currentDetailRow?.orderRId }}</el-descriptions-item>
        <el-descriptions-item label="客户订单号">{{ currentDetailRow?.allOrderCIds || currentDetailRow?.orderCId }}</el-descriptions-item>
        <el-descriptions-item label="客户名称">{{ currentDetailRow?.allCustomerNames || currentDetailRow?.customerName }}</el-descriptions-item>
        <el-descriptions-item label="客户商标">{{ currentDetailRow?.customerBrand }}</el-descriptions-item>
      </el-descriptions>

      <el-table
        v-loading="detailLoading"
        :data="packingListPageData"
        border
        stripe
        size="small"
        show-summary
        :summary-method="getPackingListSummary"
      >
        <el-table-column label="起始箱号" prop="cNoStart" width="90" align="center" />
        <el-table-column label="截止箱号" prop="cNoEnd" width="90" align="center" />
        <el-table-column label="PO.NO. (工厂型号)" prop="shoeRId" min-width="130" />
        <el-table-column label="STYLE# (客户型号)" prop="customerProductName" min-width="140" />
        <el-table-column label="COLOR" prop="colorName" width="100" />
        <el-table-column label="配码名称" prop="batchName" min-width="110" />
        <el-table-column label="SIZE" align="center" v-if="detailSizeColumns.length > 0">
          <el-table-column
            v-for="col in detailSizeColumns"
            :key="col.label"
            :label="col.label"
            width="55"
            align="center"
          >
            <template #default="{ row }">{{ row.sizeRatios?.[col.label] || '' }}</template>
          </el-table-column>
        </el-table-column>
        <el-table-column label="PRS/Ctn" prop="pairsPerCarton" width="90" align="center" />
        <el-table-column label="CTNS" prop="cartonCount" width="80" align="center" />
        <el-table-column label="Units(prs)" prop="totalPairs" width="100" align="center" />
      </el-table>

      <el-pagination
        style="margin-top: 10px"
        @size-change="handleDetailSizeChange"
        @current-change="handleDetailPageChange"
        :current-page="detailCurrentPage"
        :page-sizes="[10, 20, 30, 50, 100]"
        :page-size="detailPageSize"
        layout="total, sizes, prev, pager, next"
        :total="packingListData.length"
      />

      <template #footer>
        <span>
          <el-button type="primary" @click="exportPackingList">导出Excel</el-button>
          <el-button @click="detailDialogVisible = false">关闭</el-button>
        </span>
      </template>
    </el-dialog>

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
import * as XLSX from 'xlsx'

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

      detailDialogVisible: false,
      currentDetailRow: null,
      detailLoading: false,
      detailSizeColumns: [],
      detailCurrentPage: 1,
      detailPageSize: 20,

      approveDialogVisible: false,
      approveAction: 'APPROVE', // 或 'REJECT'
      approveForm: {
        remark: ''
      },

      invalidSelectedCount: 0
    }
  },
  computed: {
    packingListData() {
      const details = this.currentDetailRow?.details || []
      if (!details.length) return []
      // 按客户型号分组累计箱号，不同客户型号重新从1开始，小数向上取整
      let cumulative = 0
      let prevStyle = null
      return details.map((d) => {
        const style = d.customerProductName || ''
        if (style !== prevStyle) {
          cumulative = 0
          prevStyle = style
        }
        const cartons = Math.ceil(Number(d.cartonCount || 0))
        const cNoStart = cumulative + 1
        cumulative += cartons
        const cNoEnd = cumulative
        return { ...d, cNoStart, cNoEnd, cartonCount: cartons }
      })
    },
    packingListPageData() {
      const start = (this.detailCurrentPage - 1) * this.detailPageSize
      return this.packingListData.slice(start, start + this.detailPageSize)
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
      // 从 header 补充订单信息到 row（供对话框表头显示）
      const h = res.data.header || {}
      row.orderRId = row.orderRId || h.orderRId
      row.orderCId = row.orderCId || h.orderCId
      row.customerBrand = row.customerBrand || h.customerBrand
      row.allOrderRIds = h.allOrderRIds || row.allOrderRIds || row.orderRId
      row.allOrderCIds = h.allOrderCIds || row.allOrderCIds || row.orderCId
      row.allCustomerNames = h.allCustomerNames || row.allCustomerNames || row.customerName
      // 保存尺码列定义
      this.detailSizeColumns = res.data.sizeColumns || []
    },

    async openDetailDialog(row) {
      if (!row) return
      this.currentDetailRow = row
      this.detailDialogVisible = true
      this.detailCurrentPage = 1
      if (row.detailLoaded) return
      this.detailLoading = true
      try {
        await this.loadDetail(row)
      } catch (e) {
        console.error(e)
        ElMessage.error(e.response?.data?.message || '加载明细失败')
      } finally {
        this.detailLoading = false
      }
    },

    getPackingListSummary({ columns }) {
      // 合计行基于全部数据（而非当前页）
      const allData = this.packingListData
      const sums = []
      columns.forEach((col, index) => {
        if (index === 0) {
          sums[index] = '合计'
          return
        }
        if (col.property === 'cartonCount' || col.property === 'totalPairs') {
          sums[index] = allData.reduce(
            (sum, row) => sum + (Number(row[col.property]) || 0),
            0
          )
        } else {
          sums[index] = ''
        }
      })
      return sums
    },

    exportPackingList() {
      const row = this.currentDetailRow
      if (!row) return
      const allData = this.packingListData
      const sizeCols = this.detailSizeColumns
      const title = row.applyRId || '出库明细'
      const headerRows = [
        [`出库申请明细 - ${title}`],
        ['订单号', row.allOrderRIds || row.orderRId || '', '', '客户订单号', row.allOrderCIds || row.orderCId || ''],
        ['客户名称', row.allCustomerNames || row.customerName || '', '', '客户商标', row.customerBrand || ''],
        []
      ]
      const colHeaders = ['起始箱号', '截止箱号', 'PO.NO. (工厂型号)', 'STYLE# (客户型号)', 'COLOR', '配码名称']
      sizeCols.forEach(c => colHeaders.push(c.label))
      colHeaders.push('PRS/Ctn', 'CTNS', 'Units(prs)')
      headerRows.push(colHeaders)
      const dataRows = allData.map(d => {
        const r = [d.cNoStart, d.cNoEnd, d.shoeRId || '', d.customerProductName || '', d.colorName || '', d.batchName || '']
        sizeCols.forEach(c => r.push(d.sizeRatios?.[c.label] || ''))
        r.push(d.pairsPerCarton || '', d.cartonCount || '', d.totalPairs || '')
        return r
      })
      const sumCartons = allData.reduce((s, d) => s + (Number(d.cartonCount) || 0), 0)
      const sumPairs = allData.reduce((s, d) => s + (Number(d.totalPairs) || 0), 0)
      const sumRow = ['合计', '', '', '', '', '']
      sizeCols.forEach(() => sumRow.push(''))
      sumRow.push('', sumCartons, sumPairs)
      const wsData = [...headerRows, ...dataRows, sumRow]
      const ws = XLSX.utils.aoa_to_sheet(wsData)
      const wb = XLSX.utils.book_new()
      XLSX.utils.book_append_sheet(wb, ws, 'PACKING LIST')
      XLSX.writeFile(wb, `${title}.xlsx`)
    },

    handleDetailSizeChange(size) {
      this.detailPageSize = size
      this.detailCurrentPage = 1
    },
    handleDetailPageChange(page) {
      this.detailCurrentPage = page
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
