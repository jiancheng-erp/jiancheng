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
        </el-form-item>
        <el-form-item label="所属月份">
            <el-date-picker
                v-model="ruleForm.dateValue"
                type="month"
                placeholder="所属月份"
                :default-value="new Date(2025, 1, 1)"
                style="width: 300px;height: 40px;"
            />
        </el-form-item>
        <el-form-item label="价格">
            <el-input style="width: 300px;height: 40px;" v-model="ruleForm.money"></el-input>
        </el-form-item>
        <el-form-item label="操作人">
            <el-input style="width: 300px;height: 40px;" v-model="ruleForm.operName" disabled></el-input>
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
