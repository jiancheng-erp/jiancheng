<template>
    <div class="content">财务应付信息</div>

    <el-button @click="getAllPayableInfo">
        button
    </el-button>
    <el-button @click="openAddPayableTransactionDialog">
        button2
    </el-button>
    <el-switch v-model="showDetails"></el-switch>
    <el-container>
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
            <el-table-column label="Name" prop="accountOwnerName"> </el-table-column>
            <el-table-column label="Balance" prop="accountPayableBalance" sortable></el-table-column>
            <el-table-column button > </el-table-column>

        </el-table>
    </el-container>
    <el-dialog title="应付转账录入" v-model="addPayableTransactionDialogVis" style="width:1500px">
        <el-button @click="addTransactionItem"> add </el-button>
        <el-table :data="pendingTransactions">
            <el-table-column label="付款账户名" prop="fromAccountName"></el-table-column>
            <el-table-column label="付款日期" prop="transactionDate"></el-table-column>
            <el-table-column label="应受款收款账户名" prop="toAccountName"></el-table-column>
            <el-table-column label="总金额" prop="transactioAmount"></el-table-column>
        </el-table>

    </el-dialog>
</template>
<script setup lang="ts">
import { ref, onMounted, getCurrentInstance } from 'vue'
import axios from 'axios'
import { ElMessage, ElMessageBox ,TabPaneName} from 'element-plus'
import { ITEM_RENDER_EVT } from 'element-plus/es/components/virtual-list/src/defaults'
import { a } from 'vitest/dist/suite-IbNSsUWN'
const $api_baseUrl = getCurrentInstance().appContext.config.globalProperties.$apiBaseUrl
let display_data = ref([])
let showDetails = ref(false)
let payable_data = ref([])
let pendingTransactions = ref([])
let addPayableTransactionDialogVis = ref(false)
onMounted(()=>{
    getAllPayableInfo()
})
async function getAllPayableInfo(){
    const res = await axios.get($api_baseUrl + `/payable_management/get_payable_info`)
    payable_data.value = res.data.payableInfo
    console.log(payable_data.value)
}

function openAddPayableTransactionDialog(){
    addPayableTransactionDialogVis.value = true
}
function addTransactionItem(){
    pendingTransactions.value.push({})
    return
}
</script>
<style scoped></style>