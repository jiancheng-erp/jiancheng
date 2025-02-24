<template>

    <el-row :gutter="0">
        <el-col :span="12" :offset="0">
            <h1>全部待处理任务：</h1>
        </el-col>        
    </el-row>
    <el-row :gutter="20">
        <el-col :span="4" :offset="19"><el-input v-model="searchOrder" placeholder="请输入订单号" size="" :suffix-icon="Search" clearable @input="filterData"></el-input>
        </el-col>
    </el-row>
    
    <el-row :gutter="20" style="margin-top: 20px;">
        <el-col :span="24">
            <el-table :data="displayData" style="height: 500px">
                <el-table-column prop="taskName" label="任务名称"></el-table-column>
                <el-table-column prop="orderId" label="订单号"></el-table-column>
                <el-table-column prop="createTime" label="订单创建时间"></el-table-column>
                <el-table-column prop="prevTime" label="前序流程下发时间"></el-table-column>
                <el-table-column prop="prevDepart" label="前序处理部门"></el-table-column>
                <el-table-column prop="prevUser" label="前序处理人"></el-table-column>
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
            searchOrder:"",
            displayData:this.pendingTaskData
        }
    },
    methods: {
        backToAll() {
            this.$emit('backGrid')
        }, 
        filterData() {
            if (!this.searchOrder) {
                this.displayData = this.pendingTaskData
            }
            this.displayData = this.pendingTaskData.filter(task => task.orderId.includes(this.searchOrder));
        }
    }
}
</script>