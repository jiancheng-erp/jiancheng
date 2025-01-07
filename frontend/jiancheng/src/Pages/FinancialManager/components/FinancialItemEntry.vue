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
                v-model="ruleForm.itemValue"
                placeholder="请选择项目类别"
                size="large"
                style="width: 300px"
                clearable
                filterable
            >
                <el-option
                    v-for="item in selectOption1"
                    :key="item.value"
                    :label="item.label"
                    :value="item.value"
                />
            </el-select>
            <span
                style="margin-left: 20px; color: dodgerblue; cursor: pointer"
                @click="ItemVisible = true"
                >没有？点我添加</span
            >
            <span
                style="margin-left: 20px; color: red; cursor: pointer"
                @click="deleteItem"
                >删除</span
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
                v-model="ruleForm.projectItem1"
                placeholder="请选择一级科目"
                size="large"
                style="width: 300px"
                clearable
                filterable
            >
                <el-option
                    v-for="item in selectOption2"
                    :key="item.value"
                    :label="item.label"
                    :value="item.value"
                />
            </el-select>
            <span style="margin-left: 20px; color: dodgerblue; cursor: pointer" @click="addProject"
                >没有？点我添加</span
            >
            <span
                style="margin-left: 20px; color: red; cursor: pointer"
                @click="deleteItem"
                >删除</span
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
                v-model="ruleForm.projectItem2"
                placeholder="请选择二级科目"
                size="large"
                style="width: 300px"
                clearable
                filterable
            >
                <el-option
                    v-for="item in selectOption3"
                    :key="item.value"
                    :label="item.label"
                    :value="item.value"
                />
            </el-select>
            <span style="margin-left: 20px; color: dodgerblue; cursor: pointer" @click="addProject"
                >没有？点我添加</span
            >
            <span
                style="margin-left: 20px; color: red; cursor: pointer"
                @click="deleteItem"
                >删除</span
            >
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
            <el-input style="width: 300px;height: 40px;" v-model="ruleForm.money" disabled></el-input>
        </el-form-item>
        <el-form-item>
            <el-button type="primary" @click="addRuleForm" style="margin-left: 80px"
                >添加</el-button
            >
        </el-form-item>
    </el-form>
    <el-dialog title="添加项目类别" v-model="ItemVisible" width="50%">
        <el-form label-width="100px" style="max-width: 460px">
            <el-form-item label="项目类别名称">
                <el-input :rows="2" v-model="ruleForm.itemValue" />
            </el-form-item>
            <el-form-item>
                <el-button type="danger" @click="ItemVisible = false">取消</el-button>
                <el-button type="primary" @click="addRuleForm">确定</el-button>
            </el-form-item>
        </el-form>
    </el-dialog>
    <el-dialog title="添加一级科目" v-model="projectVisible" width="50%">
        <el-form label-width="100px" style="max-width: 460px">
            <el-form-item label="一级科目名称">
                <el-input :rows="2" v-model="ruleForm.projectItem1" />
            </el-form-item>
            <el-form-item>
                <el-button type="danger" @click="projectVisible = false">取消</el-button>
                <el-button type="primary" @click="addRuleForm">确定</el-button>
            </el-form-item>
        </el-form>
    </el-dialog>
    <el-dialog title="添加二级科目" v-model="projectVisible2" width="50%">
        <el-form label-width="100px" style="max-width: 460px">
            <el-form-item label="二级科目名称">
                <el-input :rows="2" v-model="ruleForm.projectItem2" />
            </el-form-item>
            <el-form-item>
                <el-button type="danger" @click="projectVisible2 = false">取消</el-button>
                <el-button type="primary" @click="addRuleForm">确定</el-button>
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
const itemUrl = `${$api_baseUrl}` + ''
let ItemVisible = ref(false)
let projectVisible = ref(false)
let projectVisible2 = ref(false)
const ruleForm = ref({
    itemValue: '',
    projectItem1: '',
    projectItem2: '',
    dateValue: '',
    money: '',
    operName:''
})

onMounted(() => {
    getItemType()
})

async function getItemType(url) {
    // selectOption1.value = await axios.get(itemUrl, {})
    // selectOption2.value = await axios.get(itemUrl, {})
}
function addRuleForm() {
    projectVisible.value = false
    ItemVisible.value = false
    getItemType()
}
function addProject() {
    if (ruleForm.value.itemValue == '') {
        ElMessage.warning('请先选择项目类别')
        return
    } else {
        projectVisible.value = true
    }
    if (ruleForm.value.projectItem1 == '') {
        ElMessage.warning('请先选择一级科目')
        return
    } else {
        projectVisible2.value = true
    }
}

function deleteItem(){}
</script>
