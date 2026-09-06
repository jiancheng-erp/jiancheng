<template>
    <el-row :gutter="20">
        <el-col class="u-page-title" :span="24" :offset="0">部门管理</el-col>
    </el-row>
    <el-row class="u-mt-5" :gutter="20">
        <el-col class="u-nowrap" :span="6" :offset="0">
            部门名称搜索：
            <el-input v-model="departmentSearch" placeholder="请输入部门名称" clearable></el-input>
        </el-col>
        <el-col :span="4" :offset="14">
            <el-button type="primary" size="default" @click="openAddDepartmentDialog">添加新部门</el-button>
        </el-col>
    </el-row>
    <el-row class="u-mt-5" :gutter="20">
        <el-col :span="24" :offset="0">
            <el-table
                :data="filteredData.slice((currentPage - 1) * pageSize, currentPage * pageSize)"
                style="width: 100%"
                height="calc(100vh - var(--main-table-offset))"
                border
            >
                <el-table-column prop="value" label="部门ID" width="120"></el-table-column>
                <el-table-column prop="label" label="部门名称"></el-table-column>
                <el-table-column label="操作" width="220">
                    <template #default="{ row }">
                        <el-button type="primary" @click="openEditDepartmentDialog(row)">编辑</el-button>
                        <el-button type="danger" @click="deleteDepartment(row)">删除</el-button>
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
    <el-dialog title="添加新部门" v-model="addDepartmentDialogVisible" width="30%">
        <el-form :model="addDepartmentForm" label-width="80px">
            <el-form-item label="部门名称" prop="departmentName">
                <el-input v-model="addDepartmentForm.departmentName" placeholder="请输入部门名称"></el-input>
            </el-form-item>
        </el-form>
        <template #footer>
            <span>
                <el-button @click="addDepartmentDialogVisible = false">取消</el-button>
                <el-button type="primary" @click="addDepartment">确定</el-button>
            </span>
        </template>
    </el-dialog>
    <el-dialog title="编辑部门" v-model="editDepartmentDialogVisible" width="30%">
        <el-form :model="editDepartmentForm" label-width="80px">
            <el-form-item label="部门名称" prop="departmentName">
                <el-input v-model="editDepartmentForm.departmentName" placeholder="请输入部门名称"></el-input>
            </el-form-item>
        </el-form>
        <template #footer>
            <span>
                <el-button @click="editDepartmentDialogVisible = false">取消</el-button>
                <el-button type="primary" @click="updateDepartment">确定</el-button>
            </span>
        </template>
    </el-dialog>
</template>

<script>
import axios from 'axios'

export default {
    data() {
        return {
            departmentSearch: '',
            departmentList: [],
            addDepartmentDialogVisible: false,
            editDepartmentDialogVisible: false,
            addDepartmentForm: {
                departmentName: ''
            },
            editDepartmentForm: {
                departmentId: '',
                departmentName: ''
            },
            currentPage: 1,
            pageSize: 10
        }
    },
    computed: {
        filteredData() {
            return this.departmentList.filter((item) =>
                (item.label || '').toLowerCase().includes(this.departmentSearch.toLowerCase())
            )
        }
    },
    mounted() {
        this.getDepartmentData()
    },
    methods: {
        handlePageChange(page) {
            this.currentPage = page
        },
        async getDepartmentData() {
            const response = await axios.get(`${this.$apiBaseUrl}/general/getalldepartments`)
            this.departmentList = response.data
        },
        openAddDepartmentDialog() {
            this.addDepartmentForm.departmentName = ''
            this.addDepartmentDialogVisible = true
        },
        async addDepartment() {
            if (!this.addDepartmentForm.departmentName.trim()) {
                this.$message.error('部门名称不能为空')
                return
            }
            try {
                await axios.post(`${this.$apiBaseUrl}/general/createdepartment`, {
                    departmentName: this.addDepartmentForm.departmentName
                })
                this.$message.success('添加成功')
                this.addDepartmentDialogVisible = false
                this.getDepartmentData()
            } catch (error) {
                this.$message.error(error?.response?.data?.error || '添加失败')
            }
        },
        openEditDepartmentDialog(row) {
            this.editDepartmentForm = {
                departmentId: row.value,
                departmentName: row.label
            }
            this.editDepartmentDialogVisible = true
        },
        async updateDepartment() {
            if (!this.editDepartmentForm.departmentName.trim()) {
                this.$message.error('部门名称不能为空')
                return
            }
            try {
                await axios.post(`${this.$apiBaseUrl}/general/updatedepartment`, {
                    departmentId: this.editDepartmentForm.departmentId,
                    departmentName: this.editDepartmentForm.departmentName
                })
                this.$message.success('修改成功')
                this.editDepartmentDialogVisible = false
                this.getDepartmentData()
            } catch (error) {
                this.$message.error(error?.response?.data?.error || '修改失败')
            }
        },
        deleteDepartment(row) {
            this.$confirm('确定删除该部门？', '提示', {
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                type: 'warning'
            })
                .then(async () => {
                    try {
                        await axios.post(`${this.$apiBaseUrl}/general/deletedepartment`, {
                            departmentId: row.value
                        })
                        this.$message.success('删除成功')
                        this.getDepartmentData()
                    } catch (error) {
                        this.$message.error(error?.response?.data?.error || '删除失败')
                    }
                })
                .catch(() => {
                    this.$message.info('已取消删除')
                })
        }
    }
}
</script>
