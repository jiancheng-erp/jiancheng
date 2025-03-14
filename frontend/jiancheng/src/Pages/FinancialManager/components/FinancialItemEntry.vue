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
                placeholder="请选择一级项目类别"
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
        <el-form-item
            label="二级科目"
            :rules="[
                { required: true, message: '二级科目不能为空' },
                { type: 'String ', message: '二级科目不能为空' }
            ]"
        >
            <el-select
                v-model="projectItem1"
                placeholder="请选择二级科目"
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
        <el-form-item
            label="三级科目"
            :rules="[
                { required: true, message: '三级科目不能为空' },
                { type: 'String ', message: '三级科目不能为空' }
            ]"
        >
            <el-select
                v-model="projectItem2"
                placeholder="请选择三级科目"
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



        <el-form-item label="项目名称">
            <el-input style="width: 300px;height: 40px;" v-model="ruleForm.recordName"></el-input>
        </el-form-item>
        <el-form-item label="供应商名称">
            <el-input style="width: 300px;height: 40px;" v-model="ruleForm.recordObjectId"></el-input>
        </el-form-item>
        <el-form-item label="资金流向">
            <el-select
                v-model="ruleForm.recordType"
                placeholder="请选择"
                size="large"
                style="width: 300px"
                clearable
                filterable
            >
                <el-option
                    v-for="item in typeOption"
                    :key="item.type"
                    :label="item.label"
                    :value="item.type"
                />
            </el-select>
        </el-form-item>
        <el-form-item label="资金数量">
            <el-input style="width: 300px;height: 40px;" v-model="ruleForm.recordAmount"></el-input>
        </el-form-item>
        <el-form-item label="创建时间">
            <el-date-picker
                v-model="ruleForm.recordCreationDate"
                type="date"
                placeholder="请选择"
                :default-value="new Date(2025, 1, 1)"
                style="width: 300px;height: 40px;"
                value-format="YYYY-MM-DD"
            />
        </el-form-item>
        <el-form-item label="处理时间">
            <el-date-picker
                v-model="ruleForm.recordProcessedDate"
                type="date"
                placeholder="请选择"
                :default-value="new Date(2025, 1, 1)"
                style="width: 300px;height: 40px;"
                value-format="YYYY-MM-DD"
            />
        </el-form-item>
        <el-form-item label="金额单位">
            <el-input style="width: 300px;height: 40px;" v-model="ruleForm.recordAmountUnitId"></el-input>
        </el-form-item>
        <el-form-item label="金额单位转换">
            <el-input style="width: 300px;height: 40px;" v-model="ruleForm.recordAmountYnitConversionId"></el-input>
        </el-form-item>
        <el-form-item label="处理状态">
            <el-input style="width: 300px;height: 40px;" v-model="ruleForm.recordIsProcessed"></el-input>
        </el-form-item>
        <el-form-item>
            <el-button type="primary" @click="addRuleForm" style="margin-left: 80px"
                >添加</el-button
            >
        </el-form-item>
    </el-form>
</template>

<script lang="js" setup>
import { ref, onMounted, getCurrentInstance } from 'vue'
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'

let selectOption1 = ref([])
let selectOption2 = ref([])
let selectOption3 = ref([])
const $api_baseUrl = getCurrentInstance().appContext.config.globalProperties.$apiBaseUrl
let allAccounts = ref([])
const ruleForm = ref({
    itemValue: '',
    projectItem1: '',
    projectItem2: '',
    dateValue: '',
    money: '',
    operName: window.localStorage.getItem('userName')
})
const itemValue = ref('');
const projectItem1 = ref('');
const projectItem2 = ref('');

onMounted(() => {
    getItemType()
})

async function getItemType(url) {
    const res = await axios.get($api_baseUrl + `/accountsmanagement/getallaccounts`)
    allAccounts.value = res.data.firstGradeAccountsMapping
    selectOption1.value = res.data.firstGradeAccountsMapping
}
function addRuleForm() {
    console.log(ruleForm.value)
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
    if (itemValue.value == '') {
        return;
    } else {
        selectOption2.value = allAccounts.value[itemValue.value].associatedSecondGradeAccounts
        if (projectItem1.value == '') {
            return;
        } else {
            selectOption3.value = selectOption2.value.find((item) => item.secondGradeAccountId == projectItem1.value).associatedThirdGradeAccounts
        }
    }
}
</script>


<!-- 
<script lang="js" setup>
import { ref, onMounted, getCurrentInstance } from 'vue'
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'

let selectOption1 = ref([])
let selectOption2 = ref([])
let selectOption3 = ref([])
const $api_baseUrl = getCurrentInstance().appContext.config.globalProperties.$apiBaseUrl
let allAccounts = ref([])
let typeOption = ref([
    { type: 0, label: '付款'},
    { type: 1, label: '收款'}
])
const ruleForm = ref({
    // itemValue: '',
    // projectItem1: '',
    // projectItem2: '',
    // dateValue: '',
    // money: '',
    operName: window.localStorage.getItem('userName'),
    accountId: '',
    recordName: '',
    recordObjectId: '',
    recordType: '',
    recordCreationDate: '',
    recordProcessedDate: '',
    recordAmountUnitId: '',
    recordAmountYnitConversionId: '',
    recordIsProcessed: ''
})
const itemValue = ref('');
const projectItem1 = ref('');
const projectItem2 = ref('');

onMounted(() => {
    getItemType()
})

async function getItemType(url) {
    const res = await axios.get($api_baseUrl + `/accountsmanagement/getallaccounts`)
    allAccounts.value = res.data.firstGradeAccountsMapping
    selectOption1.value = res.data.firstGradeAccountsMapping
}
async function addRuleForm() {
    const res = await axios.post($api_baseUrl + `/accountsmanagement/thirdgrade/addrecord`, ruleForm.value)
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
    if (itemValue.value == '') {
        return;
    } else {
        selectOption2.value = allAccounts.value[itemValue.value].associatedSecondGradeAccounts
        if (projectItem1.value == '') {
            return;
        } else {
            selectOption3.value = selectOption2.value.find((item) => item.secondGradeAccountId == projectItem1.value).associatedThirdGradeAccounts
        }
    }
}
</script> -->
