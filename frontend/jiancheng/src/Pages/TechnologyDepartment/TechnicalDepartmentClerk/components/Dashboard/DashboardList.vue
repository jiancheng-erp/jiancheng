<template><el-row :gutter="0">
        <el-col :span="12" :offset="0">
            <h1>待处理任务：{{ pendingAmount }}</h1>
        </el-col>
    </el-row>
    <el-row :gutter="20" style="margin-top: 20px;">
        <el-col :span="24">
            <el-table :data="pendingTaskData" style="height: 200px" @row-dblclick="handleRowClick">
                <el-table-column prop="taskName" label="任务名称"></el-table-column>
                <el-table-column prop="orderRid" label="订单号"></el-table-column>
                <el-table-column prop="createTime" label="订单创建时间"></el-table-column>
                <el-table-column prop="deadlineTime" label="订单截止时间"></el-table-column>
                <el-table-column prop="customerName" label="客户"></el-table-column>                
                <el-table-column prop="orderShoeCount" label="鞋型数量"></el-table-column>
                <!-- <el-table-column prop="prevTime" label="前序流程下发时间"></el-table-column>
                <el-table-column prop="prevDepart" label="前序处理部门"></el-table-column>
                <el-table-column prop="prevUser" label="前序处理人"></el-table-column> -->

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
            <h1>处理中任务：{{ inprogessAmount }}</h1>
        </el-col>
    </el-row>
    <el-row :gutter="20" style="margin-top: 20px;">
        <el-col :span="24">
            <el-table :data="inProgressTaskData" style="height: 200px" @row-dblclick="handleRowClick">
                <el-table-column prop="taskName" label="任务名称"></el-table-column>
                <el-table-column prop="orderRid" label="订单号"></el-table-column>
                <el-table-column prop="createTime" label="订单创建时间"></el-table-column>
                <el-table-column prop="deadlineTime" label="订单截止时间"></el-table-column>
                <el-table-column prop="customerName" label="客户"></el-table-column>                
                <el-table-column prop="orderShoeCount" label="鞋型数量"></el-table-column>
                
                    <!-- <el-table-column prop="prevTime" label="前序流程下发时间"></el-table-column>
                    <el-table-column prop="prevDepart" label="前序处理部门"></el-table-column>
                    <el-table-column prop="prevUser" label="前序处理人"></el-table-column> -->
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
            inprogessAmount: 0
        }
    },
    watch: {
        pendingTaskData: {
            handler(val) {
                this.pendingAmount = val.length
            },
            immediate: true
        },
        inProgressTaskData: {
            handler(val) {
                this.inprogessAmount = val.length
            },
            immediate: true
        }
    },
    mounted() {
        this.pendingAmount = this.pendingTaskData.length
        this.inprogessAmount = this.inProgressTaskData.length
    },
    methods: {
        displayPending() {
            this.$emit('changeToPend')
        },
        displayProgress() {
            this.$emit('changeToProgress')
        },
        handleRowClick(row) {
            console.log("123123123")
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