<template>
    <el-row :gutter="20" style="margin-top: 20px">
        <el-col :span="4" :offset="0" style="white-space: nowrap;">
            <el-input v-model="procedureSearch" placeholder="搜索工序" clearable @keypress.enter="getProcedureData()"
                @clear="getProcedureData" />
        </el-col>
        <el-col :span="4" :offset="0" style="white-space: nowrap;">
            <el-select v-model="teamNameSearch" placeholder="选择工组" @change="getProcedureData()" filterable clearable>
                <el-option v-for="item in teams" :key="item" :label="item" :value="item"></el-option>
            </el-select>
        </el-col>
    </el-row>
    <el-row :gutter="20" style="margin-top: 20px">
        <el-button @click="openNewProcedureDialog">
            添加工序
        </el-button>
        <el-button v-if="!isEditing" type="primary" @click="editProcedure()">编辑</el-button>
        <el-button v-if="isEditing" type="primary" @click="saveProcedure()">保存</el-button>
        <el-button v-if="isEditing" type="primary" @click="isEditing = false">退出编辑</el-button>
    </el-row>
    <el-row :gutter="20" style="margin-top: 20px">
        <el-table :data="procedureData" border>
            <el-table-column prop="procedureName" label="工序">
                <template #default="scope">
                    <p v-if="!isEditing">{{ scope.row.procedureName }}</p>
                    <el-input v-else v-model="scope.row.procedureName"></el-input>
                </template>
            </el-table-column>
            <el-table-column prop="team" label="工组">
                <template #default="scope">
                    <p v-if="!isEditing">{{ scope.row.team }}</p>
                    <el-input v-else v-model="scope.row.team"></el-input>
                </template>
            </el-table-column>
            <el-table-column prop="price" label="工价">
                <template #default="scope">
                    <p v-if="!isEditing">{{ scope.row.price }}</p>
                    <el-input v-else v-model="scope.row.price"></el-input>
                </template>
            </el-table-column>
            <el-table-column label="操作">
                <template #default="scope">
                    <el-button-group>
                        <el-button type="danger" @click="deleteProcedure(scope.row)">删除</el-button>
                    </el-button-group>
                </template>
            </el-table-column>
        </el-table>
    </el-row>
    <el-dialog v-model="isNewProcedureDialogOpen" title="新工序" width="50%">
        <el-form :model="newProcedureForm">
            <el-form-item prop="name" label="工序名字">
                <el-input v-model="newProcedureForm.name"></el-input>
            </el-form-item>
            <el-form-item prop="team" label="工组">
                <el-select v-model="newProcedureForm.team">
                    <el-option v-for="item in teams" :key="item" :label="item" :value="item"></el-option>
                </el-select>
            </el-form-item>
            <el-form-item prop="price" label="工价">
                <el-input v-model="newProcedureForm.price"></el-input>
            </el-form-item>
        </el-form>
        <el-button @click="addNewProcedure">确认</el-button>
    </el-dialog>
</template>
<script>
import axios from 'axios'
import { ElMessage } from 'element-plus';
export default {
    props: ["teams"],
    data() {
        return {
            procedureSearch: '',
            teamNameSearch: '',
            procedureData: [],
            isNewProcedureDialogOpen: false,
            newProcedureForm: {
                name: "",
                team: this.$props.teams[0],
                price: "",
            },
            isEditing: false
        }
    },
    mounted() {
        this.getProcedureData()
    },
    methods: {
        openNewProcedureDialog() {
            this.isNewProcedureDialogOpen = true
        },
        async addNewProcedure() {
            try {
                await axios.post(`${this.$apiBaseUrl}/production/addnewprocedure`, this.newProcedureForm)
                ElMessage.success("添加成功")
            }
            catch (error) {
                ElMessage.error(error)
            }
            this.newProcedureForm = {
                name: "",
                team: this.$props.teams[0],
                price: "",
            }
            this.isNewProcedureDialogOpen = false
            this.getProcedureData()
        },
        async getProcedureData() {
            let params = { 
                "teams": this.$props.teams.toString(), 
                "procedureName": this.procedureSearch,
                "teamName": this.teamNameSearch
             }
            let response = await axios.get(`${this.$apiBaseUrl}/production/getallprocedures`, { params })
            this.procedureData = response.data
        },
        async editProcedure() {
            this.isEditing = true
        },
        async saveProcedure() {
            try {
                await axios.put(`${this.$apiBaseUrl}/production/editprocedure`, this.procedureData)
                ElMessage.success("编辑成功")
                this.isEditing = false
                this.getProcedureData()
            }
            catch (error) {
                ElMessage.error(error)
            }
        },
        async deleteProcedure(row) {
            try {
                let params = { "procedureId": row.procedureId }
                await axios.delete(`${this.$apiBaseUrl}/production/deleteprocedure`, { params })
                ElMessage.success("删除成功")
                this.getProcedureData()
            }
            catch (error) {
                ElMessage.error(error)
            }
        }
    }
}
</script>