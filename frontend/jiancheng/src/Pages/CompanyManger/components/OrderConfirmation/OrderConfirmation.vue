<template>
    <div class="content">
        <el-row :gutter="20" style="margin-top: 20px">
            <el-col :span="4" :offset="0"
                ><el-input
                    v-model="orderRidFilter"
                    placeholder="请输入订单号"
                    size="default"
                    :suffix-icon="Search"
                    clearable
                    @input="filterByRid()"
                ></el-input>
            </el-col>
            <el-col :span="4" :offset="0"
                ><el-input
                    v-model="orderCidFilter"
                    placeholder="请输入客户订单号"
                    size="default"
                    :suffix-icon="Search"
                    clearable
                    @input="filterByCid()"
                ></el-input>
            </el-col>
            <el-col :span="4" :offset="0">
                <el-input
                    v-model="customerIdFilter"
                    placeholder="请输入客户号"
                    size="default"
                    :suffix-icon="Search"
                    clearable
                    @input="filterByCustomerName()"
                ></el-input>
            </el-col>
            <el-col :span="4" :offset="0">
                <el-input
                    v-model="shoeRidFilter"
                    placeholder="请输入鞋型号"
                    size="default"
                    :suffix-icon="Search"
                    clearable
                    @input="filterByShoeRid()"
                ></el-input>
            </el-col>
            <el-col :span="4" :offset="0">
                <el-input
                    v-model="shoeCidFilter"
                    placeholder="请输入客户鞋型号"
                    size="default"
                    :suffix-icon="Search"
                    clearable
                    @input="filterByShoeCid()"
                ></el-input>
            </el-col>
            <el-col :span="6" :offset="0">
                <el-radio-group v-model="radio" @change="dataPagination()">
                    <el-radio-button label="所有订单" value="all" />
                    <el-radio-button label="已审批订单" value="已审批" />
                    <el-radio-button label="待审批订单" value="待审批" />
                </el-radio-group>
            </el-col>
        </el-row>
        <el-row :gutter="20">
            <el-table :data="displayData" stripe height="650">
                <el-table-column type="index" width="50" />
                <el-table-column prop="orderRid" label="订单号" />
                <el-table-column prop="orderSalesman" label="操作员"/>
                <el-table-column prop="orderSupervisor" label="责任人"/>
                <el-table-column prop="customerName" label="客户名" />
                <el-table-column prop="orderCid" label="客户订单号" />
                <el-table-column prop="shoeRId" label="鞋型号" />
                <el-table-column prop="shoeCid" label="客户鞋型号" />
                <el-table-column prop="orderStartDate" label="订单开始日期" sortable />
                <el-table-column prop="orderEndDate" label="订单结束日期" sortable />
                <el-table-column prop="orderStatus" label="订单状态" />
                <el-table-column label="操作" width="300">
                    <template #default="scope">
                        <el-button
                            v-show="scope.row.orderStatus == '生产订单总经理确认'"
                            type="primary"
                            @click="openOrderDetail(scope.row.orderDbId)"
                            >审批生产订单</el-button
                        >
                        <el-button-group v-show="scope.row.orderStatus != '生产订单总经理确认'">
                            <el-button
                            type="primary"
                            @click="openOrderDetail(scope.row.orderDbId)"
                            >查看生产订单</el-button>
                            <el-button
                            type="danger"
                            @click="deleteOrder(scope.row.orderRid)"
                            >删除订单</el-button>
                        </el-button-group>

                    </template>
                </el-table-column>
            </el-table>
        </el-row>
        <el-row :gutter="20" style="justify-content: end; width: 100%">
            <el-pagination
                @size-change="chageCurrentPageSize"
                @current-change="changeCurrentPage"
                :current-page="currentPage"
                :page-sizes="[10, 20, 30, 40]"
                :page-size="currentPageSize"
                layout="total, sizes, prev, pager, next, jumper"
                :total="currentTotalRows"
            />
        </el-row>
    </div>
</template>

<script setup>
import { Search } from '@element-plus/icons-vue'
import axios from 'axios'
import { ref, onMounted, getCurrentInstance } from 'vue'
import { ElMessage } from 'element-plus'

let orderRidFilter = ref('')
let orderCidFilter = ref('')
let customerIdFilter = ref('')
let shoeRidFilter = ref('')
let shoeCidFilter = ref('')
let displayData = ref([])
let allData = ref([])
let examineData = ref([])
let approvedData = ref([])
let radio = ref('all')
const $api_baseUrl = getCurrentInstance().appContext.config.globalProperties.$apiBaseUrl

let currentPage = ref(1)
let currentPageSize = ref(10)
let currentTotalRows = ref(0)

onMounted(() => {
    getAllOrders()
})

function sortByAscII(val1, val2) {
    if(val1 > val2){
        return 1;
      }else if(val1 < val2){
        return -1;
      }else{
        return 0;
      }
}
async function getAllOrders() {
    const response = await axios.get(`${$api_baseUrl}/order/getallorders`)
    console.log(allData)
    allData.value = response.data.sort((a,b) => sortByAscII(a.orderRid, b.orderRid));
    // 此处需要增加订单状态筛选功能，保留状态为生产订单确认的数据
    const arr1 = []
    const arr2 = []
    for (let i = 0; i < response.data.length; i++) {
        if (response.data[i].orderStatusVal === 7) {
            arr1.push(response.data[i])
        } else if (response.data[i].orderStatusVal > 7) {
            arr2.push(response.data[i])
        }
    }
    examineData.value = arr1.sort((a,b) => sortByAscII(a.orderRid, b.orderRid))
    approvedData.value = arr2.sort((a,b) => sortByAscII(a.orderRid, b.orderRid))
    dataPagination()
}

function dataPagination() {
    orderRidFilter.value = ''
    orderCidFilter.value = ''
    if (radio.value == 'all') {
        displayData.value = allData.value.slice(
            (currentPage.value - 1) * currentPageSize.value,
            currentPageSize.value * currentPage.value
        )
        currentTotalRows.value = allData.value.length
    } else if (radio.value == '待审批') {
        displayData.value = examineData.value.slice(
            (currentPage.value - 1) * currentPageSize.value,
            currentPageSize.value * currentPage.value
        )
        currentTotalRows.value = examineData.value.length
    } else {
        displayData.value = approvedData.value.slice(
            (currentPage.value - 1) * currentPageSize.value,
            currentPageSize.value * currentPage.value
        )
        currentTotalRows.value = approvedData.value.length
    }
}

async function deleteOrder(value) {
    // 此处更换删除订单的路由
    const response = await axios.post(`${$api_baseUrl}/order/getallorders`, {'orderRid': value})
    if (response.status === 200) {
        ElMessage.success('删除成功,数据正在更新,请稍后')
        getAllOrders()
    } else {
        ElMessage.error('修改失败')
    }
    
}

function openOrderDetail(orderId) {
    let url = ''
    url = `${window.location.origin}/companyManager/orderConfirmDetail/orderid=${orderId}`
    window.open(url, '_blank')
}
function filterByRid() {
    if (radio.value == 'all') {
        const arr = allData.value.filter((task) => {
                const filterMatch = task.orderRid.toLowerCase().includes(orderRidFilter.value.toLowerCase())
                return filterMatch
            })
        currentTotalRows.value = arr.length
        displayData.value = arr.slice(
            (currentPage.value - 1) * currentPageSize.value,
            currentPageSize.value * currentPage.value
        )
        currentTotalRows.value = arr.length
    } else if (radio.value == '待审批') {
        const arr = examineData.value.filter((task) => {
                const filterMatch = task.orderRid.toLowerCase().includes(orderRidFilter.value.toLowerCase())
                return filterMatch
            })
        currentTotalRows.value = arr.length
        displayData.value = arr.slice(
            (currentPage.value - 1) * currentPageSize.value,
            currentPageSize.value * currentPage.value
        )
    } else {
        const arr = approvedData.value.filter((task) => {
                const filterMatch = task.orderRid.toLowerCase().includes(orderRidFilter.value.toLowerCase())
                return filterMatch
            })
        currentTotalRows.value = arr.length
        displayData.value = arr.slice(
            (currentPage.value - 1) * currentPageSize.value,
            currentPageSize.value * currentPage.value
        )
    }
}
function filterByCid() {
    if (radio.value == 'all') {
        const arr = allData.value.filter((task) => {
                const filterMatch = task.orderCid.toLowerCase().includes(orderCidFilter.value.toLowerCase())
                return filterMatch
            })
        currentTotalRows.value = arr.length
        displayData.value = arr.slice(
            (currentPage.value - 1) * currentPageSize.value,
            currentPageSize.value * currentPage.value
        )
        currentTotalRows.value = arr.length
    } else if (radio.value == '待审批') {
        const arr = examineData.value.filter((task) => {
                const filterMatch = task.orderCid.toLowerCase().includes(orderCidFilter.value.toLowerCase())
                return filterMatch
            })
        currentTotalRows.value = arr.length
        displayData.value = arr.slice(
            (currentPage.value - 1) * currentPageSize.value,
            currentPageSize.value * currentPage.value
        )
    } else {
        const arr = approvedData.value.filter((task) => {
                const filterMatch = task.orderCid.toLowerCase().includes(orderCidFilter.value.toLowerCase())
                return filterMatch
            })
        currentTotalRows.value = arr.length
        displayData.value = arr.slice(
            (currentPage.value - 1) * currentPageSize.value,
            currentPageSize.value * currentPage.value
        )
    }

}
function filterByCustomerName() {
    if (radio.value == 'all') {
        const arr = allData.value.filter((task) => {
                const filterMatch = task.customerName.toLowerCase().includes(customerIdFilter.value.toLowerCase())
                return filterMatch
            })
        currentTotalRows.value = arr.length
        displayData.value = arr.slice(
            (currentPage.value - 1) * currentPageSize.value,
            currentPageSize.value * currentPage.value
        )
        currentTotalRows.value = arr.length
    } else if (radio.value == '待审批') {
        const arr = examineData.value.filter((task) => {
                const filterMatch = task.customerName.toLowerCase().includes(customerIdFilter.value.toLowerCase())
                return filterMatch
            })
        currentTotalRows.value = arr.length
        displayData.value = arr.slice(
            (currentPage.value - 1) * currentPageSize.value,
            currentPageSize.value * currentPage.value
        )
    } else {
        const arr = approvedData.value.filter((task) => {
                const filterMatch = task.customerName.toLowerCase().includes(customerIdFilter.value.toLowerCase())
                return filterMatch
            })
        currentTotalRows.value = arr.length
        displayData.value = arr.slice(
            (currentPage.value - 1) * currentPageSize.value,
            currentPageSize.value * currentPage.value
        )
    }
}
function filterByShoeRid() {
    if (radio.value == 'all') {
        const arr = allData.value.filter((task) => {
                const filterMatch = task.shoeRId.toLowerCase().includes(shoeRidFilter.value.toLowerCase())
                return filterMatch
            })
        currentTotalRows.value = arr.length
        displayData.value = arr.slice(
            (currentPage.value - 1) * currentPageSize.value,
            currentPageSize.value * currentPage.value
        )
        currentTotalRows.value = arr.length
    } else if (radio.value == '待审批') {
        const arr = examineData.value.filter((task) => {
                const filterMatch = task.shoeRId.toLowerCase().includes(shoeRidFilter.value.toLowerCase())
                return filterMatch
            })
        currentTotalRows.value = arr.length
        displayData.value = arr.slice(
            (currentPage.value - 1) * currentPageSize.value,
            currentPageSize.value * currentPage.value
        )
    } else {
        const arr = approvedData.value.filter((task) => {
                const filterMatch = task.shoeRId.toLowerCase().includes(shoeRidFilter.value.toLowerCase())
                return filterMatch
            })
        currentTotalRows.value = arr.length
        displayData.value = arr.slice(
            (currentPage.value - 1) * currentPageSize.value,
            currentPageSize.value * currentPage.value
        )
    }
}
function filterByShoeCid() {
    if (radio.value == 'all') {
        const arr = allData.value.filter((task) => {
                const filterMatch = task.shoeCid.toLowerCase().includes(shoeCidFilter.value.toLowerCase())
                return filterMatch
            })
        currentTotalRows.value = arr.length
        displayData.value = arr.slice(
            (currentPage.value - 1) * currentPageSize.value,
            currentPageSize.value * currentPage.value
        )
        currentTotalRows.value = arr.length
    } else if (radio.value == '待审批') {
        const arr = examineData.value.filter((task) => {
                const filterMatch = task.shoeCid.toLowerCase().includes(shoeCidFilter.value.toLowerCase())
                return filterMatch
            })
        currentTotalRows.value = arr.length
        displayData.value = arr.slice(
            (currentPage.value - 1) * currentPageSize.value,
            currentPageSize.value * currentPage.value
        )
    } else {
        const arr = approvedData.value.filter((task) => {
                const filterMatch = task.shoeCid.toLowerCase().includes(shoeCidFilter.value.toLowerCase())
                return filterMatch
            })
        currentTotalRows.value = arr.length
        displayData.value = arr.slice(
            (currentPage.value - 1) * currentPageSize.value,
            currentPageSize.value * currentPage.value
        )
    }
}

function chageCurrentPageSize(val) {
    currentPageSize.value = val
    dataPagination()
}

function changeCurrentPage(val) {
    currentPage.value = val
    dataPagination()
}
</script>

<style scoped>
.content {
    height: calc(100% - 40px);
}
</style>
