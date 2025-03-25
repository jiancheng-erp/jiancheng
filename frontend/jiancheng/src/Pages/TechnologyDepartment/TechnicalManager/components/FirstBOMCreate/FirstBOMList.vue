<template><el-row :gutter="0">
    <el-col :span="12" :offset="0">
        <h1>待处理任务：{{ pendingAmount }}</h1>
    </el-col>
</el-row>
<el-row :gutter="20" style="margin-top: 20px;">
    <el-col :span="24">
        <el-table :data="pendingTaskData" style="height: 200px" @row-click="handleRowClick">
            <el-table-column prop="taskName" label="任务名称"></el-table-column>
            <el-table-column prop="orderRid" label="订单号"></el-table-column>
            <el-table-column prop="createTime" label="订单创建时间"></el-table-column>
            <el-table-column prop="customerName" label="客户"></el-table-column>                
            <el-table-column prop="shoeRId" label="工厂型号"></el-table-column>
        </el-table>

    </el-col>
</el-row>
<el-row :gutter="0" style="margin-top: 20px;">
        <el-col :span="2" :offset="22">
            <el-button size="large" @click="displayPending">查看更多</el-button>

        </el-col>
    </el-row>
<el-row :gutter="0" style="margin-top: 20px;">
    <el-col :span="12" :offset="0">
        <h1>处理中任务：{{ inprogressAmount }}</h1>
    </el-col>
</el-row>
<el-row :gutter="20" style="margin-top: 20px;">
    <el-col :span="24">
        <el-table :data="inProgressTaskData" style="height: 200px" @row-click="handleRowClick">
            <el-table-column prop="taskName" label="任务名称"></el-table-column>
            <el-table-column prop="orderRid" label="订单号"></el-table-column>
            <el-table-column prop="createTime" label="订单创建时间"></el-table-column>
            <el-table-column prop="deadlineTime" label="订单截止时间"></el-table-column>
            <el-table-column prop="customerName" label="客户"></el-table-column>                
            <el-table-column prop="shoeRId" label="工厂型号"></el-table-column>
        </el-table>

    </el-col>
</el-row>
<el-row :gutter="0" style="margin-top: 20px;">
        <el-col :span="2" :offset="22">
            <el-button size="large" @click="displayProgress">查看更多</el-button>

        </el-col>
    </el-row>
</template>

<script>
export default {
    props: ['pendingTaskData', 'inProgressTaskData'],
    data() {
        return {
            pendingAmount: 0,
            inprogressAmount: 0
        }
    },
    watch: {
        pendingTaskData: {
            handler: function (val) {
                this.pendingAmount = val.length
            },
            deep: true
        },
        inProgressTaskData: {
            handler: function (val) {
                this.inprogressAmount = val.length
            },
            deep: true
        }
    },
    mounted() {
        this.pendingAmount = this.pendingTaskData.length
        this.inprogressAmount = this.inProgressTaskData.length
    },
    methods: {
        displayPending(){
            this.$emit('changeToPend')
        },
        displayProgress(){
            this.$emit('changeToProgress')
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
    },

}
</script>