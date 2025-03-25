<template>
    <div class="content">财务应付信息</div>

    <el-button @click="getAllPayableInfoNew" type="info">
        刷新
    </el-button>
    <el-button @click="openAddPayableTransactionDialog" type="primary">
        处理应付款
    </el-button>
    <!-- <el-switch v-model="showDetails"></el-switch> -->
    <el-switch v-model="oldNewLayout"
            size="large"
            active-text="库存明细"
            inactive-text="金额明细"></el-switch>
    <el-container v-if="oldNewLayout">
        <el-table :data="payable_data">
            <el-table-column type="expand">
                <template #default="props">
                    <div m="4">
                        <p m="t-0 b-2" v-if="showDetails">地址: {{ props.row.accountOwnerAddress }}</p>
                        <p m="t-0 b-2" v-if="showDetails">联系方式: {{ props.row.accountOwnderContactInfo }}</p>
                        <p m="t-0 b-2" v-if="showDetails">银行信息: {{ props.row.accountOwnerBankInfo }}</p>
                    <h2>历史记录</h2>
                    <el-table :data="props.row.transactionDetails">
                        <el-table-column label="入库时间" prop="inboundTime" sortable></el-table-column>
                        <el-table-column label="材料类型" prop="materialType"></el-table-column>
                        <el-table-column label="材料名称" prop="materialName"></el-table-column>
                        <el-table-column label="材料型号" prop="materialModel"></el-table-column>
                        <el-table-column label="材料规格" prop="materialSpecification"></el-table-column>
                        <el-table-column label="数量" prop="materialAmount" sortable></el-table-column>
                        <el-table-column label="单位" prop="materialUnit"></el-table-column>
                        <el-table-column label="单位价格" prop="materialUnitPrice" sortable></el-table-column>
                        <el-table-column label="产生金额" prop="transactionAmount" sortable></el-table-column>
                    </el-table>
                </div>
                </template>
            </el-table-column>
            <el-table-column label="应付对象" prop="accountOwnerName"> </el-table-column>
            <el-table-column label="应付余额" prop="accountPayableBalance" sortable></el-table-column>
            <el-table-column button > </el-table-column>

        </el-table>
    </el-container>

    <el-container v-if="!oldNewLayout">
        <el-table :data="display_data" >
            <el-table-column type="expand">
                <template #default="props">
                    <el-table :data="props.row.transactionDetails">
                        <el-table-column type="expand">
                            <template #default="local">
                                <el-table :data="local.materialInbound">

                                </el-table>
                            </template>
                        </el-table-column>
                        <el-table-column label="发生时间" prop="transactionDate" sortable></el-table-column>
                        <el-table-column label="记录类型" prop="transactionType"></el-table-column>
                        <!-- <el-table-column label="材料名称" prop="materialName"></el-table-column>
                        <el-table-column label="材料型号" prop="materialModel"></el-table-column>
                        <el-table-column label="材料规格" prop="materialSpecification"></el-table-column>
                        <el-table-column label="数量" prop="materialAmount" sortable></el-table-column>
                        <el-table-column label="单位" prop="materialUnit"></el-table-column>
                        <el-table-column label="单位价格" prop="materialUnitPrice" sortable></el-table-column> -->
                        <el-table-column label="产生金额" prop="transactionAmount" sortable></el-table-column>
                    </el-table>
                </template>
            </el-table-column>
            <el-table-column label="应付对象" prop="accountOwnerName"></el-table-column>
            <el-table-column label="当前应付余额" prop="accountPayableBalance"></el-table-column>
            <el-table-column label="总应付数额" prop="accountTotalPayable"></el-table-column>
            <el-table-column label="总排款数额" prop="accountTotalPaid"></el-table-column>
        </el-table>

    </el-container>
    <el-dialog title="应付转账录入" v-model="addPayableTransactionDialogVis" style="width:1500px">
        <el-button @click="addTransactionItem"> 添加 </el-button>
        <el-table :data="pendingTransactions" border style="width: 100%">
            <el-table-column label="付款账户名" prop="fromAccountName">
                <template #default="scope">
                  <el-select v-model="scope.row.fromAccountName">
                    <el-option
                        v-for="account in thirdGradeAccounts"
                        :key="account.thirdGradeAccountId"
                        :label="account.thirdGradeAccountName"
                        :value="account.thirdGradeAccountId"
                    >
                    </el-option>
                </el-select>
                </template>
            </el-table-column>
            <el-table-column label="付款日期" prop="transactionDate">
                <template #default="scope">
                <el-date-picker v-model="scope.row.transactionDate">

                </el-date-picker>
                </template>
            </el-table-column>
            <el-table-column label="应受款收款账户名" prop="toAccountName">
                <template #default="scope">
                    <el-select v-model="scope.row.toAccountName">
                    <el-option
                            v-for="payableAccount in payable_data"
                            :key="payableAccount.accountId"
                            :value="payableAccount.accountId"
                            :label="payableAccount.accountOwnerName">
                    </el-option>
                    </el-select>
                </template>
            </el-table-column>
            <el-table-column label="账户总应付金额" prop="accountPayableAmount"></el-table-column>
            <el-table-column label="本次转账金额" prop="transactionAmount">
                <template #default="scope">
                    <el-input v-model="scope.row.transactionAmount">

                    </el-input>
                </template>
            </el-table-column>
            <el-table-column label="账户剩余应付金额" prop="remainingPayableAmount"></el-table-column>
            <el-table-column aligh="right">
                <template #default="scope">
                    <el-button size="small" type="danger" @click="handleDelete(scope.$index, scope.row)">
                        删除
                    </el-button>
                </template>
            </el-table-column>
        </el-table>
        <template #footer>
            <el-button type="plain" @click="closeAddTransactionDialog">
                取消
            </el-button>
            <el-button type="primary" @click="submitNewTransactions">
                提交
            </el-button>
        </template>
    </el-dialog>
</template>
<script setup lang="ts">
import { ref, onMounted, getCurrentInstance } from 'vue'
import axios from 'axios'
import { ElMessage, ElMessageBox ,TabPaneName} from 'element-plus'
import { ITEM_RENDER_EVT } from 'element-plus/es/components/virtual-list/src/defaults'
import { a } from 'vitest/dist/suite-IbNSsUWN'
import { display } from 'html2canvas/dist/types/css/property-descriptors/display'

interface Transaction {
    fromAccountName:string
    toAccountName:string
    transactionAmount:number
}
const $api_baseUrl = getCurrentInstance().appContext.config.globalProperties.$apiBaseUrl
let display_data = ref([])
let showDetails = ref(false)
let oldNewLayout = ref(false)
let payable_data = ref([])
let pendingTransactions = ref([])
let addPayableTransactionDialogVis = ref(false)
let thirdGradeAccounts = ref([])
let currentDateTime = ref(new Date((new Date()).getTime() - (new Date()).getTimezoneOffset() * 60000).toISOString().slice(0, 19).replace('T', ' '))
onMounted(()=>{
    getAllPayableInfo()
    getThirdGradeAccountInfo()
    getAllPayableInfoNew()
})
async function getAllPayableInfo(){
    const res = await axios.get($api_baseUrl + `/payable_management/get_payable_info`)
    payable_data.value = res.data.payableInfo
}
async function getAllPayableInfoNew(){
    const res = await axios.get($api_baseUrl + `/payable_management/get_payable_info_new`)
    display_data.value = res.data.payableInfo
    console.log(display_data.value)
}
async function getThirdGradeAccountInfo(){
    const res = await axios.get($api_baseUrl + `/accountsmanagement/thirdgrade/getaccounts`)
    thirdGradeAccounts.value = res.data.thirdGradeAccountList
}
async function submitNewTransactions(){
    const res = await axios.post($api_baseUrl + `/payable_management/add_transactions`,
        {
            data:pendingTransactions.value
        }
    )
    pendingTransactions.value = []
    return 
}
// async function queryMaterialInboundDetail(row){
//     console.log(row)
//     console.log(1)
//     return
// }
function openAddPayableTransactionDialog(){
    addPayableTransactionDialogVis.value = true
}
function closeAddTransactionDialog(){
    addPayableTransactionDialogVis.value = false
}
function addTransactionItem(){
    pendingTransactions.value.push({transactionDate:currentDateTime})
    return
}
function handleDelete(index:number, row:Transaction)
{
    console.log(index)
    console.log(row)
    pendingTransactions.value.splice(index,1)
}

</script>
<style scoped></style>