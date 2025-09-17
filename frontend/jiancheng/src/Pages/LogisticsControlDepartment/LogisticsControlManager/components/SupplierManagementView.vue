<template>
    <el-row :gutter="20">
        <el-col :span="24" style="font-size: xx-large; text-align: center;">供应商管理</el-col>
    </el-row>

    <el-row :gutter="20">
        <el-col>
            <el-input v-model="searchQuery" placeholder="搜索供应商名称" clearable @clear="filterSuppliers"
                @change="filterSuppliers" style="width: 300px;" />
        </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px;">
        <el-col :span="24">
            <el-table :data="paginatedSupplierData" border style="height: 500px;">
                <el-table-column prop="supplierName" label="供应商名称"></el-table-column>
                <el-table-column prop="supplierField" label="供应商供货类型"></el-table-column>
                <el-table-column label="操作">
                    <template #default="scope">
                        <el-button type="primary" @click="openEditDialog(scope.row)">修改</el-button>
                        <el-button type="danger" @click="deleteSupplier(scope.row)">删除</el-button>
                    </template>
                </el-table-column>
            </el-table>
        </el-col>
    </el-row>

    <!-- Pagination -->
    <el-row :gutter="20" style="margin-top: 20px;">
        <el-col :span="24" style="text-align: center;">
            <el-pagination @size-change="handleSizeChange" @current-change="handleCurrentChange"
                :current-page="currentPage" :page-size="pageSize" :page-sizes="[5, 10, 20, 50]"
                layout="total, sizes, prev, pager, next, jumper" :total="supplierData.length">
            </el-pagination>
        </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px;">
        <el-col :span="4" :offset="20">
            <el-button type="primary" size="default" @click="isCreateSupplierDialogVisible = true">创建新供应商</el-button>
        </el-col>
    </el-row>

    <el-dialog title="创建新供应商" v-model="isCreateSupplierDialogVisible" width="30%">
        <el-form>
            <el-form-item label="供应商名称: ">
                <el-input v-model="addSupplierData.supplierName"></el-input>
            </el-form-item>
            <el-form-item label="供应商供货类型: ">
                <el-select v-model="addSupplierData.supplierType" placeholder="请选择供货类型">
                    <el-option v-for="item in FieldData" :key="item.value" :label="item.label" :value="item.value">
                    </el-option>
                </el-select>
            </el-form-item>
        </el-form>
        <template #footer>
            <span>
                <el-button @click="cancelCreateSupplier">取消</el-button>
                <el-button type="primary" @click="confirmSubmit">确认</el-button>
            </span>
        </template>
    </el-dialog>

    <el-dialog title="修改供应商" v-model="isEditSupplierDialogVisible" width="30%">
        <el-form>
            <el-form-item label="供应商名称: ">
                <el-input v-model="addSupplierData.supplierName"></el-input>
            </el-form-item>
            <el-form-item label="供应商供货类型: ">
                <el-select v-model="addSupplierData.supplierType" placeholder="请选择供货类型">
                    <el-option v-for="item in FieldData" :key="item.value" :label="item.label" :value="item.value">
                    </el-option>
                </el-select>
            </el-form-item>
        </el-form>
        <template #footer>
            <span>
                <el-button @click="closeEditSupplierDialog">取消</el-button>
                <el-button type="primary" @click="editSupplier">确认</el-button>
            </span>
        </template>
    </el-dialog>
</template>

<script>
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus';

export default {
    data() {
        return {
            datafinished: true,
            isCreateSupplierDialogVisible: false,
            supplierData: [], // All supplier data
            currentPage: 1, // Current page
            pageSize: 10, // Items per page
            addSupplierData: {
                supplierId: null,
                supplierName: '',
                supplierType: '',
                supplierField: ''
            },
            FieldData: [
                { value: 'N', label: '普通供货商' },
                { value: 'W', label: '外加工供货商' }
            ],
            searchQuery: '', // Search query
            isEditSupplierDialogVisible: false
        }
    },
    computed: {
        // Compute paginated supplier data
        paginatedSupplierData() {
            const start = (this.currentPage - 1) * this.pageSize;
            const end = start + this.pageSize;
            return this.supplierData.slice(start, end);
        }
    },
    mounted() {
        this.getSupplierData();
    },
    methods: {
        openEditDialog(row) {
            this.addSupplierData = JSON.parse(JSON.stringify(row));
            this.isEditSupplierDialogVisible = true;
        },
        async editSupplier() {
            try {
                let data = {
                    supplierId: this.addSupplierData.supplierId,
                    supplierName: this.addSupplierData.supplierName,
                    supplierType: this.addSupplierData.supplierType
                }
                await axios.put(`${this.$apiBaseUrl}/logistics/editsupplier`, data);
            }
            catch (error) {
                console.error("Error editing supplier:", error);
                if (error.response) {
                    ElMessage.error(error.response.data.message);
                }
                else {
                    ElMessage.error('修改供应商失败');
                }
                return;
            }
            this.closeEditSupplierDialog();
            this.getSupplierData();
            ElMessage.success('修改成功');
        },
        filterSuppliers() {
            if (!this.searchQuery) {
                this.getSupplierData();
                return;
            }
            const query = this.searchQuery.toLowerCase();
            this.supplierData = this.supplierData.filter(supplier =>
                supplier.supplierName.toLowerCase().includes(query)
            );
            this.currentPage = 1; // Reset to first page
        },
        async deleteSupplier(row) {
            const supplierId = row.supplierId;
            try {
                await axios.delete(`${this.$apiBaseUrl}/logistics/deleteSupplier`, {
                    data: { supplierId: supplierId }
                });
                this.getSupplierData();
                ElMessage.success('删除成功');
            } catch (error) {
                console.error("Error deleting supplier:", error);
                if (error.response) {
                    ElMessage.error(error.response.data.message);
                }
                else {
                    ElMessage.error('删除供应商失败');
                }
            }
        },
        async getSupplierData() {
            try {
                const response = await axios.get(`${this.$apiBaseUrl}/logistics/allsuppliers`);
                this.supplierData = response.data;
                // this.datafinished = false;
            } catch (error) {
                console.error("Error fetching supplier data:", error);
                this.datafinished = false;
            }
        },
        async createSupplier() {
            try {
                this.datafinished = true;
                await axios.post(`${this.$apiBaseUrl}/logistics/createsupplier`, this.addSupplierData);
                this.isCreateSupplierDialogVisible = false;
                this.getSupplierData();
                ElMessage.success('创建成功');
            } catch (error) {
                console.error("Error creating supplier:", error);
                if (error.response) {
                    ElMessage.error(error.response.data.message);
                }
                else {
                    ElMessage.error('创建供应商失败');
                }
            }
        },
        emptySupplierData() {
            this.addSupplierData.supplierId = null;
            this.addSupplierData.supplierName = '';
            this.addSupplierData.supplierField = '';
        },
        cancelCreateSupplier() {
            this.emptySupplierData();
            this.isCreateSupplierDialogVisible = false;
        },
        closeEditSupplierDialog() {
            this.emptySupplierData();
            this.isEditSupplierDialogVisible = false;
        },
        confirmSubmit() {
            ElMessageBox.confirm('确认提交吗?', '提示', {
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                type: 'warning'
            }).then(() => {
                this.createSupplier();
            }).catch(() => {
                this.$message({
                    type: 'info',
                    message: '已取消提交'
                });
            });
        },
        handleSizeChange(newSize) {
            this.pageSize = newSize;
            this.currentPage = 1; // Reset to first page
        },
        handleCurrentChange(newPage) {
            this.currentPage = newPage;
        }
    }
}
</script>
