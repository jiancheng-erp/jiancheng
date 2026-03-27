<template>
    <el-row :gutter="20">
        <el-col :span="24" :offset="0" style="font-size: xx-large; text-align: center">订单查询</el-col>
    </el-row>
    <el-row :gutter="20">
        <el-col :span="6" :offset="0" style="white-space: nowrap">
            订单号搜索：
            <el-input v-model="orderSearch" placeholder="" size="" :suffix-icon="Search" clearable @change="tableFilter"></el-input>
        </el-col>
        <el-col :span="6" :offset="2" style="white-space: nowrap">
            客人名称搜索：
            <el-input v-model="customerSearch" placeholder="" size="" :suffix-icon="Search" clearable @change="tableFilter"></el-input>
        </el-col>
        <el-col :span="6" :offset="2" style="white-space: nowrap">
            工厂型号搜索：
            <el-input v-model="shoeRIdSearch" placeholder="" size="" :suffix-icon="Search" clearable @change="tableFilter"></el-input>
        </el-col>
    </el-row>
    <el-row :gutter="20" style="margin-top: 10px">
        <el-col :span="7" :offset="0" style="white-space: nowrap">
            订单日期：
            <el-date-picker v-model="startDateRange" type="daterange" range-separator="至"
                start-placeholder="开始" end-placeholder="结束" value-format="YYYY-MM-DD"
                style="width: 240px" @change="tableFilter" clearable />
        </el-col>
        <el-col :span="7" :offset="2" style="white-space: nowrap">
            交货日期：
            <el-date-picker v-model="endDateRange" type="daterange" range-separator="至"
                start-placeholder="开始" end-placeholder="结束" value-format="YYYY-MM-DD"
                style="width: 240px" @change="tableFilter" clearable />
        </el-col>
        <el-col :span="6" :offset="1">
            <el-button type="primary" @click="tableFilter">搜索</el-button>
            <el-button @click="resetFilters">重置</el-button>
            <el-button type="success" @click="exportExcel" :loading="exporting">导出Excel</el-button>
            <el-switch v-model="showRmb" active-text="RMB" inactive-text="原单位" style="margin-left: 12px" />
        </el-col>
    </el-row>
    <el-row style="margin-top: 8px" v-if="Object.keys(currencyRates).length">
        <el-col :span="24">
            <span style="font-size: 13px; color: #909399">实时汇率：</span>
            <el-tag v-for="(rate, currency) in displayRates" :key="currency" size="small" style="margin-right: 6px" type="info">
                1 {{ currency }} = {{ rate }} RMB
            </el-tag>
        </el-col>
    </el-row>
    <el-row>
        <el-table :data="orderFilterData" border stripe height="600">
            <el-table-column type="expand">
                <template #default="props">
                    <el-table :data="props.row.shoes" :border="true">
                        <el-table-column label="工厂型号" prop="shoeRid" />
                        <el-table-column label="客户型号" prop="customerId" />
                        <el-table-column label="业务下发时间" prop="bussinessEventTime" />
                        <el-table-column label="投产指令单下发时间" prop="productionOrderIssueEventTime" />
                        <el-table-column label="用量填写完成时间" prop="firstUsageInputIssueEventTime" />
                        <el-table-column label="一次采购订单完成时间" prop="firstPurchaseOrderIssueEventTime" />
                        <el-table-column label="二次采购订单完成时间" prop="secondPurchaseOrderIssueEventTime" />
                        <el-table-column prop="statuses" label="鞋型状态"></el-table-column>
                        <el-table-column prop="purchaseStatus" label="采购状态"></el-table-column>
                        <el-table-column prop="purchaseStatus" label="采购状态"></el-table-column>
                    </el-table>
                </template>
            </el-table-column>
            <el-table-column prop="orderRid" label="订单号"></el-table-column>
            <el-table-column prop="customerName" label="客人名称"></el-table-column>
            <el-table-column prop="shoeRid" label="工厂型号"></el-table-column>
            <el-table-column prop="customerId" label="客户型号"></el-table-column>
            <el-table-column prop="orderAmount" label="订单数量"></el-table-column>
            <el-table-column prop="orderTotalPrice" :label="showRmb ? '订单总价(RMB)' : '订单总价'" width="160">
                <template #default="{ row }">
                    <template v-if="showRmb">
                        {{ row.orderTotalPriceRmb != null ? Number(row.orderTotalPriceRmb).toFixed(2) + ' RMB' : '' }}
                    </template>
                    <template v-else>
                        {{ row.orderTotalPrice != null ? Number(row.orderTotalPrice).toFixed(2) + ' ' + (row.orderCurrency || '') : '' }}
                    </template>
                </template>
            </el-table-column>
            <el-table-column prop="createTime" label="订单日期"></el-table-column>
            <el-table-column prop="deadlineTime" label="交货日期"></el-table-column>
            <el-table-column prop="status" label="订单状态"></el-table-column>
            <el-table-column label="操作" width="100" v-if="showDetailLink">
                <template #default="scope">
                    <el-button type="primary" link @click="openOrderDetail(scope.row)">查看详情</el-button>
                </template>
            </el-table-column>
        </el-table>
    </el-row>
    <el-row :gutter="20">
        <el-col>
            <el-pagination v-model:current-page="currentPage" :page-size="pageSize" layout="total, prev, pager, next, jumper" :total="totalData" @current-change="handlePageChange"></el-pagination>
        </el-col>
    </el-row>
</template>

<script>
import { ref, onMounted } from 'vue'
import { Search } from '@element-plus/icons-vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'

export default {
    data() {
        return {
            Search,
            orderSearch: '',
            shoeRIdSearch: '',
            orderData: [],
            orderFilterData: [],
            customerSearch: '',
            startDateRange: null,
            endDateRange: null,
            currentPage: 1,
            pageSize: 10,
            totalPages: 0,
            totalData: 0,
            viewPastTasks: 0,
            exporting: false,
            showRmb: false,
            currencyRates: {}
        }
    },
    computed: {
        showDetailLink() {
            const role = parseInt(localStorage.getItem('role'), 10)
            return role === 10
        },
        displayRates() {
            const skip = new Set(['RMB', 'CNY', 'USA', 'USE', '美金', '€'])
            const result = {}
            for (const [k, v] of Object.entries(this.currencyRates)) {
                if (!skip.has(k) && v !== 1.0) {
                    result[k] = v
                }
            }
            return result
        },
        queryParams() {
            const params = {
                page: this.currentPage,
                pageSize: this.pageSize,
                orderSearch: this.orderSearch,
                customerSearch: this.customerSearch,
                shoeRIdSearch: this.shoeRIdSearch,
                viewPastTasks: this.viewPastTasks
            }
            if (this.startDateRange && this.startDateRange.length === 2) {
                params.startDateFrom = this.startDateRange[0]
                params.startDateTo = this.startDateRange[1]
            }
            if (this.endDateRange && this.endDateRange.length === 2) {
                params.endDateFrom = this.endDateRange[0]
                params.endDateTo = this.endDateRange[1]
            }
            return params
        }
    },
    async mounted() {
        this.$setAxiosToken()
        await Promise.all([this.getOrderData(this.currentPage), this.fetchCurrencyRates()])
    },
    methods: {
        async getOrderData() {
            try {
                const response = await axios.get(`${this.$apiBaseUrl}/order/getorderfullinfo`, {
                    params: this.queryParams
                })
                this.orderFilterData = response.data.result
                this.orderFilterData = this.orderFilterData.map((order) => ({
                    ...order,
                    shoeRid: order.shoes.map((s) => s.shoeRid).join(', ') || 'N/A',
                    customerId: order.shoes.map((s) => s.customerId).join(', ') || 'N/A'
                }))
                this.totalData = response.data.total
            } catch (error) {
                console.error('Error fetching order data:', error)
            }
        },
        async fetchCurrencyRates() {
            try {
                const resp = await axios.get(`${this.$apiBaseUrl}/order/getcurrencyrates`)
                this.currencyRates = resp.data.rates || {}
            } catch (e) {
                console.error('Error fetching currency rates:', e)
            }
        },
        handlePageChange(page) {
            this.currentPage = page
            this.getOrderData()
        },
        tableFilter() {
            this.currentPage = 1
            this.getOrderData()
        },
        resetFilters() {
            this.orderSearch = ''
            this.customerSearch = ''
            this.shoeRIdSearch = ''
            this.startDateRange = null
            this.endDateRange = null
            this.tableFilter()
        },
        async exportExcel() {
            this.exporting = true
            try {
                const params = { ...this.queryParams }
                delete params.page
                delete params.pageSize
                if (this.showRmb) {
                    params.convertToRMB = '1'
                }
                const response = await axios.get(`${this.$apiBaseUrl}/order/exportorderexcel`, {
                    params,
                    responseType: 'blob'
                })
                const blob = new Blob([response.data], { type: response.headers['content-type'] })
                const disposition = response.headers['content-disposition']
                let filename = '订单查询.xlsx'
                if (disposition && disposition.includes('filename=')) {
                    const match = disposition.match(/filename="?(.+?)"?$/)
                    if (match && match[1]) {
                        filename = decodeURIComponent(match[1])
                    }
                }
                const link = document.createElement('a')
                link.href = URL.createObjectURL(blob)
                link.download = filename
                document.body.appendChild(link)
                link.click()
                document.body.removeChild(link)
                URL.revokeObjectURL(link.href)
            } catch (error) {
                ElMessage.error('导出失败')
                console.error('Export error:', error)
            } finally {
                this.exporting = false
            }
        },
        handleRowClick(row) {
            const url = `${window.location.origin}/processsheet/orderid=${row.orderId}`
            window.open(url, '_blank')
        },
        openOrderDetail(row) {
            const url = `${window.location.origin}/business/businessorderdetail/orderid=${row.orderId}/finance`
            window.open(url, '_blank')
        },
        handleRowClick2(row) {
            const url = `${window.location.origin}/technicalmanager/secondbomusagereview/orderid=${row.orderId}`
            window.open(url, '_blank')
        }
    }
}
</script>
