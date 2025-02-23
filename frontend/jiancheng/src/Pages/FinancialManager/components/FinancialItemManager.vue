<template>
    <el-form label-position="right" label-width="auto" size="default">
        <el-form-item
            label="项目类别"
            :rules="[
                { required: true, message: '项目类别不能为空' },
                { type: 'String ', message: '项目类别不能为空' }
            ]"
        >
            <el-select
                v-model="itemValue"
                placeholder="请选择项目类别"
                size="large"
                style="width: 300px"
                clearable
                filterable
                @change="findNextItem(1)"
            >
                <el-option
                    v-for="item in selectOption1"
                    :key="item.firstGradeAccountName"
                    :label="item.firstGradeAccountName"
                    :value="item.firstGradeAccountId"
                />
            </el-select>
            <span
                style="margin-left: 20px; color: dodgerblue; cursor: pointer"
                @click="addProject(1)"
                >没有？点我添加</span
            >
            <span
                style="margin-left: 20px; color: red; cursor: pointer"
                @click="deleteItem(1)"
                >删除</span
            >
            <span
                style="margin-left: 20px; color: #e6a23c; cursor: pointer"
                @click="updateItem(1)"
                >更正</span
            >
        </el-form-item>
        <el-form-item
            label="一级科目"
            :rules="[
                { required: true, message: '一级科目不能为空' },
                { type: 'String ', message: '一级科目不能为空' }
            ]"
        >
            <el-select
                v-model="projectItem1"
                placeholder="请选择一级科目"
                size="large"
                style="width: 300px"
                clearable
                filterable
                @change="findNextItem(2)"
            >
                <el-option
                    v-for="item in selectOption2"
                    :key="item.secondGradeAccountName"
                    :label="item.secondGradeAccountName"
                    :value="item.secondGradeAccountId"
                />
            </el-select>
            <span style="margin-left: 20px; color: dodgerblue; cursor: pointer" @click="addProject(2)"
                >没有？点我添加</span
            >
            <span
                style="margin-left: 20px; color: red; cursor: pointer"
                @click="deleteItem(2)"
                >删除</span
            >
            <span
                style="margin-left: 20px; color: #e6a23c; cursor: pointer"
                @click="updateItem(2)"
                >更正</span
            >
        </el-form-item>
        <el-form-item
            label="二级科目"
            :rules="[
                { required: true, message: '二级科目不能为空' },
                { type: 'String ', message: '二级科目不能为空' }
            ]"
        >
            <el-select
                v-model="projectItem2"
                placeholder="请选择二级科目"
                size="large"
                style="width: 300px"
                clearable
                filterable
            >
                <el-option
                    v-for="item in selectOption3"
                    :key="item.thirdGradeAccountName"
                    :label="item.thirdGradeAccountName"
                    :value="item.thirdGradeAccountId"
                />
            </el-select>
            <span style="margin-left: 20px; color: dodgerblue; cursor: pointer" @click="addProject(3)"
                >没有？点我添加</span
            >
            <span
                style="margin-left: 20px; color: red; cursor: pointer"
                @click="deleteItem(3)"
                >删除</span
            >
            <span
                style="margin-left: 20px; color: #e6a23c; cursor: pointer"
                @click="updateItem(3)"
                >更正</span
            >
        </el-form-item>
    </el-form>
    <el-dialog :title="operateType" v-model="dialogVisible" width="50%">
        <el-form label-width="100px" style="max-width: 460px">
            <el-form-item label="项目类别" v-if="addType == 1">
                <el-input :rows="2" v-model="first_grade_account_name" />
            </el-form-item>
            <el-form-item label="项目类别" v-else>
            <el-select
                v-model="itemValue"
                placeholder="请选择项目类别"
                size="large"
                style="width: 300px"
                clearable
                filterable
                @change="findNextItem(1)"
            >
                <el-option
                    v-for="item in selectOption1"
                    :key="item.firstGradeAccountName"
                    :label="item.firstGradeAccountName"
                    :value="item.firstGradeAccountId"
                />
            </el-select>
            </el-form-item>
            <el-form-item label="一级科目名称" v-if="addType == 2">
                <el-input :rows="2" v-model="second_grade_account_name" />
            </el-form-item>
            <el-form-item label="一级科目名称" v-if="addType == 3">
            <el-select
                v-model="projectItem1"
                placeholder="请选择一级科目"
                size="large"
                style="width: 300px"
                clearable
                filterable
                @change="findNextItem(2)"
            >
                <el-option
                    v-for="item in selectOption2"
                    :key="item.secondGradeAccountName"
                    :label="item.secondGradeAccountName"
                    :value="item.secondGradeAccountId"
                />
            </el-select>
            </el-form-item>
            <el-form-item label="二级科目名称" v-if="addType == 3">
                <el-input :rows="2" v-model="third_grade_account_name" />
            </el-form-item>
            <el-form-item>
                <el-button type="danger" @click="dialogVisible = false">取消</el-button>
                <el-button type="primary" @click="addData">确定</el-button>
            </el-form-item>
        </el-form>
    </el-dialog>
    <el-dialog :title="operateType" v-model="dialogVisible1" width="50%">
        <el-form label-width="200px" style="max-width: 460px">
            <el-form-item label="请选择修改的项目类别">
                <el-select
                    v-model="itemValue"
                    placeholder="请选择项目类别"
                    size="large"
                    style="width: 300px"
                    clearable
                    filterable
                    @change="findNextItem(1)"
                >
                    <el-option
                        v-for="item in selectOption1"
                        :key="item.firstGradeAccountName"
                        :label="item.firstGradeAccountName"
                        :value="item.firstGradeAccountId"
                    />
                </el-select>
            </el-form-item>
            <el-form-item label="新的的项目类别名称" v-if="modifyType == 1">
                <el-input :rows="2" v-model="first_grade_account_name" />
            </el-form-item>
            <el-form-item label="请选择修改的一级科目" v-if="modifyType != 1">
                <el-select
                    v-model="projectItem1"
                    placeholder="请选择一级科目"
                    size="large"
                    style="width: 300px"
                    clearable
                    filterable
                    @change="findNextItem(2)"
                >
                    <el-option
                        v-for="item in selectOption2"
                        :key="item.secondGradeAccountName"
                        :label="item.secondGradeAccountName"
                        :value="item.secondGradeAccountId"
                    />
                </el-select>
            </el-form-item>
            <el-form-item label="新的的一级科目名称" v-if="modifyType == 2">
                <el-input :rows="2" v-model="second_grade_account_name" />
            </el-form-item>
            <el-form-item label="请选择修改的二级科目" v-if="modifyType == 3">
                <el-select
                    v-model="projectItem2"
                    placeholder="请选择二级科目"
                    size="large"
                    style="width: 300px"
                    clearable
                    filterable
                >
                    <el-option
                        v-for="item in selectOption3"
                        :key="item.thirdGradeAccountName"
                        :label="item.thirdGradeAccountName"
                        :value="item.thirdGradeAccountId"
                    />
                </el-select>
            </el-form-item>
            <el-form-item label="新的的二级科目名称" v-if="modifyType == 3">
                <el-input :rows="2" v-model="third_grade_account_name" />
            </el-form-item>
            <el-form-item>
                <el-button type="danger" @click="dialogVisible1 = false">取消</el-button>
                <el-button type="primary" @click="updateData">确定</el-button>
            </el-form-item>
        </el-form>
    </el-dialog>
</template>

<script lang="js" setup>
import { ref, onMounted, getCurrentInstance } from 'vue'
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'

let selectOption1 = ref([])
let selectOption2 = ref([])
let selectOption3 = ref([])
const $api_baseUrl = getCurrentInstance().appContext.config.globalProperties.$apiBaseUrl
let dialogVisible = ref(false)
let dialogVisible1 = ref(false)
const itemValue = ref('');
const projectItem1 = ref('');
const projectItem2 = ref('');
const operateType = ref('');
const first_grade_account_name = ref('');
const second_grade_account_name = ref('');
const third_grade_account_name = ref('');
let allAccounts = ref([])
let addType = ref(0);
let modifyType = ref(0);

onMounted(() => {
    getItemType()
})

async function getItemType() {
    selectOption1.value = []
    selectOption2.value = []
    selectOption3.value = []
    itemValue.value = ''
    projectItem1.value = ''
    projectItem2.value = ''
    first_grade_account_name.value = ''
    second_grade_account_name.value = ''
    third_grade_account_name.value = ''
    const res = await axios.get($api_baseUrl + `/accountsmanagement/getallaccounts`)
    allAccounts.value = res.data.firstGradeAccountsMapping
    selectOption1.value = res.data.firstGradeAccountsMapping
}
function addData() {
    if (addType.value == 1) {
        axios.post($api_baseUrl + `/accountsmanagement/firstgrade/addaccount`, {
            first_grade_account_name: first_grade_account_name.value
        }).then(res => {
            ElMessage.success('添加成功')
            dialogVisible.value = false
            getItemType()
        }).catch((error) => {
            ElMessage.error('添加失败,失败原因：' + error.response.data.msg)
        })
    } else if (addType.value == 2) {
        axios.post($api_baseUrl + `/accountsmanagement/secondgrade/addaccount`, {
            account_belongs_fg: itemValue.value,
            second_grade_account_name: second_grade_account_name.value
        }).then(res => {
            ElMessage.success('添加成功')
            dialogVisible.value = false
            getItemType()
        }).catch((error) => {
            ElMessage.error('添加失败,失败原因：' + error.response.data.msg)
        })
    } else {
        axios.post($api_baseUrl + `/accountsmanagement/thirdgrade/addaccount`, {
            third_grade_account_name: third_grade_account_name.value,
            account_belongs_sg: projectItem1.value
        }).then(res => {
            ElMessage.success('添加成功')
            dialogVisible.value = false
            getItemType()
        }).catch((error) => {
            ElMessage.error('添加失败,失败原因：' + error.response.data.msg)
        })
    }
}
function addProject(val) {
    dialogVisible.value = true;
    switch (val) {
        case 1:
            operateType.value = '添加项目类别'
            addType.value = 1
            break;
    
        case 2:
            operateType.value = '添加一级科目'
            addType.value = 2
            break;

        case 3:
            operateType.value = '添加二级科目'
            addType.value = 3
            break;
    }
}

function deleteItem(value){
    switch (value) {
        case 1:
            
            break;
    
        case 2:
        
            break;

        case 3:
        
            break;
    }
}

function updateItem(value){
    dialogVisible1.value = true;
    switch (value) {
        case 1:
            operateType.value = '修改项目类别'
            modifyType.value = 1
            break;
    
        case 2:
            operateType.value = '修改一级科目'
            modifyType.value = 2
            break;

        case 3:
            operateType.value = '修改二级科目'
            modifyType.value = 3
            break;
    }
}

function updateData () {
    if (modifyType.value == 1) {
        axios.post($api_baseUrl + `/accountsmanagement/firstgrade/updateaccountname`, {
            accountId: itemValue.value,
            accountNameOld: selectOption1.value[itemValue.value].firstGradeAccountName,
            accountNameNew: first_grade_account_name.value
        }).then(res => {
            ElMessage.success('添加成功')
            dialogVisible1.value = false
            getItemType()
        }).catch((error) => {
            ElMessage.error('添加失败,失败原因：' + error.response.data.msg)
        })
    } else if (modifyType.value == 2) {
        axios.post($api_baseUrl + `/accountsmanagement/secondgrade/updateaccountname`, {
            accountId: projectItem1.value,
            accountNameOld: selectOption2.value.find((item) => item.secondGradeAccountId == projectItem1.value).secondGradeAccountName,
            accountNameNew: second_grade_account_name.value
        }).then(res => {
            ElMessage.success('添加成功')
            dialogVisible1.value = false
            getItemType()
        }).catch((error) => {
            ElMessage.error('添加失败,失败原因：' + error.response.data.msg)
        })
    } else {
        axios.post($api_baseUrl + `/accountsmanagement/thirdgrade/updateaccountname`, {
            accountId: projectItem2.value,
            accountNameOld: selectOption3.value.find((item) => item.thirdGradeAccountId == projectItem2.value).thirdGradeAccountName,
            accountNameNew: third_grade_account_name.value
        }).then(res => {
            ElMessage.success('添加成功')
            dialogVisible1.value = false
            getItemType()
        }).catch((error) => {
            ElMessage.error('添加失败,失败原因：' + error.response.data.msg)
        })
    }
}

function findNextItem(val){
    if (val == 1) {
        selectOption2.value = []
        selectOption3.value = []
        projectItem1.value = ''
        projectItem2.value = ''
    } else {
        selectOption3.value = []
        projectItem2.value = ''
    }
    if (!itemValue.value) {
        return;
    } else {
        selectOption2.value = allAccounts.value[itemValue.value].associatedSecondGradeAccounts
        if (!projectItem1.value) {
            return;
        } else {
            selectOption3.value = selectOption2.value.find((item) => item.secondGradeAccountId == projectItem1.value).associatedThirdGradeAccounts
        }
    }
}
</script>
