<template>
    <el-row :gutter="0">
        <el-col :span="12" :offset="0">
            <h1>全部处理中任务：{{ inprogressAmount }}</h1>
        </el-col>
    </el-row>
    <el-row :gutter="20" style="margin-top: 20px;">
        <el-col :span="4" :offset="0"><el-button size="default" @click="backToAll">返回全部任务</el-button></el-col>    
        <el-col :span="4" :offset="15"><el-input v-model="searchOrder" placeholder="请输入订单号" :suffix-icon="Search" clearable @input="filterData"></el-input>
        </el-col>
    </el-row>
    <el-row :gutter="20" style="margin-top: 20px;">
        <el-col :span="24">
            <el-table :data="displayData" style="height: 500px" @row-click="handleRowClick">
                <el-table-column prop="taskName" label="任务名称"></el-table-column>
                <el-table-column prop="orderRId" label="订单号"></el-table-column>
                <el-table-column prop="createTime" label="订单创建时间"></el-table-column>
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
        this.inprogressAmount = this.inProgressTaskData.length
    },
    methods: {
        backToAll() {
            this.$emit('backToList')
        }, 
        filterData() {
            if (!this.searchOrder) {
                this.displayData = this.inProgressTaskData
            }
            this.displayData = this.inProgressTaskData.filter(task => task.orderRId.toLowerCase().includes(this.searchOrder.toLowerCase()));
        },
        refreshTaskData() {
            this.$emit('getAllData')
        },
        handleRowClick(row) {
            let url;
            if (row.taskName === '二次采购订单创建') {
                url = `${window.location.origin}/logistics/secondpurchase/orderid=${row.orderId}`;
            }
            if (url) {
                window.callRefreshTaskData = function () {
                    this.refreshTaskData();
                }.bind(this);
                window.open(url, '_blank');
            }
        },
    }
}
</script>