<template>
    <el-row :gutter="20">
        <el-col :span="24" :offset="0" style="font-size: xx-large; text-align: center">工艺单修改管理</el-col>
    </el-row>
    <el-row :gutter="20" style="margin-top: 12px;">
        <el-col :span="6" style="white-space: nowrap">
            订单号搜索：
            <el-input
                v-model="orderSearch"
                placeholder=""
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
                :suffix-icon="Search"
                clearable
                @change="tableFilter"
            ></el-input>
        </el-col>
    </el-row>
    <el-row style="margin-top: 8px;">
        <el-table :data="orderFilterData" border stripe height="600" @expand-change="handleExpandChange">
            <el-table-column type="expand">
                <template #default="props">
                    <div v-if="loadingCraftSheet[props.row.orderId]" style="padding: 12px;">
                        <el-text type="info">加载工艺单状态中...</el-text>
                    </div>
                    <el-table
                        v-else-if="craftSheetData[props.row.orderId]"
                        :data="craftSheetData[props.row.orderId]"
                        border
                        size="small"
                    >
                        <el-table-column label="工厂型号" prop="inheritId" width="140" />
                        <el-table-column label="工艺单状态" prop="status" width="160" />
                        <el-table-column label="操作">
                            <template #default="csScope">
                                <el-button
                                    v-if="['已审核并下发','等待用量填写','完成用量填写'].includes(csScope.row.status)"
                                    type="danger"
                                    size="small"
                                    @click="gotoProcessSheet(props.row)"
                                >修改工艺单</el-button>
                                <el-button
                                    v-if="csScope.row.status === '已上传'"
                                    type="warning"
                                    size="small"
                                    @click="gotoProcessSheet(props.row)"
                                >修改投产指令单</el-button>
                            </template>
                        </el-table-column>
                    </el-table>
                    <div v-else style="padding: 12px;">
                        <el-text type="info">暂无工艺单数据</el-text>
                    </div>
                </template>
            </el-table-column>
            <el-table-column prop="orderRid" label="订单号" width="140"></el-table-column>
            <el-table-column prop="customerName" label="客人名称" width="120"></el-table-column>
            <el-table-column prop="createTime" label="订单日期" width="120"></el-table-column>
            <el-table-column prop="deadlineTime" label="交货日期" width="120"></el-table-column>
            <el-table-column prop="status" label="订单状态"></el-table-column>
        </el-table>
    </el-row>
    <el-row :gutter="20" style="margin-top: 8px;">
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
import { Search } from '@element-plus/icons-vue'
import axios from 'axios'

export default {
    data() {
        return {
            Search,
            orderSearch: '',
            customerSearch: '',
            shoeRIdSearch: '',
            orderFilterData: [],
            currentPage: 1,
            pageSize: 10,
            totalData: 0,
            craftSheetData: {},
            loadingCraftSheet: {},
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
                this.orderFilterData = response.data.result
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
        async handleExpandChange(row, expandedRows) {
            const isExpanded = expandedRows.some(r => r.orderId === row.orderId)
            if (!isExpanded || this.craftSheetData[row.orderId] !== undefined) return
            this.loadingCraftSheet = { ...this.loadingCraftSheet, [row.orderId]: true }
            try {
                const response = await axios.get(`${this.$apiBaseUrl}/craftsheet/getordershoelist`, {
                    params: { orderid: row.orderId }
                })
                this.craftSheetData = { ...this.craftSheetData, [row.orderId]: response.data }
            } catch (e) {
                this.craftSheetData = { ...this.craftSheetData, [row.orderId]: [] }
            } finally {
                this.loadingCraftSheet = { ...this.loadingCraftSheet, [row.orderId]: false }
            }
        },
        gotoProcessSheet(row) {
            this.$router.push(`/processsheet/orderid=${row.orderId}`)
        },
    },
}
</script>
