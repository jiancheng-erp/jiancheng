<template>
    <el-row :gutter="20">
        <el-col class="u-page-title" :span="24" :offset="0">生产节点管理</el-col>
    </el-row>
    <el-row class="u-mt-5" :gutter="20">
        <el-col class="u-nowrap" :span="4" :offset="0">
            订单号筛选：
            <el-input v-model="orderRIdSearch" placeholder="请输入订单号" clearable @keypress.enter="getOrderTableData()"
                @clear="getOrderTableData()" />
        </el-col>
        <el-col class="u-nowrap" :span="4" :offset="2">
            鞋型号筛选：
            <el-input v-model="shoeRIdSearch" placeholder="请输入鞋型号" clearable @keypress.enter="getOrderTableData()"
                @clear="getOrderTableData()" />
        </el-col>
        <el-col :span="4" :offset="4">
            <span class="u-nowrap">状态点查询：
                <el-select v-model="nodeNameSearch" clearable filterable @change="getOrderTableData()"
                    @clear="getOrderTableData()">
                    <el-option v-for="item in [
                        '生产开始',
                        '裁断开始',
                        '针车预备开始',
                        '针车开始',
                        '成型开始',
                        '裁断结束',
                        '针车结束',
                        '成型结束',
                        '生产结束'
                    ]" :key="item" :label="item" :value="item">
                    </el-option>
                </el-select>
            </span>
        </el-col>
    </el-row>
    <el-row :gutter="20">
        <el-table :data="orderTableData" border stripe>
            <el-table-column prop="orderRId" label="订单号"></el-table-column>
            <el-table-column prop="shoeRId" label="鞋型号"></el-table-column>
            <el-table-column prop="nodeName" label="需确认状态点"></el-table-column>
            <el-table-column label="操作">
                <template #default="scope">
                    <el-button type="primary" size="small" @click="openConfirmationPage(scope.row)">确认状态完成</el-button>
                </template>
            </el-table-column>
        </el-table>
    </el-row>
    <el-row :gutter="20">
        <el-col :span="12" :offset="14">
            <el-pagination @size-change="handleSizeChange" @current-change="handlePageChange"
                :current-page="currentPage" :page-sizes="[10, 20, 30, 40]" :page-size="pageSize"
                layout="total, sizes, prev, pager, next, jumper" :total="totalRows" />
        </el-col>
    </el-row>
</template>
<script>
import { ElMessage, ElMessageBox } from 'element-plus'
import axios from 'axios'
export default {
    data() {
        return {
            currentPage: 1,
            pageSize: 10,
            totalRows: 0,
            orderRIdSearch: '',
            shoeRIdSearch: '',
            nodeNameSearch: '',
            orderTableData: [],
        }
    },
    mounted() {
        this.getOrderTableData()
    },
    methods: {
        handleSizeChange(val) {
            this.pageSize = val
            this.getOrderTableData()
        },
        handlePageChange(val) {
            this.currentPage = val
            this.getOrderTableData()
        },
        async getOrderTableData() {
            const params = {
                "page": this.currentPage,
                "pageSize": this.pageSize,
                "orderRId": this.orderRIdSearch,
                "shoeRId": this.shoeRIdSearch,
                "nodeName": this.nodeNameSearch
            }
            const response = await axios.get(`${this.$apiBaseUrl}/production/productionmanager/getfinishednodes`, { params })
            this.orderTableData = response.data.result
            this.totalRows = response.data.totalLength
        },
        async openConfirmationPage(rowData) {
			const params = {
				"orderId": rowData.orderId,
				"orderShoeId": rowData.orderShoeId,
			}
			const queryString = new URLSearchParams(params).toString();
			const url = `${window.location.origin}/productiongeneral/productionstatustracking?${queryString}`
			window.open(url, '_blank')
        },
    }
}
</script>
