<template>
    <el-row :gutter="20">
        <el-col class="u-page-title" :span="24" :offset="0">一次采购入库</el-col>
    </el-row>
    <component :is="currentDash" :pendingTaskData="textData" :inProgressTaskData="textData2" @backToList="changeToList"
    @changeToPend="changeToPend" @changeToProgress="changeToProgress">
    </component>
</template>
<script>
import { Grid, Memo } from '@element-plus/icons-vue'
import FirstOrderList from './FirstWarehousing/FirstWarehousingList.vue'
import FirstOrderPend from './FirstWarehousing/FirstWarehousingListPend.vue'
import FirstOrderProgress from './FirstWarehousing/FirstWarehousingListProgress.vue'

export default {
    components: {
        FirstOrderList,
        FirstOrderPend,
        FirstOrderProgress
    },
    data() {
        return {
            Grid,
            Memo,
            currentDash: 'FirstOrderList',
            textData: [{
                taskName: "一次采购入库",
                orderId: "K24-024 2111620",
                createTime: "2024-06-10",
                prevTime: "2024-06-10 18:00:00",
                prevDepart: "物控部",
                prevUser: "XXX"
            },
            {
                taskName: "一次采购入库",
                orderId: "K24-025 2111622",
                createTime: "2024-06-10",
                prevTime: "2024-06-10 18:00:00",
                prevDepart: "物控部",
                prevUser: "XXX"
            },
            {
                taskName: "一次采购入库",
                orderId: "K24-021 2111620",
                createTime: "2024-06-10",
                prevTime: "2024-06-10 18:00:00",
                prevDepart: "物控部",
                prevUser: "XXX"
            },
            {
                taskName: "一次采购入库",
                orderId: "K24-021 2111620",
                createTime: "2024-06-10",
                prevTime: "2024-06-10 18:00:00",
                prevDepart: "物控部",
                prevUser: "XXX"
            },
            {
                taskName: "一次采购入库",
                orderId: "K24-021 2111620",
                createTime: "2024-06-10",
                prevTime: "2024-06-10 18:00:00",
                prevDepart: "物控部",
                prevUser: "XXX"
            },
            {
                taskName: "一次采购入库",
                orderId: "K24-021 2111620",
                createTime: "2024-06-10",
                prevTime: "2024-06-10 18:00:00",
                prevDepart: "物控部",
                prevUser: "XXX"
            },
            ],
            textData2: [{
                taskName: "一次采购入库",
                orderId: "K24-021 2111628",
                createTime: "2024-06-10",
                prevTime: "2024-06-10 18:00:00",
                prevDepart: "物控部",
                prevUser: "XXX"
            },
            {
                taskName: "一次采购入库",
                orderId: "K24-021 2111620",
                createTime: "2024-06-10",
                prevTime: "2024-06-10 18:00:00",
                prevDepart: "物控部",
                prevUser: "XXX"
            },
            ],
        }
    },
    methods: {
        changeToList() {
            this.currentDash = 'FirstOrderList'
        },
        changeToPend() {
            this.currentDash = 'FirstOrderPend'
        },
        changeToProgress() {
            console.log(this.currentDash)
            this.currentDash = 'FirstOrderProgress'
        }

    }
}
</script>
<style scoped></style>