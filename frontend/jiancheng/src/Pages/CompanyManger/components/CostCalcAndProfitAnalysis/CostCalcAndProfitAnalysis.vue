<template>
    <div class="content">
        <el-row :gutter="20" style="margin-top: 20px; justify-content: space-between; width: 100%">
            <el-col class="u-nowrap" :span="4" :offset="0">
                订单号筛选：
                <el-input v-model="orderRIdSearch" placeholder="请输入订单号" clearable />
                <el-button class="u-ml-5"
                    type="primary"
                    @click="updataParams('orderRid', orderRIdSearch)"
                   
                    >筛选</el-button
                >
            </el-col>
            <!-- <el-button type="primary" size="middle" @click="" :icon="Download"></el-button> -->
        </el-row>
        <el-table
            :data="currentTableData"
            style="width: 100%; margin-bottom: 20px; height: 600px"
            @cell-click="showDialog1"
        >
            <el-table-column>
                <el-table-column type="expand">
                    <template #default="props">
                        <el-table
                            :data="props.row.orderShoes"
                            style="width: 100%; margin-bottom: 5px;"
                            @cell-click="showDialog2"
                        >
                            <el-table-column prop="shoeRId" label="工厂鞋型编号" sortable />
                            <el-table-column prop="shoeName" label="客户鞋型编号" sortable />
                            <el-table-column
                                prop="totalMaterialCost"
                                label="材料采购成本"
                                sortable
                            />
                            <el-table-column
                                prop="labourCost"
                                label="生产人工成本"
                                sortable
                            />
                            <el-table-column
                                prop="administrativeExpenses"
                                label="行政费用"
                                sortable
                            />
                            <el-table-column prop="logisticsCost" label="物流费用" sortable />
                            <el-table-column prop="outsouceCost" label="外加工成本" sortable />
                            <el-table-column prop="profit" label="订单利润" sortable />
                            <el-table-column prop="profitPerShoe" label="效率指标" sortable />
                        </el-table>
                    </template>
                </el-table-column>
                <el-table-column prop="orderRid" label="订单编号" sortable />
                <el-table-column prop="orderTotalMaterialCost" label="材料采购成本" sortable />
                <el-table-column prop="orderTotalLabourCost" label="生产人工成本" sortable />
                <el-table-column
                    prop="orderTotalAdministrativeExpenses"
                    label="行政费用"
                    sortable
                />
                <el-table-column prop="orderTotalLogisticsCost" label="物流费用" sortable />
                <el-table-column prop="orderTotalOutsouceCost" label="外包成本" sortable />
                <el-table-column prop="orderTotalProfit" label="订单利润" sortable />
                <el-table-column prop="orderTotalProfitPerShoe" label="效率指标" sortable />
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
    <el-dialog title="生产人工成本详细数据" v-model="dialogVisible1" width="50%">
        <el-table
            :data="smallTabelData1"
            style="width: 100%; margin-bottom: 20px; height: 150px"
        >
            <el-table-column>
                <el-table-column prop="orderTotalCuttingCost" label="裁断内部成本" sortable />
                <el-table-column prop="orderTotalSewingCost" label="针车内部成本" sortable />
                <el-table-column prop="orderTotalMoldingCost" label="成型内部成本" sortable />
            </el-table-column>
        </el-table>
    </el-dialog>
    <el-dialog title="生产人工成本详细数据" v-model="dialogVisible2" width="50%">
        <el-table
            :data="smallTabelData2"
            style="width: 100%; margin-bottom: 20px; height: 150px"
        >
            <el-table-column>
                <el-table-column prop="cuttingCost" label="裁断内部成本" sortable />
                <el-table-column prop="sewingCost" label="针车内部成本" sortable />
                <el-table-column prop="moldingCost" label="成型内部成本" sortable />
            </el-table-column>
        </el-table>
    </el-dialog>
</template>

<script lang="js" setup name="CostCalcAndProfitAnalysis">
import { ref, onMounted, getCurrentInstance, watch } from 'vue'
import useTablePagination from '../../hooks/useTablePagination'
import { Download } from '@element-plus/icons-vue'

const $api_baseUrl = getCurrentInstance().appContext.config.globalProperties.$apiBaseUrl

let orderRIdSearch = ref('')
const dialogVisible1 = ref(false)
let smallTabelData1 = ref([])
const dialogVisible2 = ref(false)
let smallTabelData2 = ref([])
// let localData
const routeMsg = `${$api_baseUrl}/headmanager/getcostinfo`
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


function showDialog1(row, column, cell, event) {
    if (column.getColumnIndex() === 0) {
        return;
    }
    // 增加判断展示的是否是人工成本列的单元格
    smallTabelData1.value.splice(0, 1, row)
    dialogVisible1.value = true
}
function showDialog2(row, column, cell, event) {
    // 增加判断展示的是否是人工成本列的单元格
    smallTabelData2.value.splice(0, 1, row)
    dialogVisible2.value = true
}
</script>

<style scoped>
.content {
    height: calc(100% - 40px);
}
</style>
