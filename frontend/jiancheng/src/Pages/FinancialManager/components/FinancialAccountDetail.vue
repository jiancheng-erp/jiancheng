<template>
    <el-container>
        <el-tabs tab-position="left" style="height: 700px" @tab-click="updateSecondGradeTabs">
            <el-tab-pane v-for="firstGradeAccount in firstGradeAccounts" :label="firstGradeAccount.firstGradeAccountName" 
            :key="firstGradeAccount.firstGradeAccountId" :name="firstGradeAccount.firstGradeAccountId">
                <el-container>

                    <el-tabs tab-position="left" style="height:700px" @tab-click="updateThirdGradeTabs">
                        <el-tab-pane v-for="secondGradeAccount in secondGradeAccounts" :label="secondGradeAccount.secondGradeAccountName"
                        :key="secondGradeAccount.secondGradeAccountId" :name="secondGradeAccount.secondGradeAccountId">
                        <el-container>
                            <el-tabs tab-position="left" style="height:700px" @tab-click="updateThirdGradeInfo">
                                <el-tab-pane v-for="thirdGradeAccount in thirdGradeAccounts" :label="thirdGradeAccount.thirdGradeAccountName"
                                :key="thirdGradeAccount.thirdGradeAccountId" :name="thirdGradeAccount.thirdGradeAccountId">
                            </el-tab-pane>
                            </el-tabs>
                            "TODO"
                            科目下信息展示
                            <!-- <el-form>
                                <el-form-item v-model = secondGradeAccounts>

                                </el-form-item>
                            </el-form> -->
                        </el-container>
                        </el-tab-pane>
                    </el-tabs>
                </el-container>
            </el-tab-pane>
        </el-tabs>
    </el-container>
</template>


<script lang="ts" setup>
import { ref, onMounted, getCurrentInstance } from 'vue'
import axios from 'axios'
import { ElMessage, ElMessageBox ,TabPaneName} from 'element-plus'
import { ITEM_RENDER_EVT } from 'element-plus/es/components/virtual-list/src/defaults'
let firstGradeAccounts = ref([])
let secondGradeAccounts = ref([])
let thirdGradeAccounts = ref([])
const $api_baseUrl = getCurrentInstance().appContext.config.globalProperties.$apiBaseUrl
let currentDisplayAccountName = ref('')
let currentDisplayAccountBalance = ref('')
let currentDisplayRecords = ref([])
onMounted(()=>{
    getAllAccounts()
})
async function getAllAccounts(){
    const res = await axios.get($api_baseUrl + `/accountsmanagement/getallaccounts`)
    firstGradeAccounts.value = res.data.firstGradeAccountsMapping
    console.log(firstGradeAccounts.value)
}

function updateSecondGradeTabs(targetName: TabPaneName){
    console.log(firstGradeAccounts.value)
    secondGradeAccounts.value = firstGradeAccounts.value[targetName['paneName']].associatedSecondGradeAccount
}
function updateThirdGradeTabs(targetName: TabPaneName){
    console.log(secondGradeAccounts.value)
    thirdGradeAccounts.value = secondGradeAccounts.value.find((account)=> account.secondGradeAccountId == targetName['paneName']).associatedThirdGradeAccount
}
function updateThirdGradeInfo(targetName: TabPaneName){
    console.log(targetName['paneName'])
}

</script>

<!-- // let selectOption1 = ref([])
// let selectOption2 = ref([])
// let selectOption3 = ref([])
// const $api_baseUrl = getCurrentInstance().appContext.config.globalProperties.$apiBaseUrl
// let dialogVisible = ref(false)
// let dialogVisible1 = ref(false)
// const itemValue = ref('');
// const projectItem1 = ref('');
// const projectItem2 = ref('');
// const operateType = ref('');
// const first_grade_account_name = ref('');
// const second_grade_account_name = ref('');
// const third_grade_account_name = ref('');
// let allAccounts = ref([])
// let addType = ref(0);
// let modifyType = ref(0);

// onMounted(() => {
//     getItemType()
// })

// async function getItemType() {
//     selectOption1.value = []
//     selectOption2.value = []
//     selectOption3.value = []
//     itemValue.value = ''
//     projectItem1.value = ''
//     projectItem2.value = ''
//     first_grade_account_name.value = ''
//     second_grade_account_name.value = ''
//     third_grade_account_name.value = ''
//     const res = await axios.get($api_baseUrl + `/accountsmanagement/getallaccounts`)
//     allAccounts.value = res.data.firstGradeAccountsMapping
//     selectOption1.value = res.data.firstGradeAccountsMapping
// }
// function addData() {
//     if (addType.value == 1) {
//         axios.post($api_baseUrl + `/accountsmanagement/firstgrade/addaccount`, {
//             first_grade_account_name: first_grade_account_name.value
//         }).then(res => {
//             ElMessage.success('添加成功')
//             dialogVisible.value = false
//             getItemType()
//         }).catch((error) => {
//             ElMessage.error('添加失败,失败原因：' + error.response.data.msg)
//         })
//     } else if (addType.value == 2) {
//         axios.post($api_baseUrl + `/accountsmanagement/secondgrade/addaccount`, {
//             account_belongs_fg: itemValue.value,
//             second_grade_account_name: second_grade_account_name.value
//         }).then(res => {
//             ElMessage.success('添加成功')
//             dialogVisible.value = false
//             getItemType()
//         }).catch((error) => {
//             ElMessage.error('添加失败,失败原因：' + error.response.data.msg)
//         })
//     } else {
//         axios.post($api_baseUrl + `/accountsmanagement/thirdgrade/addaccount`, {
//             third_grade_account_name: third_grade_account_name.value,
//             account_belongs_sg: projectItem1.value
//         }).then(res => {
//             ElMessage.success('添加成功')
//             dialogVisible.value = false
//             getItemType()
//         }).catch((error) => {
//             ElMessage.error('添加失败,失败原因：' + error.response.data.msg)
//         })
//     }
// }
// function addProject(val) {
//     dialogVisible.value = true;
//     switch (val) {
//         case 1:
//             operateType.value = '添加项目类别'
//             addType.value = 1
//             break;
    
//         case 2:
//             operateType.value = '添加一级科目'
//             addType.value = 2
//             break;

//         case 3:
//             operateType.value = '添加二级科目'
//             addType.value = 3
//             break;
//     }
// }

// function deleteItem(value){
//     switch (value) {
//         case 1:
            
//             break;
    
//         case 2:
        
//             break;

//         case 3:
        
//             break;
//     }
// }

// function updateItem(value){
//     dialogVisible1.value = true;
//     switch (value) {
//         case 1:
//             operateType.value = '修改项目类别'
//             modifyType.value = 1
//             break;
    
//         case 2:
//             operateType.value = '修改一级科目'
//             modifyType.value = 2
//             break;

//         case 3:
//             operateType.value = '修改二级科目'
//             modifyType.value = 3
//             break;
//     }
// }

// function updateData () {
//     if (modifyType.value == 1) {
//         axios.post($api_baseUrl + `/accountsmanagement/firstgrade/updateaccountname`, {
//             accountId: itemValue.value,
//             accountNameOld: selectOption1.value[itemValue.value].firstGradeAccountName,
//             accountNameNew: first_grade_account_name.value
//         }).then(res => {
//             ElMessage.success('添加成功')
//             dialogVisible1.value = false
//             getItemType()
//         }).catch((error) => {
//             ElMessage.error('添加失败,失败原因：' + error.response.data.msg)
//         })
//     } else if (modifyType.value == 2) {
//         axios.post($api_baseUrl + `/accountsmanagement/secondgrade/updateaccountname`, {
//             accountId: projectItem1.value,
//             accountNameOld: selectOption2.value.find((item) => item.secondGradeAccountId == projectItem1.value).secondGradeAccountName,
//             accountNameNew: second_grade_account_name.value
//         }).then(res => {
//             ElMessage.success('添加成功')
//             dialogVisible1.value = false
//             getItemType()
//         }).catch((error) => {
//             ElMessage.error('添加失败,失败原因：' + error.response.data.msg)
//         })
//     } else {
//         axios.post($api_baseUrl + `/accountsmanagement/thirdgrade/updateaccountname`, {
//             accountId: projectItem2.value,
//             accountNameOld: selectOption3.value.find((item) => item.thirdGradeAccountId == projectItem2.value).thirdGradeAccountName,
//             accountNameNew: third_grade_account_name.value
//         }).then(res => {
//             ElMessage.success('添加成功')
//             dialogVisible1.value = false
//             getItemType()
//         }).catch((error) => {
//             ElMessage.error('添加失败,失败原因：' + error.response.data.msg)
//         })
//     }
// }

// function findNextItem(val){
//     if (val == 1) {
//         selectOption2.value = []
//         selectOption3.value = []
//         projectItem1.value = ''
//         projectItem2.value = ''
//     } else {
//         selectOption3.value = []
//         projectItem2.value = ''
//     }
//     if (!itemValue.value) {
//         return;
//     } else {
//         selectOption2.value = allAccounts.value[itemValue.value].associatedSecondGradeAccounts
//         if (!projectItem1.value) {
//             return;
//         } else {
//             selectOption3.value = selectOption2.value.find((item) => item.secondGradeAccountId == projectItem1.value).associatedThirdGradeAccounts
//         }
//     }
// }
//  -->
