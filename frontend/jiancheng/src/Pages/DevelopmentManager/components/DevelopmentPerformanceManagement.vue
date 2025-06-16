<template>
    <el-row :gutter="20">
        <el-col :span="24" style="font-size: xx-large; text-align: center">绩效管理</el-col>
    </el-row>

    <el-table :data="designerList" border stripe style="width: 100%">
        <el-table-column prop="designer" label="设计师" />
        <el-table-column prop="department" label="所属部门" />
        <el-table-column prop="totalOrderCount" label="鞋型总使用次数" />
        <el-table-column label="操作" width="160">
            <template #default="scope">
                <el-button type="primary" size="small" @click="openPerformanceDialog(scope.row)">查看绩效</el-button>
            </template>
        </el-table-column>
    </el-table>

    <!-- 对话框：鞋型绩效详情 -->
    <el-dialog v-model="dialogVisible" :title="`设计师：${selectedDesigner} 的鞋型使用情况`" width="60%">
        <el-row :gutter="20" style="margin-bottom: 10px">
            <el-col :span="10">
                <el-input v-model="searchText" placeholder="搜索鞋型编号" clearable />
            </el-col>
            <el-col :span="8">
                <el-date-picker
                    v-model="dateRangeFilter"
                    type="daterange"
                    start-placeholder="开始日期"
                    end-placeholder="结束日期"
                    format="YYYY-MM-DD"
                    value-format="YYYY-MM-DD"
                    clearable
                    style="width: 100%"
                />
            </el-col>
            <el-col :span="6" style="text-align: right; font-weight: bold; line-height: 32px"> 总订单数：{{ filteredOrderCount }} </el-col>
        </el-row>

        <el-table :data="paginatedData" border stripe :pagination="false">
            <el-table-column type="expand">
                <template #default="props">
                    <el-table :data="filteredOrders(props.row.orders)" border size="small">
                        <el-table-column prop="orderRid" label="订单编号" />
                        <el-table-column prop="customerId" label="客户ID" />
                        <el-table-column prop="startDate" label="开始时间" />
                        <el-table-column prop="endDate" label="结束时间" />
                    </el-table>
                </template>
            </el-table-column>
            <el-table-column prop="shoeRid" label="鞋型编号" />
            <el-table-column label="使用次数（订单数）">
                <template #default="scope">
                    {{ filteredOrders(scope.row.orders).length }}
                </template>
            </el-table-column>
        </el-table>

        <el-pagination
            layout="prev, pager, next"
            :total="filteredPerformanceData.length"
            :page-size="10"
            :current-page="currentPage"
            @current-change="handlePageChange"
            background
            style="margin-top: 15px; text-align: right"
        />

        <template #footer>
            <span><el-button @click="dialogVisible = false">关闭</el-button></span>
        </template>
    </el-dialog>
</template>
<script>
import axios from 'axios'

export default {
    data() {
        return {
            designerList: [],
            allPerformanceDataMap: {}, // 缓存每位设计师数据
            performanceData: [], // 当前选中设计师数据
            selectedDesigner: '',
            dialogVisible: false,
            searchText: '',
            currentPage: 1,
            startDateFilter: '',
            dateRangeFilter: []
        }
    },
    computed: {
        filteredPerformanceData() {
            return this.performanceData.filter((item) => {
                const matchShoeRid = !this.searchText || (item.shoeRid && item.shoeRid.includes(this.searchText))
                const matchOrderCount = this.filteredOrders(item.orders).length > 0
                return matchShoeRid && matchOrderCount
            })
        },

        paginatedData() {
            const start = (this.currentPage - 1) * 10
            const end = start + 10
            return this.filteredPerformanceData.slice(start, end)
        },
        filteredOrderCount() {
            return this.filteredPerformanceData.reduce((sum, item) => {
                return sum + this.filteredOrders(item.orders).length
            }, 0)
        }
    },
    mounted() {
        this.loadDesignerList()
    },
    methods: {
        async loadDesignerList() {
            const res = await axios.get(`${this.$apiBaseUrl}/devproductionorder/getalldesigners`)
            this.designerList = res.data.data
        },
        async openPerformanceDialog(row) {
            this.selectedDesigner = row.designer
            this.dialogVisible = true
            this.searchText = ''
            this.currentPage = 1

            // 缓存查询结果，避免重复请求
            if (!this.allPerformanceDataMap[row.designer]) {
                const res = await axios.get(`${this.$apiBaseUrl}/devproductionorder/getallshoeswithadesigner`, {
                    params: { designer: row.designer }
                })
                this.allPerformanceDataMap[row.designer] = res.data.data
            }

            this.performanceData = this.allPerformanceDataMap[row.designer]
        },
        handlePageChange(page) {
            this.currentPage = page
        },
        filteredOrders(orders) {
            if (!this.dateRangeFilter || this.dateRangeFilter.length !== 2) return orders
            const [startDate, endDate] = this.dateRangeFilter

            return orders.filter((o) => {
                return o.startDate && o.startDate >= startDate && o.startDate <= endDate
            })
        }
    }
}
</script>
