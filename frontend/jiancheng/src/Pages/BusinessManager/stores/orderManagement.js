import { defineStore } from 'pinia'

export const useOrderManagementStore = defineStore('orderManagement', {
    state: () => ({
        orderNotInCurStatus: '',
        orderInCurStatus: '',
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
        filterData: [],
        filterList: [],
        indexToFilter: [],
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
            this.displayData = orders
            this.totalItems = orders.length
            this.currentPage = 1
        },
        handlePageChange(newPage) {
            this.currentPage = newPage
        },
        switchRadio(value) {
            if (value === 'all') {
                this.orderInCurStatus = '已下发'
                this.orderNotInCurStatus = '未下发'
            } else if (value === '已下发') {
                this.orderInCurStatus = ''
                this.orderNotInCurStatus = 'all'
            } else {
                this.orderInCurStatus = 'all'
                this.orderNotInCurStatus = ''
            }
            this.filterDisplayOrder()
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
            this.filterList = []
            this.indexToFilter = []
        },
        filterOrderByFilterType(filterType) {
            switch (filterType) {
                case 1:
                    this.filterByRid()
                    break
                case 2:
                    this.filterByCid()
                    break
                case 3:
                    this.filterByCustomerName()
                    break
                case 4:
                    this.filterByCustomerBrand()
                    break
                case 5:
                    this.filterOrderByStartDate()
                    break
                case 6:
                    this.filterOrderByEndDate()
                    break
                case 7:
                    this.filterOrderByShoeRId()
                    break
                case 8:
                    this.filterByCustomerProductName()
                    break
                default:
                    break
            }
        },
        filterOrderByShoeRId() {
            this.filterData = this.displayData.filter((task) => {
                const filterMatch = task.shoeRId.toLowerCase().includes(this.shoeRIdSearch.toLowerCase())
                return filterMatch
            })
            this.displayData = this.filterData
        },
        filterByCustomerProductName() {
            this.filterData = this.displayData.filter((task) => {
                const filterMatch = task.customerProductName.toLowerCase().includes(this.customerProductNameFilter.toLowerCase())
                return filterMatch
            })
            this.displayData = this.filterData
        },
        filterDisplayOrder() {
            this.filterList = [
                this.orderRidFilter,
                this.orderCidFilter,
                this.orderCustomerNameFilter,
                this.orderCustomerBrandFilter,
                this.orderStartDateFilter,
                this.orderEndDateFilter,
                this.shoeRIdSearch,
                this.customerProductNameFilter
            ]
            this.indexToFilter = this.filterList.filter((filter) => filter).map((filter) => this.filterList.indexOf(filter))
            this.displayData = this.unfilteredData
            this.indexToFilter.forEach((index) => this.filterOrderByFilterType(index + 1))
            this.filterOrderByStatus()
            this.totalItems = this.displayData.length
            this.currentPage = 1
        },
        filterOrderByStatus() {
            if (this.orderInCurStatus && this.orderNotInCurStatus) {
                return
            }
            if (this.orderInCurStatus) {
                this.filterData = this.displayData.filter((task) => task.orderStatusVal == 6)
                this.displayData = this.filterData
            } else if (this.orderNotInCurStatus) {
                this.filterData = this.displayData.filter((task) => task.orderStatusVal != 6)
                this.displayData = this.filterData
            }
        },
        filterOrderByStartDate() {
            this.filterData = this.displayData.filter((task) => {
                const filterMatch = new Date(task.orderStartDate) >= this.orderStartDateFilter[0] &&
                    new Date(task.orderStartDate) <= this.orderStartDateFilter[1]
                return filterMatch
            })
            this.displayData = this.filterData
        },
        filterOrderByEndDate() {
            this.filterData = this.displayData.filter((task) => {
                const filterMatch = new Date(task.orderEndDate) >= this.orderEndDateFilter[0] &&
                    new Date(task.orderEndDate) <= this.orderEndDateFilter[1]
                return filterMatch
            })
            this.displayData = this.filterData
        },
        filterByCustomerName() {
            this.filterData = this.displayData.filter((task) => {
                const filterMatch = task.customerName.toLowerCase().includes(this.orderCustomerNameFilter.toLowerCase())
                return filterMatch
            })
            this.displayData = this.filterData
        },
        filterByCustomerBrand() {
            this.filterData = this.displayData.filter((task) => {
                const filterMatch = task.customerBrand.toLowerCase().includes(this.orderCustomerBrandFilter.toLowerCase())
                return filterMatch
            })
            this.displayData = this.filterData
        },
        filterByCid() {
            this.filterData = this.displayData.filter((task) => {
                const filterMatch = task.orderCid.toLowerCase().includes(this.orderCidFilter.toLowerCase())
                return filterMatch
            })
            this.displayData = this.filterData
        },
        filterByRid() {
            this.filterData = this.displayData.filter((task) => {
                const filterMatch = task.orderRid.toLowerCase().includes(this.orderRidFilter.toLowerCase())
                return filterMatch
            })
            this.displayData = this.filterData
        }
    }
})
