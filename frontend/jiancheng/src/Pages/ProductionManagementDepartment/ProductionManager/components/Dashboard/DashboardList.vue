<template><el-row :gutter="0">
    <el-col :span="12" :offset="0">
        <h1>待处理任务：</h1>
    </el-col>
</el-row>
<el-row class="u-mt-5" :gutter="20">
    <el-col :span="24">
        <el-table class="u-h-200" :data="pendingTaskData">
            <el-table-column prop="taskName" label="任务名称"></el-table-column>
            <el-table-column prop="orderId" label="订单号"></el-table-column>
            <el-table-column prop="createTime" label="订单创建时间"></el-table-column>
            <el-table-column prop="prevTime" label="前序流程下发时间"></el-table-column>
            <el-table-column prop="prevDepart" label="前序处理部门"></el-table-column>
            <el-table-column prop="prevUser" label="前序处理人"></el-table-column>
        </el-table>

    </el-col>
</el-row>
<el-row class="u-mt-5" :gutter="0">
        <el-col :span="2" :offset="22">
            <el-button size="large" @click="displayPending">查看更多</el-button>

        </el-col>
    </el-row>
<el-row class="u-mt-5" :gutter="0">
    <el-col :span="12" :offset="0">
        <h1>处理中任务：</h1>
    </el-col>
</el-row>
<el-row class="u-mt-5" :gutter="20">
    <el-col :span="24">
        <el-table class="u-h-200" :data="inProgressTaskData">
            <el-table-column prop="taskName" label="任务名称"></el-table-column>
            <el-table-column prop="orderId" label="订单号"></el-table-column>
            <el-table-column prop="createTime" label="订单创建时间"></el-table-column>
            <el-table-column prop="prevTime" label="前序流程下发时间"></el-table-column>
            <el-table-column prop="prevDepart" label="前序处理部门"></el-table-column>
            <el-table-column prop="prevUser" label="前序处理人"></el-table-column>
        </el-table>

    </el-col>
</el-row>
<el-row class="u-mt-5" :gutter="0">
        <el-col :span="2" :offset="22">
            <el-button size="large" @click="displayProgress">查看更多</el-button>

        </el-col>
    </el-row>
</template>

<script>
export default {
    props: ['pendingTaskData', 'inProgressTaskData'],
    methods: {
        displayPending(){
            this.$emit('changeToPend')
        },
        displayProgress(){
            this.$emit('changeToProgress')
        }
    }
}
</script>