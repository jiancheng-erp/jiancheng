<template>
    <el-row :gutter="20">
        <el-col :span="24" :offset="0" style="font-size: xx-large; text-align: center;">任务看板</el-col>
    </el-row>

    <el-row :gutter="0">
        <el-col :span="5" :offset="20">
            <el-button-group>
                <el-button size="default" @click="changeToGrid" :icon="Grid">卡片显示</el-button>
                <el-button size="default" @click="changeToList" :icon="Memo">列表显示</el-button>
            </el-button-group>

        </el-col>


    </el-row>
    <component :is="currentDash" :pendingTaskData="textData" :inProgressTaskData="textData2" @backGrid="changeToGrid"
    @changeToPend="changeToPend" @changeToProgress="changeToProgress">
    </component>
</template>
<script>
import { Grid, Memo } from '@element-plus/icons-vue'
import DashboardGrid from './Dashboard/DashboardGrid.vue';
import DashboardList from './Dashboard/DashboardList.vue'
import DashboardPend from './Dashboard/DashboardListPend.vue'
import DashboardProgress from './Dashboard/DashboardListProgress.vue'

export default {
    components: {
        DashboardGrid,
        DashboardList,
        DashboardPend,
        DashboardProgress
    },
    data() {
        return {
            Grid,
            Memo,
            currentDash: 'DashboardGrid',
            textData: [{
                taskName: "一次BOM填写",
                orderId: "K24-024 2111620",
                createTime: "2024-06-10",
                prevTime: "2024-06-10 18:00:00",
                prevDepart: "开发部",
                prevUser: "XXX"
            },
            {
                taskName: "一次BOM填写",
                orderId: "K24-025 2111622",
                createTime: "2024-06-10",
                prevTime: "2024-06-10 18:00:00",
                prevDepart: "开发部",
                prevUser: "XXX"
            },
            {
                taskName: "一次BOM填写",
                orderId: "K24-021 2111620",
                createTime: "2024-06-10",
                prevTime: "2024-06-10 18:00:00",
                prevDepart: "开发部",
                prevUser: "XXX"
            },
            {
                taskName: "二次BOM填写",
                orderId: "K24-021 2111620",
                createTime: "2024-06-10",
                prevTime: "2024-06-10 18:00:00",
                prevDepart: "技术部",
                prevUser: "XXX"
            },
            {
                taskName: "一次BOM填写",
                orderId: "K24-021 2111620",
                createTime: "2024-06-10",
                prevTime: "2024-06-10 18:00:00",
                prevDepart: "开发部",
                prevUser: "XXX"
            },
            {
                taskName: "二次BOM填写",
                orderId: "K24-021 2111620",
                createTime: "2024-06-10",
                prevTime: "2024-06-10 18:00:00",
                prevDepart: "技术部",
                prevUser: "XXX"
            },
            ],
            textData2: [{
                taskName: "一次BOM填写",
                orderId: "K24-021 2111628",
                createTime: "2024-06-10",
                prevTime: "2024-06-10 18:00:00",
                prevDepart: "开发部",
                prevUser: "XXX"
            },
            {
                taskName: "二次BOM填写",
                orderId: "K24-021 2111620",
                createTime: "2024-06-10",
                prevTime: "2024-06-10 18:00:00",
                prevDepart: "技术部",
                prevUser: "XXX"
            },
            ],
        }
    },
    methods: {
        changeToGrid() {
            this.currentDash = 'DashboardGrid'
        },
        changeToList() {
            this.currentDash = 'DashboardList'
        },
        changeToPend() {
            this.currentDash = 'DashboardPend'
        },
        changeToProgress() {
            console.log(this.currentDash)
            this.currentDash = 'DashboardProgress'
        }

    }
}
</script>
<style></style>