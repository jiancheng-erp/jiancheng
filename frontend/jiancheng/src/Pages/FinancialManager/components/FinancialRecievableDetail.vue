<template>
    <el-tabs>
        <el-tab-pane label="应收明细">
            <!-- 筛选区域 -->
            <el-row :gutter="5">
                <el-col :span="4">
                    <el-input v-model="searchOrder" placeholder="订单编号" clearable @input="loadReceivables(1)" />
                </el-col>
                <el-col :span="4">
                    <el-input v-model="searchCustomer" placeholder="客户名称" clearable @input="loadReceivables(1)" />
                </el-col>
                <el-col :span="4">
                    <el-input v-model="searchFactoryModel" placeholder="工厂型号" clearable @input="loadReceivables(1)" />
                </el-col>
                <el-col :span="4">
                    <el-input v-model="searchCustomerModel" placeholder="客户型号" clearable @input="loadReceivables(1)" />
                </el-col>
                <el-col :span="5">
                    <el-date-picker
                        v-model="dateRange"
                        type="daterange"
                        start-placeholder="开始日期"
                        end-placeholder="结束日期"
                        format="YYYY-MM-DD"
                        value-format="YYYY-MM-DD"
                        clearable
                        style="width: 280px"
                        @change="loadReceivables(1)"
                    />
                </el-col>
                <el-col :span="2">
                    <el-button type="primary" @click="downloadExcel">下载EXCEL文档</el-button>
                </el-col>
            </el-row>

            <!-- 表格 -->
            <el-table :data="receivableList" style="width: 100%; margin-top: 10px" border>
                <el-table-column type="expand">
                    <template #default="props">
                        <el-table :data="props.row.shoes" border>
                            <el-table-column label="工厂型号" prop="factoryModel" />
                            <el-table-column label="客户型号" prop="customerModel" />
                            <el-table-column label="颜色" prop="color" />
                            <el-table-column label="数量" prop="quantity" />
                            <el-table-column label="单价" prop="unitPrice" :formatter="priceFormatter" />
                            <el-table-column label="总金额" prop="subtotal" :formatter="subtotalFormatter" />
                        </el-table>
                    </template>
                </el-table-column>

                <el-table-column label="订单编号" prop="orderCode" />
                <el-table-column label="客户名称" prop="customerName" />
                <el-table-column label="客户商标" prop="customerBrand"></el-table-column>
                <el-table-column label="订单总金额" prop="totalAmount" :formatter="totalFormatter" />
                <el-table-column label="是否结清" prop="isPaid" :formatter="paidFormatter"/>
                <el-table-column label="下单日期" prop="orderDate" />
                <el-table-column label="预计结束日期" prop="orderEndDate"></el-table-column>
                <el-table-column label="实际结束日期" prop="orderActualEndDate"></el-table-column>
                <el-table-column label="操作" width="240">
                    <template #default="scope">
                        <el-button type="primary" @click="confirmPaid(scope.row)" :disabled="confirmAvaliable(scope.row)">确认结清</el-button>
                        <el-button type="danger" @click="RevertStatus(scope.row)" :disabled="revertAvaliable(scope.row)">退回状态</el-button>
                    </template>
                </el-table-column>
            </el-table>

            <!-- 分页 -->
            <div style="margin-top: 20px; text-align: right">
                <el-pagination background layout="prev, pager, next, jumper, total" :current-page="page" :page-size="pageSize" :total="total" @current-change="loadReceivables" />
            </div>
        </el-tab-pane>
    </el-tabs>
</template>

<script setup lang="ts">
import { ref, onMounted, getCurrentInstance } from 'vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'
import useSetAxiosToken from '../hooks/useSetAxiosToken'

const { setAxiosToken } = useSetAxiosToken()
const $api_baseUrl = getCurrentInstance().appContext.config.globalProperties.$apiBaseUrl
const role = localStorage.getItem('role')

interface ShoeItem {
    factoryModel: string
    customerModel: string
    color: string
    sizeRange: string
    quantity: number
    unitPrice: number
    subtotal: number
}

interface ReceivableItem {
    orderCode: string
    customerName: string
    orderDate: string
    totalAmount: number
    paidAmount: number
    shoes: ShoeItem[]
}

const receivableList = ref<ReceivableItem[]>([])
const page = ref(1)
const pageSize = 10
const total = ref(0)

const searchOrder = ref('')
const searchCustomer = ref('')
const searchFactoryModel = ref('')
const searchCustomerModel = ref('')
const dateRange = ref<[string, string] | null>(null)

const loadReceivables = async (newPage = page.value) => {
    page.value = newPage
    const [startDate, endDate] = dateRange.value || [null, null]

    try {
        const { data } = await axios.get(`${$api_baseUrl}/finance/get_receivable_list`, {
            params: {
                page: page.value,
                per_page: pageSize,
                searchOrder: searchOrder.value,
                searchCustomer: searchCustomer.value,
                factoryModel: searchFactoryModel.value,
                customerModel: searchCustomerModel.value,
                startDate,
                endDate
            }
        })
        receivableList.value = data.receivables
        total.value = data.total
    } catch (err) {
        console.error('Failed to load receivables:', err)
    }
}

const unpaidFormatter = (row: any) => {
    if (!row) return '-'
    return (row.totalAmount - row.paidAmount).toFixed(2)
}

const priceFormatter = (row: any) => {
    if (!row) return '-'
    return row.unitPrice ? row.unitPrice.toFixed(2) : '-'
}

const subtotalFormatter = (row: any) => {
    if (!row) return '-'
    return row.subtotal ? row.subtotal.toFixed(2) : '-'
}

const paidFormatter = (row: any) => {
    if (!row) return '-'
    return row.isPaid ? '是' : '否'
}

const totalFormatter = (row: any) => {
    if (!row) return '-'
    return row.totalAmount ? row.totalAmount.toFixed(2) : '-'
}

onMounted(() => {
    setAxiosToken()
    loadReceivables()
})

async function downloadExcel() {
    try {
        const res = await axios.get($api_baseUrl + `/finance/download_receivable_excel`, {
            params: {
                searchOrder: searchOrder.value,
                searchCustomer: searchCustomer.value,
                factoryModel: searchFactoryModel.value,
                customerModel: searchCustomerModel.value,
                startDate: dateRange.value ? dateRange.value[0] : null,
                endDate: dateRange.value ? dateRange.value[1] : null
            },
            responseType: 'blob' // Important: this tells Axios to handle binary data
        })

        // Create a Blob from the response data
        const blob = new Blob([res.data], { type: res.headers['content-type'] })

        // Use the filename from the Content-Disposition header if available
        const disposition = res.headers['content-disposition']
        let filename = '财务部应收明细.xlsx' // fallback name
        if (disposition && disposition.includes('filename=')) {
            const match = disposition.match(/filename="?(.+?)"?$/)
            if (match.length > 1) {
                filename = decodeURIComponent(match[1])
            }
        }

        // Create a link and trigger the download
        const link = document.createElement('a')
        link.href = URL.createObjectURL(blob)
        link.download = filename
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        URL.revokeObjectURL(link.href)
    } catch (error) {
        console.error('Failed to download Excel:', error)
    }
}
async function confirmPaid(row) {
    console.log('Confirming paid for order:', row.orderCode)
    try {
        const response = await axios.post(`${$api_baseUrl}/finance/confirm_paid`, {
            orderCode: row.orderCode
        })
        if (response.status === 200) {
            ElMessage.success('确认结清成功')
            loadReceivables()
        } else {
            ElMessage.error('确认结清失败: ' + response.data.message)
        }
    } catch (error) {
        console.error('Error confirming paid:', error)
        ElMessage.error('确认结清失败，请稍后再试')
    }
}

async function RevertStatus(row) {
    try {
        const response = await axios.post(`${$api_baseUrl}/finance/revert_status`, {
            orderCode: row.orderCode
        })
        if (response.status === 200) {
            ElMessage.success('退回状态成功')
            loadReceivables()
        } else {
            ElMessage.error('退回状态失败: ' + response.data.message)
        }
    } catch (error) {
        console.error('Error reverting status:', error)
        ElMessage.error('退回状态失败，请稍后再试')
    }
}
function confirmAvaliable(row: { isPaid: any }) {
    return !((role === '10' || role === '24') && !row.isPaid)
}
function revertAvaliable(row: { isPaid: any }) {
    return !(role === '10' && row.isPaid)
}
</script>

<style scoped>
/* 适当调整样式 */
</style>
