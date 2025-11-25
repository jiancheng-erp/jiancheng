<template>
    <el-dialog title="添加鞋款" v-model="dialogStore.addShoeTypeDialogVis" width="50%">
        <el-form :model="dialogStore.shoeColorForm" label-width="120px" :inline="false">
            <el-form-item label="所属鞋型编号">
                <el-input v-model="dialogStore.shoeColorForm.displayRid" :disabled="true"></el-input>
            </el-form-item>
            <el-form-item label="选择颜色">
                <el-select v-model="dialogStore.shoeColorForm.shoeTypeColors" placeholder="请选择" multiple>
                    <el-option v-for="item in colorOptions" :key="item.value" :label="item.label" :value="item.value"></el-option>
                </el-select>
            </el-form-item>
        </el-form>
        <template #footer>
            <span>
                <el-button @click="dialogStore.closeAddShoeTypeDialog">取消</el-button>
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
