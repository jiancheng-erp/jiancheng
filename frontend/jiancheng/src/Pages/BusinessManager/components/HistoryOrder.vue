<template>
  <el-row :gutter="20">
    <el-col :span="24" style="font-size: xx-large; text-align: center">历史订单</el-col>
  </el-row>

  <!-- 简洁工具栏：筛选维度与刷新 -->
  <el-row :gutter="10" style="margin-top: 16px">
    <el-col :span="6">
      <el-select v-model="filterStatus" placeholder="筛选维度" size="default" style="width: 180px" @change="reload">
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

  <!-- 表格 -->
  <el-row :gutter="20" style="margin-top: 12px">
    <el-table :data="paginatedDisplayData" border stripe height="500" :loading="loading" @row-dblclick="orderRowDbClick">
      <el-table-column prop="orderRid" label="订单号" sortable />
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

    <el-pagination
      :current-page="currentPage"
      :page-size="pageSize"
      :total="totalItems"
      @current-change="handlePageChange"
      layout="total,prev,pager,next,jumper"
      style="margin-top: 20px"
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
      } else {
        url = `${window.location.origin}/business/businessorderdetail/orderid=${orderId}`
      }
      window.open(url, '_blank')
    }
  }
}
</script>

<style scoped>
/* 可按需补充样式 */
</style>
