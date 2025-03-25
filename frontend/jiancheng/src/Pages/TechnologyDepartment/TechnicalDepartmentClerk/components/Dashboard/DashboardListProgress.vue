<template>
    <el-row :gutter="0">
        <el-col :span="12" :offset="0">
            <h1>全部处理中任务：{{ inprogressAmount }}</h1>
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
    props: ['inProgressTaskData'],
    data() {
        return {
            Search,
            searchOrder: "",
            displayData: this.inProgressTaskData,
            inprogressAmount: 0
        }
    },
    watch: {
        inProgressTaskData: {
            handler: function (val) {
                this.displayData = val;
                this.inprogressAmount = val.length;
            },
            deep: true
        }
    },
    mounted() {
        this.displayData = this.inProgressTaskData
        this.inprogressAmount = this.inProgressTaskData.length
    },
    methods: {
        backToAll() {
            this.$emit('backGrid')
        },
        filterData() {
            if (!this.searchOrder) {
                this.displayData = this.inProgressTaskData
            }
            this.displayData = this.inProgressTaskData.filter(task => task.orderRid.toLowerCase().includes(this.searchOrder.toLowerCase()));
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