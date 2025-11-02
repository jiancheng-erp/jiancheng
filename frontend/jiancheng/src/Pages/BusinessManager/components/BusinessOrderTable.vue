<script setup>
import { ref, onMounted } from 'vue'
import { useOrderStore } from '@/stores/businessOrderStore'

const store = useOrderStore()

const orderStatusOption = ref([
    { label: '全部订单', value: 'all' },
  { label: '我审批的订单', value: 'to_approve' },
  { label: '我发起的订单', value: 'mine' }])
const selectedOrderStatus = ref(orderStatusOption.value[2])
// Filters
const shortcuts = [/* your date picker shortcuts */]

// onMounted(async () => {
//   // Fetch orders for current user
//   await store.fetchOrders({ currentStaffId: 123 })
// })

function handleInputChange(key, value) {
  store.setFilter(key, value)
}

function handlePageChange(page) {
  store.setPage(page)
}

function switchRadio(value) {
  store.setFilter('radio', value)
}

function switchScope(value) {
  store.fetchOrders({filterStatus:value})
}
</script>

<template>
  <el-row :gutter="10">
    <el-col :span="4">
        <el-select v-model="selectedOrderStatus" placeholder="请选择订单类型" size="default" @change="switchScope" style="width: 200px; width: 150px">
            <el-option v-for="item in orderStatusOption" :key="item.value" :label="item.label" :value="item.value" />
        </el-select>
    </el-col>
    <el-col :span="4">
      <el-input v-model="store.filters.orderRid" @input="handleInputChange('orderRid', $event)" placeholder="订单号筛选" clearable />
    </el-col>

    <el-col :span="4">
      <el-radio-group v-model="store.filters.radio" @change="switchRadio">
        <el-radio-button label="all">全部订单</el-radio-button>
        <el-radio-button label="已下发">已下发</el-radio-button>
        <el-radio-button label="未下发">未下发</el-radio-button>
      </el-radio-group>
    </el-col>

  </el-row>

  <el-table :data="store.paginatedOrders" border stripe >
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
            <el-button-group>
                <el-button type="primary" size="default" @click="openOrderDetail(scope.row.orderDbId)">查看订单详情</el-button>
                <!-- <el-button v-if="scope.row.orderStatusVal < 9 && this.userRole == 4" type="danger" size="default" @click="deleteOrder(scope.row)">删除订单</el-button> -->
            </el-button-group>
        </template>
    </el-table-column>
  </el-table>

  <el-pagination
    :current-page="store.currentPage"
    :page-size="store.pageSize"
    :total="store.filteredOrders.length"
    @current-change="handlePageChange"
  />
</template>