<!-- eslint-disable vue/valid-v-for -->
<template><el-row :gutter="0">
        <el-col :span="12" :offset="0">
            <h1>待处理任务：</h1>
        </el-col>
    </el-row>
    <el-row :gutter="20" style="margin-top: 20px;">
        <el-col :span="6" :offset="0" v-for="colIndex in 4">
            <el-card shadow="always" :body-style="{ padding: '10px' }" v-if="getPendingItem(colIndex)"
                @click="openNewWindow(getPendingItem(colIndex))">
                <template #header>
                    <div style="text-align: center;">
                        {{ getPendingItem(colIndex).taskName }}
                    </div>
                </template>
                <div>订单号：{{ getPendingItem(colIndex).orderRid }}</div>
                <div>订单创建时间：{{ getPendingItem(colIndex).createTime }}</div>
                <div>订单截止时间：{{ getPendingItem(colIndex).deadlineTime }}</div>
                <div>客户：{{ getPendingItem(colIndex).customerName }}</div>
                <div>工厂型号：{{ getPendingItem(colIndex).shoeRId }}</div>
            </el-card>

        </el-col>
    </el-row>
    <el-row :gutter="0" style="margin-top: 20px;">
        <el-col :span="2" :offset="22">
            <el-button size="large" @click="displayPending">查看更多</el-button>

        </el-col>
    </el-row>
    <el-row :gutter="0">
        <el-col :span="12" :offset="0">
            <h1>处理中任务：</h1>
        </el-col>
    </el-row>
    <el-row :gutter="20" style="margin-top: 20px;">
        <el-col :span="6" :offset="0" v-for="colIndex in 4">
            <el-card shadow="always" :body-style="{ padding: '10px' }" v-if="getinProgressItem(colIndex)"
                @click="openNewWindow(getinProgressItem(colIndex))">
                <template #header>
                    <div style="text-align: center;">
                        <span>{{ getinProgressItem(colIndex).taskName }}</span>
                    </div>
                </template>
                <div>订单号：{{ getinProgressItem(colIndex).orderRid }}</div>
                <div>订单创建时间：{{ getinProgressItem(colIndex).createTime }}</div>
                <div>订单截止时间：{{ getinProgressItem(colIndex).deadlineTime }}</div>
                <div>客户：{{ getinProgressItem(colIndex).customerName }}</div>
                <div>工厂型号：{{ getinProgressItem(colIndex).shoeRId }}</div>
            </el-card>

        </el-col>
    </el-row>
    <el-row :gutter="0" style="margin-top: 20px;">
        <el-col :span="2" :offset="22">
            <el-button size="large" @click="displayProgress">查看更多</el-button>

        </el-col>
    </el-row></template>
<script>
export default {
    props: ['pendingTaskData', 'inProgressTaskData'],
    data() {
        return {

        }
    },
    methods: {
        getPendingItem(colIndex) {
            const index = colIndex - 1
            return index <= this.pendingTaskData.length ? this.pendingTaskData[index] : null
        },
        getinProgressItem(colIndex) {
            const index = colIndex - 1
            return index < this.inProgressTaskData.length ? this.inProgressTaskData[index] : null
        },
        displayPending() {
            this.$emit('changeToPend')
        },
        displayProgress() {
            this.$emit('changeToProgress')
        },
        openNewWindow(task) {
            let url = task['taskURL']
            window.open(url, '_blank');
        }
    }
}
</script>