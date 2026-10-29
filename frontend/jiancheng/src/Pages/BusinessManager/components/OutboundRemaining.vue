<template>
  <el-row :gutter="20">
    <el-col class="u-page-title" :span="24">出库剩余明细</el-col>
  </el-row>

  <el-row :gutter="10" style="margin-top: 16px">
    <el-col :span="10">
      <el-select class="u-w-180" v-model="filterStatus" placeholder="筛选维度" size="default" @change="loadOrders">
        <el-option label="经理审核视图" value="0" />
        <el-option label="业务创建视图" value="1" />
      </el-select>
      <el-radio-group v-model="statusFilter" size="default" style="margin-left: 8px" @change="applyFilters">
        <el-radio-button label="部分出库" value="partial" />
        <el-radio-button label="全部进行中订单" value="all" />
      </el-radio-group>
      <el-button type="primary" :loading="loading" style="margin-left: 8px" @click="loadOrders">刷新</el-button>
    </el-col>
    <el-col :span="4"><el-input v-model="orderRidFilter" placeholder="订单号筛选" clearable @input="applyFilters" /></el-col>
    <el-col :span="4"><el-input v-model="shoeRIdFilter" placeholder="工厂型号筛选" clearable @input="applyFilters" /></el-col>
    <el-col :span="4"><el-input v-model="customerFilter" placeholder="客户名称筛选" clearable @input="applyFilters" /></el-col>
  </el-row>

  <el-row :gutter="20" style="margin-top: 12px">
    <el-table :data="paginatedData" border stripe v-loading="loading" height="calc(100vh - var(--main-table-offset))"
      @row-dblclick="(row) => openDetail(row)">
      <el-table-column prop="orderRid" label="订单号" sortable />
      <el-table-column prop="orderTotalPairs" label="总双数" width="100" sortable />
      <el-table-column prop="customerName" label="客户名" />
      <el-table-column prop="customerProductName" label="客户型号" />
      <el-table-column prop="shoeRId" label="工厂型号" />
      <el-table-column prop="orderEndDate" label="订单结束日期" sortable />
      <el-table-column label="生产状态" min-width="170">
        <template #default="scope">
          <el-tag v-if="scope.row.productionStatus" :type="statusTagType(scope.row.productionStatus)"
            :class="{ 'clickable-tag': scope.row.productionStatus.startsWith('部分出库') }"
            @click="scope.row.productionStatus.startsWith('部分出库') && openDetail(scope.row)">{{ scope.row.productionStatus }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="160">
        <template #default="scope">
          <el-button type="primary" @click="openDetail(scope.row)">查看剩余明细</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-pagination class="u-mt-5" :current-page="currentPage" :page-size="pageSize" :total="filteredData.length"
      layout="total,prev,pager,next,jumper" @current-change="(p) => (currentPage = p)" />
  </el-row>

  <OutboundRemainingDialog v-model="dialogVisible" :order-id="currentOrderId" />
</template>

<script>
import axios from 'axios'
import { ElMessage } from 'element-plus'
import OutboundRemainingDialog from './OutboundRemainingDialog.vue'

export default {
  name: 'OutboundRemaining',
  components: { OutboundRemainingDialog },
  data() {
    return {
      loading: false,
      filterStatus: '0',
      statusFilter: 'partial',
      allData: [],
      filteredData: [],
      currentPage: 1,
      pageSize: 20,
      orderRidFilter: '',
      shoeRIdFilter: '',
      customerFilter: '',
      dialogVisible: false,
      currentOrderId: null
    }
  },
  computed: {
    paginatedData() {
      const start = (this.currentPage - 1) * this.pageSize
      return this.filteredData.slice(start, start + this.pageSize)
    }
  },
  mounted() {
    this.loadOrders()
  },
  methods: {
    async loadOrders() {
      this.loading = true
      try {
        const res = await axios.get(`${this.$apiBaseUrl}/order/getbusinessdisplayorderbyuser`, {
          params: { currentStaffId: localStorage.getItem('staffid'), filterStatus: this.filterStatus }
        })
        this.allData = Array.isArray(res.data) ? res.data : []
      } catch (e) {
        console.error(e)
        ElMessage.error('获取订单失败')
        this.allData = []
      } finally {
        this.loading = false
      }
      this.applyFilters()
    },
    applyFilters() {
      const includes = (a, b) => (a || '').toString().toLowerCase().includes((b || '').toString().toLowerCase())
      this.filteredData = this.allData.filter((d) => {
        if (this.statusFilter === 'partial' && !(d.productionStatus || '').startsWith('部分出库')) return false
        return (
          includes(d.orderRid, this.orderRidFilter) &&
          includes(d.shoeRId, this.shoeRIdFilter) &&
          includes(d.customerName, this.customerFilter)
        )
      })
      this.currentPage = 1
    },
    statusTagType(status) {
      if (status.startsWith('部分出库')) return 'warning'
      if (status.startsWith('已全部出库')) return 'success'
      return 'info'
    },
    openDetail(row) {
      this.currentOrderId = row.orderDbId
      this.dialogVisible = true
    }
  }
}
</script>

<style scoped>
.clickable-tag {
  cursor: pointer;
}
</style>
