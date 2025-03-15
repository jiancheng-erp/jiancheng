<template>
	<el-row :gutter="20">
		<el-col :span="24" style="font-size: xx-large; text-align: center;">退回任务列表</el-col>
	</el-row>
    <el-row :gutter="20">
        <el-col :span="4">
            <el-input v-model="orderSearch" placeholder="请输入订单号" style="width: 200px; margin-bottom: 20px;"></el-input>
        </el-col>
        <el-col :span="4">
            <el-input v-model="customerSearch" placeholder="请输入客户号" style="width: 200px; margin-bottom: 20px;"></el-input>
        </el-col>
        <el-col :span="4">
            <el-button type="primary" @click="filterData">搜索</el-button>
            <el-button @click="resetFilters">重置</el-button>
        </el-col>
    </el-row>
    <el-row :gutter="20">
        <el-col :span="24">
            <el-table :data="paginatedData" border stripe height="400">
                <el-table-column prop="orderRId" label="订单号"></el-table-column>
                <el-table-column prop="customerName" label="客户号"></el-table-column>
                <el-table-column prop="shoeId" label="鞋型号"></el-table-column>
                <el-table-column prop="statusSource" label="退回部门"></el-table-column>
                <el-table-column prop="revertReason" label="退回原因"></el-table-column>
                <el-table-column prop="revertTime" label="退回时间"></el-table-column>
                <el-table-column label="操作">
                    <template #default="scope">
                        <el-button type="primary" size="mini" @click="openRevertPage(scope.row)">处理退回</el-button>
                    </template>
                </el-table-column>
            </el-table>
            <el-pagination
                background
                layout="prev, pager, next"
                :current-page="currentPage"
                :page-size="pageSize"
                :total="filteredData.length"
                @current-change="handlePageChange">
            </el-pagination>
        </el-col>
    </el-row>
</template>

<script>
import axios from 'axios'

export default {
    props: ['departmentId'],
    data() {
        return {
            orderSearch: '',
            customerSearch: '',
            revertData: [],
            filteredData: [],
            currentPage: 1,
            pageSize: 10
        }
    },
    mounted() {
        this.$setAxiosToken()
        this.getRevertData()
    },
    computed: {
        paginatedData() {
            const start = (this.currentPage - 1) * this.pageSize;
            return this.filteredData.slice(start, start + this.pageSize);
        }
    },
    methods: {
        async getRevertData() {
            const response = await axios.get(`${this.$apiBaseUrl}/revertorder/getrevertorderlist`, {
                params: { departmentId: this.departmentId }
            })
            this.revertData = response.data
            this.filteredData = response.data
        },
        filterData() {
            this.filteredData = this.revertData.filter(item =>
                (!this.orderSearch || item.orderRId.includes(this.orderSearch)) &&
                (!this.customerSearch || item.customerName.includes(this.customerSearch))
            )
            this.currentPage = 1
        },
        resetFilters() {
            this.orderSearch = ''
            this.customerSearch = ''
            this.filteredData = this.revertData
            this.currentPage = 1
        },
        handlePageChange(page) {
            this.currentPage = page
        },
        openRevertPage(row) {
            if (this.departmentId === "7") {
                window.open(`${window.location.origin}/developmentmanager/revertproductionorder/orderid=${row.orderId}`)
            }
            else if (this.departmentId === "14") {
                if (row.currentStatus === 4) {
                    window.open(`${window.location.origin}/usagecalculation/revertusagecalculation/orderid=${row.orderId}`)
                }
            }
        }
    }
}
</script>
