<template>
    <div style="padding: 20px;">
        <h3>材料单价查询</h3>

        <!-- 筛选栏 -->
        <el-row :gutter="12" style="margin-bottom: 16px;" align="middle">
            <!-- 厂家 下拉 -->
            <el-col :span="4">
                <el-select
                    v-model="filters.supplierName"
                    placeholder="厂家"
                    clearable
                    filterable
                    style="width: 100%"
                    @change="onSearch"
                >
                    <el-option
                        v-for="s in options.suppliers"
                        :key="s"
                        :label="s"
                        :value="s"
                    />
                </el-select>
            </el-col>

            <!-- 类型 下拉 -->
            <el-col :span="4">
                <el-select
                    v-model="filters.materialType"
                    placeholder="材料类型"
                    clearable
                    filterable
                    style="width: 100%"
                    @change="onSearch"
                >
                    <el-option
                        v-for="t in options.materialTypes"
                        :key="t"
                        :label="t"
                        :value="t"
                    />
                </el-select>
            </el-col>

            <!-- 名称 下拉 -->
            <el-col :span="4">
                <el-select
                    v-model="filters.materialName"
                    placeholder="材料名称"
                    clearable
                    filterable
                    style="width: 100%"
                    @change="onSearch"
                >
                    <el-option
                        v-for="n in options.materialNames"
                        :key="n"
                        :label="n"
                        :value="n"
                    />
                </el-select>
            </el-col>

            <!-- 型号 输入框 -->
            <el-col :span="4">
                <el-input
                    v-model="filters.materialModel"
                    placeholder="材料型号"
                    clearable
                    @keyup.enter="onSearch"
                />
            </el-col>

            <!-- 通用搜索 -->
            <el-col :span="5">
                <el-input
                    v-model="filters.search"
                    placeholder="通用搜索（所有字段）"
                    clearable
                    @keyup.enter="onSearch"
                >
                    <template #prefix>
                        <el-icon><Search /></el-icon>
                    </template>
                </el-input>
            </el-col>

            <el-col :span="3">
                <el-button type="primary" @click="onSearch">查询</el-button>
                <el-button @click="resetFilters">重置</el-button>
            </el-col>
        </el-row>

        <!-- 数据表格 -->
        <el-table :data="tableData" border stripe v-loading="loading">
            <el-table-column prop="materialType" label="材料类型" />
            <el-table-column prop="supplierName" label="厂家名称" />
            <el-table-column prop="materialName" label="材料名称" />
            <el-table-column prop="materialModel" label="材料型号" />
            <el-table-column prop="materialSpecification" label="材料规格" />
            <el-table-column prop="color" label="颜色" />
            <el-table-column prop="unit" label="单位" />
            <el-table-column prop="unitPrice" label="均价（元）" align="right">
                <template #default="scope">
                    {{ scope.row.unitPrice.toFixed(4) }}
                </template>
            </el-table-column>
        </el-table>

        <!-- 分页 -->
        <div style="display: flex; justify-content: flex-end; margin-top: 16px;">
            <el-pagination
                v-model:current-page="currentPage"
                v-model:page-size="pageSize"
                :page-sizes="[20, 50, 100]"
                :total="totalLength"
                layout="total, sizes, prev, pager, next, jumper"
                @size-change="onSearch"
                @current-change="fetchData"
            />
        </div>
    </div>
</template>

<script>
import axios from 'axios'
import { Search } from '@element-plus/icons-vue'

export default {
    name: 'MaterialPriceView',
    components: { Search },
    data() {
        return {
            loading: false,
            tableData: [],
            totalLength: 0,
            currentPage: 1,
            pageSize: 20,
            filters: {
                supplierName: '',
                materialType: '',
                materialName: '',
                materialModel: '',
                search: '',
            },
            options: {
                suppliers: [],
                materialTypes: [],
                materialNames: [],
            },
        }
    },
    mounted() {
        this.loadFilterOptions()
        this.fetchData()
    },
    methods: {
        async loadFilterOptions() {
            const response = await axios.get(`${this.$apiBaseUrl}/usagecalculation/getmaterialpricefilters`)
            this.options = response.data
        },
        onSearch() {
            this.currentPage = 1
            this.fetchData()
        },
        async fetchData() {
            this.loading = true
            try {
                const response = await axios.get(`${this.$apiBaseUrl}/usagecalculation/getmaterialprices`, {
                    params: {
                        page: this.currentPage,
                        pageSize: this.pageSize,
                        supplierName: this.filters.supplierName,
                        materialType: this.filters.materialType,
                        materialName: this.filters.materialName,
                        materialModel: this.filters.materialModel,
                        search: this.filters.search,
                    },
                })
                this.tableData = response.data.result
                this.totalLength = response.data.totalLength
            } finally {
                this.loading = false
            }
        },
        resetFilters() {
            this.filters = { supplierName: '', materialType: '', materialName: '', materialModel: '', search: '' }
            this.onSearch()
        },
    },
}
</script>
