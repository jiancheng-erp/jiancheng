<template>
    <div class="content">
        <el-row :gutter="16" style="margin-top: 20px; justify-content: space-between; width: 100%">
            <el-col :span="4" :offset="0" style="white-space: nowrap">
                进行中订单号筛选：
                <el-input v-model="orderRIdSearch" placeholder="请输入订单号" clearable />
                <el-button
                    type="primary"
                    @click="updataParams('orderRid', orderRIdSearch)"
                    style="margin-left: 20px"
                    >筛选</el-button
                >
            </el-col>
            <!-- <el-button type="primary" @click="" :icon="Download"></el-button> -->
        </el-row>
        <el-table
            :data="currentTableData"
            style="width: 100%; margin-bottom: 20px; height: 540px"
            border
        >
            <el-table-column>
                <el-table-column type="expand">
                    <template #default="props">
                        <el-table
                            :data="props.row.orderShoes"
                            style="width: calc(100% - 48px); margin-bottom: 5px; margin-left: 48px"
                        >
                            <el-table-column prop="shoeRId" label="工厂鞋型编号" sortable />
                            <el-table-column prop="shoeName" label="客户鞋型编号" sortable />
                            <el-table-column
                                prop="isMaterialArrived"
                                label="当前材料物流状态"
                                sortable
                            />
                            <el-table-column prop="orderShoeStatus" label="生产状态" sortable />
                            <el-table-column prop="outboundStatus" label="发货状态" sortable />
                        </el-table>
                    </template>
                </el-table-column>
                <el-table-column prop="orderRid" label="订单编号" sortable />
                <el-table-column prop="customerName" label="客户名称" />
                <el-table-column prop="orderStartDate" label="订单开始日期" />
                <el-table-column label="操作">
                    <template #default="scope">
                        <el-button
                            link
                            type="primary"
                            size="small"
                            @click="
                                edit('edit', scope.row.orderRid + '>' + scope.row.orderId, 'add')
                            "
                        >
                            订单详情
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
import { ref, getCurrentInstance } from 'vue'
import { onMounted } from 'vue'
import useTablePagination from '../../hooks/useTablePagination'
import { Download } from '@element-plus/icons-vue'

const edit = defineEmits(['edit'])
const $api_baseUrl = getCurrentInstance().appContext.config.globalProperties.$apiBaseUrl

let orderRIdSearch = ref('')
let importantStatusFilter = ref('')
const routeMsg = `${$api_baseUrl}/headmanager/getorderstatusinfo`
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
    updataParams('orderStatus', { route: routeMsg, orderType: 0 })
})
</script>

<style scoped></style>
