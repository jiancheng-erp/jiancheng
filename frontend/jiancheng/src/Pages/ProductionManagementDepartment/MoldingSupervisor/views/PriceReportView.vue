<template>
    <el-container>
        <el-header height="">
            <AllHeader></AllHeader>
        </el-header>
        <el-main>
            <el-row :gutter="20" style="text-align: center;">
                <el-col :span="24" :offset="0" style="font-size: xx-large; text-align: center;">成型工价填报</el-col>
            </el-row>
            <el-row :gutter="20">
                <el-col :span="24" :offset="0">
                    <el-descriptions title="订单信息" :column="3" border>
                        <el-descriptions-item label="订单编号">{{ props.orderRId }}</el-descriptions-item>
                        <el-descriptions-item label="订单创建时间">{{ props.createTime }}</el-descriptions-item>
                        <el-descriptions-item label="客户">{{ props.customerName }}</el-descriptions-item>
                    </el-descriptions></el-col>
            </el-row>
            <el-table :data="taskData" border>
                <el-table-column prop="shoeRId" label="鞋型号"></el-table-column>
                <el-table-column prop="date" label="提交日期"></el-table-column>
                <el-table-column prop="statusName" label="状态"></el-table-column>
                <el-table-column label="操作">
                    <template #default="scope">
                        <el-button-group v-if="scope.row.statusName === '未提交工价单'">
                            <el-button type="primary" @click="handleEdit(scope.row)">编辑</el-button>
                            <el-button type="success"
                                @click="openPreviewDialog(scope.row)">预览</el-button>
                            <el-button type="warning"
                                @click="handleSubmit(scope.row)">提交</el-button>
                        </el-button-group>
                        <el-button-group v-if="scope.row.statusName === '已提交工价单'">
                            <el-button type="success" @click="openPreviewDialog(scope.row)">预览</el-button>
                        </el-button-group>
                    </template>
                </el-table-column>
            </el-table>
            <div v-if="createVis">
                <PriceReportCreator :currentRowData="currentRowData" :handleClose="handleClose" />
            </div>
            <div v-else-if="previewVis">
                <PreviewReportPage :currentRowData="currentRowData" :handleClose="handleClose" />
            </div>
        </el-main>
    </el-container>
</template>

<script setup>
import { onMounted, ref } from 'vue';
import axios from 'axios';
import PriceReportCreator from '../components/LaborPriceReport/PriceReportCreator.vue'
import PreviewReportPage from '../components/LaborPriceReport/PreviewReportPage.vue';
import AllHeader from '@/components/AllHeader.vue';
const createVis = ref(false)
const previewVis = ref(false)
const currentTitle = ref('')
const currentRowData = ref({})
const props = defineProps({
    'orderId': Number,
    'orderRId': String,
    'createTime': String,
    'customerName': String,
    'taskName': String
})
const taskData = ref([])
onMounted(async () => {
    const params = {
        "orderId": props.orderId,
        "teams": "成型"
    }
    const response = await axios.get("http://localhost:8000/production/getallordershoespricereports", { params })
    response.data.forEach(element => {
        {
            if (element.status == 0) {
                element["statusName"] = "未提交工价单"
            }
            else if (element.status == 1) {
                element["statusName"] = "已提交工价单"
            } else {
                element["statusName"] = "已审核工价单"
            }
            taskData.value.push(element)
        }
    });
})

const handleEdit = (rowData) => {
    createVis.value = true
    currentRowData.value = rowData
}
const openPreviewDialog = (rowData) => {
    currentRowData.value = rowData
    previewVis.value = true
}
const handleSubmit = async (rowData) => {
    console.log(rowData)
    const response = await axios.post("http://localhost:8000/production/submitpricereport", 
    { "orderId": props.orderId, "orderShoeId": rowData.orderShoeId, "reportIdArr": [rowData.reportId] })
    console.log(response)
    window.location.reload()
}
const handleClose = (option) => {
    if (option === 0) createVis.value = false
    else if (option === 1) previewVis.value = false
}
</script>
