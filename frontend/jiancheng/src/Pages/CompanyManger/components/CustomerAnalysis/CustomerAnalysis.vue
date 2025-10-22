<!-- CustomerAnalyticsSingle.vue -->
<template>
    <div class="page p-4 customer-analytics">
        <!-- ========== 筛选区（模式切换 + 不同下拉） ========== -->
        <el-card shadow="never" class="mb-3">
            <el-form :inline="true" :model="filters" @keyup.enter="loadAll">
                <el-form-item label="分析范围">
                    <el-radio-group v-model="filters.scope" @change="onScopeChange">
                        <el-radio-button label="name">客户名（聚合）</el-radio-button>
                        <el-radio-button label="brand">商标（单一）</el-radio-button>
                    </el-radio-group>
                </el-form-item>

                <!-- 主客户（根据 scope 切换控件） -->
                <el-form-item v-if="filters.scope === 'name'" label="主客户名">
                    <el-select
                        v-model="filters.primaryCustomerName"
                        filterable
                        clearable
                        placeholder="输入客户名搜索"
                        :remote="true"
                        :remote-method="remoteSearchNames"
                        :loading="searching"
                        style="min-width: 320px"
                    >
                        <el-option v-for="n in nameOptions" :key="n" :label="n" :value="n" />
                    </el-select>
                </el-form-item>

                <el-form-item v-else label="主商标（品牌）">
                    <el-select
                        v-model="filters.primaryCustomerId"
                        filterable
                        remote
                        clearable
                        placeholder="输入名称或ID搜索品牌"
                        :remote-method="remoteSearchBrands"
                        :loading="searching"
                        style="min-width: 380px"
                    >
                        <el-option-group v-for="g in brandGroups" :key="g.label" :label="g.label">
                            <el-option v-for="opt in g.options" :key="opt.value" :label="opt.label" :value="opt.value" />
                        </el-option-group>
                    </el-select>
                </el-form-item>

                <!-- 对比（根据 scope 切换控件） -->
                <el-form-item v-if="filters.scope === 'name'" label="对比客户名">
                    <el-select
                        v-model="filters.compareCustomerNames"
                        multiple
                        filterable
                        clearable
                        collapse-tags
                        placeholder="输入客户名搜索"
                        :remote="true"
                        :remote-method="remoteSearchNames"
                        :loading="searching"
                        style="min-width: 420px"
                    >
                        <el-option v-for="n in nameOptions" :key="n" :label="n" :value="n" />
                    </el-select>
                </el-form-item>

                <el-form-item v-else label="对比商标">
                    <el-select
                        v-model="filters.compareCustomerIds"
                        multiple
                        filterable
                        remote
                        clearable
                        collapse-tags
                        placeholder="输入名称或ID搜索品牌"
                        :remote-method="remoteSearchBrands"
                        :loading="searching"
                        style="min-width: 520px"
                    >
                        <el-option-group v-for="g in brandGroups" :key="g.label" :label="g.label">
                            <el-option v-for="opt in g.options" :key="opt.value" :label="opt.label" :value="opt.value" />
                        </el-option-group>
                    </el-select>
                </el-form-item>

                <el-form-item label="时间范围">
                    <el-date-picker v-model="filters.dateRange" type="daterange" start-placeholder="开始日期" end-placeholder="结束日期" unlink-panels value-format="YYYY-MM-DD" />
                </el-form-item>

                <el-form-item>
                    <el-button type="primary" :loading="loading.summary" @click="loadAll">查询</el-button>
                    <el-button @click="resetFilters">清空</el-button>
                    <el-button @click="exportAll">导出</el-button>
                </el-form-item>
            </el-form>
        </el-card>

        <!-- ========== KPI（分布 + 绩效） ========== -->
        <el-row :gutter="16" class="mb-3 kpi-row">
            <el-col :span="3" v-for="card in kpiCards" :key="card.key">
                <el-card shadow="never" class="kpi-card">
                    <div class="kpi-title">{{ card.title }}</div>
                    <div class="kpi-value">
                        <span v-if="card.isMoney">{{ formatMoney(kpisPrimary[card.key]) }}</span>
                        <span v-else-if="card.isPercent">{{ formatPercent(kpisPrimary[card.key]) }}</span>
                        <span v-else>{{ kpisPrimary[card.key] ?? '-' }}</span>
                    </div>
                </el-card>
            </el-col>
        </el-row>

        <!-- ========== 图表区 ========== -->
        <el-row :gutter="16" class="mb-3">
            <el-col :span="12">
                <el-card shadow="never" class="chart-card" header="鞋型单价分布（主 · 直方图）">
                    <div class="chart" ref="refUnitPriceHist"></div>
                </el-card>
            </el-col>
            <el-col :span="12">
                <el-card shadow="never" class="chart-card" header="鞋型单价分布对比（多 · 分箱折线）">
                    <div class="chart" ref="refUnitPriceCompare"></div>
                </el-card>
            </el-col>
        </el-row>

        <el-row :gutter="16" class="mb-3">
            <el-col :span="12">
                <el-card shadow="never" class="chart-card" header="设计师分布（主 · 次数）">
                    <div class="chart" ref="refDesignerBar"></div>
                </el-card>
            </el-col>
            <el-col :span="12">
                <el-card shadow="never" class="chart-card" header="最常选鞋型 Top N（主 · 次数）">
                    <div class="chart" ref="refTopShoeTypes"></div>
                </el-card>
            </el-col>
        </el-row>
        <!-- 生产耗时分布 + 供应商 Top（如果你后面还有供应商对比，这里只放耗时分布也行） -->
        <el-row :gutter="16" class="mb-3">
            <el-col :span="12">
                <el-card shadow="never" class="chart-card" header="生产耗时分布（客户维度 · 箱线图）">
                    <div class="chart" ref="refLeadtimeBox"></div>
                </el-card>
            </el-col>
            <!-- 右侧你可以保留空白，或放别的卡片；若你已经在后面有“供应商使用次数 Top N”，这里也可以只保留左半列 -->
            <!--
  <el-col :span="12">
    <el-card shadow="never" class="chart-card" header="（可选）其他图表">
      <div class="chart"></div>
    </el-card>
  </el-col>
  -->
        </el-row>

        <!-- ====== 供应商：把“材料类型筛选”放在卡片标题右侧（两个图共用） ====== -->
        <el-row :gutter="16" class="mb-3">
            <el-col :span="12">
                <el-card shadow="never" class="chart-card">
                    <template #header>
                        <div class="card-head">
                            <span class="card-title">供应商使用次数（主 Top N）</span>
                            <div class="head-actions">
                                <el-radio-group v-model="activeMaterialCat" size="small" @change="applySupplierUsageByCat">
                                    <el-radio-button v-for="cat in materialCatOptions" :key="cat" :label="cat" />
                                </el-radio-group>
                            </div>
                        </div>
                    </template>
                    <div class="chart" ref="refSupplierUsageTop"></div>
                </el-card>
            </el-col>

            <el-col :span="12">
                <el-card shadow="never" class="chart-card">
                    <template #header>
                        <div class="card-head">
                            <span class="card-title">供应商使用次数对比（不同客户）</span>
                            <div class="head-actions">
                                <el-radio-group v-model="activeMaterialCat" size="small" @change="applySupplierUsageByCat">
                                    <el-radio-button v-for="cat in materialCatOptions" :key="cat" :label="cat" />
                                </el-radio-group>
                            </div>
                        </div>
                    </template>
                    <div class="chart" ref="refSupplierUsageCompare"></div>
                </el-card>
            </el-col>
        </el-row>

        <!-- ========== 明细 Tabs ========== -->
        <el-tabs v-model="activeTab" type="border-card">
            <el-tab-pane label="主客户订单" name="orders">
                <vxe-table :data="table.orders.rows" height="520" border show-overflow>
                    <vxe-column field="order_rid" title="订单号" width="150" />
                    <vxe-column field="shoe_type" title="鞋型" width="180" />
                    <vxe-column field="designer" title="设计师" width="140" />
                    <vxe-column field="unit_price" title="单价" :formatter="moneyFmt" />
                    <vxe-column field="lead_days" title="生产耗时(天)" width="140" />
                    <vxe-column field="status_name" title="状态" width="120" />
                    <vxe-column field="start_end" title="起止" width="220" />
                </vxe-table>
                <div class="table-footer">
                    <el-pagination
                        background
                        layout="prev, pager, next, jumper"
                        :total="table.orders.total"
                        :page-size="table.orders.size"
                        v-model:current-page="table.orders.page"
                        @current-change="loadOrders"
                    />
                </div>
            </el-tab-pane>

            <el-tab-pane label="设计师分布明细" name="designers">
                <vxe-table :data="table.designers.rows" height="520" border show-overflow>
                    <vxe-column field="designer" title="设计师" width="200" />
                    <vxe-column field="count" title="出现次数" width="140" />
                    <vxe-column field="ratio" title="占比" :formatter="percentFmt" />
                </vxe-table>
                <div class="table-footer">
                    <el-pagination
                        background
                        layout="prev, pager, next, jumper"
                        :total="table.designers.total"
                        :page-size="table.designers.size"
                        v-model:current-page="table.designers.page"
                        @current-change="loadDesignersTable"
                    />
                </div>
            </el-tab-pane>

            <el-tab-pane label="热门鞋型明细" name="shoes">
                <vxe-table :data="table.shoeTypes.rows" height="520" border show-overflow>
                    <vxe-column field="shoe_type" title="鞋型" width="220" />
                    <vxe-column field="count" title="出现次数" width="140" />
                    <vxe-column field="avg_unit_price" title="平均单价" :formatter="moneyFmt" />
                </vxe-table>
                <div class="table-footer">
                    <el-pagination
                        background
                        layout="prev, pager, next, jumper"
                        :total="table.shoeTypes.total"
                        :page-size="table.shoeTypes.size"
                        v-model:current-page="table.shoeTypes.page"
                        @current-change="loadShoeTypesTable"
                    />
                </div>
            </el-tab-pane>

            <el-tab-pane label="供应商使用次数" name="suppliers">
                <vxe-table :data="table.suppliers.rows" height="520" border show-overflow>
                    <vxe-column field="supplier_name" title="供应商" width="260" />
                    <vxe-column field="usage_count" title="使用次数" width="140" />
                    <vxe-column field="usage_ratio" title="次数占比" :formatter="percentFmt" width="140" />
                    <vxe-column field="category_top" title="主要品类" width="160" />
                </vxe-table>
                <div class="table-footer">
                    <el-pagination
                        background
                        layout="prev, pager, next, jumper"
                        :total="table.suppliers.total"
                        :page-size="table.suppliers.size"
                        v-model:current-page="table.suppliers.page"
                        @current-change="loadSuppliersTable"
                    />
                </div>
            </el-tab-pane>

            <el-tab-pane label="客户对比（分布摘要）" name="compare">
                <vxe-table :data="table.compare.rows" height="520" border show-overflow>
                    <vxe-column field="customer" title="客户/商标" width="240" />
                    <vxe-column field="orders" title="订单数" width="120" />
                    <vxe-column field="unit_price_p50" title="单价P50" :formatter="moneyFmt" />
                    <vxe-column field="unit_price_p90" title="单价P90" :formatter="moneyFmt" />
                    <vxe-column field="lead_days_p50" title="耗时P50(天)" />
                    <vxe-column field="lead_days_p90" title="耗时P90(天)" />
                    <vxe-column field="top_designer" title="Top 设计师" />
                    <vxe-column field="top_supplier" title="Top 供应商(次数)" />
                </vxe-table>
                <div class="table-footer">
                    <el-pagination
                        background
                        layout="prev, pager, next, jumper"
                        :total="table.compare.total"
                        :page-size="table.compare.size"
                        v-model:current-page="table.compare.page"
                        @current-change="loadCompareTable"
                    />
                </div>
            </el-tab-pane>
        </el-tabs>
    </div>
</template>

<script setup lang="ts">
import { onMounted, onBeforeUnmount, ref, reactive, nextTick, getCurrentInstance } from 'vue'
import axios from 'axios'
import dayjs from 'dayjs'
import * as echarts from 'echarts'

const { $apiBaseUrl } = getCurrentInstance().appContext.config.globalProperties

/** ========== 配置 ========== */
const MOCK = false

/** ========== 类型 ========== */
type CustomerDTO = { customerId: number; customerName: string; customerBrand?: string }
type GroupedOption = { label: string; options: Array<{ label: string; value: number }> }

/** ========== 下拉（客户名 & 按客户名分组的品牌） ========== */
const nameOptions = ref<string[]>([])
const brandGroups = ref<GroupedOption[]>([])
const allCustomers = ref<CustomerDTO[]>([])
const searching = ref(false)

/** ========== 过滤器 & 加载状态 ========== */
const filters = reactive({
    scope: 'name' as 'name' | 'brand',
    // name 模式
    primaryCustomerName: '' as string | '',
    compareCustomerNames: [] as string[],
    // brand 模式
    primaryCustomerId: null as number | null,
    compareCustomerIds: [] as number[],
    // 共有
    dateRange: [dayjs().startOf('year').format('YYYY-MM-DD'), dayjs().format('YYYY-MM-DD')] as string[] | null,
    status: '' as string | ''
})
const loading = reactive({ summary: false })

/** ========== KPI ========== */
const kpisPrimary = reactive<any>({
    order_count: 0,
    median_unit_price: 0,
    p90_unit_price: 0,
    median_lead_days: 0,
    on_time_rate: 0,
    gmv: 0,
    total_cost: 0,
    gross_profit: 0,
    gross_margin: 0
})
const kpiCards = [
    { key: 'order_count', title: '订单数' },
    { key: 'median_unit_price', title: '单价中位数', isMoney: true },
    { key: 'p90_unit_price', title: '单价P90', isMoney: true },
    { key: 'median_lead_days', title: '订单耗时中位数(天)' },
    { key: 'on_time_rate', title: '按期率', isPercent: true },
    { key: 'gmv', title: '销售金额', isMoney: true },
    { key: 'total_cost', title: '总成本', isMoney: true },
    { key: 'gross_profit', title: '毛利', isMoney: true },
    { key: 'gross_margin', title: '毛利率', isPercent: true }
]

/** ========== 图表 refs ========== */
const refUnitPriceHist = ref<HTMLDivElement>()
const refUnitPriceCompare = ref<HTMLDivElement>()
const refDesignerBar = ref<HTMLDivElement>()
const refTopShoeTypes = ref<HTMLDivElement>()
const refLeadtimeBox = ref<HTMLDivElement>()
const refSupplierUsageTop = ref<HTMLDivElement>()
const refSupplierUsageCompare = ref<HTMLDivElement>()
let chartUnitPriceHist: echarts.ECharts | null = null
let chartUnitPriceCompare: echarts.ECharts | null = null
let chartDesignerBar: echarts.ECharts | null = null
let chartTopShoeTypes: echarts.ECharts | null = null
let chartLeadtimeBox: echarts.ECharts | null = null
let chartSupplierUsageTop: echarts.ECharts | null = null
let chartSupplierUsageCompare: echarts.ECharts | null = null

/** ========== 工具函数（格式化） ========== */
const formatMoney = (v: any) => {
    const n = Number(v ?? 0)
    if (Number.isNaN(n)) return '-'
    return n.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}
const formatPercent = (v: any) => {
    const n = Number(v ?? 0)
    if (Number.isNaN(n)) return '-'
    return (n * 100).toFixed(1) + '%'
}
const moneyFmt = ({ cellValue }: any) => formatMoney(cellValue)
const percentFmt = ({ cellValue }: any) => formatPercent(cellValue)

/** ========== 统计/主题 ========== */
function getBins(data: number[], binCount = 12) {
    if (!data.length) return { edges: [], counts: [] }
    const min = Math.min(...data),
        max = Math.max(...data)
    if (min === max) return { edges: [min, max], counts: [data.length] }
    const step = (max - min) / binCount
    const edges = Array.from({ length: binCount + 1 }, (_, i) => min + i * step)
    const counts = Array(binCount).fill(0)
    data.forEach((v) => {
        let idx = Math.floor((v - min) / step)
        if (idx >= binCount) idx = binCount - 1
        if (idx < 0) idx = 0
        counts[idx]++
    })
    return { edges, counts }
}
const PALETTE = ['#5B8FF9', '#61DDAA', '#65789B', '#F6BD16', '#7262FD', '#78D3F8', '#FF99C3', '#FB8D34', '#9AE65C', '#F690BA']
const THEME_KEY = '__ECHARTS_THEME_CLEAN_REGISTERED__'
const g: any = typeof window !== 'undefined' ? window : globalThis
if (!g[THEME_KEY]) {
    echarts.registerTheme('clean', {
        color: PALETTE,
        textStyle: { fontFamily: 'Inter, system-ui, -apple-system, Segoe UI, Roboto, Arial' },
        grid: { left: 40, right: 24, top: 40, bottom: 40, containLabel: true },
        tooltip: { backgroundColor: '#1f2937', borderWidth: 0, textStyle: { color: '#fff' } },
        legend: { top: 8, itemWidth: 12, itemHeight: 12 },
        categoryAxis: { axisLine: { lineStyle: { color: '#9CA3AF' } }, axisLabel: { color: '#374151' }, axisTick: { show: false }, splitLine: { show: false } },
        valueAxis: { axisLine: { show: false }, axisLabel: { color: '#4B5563' }, splitLine: { show: true, lineStyle: { color: '#E5E7EB' } } }
    })
    g[THEME_KEY] = true
}
function initChart(refEl: HTMLDivElement | undefined | null, holder: echarts.ECharts | null) {
    if (!refEl) return null
    if (holder) return holder
    return echarts.init(refEl, 'clean', { renderer: 'canvas' })
}
function linearGrad(color: string, a = 1, b = 0.15) {
    return new (echarts as any).graphic.LinearGradient(0, 0, 0, 1, [
        { offset: 0, color, opacity: a },
        { offset: 1, color, opacity: b }
    ])
}
const TB = { feature: { saveAsImage: {}, dataZoom: { yAxisIndex: 'none' } }, right: 10 }
function addZoomIfLong(labels: string[]) {
    return labels.length > 12 ? [{ type: 'slider', height: 16, bottom: 0 }, { type: 'inside' }] : []
}
const EMPH_BAR = { focus: 'self', itemStyle: { shadowBlur: 8, shadowColor: 'rgba(0,0,0,.15)' } }

/** ========== 图表渲染（略：除供应商外与原版一致） ========== */
function renderUnitPriceHist(unitPrices: number[]) {
    const { edges, counts } = getBins(unitPrices, 12)
    const labels = counts.map((_, i) => `${edges[i].toFixed(0)}~${edges[i + 1]?.toFixed(0)}`)
    chartUnitPriceHist = initChart(refUnitPriceHist.value, chartUnitPriceHist)
    chartUnitPriceHist?.setOption({
        toolbox: TB,
        tooltip: { trigger: 'axis' },
        xAxis: { type: 'category', data: labels, axisLabel: { interval: 0, rotate: labels.length > 10 ? 30 : 0 } },
        yAxis: { type: 'value', name: '订单数' },
        dataZoom: addZoomIfLong(labels),
        series: [{ type: 'bar', name: '频次', data: counts, barWidth: '60%', itemStyle: { borderRadius: [6, 6, 0, 0], color: linearGrad(PALETTE[0]) }, emphasis: EMPH_BAR }]
    })
}
function renderUnitPriceCompare(series: Array<{ customer: string; unit_prices: number[] }>) {
    const allValues = series.flatMap((s) => s.unit_prices)
    chartUnitPriceCompare = initChart(refUnitPriceCompare.value, chartUnitPriceCompare)
    if (!allValues.length) {
        chartUnitPriceCompare?.clear()
        return
    }
    const { edges } = getBins(allValues, 12)
    const labels = Array.from({ length: edges.length - 1 }, (_, i) => `${edges[i].toFixed(0)}~${edges[i + 1].toFixed(0)}`)
    const makeCounts = (data: number[]) => {
        const counts = Array(edges.length - 1).fill(0)
        data.forEach((v) => {
            let idx = edges.findIndex((e, i) => v >= edges[i] && v < edges[i + 1])
            if (idx === -1) idx = edges.length - 2
            counts[idx]++
        })
        return counts
    }
    chartUnitPriceCompare.setOption({
        toolbox: TB,
        legend: { type: 'scroll', top: 6 },
        tooltip: { trigger: 'axis' },
        xAxis: { type: 'category', data: labels, axisLabel: { interval: 0, rotate: labels.length > 10 ? 30 : 0 } },
        yAxis: { type: 'value', name: '订单数' },
        dataZoom: addZoomIfLong(labels),
        series: series.map((s, idx) => ({
            name: s.customer,
            type: 'line',
            smooth: true,
            showSymbol: false,
            lineStyle: { width: 2 },
            areaStyle: { opacity: 0.15, color: linearGrad(PALETTE[idx % PALETTE.length], 0.6, 0.05) },
            emphasis: { focus: 'series' },
            data: makeCounts(s.unit_prices)
        }))
    })
}
function renderDesignerBar(rows: Array<{ designer: string; count: number }>) {
    const cats = rows.map((r) => r.designer || '（未填写）')
    const vals = rows.map((r) => r.count ?? 0)
    chartDesignerBar = initChart(refDesignerBar.value, chartDesignerBar)
    if (!cats.length) {
        chartDesignerBar?.clear()
        return
    }
    chartDesignerBar.setOption({
        toolbox: TB,
        tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
        grid: { top: 48, left: 40, right: 20, bottom: 46, containLabel: true },
        xAxis: { type: 'category', data: cats, axisLabel: { interval: 0, rotate: cats.length > 12 ? 30 : 0 } },
        yAxis: { type: 'value', name: '次数', splitNumber: 5 },
        dataZoom: addZoomIfLong(cats),
        series: [
            {
                type: 'bar',
                barMaxWidth: 40,
                data: vals.map((v, i) => ({ value: v, itemStyle: { color: linearGrad(PALETTE[i % PALETTE.length]) } })),
                itemStyle: { borderRadius: [10, 10, 0, 0] },
                label: { show: true, position: 'top', color: '#374151', fontWeight: 600 },
                emphasis: EMPH_BAR
            }
        ]
    })
}
function renderTopShoeTypes(rows: Array<{ shoe_type: string; count: number }>) {
    const sorted = [...rows].sort((a, b) => (b.count ?? 0) - (a.count ?? 0))
    const cats = sorted.map((r) => r.shoe_type || '-')
    const vals = sorted.map((r) => r.count ?? 0)
    chartTopShoeTypes = initChart(refTopShoeTypes.value, chartTopShoeTypes)
    if (!cats.length) {
        chartTopShoeTypes?.clear()
        return
    }
    chartTopShoeTypes.setOption({
        toolbox: TB,
        tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
        grid: { top: 50, left: 50, right: 30, bottom: 60, containLabel: true },
        xAxis: { type: 'category', data: cats, axisLabel: { interval: 0, rotate: cats.length > 10 ? 30 : 0 } },
        yAxis: { type: 'value', name: '次数', splitLine: { lineStyle: { color: '#eee' } } },
        dataZoom: addZoomIfLong(cats),
        series: [
            {
                name: '鞋型使用次数',
                type: 'bar',
                barMaxWidth: 40,
                data: vals.map((v, i) => ({
                    value: v,
                    itemStyle: {
                        color: new (echarts as any).graphic.LinearGradient(0, 0, 0, 1, [
                            { offset: 0, color: PALETTE[(i + 2) % PALETTE.length] },
                            { offset: 1, color: 'rgba(255,255,255,0.3)' }
                        ]),
                        borderRadius: [8, 8, 0, 0]
                    }
                })),
                label: { show: true, position: 'top', color: '#333', fontWeight: 600, formatter: '{c}' },
                emphasis: { focus: 'self', itemStyle: { shadowBlur: 10, shadowColor: 'rgba(0,0,0,0.2)' } }
            }
        ]
    })
}
function renderLeadtimeHistogramCompare(seriesByCustomer: Array<{ customer: string; lead_days: number[] }>, binCount = 12) {
    chartLeadtimeBox = initChart(refLeadtimeBox.value, chartLeadtimeBox)
    if (!seriesByCustomer?.length) {
        chartLeadtimeBox?.clear()
        return
    }
    const all = seriesByCustomer.flatMap((s) => s.lead_days || []).filter(Number.isFinite)
    if (!all.length) {
        chartLeadtimeBox?.clear()
        return
    }
    const minV = Math.min(...all),
        maxV = Math.max(...all)
    const step = Math.max(1, (maxV - minV) / binCount)
    const edges = Array.from({ length: binCount + 1 }, (_, i) => minV + i * step)
    const labels = Array.from({ length: binCount }, (_, i) => `${Math.round(edges[i])}~${Math.round(edges[i + 1])}`)
    const makeCounts = (arr: number[]) => {
        const counts = Array(binCount).fill(0)
        for (const v of arr) {
            let idx = Math.floor((v - minV) / step)
            if (idx < 0) idx = 0
            if (idx >= binCount) idx = binCount - 1
            counts[idx]++
        }
        return counts
    }
    const series = seriesByCustomer.map((s, i) => ({
        name: s.customer || `客户${i + 1}`,
        type: 'bar',
        barGap: 0,
        barCategoryGap: '28%',
        itemStyle: {
            borderRadius: [6, 6, 0, 0],
            color: new (echarts as any).graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color: PALETTE[i % PALETTE.length] },
                { offset: 1, color: 'rgba(255,255,255,0.25)' }
            ])
        },
        emphasis: { focus: 'series' },
        data: makeCounts(s.lead_days || [])
    }))
    chartLeadtimeBox.setOption(
        {
            toolbox: TB,
            legend: { type: 'scroll', top: 6 },
            tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
            grid: { top: 56, left: 48, right: 28, bottom: 60, containLabel: true },
            xAxis: { type: 'category', data: labels, axisLabel: { interval: 0, rotate: labels.length > 12 ? 30 : 0 } },
            yAxis: { type: 'value', name: '订单数' },
            dataZoom: addZoomIfLong(labels),
            series
        },
        true
    )
}

/** ===== 供应商次数（数据缓存 + 渲染） ===== */
const CAT_NAME_MAP: Record<string, string> = { S: '面料', I: '里料', A: '辅料', O: '大底', M: '中底' }
const MATERIAL_CAT_LABELS = ['面料', '里料', '辅料', '大底', '中底'] as const
type MaterialCat = (typeof MATERIAL_CAT_LABELS)[number]
const materialCatOptions = ref<MaterialCat[]>([...MATERIAL_CAT_LABELS])
const activeMaterialCat = ref<MaterialCat>('面料')
let supplierUsageCache: any = null // 缓存上次接口返回

function renderSupplierUsageTop(rows: Array<{ name: string; usage_count: number }>) {
    const cats = rows.map((r) => r.name || '-')
    const vals = rows.map((r) => r.usage_count ?? 0)
    chartSupplierUsageTop = initChart(refSupplierUsageTop.value, chartSupplierUsageTop)
    if (!cats.length) {
        chartSupplierUsageTop?.clear()
        return
    }
    chartSupplierUsageTop.setOption({
        toolbox: TB,
        tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
        grid: { top: 48, left: 40, right: 20, bottom: 46, containLabel: true },
        xAxis: { type: 'category', data: cats, axisLabel: { interval: 0, rotate: cats.length > 12 ? 30 : 0 } },
        yAxis: { type: 'value', name: '次数', splitNumber: 5 },
        dataZoom: addZoomIfLong(cats),
        series: [
            {
                type: 'bar',
                barMaxWidth: 38,
                data: vals.map((v, i) => ({ value: v, itemStyle: { color: linearGrad(PALETTE[(i + 4) % PALETTE.length]) } })),
                itemStyle: { borderRadius: [10, 10, 0, 0] },
                label: { show: true, position: 'top', color: '#374151' },
                emphasis: EMPH_BAR
            }
        ]
    })
}
function renderSupplierUsageCompare(rows: Array<{ supplier: string; counts: Record<string, number> }>) {
    const suppliers = rows.map((r) => r.supplier || '-')
    const customers = Array.from(new Set(rows.flatMap((r) => Object.keys(r.counts || {}))))
    chartSupplierUsageCompare = initChart(refSupplierUsageCompare.value, chartSupplierUsageCompare)
    if (!suppliers.length) {
        chartSupplierUsageCompare?.clear()
        return
    }
    chartSupplierUsageCompare.setOption({
        toolbox: TB,
        legend: { type: 'scroll', top: 6 },
        tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
        grid: { top: 56, left: 40, right: 20, bottom: 52, containLabel: true },
        xAxis: { type: 'category', data: suppliers, axisLabel: { interval: 0, rotate: suppliers.length > 10 ? 30 : 0 } },
        yAxis: { type: 'value', name: '次数', splitNumber: 5 },
        dataZoom: addZoomIfLong(suppliers),
        series: customers.map((c, idx) => ({
            name: c,
            type: 'bar',
            barMaxWidth: 28,
            itemStyle: { borderRadius: [8, 8, 0, 0], color: linearGrad(PALETTE[idx % PALETTE.length]) },
            emphasis: EMPH_BAR,
            data: suppliers.map((s) => rows.find((r) => r.supplier === s)?.counts?.[c] ?? 0)
        }))
    })
}

/** 把缓存数据套用到选中类目并渲染 + 同步表格 */
function applySupplierUsageByCat() {
    if (!supplierUsageCache) return
    const mapCat = (obj: any) => {
        const res: Record<string, any[]> = {}
        const src = obj || {}
        Object.keys(src).forEach((k) => {
            res[k] = src[k] || []
        })
        return res
    }
    const byCatPrimary = mapCat(supplierUsageCache.primary?.by_category)
    const byCatCompare = mapCat(supplierUsageCache.compare?.by_category)
    const cat = activeMaterialCat.value
    const topList = (byCatPrimary[cat] || []).map((i: any) => ({
        name: i.supplier_name ?? i.supplier ?? '-',
        usage_count: Number(i.usage_count ?? i.count ?? 0)
    }))
    const compareList = (byCatCompare[cat] || []).map((row: any) => ({
        supplier: row.supplier ?? row.supplier_name ?? '-',
        counts: row.counts || {}
    }))
    renderSupplierUsageTop(topList)
    renderSupplierUsageCompare(compareList)
    const totalUsage = topList.reduce((s, x) => s + (x.usage_count || 0), 0) || 1
    table.suppliers.rows = topList.map((s: any) => ({
        supplier_name: s.name,
        usage_count: s.usage_count,
        usage_ratio: s.usage_count / totalUsage,
        category_top: cat
    }))
}

/** ========== 下拉：加载与远程搜索 ========== */
function buildBrandGroups(list: CustomerDTO[]): GroupedOption[] {
    const map = new Map<string, Array<{ label: string; value: number }>>()
    for (const c of list) {
        const group = c.customerName || '未命名'
        const label = c.customerBrand ? `${c.customerBrand} · ${c.customerName}（ID:${c.customerId}）` : `${c.customerName}（ID:${c.customerId}）`
        const arr = map.get(group) || []
        arr.push({ label, value: c.customerId })
        map.set(group, arr)
    }
    return Array.from(map.entries()).map(([label, options]) => ({ label, options }))
}
function distinctNames(list: CustomerDTO[]) {
    return Array.from(new Set(list.map((i) => i.customerName).filter(Boolean))).sort()
}
async function initCustomers() {
    const { data } = await axios.get<CustomerDTO[]>(`${$apiBaseUrl}/customer/getcustomerdetailsforanalysis`)
    allCustomers.value = Array.isArray(data) ? data : []
    nameOptions.value = distinctNames(allCustomers.value)
    brandGroups.value = buildBrandGroups(allCustomers.value)
    // 默认主对象
    if (filters.scope === 'name') {
        if (!filters.primaryCustomerName && nameOptions.value.length) filters.primaryCustomerName = nameOptions.value[0]
    } else {
        const first = brandGroups.value[0]?.options?.[0]
        if (!filters.primaryCustomerId && first) filters.primaryCustomerId = first.value
    }
}
async function remoteSearchNames(query: string) {
    searching.value = true
    try {
        const { data } = await axios.get<CustomerDTO[]>(`${$apiBaseUrl}/customer/getcustomerdetailsforanalysis`, { params: query ? { customerName: query } : {} })
        nameOptions.value = distinctNames(Array.isArray(data) ? data : [])
    } finally {
        searching.value = false
    }
}
async function remoteSearchBrands(query: string) {
    searching.value = true
    try {
        const params: any = {}
        if (query?.trim()) {
            if (/^\d+$/.test(query.trim())) params.customerId = Number(query.trim())
            else params.customerName = query.trim()
        }
        const { data } = await axios.get<CustomerDTO[]>(`${$apiBaseUrl}/customer/getcustomerdetailsforanalysis`, { params })
        brandGroups.value = buildBrandGroups(Array.isArray(data) ? data : [])
    } finally {
        searching.value = false
    }
}
function onScopeChange() {
    if (filters.scope === 'name') {
        filters.primaryCustomerId = null
        filters.compareCustomerIds = []
        if (!filters.primaryCustomerName && nameOptions.value.length) filters.primaryCustomerName = nameOptions.value[0]
    } else {
        filters.primaryCustomerName = ''
        filters.compareCustomerNames = []
        const first = brandGroups.value[0]?.options?.[0]
        if (!filters.primaryCustomerId && first) filters.primaryCustomerId = first.value
    }
}

/** ========== 业务 API 调用（参数对齐后端） ========== */
function baseRange() {
    const [from, to] = filters.dateRange || [null, null]
    return { date_from: from, date_to: to, status: filters.status || '' }
}
async function fetchUnitPriceGraph() {
    const params: any = { scope: filters.scope, ...baseRange() }
    if (filters.scope === 'name') {
        params.customerName = filters.primaryCustomerName || ''
        if (filters.compareCustomerNames?.length) params['compareCustomerNames[]'] = filters.compareCustomerNames
    } else {
        params.customerId = filters.primaryCustomerId
        if (filters.compareCustomerIds?.length) params['compareCustomerIds[]'] = filters.compareCustomerIds
    }
    const { data } = await axios.get(`${$apiBaseUrl}/customeranalysis/unitpricegraph`, { params })
    return data
}
async function fetchKpis() {
    const [from, to] = filters.dateRange || [null, null]
    const params: any = { scope: filters.scope, date_from: from, date_to: to, status: filters.status || '' }
    if (filters.scope === 'name') params.customerName = filters.primaryCustomerName
    else params.customerId = filters.primaryCustomerId
    const { data } = await axios.get(`${$apiBaseUrl}/customeranalysis/kpis`, { params })
    Object.assign(kpisPrimary, data?.primary?.kpis || {})
}
async function fetchDesignerDistribution() {
    const [from, to] = filters.dateRange || [null, null]
    const params: any = { scope: filters.scope, date_from: from, date_to: to, status: filters.status || '', top_n: 20 }
    if (filters.scope === 'name') params.customerName = filters.primaryCustomerName
    else params.customerId = filters.primaryCustomerId
    const { data } = await axios.get(`${$apiBaseUrl}/customeranalysis/designerdistribution`, { params })
    renderDesignerBar(data?.primary?.designers || [])
}
async function fetchTopShoeTypes() {
    const [from, to] = filters.dateRange || [null, null]
    const params: any = { scope: filters.scope || (filters.primaryCustomerName ? 'name' : 'brand'), date_from: from, date_to: to, status: filters.status || '', top_n: 20 }
    if (params.scope === 'name') params.customerName = filters.primaryCustomerName
    else params.customerId = filters.primaryCustomerId
    if (filters.compareCustomerIds?.length) params['compareCustomerIds[]'] = filters.compareCustomerIds
    const { data } = await axios.get(`${$apiBaseUrl}/customeranalysis/topshoetypes`, { params })
    return data
}
async function fetchLeadtimeDistribution() {
    const [from, to] = filters.dateRange || [null, null]
    const params: any = { scope: filters.scope || (filters.primaryCustomerName ? 'name' : 'brand'), date_from: from, date_to: to, status: filters.status || '' }
    if (params.scope === 'name') params.customerName = filters.primaryCustomerName
    else params.customerId = filters.primaryCustomerId
    if (filters.compareCustomerIds?.length) params['compareCustomerIds[]'] = filters.compareCustomerIds
    const { data } = await axios.get(`${$apiBaseUrl}/customeranalysis/leadtimedistribution`, { params })
    const series = [{ customer: data.primary.customer, lead_days: data.primary.lead_days }, ...(data.compare || [])]
    renderLeadtimeHistogramCompare(series)
}

/** 新：供应商使用次数（支持 name/brand 两种 scope；本地缓存 + 应用） */
async function fetchSupplierUsage() {
    const [from, to] = filters.dateRange || [null, null]
    const params: any = { scope: filters.scope, date_from: from || undefined, date_to: to || undefined, status: filters.status || undefined }
    if (filters.scope === 'name') {
        params.customerName = filters.primaryCustomerName || undefined
        if (filters.compareCustomerNames?.length) params['compareCustomerNames[]'] = filters.compareCustomerNames
    } else {
        params.customerId = filters.primaryCustomerId || undefined
        if (filters.compareCustomerIds?.length) params['compareCustomerIds[]'] = filters.compareCustomerIds
    }
    const { data } = await axios.get(`${$apiBaseUrl}/customeranalysis/supplierusage`, { params })
    // 统一“可选材料类目”
    const availableCats = Object.keys(data?.primary?.by_category || {})
    materialCatOptions.value = availableCats.length ? (availableCats.filter((c) => MATERIAL_CAT_LABELS.includes(c as any)) as MaterialCat[]) : ([] as MaterialCat[])
    if (!materialCatOptions.value.length && availableCats.length) {
        materialCatOptions.value = [availableCats[0] as MaterialCat]
    }
    if (!materialCatOptions.value.includes(activeMaterialCat.value) && materialCatOptions.value.length) {
        activeMaterialCat.value = materialCatOptions.value[0]
    }
    supplierUsageCache = data
    applySupplierUsageByCat()
    return data
}

/** ========== 页面加载 ========== */
async function fetchSummary() {
    loading.summary = true
    try {
        if (MOCK) return
        const up = await fetchUnitPriceGraph()
        await fetchKpis()
        const designerData = await fetchDesignerDistribution()
        const shoeTypeData = await fetchTopShoeTypes()
        await fetchLeadtimeDistribution()
        await fetchSupplierUsage()
        await nextTick()
        // 渲染单价相关
        chartUnitPriceHist || (chartUnitPriceHist = initChart(refUnitPriceHist.value, null))
        renderUnitPriceHist(up?.primary?.unit_prices || [])
        renderUnitPriceCompare(Array.isArray(up?.compare?.unit_prices) ? up.compare.unit_prices : [])
        // 其他图
        if (designerData) renderDesignerBar(designerData?.primary?.designers || [])
        if (shoeTypeData) renderTopShoeTypes(shoeTypeData?.primary?.shoes || [])
    } finally {
        loading.summary = false
    }
}

/** ===== 表格容器 ===== */
const activeTab = ref('orders')


/** ===== 交互 ===== */
async function loadAll() {
    if (filters.scope === 'name' && !filters.primaryCustomerName) return
    if (filters.scope === 'brand' && !filters.primaryCustomerId) return
    await fetchSummary()
      table.orders.page = table.designers.page = table.shoeTypes.page = table.suppliers.page = table.compare.page = 1
  if (activeTab.value === 'orders')    await loadOrders()
  if (activeTab.value === 'designers') await loadDesignersTable()
  if (activeTab.value === 'shoes')     await loadShoeTypesTable()
  if (activeTab.value === 'suppliers') await loadSuppliersTable()
  if (activeTab.value === 'compare')   await loadCompareTable()
}
import { watch } from 'vue'

// 1) 表格容器：加上分页字段
const table = reactive({
  orders:    { rows: [] as any[], page: 1, size: 20, total: 0 },
  designers: { rows: [] as any[], page: 1, size: 20, total: 0 },
  shoeTypes: { rows: [] as any[], page: 1, size: 20, total: 0 },
  suppliers: { rows: [] as any[], page: 1, size: 20, total: 0 },
  compare:   { rows: [] as any[], page: 1, size: 20, total: 0 },
})

function scopeParams() {
  const params: any = { scope: filters.scope, ...baseRange() }
  if (filters.scope === 'name') {
    params.customerName = filters.primaryCustomerName || ''
    if (filters.compareCustomerNames?.length) params['compareCustomerNames[]'] = filters.compareCustomerNames
  } else {
    params.customerId = filters.primaryCustomerId
    if (filters.compareCustomerIds?.length) params['compareCustomerIds[]'] = filters.compareCustomerIds
  }
  return params
}

// 2) 各表加载函数（服务端分页）
async function loadOrders() {
  const params: any = { ...scopeParams(), page: table.orders.page, size: table.orders.size }
  const { data } = await axios.get(`${$apiBaseUrl}/customeranalysis/orders`, { params })
  table.orders.rows  = data?.rows || []
  table.orders.total = data?.total || 0
}

async function loadDesignersTable() {
  const params: any = { ...scopeParams(), page: table.designers.page, size: table.designers.size }
  const { data } = await axios.get(`${$apiBaseUrl}/customeranalysis/designers-table`, { params })
  table.designers.rows  = data?.rows || []
  table.designers.total = data?.total || 0
}

async function loadShoeTypesTable() {
  const params: any = { ...scopeParams(), page: table.shoeTypes.page, size: table.shoeTypes.size }
  const { data } = await axios.get(`${$apiBaseUrl}/customeranalysis/shoetypes-table`, { params })
  table.shoeTypes.rows  = data?.rows || []
  table.shoeTypes.total = data?.total || 0
}

async function loadSuppliersTable() {
  // 供应商表需要材料类别（与你图表一致）
  const params: any = { ...scopeParams(), page: table.suppliers.page, size: table.suppliers.size, material_cat: activeMaterialCat.value }
  const { data } = await axios.get(`${$apiBaseUrl}/customeranalysis/supplierusage-table`, { params })
  table.suppliers.rows  = data?.rows || []
  table.suppliers.total = data?.total || 0
}

async function loadCompareTable() {
  const params: any = { ...scopeParams(), page: table.compare.page, size: table.compare.size }
  const { data } = await axios.get(`${$apiBaseUrl}/customeranalysis/compare-summary`, { params })
  table.compare.rows  = data?.rows || []
  table.compare.total = data?.total || 0
}

// 3) Tab 切换懒加载
watch(() => activeTab.value, async (name) => {
  await nextTick()
  if (name === 'orders')    return loadOrders()
  if (name === 'designers') return loadDesignersTable()
  if (name === 'shoes')     return loadShoeTypesTable()
  if (name === 'suppliers') return loadSuppliersTable()
  if (name === 'compare')   return loadCompareTable()
})


// 5) 当材料类别切换时，如果“供应商使用次数”页签在看，也刷新表格
function resetFilters() {
    filters.dateRange = [dayjs().startOf('year').format('YYYY-MM-DD'), dayjs().format('YYYY-MM-DD')]
    filters.status = ''
    if (filters.scope === 'name') {
        filters.primaryCustomerName = nameOptions.value[0] || ''
        filters.compareCustomerNames = []
    } else {
        const first = brandGroups.value[0]?.options?.[0]
        filters.primaryCustomerId = first?.value ?? null
        filters.compareCustomerIds = []
    }
}
function exportAll() {
    ElMessage?.success?.('已触发导出（示例）')
}

/** ===== Resize & 生命周期 ===== */
function resizeAll() {
    chartUnitPriceHist?.resize()
    chartUnitPriceCompare?.resize()
    chartDesignerBar?.resize()
    chartTopShoeTypes?.resize()
    chartLeadtimeBox?.resize()
    chartSupplierUsageTop?.resize()
    chartSupplierUsageCompare?.resize()
}
window.addEventListener('resize', resizeAll)
onBeforeUnmount(() => {
    window.removeEventListener('resize', resizeAll)
    chartUnitPriceHist?.dispose()
    chartUnitPriceHist = null
    chartUnitPriceCompare?.dispose()
    chartUnitPriceCompare = null
    chartDesignerBar?.dispose()
    chartDesignerBar = null
    chartTopShoeTypes?.dispose()
    chartTopShoeTypes = null
    chartLeadtimeBox?.dispose()
    chartLeadtimeBox = null
    chartSupplierUsageTop?.dispose()
    chartSupplierUsageTop = null
    chartSupplierUsageCompare?.dispose()
    chartSupplierUsageCompare = null
})
onMounted(async () => {
    await initCustomers()
    await loadAll()
})
</script>

<style scoped>
.customer-analytics .kpi-card {
    height: 116px;
    border-radius: 12px;
    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.04);
}
.kpi-title {
    font-size: 12px;
    color: var(--el-text-color-secondary);
}
.kpi-value {
    font-size: 22px;
    font-weight: 700;
    line-height: 1.2;
    margin-top: 6px;
    letter-spacing: 0.2px;
}

.chart-card {
    min-height: 360px;
}
.chart-card :deep(.el-card__header) {
    font-weight: 600;
}
.chart {
    width: 100%;
    height: 320px;
}

.card-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
}
.card-title {
    font-weight: 600;
}
.head-actions {
    display: flex;
    gap: 8px;
    align-items: center;
}

.table-footer {
    display: flex;
    justify-content: flex-end;
    padding: 10px 0;
}

.mb-3 {
    margin-bottom: 16px;
}
.p-4 {
    padding: 16px;
}
</style>
