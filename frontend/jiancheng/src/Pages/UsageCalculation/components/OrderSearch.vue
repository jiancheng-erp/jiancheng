<template>
    <el-row :gutter="20">
        <el-col :span="24" :offset="0" style="font-size: xx-large; text-align: center"
            >订单查询</el-col
        >
    </el-row>
    <el-row :gutter="20">
        <el-col :span="6" :offset="0" style="white-space: nowrap">
            订单号搜索：
            <el-input
                v-model="orderSearch"
                placeholder=""
                size=""
                :suffix-icon="Search"
                clearable
                @change="tableFilter"
            ></el-input>
        </el-col>
        <el-col :span="6" :offset="2" style="white-space: nowrap">
            客人名称搜索：
            <el-input
                v-model="customerSearch"
                placeholder=""
                size=""
                :suffix-icon="Search"
                clearable
                @change="tableFilter"
            ></el-input>
        </el-col>
        <el-col :span="6" :offset="2" style="white-space: nowrap">
            工厂型号搜索：
            <el-input
                v-model="shoeRIdSearch"
                placeholder=""
                size=""
                :suffix-icon="Search"
                clearable
                @change="tableFilter"
            ></el-input>
        </el-col>
    </el-row>
    <el-row>
        <el-table :data="orderFilterData" border stripe height="600">
            <el-table-column type="expand">
                <template #default="props">
                    <el-table :data="props.row.shoes" :border="true">
                        <el-table-column label="工厂型号" prop="shoeRid" />
                        <el-table-column label="客户型号" prop="customerId" />
                        <el-table-column label="一次BOM编号" prop="firstBom">
                            <template #default="scope">
                                <el-link
                                    :disabled="scope.row.firstBom === 'N/A'"
                                    :underline="false"
                                    type="primary"
                                    @click="handleFirstBomDetail(scope.row.firstBom)"
                                >
                                    {{ scope.row.firstBom }}
                                </el-link>
                            </template>
                        </el-table-column>
                        <el-table-column label="二次BOM编号" prop="secondBom">
                            <template #default="scope">
                                <el-link
                                    :disabled="scope.row.secondBom === 'N/A'"
                                    :underline="false"
                                    type="primary"
                                    @click="handleSecondBomDetail(scope.row.secondBom)"
                                >
                                    {{ scope.row.secondBom }}
                                </el-link>
                            </template>
                        </el-table-column>
                        <el-table-column label="一次采购订单编号" prop="firstOrder">
                            <template #default="scope">
                                <el-link
                                    :disabled="scope.row.firstOrder === 'N/A'"
                                    :underline="false"
                                    type="primary"
                                    @click="handlePurchaseOrderDetail(scope.row.firstOrder)"
                                >
                                    {{ scope.row.firstOrder }}
                                </el-link>
                            </template>
                        </el-table-column>
                        <el-table-column label="二次采购订单编号" prop="secondOrder">
                            <template #default="scope">
                                <el-link
                                    :disabled="scope.row.secondOrder === 'N/A'"
                                    :underline="false"
                                    type="primary"
                                    @click="handlePurchaseOrderDetail(scope.row.secondOrder)"
                                >
                                    {{ scope.row.secondOrder }}
                                </el-link>
                            </template>
                        </el-table-column>
                        <el-table-column prop="statuses" label="鞋型状态"></el-table-column>
                    </el-table>
                </template>
            </el-table-column>
            <el-table-column prop="orderRid" label="订单号"></el-table-column>
            <el-table-column prop="customerName" label="客人名称"></el-table-column>
            <el-table-column prop="createTime" label="订单日期"></el-table-column>
            <el-table-column prop="deadlineTime" label="交货日期"></el-table-column>
            <el-table-column prop="status" label="订单状态"></el-table-column>
            <el-table-column label="操作" width="350">
                <template #default="scope">
                    <el-button type="primary" size="default" @click="handleRowClick(scope.row)">查看用量填写页面</el-button>
                    <el-button type="primary" size="default" @click="handleRowClickForSecondBOM(scope.row)">查看生产BOM</el-button>
                </template>
            </el-table-column>
            
        </el-table>
    </el-row>
    <el-row :gutter="20">
    <el-col>
        <el-pagination
            v-model:current-page="currentPage"
            :page-size="pageSize"
            layout="total, prev, pager, next, jumper"
            :total="totalData"
            @current-change="handlePageChange"
        ></el-pagination>
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
                    },
                })
                this.orderFilterData = response.data // Update table data
                const response2 = await axios.get(`${this.$apiBaseUrl}/order/getorderpageinfo`, {
                params: {
                    orderSearch: this.orderSearch,
                    customerSearch: this.customerSearch,
                    shoeRIdSearch: this.shoeRIdSearch,
                },
                })
                this.totalData = response2.data.totalOrders // Total orders for pagination
                console.log("Total orders:", response2)
                console.log("Total orders:", this.totalData)
            } catch (error) {
                console.error("Error fetching order data:", error)
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
            const url = `${window.location.origin}/usagecalculation/usagecalculationinput/orderid=${row.orderId}`;
            window.open(url, '_blank');
        },
        handleRowClickForSecondBOM(row) {
            const url = `${window.location.origin}/usagecalculation/secondBOM/orderid=${row.orderId}`;
            window.open(url, '_blank');
        },
    },
}
</script>
