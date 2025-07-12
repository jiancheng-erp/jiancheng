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
            <el-table-column prop="createTime" label="订单日期"></el-table-column>
            <el-table-column prop="deadlineTime" label="交货日期"></el-table-column>
            <el-table-column prop="status" label="订单状态"></el-table-column>
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

export default {
    data() {
        return {
            Search,
            orderSearch: '',
            shoeRIdSearch: '',
            orderData: [],
            orderFilterData: [],
            customerSearch: '',
            currentPage: 1,
            pageSize: 10,
            totalPages: 0,
            totalData: 0,
            viewPastTasks: 0
        }
    },
    async mounted() {
        this.$setAxiosToken()
        await this.getOrderData(this.currentPage)
    },
    methods: {
        async getOrderData() {
            try {
                const response = await axios.get(`${this.$apiBaseUrl}/order/getorderfullinfo`, {
                    params: {
                        page: this.currentPage,
                        pageSize: this.pageSize,
                        orderSearch: this.orderSearch,
                        customerSearch: this.customerSearch,
                        shoeRIdSearch: this.shoeRIdSearch,
                        viewPastTasks: this.viewPastTasks
                    }
                })
                this.orderFilterData = response.data.result // Update table data
                this.orderFilterData = this.orderFilterData.map((order) => ({
                    ...order,
                    shoeRid: order.shoes.map((s) => s.shoeRid).join(', ') || 'N/A',
                    customerId: order.shoes.map((s) => s.customerId).join(', ') || 'N/A'
                }))
                this.totalData = response.data.total // Update total data count
            } catch (error) {
                console.error('Error fetching order data:', error)
            }
        },
        handlePageChange(page) {
            this.currentPage = page
            this.getOrderData()
        },
        tableFilter() {
            // Reset to the first page on filter
            this.currentPage = 1
            this.getOrderData()
        },
        handleRowClick(row) {
            const url = `${window.location.origin}/processsheet/orderid=${row.orderId}`
            window.open(url, '_blank')
        },
        handleRowClick2(row) {
            const url = `${window.location.origin}/technicalmanager/secondbomusagereview/orderid=${row.orderId}`
            window.open(url, '_blank')
        }
    }
}
</script>
