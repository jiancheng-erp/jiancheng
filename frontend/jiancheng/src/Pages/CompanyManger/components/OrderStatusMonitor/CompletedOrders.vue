<template>
    <div class="content">
        <el-row :gutter="16" style="margin-top: 20px; justify-content: space-between; width: 100%">
            <el-col class="u-nowrap" :span="4" :offset="0">
                已完成订单号筛选：
                <el-input v-model="orderRIdSearch" placeholder="请输入订单号" clearable />
                <el-button class="u-ml-5"
                    type="primary"
                    size="middle"
                    @click="updataParams('orderRid', orderRIdSearch)"
                   
                    >筛选</el-button
                >
            </el-col>
            <!-- <el-button type="primary" size="middle" @click="" :icon="Download"></el-button> -->
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
                            style="width: 100%; margin-bottom: 20px"
                            @cell-mouse-enter="enterSelectionRows"
                            @cell-mouse-leave="leaveSelectionRows"
                        >
                            <el-table-column />
                            <el-table-column prop="factoryId" label="工厂鞋型编号" sortable />
                            <el-table-column prop="customerId" label="客户鞋型编号" sortable />
                            <el-table-column
                                prop="producPrepareCycle"
                                label="生产预备周期(天)"
                                sortable
                            />
                            <el-table-column prop="productionCycle" label="生产周期(天)" sortable />
                            <el-table-column prop="deliveryCycle" label="发货周期(天)" sortable />
                            <el-table-column prop="orderProfit" label="订单利润" sortable />
                            <el-table-column prop="projectCycle" label="项目总周期(天)" sortable />
                            <el-table-column prop="profitRatio" label="盈利比率" sortable />
                        </el-table>
                    </template>
                </el-table-column>
                <el-table-column prop="orderRId" label="订单编号" sortable />
                <el-table-column label="操作">
                    <template #default="scope">
                        <el-button
                            link
                            type="primary"
                            size="small"
                            @click="edit('edit', scope.row.orderRId, 'add', scope.row)"
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
import { ref, onMounted, getCurrentInstance } from 'vue'
import useTablePagination from '../../hooks/useTablePagination'
import { Download } from '@element-plus/icons-vue'

const edit = defineEmits(['edit'])

let orderRIdSearch = ref('')
const $api_baseUrl = getCurrentInstance().appContext.config.globalProperties.$apiBaseUrl
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
    updataParams('orderStatus', { route: routeMsg, orderType: 1 })
})

function enterSelectionRows(row, column, cell, event) {
    //增加判断是否移入的是周期几列

    createTips(event, row, `开始日期：${row.startDate} <br />结束日期：${row.endDate}`)
}
function leaveSelectionRows(row, column, cell, event) {
    removeTips(row)
}
// 创建toolTip
function createTips(el, row, value) {
    const { detailId } = row
    const tooltipDom = document.createElement('div')
    tooltipDom.style.cssText = `
        display: inline-block;
        max-width: 400px;
        max-height: 400px;
        position: absolute;
        top: ${el.clientY + 5}px;
        left: ${el.clientX}px;
        padding:5px 10px;
        overflow: auto;
        font-size: 14px;
        font-family: PingFangSC-Regular, PingFang SC;
        font-weight: 400;
        color: #595959;
        background: #fff;
        border-radius: 5px;
        z-index: 19999;
        box-shadow: 0 4px 12px 1px #ccc;
      `
    tooltipDom.innerHTML = value
    tooltipDom.setAttribute('id', `tooltip-${detailId}`)
    // 将浮层插入到body中
    document.body.appendChild(tooltipDom)
}

// 删除tooltip
function removeTips(row) {
    const { detailId } = row
    const tooltipDomLeave = document.querySelectorAll(`#tooltip-${detailId}`)
    if (tooltipDomLeave.length) {
        tooltipDomLeave.forEach((dom) => {
            document.body.removeChild(dom)
        })
    }
}
</script>
<style scoped></style>
