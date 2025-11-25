<template>
    <el-dialog title="裁剪并上传鞋图" v-model="dialogStore.reUploadImageDialogVis" width="60%" :close-on-click-modal="false">
        <input type="file" accept="image/*" @change="$emit('file-change', $event)" />
        <cropper v-if="imageUrl" ref="cropper" :src="imageUrl" :auto-zoom="true" :resize-image="true" :background-class="'cropper-background'" />

        <template #footer>
            <el-button @click="$emit('close')">取消</el-button>
            <el-button type="primary" :disabled="!imageUrl" @click="$emit('upload')"> 确认上传 </el-button>
        </template>
    </el-dialog>
</template>

<script setup>
import { useOrderDialogStore } from '@/Pages/BusinessManager/stores/orderDialog'
import { Cropper } from 'vue-advanced-cropper'

defineProps({
    imageUrl: {
        type: String,
        default: ''
    }
})

defineEmits(['file-change', 'close', 'upload'])

const dialogStore = useOrderDialogStore()
</script>