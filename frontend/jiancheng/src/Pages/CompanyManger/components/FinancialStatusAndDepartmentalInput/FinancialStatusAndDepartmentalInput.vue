<template>
    <div class="content">
        <el-row :gutter="20" style="margin-top: 20px; justify-content: space-between">
            <el-col class="u-nowrap" :span="4" :offset="0">
                订单号筛选：
                <el-input v-model="orderRIdSearch" placeholder="请输入订单号" clearable />
                <el-button class="u-ml-5"
                    type="primary"
                    @click="updataParams('orderRid', orderRIdSearch)"
                   
                    >筛选</el-button
                >
            </el-col>
            <!-- <el-button type="primary" size="large" @click="" :icon="Download"></el-button> -->
        </el-row>
        <el-table
            :data="currentTableData"
            style="width: 100%; margin-bottom: 20px; height: 640px"
            border
        >
            <el-table-column>
                <el-table-column type="expand">
                    <template #default="props">
                        <el-table
                            :data="props.row.orderShoes"
                            style="width: 100%; margin-bottom: 5px; margin-left: 48px"
                        >
                            <el-table-column prop="shoeRId" label="工厂鞋型编号" sortable />
                            <el-table-column prop="shoeName" label="客户鞋型编号" sortable />

                            <el-table-column prop="priceInputStatus" label="鞋型售价填写状态">
                                <template #default="scope">
                                    <el-tag
                                        :type="
                                            scope.row.priceInputStatus === '已填写'
                                                ? 'success'
                                                : scope.row.priceInputStatus === '未填写'
                                                  ? 'danger'
                                                  : 'warning'
                                        "
                                        >{{ scope.row.priceInputStatus }}</el-tag
                                    >
                                </template>
                            </el-table-column>
                            <el-table-column prop="materialInboundStatus" label="材料入库状态">
                                <template #default="scope">
                                    <el-tag
                                        :type="
                                            scope.row.materialInboundStatus === '已填写'
                                                ? 'success'
                                                : scope.row.materialInboundStatus === '未填写'
                                                  ? 'danger'
                                                  : 'warning'
                                        "
                                        >{{ scope.row.materialInboundStatus }}</el-tag
                                    >
                                </template>
                            </el-table-column>
                            <el-table-column prop="cuttingInputStatus" label="裁断价格填写状态">
                                <template #default="scope">
                                    <el-tag
                                        :type="
                                            scope.row.cuttingInputStatus === '已填写'
                                                ? 'success'
                                                : scope.row.cuttingInputStatus === '未填写'
                                                  ? 'danger'
                                                  : 'warning'
                                        "
                                        >{{ scope.row.cuttingInputStatus }}</el-tag
                                    >
                                </template>
                            </el-table-column>
                            <el-table-column prop="sewingInputStatus" label="针车价格填写状态">
                                <template #default="scope">
                                    <el-tag
                                        :type="
                                            scope.row.sewingInputStatus === '已填写'
                                                ? 'success'
                                                : scope.row.sewingInputStatus === '未填写'
                                                  ? 'danger'
                                                  : 'warning'
                                        "
                                        >{{ scope.row.sewingInputStatus }}</el-tag
                                    >
                                </template>
                            </el-table-column>
                            <el-table-column prop="moldingInputStatus" label="成型价格填写状态">
                                <template #default="scope">
                                    <el-tag
                                        :type="
                                            scope.row.moldingInputStatus === '已填写'
                                                ? 'success'
                                                : scope.row.moldingInputStatus === '未填写'
                                                  ? 'danger'
                                                  : 'warning'
                                        "
                                        >{{ scope.row.moldingInputStatus }}</el-tag
                                    >
                                </template>
                            </el-table-column>
                        </el-table>
                    </template>
                </el-table-column>
                <el-table-column prop="orderRid" label="订单编号" sortable />
                <el-table-column prop="customerName" label="客户名称" />
                <el-table-column prop="orderStartDate" label="订单开始日期" />
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

<script lang="js" setup name="CostCalcAndProfitAnalysis">
import { ref, onMounted, getCurrentInstance } from 'vue'
import useTablePagination from '../../hooks/useTablePagination'
import { Download } from '@element-plus/icons-vue'

const $api_baseUrl = getCurrentInstance().appContext.config.globalProperties.$apiBaseUrl
const routeMsg = `${$api_baseUrl}/headmanager/financialstatus`
let orderRIdSearch = ref('')
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

const cellStyle = (row) => {
    if (row.priceInputStatus === '已填写') {
        return 'sucess'
    } else if (row.priceInputStatus === '未填写') {
        return 'danger'
    } else {
        return 'sucess'
    }
}
</script>

<style scoped>
.content {
    height: calc(100% - 40px);
}
</style>
