<template>
    <el-container>
        <el-header height="">
            <AllHeader></AllHeader>
        </el-header>
        <el-main>
            <el-row :gutter="20" style="text-align: center;">
                <el-col :span="24" :offset="0" style="font-size: xx-large; text-align: center;">{{ `${props.teams}工序填报`
                    }}</el-col>
            </el-row>
            <el-row :gutter="20">
                <el-col :span="24" :offset="0">
                    <el-descriptions title="鞋型号信息" :column="3" border>
                        <el-descriptions-item label="订单号">{{ orderInfo.orderRId }}</el-descriptions-item>
                        <el-descriptions-item label="鞋型号">{{ orderInfo.shoeRId }}</el-descriptions-item>
                        <el-descriptions-item label="客户型号">{{ orderInfo.customerProductName }}</el-descriptions-item>
                        <el-descriptions-item label="工段开始日期">{{ orderInfo.cuttingStartDate }}</el-descriptions-item>
                        <el-descriptions-item label="工段结束日期">{{ orderInfo.cuttingEndDate }}</el-descriptions-item>
                        <el-descriptions-item label="工价单状态">{{ statusName }}</el-descriptions-item>
                    </el-descriptions>
                </el-col>
            </el-row>
            <el-row v-if="statusName === '被驳回'" :gutter="20">
                <span>驳回原因：{{ rejectionReason }}</span>
            </el-row>
            <el-row :gutter="20">
                <el-col :span="24">
                    <el-tabs v-model="currentTab" tab-position="top">
                        <el-tab-pane v-for="item in panes" :key="item" :label="item" :name="item">
                            <PriceReportTable ref="childComp"
                                :tableData="priceReportInfo[item]['tableData']" :procedureInfo="procedureInfo"
                                :readOnly="readOnly" :team="currentTab"
                                @update-items="handleUpdateItems" />
                        </el-tab-pane>
                    </el-tabs>
                </el-col>
            </el-row>
            <el-row :gutter="20">
                <el-col>
                    <el-button-group>
                        <el-button type="info" @click="saveAsTemplate">保存为模板</el-button>
                        <el-button v-if="!readOnly" type="info" @click="loadTemplate">加载模板</el-button>
                        <!-- <el-button type="primary" @click="">下载为Excel</el-button> -->
                    </el-button-group>
                </el-col>
            </el-row>
            <el-row :gutter="20">
                <el-col :offset="20">
                    <el-button-group>
                        <el-button v-if="!readOnly" type="primary" @click="handleSaveData">保存</el-button>
                        <el-button v-if="!readOnly" type="success" @click="handleSubmit">提交</el-button>
                        <el-button type="info" @click="generateProductionForm">生产流程卡</el-button>
                    </el-button-group>
                </el-col>

            </el-row>
        </el-main>
    </el-container>
</template>

<script setup>
import { onMounted, ref, reactive, getCurrentInstance, watch } from 'vue';
import axios from 'axios';
import PriceReportTable from './PriceReportTable.vue';
import AllHeader from '@/components/AllHeader.vue';
import { ElMessage, ElMessageBox } from 'element-plus';
const priceReportInfo = reactive({})
const procedureInfo = ref({})
const proxy = getCurrentInstance()
const apiBaseUrl = proxy.appContext.config.globalProperties.$apiBaseUrl
const props = defineProps(["orderId", "orderShoeId", "teams"])
const orderInfo = ref({})
const readOnly = ref(true)
const panes = ref([])
const teamsArr = ref([])
const statusName = ref('')
const rejectionReason = ref('')
const currentTab = ref('')
const childComp = ref(null)

onMounted(async () => {
    setReportPanes()
    await getPriceReportDetail()
    getOrderInfo()
    getAllProcedures()
})

const handleUpdateItems = (items) => {
    priceReportInfo[currentTab.value]['tableData'] = items
};

const setReportPanes = () => {
    teamsArr.value = props.teams.split(",")
    teamsArr.value.forEach(team => {
        panes.value.push(team)
        priceReportInfo[team] = { "tableData": [], reportId: null }
    })
    currentTab.value = panes.value[0]
}

const generateProductionForm = async () => {
    window.open(
        `${apiBaseUrl}/production/downloadproductionform?orderShoeId=${orderInfo.value.orderShoeId}&reportId=${priceReportInfo[currentTab.value].reportId}`
    )
}

const getOrderInfo = async () => {
    let params = { "orderId": props.orderId, "orderShoeId": props.orderShoeId }
    let response = await axios.get(`${apiBaseUrl}/production/productionmanager/getorderinfo`, { params })
    orderInfo.value = response.data
    params = { "orderShoeId": props.orderShoeId }
    response = await axios.get(`${apiBaseUrl}/production/getproductioninfo`, { params })
    orderInfo.value = { ...orderInfo.value, ...response.data }
}

const getAllProcedures = async () => {
    const params = { teams: props.teams }
    const response = await axios.get(`${apiBaseUrl}/production/getallprocedures`, { params })
    procedureInfo.value = response.data
}

const getPriceReportDetail = async () => {
    for (const team of teamsArr.value) {
        const params = {
            "orderShoeId": props.orderShoeId,
            "team": team
        }
        const response = await axios.get(`${apiBaseUrl}/production/getpricereportdetailbyordershoeid`, { params })
        priceReportInfo[team]["tableData"] = response.data.detail
        priceReportInfo[team]["reportId"] = response.data.metaData.reportId
        statusName.value = response.data.metaData.statusName
        rejectionReason.value = response.data.metaData.rejectionReason
    }
    if (statusName.value === '已审批' || statusName.value === '已提交') {
        readOnly.value = true
    }
    else {
        readOnly.value = false
    }
}

const handleSaveData = async () => {
    try {
        for (const [key, info] of Object.entries(priceReportInfo)) {
            await axios.post(`${apiBaseUrl}/production/storepricereportdetail`,
                { reportId: info.reportId, newData: info.tableData })
        }
        ElMessage.success("保存成功")
    }
    catch (error) {
        console.log(error)
        ElMessage.error("保存失败")
    }
}

const handleSubmit = async () => {
    ElMessageBox.confirm('确认提交工序吗?', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
    }).then(async () => {
        try {
            await handleSaveData()
            let idArr = []
            for (const [key, info] of Object.entries(priceReportInfo)) {
                idArr.push(info.reportId)
            }
            await axios.post(`${apiBaseUrl}/production/submitpricereport`,
                { "orderId": props.orderId, "orderShoeId": props.orderShoeId, "reportIdArr": idArr })
            ElMessage.success("提交成功")
            await getPriceReportDetail()
        }
        catch (error) {
            console.log(error)
            ElMessage.error("提交失败")
        }
    }).catch(() => {
        ElMessage.info("已取消提交")
    });

}

const saveAsTemplate = async () => {
    ElMessageBox.confirm('确认保存模板吗?', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
    }).then(async () => {
        try {
            await axios.post(`${apiBaseUrl}/production/storepricereportdetail`,
                { reportId: priceReportInfo[currentTab.value].reportId, newData: priceReportInfo[currentTab.value].tableData })
            await axios.put(`${apiBaseUrl}/production/savetemplate`,
                { "reportId": priceReportInfo[currentTab.value].reportId, "shoeId": orderInfo.value.shoeId, "team": currentTab.value, "reportRows": priceReportInfo[currentTab.value].tableData })
            ElMessage.success("保存成功")
        }
        catch (error) {
            console.log(error)
            ElMessage.error("保存失败")
        }
    }).catch(() => {
        ElMessage.info("已取消保存")
    });

}

const loadTemplate = async () => {
    ElMessageBox.confirm('确认加载模板吗?', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
    }).then(async () => {
        try {
            let params = { "shoeId": orderInfo.value.shoeId, "team": currentTab.value }
            let response = await axios.get(`${apiBaseUrl}/production/loadtemplate`, { params })
            priceReportInfo[currentTab.value].tableData = response.data

            ElMessage.success("加载成功")
        }
        catch (error) {
            ElMessage.error(error)
        }
    }).catch(() => {
        ElMessage.info("已取消加载")
    });

}
</script>
