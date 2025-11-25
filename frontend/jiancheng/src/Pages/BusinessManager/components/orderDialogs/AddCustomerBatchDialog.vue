<template>
    <el-dialog title="添加配码" v-model="dialogStore.addCustomerBatchDialogVisible" width="30%">
        <el-form :model="batchForm" label-width="120px" :inline="false" size="default">
            <el-form-item label="配码名称">
                <el-input v-model="batchForm.packagingInfoName"></el-input>
            </el-form-item>
            <el-form-item label="配码地区">
                <el-input v-model="batchForm.packagingInfoLocale" disabled="true"></el-input>
            </el-form-item>
            <el-form-item v-for="col in Object.keys(attrMapping).filter((key) => curBatchType[key] != null)" :key="col" :label="curBatchType[col]">
                <el-input v-model="batchForm[attrMapping[col]]"></el-input>
            </el-form-item>
        </el-form>

        <template #footer>
            <span>
                <el-button @click="$emit('close')">取消</el-button>
                <el-button type="primary" @click="$emit('submit')">确认提交</el-button>
            </span>
        </template>
    </el-dialog>
</template>

<script setup>
import { useOrderDialogStore } from '@/Pages/BusinessManager/stores/orderDialog'

const batchForm = defineModel('batchForm', { type: Object, default: () => ({}) })

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

defineEmits(['close', 'submit'])

const dialogStore = useOrderDialogStore()
</script>
