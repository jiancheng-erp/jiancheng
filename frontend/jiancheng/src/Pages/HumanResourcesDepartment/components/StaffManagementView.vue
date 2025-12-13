<template>
    <el-row :gutter="20">
        <el-col :span="24" :offset="0" style="font-size: xx-large; text-align: center"
            >人员管理</el-col
        >
    </el-row>
    <el-row :gutter="20" style="margin-top: 20px">
        <el-col :span="4" :offset="0" style="white-space: nowrap">
            职员姓名搜索：
            <el-input
                v-model="staffSearch"
                placeholder="请输入职员姓名"
                clearable
                suffix-icon=""
            ></el-input>
        </el-col>
        <el-col :span="4" :offset="2" style="white-space: nowrap">
            职员职位筛选：
            <el-select v-model="characterIdFilter" placeholder="请选择职位" clearable>
                <el-option
                    v-for="item in characterData"
                    :key="item.value"
                    :label="item.label"
                    :value="item.value"
                ></el-option>
            </el-select>
        </el-col>
        <el-col :span="4" :offset="2" style="white-space: nowrap">
            职员部门筛选：
            <el-select v-model="departmentIdFilter" placeholder="请选择部门" clearable>
                <el-option
                    v-for="item in departmentData"
                    :key="item.value"
                    :label="item.label"
                    :value="item.value"
                ></el-option>
            </el-select>
        </el-col>
        <el-col :span="4" :offset="2" style="white-space: nowrap">
            职员状态筛选：
            <el-select v-model="statusFilter" placeholder="请选择部门" clearable>
                <el-option
                    v-for="item in statusData"
                    :key="item.value"
                    :label="item.label"
                    :value="item.value"
                ></el-option>
            </el-select>
        </el-col>
        <el-col :span="4" :offset="0">
            <el-button type="primary" size="default" @click="openAddStaffDialog"
                >添加新员工</el-button
            >
        </el-col>
    </el-row>
    <el-row :gutter="20" style="margin-top: 20px">
        <el-col :span="24" :offset="0">
            <el-table
                :data="filteredData.slice((currentPage - 1) * pageSize, currentPage * pageSize)"
                style="width: 100%"
                height="550"
                border
            >
                <el-table-column prop="staffName" label="职员姓名"></el-table-column>
                <el-table-column prop="characterName" label="职位"></el-table-column>
                <el-table-column prop="departmentName" label="部门"></el-table-column>
                <el-table-column prop="staffStatus" label="职员状态"></el-table-column>
                <el-table-column prop="wechatId" label="微信ID"></el-table-column>
                <el-table-column label="操作">
                    <template #default="{ row }">
                        <el-button type="danger" @click="resignStaff(row)">离职</el-button>
                        <el-button type="primary" @click="previewStaff(row)">查看职员信息</el-button>
                        <el-button type="warning" @click="openEditWechat(row)">修改微信ID</el-button>
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
    <el-dialog title="添加新员工" v-model="addStaffDialogVisible" width="30%">
        <el-form :model="addStaffForm" label-width="80px">
            <el-form-item label="职员姓名" prop="staffName">
                <el-input v-model="addStaffForm.staffName" placeholder="请输入职员姓名"></el-input>
            </el-form-item>
            <el-form-item label="职位" prop="characterId">
                <el-select v-model="addStaffForm.characterId" placeholder="请选择职位" clearable>
                    <el-option
                        v-for="item in characterData"
                        :key="item.value"
                        :label="item.label"
                        :value="item.value"
                    ></el-option>
                </el-select>
            </el-form-item>
            <el-form-item label="部门" prop="departmentId">
                <el-select v-model="addStaffForm.departmentId" placeholder="请选择部门" clearable>
                    <el-option
                        v-for="item in departmentData"
                        :key="item.value"
                        :label="item.label"
                        :value="item.value"
                    ></el-option>
                </el-select>
            </el-form-item>
        </el-form>
        <span slot="footer" class="dialog-footer">
            <el-button @click="addStaffDialogVisible = false">取消</el-button>
            <el-button type="primary" @click="addStaff">确定</el-button>
        </span>
    </el-dialog>
    <el-dialog v-model="previewStaffDialogVisible" title="职员信息" width="40%">
        <el-descriptions title="职员信息" column="2" border>
            <el-descriptions-item label="职员姓名">{{ previewStaffForm.staffName }}</el-descriptions-item>
            <el-descriptions-item label="职位">{{ previewStaffForm.characterName }}</el-descriptions-item>
            <el-descriptions-item label="部门">{{ previewStaffForm.departmentName }}</el-descriptions-item>
            <el-descriptions-item label="职员状态">{{ previewStaffForm.staffStatus }}</el-descriptions-item>
            <el-descriptions-item label="出生日期">{{ previewStaffForm.birthDate }}</el-descriptions-item>
            <el-descriptions-item label="手机号码">{{ previewStaffForm.phoneNumber }}</el-descriptions-item>
            <el-descriptions-item label="身份证号">{{ previewStaffForm.IdNumber }}</el-descriptions-item>
            <el-descriptions-item label="微信ID">{{ previewStaffForm.wechatId }}</el-descriptions-item>
        </el-descriptions>
        <span slot="footer" class="dialog-footer">
            <el-button type="primary" @click="previewStaffDialogVisible = false">确定</el-button>
        </span>
    </el-dialog>
    <el-dialog v-model="editWechatDialogVisible" title="修改微信ID" width="30%">
        <el-form :model="editWechatForm" label-width="90px">
            <el-form-item label="职员姓名">
                <el-input v-model="editWechatForm.staffName" disabled></el-input>
            </el-form-item>
            <el-form-item label="微信ID">
                <el-input v-model="editWechatForm.wechatId" placeholder="请输入微信ID"></el-input>
            </el-form-item>
        </el-form>
        <span slot="footer" class="dialog-footer">
            <el-button @click="editWechatDialogVisible = false">取消</el-button>
            <el-button type="primary" @click="updateWechatId">保存</el-button>
        </span>
    </el-dialog>
</template>

<script>
import axios from 'axios'

export default {
    data() {
        return {
            staffSearch: '',
            characterIdFilter: '',
            departmentIdFilter: '',
            statusFilter: '',
            staffList: [],
            addStaffDialogVisible: false,
            previewStaffDialogVisible: false,
            editWechatDialogVisible: false,
            addStaffForm: {
                staffName: '',
                characterId: '',
                departmentId: ''
            },
            previewStaffForm: {
                staffName: '',
                characterName: '',
                departmentName: '',
                staffStatus: '',
                IdNumber: '',
                phoneNumber: '',
                birthDate: '',
                wechatId: '',
            },
            editWechatForm: {
                staffId: '',
                staffName: '',
                wechatId: ''
            },
            characterData: [],
            departmentData: [],
            statusData:[
                {
                    value: '在职',
                    label: '在职'
                },
                {
                    value: '离职',
                    label: '离职'
                }
            ],
            currentPage: 1, // Current pagination page
            pageSize: 10 // Number of rows per page
        }
    },
    computed: {
        // Filtered data based on search inputs
        filteredData() {
        return this.staffList.filter((item) => {
            const staffNameMatch = item.staffName
                .toLowerCase()
                .includes(this.staffSearch.toLowerCase());
            const characterMatch =
                !this.characterIdFilter || item.characterId === this.characterIdFilter;
            const departmentMatch =
                !this.departmentIdFilter || item.departmentId === this.departmentIdFilter;
            const statusMatch =
                !this.statusFilter || item.staffStatus === this.statusFilter;
            // Return true if all conditions are met
            return staffNameMatch && characterMatch && departmentMatch && statusMatch;
        });
    },
    },
    mounted() {
        this.getCharacterData()
        this.getDepartmentData()
        this.getStaffData()
    },
    methods: {
        handlePageChange(page) {
            this.currentPage = page
        },
        openAddStaffDialog() {
            this.addStaffDialogVisible = true
        },
        addStaff() {
            console.log(this.addStaffForm)
            this.$confirm('确定添加新员工？', '提示', {
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                type: 'warning'
            })
                .then(async () => {
                    this.datafinished = true
                    await axios
                        .post(`${this.$apiBaseUrl}/staffmanage/createstaff`, this.addStaffForm)
                        .then((response) => {
                            console.log(response)
                            this.addStaffDialogVisible = false
                            this.getStaffData()
                        })
                        .catch((error) => {
                            console.log('Edit user failed!')
                        })
                })
                .then(() => {
                    this.$message({
                        type: 'success',
                        message: '添加成功'
                    })
                })
                .catch(() => {
                    this.$message({
                        type: 'info',
                        message: '已取消添加'
                    })
                })
        },
        async previewStaff(row) {
            console.log(row)
            const response = await axios.post(`${this.$apiBaseUrl}/staffmanage/getstaffinfo`, {
                staffId: row.staffId
            })
            this.previewStaffForm = response.data
            this.previewStaffDialogVisible = true

        },
        async openEditWechat(row) {
            try {
                const response = await axios.post(`${this.$apiBaseUrl}/staffmanage/getstaffinfo`, {
                    staffId: row.staffId
                })
                const data = response.data
                this.editWechatForm = {
                    staffId: data.staffId,
                    staffName: data.staffName,
                    wechatId: data.wechatId || ''
                }
                this.editWechatDialogVisible = true
            } catch (error) {
                this.$message.error('加载微信ID失败')
            }
        },
        async updateWechatId() {
            if (!this.editWechatForm.staffId) {
                this.$message.error('缺少员工ID')
                return
            }
            try {
                await axios.post(`${this.$apiBaseUrl}/staffmanage/updatewechatid`, {
                    staffId: this.editWechatForm.staffId,
                    wechatId: this.editWechatForm.wechatId
                })
                this.$message.success('保存成功')
                this.editWechatDialogVisible = false
                this.getStaffData()
            } catch (error) {
                this.$message.error(error?.response?.data?.error || '保存失败')
            }
        },
        editStaff(row) {
            console.log(row)
        },
        resignStaff(row) {
            console.log(row)
            this.$confirm('确定离职该员工？', '提示', {
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                type: 'warning'
            })
                .then(async () => {
                    await axios
                        .post(`${this.$apiBaseUrl}/staffmanage/resignstaff`, {
                            staffId: row.staffId
                        })
                        .then((response) => {
                            console.log(response)
                            this.getStaffData()
                        })
                        .catch((error) => {
                            console.log('Resign staff failed!')
                        })
                })
                .then(() => {
                    this.$message({
                        type: 'success',
                        message: '离职成功'
                    })
                })
                .catch(() => {
                    this.$message({
                        type: 'info',
                        message: '已取消离职'
                    })
                })
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
            const response = await axios.get(`${this.$apiBaseUrl}/staffmanage/getallstaff`)
            console.log(response)
            this.staffList = response.data
        }
    }
}
</script>
