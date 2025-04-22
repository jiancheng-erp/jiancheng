<template>
    <el-dialog title="搜索条件设置" v-model="localVisible" @close="handleClose" width="30%">
        <el-form>
            <el-form-item label="客户名称">
                <el-select v-model="searchForm.customerNameSearch" value-key="" placeholder="例：37" clearable filterable>
                    <el-option v-for="item in customerNameOptions" :value="item" :label="item" />
                </el-select>
            </el-form-item>
            <el-form-item label="客户商标">
                <el-input v-model="searchForm.customerBrandSearch" placeholder="例：CLOWSE" clearable />
            </el-form-item>
            <el-form-item label="订单号">
                <el-input v-model="searchForm.orderRIdSearch" placeholder="例：K24-001" clearable />
            </el-form-item>
            <el-form-item label="工厂型号">
                <el-input v-model="searchForm.shoeRIdSearch" placeholder="例：3E1122" clearable />
            </el-form-item>
            <el-form-item label="客户型号">
                <el-input v-model="searchForm.customerProductNameSearch" placeholder="例：CL-B001" clearable />
            </el-form-item>
            <el-form-item label="状态点">
                <el-select v-model="searchForm.statusNodeSearch" placeholder="例：生产中" clearable>
                    <el-option v-for="item in [
                        '未排期',
                        '已保存排期',
                        '生产前确认',
                        '生产中',
                        '生产结束',
                    ]" :key="item" :label="item" :value="item">
                    </el-option>
                </el-select>
            </el-form-item>
            <el-form-item label="订单日期">
                <el-date-picker v-model="searchForm.orderDateRangeSearch" type="daterange" range-separator="至"
                    start-placeholder="订单开始日期" end-placeholder="订单结束日期" value-format="YYYY-MM-DD" clearable>
                </el-date-picker>
            </el-form-item>
            <el-form-item label="订单排序">
                <el-select v-model="searchForm.sortCondition" clearable>
                    <el-option v-for="item in [
                        '最新',
                        '最旧',
                        '周期最长',
                        '数量最多',
                    ]" :key="item" :label="item" :value="item">
                    </el-option>
                </el-select>
            </el-form-item>
        </el-form>

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
        customerNameOptions: {
            type: Array,
            required: true,
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