<template>
    <div class="uncompleted-outbound">
        <el-card shadow="never" class="header-card">
            <div class="header-row">
                <div class="title">
                    <span>未出库材料查看</span>
                    <el-tag size="small" type="info" class="ml-2">只读</el-tag>
                </div>
                <div class="hint">展示尚未完成出库的材料(剩余库存 > 0)；勾选"仅看从未出过库"可只看完全未动用的入库材料。</div>
            </div>
        </el-card>

        <el-tabs v-model="activeTab" class="tabs" type="border-card">
            <el-tab-pane v-for="tab in warehouseTabs" :key="tab.key" :label="tab.label" :name="tab.key">
                <el-row :gutter="20">
                    <el-col>
                        <el-input v-model="filters[tab.key].materialName" placeholder="材料名称搜索"
                            @change="reload(tab.key)" @clear="reload(tab.key)" clearable
                            style="width: 200px;"></el-input>
                        <el-input v-model="filters[tab.key].supplierName" placeholder="厂家搜索"
                            @change="reload(tab.key)" @clear="reload(tab.key)" clearable
                            style="width: 200px; margin-left: 12px;"></el-input>
                        <el-checkbox v-model="filters[tab.key].onlyNeverOutbound" @change="reload(tab.key)"
                            style="margin-left: 16px;">仅看从未出过库</el-checkbox>
                    </el-col>
                </el-row>

                <div class="status-legend">
                    <span class="legend-item"><span class="legend-dot status-never"></span>未出库</span>
                    <span class="legend-item"><span class="legend-dot status-partial"></span>部分出库</span>
                </div>

                <el-table v-if="activeTab === tab.key" :data="state[tab.key].tableData" border stripe height="600"
                    :row-class-name="rowClassName" style="margin-top: 8px;">
                    <el-table-column prop="materialName" label="材料名称" min-width="160" show-overflow-tooltip />
                    <el-table-column prop="supplierName" label="厂家" min-width="140" show-overflow-tooltip />
                    <el-table-column prop="materialTypeName" label="材料类型" min-width="100" />
                    <el-table-column prop="materialModel" label="型号" min-width="100" show-overflow-tooltip />
                    <el-table-column prop="materialSpecification" label="规格" min-width="140" show-overflow-tooltip />
                    <el-table-column prop="materialColor" label="颜色" min-width="80" show-overflow-tooltip />
                    <el-table-column prop="actualInboundUnit" label="单位" width="70" />
                    <el-table-column prop="inboundAmount" label="累计入库" min-width="100" />
                    <el-table-column prop="outboundAmount" label="累计出库" min-width="100" />
                    <el-table-column prop="currentAmount" label="当前剩余" min-width="100" />
                    <el-table-column label="出库状态" min-width="100">
                        <template #default="scope">
                            <el-tag :type="statusTagType(scope.row)" size="small">{{ scope.row.outboundStatus }}</el-tag>
                        </template>
                    </el-table-column>
                    <el-table-column prop="orderRId" label="订单号" min-width="120" show-overflow-tooltip />
                    <el-table-column prop="shoeRId" label="工厂鞋型" min-width="120" show-overflow-tooltip />
                    <el-table-column prop="estimatedArrivalDate" label="预计到货日期" min-width="120" />
                </el-table>

                <el-pagination v-if="activeTab === tab.key" style="margin-top: 8px;"
                    @size-change="(v) => handleSizeChange(tab.key, v)"
                    @current-change="(v) => handlePageChange(tab.key, v)"
                    :current-page="state[tab.key].currentPage" :page-sizes="[10, 20, 30, 50, 100]"
                    :page-size="state[tab.key].pageSize" layout="total, sizes, prev, pager, next, jumper"
                    :total="state[tab.key].total" />
            </el-tab-pane>
        </el-tabs>
    </div>
</template>

<script>
import axios from 'axios'

const WAREHOUSE_TABS = [
    { key: 'fabric', label: '面料/里料/复合仓', materialTypes: ['面料', '里料', '复合'] },
    { key: 'sole', label: '底材仓', materialTypes: ['底材'] },
    { key: 'package', label: '包材仓', materialTypes: ['包材'] },
    { key: 'aux', label: '辅料及饰品仓', materialTypes: ['辅料', '饰品'] }
]

function makeDefaultFilter() {
    return { materialName: null, supplierName: null, onlyNeverOutbound: false }
}
function makeDefaultState() {
    return { tableData: [], total: 0, currentPage: 1, pageSize: 20 }
}

export default {
    name: 'UncompletedOutboundMaterialsView',
    data() {
        const filters = {}
        const state = {}
        WAREHOUSE_TABS.forEach(t => {
            filters[t.key] = makeDefaultFilter()
            state[t.key] = makeDefaultState()
        })
        return {
            activeTab: WAREHOUSE_TABS[0].key,
            warehouseTabs: WAREHOUSE_TABS,
            filters,
            state
        }
    },
    watch: {
        activeTab(newKey) {
            this.fetchData(newKey)
        }
    },
    mounted() {
        this.fetchData(this.activeTab)
    },
    methods: {
        rowClassName({ row }) {
            if (!row.everOutbound) return 'row-status-never'
            if (Number(row.currentAmount) > 0) return 'row-status-partial'
            return ''
        },
        statusTagType(row) {
            if (!row.everOutbound) return 'warning'
            if (Number(row.currentAmount) > 0) return 'info'
            return 'success'
        },
        reload(tabKey) {
            this.state[tabKey].currentPage = 1
            this.fetchData(tabKey)
        },
        async fetchData(tabKey) {
            const tab = WAREHOUSE_TABS.find(t => t.key === tabKey)
            if (!tab) return
            const f = this.filters[tabKey]
            const s = this.state[tabKey]
            try {
                const params = {
                    page: s.currentPage,
                    pageSize: s.pageSize,
                    materialTypes: tab.materialTypes.join(','),
                    materialName: f.materialName,
                    supplierName: f.supplierName,
                    onlyNeverOutbound: f.onlyNeverOutbound ? 1 : 0
                }
                const res = await axios.get(
                    `${this.$apiBaseUrl}/warehouse/getuncompletedoutboundmaterials`,
                    { params }
                )
                s.tableData = res.data.result || []
                s.total = res.data.total || 0
            } catch (e) {
                console.error(e)
            }
        },
        handleSizeChange(tabKey, val) {
            this.state[tabKey].pageSize = val
            this.fetchData(tabKey)
        },
        handlePageChange(tabKey, val) {
            this.state[tabKey].currentPage = val
            this.fetchData(tabKey)
        }
    }
}
</script>

<style scoped>
.uncompleted-outbound {
    display: flex;
    flex-direction: column;
    gap: 12px;
}

.header-card .header-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.header-card .title {
    font-size: 16px;
    font-weight: 600;
}

.header-card .hint {
    color: #909399;
    font-size: 13px;
}

.tabs {
    background: #fff;
}

.ml-2 {
    margin-left: 8px;
}

.status-legend {
    margin-top: 10px;
    display: flex;
    gap: 16px;
    color: #606266;
    font-size: 13px;
}

.legend-item {
    display: inline-flex;
    align-items: center;
    gap: 6px;
}

.legend-dot {
    display: inline-block;
    width: 12px;
    height: 12px;
    border-radius: 2px;
    border: 1px solid rgba(0, 0, 0, 0.08);
}

.legend-dot.status-never {
    background: #fdf6ec;
}

.legend-dot.status-partial {
    background: #ecf5ff;
}
</style>

<style>
.el-table .row-status-never td.el-table__cell {
    background-color: #fdf6ec !important;
}

.el-table .row-status-partial td.el-table__cell {
    background-color: #ecf5ff !important;
}
</style>
