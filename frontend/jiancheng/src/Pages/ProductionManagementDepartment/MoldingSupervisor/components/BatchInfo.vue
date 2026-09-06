<template>
    <el-row class="u-mt-5" :gutter="20">
        <el-col class="u-nowrap" :span="4" :offset="0">
            订单号筛选：
            <el-input v-model="orderRIdSearch" placeholder="请输入订单号" clearable @keypress.enter="getBatchInfoOverview()"
                @clear="getBatchInfoOverview" />
        </el-col>
        <el-col class="u-nowrap" :span="4" :offset="2">
            鞋型号筛选：
            <el-input v-model="shoeRIdSearch" placeholder="请输入鞋型号" clearable @keypress.enter="getBatchInfoOverview()"
                @clear="getBatchInfoOverview()" />
        </el-col>
        <el-col class="u-nowrap" :span="4" :offset="2">
            <el-date-picker v-model="dateValueSearch" type="daterange" start-placeholder="开始日期"
                end-placeholder="结束日期" value-format="YYYY-MM-DD"></el-date-picker>
        </el-col>
    </el-row>
    <el-table :data="orderShoeInfo" border stripe>
        <el-table-column prop="orderRId" label="订单号"></el-table-column>
        <el-table-column prop="orderStartDate" label="订单开始日期"></el-table-column>
        <el-table-column prop="orderEndDate" label="订单结束日期"></el-table-column>
        <el-table-column prop="shoeRId" label="鞋型号"></el-table-column>
        <el-table-column prop="customerProductName" label="客户型号"></el-table-column>
        <el-table-column label="配码信息">
            <template #default="scope">
                <el-button type="primary" @click="openBatchInfoDialog(scope.row)">查看</el-button>
            </template>
        </el-table-column>
    </el-table>
    <el-row :gutter="20">
        <el-col :span="12" :offset="15">
            <el-pagination v-model:current-page="currentPage" v-model:page-size="pageSize"
                :page-sizes="[10, 20, 30, 40]" layout="total, sizes, prev, pager, next, jumper" :total="totalPages"
                @size-change="handleSizeChange" @current-change="handlePageChange" />
        </el-col>
    </el-row>

    <el-dialog title="配码信息" v-model="isBatchInfoDialogOpen" width="80%">
        <el-table :data="orderShoeBatchInfo" :span-method="spanMethod" border stripe :max-height="700">
            <el-table-column prop="colorName" label="颜色"></el-table-column>
            <el-table-column prop="totalAmount" label="颜色总数"></el-table-column>
            <el-table-column prop="batchName" label="配码编号"></el-table-column>
            <el-table-column v-for="column in filteredColumns" :key="column.prop" :prop="column.prop"
                :label="column.label"></el-table-column>
            <el-table-column prop="pairAmount" label="双数"></el-table-column>
        </el-table>
    </el-dialog>
</template>
<script>
import axios from 'axios';
import { getShoeSizesName, shoeBatchInfoTableSpanMethod } from '../../utils';
export default {
    data() {
        return {
            orderShoeInfo: [],
            orderRIdSearch: '',
            shoeRIdSearch: '',
            currentPage: 1,
            pageSize: 10,
            totalPages: 0,
            isBatchInfoDialogOpen: false,
            currentRow: {},
            getShoeSizesName,
            shoeSizeColumns: [],
            orderShoeBatchInfo: [],
            spanMethod: null,
            dateValueSearch: null,
        }
    },
    mounted() {
        this.getBatchInfoOverview()
    },
    computed: {
        filteredColumns() {
            return this.shoeSizeColumns.filter(column =>
                this.orderShoeBatchInfo.some(row => row[column.prop] !== undefined && row[column.prop] !== null && row[column.prop] !== 0)
            );
        }
    },
    methods: {
        async getBatchInfoOverview() {
            const params = {
                "page": this.currentPage,
                "pageSize": this.pageSize,
                "orderRId": this.orderRIdSearch,
                "shoeRId": this.shoeRIdSearch,
            }
            const response = await axios.get(`${this.$apiBaseUrl}/production/getallordershoeinfo`, { params })
            this.orderShoeInfo = response.data.result
            this.totalPages = response.data.totalLength
        },
        handlePageChange(val) {
            this.currentPage = val
            this.getBatchInfoOverview()
        },
        handleSizeChange(val) {
            this.pageSize = val
            this.getBatchInfoOverview()
        },
        async openBatchInfoDialog(row) {
            this.currentRow = row
            this.shoeSizeColumns = await this.getShoeSizesName(row.orderId)
            await this.getOrderShoeBatchInfo()
            this.isBatchInfoDialogOpen = true
        },
        async getOrderShoeBatchInfo() {
            const params = {
                "orderShoeId": this.currentRow.orderShoeId,
            }
            const response = await axios.get(`${this.$apiBaseUrl}/production/getordershoebatchinfo`, { params })
            this.orderShoeBatchInfo = response.data
            this.spanMethod = shoeBatchInfoTableSpanMethod(this.orderShoeBatchInfo)
        }
    }
}

</script>
