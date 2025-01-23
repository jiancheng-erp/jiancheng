<template>
    <el-row :gutter="20" style="margin-top: 20px">
        <el-col :span="4" :offset="0" style="white-space: nowrap;">
            <el-input v-model="productionTeamSearch" placeholder="搜索车间" clearable @keypress.enter="getProductionLines()"
                @clear="getProductionLines" />
        </el-col>
    </el-row>
    <el-row :gutter="20" style="margin-top: 20px">
        <el-button @click="openNewDialog">
            添加组号
        </el-button>
        <el-button v-if="!isEditing" type="primary" @click="editProductionLine()">编辑</el-button>
        <el-button v-if="isEditing" type="primary" @click="saveProductionLine()">保存</el-button>
        <el-button v-if="isEditing" type="primary" @click="isEditing = false">退出编辑</el-button>
    </el-row>
    <el-row :gutter="20" style="margin-top: 20px">
        <el-table :data="productionLinesData" border>
            <el-table-column type="index"></el-table-column>
            <el-table-column prop="productionTeam" label="车间"></el-table-column>
            <el-table-column prop="productionLineName" label="组号名字">
                <template #default="scope">
                    <p v-if="!isEditing">{{ scope.row.productionLineName }}</p>
                    <el-input v-else v-model="scope.row.productionLineName"></el-input>
                </template>
            </el-table-column>
            <!-- <el-table-column label="操作">
                <template #default="scope">
                    <el-button-group>
                        <el-button type="danger" @click="deleteProductionLine(scope.row)">删除</el-button>
                    </el-button-group>
                </template>
            </el-table-column> -->
        </el-table>
    </el-row>
    <el-dialog v-model="isNewDialogOpen" title="新组别" width="50%">
        <el-form :model="newProductionLineForm">
            <el-form-item prop="team" label="组别名字">
                <el-select v-model="newProductionLineForm.team">
                    <el-option v-for="item in ['裁断', '针车预备', '针车', '成型']" :value="item" :label="item">
                    </el-option>
                </el-select>
            </el-form-item>
            <el-form-item prop="name" label="组别名字">
                <el-input v-model="newProductionLineForm.name"></el-input>
            </el-form-item>
        </el-form>
        <el-button @click="addNewProductionLine">确认</el-button>
    </el-dialog>
</template>
<script>
import axios from 'axios'
import { ElMessage } from 'element-plus';
export default {
    data() {
        return {
            productionTeamSearch: '',
            productionLinesData: [],
            isNewDialogOpen: false,
            newProductionLineForm: {
                name: null,
                team: null,
            },
            isEditing: false
        }
    },
    mounted() {
        this.getProductionLines()
    },
    methods: {
        openNewDialog() {
            this.isNewDialogOpen = true
        },
        async addNewProductionLine() {
            try {
                await axios.post(`${this.$apiBaseUrl}/production/addnewproductionline`, this.newProductionLineForm)
                ElMessage.success("添加成功")
            }
            catch (error) {
                ElMessage.error(error.response.data.message)
            }
            this.newProductionLineForm = {
                name: null,
                team: null,
            }
            this.isNewDialogOpen = false
            this.getProductionLines()
        },
        async getProductionLines() {
            let params = { "team": this.productionTeamSearch }
            let response = await axios.get(`${this.$apiBaseUrl}/production/getallproductionlines`, { params })
            this.productionLinesData = response.data
        },
        async editProductionLine() {
            this.isEditing = true
        },
        async saveProductionLine() {
            try {
                await axios.patch(`${this.$apiBaseUrl}/production/editproductionline`, this.productionLinesData)
                ElMessage.success("编辑成功")
                this.isEditing = false
                this.getProductionLines()
            }
            catch (error) {
                ElMessage.error(error)
            }
        },
        async deleteProductionLine(row) {
            try {
                let params = { "productionLineId": row.productionLineId }
                await axios.delete(`${this.$apiBaseUrl}/production/deleteproductionline`, { params })
                ElMessage.success("删除成功")
                this.getProductionLines()
            }
            catch (error) {
                ElMessage.error(error)
            }
        }
    }
}
</script>