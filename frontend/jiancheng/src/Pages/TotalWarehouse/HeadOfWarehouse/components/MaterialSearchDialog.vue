<template>
    <el-dialog title="搜索条件设置" v-model="localVisible" @close="handleClose" width="30%">
        请选择仓库：
        <el-select v-model="searchForm.warehouseId" filterable clearable>
            <el-option v-for="item in warehouseOptions" :key="item.warehouseId" :value="item.warehouseId"
                :label="item.warehouseName"></el-option>
        </el-select>
        请选择材料类型：
        <el-select v-model="searchForm.materialTypeSearch" value-key="" placeholder="" clearable filterable>
            <el-option v-for="item in materialTypeOptions" :value="item" />
        </el-select>
        请选择材料名称：
        <el-select v-model="searchForm.materialNameSearch" value-key="" placeholder="" clearable filterable>
            <el-option v-for="item in materialNameOptions" :value="item.value" :label="item.label" />
        </el-select>
        请选择材料型号：
        <el-input v-model="searchForm.materialModelSearch" placeholder="" clearable />
        请选择材料规格：
        <el-input v-model="searchForm.materialSpecificationSearch" placeholder="" clearable />
        请选择材料颜色：
        <el-input v-model="searchForm.materialColorSearch" placeholder="" clearable />
        请选择材料供应商：
        <el-select v-model="searchForm.materialSupplierSearch" value-key="" placeholder="" clearable filterable>
            <el-option v-for="item in materialSupplierOptions" :value="item" />
        </el-select>
        <div style="display: block;" >
            搜索不带订单材料：
            <el-switch v-model="searchForm.isNonOrderMaterial" :active-value="1" :inactive-value="0" />
        </div>
        订单号筛选：
        <el-input v-model="searchForm.orderNumberSearch" placeholder="" clearable :disabled="searchForm.isNonOrderMaterial == 1" />
        鞋型号筛选：
        <el-input v-model="searchForm.shoeNumberSearch" placeholder="" clearable :disabled="searchForm.isNonOrderMaterial == 1" />
        采购订单号筛选：
        <el-input v-model="searchForm.purchaseDivideOrderRIdSearch" placeholder="" clearable />
        <template #footer>
            <span>
                <el-button type="primary" @click="handleClose()">返回</el-button>
                <el-button type="primary" @click="handleConfirm()">确认</el-button>
            </span>
        </template>
    </el-dialog>
</template>
<script>
import axios from 'axios'
import { markRaw } from 'vue'
import { Search } from '@element-plus/icons-vue'
export default {
    props: {
        materialTypeOptions: {
            type: Array,
            required: true,
        },
        materialSupplierOptions: {
            type: Array,
            required: true
        },
        materialNameOptions: {
            type: Array,
            required: true
        },
        warehouseOptions: {
            type: Array,
            required: true
        },
        visible: {
            type: Boolean,
            required: true
        },
        searchForm: {
            type: Object,
            required: true
        }
    },
    emits: ["update-visible", "confirm"],
    data() {
        return {
            localVisible: this.visible
        }
    },
    watch: {
        visible(newVal) {
            this.localVisible = newVal;
        },
        localVisible(newVal) {
            this.$emit("update-visible", newVal);
        },
    },
    methods: {
        handleClose() {
            this.localVisible = false;
        },
        handleConfirm() {
            this.$emit("confirm", this.searchForm);
            this.handleClose();
        },
    },
}
</script>