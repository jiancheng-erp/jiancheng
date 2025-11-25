<template>
    <el-dialog title="新配码模板保存" v-model="dialogStore.customerBatchTemplateSaveVis" width="60%" :close-on-click-modal="false">
        <el-form :model="batchTemplateForm" label-width="120px" :inline="false">
            <el-form-item label="模板名称">
                <el-input v-model="batchTemplateForm.templateName"></el-input>
            </el-form-item>
            <el-form-item label="客户名称">
                <el-input v-model="batchTemplateForm.customerName" disabled></el-input>
            </el-form-item>
            <el-form-item label="客户商标">
                <el-input v-model="batchTemplateForm.customerBrand" disabled></el-input>
            </el-form-item>
            <el-form-item label="模板描述">
                <el-input v-model="batchTemplateForm.templateDescription"></el-input>
            </el-form-item>
        </el-form>
        <el-table :data="batchTemplateForm.templateDetail" border stripe height="500">
            <el-table-column prop="packagingInfoName" label="配码名称" sortable />
            <el-table-column prop="packagingInfoLocale" label="配码地区" sortable />
            <el-table-column
                v-for="col in Object.keys(attrMapping).filter((key) => curBatchType[key] != null)"
                :key="col"
                :label="curBatchType[col]"
                :prop="attrMapping[col]"
            ></el-table-column>
            <el-table-column prop="totalQuantityRatio" label="比例和" sortable />
        </el-table>

        <template #footer>
            <el-button @click="$emit('close')">取消</el-button>
            <el-button type="primary" @click="$emit('save')"> 确认保存 </el-button>
        </template>
    </el-dialog>
</template>

<script setup>
import { useOrderDialogStore } from '@/Pages/BusinessManager/stores/orderDialog'

const batchTemplateForm = defineModel('batchTemplateForm', { type: Object, default: () => ({ templateDetail: [] }) })

defineProps({
    attrMapping: {
        type: Object,
        default: () => ({})
    },
    curBatchType: {
        type: Object,
        default: () => ({})
    }
})

defineEmits(['save', 'close'])

const dialogStore = useOrderDialogStore()
</script>