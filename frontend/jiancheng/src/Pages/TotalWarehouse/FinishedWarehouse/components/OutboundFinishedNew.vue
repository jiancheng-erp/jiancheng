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
    <el-row class="mb-2">
      <el-col :span="12">
        <span style="color:#999;">仅展示状态为「待仓库出库」的申请单</span>
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
      <el-table-column type="expand">
        <template #default="{ row }">
          <el-table
            v-if="row.detailLoaded"
            :data="row.details"
            border
            stripe
            size="small"
          >
            <el-table-column prop="orderRId" label="订单号" width="120" />
            <el-table-column prop="shoeRId" label="工厂型号" width="140" />
            <el-table-column prop="customerProductName" label="客户鞋号" />
            <el-table-column prop="colorName" label="颜色" width="80" />
            <el-table-column prop="batchName" label="配码名称" width="120" />
            <el-table-column prop="packagingInfoName" label="包装方案" width="120" />
            <el-table-column prop="currentStock" label="当前库存(双)" width="120" />
            <el-table-column label="入库状态" width="120">
              <template #default="{ row }">
                <el-tag :type="row.inboundFinished ? 'success' : 'warning'">
                  {{ row.inboundFinished ? '已完成入库' : '未完成入库' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="cartonCount" label="申请箱数" width="100" />
            <el-table-column prop="pairsPerCarton" label="每箱双数" width="100" />
            <el-table-column prop="totalPairs" label="申请双数" width="100" />
            <el-table-column prop="remark" label="业务备注" min-width="140" />
          </el-table>
          <div v-else style="padding:12px;">
            <el-button type="primary" size="small" @click="loadDetail(row)">
              加载明细
            </el-button>
          </div>
        </template>
      </el-table-column>

      <el-table-column prop="applyRId" label="申请单号" width="180" />
      <el-table-column prop="orderRId" label="订单号" width="140" />
      <el-table-column prop="orderCId" label="客户订单号" width="160" />
      <el-table-column prop="customerName" label="客户名称" min-width="140" />
      <el-table-column prop="customerBrand" label="客户商标" min-width="120" />
      <el-table-column prop="totalPairs" label="申请总双数" width="120" />
      <el-table-column prop="statusLabel" label="状态" width="140" />
      <el-table-column prop="remark" label="业务备注" min-width="180" show-overflow-tooltip />
      <el-table-column prop="createTime" label="创建时间" width="180" />
      <el-table-column prop="updateTime" label="更新时间" width="180" />

      <el-table-column label="操作" width="180" fixed="right">
        <template #default="{ row }">
          <el-button
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

    <!-- ===== 仓库确认出库对话框 ===== -->
    <el-dialog
      v-model="executeDialogVisible"
      :title="`确认出库 - 申请单 ${currentExecuteRow?.applyRId || ''}`"
      width="60%"
    >
      <el-form :model="executeForm" label-width="80px">
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

      <el-table
        v-if="executeDetails.length"
        :data="executeDetails"
        border
        stripe
        size="small"
        class="mb-2"
        max-height="320px"
      >
        <el-table-column prop="shoeRId" label="工厂型号" width="140" />
        <el-table-column prop="colorName" label="颜色" width="80" />
        <el-table-column prop="batchName" label="配码名称" width="120" />
        <el-table-column prop="packagingInfoName" label="包装方案" width="120" />
        <el-table-column prop="currentStock" label="当前库存(双)" width="120" />
        <el-table-column label="入库状态" width="120">
          <template #default="{ row }">
            <el-tag :type="row.inboundFinished ? 'success' : 'warning'">
              {{ row.inboundFinished ? '已完成入库' : '未完成入库' }}
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
              @change="recalcExecuteSummary"
            />
          </template>
        </el-table-column>
        <el-table-column label="实际出库(双)" width="120">
          <template #default="{ row }">
            {{ row.actualPairs || 0 }}
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
      <div v-if="executeDetails.length" class="execute-summary">
        预计合计：{{ executeTotalExpected }} 双；实际合计：{{ executeTotalActual }} 双；差异：{{ executeTotalActual - executeTotalExpected }} 双
      </div>

      <!-- <p style="margin-top: 8px; color:#999;">
        出库时请按每个配码填写实际出库箱数，系统自动按每箱双数换算并对比预计数量。
        <br />1）校验库存是否足够；
        <br />2）生成 <strong>shoe_outbound_record</strong> 及明细；
        <br />3）扣减成品库存，并把申请单状态更新为「已完成出库」。
      </p> -->

      <template #footer>
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

      // 仓库执行出库
      executeDialogVisible: false,
      currentExecuteRow: null,
      executeForm: {
        picker: '',
        remark: ''
      },
      executeDetails: [],
      executeTotalExpected: 0,
      executeTotalActual: 0
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
        status: this.STATUS_ENUM.PENDING_WAREHOUSE, // 只看待仓库出库
        startDate: this.filters.dateRange?.[0] || undefined,
        endDate: this.filters.dateRange?.[1] || undefined
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
      const { details } = res.data || {}
      row.details = (details || []).map((item) => ({
        ...item,
        inboundFinished: item.inboundFinished === 1 || item.finishedStatus === 1
      }))
      row.detailLoaded = true
      return row.details
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
      const notInboundFinished = details.filter((item) => !item.inboundFinished)
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
            ? `存在未完成入库的明细（${hint}），请入库完成后再出库`
            : '存在未完成入库的明细，请入库完成后再出库'
        )
        return
      }
      this.executeDetails = details.map((item) => ({
        ...item,
        actualCartonCount: Number(item.cartonCount) || 0,
        actualPairs: (Number(item.cartonCount) || 0) * (Number(item.pairsPerCarton) || 0),
        _diff: 0
      }))
      this.recalcExecuteSummary()
      this.executeForm = {
        picker: '',
        remark: ''
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
      const unfinishedDetail = this.executeDetails.find((item) => !item.inboundFinished)
      if (unfinishedDetail) {
        ElMessage.error('仍有未完成入库的明细，暂无法出库')
        return
      }

      const detailPayload = this.executeDetails.map((item) => ({
        applyDetailId: item.applyDetailId,
        actualCartonCount: Number(item.actualCartonCount)
      }))
      const invalidDetail = detailPayload.find(
        (d) => Number.isNaN(d.actualCartonCount) || d.actualCartonCount < 0
      )
      if (invalidDetail) {
        ElMessage.error('请填写合法的实际出库箱数（需为非负数）')
        return
      }
      const overExpected = this.executeDetails.find(
        (item) => (Number(item.actualPairs) || 0) > (Number(item.totalPairs) || 0)
      )
      if (overExpected) {
        ElMessage.error('实际出库数量不能大于预计出库数量，请调整后再提交')
        return
      }

      const payload = {
        applyId: this.currentExecuteRow.applyId,
        picker: this.executeForm.picker,
        remark: this.executeForm.remark,
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

    recalcExecuteSummary() {
      let expected = 0
      let actual = 0
      this.executeDetails.forEach((item) => {
        const exp = Number(item.totalPairs) || 0
        const carton = Number(item.actualCartonCount)
        const normalizedCarton = Number.isFinite(carton) ? carton : 0
        const pairsPerCarton = Number(item.pairsPerCarton) || 0
        const maxCarton =
          pairsPerCarton > 0 ? exp / pairsPerCarton : normalizedCarton
        const cappedCarton =
          pairsPerCarton > 0
            ? Math.min(normalizedCarton, maxCarton)
            : normalizedCarton
        item.actualCartonCount = cappedCarton
        const normalizedActual = cappedCarton * pairsPerCarton
        item.actualPairs = normalizedActual
        item._diff = normalizedActual - exp
        expected += exp
        actual += normalizedActual
      })
      this.executeTotalExpected = expected
      this.executeTotalActual = actual
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
.execute-summary {
  margin: 6px 0 12px;
  color: #666;
}
</style>
