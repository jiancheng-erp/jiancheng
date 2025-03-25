<template>

    <el-row :gutter="0">
        <el-col :span="12" :offset="0">
            <h1>全部待处理任务：{{ pendingAmount }}</h1>
        </el-col>
    </el-row>
    <el-row :gutter="20">
        <el-col :span="4"><el-input v-model="searchOrder" placeholder="请输入订单号"
                :suffix-icon="Search" clearable @change="filterData"></el-input>
        </el-col>
        <el-col :span="4">
            <el-input v-model="searchShoe" placeholder="请输入工厂型号"
                :suffix-icon="Search" clearable @change="filterDataByShoe">
            </el-input>
        </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px;">
        <el-col :span="24">
            <el-table :data="displayData" style="height: 500px" @row-dblclick="handleRowClick">
                <el-table-column prop="taskName" label="任务名称"></el-table-column>
                <el-table-column prop="orderRid" label="订单号"></el-table-column>
                <el-table-column prop="shoeRId" label="工厂型号"></el-table-column>
                <el-table-column prop="createTime" label="订单创建时间"></el-table-column>
                <el-table-column prop="deadlineTime" label="订单截止时间"></el-table-column>
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
            searchShoe: "",
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
        filterDataByShoe() {
            if (!this.searchShoe) {
                this.displayData = this.pendingTaskData
            }
            this.displayData = this.pendingTaskData.filter(task => task.shoeRId.toLowerCase().includes(this.searchShoe.toLowerCase()));
        },
        handleRowClick(row) {
            let url = row['taskURL']
            window.open(url, '_blank');
        },
    }
}
</script>