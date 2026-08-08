<template>
  <div class="order-summary">
    <el-form :inline="true" class="filter-bar">
      <el-form-item label="订单时间">
        <el-date-picker
          v-model="startDateRange"
          type="daterange"
          value-format="YYYY-MM-DD"
          range-separator="~"
          start-placeholder="开始"
          end-placeholder="结束"
          style="width: 240px"
        />
      </el-form-item>
      <el-form-item label="订单交货期">
        <el-date-picker
          v-model="endDateRange"
          type="daterange"
          value-format="YYYY-MM-DD"
          range-separator="~"
          start-placeholder="开始"
          end-placeholder="结束"
          style="width: 240px"
        />
      </el-form-item>
      <el-form-item label="客户">
        <el-input v-model="filters.customerName" placeholder="客户名称" clearable style="width: 150px" />
      </el-form-item>
      <el-form-item label="部门">
        <el-select v-model="filters.departmentId" placeholder="全部" clearable style="width: 140px">
          <el-option v-for="d in departments" :key="d.value" :label="d.label" :value="d.value" />
        </el-select>
      </el-form-item>
      <el-form-item label="编号">
        <el-input v-model="filters.orderRId" placeholder="订单编号" clearable style="width: 150px" />
      </el-form-item>
      <el-form-item label="客人型号">
        <el-input v-model="filters.customerProductName" placeholder="客人型号" clearable style="width: 140px" />
      </el-form-item>
      <el-form-item label="工厂型号">
        <el-input v-model="filters.shoeRId" placeholder="工厂型号" clearable style="width: 140px" />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="onSearch">查询</el-button>
        <el-button @click="resetFilters">重置</el-button>
        <el-button type="success" :loading="exporting" @click="exportExcel">导出Excel</el-button>
      </el-form-item>
    </el-form>

    <el-table :data="tableData" border stripe size="small" style="width: 100%">
      <el-table-column type="index" label="序号" width="70" :index="indexMethod" align="center" />
      <el-table-column prop="startDate" label="订单时间" width="120" align="center" />
      <el-table-column prop="orderRId" label="编号" width="130" />
      <el-table-column prop="customerName" label="客户" min-width="130" />
      <el-table-column prop="departmentName" label="部门" width="110" />
      <el-table-column prop="totalPairs" label="数量（双）" width="110" align="center" />
      <el-table-column label="金额" width="130" align="right">
        <template #default="{ row }">
          {{ row.amount != null ? formatAmount(row.amount) : '' }}
        </template>
      </el-table-column>
      <el-table-column prop="currency" label="币种" width="80" align="center" />
      <el-table-column prop="endDate" label="订单交货期" width="120" align="center" />
      <el-table-column prop="customerProductName" label="客人型号" min-width="120" />
      <el-table-column prop="shoeRId" label="工厂型号" min-width="130" />
    </el-table>

    <el-pagination
      class="pagination"
      background
      layout="total, prev, pager, next, sizes"
      :total="total"
      :page-size="pageSize"
      :current-page="currentPage"
      :page-sizes="[20, 50, 100, 200]"
      @current-change="handlePageChange"
      @size-change="handleSizeChange"
    />
  </div>
</template>

<script>
import axios from 'axios'
import { ElMessage } from 'element-plus'

export default {
  name: 'OrderSummary',
  data() {
    return {
      filters: {
        customerName: '',
        departmentId: null,
        orderRId: '',
        customerProductName: '',
        shoeRId: ''
      },
      startDateRange: null,
      endDateRange: null,
      departments: [],
      tableData: [],
      total: 0,
      currentPage: 1,
      pageSize: 20,
      exporting: false
    }
  },
  mounted() {
    this.loadDepartments()
    this.loadTable()
  },
  methods: {
    indexMethod(index) {
      return (this.currentPage - 1) * this.pageSize + index + 1
    },
    formatAmount(v) {
      return Number(v).toLocaleString('zh-CN', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
      })
    },
    buildParams() {
      return {
        startDateFrom: this.startDateRange?.[0] || undefined,
        startDateTo: this.startDateRange?.[1] || undefined,
        endDateFrom: this.endDateRange?.[0] || undefined,
        endDateTo: this.endDateRange?.[1] || undefined,
        customerName: this.filters.customerName || undefined,
        departmentId: this.filters.departmentId || undefined,
        orderRId: this.filters.orderRId || undefined,
        customerProductName: this.filters.customerProductName || undefined,
        shoeRId: this.filters.shoeRId || undefined
      }
    },
    async loadDepartments() {
      try {
        const res = await axios.get(`${this.$apiBaseUrl}/general/getbusinessdepartments`)
        this.departments = res.data || []
      } catch (e) {
        console.error(e)
      }
    },
    async loadTable() {
      try {
        const res = await axios.get(`${this.$apiBaseUrl}/headmanager/ordersummary/list`, {
          params: { ...this.buildParams(), page: this.currentPage, pageSize: this.pageSize }
        })
        this.tableData = res.data.result || []
        this.total = res.data.total || 0
      } catch (e) {
        console.error(e)
        ElMessage.error(e.response?.data?.message || '获取订单汇总失败')
      }
    },
    onSearch() {
      this.currentPage = 1
      this.loadTable()
    },
    resetFilters() {
      this.filters = {
        customerName: '',
        departmentId: null,
        orderRId: '',
        customerProductName: '',
        shoeRId: ''
      }
      this.startDateRange = null
      this.endDateRange = null
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
    async exportExcel() {
      this.exporting = true
      try {
        const res = await axios.get(`${this.$apiBaseUrl}/headmanager/ordersummary/export`, {
          params: this.buildParams(),
          responseType: 'blob'
        })
        const url = window.URL.createObjectURL(res.data)
        const link = document.createElement('a')
        link.href = url
        link.download = `订单汇总_${Date.now()}.xlsx`
        link.click()
        window.URL.revokeObjectURL(url)
      } catch (e) {
        console.error(e)
        ElMessage.error('导出失败')
      } finally {
        this.exporting = false
      }
    }
  }
}
</script>

<style scoped>
.filter-bar {
  margin-bottom: 8px;
}
.pagination {
  margin-top: 12px;
  justify-content: flex-end;
}
</style>
