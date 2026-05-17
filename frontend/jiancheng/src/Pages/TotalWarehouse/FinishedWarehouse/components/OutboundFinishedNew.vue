<template>
  <div class="page p-4">
    <!-- ===== 筛选区 ===== -->
    <el-card shadow="never" class="mb-3">
      <el-form :inline="true" :model="filters" @keyup.enter="loadTable">
        <el-form-item label="申请日期">
          <el-date-picker
            v-model="filters.dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
            unlink-panels
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
            placeholder="出库申请单号"
            clearable
          />
        </el-form-item>

        <el-form-item label="客户名称">
          <el-input
            v-model="filters.customerName"
            placeholder="客户名称"
            clearable
          />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="loadTable">查询</el-button>
          <el-button @click="resetFilters">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- ===== 操作区 ===== -->
    <el-row class="mb-2" :gutter="12" align="middle">
      <el-col :span="14">
        <el-radio-group v-model="listStatus" @change="loadTable" size="small">
          <el-radio-button :label="3">待出库</el-radio-button>
          <el-radio-button :label="4">已完成</el-radio-button>
          <el-radio-button :label="-1">全部</el-radio-button>
        </el-radio-group>
        <el-radio-group v-model="listApplyType" @change="loadTable" size="small" style="margin-left:16px;">
          <el-radio-button :label="null">全部类型</el-radio-button>
          <el-radio-button :label="0">业务申请</el-radio-button>
          <el-radio-button :label="1">仓库直发</el-radio-button>
        </el-radio-group>
      </el-col>
    </el-row>

    <!-- ===== 申请单列表 ===== -->
    <el-table
      :data="tableData"
      border
      stripe
      height="60vh"
      row-key="applyId"
    >
      <el-table-column label="明细" width="80" fixed="left">
        <template #default="{ row }">
          <el-button type="primary" link size="small" @click="openPackingListDialog(row)">查看</el-button>
        </template>
      </el-table-column>

      <el-table-column prop="applyRId" label="申请单号" width="180" />
      <el-table-column prop="orderRId" label="订单号" width="140" />
      <el-table-column prop="orderCId" label="客户订单号" width="160" />
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
      <el-table-column prop="pendingPairs" label="待出库双数" width="120" />
      <el-table-column prop="actualPairs" label="已出库双数" width="120" />
      <el-table-column label="发起方" width="100">
        <template #default="{ row }">
          <el-tag v-if="row.applyType === 1" type="warning" size="small">仓库直发</el-tag>
          <el-tag v-else size="small">业务申请</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="statusLabel" label="状态" width="140" />
      <el-table-column prop="remark" label="业务备注" min-width="180" show-overflow-tooltip />
      <el-table-column prop="createTime" label="创建时间" width="180" />
      <el-table-column prop="updateTime" label="更新时间" width="180" />

      <el-table-column label="操作" width="180" fixed="right">
        <template #default="{ row }">
          <el-button
            v-if="row.status === STATUS_ENUM.PENDING_WAREHOUSE"
            type="primary"
            size="small"
            @click="openExecuteDialog(row)"
          >
            确认出库
          </el-button>
        </template>
      </el-table-column>
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

    <!-- ===== PACKING LIST 明细对话框 ===== -->
    <el-dialog
      v-model="packingListDialogVisible"
      :title="`出库申请明细 - ${packingListRow?.applyRId || ''}`"
      width="92%"
    >
      <el-descriptions :column="4" border size="small" style="margin-bottom: 12px">
        <el-descriptions-item label="订单号">{{ packingListRow?.allOrderRIds || packingListRow?.orderRId }}</el-descriptions-item>
        <el-descriptions-item label="客户订单号">{{ packingListRow?.allOrderCIds || packingListRow?.orderCId }}</el-descriptions-item>
        <el-descriptions-item label="客户名称">{{ packingListRow?.allCustomerNames || packingListRow?.customerName }}</el-descriptions-item>
        <el-descriptions-item label="客户商标">{{ packingListRow?.customerBrand }}</el-descriptions-item>
      </el-descriptions>

      <el-table
        v-loading="packingListLoading"
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
        <el-table-column label="SIZE" align="center" v-if="packingListSizeColumns.length > 0">
          <el-table-column
            v-for="col in packingListSizeColumns"
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
        @size-change="(s) => { packingListPageSize = s; packingListCurrentPage = 1 }"
        @current-change="(p) => { packingListCurrentPage = p }"
        :current-page="packingListCurrentPage"
        :page-sizes="[10, 20, 30, 50, 100]"
        :page-size="packingListPageSize"
        layout="total, sizes, prev, pager, next"
        :total="packingListDataAll.length"
      />

      <template #footer>
        <el-button type="primary" @click="exportPackingList">导出Excel</el-button>
        <el-button @click="packingListDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- ===== 仓库确认出库对话框 ===== -->
    <el-dialog
      v-model="executeDialogVisible"
      :title="`确认出库 - 申请单 ${currentExecuteRow?.applyRId || ''}`"
      width="90%"
    >
      <el-form :model="executeForm" label-width="80px">
        <el-form-item label="实际出库日期">
          <el-date-picker
            v-model="executeForm.actualOutboundDate"
            type="date"
            placeholder="默认为当天"
            value-format="YYYY-MM-DD"
            clearable
          />
        </el-form-item>
        <el-form-item label="拣货人">
          <el-input v-model="executeForm.picker" placeholder="必填：拣货人姓名" />
        </el-form-item>
        <el-form-item label="出库备注">
          <el-input
            v-model="executeForm.remark"
            type="textarea"
            :rows="3"
            placeholder="选填：仓库出库备注"
          />
        </el-form-item>
      </el-form>

      <!-- 快速选择工具栏 -->
      <div v-if="executeDetails.length" style="display:flex; align-items:center; gap:12px; margin-bottom:8px; flex-wrap:wrap;">
        <el-button size="small" @click="selectAll">全选已入库</el-button>
        <el-button size="small" @click="deselectAll">取消全选</el-button>
        <span style="color:#666; font-size:13px;">按鞋型选择：</span>
        <el-select
          v-model="executeFilterShoeRId"
          placeholder="全部鞋型"
          clearable
          size="small"
          style="width:180px;"
          @change="onExecuteShoeFilter"
        >
          <el-option
            v-for="rid in executeShoeRIdOptions"
            :key="rid"
            :label="rid"
            :value="rid"
          />
        </el-select>
        <el-button size="small" @click="selectFilteredShoeRId">选中该鞋型</el-button>
      </div>

      <!-- 已选鞋型汇总 -->
      <div v-if="selectedShoeRIdSummary.length" style="margin-bottom:8px; display:flex; align-items:center; gap:6px; flex-wrap:wrap;">
        <span style="color:#409eff; font-size:13px; font-weight:500;">已选鞋型：</span>
        <el-tag
          v-for="item in selectedShoeRIdSummary"
          :key="item.shoeRId"
          size="small"
          closable
          style="margin-right:4px;"
          @close="deselectShoeRId(item.shoeRId)"
        >
          {{ item.shoeRId }}（{{ item.count }}条）
        </el-tag>
        <span style="color:#999; font-size:12px; margin-left:4px;">
          共 {{ selectedShoeRIdSummary.reduce((s, i) => s + i.count, 0) }} 条明细
        </span>
      </div>

      <el-table
        v-if="executeDetails.length"
        :data="executeDetailsPaged"
        border
        stripe
        size="small"
        class="mb-2"
        max-height="320px"
      >
        <el-table-column label="选择" width="60" align="center">
          <template #default="{ row }">
            <el-checkbox v-model="row._selected" :disabled="!canSelectExecuteDetail(row)" @change="recalcExecuteSummary" />
          </template>
        </el-table-column>
        <el-table-column prop="customerName" label="客户名称" width="120" />
        <el-table-column prop="shoeRId" label="工厂型号" width="140" />
        <el-table-column prop="customerProductName" label="客户鞋号" />
        <el-table-column prop="colorName" label="颜色" width="80" />
        <el-table-column prop="batchName" label="配码名称" width="120" />
        <el-table-column prop="packagingInfoName" label="包装方案" width="120" />
        <el-table-column prop="currentStock" label="当前库存(双)" width="120" />
        <el-table-column label="入库状态" width="120">
          <template #default="{ row }">
            <el-tag :type="!row.inboundFinished ? 'warning' : (Number(row.currentStock) <= 0 ? 'info' : 'success')">
              {{ !row.inboundFinished ? '未完成入库' : (Number(row.currentStock) <= 0 ? '库存为0' : '可出库') }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="cartonCount" label="预计箱数" width="100" />
        <el-table-column prop="totalPairs" label="预计出库(双)" width="120" />
        <el-table-column label="实际箱数" width="160">
          <template #default="{ row }">
            <el-input-number
              v-model="row.actualCartonCount"
              :min="0"
              :precision="2"
              controls-position="right"
              style="width: 120px"
              @change="onCartonChange(row)"
            />
          </template>
        </el-table-column>
        <el-table-column label="实际出库(双)" width="160">
          <template #default="{ row }">
            <el-input-number
              v-model="row.actualPairs"
              :min="0"
              :precision="0"
              controls-position="right"
              style="width: 120px"
              @change="onPairsChange(row)"
            />
          </template>
        </el-table-column>
        <el-table-column label="差异(双)" width="120">
          <template #default="{ row }">
            <span :style="{ color: row._diff ? '#e6a23c' : '#67c23a' }">
              {{ row._diff || 0 }}
            </span>
          </template>
        </el-table-column>
      </el-table>
      <!-- 出库明细分页 -->
      <el-pagination
        v-if="executeDetails.length > executePageSize"
        :current-page="executeCurrentPage"
        :page-size="executePageSize"
        :page-sizes="[20, 50, 100]"
        :total="executeDetails.length"
        layout="total, sizes, prev, pager, next"
        size="small"
        style="margin-top:6px;"
        @current-change="(p) => executeCurrentPage = p"
        @size-change="(s) => { executePageSize = s; executeCurrentPage = 1 }"
      />
      <div v-if="executeDetails.length" class="execute-summary">
        外部待出库：{{ executeTotalAllPending }} 双；可确认出库：{{ executeTotalExpected }} 双；实际合计：{{ executeTotalActual }} 双；差异：{{ executeTotalActual - executeTotalExpected }} 双
      </div>

      <!-- <p style="margin-top: 8px; color:#999;">
        出库时请按每个配码填写实际出库箱数，系统自动按每箱双数换算并对比预计数量。
        <br />1）校验库存是否足够；
        <br />2）生成 <strong>shoe_outbound_record</strong> 及明细；
        <br />3）扣减成品库存，并把申请单状态更新为「已完成出库」。
      </p> -->

      <template #footer>
        <div class="dialog-totals" v-if="executeDetails.length">
          <span>已选明细：<b>{{ executeTotalSelectedRows }}</b> 行</span>
          <span>合计出库箱数：<b>{{ executeTotalActualCartons }}</b> 箱</span>
          <span>合计出库双数：<b>{{ executeTotalActual }}</b> 双</span>
          <span>预计双数：<b>{{ executeTotalExpected }}</b> 双</span>
          <span>差异：<b :style="{ color: (executeTotalActual - executeTotalExpected) === 0 ? '#67c23a' : '#e6a23c' }">{{ executeTotalActual - executeTotalExpected }}</b> 双</span>
        </div>
        <span>
          <el-button @click="executeDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitExecute">确认出库</el-button>
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
  name: 'FinishedWarehouseOutbound',
  data() {
    return {
      STATUS_ENUM: {
        DRAFT: 0,
        PENDING_GM: 1,
        GM_REJECTED: 2,
        PENDING_WAREHOUSE: 3,
        FINISHED: 4,
        VOID: 5
      },

      filters: {
        dateRange: [],
        orderRId: '',
        applyRId: '',
        customerName: ''
      },

      currentPage: 1,
      pageSize: 20,
      pageSizes: [10, 20, 50, 100],
      total: 0,

      tableData: [],

      listStatus: 3, // 3=待出库(默认), 4=已完成, -1=全部
      listApplyType: null, // null=全部, 0=业务申请, 1=仓库直发

      // PACKING LIST 明细对话框
      packingListDialogVisible: false,
      packingListRow: null,
      packingListLoading: false,
      packingListSizeColumns: [],
      packingListCurrentPage: 1,
      packingListPageSize: 20,

      // 仓库执行出库
      executeDialogVisible: false,
      currentExecuteRow: null,
      executeForm: {
        picker: '',
        remark: '',
        actualOutboundDate: ''
      },
      executeDetails: [],
      executeTotalAllPending: 0,
      executeTotalExpected: 0,
      executeTotalActual: 0,
      executeTotalActualCartons: 0,
      executeTotalSelectedRows: 0,
      executeFilterShoeRId: '',
      executeCurrentPage: 1,
      executePageSize: 20
    }
  },
  computed: {
    // PACKING LIST 数据（带起止箱号）
    packingListDataAll() {
      const details = this.packingListRow?.details || []
      if (!details.length) return []
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
        return { ...d, cNoStart, cNoEnd: cumulative, cartonCount: cartons }
      })
    },
    packingListPageData() {
      const start = (this.packingListCurrentPage - 1) * this.packingListPageSize
      return this.packingListDataAll.slice(start, start + this.packingListPageSize)
    },
    executeShoeRIdOptions() {
      const set = new Set(this.executeDetails.map((d) => d.shoeRId).filter(Boolean))
      return [...set].sort()
    },
    executeDetailsPaged() {
      const start = (this.executeCurrentPage - 1) * this.executePageSize
      return this.executeDetails.slice(start, start + this.executePageSize)
    },
    selectedShoeRIdSummary() {
      const map = {}
      this.executeDetails.forEach((d) => {
        if (d._selected && d.shoeRId) {
          if (!map[d.shoeRId]) map[d.shoeRId] = 0
          map[d.shoeRId]++
        }
      })
      return Object.keys(map).sort().map((k) => ({ shoeRId: k, count: map[k] }))
    }
  },
  mounted() {
    this.loadTable()
  },
  methods: {
    resetFilters() {
      this.filters = {
        dateRange: [],
        orderRId: '',
        applyRId: '',
        customerName: ''
      }
      this.currentPage = 1
      this.loadTable()
    },

    async loadTable() {
      const params = {
        page: this.currentPage,
        pageSize: this.pageSize,
        orderRId: this.filters.orderRId || undefined,
        applyRId: this.filters.applyRId || undefined,
        customerName: this.filters.customerName || undefined,
        startDate: this.filters.dateRange?.[0] || undefined,
        endDate: this.filters.dateRange?.[1] || undefined
      }
      if (this.listStatus != null && this.listStatus >= 0) {
        params.status = this.listStatus
      }
      if (this.listApplyType != null) {
        params.applyType = this.listApplyType
      }
      const res = await axios.get(`${this.$apiBaseUrl}/warehouse/outbound-apply/list`, { params })
      this.tableData = (res.data.result || []).map((item) => ({
        ...item,
        detailLoaded: false,
        details: []
      }))
      this.total = res.data.total || 0
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

    async loadDetail(row) {
      if (!row || !row.applyId) return
      const res = await axios.get(`${this.$apiBaseUrl}/warehouse/outbound-apply/detail`, {
        params: { applyId: row.applyId }
      })
      const { details, header, sizeColumns } = res.data || {}
      row.details = (details || []).map((item) => ({
        ...item,
        inboundFinished: Number(item.finishedStatus) >= 1
      }))
      row.detailLoaded = true
      // 补充多订单/客户信息
      const h = header || {}
      row.allOrderRIds = h.allOrderRIds || row.allOrderRIds || row.orderRId
      row.allOrderCIds = h.allOrderCIds || row.allOrderCIds || row.orderCId
      row.allCustomerNames = h.allCustomerNames || row.allCustomerNames || row.customerName
      row.customerBrand = row.customerBrand || h.customerBrand
      row._sizeColumns = sizeColumns || []
      return row.details
    },

    // 打开 PACKING LIST 明细对话框
    async openPackingListDialog(row) {
      if (!row) return
      this.packingListRow = row
      this.packingListDialogVisible = true
      this.packingListCurrentPage = 1
      if (row.detailLoaded) {
        this.packingListSizeColumns = row._sizeColumns || []
        return
      }
      this.packingListLoading = true
      try {
        await this.loadDetail(row)
        this.packingListSizeColumns = row._sizeColumns || []
      } catch (e) {
        console.error(e)
        ElMessage.error(e.response?.data?.message || '加载明细失败')
      } finally {
        this.packingListLoading = false
      }
    },

    getPackingListSummary({ columns }) {
      const allData = this.packingListDataAll
      const sums = []
      columns.forEach((col, index) => {
        if (index === 0) {
          sums[index] = '合计'
          return
        }
        if (col.property === 'cartonCount' || col.property === 'totalPairs') {
          sums[index] = allData.reduce((sum, row) => sum + (Number(row[col.property]) || 0), 0)
        } else {
          sums[index] = ''
        }
      })
      return sums
    },

    exportPackingList() {
      const row = this.packingListRow
      if (!row) return
      const allData = this.packingListDataAll
      const sizeCols = this.packingListSizeColumns
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

    // 打开执行出库对话框
    async openExecuteDialog(row) {
      if (!row) return
      this.currentExecuteRow = row
      const details = row.detailLoaded ? row.details : await this.loadDetail(row)
      if (!details || !details.length) {
        ElMessage.error('该申请单没有明细，无法出库')
        return
      }
      // 仅展示“本申请仍待出库”的明细（按申请明细 totalPairs 判断）。
      const pendingDetails = details.filter((item) => Number(item.totalPairs) > 0)
      if (!pendingDetails.length) {
        ElMessage.info('该申请单所有明细均已出库完成')
        return
      }
      const noStockDetails = pendingDetails.filter((item) => Number(item.currentStock) <= 0)
      if (noStockDetails.length) {
        ElMessage.warning(`有 ${noStockDetails.length} 条明细库存为0，已自动禁用`) 
      }
      const notInboundFinished = pendingDetails.filter((item) => !item.inboundFinished)
      if (notInboundFinished.length) {
        const hint = notInboundFinished
          .slice(0, 3)
          .map((item) => {
            const shoe = item.shoeRId || ''
            const color = item.colorName ? `-${item.colorName}` : ''
            return `${shoe}${color}` || '未知明细'
          })
          .join(', ')
        ElMessage.warning(
          hint
            ? `部分明细尚未完成入库（${hint}），已自动禁用，可对已入库明细进行出库`
            : '部分明细尚未完成入库，已自动禁用'
        )
      }
      this.executeDetails = pendingDetails.map((item) => ({
        ...item,
        actualCartonCount: Number(item.cartonCount) || 0,
        actualPairs: (Number(item.cartonCount) || 0) * (Number(item.pairsPerCarton) || 0),
        _diff: 0,
        _selected: !!item.inboundFinished && Number(item.currentStock) > 0
      }))
      this.executeFilterShoeRId = ''
      this.executeCurrentPage = 1
      this.recalcExecuteSummary()
      this.executeForm = {
        picker: '',
        remark: '',
        actualOutboundDate: ''
      }
      this.executeDialogVisible = true
    },

    // 提交执行出库
    async submitExecute() {
      if (!this.currentExecuteRow || !this.currentExecuteRow.applyId) {
        ElMessage.error('缺少申请单信息，无法出库')
        return
      }
      if (!this.executeDetails.length) {
        ElMessage.error('请先加载并填写实际出库明细')
        return
      }
      if (!this.executeForm.picker) {
        ElMessage.error('请填写拣货人')
        return
      }
      const selectedUnfinishedDetail = this.executeDetails.find(
        (item) => item._selected && !item.inboundFinished
      )
      if (selectedUnfinishedDetail) {
        ElMessage.error('勾选明细中仍有未完成入库项，暂无法出库')
        return
      }

      const detailPayload = this.executeDetails
        .filter((item) => item._selected && Number(item.actualCartonCount) > 0)
        .map((item) => ({
          applyDetailId: item.applyDetailId,
          actualCartonCount: Number(item.actualCartonCount)
        }))
      
      if (!detailPayload.length) {
        ElMessage.error('请至少勾选一行明细并填写实际出库箱数')
        return
      }

      const invalidDetail = detailPayload.find(
        (d) => Number.isNaN(d.actualCartonCount) || d.actualCartonCount < 0
      )
      if (invalidDetail) {
        ElMessage.error('请填写合法的实际出库箱数（需为非负数）')
        return
      }
      const overExpected = this.executeDetails.find(
        (item) => (Number(item.actualCartonCount) > 0) && ((Number(item.actualPairs) || 0) > (Number(item.totalPairs) || 0))
      )
      if (overExpected) {
        ElMessage.error('实际出库数量不能大于预计出库数量，请调整后再提交')
        return
      }

      const payload = {
        applyId: this.currentExecuteRow.applyId,
        picker: this.executeForm.picker,
        remark: this.executeForm.remark,
        actualOutboundDate: this.executeForm.actualOutboundDate || undefined,
        details: detailPayload
      }

      try {
        const res = await axios.post(
          `${this.$apiBaseUrl}/warehouse/outbound-apply/execute`,
          payload
        )
        const data = res.data || {}
        // data 里已经包含 outboundRecordId / outboundRId / status 等
        ElMessage.success(
          data.message ||
            `出库成功，生成出库单号：${data.outboundRId || ''}`
        )
        this.executeDialogVisible = false
        this.executeDetails = []
        this.loadTable()
      } catch (e) {
        console.error(e)
        const msg =
          e.response?.data?.message || e.response?.data?.error || '出库失败'
        ElMessage.error(msg)
      }
    },

    selectAll() {
      this.executeDetails.forEach((item) => {
        if (this.canSelectExecuteDetail(item)) item._selected = true
      })
      this.recalcExecuteSummary()
    },
    deselectAll() {
      this.executeDetails.forEach((item) => {
        item._selected = false
      })
      this.recalcExecuteSummary()
    },
    onExecuteShoeFilter() {
      // 仅用于联动「选中该鞋型」按钮，不自动勾选
    },
    selectFilteredShoeRId() {
      if (!this.executeFilterShoeRId) return
      this.executeDetails.forEach((item) => {
        if (item.shoeRId === this.executeFilterShoeRId && this.canSelectExecuteDetail(item)) {
          item._selected = true
        }
      })
      this.recalcExecuteSummary()
    },
    canSelectExecuteDetail(item) {
      return !!item?.inboundFinished && Number(item?.currentStock) > 0
    },
    deselectShoeRId(shoeRId) {
      this.executeDetails.forEach((item) => {
        if (item.shoeRId === shoeRId) {
          item._selected = false
        }
      })
      this.recalcExecuteSummary()
    },
    onCartonChange(row) {
      const pairsPerCarton = Number(row.pairsPerCarton) || 0
      const maxPairs = Number(row.totalPairs) || 0
      let carton = Number(row.actualCartonCount) || 0
      if (pairsPerCarton > 0 && carton * pairsPerCarton > maxPairs) {
        carton = maxPairs / pairsPerCarton
        row.actualCartonCount = Math.round(carton * 100) / 100
      }
      row.actualPairs = Math.round(carton * pairsPerCarton)
      this.recalcExecuteSummary()
    },
    onPairsChange(row) {
      const pairsPerCarton = Number(row.pairsPerCarton) || 0
      const maxPairs = Number(row.totalPairs) || 0
      let pairs = Number(row.actualPairs) || 0
      if (pairs > maxPairs) {
        pairs = maxPairs
        row.actualPairs = pairs
      }
      row.actualCartonCount = pairsPerCarton > 0 ? Math.round((pairs / pairsPerCarton) * 100) / 100 : 0
      this.recalcExecuteSummary()
    },
    recalcExecuteSummary() {
      let allPending = 0
      let expected = 0
      let actual = 0
      let actualCartons = 0
      let selectedRows = 0
      this.executeDetails.forEach((item) => {
        const exp = Number(item.totalPairs) || 0
        const act = Number(item.actualPairs) || 0
        const actC = Number(item.actualCartonCount) || 0
        item._diff = act - exp
        allPending += exp
        if (this.canSelectExecuteDetail(item)) {
          expected += exp
        }
        actual += act
        if (item._selected && actC > 0) {
          actualCartons += actC
          selectedRows += 1
        }
      })
      this.executeTotalAllPending = allPending
      this.executeTotalExpected = expected
      this.executeTotalActual = actual
      this.executeTotalActualCartons = Number(actualCartons.toFixed(2))
      this.executeTotalSelectedRows = selectedRows
    }
  }
}
</script>

<style scoped>
.page {
  background: #f8f8f8;
}
.dialog-totals {
  display: flex;
  flex-wrap: wrap;
  gap: 24px;
  padding: 8px 12px;
  margin-bottom: 8px;
  background: #f5f7fa;
  border-radius: 4px;
  font-size: 13px;
  color: #606266;
  text-align: left;
  justify-content: flex-start;
}
.dialog-totals b {
  color: #409eff;
  margin: 0 2px;
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
.execute-summary {
  margin: 6px 0 12px;
  color: #666;
}
</style>
