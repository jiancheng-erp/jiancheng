<template>
    <el-row :gutter="20">
        <el-col>
            <el-input v-model="orderRIdSearch" placeholder="订单号搜索" clearable @change="getOrderTableData()"
                @clear="getOrderTableData()" class="search-input"/>
            <el-input v-model="shoeRIdSearch" placeholder="鞋型号搜索" clearable @change="getOrderTableData()"
                @clear="getOrderTableData()" class="search-input"/>
            <el-input v-model="customerNameSearch" placeholder="客户名称搜索" clearable @change="getOrderTableData()"
                @clear="getOrderTableData()" class="search-input"/>
            <el-input v-model="customerProductNameSearch" placeholder="客户型号搜索" clearable @change="getOrderTableData()"
                @clear="getOrderTableData()" class="search-input"/>
            <el-select v-model="statusSearch" clearable filterable @change="getOrderTableData()" placeholder="状态搜索" class="search-input">
                <el-option v-for="item in ['未提交', '生产副总审核中', '生产副总驳回', '总经理审核中', '总经理驳回', '已审批']" :key="item"
                    :label="item" :value="item">
                </el-option>
            </el-select>
        </el-col>
        <!-- <el-col :span="4">
            <el-select v-model="departmentSearch" clearable filterable @change="getOrderTableData()" placeholder="工段搜索">
                <el-option v-for="item in ['裁断', '针车', '成型']" :key="item" :label="item" :value="item">
                </el-option>
            </el-select>
        </el-col> -->
    </el-row>
    <el-row :gutter="20">
        <el-col :span="24" :offset="0">
            <el-table :data="orderTableData" border stripe style="height: 75vh">
                <el-table-column prop="orderRId" label="订单号"></el-table-column>
                <el-table-column prop="shoeRId" label="鞋型号"></el-table-column>
                <el-table-column prop="customerName" label="客户名称"></el-table-column>
                <el-table-column prop="customerProductName" label="客户型号"></el-table-column>
                <el-table-column prop="teamName" label="需审批工段"></el-table-column>
                <el-table-column prop="statusName" label="状态"></el-table-column>
                <el-table-column label="操作">
                    <template #default="scope">
                        <el-button type="primary" size="small" @click="openWageApproval(scope.row)">审批</el-button>
                    </template>
                </el-table-column>
            </el-table>
        </el-col>
    </el-row>
    <el-row :gutter="20">
        <el-col>
            <el-pagination @size-change="handleSizeChange" @current-change="handlePageChange"
                :current-page="currentPage" :page-sizes="[10, 20, 30, 40]" :page-size="pageSize"
                layout="total, sizes, prev, pager, next, jumper" :total="totalRows" />
        </el-col>
    </el-row>
</template>
<script>
import axios from 'axios'
export default {
    data() {
        return {
            role: localStorage.getItem('role'),
            orderRIdSearch: '',
            shoeRIdSearch: '',
            customerNameSearch: '',
            customerProductNameSearch: '',
            teamsSearch: [
                '裁断', '针车', '成型'
            ],
            statusSearch: '',
            orderTableData: [],
            currentPage: 1,
            pageSize: 10,
            totalRows: 0
        }
    },
    mounted() {
        this.getDefaultStatus()
        this.getOrderTableData()
    },
    methods: {
        getDefaultStatus() {
            if (this.role === '3') {
                this.statusSearch = '生产副总审核中'
            } else {
                this.statusSearch = '总经理审核中'
            }
        },
        async getOrderTableData() {
            const params = {
                "page": this.currentPage,
                "pageSize": this.pageSize,
                "orderRId": this.orderRIdSearch,
                "shoeRId": this.shoeRIdSearch,
                "team": this.teamsSearch.toString(),
                "statusName": this.statusSearch,
                "customerName": this.customerNameSearch,
                "customerProductName": this.customerProductNameSearch
            }
            const response = await axios.get(`${this.$apiBaseUrl}/production/getnewpricereports`, { params })
            this.orderTableData = response.data.result
            this.totalRows = response.data.totalLength
        },
        handleSizeChange(val) {
            this.pageSize = val
            this.getOrderTableData()
        },
        handlePageChange(val) {
            this.currentPage = val
            this.getOrderTableData()
        },
        openWageApproval(row) {
            let params = {"orderId": row.orderId, "orderShoeId": row.orderShoeId}
			const queryString = new URLSearchParams(params).toString();
			const url = `${window.location.origin}/productionmanager/productionwageapproval?${queryString}`
            window.open(url, '_blank')
        }
    }
}
</script>
