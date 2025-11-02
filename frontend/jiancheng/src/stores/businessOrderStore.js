import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from '@/utils/axios'

export const useOrderStore = defineStore('orderStore', () => {
  // Raw data fetched from API
  const allOrders = ref([])
  const displayOrders = ref([])
  // Filters
  const filters = ref({
    orderRid: '',
    orderCid: '',
    customerName: '',
    customerBrand: '',
    customerProductName: '',
    shoeRId: '',
    orderStatus: '',
    startDate: [],
    endDate: [],
    radio: 'all'
  })

  // Pagination
  const currentPage = ref(1)
  const pageSize = ref(20)

  // Computed filtered & paginated data
  const filteredOrders = computed(() => {

    let data = allOrders.value

    // Apply text filters
    if (filters.value.orderRid) {
      data = data.filter(o => o.orderRid.includes(filters.value.orderRid))
    }
    if (filters.value.orderCid) {
      data = data.filter(o => o.orderCid.includes(filters.value.orderCid))
    }
    if (filters.value.customerName) {
      data = data.filter(o => o.customerName.includes(filters.value.customerName))
    }
    if (filters.value.customerBrand) {
      data = data.filter(o => o.customerBrand.includes(filters.value.customerBrand))
    }
    if (filters.value.customerProductName) {
      data = data.filter(o => o.customerProductName.includes(filters.value.customerProductName))
    }
    if (filters.value.shoeRId) {
      data = data.filter(o => o.shoeRId.includes(filters.value.shoeRId))
    }

    // Status filter
    if (filters.value.orderStatus && filters.value.orderStatus !== '全部订单') {
      data = data.filter(o => o.orderStatus === filters.value.orderStatus)
    }

    // Radio filter example (all / 已下发 / 未下发)
    if (filters.value.radio === '已下发') {
      data = data.filter(o => o.orderStatusVal > 6)
    } else if (filters.value.radio === '未下发') {
      data = data.filter(o => o.orderStatusVal == 6)
    }

    // Date range filters
    if (filters.value.startDate.length === 2) {
      const [start, end] = filters.value.startDate
      data = data.filter(o => new Date(o.orderStartDate) >= start && new Date(o.orderStartDate) <= end)
    }
    if (filters.value.endDate.length === 2) {
      const [start, end] = filters.value.endDate
      data = data.filter(o => new Date(o.orderEndDate) >= start && new Date(o.orderEndDate) <= end)
    }

    return data
  })

  const paginatedOrders = computed(() => {
    const start = (currentPage.value - 1) * pageSize.value
    const end = start + pageSize.value
    return filteredOrders.value.slice(start, end)
  })

  // Actions
  async function fetchOrders(params = {}) {

    // Example: role-based fetch
    console.log("params is ", params.filterStatus)
    let response
    if (params.filterStatus === 'all'){
      response = await axios.get('/order/getallorders')
    }
    else {
      if (params.filterStatus === 'to_approve'){
        console.log('approve')
      }
      else{
        console.log('by me')
      }
      response = await axios.get('/order/getbusinessdisplayorderbyuser')
    }
    console.log(response)
    allOrders.value = response.data
  }

  function setFilter(key, value) {
    filters.value[key] = value
    currentPage.value = 1
  }

  function setPage(page) {
    currentPage.value = page
  }

  return {
    allOrders,
    filters,
    currentPage,
    pageSize,
    filteredOrders,
    paginatedOrders,
    fetchOrders,
    setFilter,
    setPage
  }
})