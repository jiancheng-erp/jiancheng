<template>

    <el-row :gutter="0">
        <el-col :span="12" :offset="0">
            <h1>全部待处理任务：{{ pendingAmount }}</h1>
        </el-col>        
    </el-row>
    <el-row :gutter="20" style="margin-top: 20px;">
        <el-col :span="4" :offset="0"><el-button size="default" @click="backToAll">返回全部任务</el-button></el-col>    
        <el-col :span="4" :offset="11"><el-input v-model="searchOrder" placeholder="请输入订单号" size="" :suffix-icon="Search" clearable @input="filterData"></el-input>
        </el-col>
        <el-col :span="4" :offset="0"><el-input v-model="searchShoe" placeholder="请输入鞋型号" size="" :suffix-icon="Search" clearable @input="filterData"></el-input>
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
            searchShoe:"",
            displayData:this.pendingTaskData,
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
            this.$emit('backToList')
        }, 
        filterData() {
            this.displayData = this.pendingTaskData.filter(task => {
                return task.orderRid.toLowerCase().includes(this.searchOrder.toLowerCase()) && task.shoeRId.toLowerCase().includes(this.searchShoe.toLowerCase());
            });
            this.pendingAmount = this.displayData.length;
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