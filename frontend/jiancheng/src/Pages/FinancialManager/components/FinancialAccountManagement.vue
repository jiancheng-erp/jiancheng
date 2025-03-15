<template>
    <el-container class="header">
        财务账户设置
    </el-container>
        <el-form >
            <el-button class="aside-item" size = "small" @click="openAddFirstGradeAccountDialog">
            填加一级科目
            </el-button>
            <el-button class="aside-item" size = "small" @click="openAddSecondGradeAccountDialog">
            填加二级科目
            </el-button>
            <el-button class="aside-item" size = "small" @click="openAddThirdGradeAccountDialog">
            填加三级科目
            </el-button>
            <!-- <el-button size = "small" @click="openPayableAccountConfigureDialog">
            设置应付账目所属
            </el-button>
            <el-button size="small" @click="openRecievableAccountConfigureDialog">
            设置应收账目所属
            </el-button> -->
        </el-form>
    <!-- <el-form-item>
                "TODO"
                "设置各仓库入库材料默认三级账号"
                "设置应付款 应收款默认三级账号"
                "设置各级账号功能及与应收应付关系"
    </el-form-item> -->

    <el-dialog title="一级财务项目" v-model="addFirstGradeAccountDialogVis" :before-close="handleClose">
        <el-form>
            <el-form-item label="项目名称">
                <el-input v-model="newFirstGradeAccountName">
                </el-input>
                <el-footer>
                    <el-button @click="closeAddFirstDialog">
                          取消
                    </el-button>
                    <el-button @click="addFirstGradeAccount">
                          确认
                    </el-button>
                </el-footer>
            </el-form-item>
        </el-form>
    </el-dialog>

    <el-dialog title="二级财务项目" v-model="addSecondGradeAccountDialogVis" :before-close="handleClose">
        <el-form>
            <el-select
           v-model ="firstGradeAccountBelonged"
           placeholder="请选择科目"
           style="width:300px"
           clearable
           filterable
           >
           <el-option
           v-for="firstGradeAccount in displayFirstGradeAccounts"
           :key="firstGradeAccount.firstGradeAccountId"
           :label="firstGradeAccount.firstGradeAccountName"
           :value="firstGradeAccount.firstGradeAccountId">

           </el-option>
            </el-select>

                <el-form-item label="二级项目名称">
                    <el-input v-model="newSecondGradeAccountName">
                    </el-input>
                    <el-footer>
                        <el-button @click="closeAddSecondDialog">
                            取消
                        </el-button>
                        <el-button @click="addSecondGradeAccount">
                            确认
                        </el-button>
                    </el-footer>
                </el-form-item>
        </el-form>
    </el-dialog>
        
    
    <el-dialog title="三级财务项目" v-model="addThirdGradeAccountDialogVis" :before-close="handleClose">
        <el-form>
    <el-select
            v-model ="selectedFirstGradeAccount"
            placeholder="请选择一级科目"
            style="width:300px"
            clearable
            filterable
            @change="updateSecondGradeAccounts"
            >
            <el-option
            v-for="firstGradeAccount in displayFirstGradeAccounts"
            :key="firstGradeAccount.firstGradeAccountId"
            :label="firstGradeAccount.firstGradeAccountName"
            :value="firstGradeAccount.firstGradeAccountId">

            </el-option>
                </el-select>
                <el-select
                v-model = "secondGradeAccountBelonged"
                placeholder="请选择二级科目"
                style="width:300px"
                clearable
                filterable
                >
                <el-option
                v-for="secondGradeAccount in displaySecondGradeAccounts"
                :key="secondGradeAccount.secondGradeAccountId"
                :label="secondGradeAccount.secondGradeAccountName"
                :value="secondGradeAccount.secondGradeAccountId"
                >

                </el-option>
                </el-select>
                <el-select
                    v-model="newThirdGradeAccountTypeId"
                    placeholder="请选择三级科目种类"
                    style="width:300px"
                    clearable
                    filterable
                    >
                    <el-option
                    v-for="accountType in accountTypes"
                    :key="accountType.typeId"
                    :label="accountType.typeName"
                    :value="accountType.typeId"
                    >
                </el-option>
                </el-select>
                <el-form-item label="三级科目名称">
                    <el-input v-model="newThirdGradeAccountName">
                    </el-input>
                </el-form-item>
        </el-form>
        <template #footer>
            <el-button type="primary" @click="closeAddThirdDialog">
                取消
            </el-button>
            <el-button @click="addThirdGradeAccount">
                确认
            </el-button>
        </template>
    </el-dialog>
    <el-dialog title="设置应付账目所属" v-model="payableAccountConfigureDialogVis">
        <el-row>
            当前应付账目所属信息
            <el-table :data="payableAccountInfo">
                <el-table-column prop="accountName" label="账目名称"></el-table-column>
                <el-table-column prop="accountBoundEvent" label="科目绑定事件"></el-table-column>
            </el-table>
        </el-row>
        <el-form>
            <el-form-item label="科目应付事件"></el-form-item>
            <el-select v-model="boundPayableEventTypeId" placeholder="请选择科目应付事件"
            >
            <el-option v-for="payableType in payableTypes"
                        :key="payableType.typeId"
                        :label="payableType.typeName"
                        :value="payableType.typeId">
            </el-option>
            </el-select>
            
            <el-form-item label="事件所属三级科目"></el-form-item>
            <el-select v-model="boundThirdGradeAccount" placeholder="设置所属三级科目">
            <el-option v-for="account in payableBoudableAccounts"
            :key="account.thirdGradeAccountId"
            :label="account.thirdGradeAccountName"
            :value="account.thirdGradeAccountId"
            </el-option>
            </el-select>
        </el-form>
        <template #footer>
            <el-button type="primary" @click="boundPayableAccountEvent">confirm</el-button>
        </template>   
        
        
    </el-dialog>
</template>
<script setup lang="ts">
import { ref, onMounted, getCurrentInstance } from 'vue'
import axios from 'axios'
import { ElMessage, ElMessageBox ,TabPaneName} from 'element-plus'
import { ITEM_RENDER_EVT } from 'element-plus/es/components/virtual-list/src/defaults'
const $api_baseUrl = getCurrentInstance().appContext.config.globalProperties.$apiBaseUrl
let addFirstGradeAccountDialogVis = ref(false)
let addSecondGradeAccountDialogVis = ref(false)
let addThirdGradeAccountDialogVis = ref(false)
let payableAccountConfigureDialogVis = ref(false)
let recievableAccountConfigureDialogVis = ref(false)
let newFirstGradeAccountName = ref('')
let newSecondGradeAccountName = ref('')
let newThirdGradeAccountName = ref('')
let newThirdGradeAccountTypeId =ref('')
let firstGradeAccountBelonged = ref('')
let secondGradeAccountBelonged = ref('')
let displayFirstGradeAccounts = ref([])
let displaySecondGradeAccounts = ref([])
let displayThirdGradeAccounts = ref([])
let selectedFirstGradeAccount = ref('')

let firstGradeAccounts = ref([])
let secondGradeAccounts = ref([])
let thirdGradeAccounts = ref([])

let accountTypes = ref([
    {"typeId":"0", "typeName":"应收账户"},{"typeId":"1", "typeName":"应付账户"},
    {"typeId":"2", "typeName":"现金账户"},{"typeId":"3", "typeName":"付款账户"},
    {"typeId":"4","typeName":"收款账户"}
])
let payableTypes = ref([
    {"typeId":"0", "typeName":"材料采购入库产生应付","typeSymbolDb":"I"},{"typeId":"1", "typeName":"委外加工入库产生应付","typeSymbolDb":"C"},
    {"typeId":"3", "typeName":"其他类型入库产生应付","typeSymbolDb":"M"}
])
let recievableTypes = ref([
    {"typeId":"0", "typeName":"订单货款应收", "typeSymbolDb":"O"},{"typdId":"1", "typeName":"其他产生应收", "typeSymbolDb":"E"}
])

let boundPayableEventTypeId = ref('')

let boundThirdGradeAccount = ref('')
let payableAssociatedAccounts = ref([])
let payableBoudableAccounts = ref([])
let recievablAssociatedAccounts = ref([])
let payableAccountInfo = ref([])
let recievableAccountInfo = ref([])
onMounted(()=>{
    getAllAccounts()
    getBoundInfo()
})
async function getAllAccounts(){
    const res = await axios.get($api_baseUrl + `/accountsmanagement/getallaccounts`)
    displayFirstGradeAccounts.value = res.data.firstGradeAccountsMapping
    firstGradeAccounts.value = res.data.firstGradeAccountsMapping
}
async function getBoundInfo(){
    const third_res = await axios.get($api_baseUrl + `/accountsmanagement/thirdgrade/getaccounts`)
    thirdGradeAccounts.value = third_res.data.thirdGradeAccountList
    payableBoudableAccounts.value = thirdGradeAccounts.value.filter(account => account.thirdGradeAccountType==='1' && account.thirdGradeAccountBoundEvent===null)
    const bound_info_res = await axios.get($api_baseUrl + `/accountsmanagement/thirdgrade/getboundinfo`)
    payableAccountInfo.value = bound_info_res.data.payableBoundInfo
    recievableAccountInfo.value = bound_info_res.data.recievableBoundInfo
}
function testing(){
//    axios.get($api_baseUrl + `/accountsmanagement/performancetesting`)
}
function openAddFirstGradeAccountDialog(){
    addFirstGradeAccountDialogVis.value = true
}
function openAddSecondGradeAccountDialog(){
    addSecondGradeAccountDialogVis.value = true
}
function openAddThirdGradeAccountDialog(){
    addThirdGradeAccountDialogVis.value = true
}
function openPayableAccountConfigureDialog(){
    payableAccountConfigureDialogVis.value = true
}
function openRecievableAccountConfigureDialog(){
    recievableAccountConfigureDialogVis.value = true
}
async function addFirstGradeAccount(){
    const res = await axios.post($api_baseUrl +　`/accountsmanagement/firstgrade/addaccount`,{'firstGradeAccountName':newFirstGradeAccountName.value})
    newFirstGradeAccountName.value = ''
    addFirstGradeAccountDialogVis.value = false
    await getAllAccounts()
    await getBoundInfo()

}
async function addSecondGradeAccount(){
    console.log(newSecondGradeAccountName.value)
    const res = await axios.post($api_baseUrl +　`/accountsmanagement/secondgrade/addaccount`,{'secondGradeAccountName':newSecondGradeAccountName.value,
        'firstGradeAccountBelonged':firstGradeAccountBelonged.value
    })
    firstGradeAccountBelonged.value = ''
    newSecondGradeAccountName.value = ''
    addSecondGradeAccountDialogVis.value = false
    await getAllAccounts()
    await getBoundInfo()

}
async function addThirdGradeAccount(){
    console.log(newThirdGradeAccountName.value)
    console.log(secondGradeAccountBelonged.value)
    console.log(newThirdGradeAccountTypeId.value)
    const res = await axios.post($api_baseUrl + `/accountsmanagement/thirdgrade/addaccount`,
        {"thirdGradeAccountName":newThirdGradeAccountName.value,
         "secondGradeAccountBelonged":secondGradeAccountBelonged.value,
         "thirdGradeAccountType":newThirdGradeAccountTypeId.value 
        }
    )
    newThirdGradeAccountName.value = ''
    secondGradeAccountBelonged.value = ''
    newThirdGradeAccountTypeId.value = ''
    addThirdGradeAccountDialogVis.value = false
    await getAllAccounts()
    await getBoundInfo()

}
async function boundPayableAccountEvent(){
    const res = await axios.post($api_baseUrl + `/accountsmanagement/thirdgrade/boundpayableaccount`,
        {"boundThirdGradeAccountId":boundThirdGradeAccount.value,
         "boundPayableEventTypeEnum": payableTypes.value.find((payable_type) => {
            return payable_type.typeId == boundPayableEventTypeId.value
         }).typeSymbolDb
        }
    )
    await getBoundInfo()
    boundPayableEventTypeId.value = ''
    boundThirdGradeAccount.value = ''
    payableAccountConfigureDialogVis.value = false
}
function updateSecondGradeAccounts(){
    displaySecondGradeAccounts.value = displayFirstGradeAccounts.value[selectedFirstGradeAccount.value].associatedSecondGradeAccount
}

function closeAddFirstDialog(){
    addFirstGradeAccountDialogVis.value = false
}
function closeAddSecondDialog(){
    addSecondGradeAccountDialogVis.value = false
}
function closeAddThirdDialog(){
    addThirdGradeAccountDialogVis.value = false
}
const handleClose = (done:() => void) => {
    ElMessageBox.confirm("close the dialog?")
    .then(()=>{
        done()
    })
    .catch(()=>{
        //catch error
    })
}


</script>
<style scoped>
</style>