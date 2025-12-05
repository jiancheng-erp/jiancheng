<template>
    <el-dialog title="添加新鞋型" v-model="dialogStore.addShoeDialogVis" width="50%">
        <el-form :model="dialogStore.shoeForm" label-width="120px" :inline="false">
            <el-form-item label="鞋型编号">
                <el-input v-model="dialogStore.shoeForm.shoeRid"></el-input>
            </el-form-item>
            <el-form-item label="设计师">
                <el-input v-model="dialogStore.shoeForm.shoeDesigner"></el-input>
            </el-form-item>
            <el-form-item label="设计部门">
                <el-select v-model="dialogStore.shoeForm.shoeDepartmentId" placeholder="请选择设计部门">
                    <el-option label="开发一部" value="开发一部"></el-option>
                    <el-option label="开发二部" value="开发二部"></el-option>
                    <el-option label="开发三部" value="开发三部"></el-option>
                    <el-option label="开发五部" value="开发五部"></el-option>
                </el-select>
            </el-form-item>
            <el-form-item label="选择颜色">
                <el-select v-model="dialogStore.shoeForm.colorId" placeholder="请选择" multiple filterable>
                    <el-option v-for="item in colorOptions" :key="item.value" :label="item.label" :value="item.value"></el-option>
                </el-select>
            </el-form-item>
        </el-form>
        <template #footer>
            <span>
                <el-button @click="dialogStore.closeAddShoeDialog">取消</el-button>
                <el-button type="primary" @click="$emit('submit')">确认上传</el-button>
            </span>
        </template>
    </el-dialog>
</template>

<script setup>
import { useOrderDialogStore } from '@/Pages/BusinessManager/stores/orderDialog'

defineProps({
    colorOptions: {
        type: Array,
        default: () => []
    }
})

defineEmits(['submit'])

const dialogStore = useOrderDialogStore()
</script>
