<template>
    <el-container>
        <el-header height="">
            <AllHeader></AllHeader>
        </el-header>
        <el-main>
            <el-row :gutter="20" style="text-align: center;">
                <el-col :span="24" :offset="0" style="font-size: xx-large; text-align: center;">裁断与批皮数量填报</el-col>
            </el-row>
            <el-row>
                <el-button type="primary" @click="handleCreateReport">
                    <span>新建生产数量单</span>
                </el-button>
            </el-row>
            <el-dialog title="新建生产数量单" v-model="createReportVis">
                <el-date-picker v-model="dateValue" type="date" :disabled-date="disabledDate" value-format="YYYY-MM-DD"
                    placeholder="选择日期" />
                <template #footer>
                    <span>
                        <el-button type="primary" @click="handleConfirmCreate">保存</el-button>
                    </span>
                </template>
            </el-dialog>
            <el-row :gutter="20">
                <el-col :span="24" :offset="0">
                    <el-descriptions title="订单信息" :column="3" border>
                        <el-descriptions-item label="订单编号">{{ props.orderRId }}</el-descriptions-item>
                        <el-descriptions-item label="订单创建时间">{{ props.createTime }}</el-descriptions-item>
                        <el-descriptions-item label="客户">{{ props.customerName }}</el-descriptions-item>
                        <el-descriptions-item label="鞋型号">{{ props.shoeRId }}</el-descriptions-item>
                    </el-descriptions></el-col>
            </el-row>
            <hr />
            <el-table :data="taskData" :default-sort="{ prop: 'date', order: 'ascending' }" border>
                <el-table-column prop="creationDate" label="日期" sortable></el-table-column>
                <el-table-column prop="status" label="状态"></el-table-column>
                <el-table-column label="操作">
                    <template #default="scope">
                        <el-button v-if="scope.row.status === '已提交生产数量单'" type="success"
                            @click="openPreviewDialog(scope.row)">查看</el-button>
                        <el-button-group v-else-if="scope.row.status === '未提交生产数量单'">
                            <el-button type="primary" class="block-button"
                                @click="handleEdit(scope.row)">编辑</el-button>
                            <el-button type="success" class="block-button"
                                @click="openPreviewDialog(scope.row)">查看</el-button>
                            <el-button type="warning" class="block-button"
                                @click="handleSubmit(scope.row)">提交</el-button>
                            <el-button type="danger" class="block-button"
                                @click="handleDelete(scope.row, scope.$index)">删除</el-button>
                        </el-button-group>
                    </template>
                </el-table-column>
            </el-table>
            <div v-if="createVis">
                <AmountReportCreator :currentReport="currentReport" :orderShoeId="props.orderShoeId"
                    :handleClose="handleClose" />
            </div>
            <div v-else-if="previewVis">
                <PreviewQuantityReport :shoeRId="props.shoeRId" :currentReport="currentReport" :handleClose="handleClose"/>
            </div>
        </el-main>
    </el-container>
</template>

<script setup>
import { onMounted, ref, watch } from 'vue';
import AmountReportCreator from '../components/AmountProduced/AmountReportCreator.vue'
import PreviewQuantityReport from '../components/AmountProduced/PreviewQuantityReport.vue';
import AllHeader from '@/components/AllHeader.vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import axios from 'axios'
const createVis = ref(false)
const createReportVis = ref(false)
const previewVis = ref(false)
const props = defineProps([
    "orderId", "orderRId", "createTime", 
    "customerName", "orderShoeId", "shoeRId"
])
const taskData = ref([])
const currentReport = ref({})
const dateValue = ref('')
const createdDates = ref(new Set())


onMounted(async () => {
    // get all quantity report for this order_shoe_id
    let params = {
        "orderShoeId": props.orderShoeId,
        "team": "裁断"
    }
    const response1 = await axios.get("http://localhost:8000/production/getallquantityreports", { params })
    taskData.value = response1.data
    taskData.value.forEach(row => {
        if (row.status == 0) {
            row.status = "未提交生产数量单"
        }
        else if (row.status == 1) {
            row.status = "已提交生产数量单"
        }
        else if (row.status == 2) {
            row.status = "已审核生产数量单"
        }
    })
})

const dateFormatter = (input) => {
    const date = new Date(input);
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const formattedDate = `${year}-${month}-${day}`;
    return formattedDate
}

watch(taskData, () => {
    createdDates.value = new Set(taskData.value.map(e => e.creationDate));
}, { deep: true })

const handleEdit = (rowData) => {
    createVis.value = true
    currentReport.value = rowData
}
const disabledDate = (time) => {
    const startDate = new Date(props.createTime)
    const endDate = new Date()
    return time.getTime() < startDate || time.getTime() > endDate.getTime() || createdDates.value.has(dateFormatter(time));
}
const handleConfirmCreate = async () => {
    if (dateValue.value.length === 0) {
        ElMessage({ type: 'warning', message: '未选择一个日期!' })
        return
    }
    if (createdDates.value.has(dateValue.value)) {
        ElMessage({ type: 'warning', message: '已有该日期的报告!' })
        return
    }
    let body = {
        "orderShoeId": props.orderShoeId,
        "creationDate": dateValue.value,
        "team": "裁断"
    }
    await axios.post("http://localhost:8000/production/createquantityreport", body)
    ElMessage({ type: 'success', message: '添加成功!' })
    taskData.value.push({
        reportId: response.data.reportId,
        date: dateValue.value,
        status: "未提交生产数量表"
    })
    body = {
        reportId: response.data.reportId,
        orderShoeId: props.orderShoeId
    }
    await axios.post("http://localhost:8000/production/createquantityreportdetail", body)
    window.location.reload()
}
const handleCreateReport = () => {
    createReportVis.value = true
}

const openPreviewDialog = (rowData) => {
    currentReport.value = rowData
    previewVis.value = true
}
const handleSubmit = async (rowData) => {
    console.log(rowData)
    await axios.patch("http://localhost:8000/production/submitquantityreport", {"reportId": rowData.reportId})
    window.location.reload()
}

const handleDelete = (row, index) => {
    ElMessageBox.confirm('确定删除此行吗？', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
    }).then(async () => {
        const params = {"reportId": row.reportId}
        await axios.delete("http://localhost:8000/production/deletequantityreport", {params})
        taskData.value.splice(index, 1)
        ElMessage({
            type: 'success',
            message: '删除成功!'
        });
    }).catch(() => {
        ElMessage({
            type: 'info',
            message: '已取消删除'
        });
    });
}
const handleClose = (option) => {
    if (option === 0) createVis.value = false
    else if (option === 1) previewVis.value = false
}
</script>
