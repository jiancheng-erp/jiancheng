<template>
    <el-row :gutter="20">
        <el-col class="u-page-title" :span="24" :offset="0">订单鞋型修改</el-col>
    </el-row>
    <el-row :gutter="20">
        <el-col class="u-nowrap" :span="6" :offset="0">
            订单号搜索：
            <el-input v-model="orderSearch" placeholder="" :suffix-icon="Search" clearable
                @change="tableFilter"></el-input>
        </el-col>
        <el-col class="u-nowrap" :span="6" :offset="2">
            客人名称搜索：
            <el-input v-model="customerSearch" placeholder="" :suffix-icon="Search" clearable
                @change="tableFilter"></el-input>
        </el-col>
        <el-col class="u-nowrap" :span="6" :offset="2">
            工厂型号搜索：
            <el-input v-model="shoeRIdSearch" placeholder="" :suffix-icon="Search" clearable
                @change="tableFilter"></el-input>
        </el-col>
    </el-row>
    <el-row style="margin-top: 12px">
        <el-table :data="orderData" border stripe height="calc(100vh - var(--main-table-offset))">
            <el-table-column type="expand">
                <template #default="props">
                    <el-table :data="props.row.shoes" :border="true">
                        <el-table-column label="工厂型号" prop="shoeRid" />
                        <el-table-column label="客户型号" prop="customerId" />
                        <el-table-column label="鞋型状态" prop="statuses" />
                    </el-table>
                </template>
            </el-table-column>
            <el-table-column prop="orderRid" label="订单号"></el-table-column>
            <el-table-column prop="customerName" label="客人名称"></el-table-column>
            <el-table-column prop="createTime" label="订单日期"></el-table-column>
            <el-table-column prop="deadlineTime" label="交货日期"></el-table-column>
            <el-table-column prop="status" label="订单状态"></el-table-column>
            <el-table-column label="操作" width="160">
                <template #default="scope">
                    <el-button type="primary" @click="handleEdit(scope.row)">修改鞋型信息</el-button>
                </template>
            </el-table-column>
        </el-table>
    </el-row>
    <el-row :gutter="20">
        <el-col>
            <el-pagination v-model:current-page="currentPage" :page-size="pageSize"
                layout="total, prev, pager, next, jumper" :total="totalData"
                @current-change="handlePageChange"></el-pagination>
        </el-col>
    </el-row>

    <OrderShoeTypeEditDialog v-model="editDialogVisible" :order-id="editOrderId" @saved="getOrderData" />
</template>

<script>
import { Search } from '@element-plus/icons-vue'
import axios from 'axios'
import OrderShoeTypeEditDialog from './OrderShoeTypeEditDialog.vue'

export default {
    components: {
        OrderShoeTypeEditDialog,
    },
    data() {
        return {
            Search,
            orderSearch: '',
            customerSearch: '',
            shoeRIdSearch: '',
            orderData: [],
            currentPage: 1,
            pageSize: 10,
            totalData: 0,
            editDialogVisible: false,
            editOrderId: null,
        }
    },
    async mounted() {
        this.$setAxiosToken()
        await this.getOrderData()
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
                    },
                })
                this.orderData = response.data.result
                this.totalData = response.data.total
            } catch (error) {
                console.error('Error fetching order data:', error)
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
        handleEdit(row) {
            this.editOrderId = row.orderId
            this.editDialogVisible = true
        },
    },
}
</script>
