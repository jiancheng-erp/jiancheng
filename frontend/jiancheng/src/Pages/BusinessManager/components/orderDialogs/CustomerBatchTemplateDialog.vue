<template>
    <el-dialog title="客户配码模板列表" v-model="dialogStore.customerBatchTemplateVis" width="60%" :close-on-click-modal="false">
        <el-table :data="batchTemplateDisplayData" border stripe height="500" @selection-change="$emit('selection-change', $event)">
            <el-table-column type="selection" width="55"></el-table-column>
            <el-table-column type="expand">
                <template #default="scope">
                    <el-table :data="scope.row.batchInfoData" border>
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
                </template>
            </el-table-column>
            <el-table-column prop="templateName" label="模板名称"></el-table-column>
            <el-table-column prop="customerName" label="客户名称"></el-table-column>
            <el-table-column prop="customerBrand" label="客户商标"></el-table-column>
            <el-table-column prop="templateDescription" label="模板描述"></el-table-column>
            <el-table-column label="操作" width="200">
                <template #default="scope">
                    <el-button type="danger" @click="$emit('delete-template', scope.row)">删除模板</el-button>
                </template>
            </el-table-column>
        </el-table>

        <template #footer>
            <el-button @click="$emit('close')">取消</el-button>
            <el-button type="primary" @click="$emit('confirm-load')"> 确认加载 </el-button>
        </template>
    </el-dialog>
</template>

<script setup>
import { useOrderDialogStore } from '@/Pages/BusinessManager/stores/orderDialog'

defineProps({
    batchTemplateDisplayData: {
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

defineEmits(['selection-change', 'delete-template', 'confirm-load', 'close'])

const dialogStore = useOrderDialogStore()
</script>