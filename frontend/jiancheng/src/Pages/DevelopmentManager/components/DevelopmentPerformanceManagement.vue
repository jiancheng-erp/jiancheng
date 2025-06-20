<template>
    <el-row :gutter="20">
        <el-col :span="24" style="font-size: xx-large; text-align: center">绩效管理</el-col>
    </el-row>
    <el-row :gutter="20" style="margin-bottom: 10px">
        <el-col :span="6">
            <el-input v-model="designerSearchText" placeholder="搜索设计师" clearable @input="fetchDesignerList" />
        </el-col>
        <el-col :span="4">
            <el-date-picker
                v-model="startDateFilter"
                type="date"
                placeholder="开始日期"
                format="YYYY-MM-DD"
                value-format="YYYY-MM-DD"
                style="width: 100%"
                clearable
                @change="handleDateChange('start')"
            />
        </el-col>
        <el-col :span="4">
            <el-date-picker v-model="endDateFilter" type="date" placeholder="结束日期" format="YYYY-MM-DD" value-format="YYYY-MM-DD" style="width: 100%" clearable @change="handleDateChange('end')" />
        </el-col>
        <el-col :span="4">
            <el-date-picker v-model="yearFilter" type="year" placeholder="按年份统计" format="YYYY" value-format="YYYY" style="width: 100%" clearable @change="handleDateChange('year')" />
        </el-col>
        <el-col :span="4">
            <el-date-picker v-model="monthFilter" type="month" placeholder="按月份统计" format="YYYY-MM" value-format="YYYY-MM" style="width: 100%" clearable @change="handleDateChange('month')" />
        </el-col>
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
    <el-row style="margin-top: 10px; font-weight: bold; font-size: 16px; text-align: right">
        <el-col :span="24"> 当前筛选共计业务量：{{ totalSummary.totalBusiness }}， 生产量：{{ totalSummary.totalProduct }} </el-col>
    </el-row>

    <!-- 对话框：鞋型绩效详情 -->
    <el-dialog v-model="dialogVisible" :title="`设计师：${selectedDesigner} 的鞋型使用情况`" width="60%">
        <el-row :gutter="20" style="margin-bottom: 10px">
            <el-col :span="6">
                <el-input v-model="searchText" placeholder="搜索鞋型编号" clearable @input="fetchPerformanceData" />
            </el-col>
            <el-col :span="4">
                <el-date-picker
                    v-model="startDateFilter"
                    type="date"
                    placeholder="开始日期"
                    format="YYYY-MM-DD"
                    value-format="YYYY-MM-DD"
                    style="width: 100%"
                    clearable
                    @change="handleDateChange('start')"
                />
            </el-col>
            <el-col :span="4">
                <el-date-picker
                    v-model="endDateFilter"
                    type="date"
                    placeholder="结束日期"
                    format="YYYY-MM-DD"
                    value-format="YYYY-MM-DD"
                    style="width: 100%"
                    clearable
                    @change="handleDateChange('end')"
                />
            </el-col>
            <el-col :span="4">
                <el-date-picker v-model="yearFilter" type="year" placeholder="按年份统计" format="YYYY" value-format="YYYY" clearable style="width: 100%" @change="handleDateChange('year')" />
            </el-col>
            <el-col :span="4">
                <el-date-picker v-model="monthFilter" type="month" placeholder="按月份统计" format="YYYY-MM" value-format="YYYY-MM" clearable style="width: 100%" @change="handleDateChange('month')" />
            </el-col>
            <el-col :span="24" style="text-align: right; font-weight: bold; line-height: 32px">
                使用订单数：{{ filteredOrderCount.byShoe }}（按鞋型） / {{ filteredOrderCount.byColor }}（按颜色） ，总业务量：{{ filteredOrderSummary.totalBusiness }}，总生产量：{{
                    filteredOrderSummary.totalProduct
                }}
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
            <el-table-column prop="totalOrderCount" label="使用次数（订单数）(按鞋型)" />
            <el-table-column prop="totalOrderCountColor" label="使用次数（按颜色）" />
            <el-table-column prop="totalShoeCountBussiness" label="总业务量" />
            <el-table-column prop="totalShoeCountProduct" label="总生产量" />
        </el-table>

        <el-pagination
            layout="prev, pager, next"
            :total="performanceData.length"
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
            designerSearchText: '',
            designerList: [],
            performanceData: [],
            selectedDesigner: '',
            dialogVisible: false,
            searchText: '',
            currentPage: 1,
            startDateFilter: '',
            endDateFilter: '',
            yearFilter: '',
            monthFilter: ''
        }
    },
    computed: {
        totalSummary() {
            let totalBusiness = 0
            let totalProduct = 0
            for (const designer of this.designerList) {
                totalBusiness += Number(designer.totalShoeCountBussiness || 0)
                totalProduct += Number(designer.totalShoeCountProduct || 0)
            }
            return { totalBusiness, totalProduct }
        },
        paginatedData() {
            const start = (this.currentPage - 1) * 10
            const end = start + 10
            return this.performanceData.slice(start, end)
        },
        filteredOrderCount() {
            let totalByColor = 0
            let totalByShoe = new Set()
            for (const item of this.performanceData) {
                for (const color of item.colors) {
                    for (const order of color.orders) {
                        totalByColor += 1
                        totalByShoe.add(`${item.shoeId}_${order.orderId}`)
                    }
                }
            }
            return { byColor: totalByColor, byShoe: totalByShoe.size }
        },
        filteredOrderSummary() {
            let totalBusiness = 0
            let totalProduct = 0
            for (const item of this.performanceData) {
                for (const color of item.colors) {
                    for (const order of color.orders) {
                        totalBusiness += Number(order.businessAmount || 0)
                        totalProduct += Number(order.productAmount || 0)
                    }
                }
            }
            return { totalBusiness, totalProduct }
        }
    },
    mounted() {
        this.fetchDesignerList()
    },
    methods: {
        handleDateChange(type) {
            if (type === 'start' || type === 'end') {
                this.yearFilter = ''
                this.monthFilter = ''
            } else if (type === 'year' || type === 'month') {
                this.startDateFilter = ''
                this.endDateFilter = ''
            }
            this.fetchDesignerList()
            if (this.dialogVisible) this.fetchPerformanceData()
        },
        async fetchDesignerList() {
            const params = {
                designer: this.designerSearchText ?? '',
                startDate: this.startDateFilter ?? '',
                endDate: this.endDateFilter ?? '',
                year: this.yearFilter ?? '',
                month: this.monthFilter ?? ''
            }
            const res = await axios.get(`${this.$apiBaseUrl}/devproductionorder/getalldesigners`, { params })
            this.designerList = res.data.data
        },
        async openPerformanceDialog(row) {
            this.selectedDesigner = row.designer
            this.dialogVisible = true
            this.searchText = ''
            this.currentPage = 1
            await this.fetchPerformanceData()
        },
        async fetchPerformanceData() {
            const params = {
                designer: this.selectedDesigner,
                startDate: this.startDateFilter || '',
                endDate: this.endDateFilter || '',
                year: this.yearFilter || '',
                month: this.monthFilter || '',
                shoeRid: this.searchText || ''
            }
            const res = await axios.get(`${this.$apiBaseUrl}/devproductionorder/getallshoeswithadesigner`, { params })
            this.performanceData = res.data.data || []
        },
        handlePageChange(page) {
            this.currentPage = page
        }
    }
}
</script>
