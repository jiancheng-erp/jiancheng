<template>
  <el-row :gutter="20">
    <el-col class="u-page-title" :span="24">历史订单</el-col>
  </el-row>

  <!-- 简洁工具栏：筛选维度与刷新 -->
  <el-row :gutter="10" style="margin-top: 16px">
    <el-col :span="6">
      <el-select class="u-w-180" v-model="filterStatus" placeholder="筛选维度" size="default" @change="reload">
        <el-option label="经理审核视图" :value="'0'" />
        <el-option label="业务创建视图" :value="'1'" />
      </el-select>
      <el-button type="primary" :loading="loading" @click="reload" style="margin-left: 8px">刷新</el-button>
    </el-col>
  </el-row>

  <!-- 轻量筛选区：纯前端过滤 -->
  <el-row :gutter="10" style="margin-top: 12px">
    <el-col :span="4"><el-input v-model="orderRidFilter" placeholder="订单号筛选" clearable @input="applyFilters" /></el-col>
    <el-col :span="4"><el-input v-model="orderCidFilter" placeholder="客户订单号筛选" clearable @input="applyFilters" /></el-col>
    <el-col :span="4"><el-input v-model="orderCustomerNameFilter" placeholder="客户名称筛选" clearable @input="applyFilters" /></el-col>
    <el-col :span="4"><el-input v-model="orderCustomerBrandFilter" placeholder="客户商标筛选" clearable @input="applyFilters" /></el-col>
    <el-col :span="4"><el-input v-model="customerProductNameFilter" placeholder="客户型号筛选" clearable @input="applyFilters" /></el-col>
    <el-col :span="4"><el-input v-model="shoeRIdSearch" placeholder="工厂型号筛选" clearable @input="applyFilters" /></el-col>
  </el-row>

  <el-row :gutter="10" style="margin-top: 10px">
    <el-col :span="8">
      <el-date-picker
        v-model="orderStartDateFilter"
        type="daterange"
        unlink-panels
        range-separator="至"
        start-placeholder="开始日期 起"
        end-placeholder="开始日期 止"
        :shortcuts="shortcuts"
        size="default"
        @change="applyFilters"
      />
    </el-col>
    <el-col :span="8">
      <el-date-picker
        v-model="orderEndDateFilter"
        type="daterange"
        unlink-panels
        range-separator="至"
        start-placeholder="结束日期 起"
        end-placeholder="结束日期 止"
        :shortcuts="shortcuts"
        size="default"
        @change="applyFilters"
      />
    </el-col>
  </el-row>

  <el-row :gutter="20">
    <el-col :span="24">
      <div class="selection-banner" :class="{ 'is-active': selectedSummaryRows.length }">
        <span class="selection-banner-text">
          已选 <strong>{{ selectedSummaryRows.length }}</strong> 单，合计总双数：<strong class="pairs">{{ selectedTotalPairs }}</strong>
        </span>
        <el-button type="success" size="default" :loading="exportingSummary"
          :disabled="!selectedSummaryRows.length" @click="exportSelectionSummary">
          导出汇总Excel
        </el-button>
      </div>
    </el-col>
  </el-row>

  <!-- 表格 -->
  <el-row :gutter="20" style="margin-top: 12px">
    <el-table ref="historyTable" :data="paginatedDisplayData" border stripe height="calc(100vh - var(--main-table-offset))" :loading="loading" row-key="orderDbId" @row-dblclick="orderRowDbClick" @selection-change="handleSelectionChange">
      <el-table-column type="selection" width="55" reserve-selection />
      <el-table-column prop="orderRid" label="订单号" sortable />
      <el-table-column prop="orderTotalPairs" label="总双数" width="100" sortable />
      <el-table-column prop="orderSalesman" label="创建业务员" />
      <el-table-column prop="orderSupervisor" label="审核" />
      <el-table-column prop="orderCid" label="客户订单号" />
      <el-table-column prop="customerName" label="客户名" />
      <el-table-column prop="customerBrand" label="客户商标" />
      <el-table-column prop="customerProductName" label="客户型号" />
      <el-table-column prop="shoeRId" label="工厂型号" />
      <el-table-column prop="orderStartDate" label="订单开始日期" sortable />
      <el-table-column prop="orderEndDate" label="订单结束日期" sortable />
      <el-table-column prop="orderStatus" label="订单状态" />
      <el-table-column label="操作" width="200">
        <template #default="scope">
          <el-button type="primary" size="default" @click="openOrderDetail(scope.row.orderDbId)">查看订单详情</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination class="u-mt-5"
      :current-page="currentPage"
      :page-size="pageSize"
      :total="totalItems"
      @current-change="handlePageChange"
      layout="total,prev,pager,next,jumper"
     
    />
  </el-row>
</template>

<script>
import axios from 'axios'
import { ElMessage } from 'element-plus'

export default {
  name: 'OrderHistory',
  data() {
    return {
      // 加载 & 角色
      loading: false,
      userRole: '', // '4' 经理 / '21' 文员（字符串存储，便于比较）
      staffId: localStorage.getItem('staffid'),

      // 维度切换（经理按主管/按业务；文员随意）
      filterStatus: '0',

      // 数据与分页
      allData: [],
      displayData: [],
      currentPage: 1,
      pageSize: 20,

      // 勾选汇总
      selectedSummaryRows: [],
      exportingSummary: false,

      // 轻量筛选
      orderRidFilter: '',
      orderCidFilter: '',
      orderCustomerNameFilter: '',
      orderCustomerBrandFilter: '',
      customerProductNameFilter: '',
      shoeRIdSearch: '',
      orderStartDateFilter: '',
      orderEndDateFilter: '',

      shortcuts: [
        {
          text: '过去一周',
          value: () => {
            const end = new Date()
            const start = new Date()
            start.setTime(start.getTime() - 3600 * 1000 * 24 * 7)
            return [start, end]
          }
        },
        {
          text: '过去一月',
          value: () => {
            const end = new Date()
            const start = new Date()
            start.setTime(start.getTime() - 3600 * 1000 * 24 * 30)
            return [start, end]
          }
        }
      ]
    }
  },
  computed: {
    totalItems() {
      return this.displayData.length
    },
    paginatedDisplayData() {
      const start = (this.currentPage - 1) * this.pageSize
      return this.displayData.slice(start, start + this.pageSize)
    },
    selectedTotalPairs() {
      return this.selectedSummaryRows.reduce((sum, row) => sum + (Number(row?.orderTotalPairs) || 0), 0)
    }
  },
  mounted() {
    this.fetchUserRole().then(this.reload)
  },
  methods: {
    async fetchUserRole() {
      try {
        const res = await axios.get(`${this.$apiBaseUrl}/order/onmount`)
        this.userRole = String(res.data.role || '')
      } catch (e) {
        console.warn('fetch user role failed', e)
        this.userRole = String(localStorage.getItem('role') || '')
      }
    },
    async reload() {
      this.currentPage = 1
      await this.getHistoryOrders()
      this.$refs.historyTable?.clearSelection()
      this.selectedSummaryRows = []
      this.applyFilters()
    },

    // —— 获取历史订单（按你“角色分流”的写法）——
    async getHistoryOrders() {
      this.loading = true
      try {
        let response
        if (this.userRole === '21') {
          // 文员：按用户维度接口 + 历史标记
          response = await axios.get(`${this.$apiBaseUrl}/order/getbusinessdisplayorderbyuser`, {
            params: {
              currentStaffId: this.staffId,
              historyStatus: 1,
              filterStatus: this.filterStatus ?? '0'
            }
          })
        } else if (this.userRole === '4') {
          // 经理：统一走相同接口，便于使用 filterStatus（更稳妥）
          response = await axios.get(`${this.$apiBaseUrl}/order/getbusinessdisplayorderbyuser`, {
            params: {
              currentStaffId: this.staffId,
              historyStatus: 1,
              filterStatus: this.filterStatus ?? '0'
            }
          })
          // 若你坚持走 /order/getallorders，可切换为下面写法（确保后端支持 historyStatus）：
          // response = await axios.get(`${this.$apiBaseUrl}/order/getallorders`, { params: { historyStatus: 1 } })
        } else {
          // 其他角色：退化为同一接口
          response = await axios.get(`${this.$apiBaseUrl}/order/getbusinessdisplayorderbyuser`, {
            params: {
              currentStaffId: this.staffId,
              historyStatus: 1,
              filterStatus: this.filterStatus ?? '0'
            }
          })
        }

        this.allData = Array.isArray(response?.data) ? response.data : []
        this.displayData = this.allData
      } catch (e) {
        console.error(e)
        ElMessage.error('获取历史订单失败')
        this.allData = []
        this.displayData = []
      } finally {
        this.loading = false
      }
    },

    applyFilters() {
      let data = [...this.allData]
      const textIncludes = (a, b) => (a || '').toString().toLowerCase().includes((b || '').toString().toLowerCase())

      if (this.orderRidFilter) data = data.filter(d => textIncludes(d.orderRid, this.orderRidFilter))
      if (this.orderCidFilter) data = data.filter(d => textIncludes(d.orderCid, this.orderCidFilter))
      if (this.orderCustomerNameFilter) data = data.filter(d => textIncludes(d.customerName, this.orderCustomerNameFilter))
      if (this.orderCustomerBrandFilter) data = data.filter(d => textIncludes(d.customerBrand, this.orderCustomerBrandFilter))
      if (this.customerProductNameFilter) data = data.filter(d => textIncludes(d.customerProductName, this.customerProductNameFilter))
      if (this.shoeRIdSearch) data = data.filter(d => textIncludes(d.shoeRId, this.shoeRIdSearch))

      if (this.orderStartDateFilter && this.orderStartDateFilter.length === 2) {
        const [s, e] = this.orderStartDateFilter
        const sTs = new Date(s).getTime(), eTs = new Date(e).getTime()
        data = data.filter(d => {
          const t = new Date(d.orderStartDate).getTime()
          return !isNaN(t) && t >= sTs && t <= eTs
        })
      }

      if (this.orderEndDateFilter && this.orderEndDateFilter.length === 2) {
        const [s, e] = this.orderEndDateFilter
        const sTs = new Date(s).getTime(), eTs = new Date(e).getTime()
        data = data.filter(d => {
          const t = new Date(d.orderEndDate).getTime()
          return !isNaN(t) && t >= sTs && t <= eTs
        })
      }

      this.displayData = data
      this.currentPage = 1
    },

    handlePageChange(p) {
      this.currentPage = p
    },

    handleSelectionChange(selection) {
      this.selectedSummaryRows = selection || []
    },

    async exportSelectionSummary() {
      const orderShoeIds = this.selectedSummaryRows
        .map((row) => row.orderShoeId)
        .filter((id) => id !== undefined && id !== null)
      if (!orderShoeIds.length) {
        ElMessage.warning('请先勾选订单')
        return
      }
      this.exportingSummary = true
      try {
        const response = await axios.post(
          `${this.$apiBaseUrl}/order/exportselectionsummary`,
          { orderShoeIds },
          { responseType: 'blob' }
        )
        const blob = new Blob([response.data], {
          type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        })
        const disposition = response.headers['content-disposition'] || ''
        let filename = '订单汇总.xlsx'
        // 优先匹配 filename*=（UTF-8 完整文件名），ASCII 回退的 filename= 会丢失中文
        const utf8Match = disposition.match(/filename\*=UTF-8''([^"';]+)/i)
        const asciiMatch = disposition.match(/filename=["']?([^"';]+)["']?/i)
        const match = utf8Match || asciiMatch
        if (match && match[1]) {
          filename = decodeURIComponent(match[1])
        }
        const url = window.URL.createObjectURL(blob)
        const link = document.createElement('a')
        link.href = url
        link.download = filename
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        window.URL.revokeObjectURL(url)
      } catch (error) {
        console.error('exportSelectionSummary failed', error)
        ElMessage.error('导出汇总Excel失败')
      } finally {
        this.exportingSummary = false
      }
    },

    orderRowDbClick(row) {
      this.openOrderDetail(row.orderDbId)
    },

    openOrderDetail(orderId) {
      // 与原页面保持一致的跳转规则
      let url = ''
      if (this.userRole === '4') {
        url = `${window.location.origin}/business/businessorderdetail/orderid=${orderId}/admin`
      } else if (this.userRole === '21') {
        url = `${window.location.origin}/business/businessorderdetail/orderid=${orderId}/clerk`
      } else if (this.userRole === '27') {
        url = `${window.location.origin}/business/businessorderdetail/orderid=${orderId}/assistant`
      } else {
        url = `${window.location.origin}/business/businessorderdetail/orderid=${orderId}`
      }
      window.open(url, '_blank')
    }
  }
}
</script>

<style scoped>
.selection-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin: 8px 0 12px;
  padding: 10px 16px;
  border-radius: 6px;
  background-color: #f4f4f5;
  border: 1px dashed var(--el-border-color);
  color: var(--color-text-3);
  transition: all 0.2s ease;
}

.selection-banner.is-active {
  background-color: var(--el-color-primary-light-9);
  border: 1px solid #b3d8ff;
  color: var(--color-text-1);
}

.selection-banner-text {
  font-size: 15px;
}

.selection-banner-text .pairs {
  color: var(--el-color-primary);
  font-size: 20px;
  margin: 0 2px;
}
</style>
