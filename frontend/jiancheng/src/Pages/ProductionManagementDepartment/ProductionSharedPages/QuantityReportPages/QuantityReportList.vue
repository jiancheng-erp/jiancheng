<template>
    <el-container>
        <el-header height="">
            <AllHeader></AllHeader>
        </el-header>
        <el-main>
            <el-row class="u-text-center" :gutter="20">
                <el-col class="u-page-title" :span="24" :offset="0">{{`${props.team}数量填报`}}</el-col>
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
                    <el-descriptions title="鞋型信息" :column="3" border>
                        <el-descriptions-item label="订单号">{{ orderInfo.orderRId }}</el-descriptions-item>
                        <el-descriptions-item label="鞋型号">{{ orderInfo.shoeRId }}</el-descriptions-item>
                        <el-descriptions-item label="客户型号">{{ orderInfo.customerProductName }}</el-descriptions-item>
                        <el-descriptions-item label="订单开始日期">{{ orderInfo.orderStartDate }}</el-descriptions-item>
                        <el-descriptions-item label="订单结束日期">{{ orderInfo.orderEndDate }}</el-descriptions-item>
                        <!-- <el-descriptions-item label="工段开始日期">{{ orderInfo.cuttingStartDate }}</el-descriptions-item>
                        <el-descriptions-item label="工段结束日期">{{ orderInfo.cuttingEndDate }}</el-descriptions-item> -->
                    </el-descriptions>
                </el-col>
            </el-row>
            <el-table :data="taskData" :default-sort="{ prop: 'date', order: 'ascending' }" border stripe
                max-height="500">
                <el-table-column prop="creationDate" label="创建日期" sortable></el-table-column>
                <el-table-column prop="submissionDate" label="提交日期" sortable></el-table-column>
                <el-table-column prop="status" label="状态">
                    <template v-slot="scope">
                        <el-tooltip v-if="scope.row.status === '被驳回'" effect="dark"
                            :content="scope.row.rejectionReason">
                            <span class="rejected">{{ scope.row.status }}</span>
                        </el-tooltip>
                        <span v-else>{{ scope.row.status }}</span>
                    </template>
                </el-table-column>
                <el-table-column label="操作">
                    <template #default="scope">
                        <el-button v-if="scope.row.status === '已提交' || scope.row.status === '已审批'" type="success"
                            @click="openReportDialog(scope.row, false)">查看</el-button>
                        <el-button-group v-else-if="scope.row.status === '未提交' || scope.row.status === '被驳回'">
                            <el-button type="primary" class="block-button"
                                @click="openReportDialog(scope.row, true)">编辑</el-button>
                            <el-button type="warning" class="block-button"
                                @click="handleSubmit(scope.row)">提交</el-button>
                            <el-button type="danger" class="block-button"
                                @click="handleDelete(scope.row, scope.$index)">删除</el-button>
                        </el-button-group>
                    </template>
                </el-table-column>
            </el-table>
            <el-row>
                <el-button type="primary" @click="handleCreateReport">
                    <span>新建生产数量单</span>
                </el-button>
            </el-row>
            <el-dialog :title="`${orderInfo.shoeRId}数量单`" v-model="isReportDialogOpen" width="80%">
                <QuantityReportTable v-model:tableData="quantityTableData" :orderShoeId="props.orderShoeId"
                    :editable="editable" />
                <template #footer>
                    <el-button @click="isReportDialogOpen = false">取消</el-button>
                    <el-button v-if="editable" type="primary" @click="handleSaveData">保存</el-button>
                </template>
            </el-dialog>
        </el-main>
    </el-container>
</template>

<script setup>
import { onMounted, ref, watch, getCurrentInstance } from 'vue';
import QuantityReportTable from './QuantityReportTable.vue';
import AllHeader from '@/components/AllHeader.vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import axios from 'axios'
import { exportTableToExcel } from '../../utils';
const isReportDialogOpen = ref(false)
const props = defineProps(["orderId", "orderShoeId", "team"])
const taskData = ref([])
const currentReport = ref({})
const dateValue = ref('')
const createdDates = ref(new Set())
const proxy = getCurrentInstance()
const apiBaseUrl = proxy.appContext.config.globalProperties.$apiBaseUrl
const editable = ref(false)
const orderInfo = ref({})
const createReportVis = ref(false)
const quantityTableData = ref([])


onMounted(async () => {
    getOrderInfo()
    getAllQuantityReports()
})

const getOrderInfo = async () => {
    let params = { "orderId": props.orderId, "orderShoeId": props.orderShoeId }
    let response = await axios.get(`${apiBaseUrl}/production/productionmanager/getorderinfo`, { params })
    orderInfo.value = response.data
    console.log(orderInfo.value)
    params = { "orderShoeId": props.orderShoeId }
    response = await axios.get(`${apiBaseUrl}/production/getproductioninfo`, { params })
    orderInfo.value = { ...orderInfo.value, ...response.data }
}

const getAllQuantityReports = async () => {
    // get all quantity report for this order_shoe_id
    let params = {
        "orderShoeId": props.orderShoeId,
        "team": props.team
    }
    const response1 = await axios.get(`${apiBaseUrl}/production/getallquantityreports`, { params })
    taskData.value = response1.data
}

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

const disabledDate = (time) => {
    let startDate = new Date(orderInfo.value.orderStartDate)
    startDate.setDate(startDate.getDate() - 1);
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
        "team": props.team
    }
    await axios.post(`${apiBaseUrl}/production/createquantityreport`, body)
    ElMessage({ type: 'success', message: '添加成功!' })
    getAllQuantityReports()
    createReportVis.value = false
}
const openReportDialog = async (row, editableVal) => {
    currentReport.value = row
    editable.value = editableVal
    let teamId = -1
    if (props.team == "裁断")
        teamId = 0
    else if (props.team == "针车预备")
        teamId = 1
    else if (props.team == "针车")
        teamId = 2
    else if (props.team == "成型")
        teamId = 3
    let params = { "reportId": currentReport.value.reportId, "team": teamId }
    let response = await axios.get(`${apiBaseUrl}/production/getquantityreportdetail`, { params })
    quantityTableData.value = []
    response.data.forEach(row => {
        row["toDateAmount"] = 0
        row.productionLinesAmount.forEach(amountObj => {
            row["toDateAmount"] += amountObj.reportAmount
        })
        quantityTableData.value.push(row)
    })
    isReportDialogOpen.value = true
}

const handleSubmit = async (rowData) => {
    try {
        await axios.patch(`${apiBaseUrl}/production/submitquantityreport`, { "reportId": rowData.reportId })
        ElMessage.success("提交成功")
    }
    catch(error) {
        console.log(error)
        ElMessage.error("提交失败")
    }
    getAllQuantityReports()
}

const handleCreateReport = () => {
    createReportVis.value = true
}

const handleDelete = (row, index) => {
    ElMessageBox.confirm('确定删除此行吗？', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
    }).then(async () => {
        const params = { "reportId": row.reportId }
        await axios.delete(`${apiBaseUrl}/production/deletequantityreport`, { params })
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
const handleSaveData = async () => {
    const data = {
        "reportId": currentReport.value.reportId,
        "data": quantityTableData.value,
    }
    try {
        await axios.put(`${apiBaseUrl}/production/editquantityreportdetail`, data)
        ElMessage.success("保存成功")
    }
    catch (error) {
        ElMessage.error('保存失败')
    }
    isReportDialogOpen.value = false
}
const handleExport = () => {
    exportTableToExcel(tableData.value, columns.value, currentTitle.value + ".xlsx")
}
</script>
<style scoped></style>
