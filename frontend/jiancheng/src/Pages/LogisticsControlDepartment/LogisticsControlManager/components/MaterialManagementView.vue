<template>
    <el-row :gutter="20">
        <el-col :span="24" :offset="0" style="font-size: xx-large; text-align: center;">材料管理</el-col>
    </el-row>
    <el-row :gutter="20">
        <el-col :span="24" :offset="0">
            <el-tabs v-model="tabName" type="border-card" class="demo-tabs" @tab-click="handleClick">
                <el-tab-pane label="材料类型管理" name="材料类型管理">
                    <el-row :gutter="20" style="margin-top: 20px;">
                        <el-col :span="6" :offset="0">
                            <div style="display: flex; align-items: center; white-space: nowrap;">材料名称查询：<el-input
                                    v-model="assetsNameSearch" placeholder="" size="default" :suffix-icon="Search"
                                    clearable @input="tableWholeFilter"></el-input></div>
                        </el-col>
                        <el-col :span="6" :offset="0">
                            <div style="display: flex; align-items: center; white-space: nowrap;">材料所属库查询： <el-select
                                    v-model="warehouseName" value-key="" placeholder="" clearable filterable
                                    @change="tableWholeFilter">
                                    <el-option v-for="item in isPurchaseOrderOptions" :key="item.value"
                                        :label="item.label" :value="item.value">
                                    </el-option>
                                </el-select>
                            </div>
                        </el-col>
                        <el-col :span="6" :offset="0">
                            <div style="display: flex; align-items: center; white-space: nowrap;">厂家名称查询：<el-input
                                    v-model="factoryNameSearch" placeholder="" size="default" :suffix-icon="Search"
                                    clearable @input="tableWholeFilter"></el-input></div>
                        </el-col>
                    </el-row>
                    <el-row :gutter="20" style="margin-top: 20px;">
                        <el-col :span="24" :offset="0">
                            <el-table :data="materialPurchaseFilterData" border style="height: 500px;">
                                <el-table-column prop="materialName" label="材料名称"></el-table-column>
                                <el-table-column prop="warehouseName" label="仓库名称"></el-table-column>
                                <el-table-column prop="unit" label="单位"></el-table-column>
                                <el-table-column prop="factoryName" label="厂家名称"></el-table-column>
                                <el-table-column prop="addDate" label="添加日期"></el-table-column>
                                <el-table-column label="操作"> <template #default="scope">
                                        <el-button type="primary" @click="openPreviewDialog(scope.row)">编辑</el-button>
                                        <el-button type="primary" @click="openPreviewDialog(scope.row)">删除</el-button>
                                    </template></el-table-column>
                            </el-table>
                        </el-col>
                    </el-row>
                    <el-row style="margin-top: 20px;">
                        <el-col :span="5" :offset="22"><el-button type="primary" size="default"
                                @click="openNewMaterialDialog">添加新材料</el-button>
                        </el-col>

                    </el-row>
                </el-tab-pane>
                <el-tab-pane label="材料库存查询" name="材料库存查询">
                    <el-row :gutter="20" style="margin-top: 20px;">
                        <el-col :span="4" :offset="0">
                            <div style="display: flex; align-items: center; white-space: nowrap;">材料名称查询：<el-input
                                    v-model="assetsNameSearch" placeholder="" size="default" :suffix-icon="Search"
                                    clearable @input="tableWholeFilter"></el-input></div>
                        </el-col>
                        <el-col :span="4" :offset="0">
                            <div style="display: flex; align-items: center; white-space: nowrap;">材料所属库查询： <el-select
                                    v-model="warehouseName" value-key="" placeholder="" clearable filterable
                                    @change="tableWholeFilter">
                                    <el-option v-for="item in isPurchaseOrderOptions" :key="item.value"
                                        :label="item.label" :value="item.value">
                                    </el-option>
                                </el-select>
                            </div>
                        </el-col>
                        <el-col :span="4" :offset="0">
                            <div style="display: flex; align-items: center; white-space: nowrap;">厂家名称查询：<el-input
                                    v-model="factoryNameSearch" placeholder="" size="default" :suffix-icon="Search"
                                    clearable @input="tableWholeFilter"></el-input></div>
                        </el-col>
                        <el-col :span="4" :offset="0">
                            <div style="display: flex; align-items: center; white-space: nowrap;">订单编号查询：<el-input
                                    v-model="purchaseOrderIdSearch" placeholder="" size="default" :suffix-icon="Search"
                                    clearable @input="tableWholeFilter"></el-input></div>
                        </el-col>
                        <el-col :span="4" :offset="0">
                            <div style="display: flex; align-items: center; white-space: nowrap;">鞋型编号查询：<el-input
                                    v-model="inheritIdSearch" placeholder="" size="default" :suffix-icon="Search"
                                    clearable @input="tableWholeFilter"></el-input></div>
                        </el-col>

                    </el-row>
                    <el-row :gutter="20" style="margin-top: 20px;">
                        <el-col :span="24" :offset="0">
                            <el-table :data="materialPurchaseFilterData" border style="height: 500px;">
                                <el-table-column prop="materialName" label="材料名称"></el-table-column>
                                <el-table-column prop="warehouseName" label="仓库名称"></el-table-column>
                                <el-table-column prop="unit" label="单位"></el-table-column>
                                <el-table-column prop="amountRemain" label="剩余数量"></el-table-column>
                                <el-table-column prop="unitPrice" label="采购单价"></el-table-column>
                                <el-table-column prop="valueRemain" label="剩余价值"></el-table-column>
                                <el-table-column prop="factoryName" label="厂家名称"></el-table-column>
                                <el-table-column prop="isPurchaseOrder" label="采购方式"></el-table-column>
                                <el-table-column prop="purchaseOrderId" label="订单编号"></el-table-column>
                                <el-table-column prop="inheritId" label="鞋型编号"></el-table-column>

                                <el-table-column label="操作"> <template #default="scope">
                                        <el-button type="primary" @click="openPreviewDialog(scope.row)">编辑</el-button>
                                        <el-button type="primary" @click="openPreviewDialog(scope.row)">删除</el-button>
                                    </template></el-table-column>
                            </el-table>
                        </el-col>
                    </el-row>
                </el-tab-pane>
            </el-tabs></el-col>
    </el-row>

    <el-dialog title="批量添加新材料" v-model="newMaterialVis" width="60%">
        <el-table :data="newMaterialData" border>
            <el-table-column label="材料名称">
                <template #default="scope">
                    <el-input v-model="scope.row.materialName" placeholder="" size="default" clearable></el-input>
                </template>
            </el-table-column>
            <el-table-column label="仓库名称">
                <template #default="scope">
                    <el-select v-model="scope.row.warehouseName" placeholder="" filterable @change="">
                        <el-option v-for="item in warehouseOptions" :key="item.value" :label="item.label"
                            :value="item.value">
                        </el-option>
                    </el-select>

                </template>
            </el-table-column>
            <el-table-column label="单位">
                <template #default="scope">
                    <el-input v-model="scope.row.unit" placeholder="" size="default" clearable></el-input>

                </template></el-table-column>
            <el-table-column label="厂家名称">
                <template #default="scope">
                    <el-select v-model="scope.row.factoryName" placeholder="" filterable @change="">
                        <el-option v-for="item in factoryOptions" :key="item.value" :label="item.label"
                            :value="item.value">
                        </el-option>
                    </el-select>

                </template>
            </el-table-column>
            <el-table-column label="操作"> <template #default="scope">
                    <el-button type="danger" @click="deleteCurrentRow(scope.$index,newMaterialData)">删除</el-button>
                </template></el-table-column>
        </el-table>
        <el-button type="primary" size="default" @click="addNewMaterial">添加新材料</el-button>

        <template #footer>
            <span>
                <el-button @click="">取消</el-button>
                <el-button type="primary" @click="">确认</el-button>
            </span>
        </template>
    </el-dialog>

</template>

<script>
import { Search } from '@element-plus/icons-vue';
export default {
    data() {
        return {
            Search,
            tabName: "材料类型管理",
            newMaterialVis: false,
            newMaterialData: [],
            warehouseOptions: [{
                value: "面料仓",
                label: "面料仓",
            },
            {
                value: "里料仓",
                label: "里料仓",
            },
            {
                value: "辅料仓",
                label: "辅料仓",
            },
            ],
            factoryOptions: [{
                value: "询价",
                label: "询价",
            },
            {
                value: "一一鞋材",
                label: "一一鞋材",
            },
            {
                value: "深源皮革",
                label: "深源皮革",
            },
            ]
        }
    },
    methods: {
        openNewMaterialDialog() {
            this.newMaterialVis = true
        },
        addNewMaterial() {
            // Validate that all existing rows have non-empty fields
            for (const row of this.newMaterialData) {
                if (!row.materialName || !row.warehouseName || !row.unit || !row.factoryName) {
                    this.$message({
                        type: 'warning',
                        message: '请填写所有字段'
                    });
                    return;
                }
            }
            // If validation passes, add a new row
            this.newMaterialData.push({
                materialName: '',
                warehouseName: '面料仓',
                unit: '',
                factoryName: '询价'
            });
        },
        deleteCurrentRow(index,datafield) {
            this.$confirm('确定删除此行吗？', '提示', {
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                type: 'warning'
            }).then(() => {
                datafield.splice(index, 1);
                this.$message({
                    type: 'success',
                    message: '删除成功!'
                });
            }).catch(() => {
                this.$message({
                    type: 'info',
                    message: '已取消删除'
                });
            });
        }
    }
}
</script>