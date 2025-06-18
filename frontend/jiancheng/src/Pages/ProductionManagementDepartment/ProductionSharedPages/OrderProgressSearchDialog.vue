<template>
    <el-form :inline="true">
        <el-form-item label="客户名称">
            <el-select v-model="localSearchForm.customerNameSearch" value-key="" placeholder="例：37" clearable filterable
                @change="handleConfirm">
                <el-option v-for="item in customerNameOptions" :value="item" :label="item" />
            </el-select>
        </el-form-item>
        <el-form-item label="客户商标">
            <el-input v-model="localSearchForm.customerBrandSearch" placeholder="例：CLOWSE" @change="handleConfirm" clearable />
        </el-form-item>
        <el-form-item label="订单号">
            <el-input v-model="localSearchForm.orderRIdSearch" placeholder="例：K24-001" @change="handleConfirm" clearable />
        </el-form-item>
        <el-form-item label="工厂型号">
            <el-input v-model="localSearchForm.shoeRIdSearch" placeholder="例：3E1122" @change="handleConfirm" clearable />
        </el-form-item>
        <el-form-item label="客户型号">
            <el-input v-model="localSearchForm.customerProductNameSearch" placeholder="例：CL-B001" @change="handleConfirm" clearable />
        </el-form-item>
        <el-form-item label="状态点">
            <el-select v-model="localSearchForm.statusNodeSearch" placeholder="例：生产中" @change="handleConfirm" clearable style="width: 150px;">
                <el-option v-for="item in [
                    '裁断未开始',
                    '裁断进行中',
                    '预备未开始',
                    '预备进行中',
                    '针车未开始',
                    '针车进行中',
                    '成型未开始',
                    '成型进行中',
                    '生产已结束',
                ]" :key="item" :label="item" :value="item">
                </el-option>
            </el-select>
        </el-form-item>
        <el-form-item label="订单日期">
            <el-date-picker v-model="localSearchForm.orderDateRangeSearch" type="daterange" range-separator="至"
                start-placeholder="订单开始日期" end-placeholder="订单结束日期" value-format="YYYY-MM-DD" @change="handleConfirm" clearable>
            </el-date-picker>
        </el-form-item>
        <el-form-item label="订单排序">
            <el-select v-model="localSearchForm.sortCondition" @change="handleConfirm" clearable style="width: 150px;">
                <el-option v-for="item in [
                    '最新',
                    '最旧',
                    '周期最长',
                    '数量最多',
                ]" :key="item" :label="item" :value="item">
                </el-option>
            </el-select>
        </el-form-item>
        <el-form-item label="显示订单模式">
            <el-switch v-model="localSearchForm.mode" inactive-text="进行中的订单" active-text="所有订单" @change="handleConfirm"></el-switch>
        </el-form-item>
    </el-form>
</template>
<script>
import axios from 'axios'
import { markRaw } from 'vue'
import { Search } from '@element-plus/icons-vue'
export default {
    props: {
        customerNameOptions: {
            type: Array,
            required: true,
        },
        searchForm: {
            type: Object,
            required: true
        }
    },
    emits: ["updateSearchForm"],
    data() {
        return {
            localSearchForm: this.searchForm,
        }
    },
    methods: {
        handleConfirm() {
            this.$emit("updateSearchForm", this.localSearchForm);
        },
    },
}
</script>