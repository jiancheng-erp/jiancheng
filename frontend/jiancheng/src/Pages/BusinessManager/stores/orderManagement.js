import { defineStore } from 'pinia'

export const useOrderManagementStore = defineStore('orderManagement', {
    state: () => ({
        currentPage: 1,
        pageSize: 10,
        totalItems: 0,
        orderRidFilter: '',
        orderCidFilter: '',
        orderStartDateFilter: '',
        orderEndDateFilter: '',
        orderCustomerNameFilter: '',
        orderCustomerBrandFilter: '',
        customerProductNameFilter: '',
        shoeRIdSearch: '',
        displayData: [],
        unfilteredData: [],
        radio: 'all',
        orderStatusOption: ['全部订单', '我审批的订单', '我发起的订单'],
        selectedOrderStatus: '全部订单'
    }),
    getters: {
        paginatedDisplayData: (state) => {
            const start = (state.currentPage - 1) * state.pageSize
            const end = state.currentPage * state.pageSize
            return state.displayData.slice(start, end)
        }
    },
    actions: {
        setOrders(orders) {
            this.unfilteredData = orders
            this.filterDisplayOrder()
        },
        handlePageChange(newPage) {
            this.currentPage = newPage
        },
        resetFilters() {
            this.orderRidFilter = ''
            this.orderCidFilter = ''
            this.orderCustomerNameFilter = ''
            this.orderCustomerBrandFilter = ''
            this.orderStartDateFilter = ''
            this.orderEndDateFilter = ''
            this.shoeRIdSearch = ''
            this.customerProductNameFilter = ''
            this.filterDisplayOrder()
        },
        filterDisplayOrder() {
            const contains = (fieldVal, filterVal) =>
                String(fieldVal || '').toLowerCase().includes(String(filterVal || '').toLowerCase())

            const data = this.unfilteredData.filter((row) => {
                // Text filters
                if (this.orderRidFilter && !contains(row.orderRid, this.orderRidFilter)) return false
                if (this.orderCidFilter && !contains(row.orderCid, this.orderCidFilter)) return false
                if (this.orderCustomerNameFilter && !contains(row.customerName, this.orderCustomerNameFilter)) return false
                if (this.orderCustomerBrandFilter && !contains(row.customerBrand, this.orderCustomerBrandFilter)) return false
                if (this.customerProductNameFilter && !contains(row.customerProductName, this.customerProductNameFilter)) return false
                if (this.shoeRIdSearch && !contains(row.shoeRId, this.shoeRIdSearch)) return false

                // Date range filters
                if (this.orderStartDateFilter && this.orderStartDateFilter.length === 2) {
                    const d = new Date(row.orderStartDate)
                    if (d < this.orderStartDateFilter[0] || d > this.orderStartDateFilter[1]) return false
                }
                if (this.orderEndDateFilter && this.orderEndDateFilter.length === 2) {
                    const d = new Date(row.orderEndDate)
                    if (d < this.orderEndDateFilter[0] || d > this.orderEndDateFilter[1]) return false
                }

                // Radio filter (dispatch / revert status)
                // orderStatusVal === 6 means 已下发
                if (this.radio === '已下发' && row.orderStatusVal !== 6) return false
                if (this.radio === '未下发' && row.orderStatusVal === 6) return false
                if (this.radio === '退回' && !row.hasRevertEvent) return false

                return true
            })

            this.displayData = data
            this.totalItems = data.length
            this.currentPage = 1
        }
    }
})
