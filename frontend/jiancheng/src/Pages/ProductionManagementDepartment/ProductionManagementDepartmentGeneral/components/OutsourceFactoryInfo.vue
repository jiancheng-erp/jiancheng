<template>
    <el-row class="u-mt-5" :gutter="20">
        <el-col class="u-nowrap" :span="4" :offset="0">
            <el-input v-model="nameSearch" placeholder="搜索厂家" clearable
                @keypress.enter="getOutsourceFactoryData()" @clear="getOutsourceFactoryData" />
        </el-col>
    </el-row>
    <el-row class="u-mt-5" :gutter="20">
        <el-button @click="openNewOutsourceFactoryDialog">
            添加厂家
        </el-button>
        <el-button v-if="!isEditing" type="primary" @click="editOutsourceFactory()">编辑</el-button>
        <el-button v-if="isEditing" type="primary" @click="saveOutsourceFactory()">保存</el-button>
        <el-button v-if="isEditing" type="primary" @click="isEditing = false">退出编辑</el-button>
    </el-row>
    <el-row class="u-mt-5" :gutter="20">
        <el-table :data="outsourceFactoryData" border>
            <el-table-column prop="value" label="厂家名称">
                <template #default="scope">
                    <p v-if="!isEditing">{{ scope.row.value }}</p>
                    <el-input v-else v-model="scope.row.value"></el-input>
                </template>
            </el-table-column>
            <el-table-column label="操作">
                <template #default="scope">
                    <el-button-group>
                        <el-button type="danger" @click="deleteOutsourceFactory(scope.row)">删除</el-button>
                    </el-button-group>
                </template>
            </el-table-column>
        </el-table>
    </el-row>
    <el-dialog v-model="isNewOutsourceFactoryDialogOpen" title="新厂家" width="50%">
        <el-form :model="newOutsourceFactoryForm">
            <el-form-item prop="name" label="厂家名字">
                <el-input v-model="newOutsourceFactoryForm.name"></el-input>
            </el-form-item>
        </el-form>
        <el-button @click="addNewOutsourceFactory">确认</el-button>
    </el-dialog>
</template>
<script>
import axios from 'axios'
import { ElMessage } from 'element-plus';
export default {
    props: ["teams"],
    data() {
        return {
            outsourceFactorySearch: '',
            outsourceFactoryData: [],
            isNewOutsourceFactoryDialogOpen: false,
            newOutsourceFactoryForm: {
                name: "",
            },
            isEditing: false,
            nameSearch: '',
        }
    },
    mounted() {
        this.getOutsourceFactoryData()
    },
    methods: {
        openNewOutsourceFactoryDialog() {
            this.isNewOutsourceFactoryDialogOpen = true
        },
        async addNewOutsourceFactory() {
            try {
                const response = await axios.post(`${this.$apiBaseUrl}/general/addnewoutsourcefactory`, this.newOutsourceFactoryForm)
                ElMessage.success(response.data.message)
            }
            catch (error) {
                ElMessage.error(error.response.data.message)
            }
            this.newOutsourceFactoryForm = {
                name: "",
            }
            this.isNewOutsourceFactoryDialogOpen = false
            this.getOutsourceFactoryData()
        },
        async getOutsourceFactoryData() {
            let params = {"nameSearch": this.nameSearch}
            let response = await axios.get(`${this.$apiBaseUrl}/general/getalloutsourcefactories`, {params})
            this.outsourceFactoryData = response.data
        },
        async editOutsourceFactory() {
            this.isEditing = true
        },
        async saveOutsourceFactory() {
            try {
                const response = await axios.put(`${this.$apiBaseUrl}/general/editoutsourcefactory`, this.outsourceFactoryData)
                ElMessage.success(response.data.message)
                this.isEditing = false
                this.getOutsourceFactoryData()
            }
            catch (error) {
                ElMessage.error(error.response.data.message)
            }
        },
        async deleteOutsourceFactory(row) {
            try {
                let params = { "factoryId": row.id }
                const response = await axios.delete(`${this.$apiBaseUrl}/general/deleteoutsourcefactory`, {params})
                ElMessage.success(response.data.message)
                this.getOutsourceFactoryData()
            }
            catch (error) {
                console.log(error)
                ElMessage.error(error.response)
            }
        }
    }
}
</script>