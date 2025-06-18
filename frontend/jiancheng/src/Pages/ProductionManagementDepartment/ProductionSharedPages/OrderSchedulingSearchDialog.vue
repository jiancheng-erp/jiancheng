<template>
    <el-form :inline="true">
        <el-form-item label="订单号">
            <el-input v-model="localSearchForm.orderRIdSearch" placeholder="例：K24-001" @change="handleConfirm" clearable />
        </el-form-item>
        <el-form-item label="工厂型号">
            <el-input v-model="localSearchForm.shoeRIdSearch" placeholder="例：3E1122" @change="handleConfirm" clearable />
        </el-form-item>
        <el-form-item label="状态点">
            <el-select v-model="localSearchForm.statusNodeSearch" placeholder="例：裁断未排期" @change="handleConfirm" clearable style="width: 150px;">
                <el-option v-for="item in [
                    '裁断未排期',
                    '预备未排期',
                    '针车未排期',
                    '成型未排期',
                    '已排期',
                ]" :key="item" :label="item" :value="item">
                </el-option>
            </el-select>
        </el-form-item>
        <!-- <el-form-item label="订单日期">
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
        </el-form-item> -->
    </el-form>
</template>
<script>
export default {
    props: {
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