<template>
    <el-container>
        <el-header>
            <AllHeader></AllHeader>
        </el-header>
        <el-container>
            <el-main>
                <div class="order-sheet">
                    <div class="sheet-title">健诚集团{{ orderData.customerName }}号客人{{ orderData.customerBrand }}生产订单</div>

                    <table class="excel-table info-table">
                        <tbody>
                            <tr>
                                <td class="info-label">单号</td>
                                <td class="info-value">{{ orderData.orderRid }}</td>
                                <td class="info-label">下单日期</td>
                                <td class="info-value">{{ orderData.startDate }}</td>
                                <td class="info-label">出货日期</td>
                                <td class="info-value">{{ orderData.endDate }}</td>
                                <td class="info-label">客户订单号</td>
                                <td class="info-value">{{ orderData.orderCid }}</td>
                                <td class="info-label">业务</td>
                                <td class="info-value">{{ orderData.orderStaffName }}</td>
                                <td class="info-label">配码类型</td>
                                <td class="info-value">{{ orderData.batchInfoTypeName }}</td>
                                <td class="info-action">
                                    <el-button type="danger" size="small" @click="openRevertDialog">退回订单</el-button>
                                </td>
                            </tr>
                        </tbody>
                    </table>

                    <table class="excel-table main-table">
                        <thead>
                            <tr>
                                <th style="width: 130px">鞋图</th>
                                <th style="width: 90px">工厂款号</th>
                                <th style="width: 100px">客户型号</th>
                                <th style="width: 70px">颜色</th>
                                <th style="width: 90px">客户颜色</th>
                                <th style="width: 80px">配码</th>
                                <th class="size-col" colspan="1" v-for="s in activeSizes" :key="s.amountKey">{{ s.name }}</th>
                                <th style="width: 55px">对/件</th>
                                <th style="width: 55px">件数</th>
                                <th style="width: 55px">双数</th>
                                <th style="width: 200px">备注</th>
                                <th style="width: 120px">价格</th>
                                <th style="width: 110px">金额</th>
                            </tr>
                        </thead>
                        <tbody>
                            <template v-for="shoe in orderShoeData" :key="shoe.orderShoeId">
                                <template v-for="(colorType, ci) in shoe.orderShoeTypes" :key="colorType.orderShoeTypeId">
                                    <tr v-for="(batch, bi) in colorType.shoeTypeBatchInfoList" :key="`${colorType.orderShoeTypeId}-${bi}`">
                                        <td v-if="ci === 0 && bi === 0" :rowspan="shoeRowCount(shoe)" class="img-cell">
                                            <div v-for="ct in shoe.orderShoeTypes" :key="`img-${ct.orderShoeTypeId}`" class="img-wrap">
                                                <el-image
                                                    v-if="ct.shoeTypeImgUrl"
                                                    :src="ct.shoeTypeImgUrl"
                                                    :preview-src-list="[ct.shoeTypeImgUrl]"
                                                    fit="contain"
                                                    style="width: 120px; height: 80px"
                                                ></el-image>
                                                <span v-else class="no-img">暂无图片</span>
                                            </div>
                                        </td>
                                        <td v-if="ci === 0 && bi === 0" :rowspan="shoeRowCount(shoe)">{{ shoe.shoeRid }}</td>
                                        <td v-if="ci === 0 && bi === 0" :rowspan="shoeRowCount(shoe)">{{ shoe.shoeCid }}</td>
                                        <td v-if="bi === 0" :rowspan="colorType.shoeTypeBatchInfoList.length">{{ colorType.shoeTypeColorName }}</td>
                                        <td v-if="bi === 0" :rowspan="colorType.shoeTypeBatchInfoList.length">{{ colorType.customerColorName }}</td>
                                        <td>{{ batch.packagingInfoName }}</td>
                                        <td class="size-col" v-for="s in activeSizes" :key="s.amountKey">
                                            {{ batch[s.amountKey] || '' }}
                                        </td>
                                        <td>{{ batch.totalQuantityRatio }}</td>
                                        <td>{{ batch.unitPerRatio }}</td>
                                        <td>{{ batch.total }}</td>
                                        <td v-if="ci === 0 && bi === 0" :rowspan="shoeRowCount(shoe)" class="remark-cell">
                                            <template v-if="shoe.orderShoeRemarkExist">
                                                <div class="remark-text">{{ shoe.orderShoeRemarkRep }}</div>
                                                <el-button type="warning" size="small" @click="openEditRemarkDialog(shoe)">编辑备注</el-button>
                                            </template>
                                            <el-button v-else type="primary" size="small" @click="openRemarkDialog(shoe)">添加备注</el-button>
                                        </td>
                                        <td v-if="bi === 0" :rowspan="colorType.shoeTypeBatchInfoList.length" class="price-cell">
                                            <template v-if="colorType.shoeTypeBatchData.unitPrice !== null && colorType.shoeTypeBatchData.unitPrice !== undefined">
                                                <el-input
                                                    size="small"
                                                    v-model.lazy="colorType.shoeTypeBatchData.unitPrice"
                                                    @change="onPriceChange(colorType)"
                                                    :disabled="priceChangeNotAllowed"
                                                />
                                                <el-input
                                                    size="small"
                                                    placeholder="单位"
                                                    v-model="colorType.shoeTypeBatchData.currencyType"
                                                    @change="onCurrencyChange(colorType)"
                                                    :disabled="priceChangeNotAllowed"
                                                    style="margin-top: 4px"
                                                />
                                            </template>
                                            <span v-else>--</span>
                                        </td>
                                        <td v-if="bi === 0" :rowspan="colorType.shoeTypeBatchInfoList.length">
                                            <template v-if="colorType.shoeTypeBatchData.totalPrice !== null && colorType.shoeTypeBatchData.totalPrice !== undefined">
                                                {{ currencySymbol(colorType.shoeTypeBatchData.currencyType) }}{{ formatMoney(colorType.shoeTypeBatchData.totalPrice) }}
                                            </template>
                                            <span v-else>--</span>
                                        </td>
                                    </tr>
                                </template>
                            </template>
                            <tr class="total-row">
                                <td :colspan="5">合计</td>
                                <td></td>
                                <td class="size-col" v-for="s in activeSizes" :key="`total-${s.amountKey}`">{{ sizeTotals[s.amountKey] || '' }}</td>
                                <td></td>
                                <td></td>
                                <td>{{ grandTotalPairs }}</td>
                                <td></td>
                                <td></td>
                                <td>{{ grandTotalPrice !== null ? grandTotalCurrencySymbol + formatMoney(grandTotalPrice) : '--' }}</td>
                            </tr>
                        </tbody>
                    </table>
                </div>

                <div class="action-bar">
                    <el-button type="primary" @click="saveFormData" v-if="orderData.orderStatus === 7 || role == 1 || role == 2">保存数据</el-button>
                    <el-button type="primary" @click="showMessage" v-if="orderData.orderStatus === 7">完成审批</el-button>
                </div>
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
    <el-dialog title="退回流程" v-model="isRevertDialogVisable" width="20%" :close-on-click-modal="false">
        <span>
            <span>退回流程</span>
            <el-row :gutter="20">
                <el-col :span="24" :offset="0">
                    <el-form>
                        <el-form-item label="退回至状态" prop="revertToStatus">
                            <el-select v-model="revertForm.revertToStatus" placeholder="请选择退回至状态" clearable @change="handleStatusSelect">
                                <el-option v-for="item in revertStatusReasonOptions" :key="item.status" :label="item.statusName" :value="item.status"></el-option>
                            </el-select>
                        </el-form-item>
                        <el-form-item label="需要中间流程" prop="isNeedMiddleProcess">
                            <el-radio-group v-model="revertForm.isNeedMiddleProcess">
                                <el-radio label="1">是</el-radio>
                                <el-radio label="0">否</el-radio>
                            </el-radio-group>
                        </el-form-item>
                        <el-form-item label="退回原因" prop="revertReason">
                            <el-input v-model="revertForm.revertReason" :rows="4" placeholder="请输入退回原因" disabled></el-input>
                        </el-form-item>
                        <el-form-item label="退回详细原因" prop="revertDetail">
                            <el-input v-model="revertForm.revertDetail" type="textarea" :rows="4" placeholder="请输入退回原因"></el-input>
                        </el-form-item>
                    </el-form>
                </el-col>
            </el-row>
        </span>
        <template #footer>
            <span>
                <el-button @click="isRevertDialogVisable = false">取消</el-button>
                <el-button type="primary" :disabled="revertForm.revertToStatus === ''" @click="saveRevertForm">确认</el-button>
            </span>
        </template>
    </el-dialog>
</template>

<script setup>
import AllHeader from '@/components/AllHeader.vue'
import axios from 'axios'
import { onMounted, reactive, ref, watch, computed } from 'vue'
import { getCurrentInstance } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

const $api_baseUrl = getCurrentInstance().appContext.config.globalProperties.$apiBaseUrl

const { orderId } = defineProps(['orderId'])
const role = ref(localStorage.getItem('role'))
let orderData = ref({})
let orderShoeData = ref([])
let priceChangeNotAllowed = ref(false)
let remarkDialogVis = ref(false)
let orderShoeTypeIdToUnitPrice = reactive({})
let orderShoeTypeIdToCurrencyType = reactive({})
let batchInfoType = reactive({})
let isRevertDialogVisable = ref(false)
let revertStatusReasonOptions = ref([])
let revertForm = reactive({
    revertToStatus: '',
    revertReason: '',
    revertDetail: '',
    isNeedMiddleProcess: '0'
})
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

const activeSizes = ref([])

const sizeTotals = computed(() => {
    const totals = {}
    activeSizes.value.forEach((s) => (totals[s.amountKey] = 0))
    orderShoeData.value.forEach((shoe) =>
        (shoe.orderShoeTypes || []).forEach((colorType) =>
            (colorType.shoeTypeBatchInfoList || []).forEach((batch) => {
                activeSizes.value.forEach((s) => {
                    totals[s.amountKey] += Number(batch[s.amountKey]) || 0
                })
            })
        )
    )
    return totals
})

const grandTotalPairs = computed(() => {
    let total = 0
    orderShoeData.value.forEach((shoe) =>
        (shoe.orderShoeTypes || []).forEach((colorType) => {
            total += Number(colorType.shoeTypeBatchData?.totalAmount) || 0
        })
    )
    return total
})

const grandTotalPrice = computed(() => {
    let total = 0
    let hasPrice = false
    orderShoeData.value.forEach((shoe) =>
        (shoe.orderShoeTypes || []).forEach((colorType) => {
            const price = colorType.shoeTypeBatchData?.totalPrice
            if (price !== null && price !== undefined) {
                total += Number(price) || 0
                hasPrice = true
            }
        })
    )
    return hasPrice ? parseFloat(total.toFixed(2)) : null
})

const grandTotalCurrencySymbol = computed(() => {
    // 与单行金额口径保持一致：仅当所有有价格鞋型的币种一致且为人民币时显示 ¥，否则不显示
    const currencySet = new Set()
    orderShoeData.value.forEach((shoe) =>
        (shoe.orderShoeTypes || []).forEach((colorType) => {
            const price = colorType.shoeTypeBatchData?.totalPrice
            if (price !== null && price !== undefined) {
                currencySet.add(colorType.shoeTypeBatchData?.currencyType)
            }
        })
    )
    if (currencySet.size === 1) {
        return currencySymbol([...currencySet][0])
    }
    return ''
})

function shoeRowCount(shoe) {
    return (shoe.orderShoeTypes || []).reduce((sum, colorType) => sum + (colorType.shoeTypeBatchInfoList?.length || 0), 0)
}

function formatMoney(value) {
    const num = Number(value)
    if (isNaN(num)) return value
    return num.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function currencySymbol(currency) {
    switch (currency) {
        case 'RMB':
        case 'CNY':
        case '人民币':
            return '¥'
        case 'USD':
        case 'USA':
        case '美元':
            return '$'
        case 'EUR':
        case '欧元':
            return '€'
        default:
            return currency ? currency + ' ' : ''
    }
}

function onPriceChange(colorType) {
    const amount = Number(colorType.shoeTypeBatchData.totalAmount) || 0
    const price = parseFloat(colorType.shoeTypeBatchData.unitPrice) || 0
    colorType.shoeTypeBatchData.totalPrice = parseFloat((price * amount).toFixed(2))
    orderShoeTypeIdToUnitPrice[colorType.orderShoeTypeId] = colorType.shoeTypeBatchData.unitPrice
}

function onCurrencyChange(colorType) {
    orderShoeTypeIdToCurrencyType[colorType.orderShoeTypeId] = colorType.shoeTypeBatchData.currencyType
}

onMounted(() => {
    getOrderInfo()
    getAllRevertStatusReasonOptions()
})

async function getOrderInfo() {
    const response = await axios.get(`${$api_baseUrl}/order/getbusinessorderinfo?orderid=${orderId}`)
    console.log(orderData)
    orderData.value = response.data
    orderShoeData.value = response.data.orderShoeAllData
    batchInfoType = response.data.batchInfoType
    activeSizes.value = Object.keys(attrMappingToRatio)
        .filter((key) => batchInfoType[key] != null)
        .map((key) => ({
            name: batchInfoType[key],
            amountKey: attrMappingToAmount[key]
        }))
    orderData.value.orderShoeAllData.forEach((orderShoe) =>
        orderShoe.orderShoeTypes.forEach((orderShoeType) => {
            orderShoeTypeIdToUnitPrice[orderShoeType.orderShoeTypeId] = orderShoeType.shoeTypeBatchData.unitPrice
            orderShoeTypeIdToCurrencyType[orderShoeType.orderShoeTypeId] = orderShoeType.shoeTypeBatchData.currencyType
        })
    )
}
function tableHeaderStyle({ row, rowIndex }) {
    return 'background: #ccc; color: #000; font-weight: bolder;'
}
function imagerUrl(url) {
    if (url) {
        return url
    }
}
function updateValue(row) {
    let result = row.shoeTypeBatchData.unitPrice * row.shoeTypeBatchData.totalAmount
    row.shoeTypeBatchData.totalPrice = parseFloat(result.toFixed(2))
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
        if (window.opener?.callRefreshTaskData) {
            window.opener.callRefreshTaskData()
            console.log('Function called successfully.')
        } else {
            console.warn('Function not available on opener window.')
        }
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
function handleStatusSelect(value) {
    revertForm.revertReason = revertStatusReasonOptions.value.find((item) => item.status === value).reason
}
function openRevertDialog() {
    isRevertDialogVisable.value = true
    revertForm.revertToStatus = ''
    revertForm.revertReason = ''
    revertForm.revertDetail = ''
    revertForm.isNeedMiddleProcess = '0'
}
async function getAllRevertStatusReasonOptions() {
    const response = await axios.get(`${$api_baseUrl}/revertorder/getrevertorderreasonfororder`, {
        params: {
            orderId: orderId,
            flow: '1'
        }
    })
    if (response.status === 200) {
        revertStatusReasonOptions.value = response.data
    } else {
        ElMessage.error('获取退回状态失败')
    }
}
function saveRevertForm() {
    ElMessageBox.confirm(`确定退回此订单吗？退回至 ${revertForm.revertToStatus}, 原因是 ${revertForm.revertReason}`, '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
    })
        .then(() => {
            revertOrder()
        })
        .catch(() => {
            ElMessage.info('已取消退回')
        })
}
async function revertOrder() {
    const response = await axios.post(`${$api_baseUrl}/revertorder/revertordersavefororder`, {
        orderId: orderId,
        flow: 1,
        revertToStatus: revertForm.revertToStatus,
        revertReason: revertForm.revertReason,
        revertDetail: revertForm.revertDetail,
        isNeedMiddleProcess: revertForm.isNeedMiddleProcess
    })
    if (response.status === 200) {
        ElMessage.success('退回成功')
        getOrderInfo()
        isRevertDialogVisable.value = false
        if (window.opener?.callRefreshTaskData) {
            window.opener.callRefreshTaskData()
            console.log('Function called successfully.')
        } else {
            console.warn('Function not available on opener window.')
        }
    } else {
        ElMessage.error('退回失败')
    }
}
</script>

<style scoped>
.el-table .cell {
    white-space: pre-line !important;
}

:deep(.el-main) {
    background: #f0f2f5;
    padding: 20px;
}

.order-sheet {
    background: #ffffff;
    border-radius: 12px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
    padding: 24px 28px 30px;
    overflow-x: auto;
}

.sheet-title {
    text-align: center;
    font-size: 23px;
    font-weight: 700;
    letter-spacing: 3px;
    color: #1f2d3d;
    padding: 4px 0 20px;
}

.sheet-title::after {
    content: '';
    display: block;
    width: 90px;
    height: 3px;
    margin: 12px auto 0;
    background: linear-gradient(90deg, #409eff, #66b1ff);
    border-radius: 2px;
}

.excel-table {
    border-collapse: collapse;
    width: 100%;
    table-layout: fixed;
    font-size: 13px;
    color: #303133;
}

.excel-table th,
.excel-table td {
    border: 1px solid #d5d8dd;
    padding: 6px 6px;
    text-align: center;
    vertical-align: middle;
    word-break: break-word;
}

.excel-table th {
    background: linear-gradient(180deg, #f7f9fc, #eaeef4);
    font-weight: 600;
    color: #1f2d3d;
}

.info-table {
    margin-bottom: -1px;
}

.info-table .info-label {
    background: #eef4ff;
    color: #3a7bd5;
    font-weight: 600;
    width: 80px;
    white-space: nowrap;
}

.info-table .info-value {
    white-space: nowrap;
    color: #303133;
}

.info-table .info-action {
    width: 110px;
    background: #fafbfc;
}

.main-table thead th {
    position: sticky;
    top: 0;
    z-index: 2;
}

.main-table .size-col {
    width: 44px;
    background: #fbfcfe;
}

.main-table tbody tr:hover td {
    background: #f2f8ff;
}

.img-cell {
    padding: 6px;
    background: #fff;
}

.img-cell .img-wrap {
    display: flex;
    justify-content: center;
    align-items: center;
    padding: 3px 0;
}

.img-cell .img-wrap :deep(.el-image) {
    border-radius: 6px;
    box-shadow: 0 1px 6px rgba(0, 0, 0, 0.12);
    overflow: hidden;
}

.img-cell .no-img {
    color: #b0b3b8;
    font-size: 12px;
}

.remark-cell {
    text-align: left;
    white-space: pre-line;
    line-height: 1.6;
}

.remark-cell .remark-text {
    margin-bottom: 8px;
    color: #5a5e66;
}

.price-cell {
    padding: 6px;
}

.price-cell :deep(.el-input__wrapper) {
    border-radius: 6px;
}

.total-row td {
    font-weight: 700;
    background: #eef4ff !important;
    color: #1f2d3d;
    font-size: 14px;
}

.action-bar {
    margin-top: 20px;
    display: flex;
    justify-content: center;
    gap: 12px;
}

.action-bar :deep(.el-button) {
    min-width: 120px;
    border-radius: 8px;
}
</style>
