<template>
    <div class="content">
        <el-row :gutter="16" style="margin-top: 20px; justify-content: space-between; width: 100%">
            <el-col :span="4" :offset="0" style="white-space: nowrap">
                材料名称:
                <el-input v-model="materialName" placeholder="请输入材料名称" clearable />
            </el-col>
            <el-col :span="4" :offset="0" style="white-space: nowrap">
                材料型号:
                <el-input v-model="materialModel" placeholder="请输入材料型号" clearable />
            </el-col>
            <el-col :span="4" :offset="0" style="white-space: nowrap">
                材料规格:
                <el-input v-model="materialSpecification" placeholder="请输入材料规格" clearable />
            </el-col>
            <el-col :span="4" :offset="0" style="white-space: nowrap">
                材料厂家:
                <el-input v-model="supplierName" placeholder="请输入材料厂家" clearable />
            </el-col>
            <el-button type="primary" @click="updateData()">查询</el-button>
            <!-- <el-button type="primary" @click="" :icon="Download"></el-button> -->
        </el-row>
        <el-table
            :data="currentTableData"
            style="width: 100%; margin-bottom: 20px; height: 540px"
            row-key="id"
        >
            <el-table-column>
                <el-table-column prop="materialType" label="材料类型" sortable />
                <el-table-column prop="materialName" label="材料名称" sortable />
                <el-table-column prop="materialModel" label="材料型号" sortable />
                <el-table-column prop="materialSpecification" label="材料规格" sortable />
                <el-table-column prop="color" label="颜色" sortable />
                <el-table-column prop="supplierName" label="采购厂家" sortable />
                <el-table-column prop="unitPrice" label="材料单价" sortable />
                <el-table-column prop="purchaseAmount" label="采购数量" sortable />
                <el-table-column prop="purchaseCost" label="采购成本" sortable />
                <el-table-column prop="purchaseDate" label="最新入库日期" sortable />
                <el-table-column label="操作">
                    <template #default="scope">
                        <el-button
                            link
                            type="primary"
                            size="small"
                            @click="
                                edit(
                                    'edit',
                                    scope.row.supplierName + '_' +
                                        scope.row.materialName + '_' +
                                        scope.row.materialModel + '_' +
                                        scope.row.materialSpecification + '>' + scope.row.materialStorageId + '>' + scope.row.type + '>' + scope.row.spuMaterialId,
                                    'add'
                                )
                            "
                        >
                            历史价格曲线
                        </el-button>
                    </template>
                </el-table-column>
            </el-table-column>
        </el-table>
        <el-row :gutter="20" style="justify-content: end; width: 100%">
            <el-pagination
                @size-change="chageCurrentPageSize"
                @current-change="changeCurrentPage"
                :current-page="currentPage"
                :page-sizes="[10, 20, 30, 40]"
                :page-size="currentPageSize"
                layout="total, sizes, prev, pager, next, jumper"
                :total="currentTotalRows"
            />
        </el-row>
    </div>
</template>

<script setup>
import { ref, onMounted, getCurrentInstance } from 'vue'
import useTablePagination from '../../hooks/useTablePagination'
import { Download } from '@element-plus/icons-vue'

const edit = defineEmits(['edit'])

let materialName = ref('')
let materialModel = ref('')
let materialSpecification = ref('')
let supplierName = ref('')
const $api_baseUrl = getCurrentInstance().appContext.config.globalProperties.$apiBaseUrl
const routeMsg = `${$api_baseUrl}/headmanager/getmaterialpriceinfo`

const {
    currentPage,
    currentPageSize,
    currentTotalRows,
    currentTableData,
    getTableData,
    chageCurrentPageSize,
    changeCurrentPage,
    updataParams
} = useTablePagination()

onMounted(() => {
    updataParams('route', routeMsg)
})

function updateData() {
    updataParams('materialData', {
        materialName: materialName.value,
        materialModel: materialModel.value,
        materialSpecification: materialSpecification.value,
        supplierName: supplierName.value
    })
}
</script>

<style scoped>
.content {
    height: calc(100% - 40px);
}
</style>
