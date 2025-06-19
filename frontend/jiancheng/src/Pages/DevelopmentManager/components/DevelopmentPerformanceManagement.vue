<template>
    <el-row :gutter="20">
        <el-col :span="24" style="font-size: xx-large; text-align: center">绩效管理</el-col>
    </el-row>

    <el-table :data="designerList" border stripe style="width: 100%">
        <el-table-column prop="designer" label="设计师" />
        <el-table-column prop="department" label="所属部门" />
        <el-table-column prop="totalOrderCount" label="鞋型总使用次数(订单)" />
        <el-table-column prop="totalShoeCountBussiness" label="鞋型总业务量" />
        <el-table-column prop="totalShoeCountProduct" label="鞋型总生产量" />
        <el-table-column label="操作" width="160">
            <template #default="scope">
                <el-button type="primary" size="small" @click="openPerformanceDialog(scope.row)">查看绩效</el-button>
            </template>
        </el-table-column>
    </el-table>

    <!-- 对话框：鞋型绩效详情 -->
    <el-dialog v-model="dialogVisible" :title="`设计师：${selectedDesigner} 的鞋型使用情况`" width="60%">
        <el-row :gutter="20" style="margin-bottom: 10px">
            <el-col :span="6">
                <el-input v-model="searchText" placeholder="搜索鞋型编号" clearable />
            </el-col>
            <el-col :span="4">
                <el-date-picker v-model="startDateFilter" type="date" placeholder="开始日期" format="YYYY-MM-DD" value-format="YYYY-MM-DD" style="width: 100%" clearable />
            </el-col>
            <el-col :span="4">
                <el-date-picker v-model="endDateFilter" type="date" placeholder="结束日期" format="YYYY-MM-DD" value-format="YYYY-MM-DD" style="width: 100%" clearable />
            </el-col>
            <el-col :span="4">
                <el-date-picker v-model="yearFilter" type="year" placeholder="按年份统计" format="YYYY" value-format="YYYY" clearable style="width: 100%" />
            </el-col>

            <el-col :span="4">
                <el-date-picker v-model="monthFilter" type="month" placeholder="按月份统计" format="YYYY-MM" value-format="YYYY-MM" clearable style="width: 100%" />
            </el-col>
            <el-col :span="8" style="text-align: right; font-weight: bold; line-height: 32px">
                使用订单数：{{ filteredOrderCount.byShoe }}（按鞋型） / {{ filteredOrderCount.byColor }}（按颜色）
            </el-col>
        </el-row>

        <el-table :data="paginatedData" border stripe>
            <el-table-column type="expand">
                <template #default="props">
                    <div v-for="color in props.row.colors" :key="color.shoeTypeId" style="margin-bottom: 10px">
                        <div style="font-weight: bold">颜色：{{ color.colorName }}</div>
                        <el-table :data="color.orders" size="small" border>
                            <el-table-column prop="orderRid" label="订单编号" />
                            <el-table-column prop="customerId" label="客户ID" />
                            <el-table-column prop="startDate" label="开始时间" />
                            <el-table-column prop="endDate" label="结束时间" />
                            <el-table-column prop="businessAmount" label="业务数量" />
                            <el-table-column prop="productAmount" label="生产数量" />
                        </el-table>
                    </div>
                </template>
            </el-table-column>
            <el-table-column prop="shoeRid" label="鞋型编号" />
            <el-table-column prop="totalOrderCount" label="使用次数（订单数）(按鞋型)"> </el-table-column>
            <el-table-column prop="totalOrderCountColor" label="使用次数（按颜色）" />
            <el-table-column prop="totalShoeCountBussiness" label="总业务量" />
            <el-table-column prop="totalShoeCountProduct" label="总生产量" />
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
            endDateFilter: '',
            yearFilter: '',
            monthFilter: '',
            dateRangeFilter: []
        }
    },
    computed: {
        filteredPerformanceData() {
            return this.performanceData
                .map((item) => {
                    const filteredColors = item.colors
                        .map((color) => ({
                            ...color,
                            orders: this.filteredOrders(color.orders)
                        }))
                        .filter((color) => color.orders.length > 0)

                    if ((!this.searchText || item.shoeRid.includes(this.searchText)) && filteredColors.length > 0) {
                        return {
                            ...item,
                            colors: filteredColors
                        }
                    }
                    return null
                })
                .filter(Boolean)
        },

        paginatedData() {
            const start = (this.currentPage - 1) * 10
            const end = start + 10
            return this.filteredPerformanceData.slice(start, end)
        },

        filteredOrderCount() {
            let totalByColor = 0
            let totalByShoe = new Set()

            for (const item of this.filteredPerformanceData) {
                for (const color of item.colors) {
                    for (const order of color.orders) {
                        totalByColor += 1
                        totalByShoe.add(`${item.shoeId}_${order.orderId}`)
                    }
                }
            }

            return {
                byColor: totalByColor,
                byShoe: totalByShoe.size
            }
        }
    },
    watch: {
        startDateFilter(val) {
            if (val) {
                this.yearFilter = ''
                this.monthFilter = ''
            }
        },
        endDateFilter(val) {
            if (val) {
                this.yearFilter = ''
                this.monthFilter = ''
            }
        },
        yearFilter(val) {
            if (val) {
                this.startDateFilter = ''
                this.endDateFilter = ''
                this.monthFilter = ''
            }
        },
        monthFilter(val) {
            if (val) {
                this.startDateFilter = ''
                this.endDateFilter = ''
                this.yearFilter = ''
            }
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
            const year = this.yearFilter
            const month = this.monthFilter
            const start = this.startDateFilter
            const end = this.endDateFilter || new Date().toISOString().slice(0, 10)

            return orders.filter((o) => {
                if (year && (!o.startDate || !o.startDate.startsWith(year))) return false
                if (month && (!o.startDate || !o.startDate.startsWith(month))) return false
                if (start && o.startDate < start) return false
                if (end && o.startDate > end) return false
                return true
            })
        }
    }
}
</script>
