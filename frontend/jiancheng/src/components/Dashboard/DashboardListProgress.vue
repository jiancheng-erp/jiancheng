<template>
    <el-row :gutter="0">
        <el-col :span="12" :offset="0">
            <h1>全部处理中任务：</h1>
        </el-col>
    </el-row>
    <el-row :gutter="20">
        <el-col :span="4">
            <el-input v-model="searchOrder" placeholder="请输入订单号"
                :suffix-icon="Search" clearable @input="filterData">
            </el-input>
        </el-col>
        <el-col :span="4">
            <el-input v-model="searchShoe" placeholder="请输入工厂型号"
                :suffix-icon="Search" clearable @input="filterDataByShoe">
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
    props: ['inProgressTaskData'],
    data() {
        return {
            Search,
            searchOrder: "",
            searchShoe: "",
            displayData: this.inProgressTaskData
        }
    },
    methods: {
        backToAll() {
            this.$emit('backGrid')
        },
        filterData() {
            if (!this.searchOrder) {
                this.displayData = this.inProgressTaskData
            }
            this.displayData = this.inProgressTaskData.filter(task => task.orderRid.includes(this.searchOrder));
        },
        filterDataByShoe() {
            if (!this.searchShoe) {
                this.displayData = this.inProgressTaskData
            }
            this.displayData = this.inProgressTaskData.filter(task => task.shoeRId.toLowerCase().includes(this.searchShoe.toLowerCase()));
        },
        handleRowClick(row) {
            let url = row['taskURL']
            window.open(url, '_blank');
        },
    }
}
</script>