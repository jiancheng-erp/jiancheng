<template>
    <el-container>
        <el-header>
            <AllHeader></AllHeader>
        </el-header>
        <el-container>
            <el-main>
                <el-row :gutter="0">
                    <el-col :span="24" :offset="0">
                        <el-descriptions title="" :column="3" border>
                            <el-descriptions-item label="订单编号" align="center">{{
                                orderData.orderRid
                            }}</el-descriptions-item>
                            <el-descriptions-item label="客户订单" align="center">
                                {{ orderData.orderCid }}
                            </el-descriptions-item>
                            <el-descriptions-item label="客户信息" align="center">{{
                                orderData.customerInfo
                            }}</el-descriptions-item>
                            <el-descriptions-item label="订单周期" align="center">{{
                                orderData.dateInfo
                            }}</el-descriptions-item>
                            <el-descriptions-item label="配码类型" align="center">{{
                                orderData.batchInfoTypeName
                            }}</el-descriptions-item>
                            <el-descriptions-item label="订单业务员" align="center">
                                {{ orderData.orderStaffName }}
                            </el-descriptions-item>
                        </el-descriptions>
                    </el-col>
                </el-row>
                <el-table
                    :data="orderShoeData"
                    border
                    stripe
                    height="550"
                    :row-key="
                        (row) => {
                            return `${row.orderShoeId}`
                        }
                    "
                    :default-expand-all="true"
                    :header-row-style="tableHeaderStyle"
                    style="margin-top: 20px"
                >
                    <el-table-column type="expand">
                        <template #default="props">
                            <el-table
                                :data="props.row.orderShoeTypes"
                                border
                                :row-key="
                                    (row) => {
                                        return `${row.orderShoeTypeId}`
                                    }
                                "
                                :default-expand-all="true"
                                :header-row-style="tableHeaderStyle"
                            >
                                <el-table-column type="expand">
                                    <template #default="scope">
                                        <el-table :data="scope.row.shoeTypeBatchInfoList" :header-row-style="tableHeaderStyle">
                                            <el-table-column type="index"></el-table-column>
                                            <el-table-column
                                                prop="packagingInfoName"
                                                label="配码名称"
                                                width="180"
                                            />
                                            <el-table-column
                                                v-for="col in Object.keys(
                                                    attrMappingToRatio
                                                ).filter((key) => batchInfoType[key] != null)"
                                                :prop="attrMappingToRatio[col]"
                                                :label="batchInfoType[col]"
                                                width="60"
                                            ></el-table-column>
                                            <el-table-column
                                                prop="totalQuantityRatio"
                                                label="对/件"
                                                width="240"
                                            />
                                            <el-table-column
                                                prop="unitPerRatio"
                                                label="件数"
                                            />
                                        </el-table>
                                    </template>
                                </el-table-column>
                                <el-table-column
                                    prop="shoeTypeColorName"
                                    label="中文颜色"
                                    width="90"
                                />
                                <el-table-column
                                    prop="customerColorName"
                                    label="英文颜色"
                                    width="90"
                                />
                                <el-table-column
                                    v-for="col in Object.keys(attrMappingToAmount).filter(
                                        (key) => batchInfoType[key] != null
                                    )"
                                    :prop="`shoeTypeBatchData.${attrMappingToAmount[col]}`"
                                    :label="batchInfoType[col]"
                                    width="60"
                                ></el-table-column>
                                <el-table-column
                                    prop="shoeTypeBatchData.totalAmount"
                                    label="总数量"
                                    width="120"
                                />
                                <el-table-column label="金额" width="120">
                                    <template #default="scope">
                                        <el-input
                                            size="small"
                                            controls-position="right"
                                            @change="updateValue(scope.row)"
                                            v-model.lazy="scope.row.shoeTypeBatchData.unitPrice"
                                            :disabled="priceChangeNotAllowed"
                                        >
                                        </el-input>
                                    </template>
                                </el-table-column>
                                <el-table-column label="金额单位">
                                    <template #default="scope">
                                        <el-input
                                            size="small"
                                            controls-position="right"
                                            @change="updateCurrencyValue(scope.row)"
                                            v-model="scope.row.shoeTypeBatchData.currencyType"
                                            :disabled="priceChangeNotAllowed"
                                        >
                                        </el-input>
                                    </template>
                                </el-table-column>
                                <el-table-column
                                    prop="shoeTypeBatchData.totalPrice"
                                    label="总金额"
                                />
                                <el-table-column label="鞋型">
                                    <template #default="scope">
                                        <el-image
                                            :src="imagerUrl(scope.row.shoeTypeImgUrl)"
                                            style="width: 150px; height: 100px"
                                            v-if="scope.row.shoeTypeImgUrl"
                                        ></el-image>
                                        <span v-else>暂无图片数据</span>
                                    </template>
                                </el-table-column>
                            </el-table>
                        </template>
                    </el-table-column>
                    <el-table-column prop="shoeRid" label="鞋型编号" sortable />
                    <el-table-column prop="shoeCid" label="客户鞋型编号" sortable />
                    <el-table-column prop="currentStatus" label="鞋型状态" />
                    <el-table-column label="备注">
                        <template #default="scope">
                            <el-button
                                v-if="!scope.row.orderShoeRemarkExist"
                                type="primary"
                                size="default"
                                @click="openRemarkDialog(scope.row)"
                                style="margin-left: 20px"
                                >添加备注
                            </el-button>

                            <el-text v-if="scope.row.orderShoeRemarkExist"  style="display: inline-block;">{{
                                scope.row.orderShoeRemarkRep
                            }}</el-text>
                            <el-button
                                v-if="scope.row.orderShoeRemarkExist"
                                type="warning"
                                size="default"
                                @click="openEditRemarkDialog(scope.row)"
                                style="margin-left: 20px; margin-top: -20px;"
                            >
                                编辑备注
                            </el-button>
                        </template>
                    </el-table-column>
                </el-table>

                <span>
                    <el-button type="primary" @click="saveFormData" v-if="orderData.orderStatus === 7">保存数据</el-button>
                    <el-button type="primary" @click="showMessage" v-if="orderData.orderStatus === 7">完成审批</el-button>
                </span>
            </el-main>
        </el-container>
    </el-container>
    <el-dialog title="鞋型备注" v-model="remarkDialogVis" width="50%">
        <el-form>
            <el-form-item label="工艺备注">
                <el-input type="textarea" :rows="2" v-model="remarkForm.technicalRemark" :maxlength="255"></el-input>
            </el-form-item>

            <el-form-item label="材料备注">
                <el-input type="textarea" :rows="2" v-model="remarkForm.materialRemark" :maxlength="255"></el-input>
            </el-form-item>
        </el-form>

        <template #footer>
            <span>
                <el-button @click="remarkDialogVis = false">取消</el-button>

                <el-button type="primary" @click="submitRemarkForm">提交备注</el-button>
            </span>
        </template>
    </el-dialog>
</template>

<script setup>
import AllHeader from '@/components/AllHeader.vue'
import axios from 'axios'
import { onMounted, reactive, ref } from 'vue'
import { getCurrentInstance } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

const $api_baseUrl = getCurrentInstance().appContext.config.globalProperties.$apiBaseUrl

const { orderId } = defineProps(['orderId'])
let orderData = ref({})
let orderShoeData = ref([])
let priceChangeNotAllowed = ref(false)
let remarkDialogVis = ref(false)
let orderShoeTypeIdToUnitPrice = reactive({})
let orderShoeTypeIdToCurrencyType = reactive({})
let batchInfoType = reactive({})
let attrMappingToRatio = reactive({
    size34Name: 'size34Ratio',
    size35Name: 'size35Ratio',
    size36Name: 'size36Ratio',
    size37Name: 'size37Ratio',
    size38Name: 'size38Ratio',
    size39Name: 'size39Ratio',
    size40Name: 'size40Ratio',
    size41Name: 'size41Ratio',
    size42Name: 'size42Ratio',
    size43Name: 'size43Ratio',
    size44Name: 'size44Ratio',
    size45Name: 'size45Ratio',
    size46Name: 'size46Ratio'
})
let attrMappingToAmount = reactive({
    size34Name: 'size34Amount',
    size35Name: 'size35Amount',
    size36Name: 'size36Amount',
    size37Name: 'size37Amount',
    size38Name: 'size38Amount',
    size39Name: 'size39Amount',
    size40Name: 'size40Amount',
    size41Name: 'size41Amount',
    size42Name: 'size42Amount',
    size43Name: 'size43Amount',
    size44Name: 'size44Amount',
    size45Name: 'size45Amount',
    size46Name: 'size46Amount'
})
let remarkForm = reactive({
    orderShoeId: '',
    technicalRemark: '',
    materialRemark: ''
})

onMounted(() => {
    getOrderInfo()
})

async function getOrderInfo() {
    const response = await axios.get(
        `${$api_baseUrl}/order/getbusinessorderinfo?orderid=${orderId}`
    )
    console.log(orderData)
    orderData.value = response.data
    orderShoeData.value = response.data.orderShoeAllData
    batchInfoType = response.data.batchInfoType
    orderData.value.orderShoeAllData.forEach((orderShoe) =>
        orderShoe.orderShoeTypes.forEach((orderShoeType) => {
            orderShoeTypeIdToUnitPrice[orderShoeType.orderShoeTypeId] =
                orderShoeType.shoeTypeBatchData.unitPrice
            orderShoeTypeIdToCurrencyType[orderShoeType.orderShoeTypeId] =
                orderShoeType.shoeTypeBatchData.currencyType
        })
    )
}
function tableHeaderStyle({ row, rowIndex }) {
    return 'background: #ccc; color: #000; font-weight: bolder;'
}
function imagerUrl(url) {
    if (url) {
        return 'http://192.168.16.100:12667/' + url
    }
}
function updateValue(row) {
    let result = row.shoeTypeBatchData.unitPrice * row.shoeTypeBatchData.totalAmount
    row.shoeTypeBatchData.totalPrice = parseFloat(result.toFixed(2));
    orderShoeTypeIdToUnitPrice[row.orderShoeTypeId] = row.shoeTypeBatchData.unitPrice
}
function updateCurrencyValue(row) {
    orderShoeTypeIdToCurrencyType[row.orderShoeTypeId] = row.shoeTypeBatchData.currencyType
}
async function submitFormData() {
    const response = await axios.post(`${$api_baseUrl}/headmanager/confirmProductionOrder`, {
        orderId: location.pathname.split('=')[1]
    })
    if (response.status === 200) {
        ElMessage.success('审批成功')
        getOrderInfo()
    } else {
        ElMessage.error('审批失败')
    }
}
async function saveFormData() {
    const response = await axios.post(`${$api_baseUrl}/headmanager/saveProductionOrderPrice`, {
        unitPriceForm: orderShoeTypeIdToUnitPrice,
        currencyTypeForm: orderShoeTypeIdToCurrencyType
    })
    if (response.status === 200) {
        ElMessage.success('保存成功')
        getOrderInfo()
    } else {
        ElMessage.error('保存失败')
    }
}

const showMessage = () => {
    ElMessageBox.alert('是否确认修改', '', {
        confirmButtonText: '确认',
        callback: (action) => {
            if (action === 'confirm') {
                submitFormData()
            }
        }
    })
}

function openRemarkDialog(row) {
    remarkForm.orderShoeId = row.orderShoeId
    remarkDialogVis.value = true
}
function openEditRemarkDialog(row) {
    remarkForm.orderShoeId = row.orderShoeId
    remarkForm.technicalRemark = row.orderShoeTechnicalRemark
    remarkForm.materialRemark = row.orderShoeMaterialRemark
    remarkDialogVis.value = true
}
async function submitRemarkForm() {
    const response = await axios.post(`${$api_baseUrl}/ordercreate/updateremark`, {
        orderShoeRemarkForm: remarkForm
    })
    if (response.status === 200) {
        ElMessage.success('信息变更成功')
        getOrderInfo()
        remarkDialogVis.value = false
    } else {
        ElMessage.error('信息变更失败')
    }
}
</script>

<style scoped>
.el-table .cell {
    white-space: pre-line !important;
}
</style>
