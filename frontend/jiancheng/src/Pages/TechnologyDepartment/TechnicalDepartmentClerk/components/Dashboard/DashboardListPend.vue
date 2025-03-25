<template>

    <el-row :gutter="0">
        <el-col :span="12" :offset="0">
            <h1>全部待处理任务：{{ pendingAmount }}</h1>
        </el-col>
    </el-row>
    <el-row :gutter="20">
        <el-col :span="4" :offset="19"><el-input v-model="searchOrder" placeholder="请输入订单号" size=""
                :suffix-icon="Search" clearable @input="filterData"></el-input>
        </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px;">
        <el-col :span="24">
            <el-table :data="displayData" style="height: 500px" @row-dblclick="handleRowClick">
                <el-table-column prop="taskName" label="任务名称"></el-table-column>
                <el-table-column prop="orderRid" label="订单号"></el-table-column>
                <el-table-column prop="createTime" label="订单创建时间"></el-table-column>
                <el-table-column prop="deadlineTime" label="订单截止时间"></el-table-column>
                <!-- <el-table-column prop="prevTime" label="前序流程下发时间"></el-table-column>
                <el-table-column prop="prevDepart" label="前序处理部门"></el-table-column>
                <el-table-column prop="prevUser" label="前序处理人"></el-table-column> -->
            </el-table>

        </el-col>
    </el-row>
</template>

<script>
import { Search } from '@element-plus/icons-vue'
export default {
    props: ['pendingTaskData'],
    data() {
        return {
            Search,
            searchOrder: "",
            displayData: this.pendingTaskData,
            pendingAmount: 0
        }
    },
    watch: {
        pendingTaskData: {
            handler: function (val) {
                this.displayData = val;
                this.pendingAmount = val.length;
            },
            deep: true
        }
    },
    mounted() {
        this.displayData = this.pendingTaskData
        this.pendingAmount = this.pendingTaskData.length
    },
    methods: {
        backToAll() {
            this.$emit('backGrid')
        },
        filterData() {
            if (!this.searchOrder) {
                this.displayData = this.pendingTaskData
            }
            this.displayData = this.pendingTaskData.filter(task => task.orderRid.toLowerCase().includes(this.searchOrder.toLowerCase()));
        },
        handleRowClick(row) {
            let url;
            if (row.taskName === '一次BOM填写') {
                url = `${window.location.origin}/technicalclerk/firstBOM/orderid=${row.orderId}`;
            } else if (row.taskName === '二次BOM填写') {
                url = `${window.location.origin}/technicalclerk/secondBOM/orderid=${row.orderId}`;
            }
            if (url) {
                window.open(url, '_blank');
            }
        },
    }
}
</script>