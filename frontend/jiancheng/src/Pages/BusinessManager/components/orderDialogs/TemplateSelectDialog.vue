<template>
    <el-dialog title="选择模板" v-model="dialogStore.newOrderTemplateVis" width="50%">
        <el-input v-model="templateSearch" @input="$emit('filter')"> search </el-input>
        <el-table :data="templateDisplayData">
            <el-table-column prop="customerName" label="客户名称"></el-table-column>
            <el-table-column prop="customerBrand" label="客户商标"></el-table-column>
            <el-table-column prop="batchInfoTypeName" label="配码名称"></el-table-column>

            <el-table-column>
                <template #default="scope">
                    <el-button type="primary" @click="$emit('create-from-template', scope.row)">模板创建订单</el-button>
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
