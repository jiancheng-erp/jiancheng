<template>
  <div class="color-card-confirmation">
    <div class="toolbar">
      <div class="toolbar-left">
        <el-input
          v-model="keyword"
          size="small"
          placeholder="搜索订单号/客户/鞋型"
          clearable
          class="toolbar-search"
          @keyup.enter="handleSearch"
          @clear="handleSearch"
        />
        <el-select v-model="statusFilter" size="small" class="toolbar-select" @change="handleStatusChange">
          <el-option v-for="item in statusOptions" :key="item.value" :label="item.label" :value="item.value" />
        </el-select>
        <el-button type="primary" size="small" @click="handleSearch">搜索</el-button>
      </div>
      <div class="toolbar-right">
        <el-button
          type="success"
          size="small"
          :loading="batchLoading"
          :disabled="pendingSelectedCount === 0"
          @click="handleBatchConfirm"
        >
          批量确认
        </el-button>
        <el-button size="small" :loading="loading" @click="fetchOrders">刷新</el-button>
      </div>
    </div>

    <el-table
      ref="tableRef"
      :data="tableData"
      border
      stripe
      v-loading="loading"
      @selection-change="handleSelectionChange"
    >
      <el-table-column type="selection" width="48" :selectable="isRowSelectable" />
      <el-table-column prop="orderRid" label="订单号" min-width="150" />
      <el-table-column prop="customerName" label="客户" min-width="140" />
      <el-table-column label="鞋型" min-width="160">
        <template #default="{ row }">
          <span>{{ formatShoes(row) }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="createTime" label="开始日期" min-width="120" />
      <el-table-column prop="deadlineTime" label="交期" min-width="120" />
      <el-table-column label="色卡状态" min-width="120">
        <template #default="{ row }">
          <el-tag :type="row.colorCardStatus === '1' ? 'success' : 'warning'">
            {{ statusText(row.colorCardStatus) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" min-width="150" fixed="right">
        <template #default="{ row }">
          <el-button type="primary" size="small" :disabled="row.colorCardStatus === '1'" @click="handleConfirm(row)">
            确认色卡
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="pagination-wrapper">
      <el-pagination
        background
        layout="total, sizes, prev, pager, next, jumper"
        :total="total"
        :current-page="currentPage"
        :page-size="pageSize"
        :page-sizes="pageSizeOptions"
        @current-change="handleCurrentChange"
        @size-change="handleSizeChange"
      />
    </div>
  </div>
</template>

<script setup>
import { computed, getCurrentInstance, nextTick, onMounted, ref } from 'vue'
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'

const statusOptions = [
  { label: '全部', value: 'all' },
  { label: '待确认', value: '0' },
  { label: '已确认', value: '1' },
]

const statusFilter = ref('all')
const tableData = ref([])
const loading = ref(false)
const batchLoading = ref(false)
const keyword = ref('')
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)
const pageSizeOptions = [10, 20, 30, 50]
const tableRef = ref()
const selectedRows = ref([])

const proxy = getCurrentInstance()
const apiBaseUrl = proxy.appContext.config.globalProperties.$apiBaseUrl

const statusText = (value) => (value === '1' ? '已确认' : '待确认')
const formatShoes = (row) => (row.shoeRids && row.shoeRids.length ? row.shoeRids.join(' / ') : '-')
const isRowSelectable = (row) => row.colorCardStatus !== '1'
const pendingSelectedIds = computed(() =>
  selectedRows.value.filter((row) => row.colorCardStatus !== '1').map((row) => row.orderId),
)
const pendingSelectedCount = computed(() => pendingSelectedIds.value.length)

const clearSelection = () => {
  selectedRows.value = []
  if (tableRef.value) {
    tableRef.value.clearSelection()
  }
}

const fetchOrders = () => {
  loading.value = true
  const params = {
    page: currentPage.value,
    pageSize: pageSize.value,
  }
  if (statusFilter.value !== 'all') {
    params.status = statusFilter.value
  }
  if (keyword.value.trim()) {
    params.keyword = keyword.value.trim()
  }
  axios
    .get(`${apiBaseUrl}/order/colorcard/orders`, { params })
    .then(({ data }) => {
      tableData.value = data.orders || []
      total.value = typeof data.total === 'number' ? data.total : 0
      if (typeof data.pageSize === 'number') {
        pageSize.value = data.pageSize
      }
      if (typeof data.page === 'number') {
        currentPage.value = data.page
      }
      nextTick(() => {
        clearSelection()
      })
    })
    .catch((error) => {
      const message = error.response?.data?.message || '获取色卡信息失败'
      ElMessage.error(message)
    })
    .finally(() => {
      loading.value = false
    })
}

const handleConfirm = (row) => {
  if (row.colorCardStatus === '1') {
    return
  }
  ElMessageBox.confirm(`确认订单 ${row.orderRid} 的色卡状态？`, '提示', {
    confirmButtonText: '确认',
    cancelButtonText: '取消',
    type: 'warning',
  })
    .then(() =>
      axios.post(`${apiBaseUrl}/order/colorcard/confirm`, {
        orderId: row.orderId,
      }),
    )
    .then(({ data }) => {
      ElMessage.success(data.message || '已完成色卡确认')
      fetchOrders()
    })
    .catch((error) => {
      if (error === 'cancel' || error === 'close') {
        return
      }
      const message = error.response?.data?.message || '色卡确认失败'
      ElMessage.error(message)
    })
}

const handleBatchConfirm = () => {
  if (pendingSelectedIds.value.length === 0) {
    ElMessage.warning('请选择待确认的订单')
    return
  }
  ElMessageBox.confirm(`确认批量更新 ${pendingSelectedIds.value.length} 个订单的色卡状态？`, '提示', {
    confirmButtonText: '确认',
    cancelButtonText: '取消',
    type: 'warning',
  })
    .then(() => {
      batchLoading.value = true
      return axios.post(`${apiBaseUrl}/order/colorcard/batch-confirm`, {
        orderIds: pendingSelectedIds.value,
      })
    })
    .then(({ data }) => {
      ElMessage.success(data.message || '批量确认完成')
      fetchOrders()
    })
    .catch((error) => {
      if (error === 'cancel' || error === 'close') {
        return
      }
      const message = error.response?.data?.message || '批量确认失败'
      ElMessage.error(message)
    })
    .finally(() => {
      batchLoading.value = false
    })
}

const handleSelectionChange = (selection) => {
  selectedRows.value = selection
}

const handleSearch = () => {
  currentPage.value = 1
  fetchOrders()
}

const handleStatusChange = () => {
  currentPage.value = 1
  fetchOrders()
}

const handleSizeChange = (value) => {
  pageSize.value = value
  currentPage.value = 1
  fetchOrders()
}

const handleCurrentChange = (value) => {
  currentPage.value = value
  fetchOrders()
}

onMounted(fetchOrders)
</script>

<style scoped>
.color-card-confirmation {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.toolbar-left,
.toolbar-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.toolbar-select {
  width: 160px;
}

.toolbar-search {
  width: 220px;
}

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
}
</style>
