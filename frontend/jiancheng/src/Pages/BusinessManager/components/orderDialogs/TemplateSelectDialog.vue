<template>
    <el-dialog title="选择模板" v-model="dialogStore.newOrderTemplateVis" width="60%">
        <el-input v-model="templateSearch" @input="$emit('filter')" placeholder="搜索模板或客户"></el-input>
        <el-table :data="templateDisplayData" style="margin-top:8px">
            <el-table-column prop="templateName" label="模板名称"></el-table-column>
            <el-table-column prop="templateDescription" label="说明"></el-table-column>
            <el-table-column prop="customerName" label="客户名称"></el-table-column>
            <el-table-column prop="customerBrand" label="客户商标"></el-table-column>
            <el-table-column label="类型">
                <template #default="scope">
                    <span>{{ scope.row.orderTemplateId ? '整单模板' : (scope.row.batchInfoTemplateId ? '配码模板' : '未知') }}</span>
                </template>
            </el-table-column>

            <el-table-column label="操作" width="260">
                <template #default="scope">
                    <el-button type="primary" @click="$emit('create-from-template', scope.row)">模板创建订单</el-button>
                    <el-button type="warning" @click="$emit('edit-template', scope.row)" style="margin-left:8px">重命名</el-button>
                    <el-button type="danger" @click="$emit('delete-template', scope.row)" style="margin-left:8px">删除</el-button>
                </template>
            </el-table-column>
        </el-table>
    </el-dialog>
</template>

<script setup>
import { computed } from 'vue'
import { useOrderDialogStore } from '@/Pages/BusinessManager/stores/orderDialog'

const props = defineProps({
    templateDisplayData: {
        type: Array,
        default: () => []
    },
    templateFilter: {
        type: String,
        default: ''
    }
})

const emit = defineEmits(['create-from-template', 'filter', 'update:templateFilter'])
const dialogStore = useOrderDialogStore()

const templateSearch = computed({
    get: () => props.templateFilter,
    set: (val) => emit('update:templateFilter', val)
})
</script>
