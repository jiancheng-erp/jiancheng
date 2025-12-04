<template>
    <el-dialog
        title="裁剪并上传鞋图"
        v-model="dialogStore.reUploadImageDialogVis"
        width="60%"
        :close-on-click-modal="false"
    >
        <!-- 选择文件 -->
        <input
            type="file"
            accept="image/*"
            @change="onFileChange"
        />

        <!-- 裁剪区域 -->
        <Cropper
            v-if="imageUrl"
            ref="cropperRef"
            :src="imageUrl"
            :auto-zoom="true"
            :resize-image="true"
            :background-class="'cropper-background'"
        />

        <template #footer>
            <el-button @click="emit('close')">取消</el-button>
            <el-button
                type="primary"
                :disabled="!imageUrl"
                @click="emit('upload')"
            >
                确认上传
            </el-button>
        </template>
    </el-dialog>
</template>

<script setup>
import { ref, defineProps, defineEmits, defineExpose } from 'vue'
import { useOrderDialogStore } from '@/Pages/BusinessManager/stores/orderDialog'
import { Cropper } from 'vue-advanced-cropper'

const props = defineProps({
    imageUrl: {
        type: String,
        default: ''
    }
})

const emit = defineEmits(['file-change', 'close', 'upload'])

const dialogStore = useOrderDialogStore()

// 裁剪组件的 ref
const cropperRef = ref(null)

// 给父组件使用的 getResult 方法
const getResult = () => {
    if (!cropperRef.value) return null
    return cropperRef.value.getResult()
}

// 暴露给父组件（this.$refs.reUploadImageDialog.getResult）
defineExpose({
    getResult
})

// input change 时，把事件往外抛给父组件的 onFileChange
const onFileChange = (event) => {
    emit('file-change', event)
}
</script>

<style scoped>
.cropper-background {
    background: #f5f5f5;
}
</style>
