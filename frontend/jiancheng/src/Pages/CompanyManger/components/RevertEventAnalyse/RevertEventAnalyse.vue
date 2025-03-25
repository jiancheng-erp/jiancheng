<template>
    <div class="content">
        <el-row :gutter="16" style="margin-top: 20px; width: 100%">
            <el-col :span="4" :offset="0" style="white-space: nowrap">
                订单号筛选：
                <el-input v-model="orderRIdSearch" placeholder="请输入订单号" clearable />
            </el-col>
            <el-col :span="4" :offset="2" style="white-space: nowrap">
                责任部门筛选:
                <el-select v-model="responsibleDepartmentSearch" placeholder="请选择" style="width: 100%">
                    <el-option v-for="item in departmentOptions" :key="item.value" :label="item.label"
                        :value="item.value"></el-option>
                </el-select>
            </el-col>
            <el-col :span="4" :offset="2" style="white-space: nowrap">
                发起部门筛选:
                <el-select v-model="initialDepartmentSearch" placeholder="请选择" style="width: 100%">
                    <el-option v-for="item in departmentOptions" :key="item.value" :label="item.label"
                        :value="item.value"></el-option>
                </el-select>
            </el-col>
            <el-col :span="4" :offset="2" style="white-space: nowrap">
                退回月份筛选:
                <el-date-picker v-model="monthFilter" type="month" placeholder="选择月份" format="YYYY-MM"
                    value-format="YYYY-MM" style="width: 100%" clearable />
            </el-col>

        </el-row>
        <el-table :data="pagedTableData" style="width: 100%; margin-bottom: 20px; height: 540px" border>
            <el-table-column prop="orderRid" label="订单编号" sortable />
            <el-table-column prop="revertEventTime" label="退回时间" />
            <el-table-column prop="revertEventReason" label="退回原因" />
            <el-table-column prop="initialingDepartment" label="发起部门" />
            <el-table-column prop="responsibleDepartment" label="责任部门" />
        </el-table>
        <el-row :gutter="20" style="justify-content: end; width: 100%">
            <el-pagination @size-change="changeCurrentPageSize" @current-change="changeCurrentPage"
                :current-page="currentPage" :page-sizes="[10, 20, 30, 40]" :page-size="currentPageSize"
                layout="total, sizes, prev, pager, next, jumper" :total="currentTotalRows" />
        </el-row>
    </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import axios from 'axios'
export default {
    data() {
        return {
            orderRIdSearch: '',
            currentPage: 1,
            currentPageSize: 10,
            currentTotalRows: 0,
            currentTableData: [],
            currentSelectionRows: [],
            orderShoeStatus: '全部',
            departmentOptions: [
                { value: '全部', label: '全部' },
                { value: '技术部', label: '技术部' },
                { value: '物控部', label: '物控部' },
                { value: '用量填写', label: '用量填写' },
                { value: '开发部', label: '开发部' }
            ],
            initialDepartmentSearch: '全部',
            responsibleDepartmentSearch: '全部',
            Download: 'el-icon-download',
            monthFilter: '',
        }
    },
    computed: {
        filteredTableData() {
            return this.currentTableData.filter(order => {
                const matchOrderRid = this.orderRIdSearch
                    ? order.orderRid?.includes(this.orderRIdSearch)
                    : true
                const matchInitialDepartment = this.initialDepartmentSearch !== '全部'
                    ? order.initialingDepartment?.includes(this.initialDepartmentSearch)
                    : true
                const matchResponsibleDepartment = this.responsibleDepartmentSearch !== '全部'
                    ? order.responsibleDepartment?.includes(this.responsibleDepartmentSearch)
                    : true
                const matchMonth = this.monthFilter
                ? order.revertEventTime?.startsWith(this.monthFilter)
                : true
                return matchOrderRid && matchInitialDepartment && matchResponsibleDepartment && matchMonth
            })
        },
        pagedTableData() {
            const start = (this.currentPage - 1) * this.currentPageSize
            const end = start + this.currentPageSize
            return this.filteredTableData.slice(start, end)
        }
    },
    watch: {
        filteredTableData: {
            handler(val) {
                this.currentTotalRows = val.length
            },
            immediate: true
        }
    },
    mounted() {
        this.getTableData()
    },
    methods: {
        async getTableData() {
            const res = await axios.get(`${this.$apiBaseUrl}/headmanager/getallrevertevent`,)
            this.currentTableData = res.data
            this.currentTotalRows = res.data.length
        },
        changeCurrentPage(val) {
            this.currentPage = val
        },
        changeCurrentPageSize(val) {
            this.currentPageSize = val
            this.currentPage = 1
        }
    }

}

</script>