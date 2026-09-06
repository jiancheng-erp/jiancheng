<template>
    <el-row :gutter="20">
        <el-col class="u-page-title" :span="24" :offset="0"
            >用户管理</el-col
        >
    </el-row>
    <el-row class="u-mt-5" :gutter="20">
        <el-col class="u-nowrap" :span="4" :offset="0">
            用户名搜索：
            <el-input
                v-model="userSearch"
                placeholder="请输入用户名"
                clearable
                suffix-icon=""
            ></el-input>
        </el-col>
        <el-col class="u-nowrap" :span="4" :offset="4">
            职员姓名搜索：
            <el-input
                v-model="staffSearch"
                placeholder="请输入职员姓名"
                clearable
                suffix-icon=""
            ></el-input>
        </el-col>
        <el-col :span="4" :offset="8">
            <el-button type="primary" size="default" @click="openAddUserDialog"
                >添加新用户</el-button
            >
        </el-col>
    </el-row>
    <el-row class="u-mt-5" :gutter="20">
        <el-col :span="24" :offset="0">
            <el-table
                :data="filteredData.slice((currentPage - 1) * pageSize, currentPage * pageSize)"
                border
                style="height: 550px"
                v-loading="datafinished"
            >
                <el-table-column prop="userName" label="用户名"></el-table-column>
                <el-table-column prop="staffName" label="姓名"></el-table-column>
                <el-table-column prop="characterName" label="角色"></el-table-column>
                <el-table-column
                    prop="departmentName"
                    label="部门"
                    :filters="departmentFilter"
                    :filter-method="filterDepartment"
                    filter-placement="bottom-end"
                ></el-table-column>
                <!-- <el-table-column prop="email" label="邮箱"></el-table-column>
                <el-table-column prop="phone" label="电话"></el-table-column> -->
                <el-table-column prop="operation" label="操作">
                    <template #default="scope">
                        <el-button type="primary" size="mini" @click="openEditUserDialog(scope.row)"
                            >编辑用户</el-button
                        >
                        <el-button type="primary" size="mini" @click="handleReset(scope.row)"
                            >重置密码</el-button
                        >
                        <el-button
                            :disabled="disableDeleteButton(scope.row)"
                            type="danger"
                            size="mini"
                            @click="handleDelete(scope.row)"
                            >删除</el-button
                        >
                    </template>
                </el-table-column>
            </el-table>
            <el-pagination
                @current-change="handlePageChange"
                :current-page="currentPage"
                :page-size="pageSize"
                :total="filteredData.length"
                layout="prev, pager, next"
                style="margin-top: 20px; text-align: center"
            ></el-pagination>
        </el-col>
    </el-row>
    <el-dialog title="添加用户" v-model="addUserDialogVisible" width="30%">
        <el-form>
            <el-form-item label="用户名: ">
                <el-input v-model="addUserData.userName"></el-input>
            </el-form-item>
            <el-form-item label="姓名: ">
                <el-input v-model="addUserData.staffName"></el-input>
            </el-form-item>
            <el-form-item label="角色: ">
                <el-select v-model="addUserData.characterId" placeholder="请选择角色">
                    <el-option
                        v-for="item in characterData"
                        :key="item.value"
                        :label="item.label"
                        :value="item.value"
                    >
                    </el-option>
                </el-select>
            </el-form-item>
            <el-form-item label="部门: ">
                <el-select v-model="addUserData.departmentId" placeholder="请选择部门">
                    <el-option
                        v-for="item in departmentData"
                        :key="item.value"
                        :label="item.label"
                        :value="item.value"
                    >
                    </el-option>
                </el-select>
            </el-form-item>
        </el-form>
        <template #footer>
            <span>
                <el-button @click="addUserDialogVisible = false">取消</el-button>
                <el-button type="primary" @click="createUser">确认</el-button>
            </span>
        </template>
    </el-dialog>
    <el-dialog v-model="editUserDialogVisible" title="编辑用户" width="30%">
        <el-form>
            <el-form-item label="旧用户名: ">
                <el-input v-model="editUserData.oldUserName" disabled></el-input>
            </el-form-item>
            <el-form-item label="用户名: ">
                <el-input v-model="editUserData.userName"></el-input>
            </el-form-item>
            <el-form-item label="姓名: ">
                <el-input v-model="editUserData.staffName" disabled></el-input>
            </el-form-item>
            <el-form-item label="角色: ">
                <el-select v-model="editUserData.characterId" placeholder="请选择角色">
                    <el-option
                        v-for="item in characterData"
                        :key="item.value"
                        :label="item.label"
                        :value="item.value"
                    >
                    </el-option>
                </el-select>
            </el-form-item>
            <el-form-item label="部门: ">
                <el-select v-model="editUserData.departmentId" placeholder="请选择部门">
                    <el-option
                        v-for="item in departmentData"
                        :key="item.value"
                        :label="item.label"
                        :value="item.value"
                    >
                    </el-option>
                </el-select>
            </el-form-item>
        </el-form>
        <template #footer>
            <span>
                <el-button @click="editUserDialogVisible = false">取消</el-button>
                <el-button type="primary" @click="editUser">确认</el-button>
            </span>
        </template>
    </el-dialog>
</template>

<script>
import axios from 'axios'
import { ElMessageBox } from 'element-plus'

export default {
    data() {
        return {
            editUserDialogVisible: false,
            addUserDialogVisible: false,
            datafinished: true,
            userData: [],
            editUserData: {
                userId: 0,
                oldUserName: '',
                userName: '',
                staffName: '',
                characterId: '',
                departmentId: ''
            },
            addUserData: {
                userName: '',
                staffName: '',
                characterId: '',
                departmentId: ''
            },
            characterData: [],
            departmentData: [],
            staffData: [],
            searchValue: '',
            departmentFilter: [],
            userSearch: '', // Username search input
            staffSearch: '', // Staff name search input
            currentPage: 1, // Current pagination page
            pageSize: 10 // Number of rows per page
        }
    },
    computed: {
        // Filtered data based on search inputs
        filteredData() {
            return this.userData.filter((row) => {
                const userMatch = row.userName.toLowerCase().includes(this.userSearch.toLowerCase())
                const staffMatch = row.staffName
                    .toLowerCase()
                    .includes(this.staffSearch.toLowerCase())
                return userMatch && staffMatch
            })
        }
    },
    methods: {
        handlePageChange(page) {
            this.currentPage = page
        },
        editUser() {
            this.$confirm('确认修改用户信息吗?', '提示', {
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                type: 'warning'
            })
                .then(async () => {
                    this.datafinished = true
                    await axios
                        .post(`${this.$apiBaseUrl}/usermanage/edituser`, this.editUserData)
                        .then((response) => {
                            console.log(response)
                            this.editUserDialogVisible = false
                            this.getUserData()
                        })
                        .catch((error) => {
                            console.log('Edit user failed!')
                        })
                })
                .then(() => {
                    this.$message({
                        type: 'success',
                        message: '修改用户信息成功'
                    })
                })
                .catch(() => {
                    this.$message({
                        type: 'info',
                        message: '已取消修改用户信息'
                    })
                })
        },
        disableDeleteButton(row) {
            if (
                row.characterName === '董事长/总经理' ||
                row.characterName === '超级管理员' ||
                row.characterName === '人事部经理'
            ) {
                return true
            }
            return false
        },
        handleDelete(row) {
            console.log('Delete user:', row)
            this.$confirm('确认删除用户吗?', '提示', {
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                type: 'warning'
            })
                .then(async () => {
                    this.datafinished = true
                    await axios
                        .post(`${this.$apiBaseUrl}/user/deleteuser`, { userId: row.userId })
                        .then((response) => {
                            console.log(response)
                            this.getUserData()
                        })
                        .then(() => {
                            this.$message({
                                type: 'success',
                                message: '删除用户成功'
                            })
                        })
                        .catch((error) => {
                            console.log('Delete user failed!')
                        })
                })
                .catch(() => {
                    this.$message({
                        type: 'info',
                        message: '已取消删除用户'
                    })
                })
        },
        handleReset(row) {
            console.log('Reset password:', row)
            this.$confirm('确认重置密码吗?', '提示', {
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                type: 'warning'
            })
                .then(async () => {
                    this.datafinished = true
                    await axios
                        .post(`${this.$apiBaseUrl}/usermanage/resetpassword`, {
                            userId: row.userId
                        })
                        .then((response) => {
                            console.log(response)
                            this.getUserData()
                        })
                        .then(() => {
                            this.$message({
                                type: 'success',
                                message: '重置密码成功'
                            })
                        })
                        .catch((error) => {
                            console.log('Reset password failed!')
                        })
                })
                .catch(() => {
                    this.$message({
                        type: 'info',
                        message: '已取消重置密码'
                    })
                })
        },
        filterDepartment(value, row) {
            return row.departmentName === value
        },
        openAddUserDialog() {
            this.addUserDialogVisible = true
        },
        openEditUserDialog(row) {
            console.log(row)
            this.editUserData.userId = row.userId
            this.editUserData.departmentId = this.departmentData.find(
                (item) => item.label === row.departmentName
            ).value
            this.editUserData.characterId = this.characterData.find(
                (item) => item.label === row.characterName
            ).value
            this.editUserData.staffName = row.staffName
            this.editUserData.userName = row.userName
            this.editUserData.oldUserName = row.userName
            this.editUserDialogVisible = true
        },
        async getUserData() {
            const response = await axios.get(`${this.$apiBaseUrl}/usermanage/getallusers`)
            this.userData = response.data
            this.datafinished = false
        },
        async getCharacterData() {
            const response = await axios.get(`${this.$apiBaseUrl}/general/getallcharacters`)
            console.log(response)
            this.characterData = response.data
        },
        async getDepartmentData() {
            const response = await axios.get(`${this.$apiBaseUrl}/general/getalldepartments`)
            console.log(response)
            this.departmentData = response.data
        },
        async getStaffData() {
            const response = await axios.get(`${this.$apiBaseUrl}/general/getallstaffs`)
            console.log(response)
            this.staffData = response.data
        },
        async createUser() {
            this.$confirm('确认添加用户吗?', '提示', {
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                type: 'warning'
            })
                .then(async () => {
                    this.datafinished = true
                    await axios
                        .post(`${this.$apiBaseUrl}/usermanage/createuser`, this.addUserData)
                        .then((response) => {
                            console.log(response)
                            this.addUserDialogVisible = false
                            this.getUserData()
                        })
                        .then(() => {
                            this.$message({
                                type: 'success',
                                message: '添加用户成功'
                            })
                        })
                        .catch((error) => {
                            console.log('Create user failed!')
                        })
                })
                .catch(() => {
                    this.$message({
                        type: 'info',
                        message: '已取消添加用户'
                    })
                })
        }
    },
    mounted() {
        this.getUserData()
        this.getCharacterData()
        this.getDepartmentData()
    }
}
</script>
