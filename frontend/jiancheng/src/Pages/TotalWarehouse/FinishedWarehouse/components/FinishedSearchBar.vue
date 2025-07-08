<template>
    <el-date-picker v-if="localFilters.dateRange !== undefined" v-model="localFilters.dateRange" type="daterange" range-separator="至" start-placeholder="开始日期"
        end-placeholder="结束日期" value-format="YYYY-MM-DD" @change="getTableData" clearable />
    <el-input v-if="localFilters.dateRange !== undefined" v-model="localFilters.boundRIdSearch" placeholder="单号搜索" style="width: 200px;" @change="getTableData" clearable />
    <el-input v-model="localFilters.orderRIdSearch" placeholder="订单号搜索" style="width: 200px;" @change="getTableData" clearable />
    <el-input v-model="localFilters.shoeRIdSearch" placeholder="工厂型号搜索" style="width: 200px;" @change="getTableData" clearable />
    <el-input v-model="localFilters.customerNameSearch" placeholder="客户名称搜索" style="width: 200px;" @change="getTableData" clearable />
    <el-input v-model="localFilters.orderCIdSearch" placeholder="客户订单号搜索" style="width: 200px;" @change="getTableData" clearable />
    <el-input v-model="localFilters.customerProductNameSearch" placeholder="客户鞋型搜索" style="width: 200px;" @change="getTableData" clearable />
    <el-input v-model="localFilters.customerBrandSearch" placeholder="客户商标搜索" style="width: 200px;" @change="getTableData" clearable />

</template>
<script>
export default {
    props: {
        searchFilters: {
            type: Object,
            required: true
        },
        excludeFilters: {
            type: Array,
            default: []
        }
    },
    emits: ['confirm'],
    watch: {
        searchFilters: {
            handler(newVal) {
                this.localFilters = { ...newVal }
            },
            deep: true
        }
    },
    data() {
        return {
            localFilters: { ...this.searchFilters }
        }
    },
    methods: {
        async getTableData() {
            this.$emit('confirm', this.localFilters)
        }
    }
}
</script>