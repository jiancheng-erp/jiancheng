<template>
    <el-row :gutter="20">
        <el-col :span="24" :offset="0" style="font-size: xx-large; text-align: center;">供应商管理</el-col>
    </el-row>
    <el-row :gutter="20" style="margin-top: 20px;">
        <el-col :span="24" :offset="0">
            <el-table :data="supplierData" border style="height: 500px;">
                <el-table-column prop="supplierName" label="供应商名称"></el-table-column>
                <el-table-column prop="supplierField" label="供应商供货类型"></el-table-column>
                <el-table-column prop="addDate" label="添加日期"></el-table-column>
            </el-table>
        </el-col>
    </el-row>
    <el-row :gutter="20" style="margin-top: 20px;">
        <el-col :span="4" :offset="20"><el-button type="primary" size="default"
                @click="isCreateSupplierDialogVisible = true">创建新供应商</el-button>
        </el-col>
    </el-row>
    <el-dialog
        title="创建新供应商"
        v-model="isCreateSupplierDialogVisible"
        width="30%">
        <el-form>
            <el-form-item label="供应商名称: ">
                <el-input v-model="addSupplierData.supplierName"></el-input>
            </el-form-item>
            <el-form-item label="供应商供货类型: ">
                <el-select v-model="addSupplierData.supplierField" placeholder="请选择供货类型" multiple>
                    <el-option v-for="item in FieldData" :key="item.value" :label="item.label" :value="item.value">
                    </el-option>
                    </el-select>
            </el-form-item>
            </el-form>
        <template #footer>
        <span>
            <el-button @click="">Cancel</el-button>
            <el-button type="primary" @click="">OK</el-button>
        </span>
        </template>
    </el-dialog>
    
</template>

<script>

export default {
    data() {
        return {
            isCreateSupplierDialogVisible: false,
            supplierData: [],
            addSupplierData: {
                supplierName: '',
                supplierField: []
            },
            FieldData: [
                {
                    value: '面料',
                    label: '面料'
                },
                {
                    value: '里料',
                    label: '里料'
                },
                {
                    value: '辅料',
                    label: '辅料'
                },
                {
                    value: '底材',
                    label: '底材'
                },
                {
                    value: '耗材',
                    label: '耗材'
                },
                {
                    value: '鞋楦',
                    label: '鞋楦'
                },
                {
                    value: '固定资产',
                    label: '固定资产'
                }
            ]
        }
    }
}
</script>
