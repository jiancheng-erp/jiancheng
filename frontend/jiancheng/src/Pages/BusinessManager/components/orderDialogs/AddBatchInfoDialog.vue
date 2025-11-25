<template>
    <el-dialog title="配码添加" v-model="dialogStore.addBatchInfoDialogVis" width="90%" @close="$emit('close')">
        <el-col :span="4" :offset="15">
            <el-input
                v-model="batchName"
                placeholder="请输入配码名称"
                size="default"
                :suffix-icon="'el-icon-search'"
                clearable
                @input="$emit('filter-with-selection')"
            ></el-input>
        </el-col>
        <el-row :gutter="20">
            <el-col :span="24" :offset="0">
                <el-descriptions title="" :column="2" border>
                    <el-descriptions-item label="客户名称" align="center">{{ newOrderForm.customerName }}</el-descriptions-item>
                    <el-descriptions-item label="客户商标" align="center">{{ newOrderForm.customerBrand }}</el-descriptions-item>
                </el-descriptions>
            </el-col>
        </el-row>
        <el-row :gutter="20">
            <el-table
                :data="customerDisplayBatchData"
                border
                stripe
                height="500"
                @selection-change="$emit('selection-change', $event)"
                ref="batchTable"
            >
                <el-table-column size="small" type="selection" align="center"> </el-table-column>
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
        </el-row>

        <template #footer>
            <el-button @click="$emit('close')">取消</el-button>
            <el-button @click="$emit('open-add-customer-batch')"> 添加新配码</el-button>
            <el-button type="success" @click="$emit('open-save-template')"> 保存为新模板</el-button>
            <el-button type="primary" @click="$emit('save-batch')"> 保存配码</el-button>
        </template>
    </el-dialog>
</template>

<script setup>
import { computed, ref, defineExpose } from 'vue'
import { useOrderDialogStore } from '@/Pages/BusinessManager/stores/orderDialog'

const props = defineProps({
    batchNameFilter: {
        type: String,
        default: ''
    },
    newOrderForm: {
        type: Object,
        default: () => ({})
    },
    customerDisplayBatchData: {
        type: Array,
        default: () => []
    },
    attrMapping: {
        type: Object,
        default: () => ({})
    },
    curBatchType: {
        type: Object,
        default: () => ({})
    }
})

const emit = defineEmits([
    'selection-change',
    'update:batchNameFilter',
    'close',
    'open-add-customer-batch',
    'open-save-template',
    'save-batch',
    'filter-with-selection'
])

const dialogStore = useOrderDialogStore()
const batchTable = ref()

const batchName = computed({
    get: () => props.batchNameFilter,
    set: (val) => emit('update:batchNameFilter', val)
})

defineExpose({
    batchTable
})
</script>
