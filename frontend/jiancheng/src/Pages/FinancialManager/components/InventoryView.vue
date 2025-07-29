<template>
    <div class="content">
        <el-row :gutter="20" style="margin-top: 20px; width: 100%">
            <el-col :span="4">
                <div style="display: flex; align-items: center; white-space: nowrap">
                    材料类型查询：<el-input
                        v-model="materialTypeSearch"
                        placeholder=""
                        size="default"
                        :suffix-icon="Search"
                        clearable
                        @change="filterMaterialStorage"
                    ></el-input>
                </div>
            </el-col>
            <el-col :span="4" :offset="0">
                <div style="display: flex; align-items: center; white-space: nowrap">
                    材料名称查询：<el-input
                        v-model="materialNameSearch"
                        placeholder=""
                        size="default"
                        :suffix-icon="Search"
                        clearable
                        @change="filterMaterialStorage"
                    ></el-input>
                </div>
            </el-col>
            <el-col :span="4" :offset="0">
                <div style="display: flex; align-items: center; white-space: nowrap">
                    材料规格查询：<el-input
                        v-model="specificationNameSearch"
                        placeholder=""
                        size="default"
                        :suffix-icon="Search"
                        clearable
                        @change="filterMaterialStorage"
                    ></el-input>
                </div>
            </el-col>
            <el-col :span="4" :offset="0">
                <div style="display: flex; align-items: center; white-space: nowrap">
                    材料所属库查询：
                    <el-select
                        v-model="warehouseNameSearch"
                        placeholder=""
                        clearable
                        filterable
                        @change="filterMaterialStorage"
                    >
                        <el-option
                            v-for="item in warehouseOptions"
                            :key="item.value"
                            :label="item.label"
                            :value="item.value"
                        >
                        </el-option>
                    </el-select>
                </div>
            </el-col>
            <el-col :span="4" :offset="0">
                <div style="display: flex; align-items: center; white-space: nowrap">
                    厂家名称查询：<el-input
                        v-model="factoryNameSearch"
                        placeholder=""
                        size="default"
                        :suffix-icon="Search"
                        clearable
                        @change="filterMaterialStorage"
                    ></el-input>
                </div>
            </el-col>
            <el-col :span="4" :offset="0">
                <div style="display: flex; align-items: center; white-space: nowrap">
                    订单编号查询：<el-input
                        v-model="orderRIdSearch"
                        placeholder=""
                        size="default"
                        :suffix-icon="Search"
                        clearable
                        @change="filterMaterialStorage"
                    ></el-input>
                </div>
            </el-col>
        </el-row>
        <el-row :gutter="20" style="margin-top: 20px; width: 100%">
            <el-col :span="4" :offset="0">
                <div style="display: flex; align-items: center; white-space: nowrap">
                    鞋型编号查询：<el-input
                        v-model="inheritIdSearch"
                        placeholder=""
                        size="default"
                        :suffix-icon="Search"
                        clearable
                        @change="filterMaterialStorage"
                    ></el-input>
                </div>
            </el-col>
        </el-row>
        <el-row :gutter="20" style="margin-top: 20px; width: 100%">
            <el-col :span="24" :offset="0">
                <el-table
                    v-loading="datafinished"
                    :data="materialStorageData"
                    border
                    style="height: 450px"
                >
                    <el-table-column prop="materialType" label="材料类型"></el-table-column>
                    <el-table-column prop="materialName" label="材料名称"></el-table-column>
                    <el-table-column
                        prop="materialSpecification"
                        label="材料规格"
                    ></el-table-column>
                    <el-table-column prop="warehouseName" label="仓库名称"></el-table-column>
                    <el-table-column prop="unit" label="单位" width="75"></el-table-column>
                    <el-table-column prop="amountRemain" label="剩余数量"></el-table-column>
                    <el-table-column prop="unitPrice" label="采购单价"></el-table-column>
                    <el-table-column prop="valueRemain" label="剩余价值"></el-table-column>
                    <el-table-column prop="factoryName" label="厂家名称"></el-table-column>
                    <el-table-column prop="OrderId" label="订单编号"></el-table-column>
                    <el-table-column prop="inheritId" label="鞋型编号"></el-table-column>
                <el-table-column label="操作" width="300">
                    <template #default="scope">
                        <el-button
                            type="primary"
                            @click="lockedItem(scope.row.orderDbId)"
                            >锁定库存</el-button
                        >
                    </template>
                </el-table-column>
                </el-table>
            </el-col>
        </el-row>
        <el-row :gutter="20" style="justify-content: end; width: 100%">
            <el-col :span="12" :offset="10">
                <el-pagination
                    :total="materialStorageTotal"
                    :page-size="10"
                    :v-model:current-page="currentPage2"
                    @current-change="handleCurrentChange2"
                >
                </el-pagination>
            </el-col>
        </el-row>
    </div>
</template>
<script>
import { Check, Close, Search } from '@element-plus/icons-vue'
import axios from 'axios'
export default {
    data() {
        return {
            Check,
            Close,
            materialStorageTotal: 0,
            datafinished: true,
            materialStorageData: [],
            materialStorageAllData: [],
            materialNameSearch: '',
            warehouseNameSearch: '',
            factoryNameSearch: '',
            materialTypeSearch: '',
            specificationNameSearch: '',
            Search,
            warehouseOptions: [],
            currentPage2: 1
        }
    },
    async mounted() {
        this.handleCurrentChange2(1)
    },
    methods: {
        async filterMaterialStorage() {
            this.datafinished = true
            const response = await axios.get(`${this.$apiBaseUrl}/logistics/allmaterialstorage`, {
                params: {
                    materialtype: this.materialTypeSearch,
                    materialname: this.materialNameSearch,
                    materialspec: this.specificationNameSearch,
                    warehousename: this.warehouseNameSearch,
                    factoryname: this.factoryNameSearch,
                    orderid: this.orderRIdSearch,
                    ordershoeid: this.inheritIdSearch
                }
            })
            this.materialStorageData = response.data
            this.materialStorageAllData = response.data
            this.materialStorageTotal = response.data.length
            this.datafinished = false
        },
        handleCurrentChange2(val) {
            this.currentPage2 = val
            this.materialStorageData = this.materialStorageAllData.slice(
                (this.currentPage2 - 1) * 10,
                this.currentPage2 * 10
            )
        },
        async getMaterialStorageData() {
            this.datafinished = true
            const response = await axios.get(`${this.$apiBaseUrl}/logistics/allmaterialstorage`)
            this.materialStorageData = response.data
            this.materialStorageAllData = response.data
            this.materialStorageTotal = response.data.length
            this.datafinished = false
        },
        lockedItem(){}
    }
}
</script>
<style scoped>
.content {
    height: calc(100% - 40px);
}
</style>
