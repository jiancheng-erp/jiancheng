<template>
    <div>财务项目设置管理</div>
    <el-container>
        <div position="left">
            <el-button size = "small" @click="openAddFirstGradeAccountDialog">
            填加一级科目
            </el-button>
            <el-button size = "small" @click="openAddSecondGradeAccountDialog">
            填加二级科目
            </el-button>
            <el-button size = "small" @click="testing">
                test 
            </el-button>
            <el-form>
                <el-form-item>
                    "TODO"
                    "设置各仓库入库材料默认三级账号"
                    "设置应付款 应收款默认三级账号"
                    "设置各级账号功能及与应收应付关系"
                </el-form-item>
            </el-form>
        </div>
    </el-container>
    

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
           v-for="firstGradeAccount in firstGradeAccounts"
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
    
</template>
<script setup lang="ts">
import { ref, onMounted, getCurrentInstance } from 'vue'
import axios from 'axios'
import { ElMessage, ElMessageBox ,TabPaneName} from 'element-plus'
import { ITEM_RENDER_EVT } from 'element-plus/es/components/virtual-list/src/defaults'
const $api_baseUrl = getCurrentInstance().appContext.config.globalProperties.$apiBaseUrl
let addFirstGradeAccountDialogVis = ref(false)
let addSecondGradeAccountDialogVis = ref(false)
let newFirstGradeAccountName = ref('')
let newSecondGradeAccountName = ref('')
let firstGradeAccountBelonged = ref('')

let firstGradeAccounts = ref([])
let secondGradeAccounts = ref([])
let thirdGradeAccounts = ref([])

onMounted(()=>{
    getAllAccounts()
})
async function getAllAccounts(){
    const res = await axios.get($api_baseUrl + `/accountsmanagement/getallaccounts`)
    firstGradeAccounts.value = res.data.firstGradeAccountsMapping
    console.log(firstGradeAccounts.value)
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
async function addFirstGradeAccount(){
    const res = await axios.post($api_baseUrl +　`/accountsmanagement/firstgrade/addaccount`,{'firstGradeAccountName':newFirstGradeAccountName.value})
}
async function addSecondGradeAccount(){
    console.log(newSecondGradeAccountName.value)
    const res = await axios.post($api_baseUrl +　`/accountsmanagement/secondgrade/addaccount`,{'secondGradeAccountName':newSecondGradeAccountName.value,
        'firstGradeAccountBelonged':firstGradeAccountBelonged.value
    })
}
function closeAddFirstDialog(){
    addFirstGradeAccountDialogVis.value = false
}
function closeAddSecondDialog(){
    addSecondGradeAccountDialogVis.value = false
}
const handleClose = (done:() => void) => {
    console.log(newFirstGradeAccountName)
    ElMessageBox.confirm("close the dialog?")
    .then(()=>{
        done()
    })
    .catch(()=>{
        //catch error
    })
}

</script>
<style scoped></style>