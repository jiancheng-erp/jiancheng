<template>

    <el-row :gutter="0">
        <el-col :span="12" :offset="0">
            <h1>全部待处理任务：</h1>
        </el-col>        
    </el-row>
    <el-row :gutter="20" style="margin-top: 20px;">
        <el-col :span="4" :offset="0"><el-button size="default" @click="backToAll">返回全部任务</el-button></el-col>    
        <el-col :span="4" :offset="15"><el-input v-model="searchOrder" placeholder="请输入订单号" size="" :suffix-icon="Search" clearable @input="filterData"></el-input>
        </el-col>
    </el-row>
    
    <el-row :gutter="20" style="margin-top: 20px;">
        <el-col :span="24">
            <el-table :data="displayData" style="height: 500px" @row-click="handleRowClick">
                <el-table-column prop="taskName" label="任务名称"></el-table-column>
                <el-table-column prop="orderRid" label="订单号"></el-table-column>
                <el-table-column prop="createTime" label="订单创建时间"></el-table-column>
                <el-table-column prop="deadlineTime" label="订单截止时间"></el-table-column>
                <el-table-column prop="customerName" label="客户"></el-table-column>                
                <el-table-column prop="shoeRId" label="工厂型号"></el-table-column>
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
            this.$emit('backToList')
        }, 
        filterData() {
            if (!this.searchOrder) {
                this.displayData = this.pendingTaskData
            }
            this.displayData = this.pendingTaskData.filter(task => task.orderId.includes(this.searchOrder));
        },
        handleRowClick(row) {
            let url;
            if (row.taskName === '工艺单创建') {
                url = `${window.location.origin}/processsheet/orderid=${row.orderId}`;
            }
            if (url) {
                window.open(url, '_blank');
            }
        },
    }
}
</script>