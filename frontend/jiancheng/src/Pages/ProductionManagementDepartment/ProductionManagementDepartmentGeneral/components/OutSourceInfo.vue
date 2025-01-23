<template>
    <el-row :gutter="20">
        <el-col :span="24" :offset="0" style="font-size: xx-large; text-align: center">外包信息页面</el-col>
    </el-row>
    <el-row :gutter="20" style="margin-top: 20px">
        <el-col :span="4" :offset="0" style="white-space: nowrap;">
            订单号筛选：
            <el-input v-model="orderRIdSearch" placeholder="请输入订单号" clearable
                @keypress.enter="getOutsourceOverview()" @clear="getOutsourceOverview"/>
        </el-col>
        <el-col :span="4" :offset="2" style="white-space: nowrap;">
            鞋型号筛选：
            <el-input v-model="shoeRIdSearch" placeholder="请输入鞋型号" clearable
                @keypress.enter="getOutsourceOverview()" @clear="getOutsourceOverview"/>
        </el-col>
        <el-col :span="4" :offset="2" style="white-space: nowrap;">
            外包状态筛选：
            <el-select v-model="outsourceStatusSearch" placeholder="请选择外包状态" clearable
                @change="getOutsourceOverview()">
                <el-option v-for="item in outsourceStatusOptions" :key="item" :label="item"
                    :value="item" />
            </el-select>
        </el-col>
    </el-row>
    <el-row :gutter="20">
        <el-col :span="24" :offset="0">
            <el-table :data="orderTableData" border stripe>
                <el-table-column prop="orderRId" label="订单号"></el-table-column>
                <el-table-column prop="shoeRId" label="鞋型号"></el-table-column>
                <el-table-column prop="customerProductName" label="客户型号"></el-table-column>
                <el-table-column prop="outsourceFactory" label="外包厂家"></el-table-column>
                <el-table-column prop="outsourceType" label="外包工段"></el-table-column>
                <el-table-column prop="outsourceStatus" label="状态"></el-table-column>
                <el-table-column label="外包信息">
                    <template #default="scope">
                        <el-button type="primary" size="small"
                            @click="openOutsourceFlow(scope.row)">查看</el-button>

                    </template>
                </el-table-column>
            </el-table>
        </el-col>
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
import axios from 'axios'
export default {
    data() {
        return {
            orderRIdSearch: '',
            shoeRIdSearch: '',
            orderTableData: [],
            currentPage: 1,
            pageSize: 10,
            totalRows: 0,
            outsourceStatusOptions: [
                "未提交",
                "已提交",
                "已审批",
                "被驳回",
                "材料出库",
                "外包生产中",
                "成品入库",
                "外包结束",
            ],
            outsourceStatusSearch: '',
        }
    },
    mounted() {
        this.getOutsourceOverview()
    },
    methods: {
        handleSizeChange(val) {
            this.pageSize = val
            this.getOutsourceOverview()
        },
        handlePageChange(val) {
            this.currentPage = val
            this.getOutsourceOverview()
        },
        async getOutsourceOverview() {
            const params = {
                "page": this.currentPage,
                "pageSize": this.pageSize,
                "orderRId": this.orderRIdSearch,
                "shoeRId": this.shoeRIdSearch,
                "outsourceStatus": this.outsourceStatusSearch,
            }
            const response = await axios.get(`${this.$apiBaseUrl}/production/productionmanager/getorderoutsourceoverview`, {params})
            this.orderTableData = response.data.result
            console.log(this.orderTableData)
            this.totalRows = response.data.totalLength
        },
		openOutsourceFlow(rowData) {
			const params = {
				"orderId": rowData.orderId,
				"orderRId": rowData.orderRId,
				"orderShoeId": rowData.orderShoeId,
				"shoeRId": rowData.shoeRId,
			}
			const queryString = new URLSearchParams(params).toString();
			const url = `${window.location.origin}/productiongeneral/productionoutsource?${queryString}`
			window.open(url, '_blank')
		},
    },

}
</script>
