<!-- BusinessAnalytics.vue -->
<template>
    <div class="page p-4 business-analytics">
        <!-- ========== 筛选区（打印隐藏） ========== -->
        <el-card shadow="never" class="mb-3 no-print">
            <el-form :inline="true" :model="filters" @keyup.enter="loadAll">
                <el-form-item label="时间范围">
                    <el-date-picker v-model="filters.dateRange" type="daterange" start-placeholder="开始日期" end-placeholder="结束日期" unlink-panels value-format="YYYY-MM-DD" />
                </el-form-item>

                <!-- <el-form-item label="订单状态">
                    <el-select v-model="filters.status" clearable placeholder="全部" style="min-width: 160px">
                        <el-option v-for="s in orderStatusOptions" :key="s.value" :label="s.label" :value="s.value" />
                    </el-select>
                </el-form-item> -->

                <el-form-item>
                    <el-button type="primary" :loading="loading" @click="loadAll">查询</el-button>
                    <el-button @click="resetFilters">清空</el-button>
                </el-form-item>

                <el-form-item>
                    <!-- <el-button type="success" @click="printAll">打印</el-button> -->
                </el-form-item>
            </el-form>
        </el-card>

        <!-- ===== 打印区域开始：仅此容器会进入打印 ===== -->
        <div id="print-area" ref="refPrintArea">
            <!-- ========== KPI 总览 ========== -->
            <el-row :gutter="16" class="mb-3 kpi-row">
                <el-col :span="3" v-for="card in kpiCards" :key="card.key">
                    <el-card shadow="never" class="kpi-card">
                        <div class="kpi-title">{{ card.title }}</div>
                        <div class="kpi-value">
                            <span v-if="card.isMoney">{{ formatMoney(kpis[card.key]) }}</span>
                            <span v-else-if="card.isPercent">{{ formatPercent(kpis[card.key]) }}</span>
                            <span v-else>{{ kpis[card.key] ?? '-' }}</span>
                        </div>
                    </el-card>
                </el-col>
            </el-row>

            <!-- ========== 订单时间分布（整行） ========== -->
            <el-row :gutter="16" class="mb-3">
                <el-col :span="24">
                    <el-card shadow="never" class="rank-card">
                        <template #header>
                            <div class="card-head">
                                <span class="card-title">订单数 & 下单鞋数量 · 时间分布</span>
                                <div class="head-actions no-print">
                                    <el-select v-model="orderTimeAgg" size="small" style="width: 120px" @change="loadOrderSeries">
                                        <el-option label="按日" value="day" />
                                        <el-option label="按周" value="week" />
                                        <el-option label="按月" value="month" />
                                    </el-select>
                                </div>
                            </div>
                        </template>
                        <div class="chart print-taller" ref="refOrderTimeChart"></div>
                        <div class="print-break"></div>
                    </el-card>
                </el-col>
            </el-row>
            <el-row :gutter="16" class="mb-3">
                <el-col :span="24">
                    <el-card shadow="never" class="rank-card">
                        <template #header>
                            <div class="card-head">
                                <span class="card-title">在制（生产阶段） · 订单/鞋型 数量</span>
                                <div class="head-actions no-print">
                                    <el-select v-model="prodAgg" size="small" style="width: 120px" @change="loadProductionSeries">
                                        <el-option label="按日" value="day" />
                                        <el-option label="按周" value="week" />
                                        <el-option label="按月" value="month" />
                                    </el-select>
                                </div>
                            </div>
                        </template>
                        <div class="chart print-taller" ref="refProdChart"></div>
                        <div class="print-break"></div>
                    </el-card>
                </el-col>
            </el-row>

            <!-- ========== 客户 GMV/毛利率 组合图（整行） ========== -->
            <el-row :gutter="16" class="mb-3">
                <el-col :span="24">
                    <el-card shadow="never" class="rank-card">
                        <template #header>
                            <div class="card-head">
                                <span class="card-title">客户 GMV / 毛利率 对比</span>
                                <div class="head-actions no-print">
                                    <el-checkbox v-model="customerMetricShow.gmv" @change="renderCustomerCombo">显示 GMV</el-checkbox>
                                    <el-checkbox v-model="customerMetricShow.margin" @change="renderCustomerCombo">显示毛利率</el-checkbox>
                                    <!-- <el-button size="small" text type="primary" @click="toCustomerAnalytics()">客户分析页</el-button> -->
                                </div>
                            </div>
                        </template>
                        <div class="chart print-taller" ref="refCustomerComboChart"></div>
                        <div class="print-break"></div>
                    </el-card>
                </el-col>
            </el-row>

            <!-- ========== 四大榜单：图 + 表 ========== -->
            <el-row :gutter="16" class="mb-3">
                <!-- 订单榜 -->
                <el-col :span="12">
                    <el-card shadow="never" class="rank-card">
                        <template #header>
                            <div class="card-head">
                                <span class="card-title">订单 Top 排名</span>
                                <div class="head-actions no-print">
                                    <el-select v-model="metrics.order" size="small" style="width: 140px" @change="loadTopOrders">
                                        <el-option label="按毛利" value="gross_profit" />
                                        <el-option label="按毛利率" value="gross_margin" />
                                        <el-option label="按GMV" value="gmv" />
                                    </el-select>
                                    <el-button size="small" text type="primary" @click="toDetail('orders')">查看明细</el-button>
                                </div>
                            </div>
                        </template>

                        <div class="chart" ref="refOrderChart"></div>

                        <vxe-table :data="tops.orders.rows" height="320" border show-overflow @cell-dblclick="(row) => toDetail('orders', row.row)">
                            <vxe-column field="rank" title="#" width="56" align="center" />
                            <vxe-column field="order_rid" title="订单号" width="140" />
                            <vxe-column field="customer" title="客户" width="160" />
                            <vxe-column field="gmv" title="GMV" :formatter="moneyFmt" />
                            <vxe-column field="gross_profit" title="毛利" :formatter="moneyFmt" />
                            <vxe-column field="gross_margin" title="毛利率" :formatter="percentFmt" width="120" />
                        </vxe-table>
                        <div class="table-footer no-print">
                            <el-pagination
                                background
                                layout="prev, pager, next, jumper"
                                :total="tops.orders.total"
                                :page-size="tops.orders.size"
                                v-model:current-page="tops.orders.page"
                                @current-change="loadTopOrders"
                            />
                        </div>
                    </el-card>
                </el-col>

                <!-- 客户榜 -->
                <el-col :span="12">
                    <el-card shadow="never" class="rank-card">
                        <template #header>
                            <div class="card-head">
                                <span class="card-title">客户 Top 排名</span>
                                <div class="head-actions no-print">
                                    <el-select v-model="metrics.customer" size="small" style="width: 160px" @change="loadTopCustomers">
                                        <el-option label="按GMV" value="gmv" />
                                        <el-option label="按毛利" value="gross_profit" />
                                        <el-option label="按毛利率" value="gross_margin" />
                                        <el-option label="按订单数" value="orders" />
                                    </el-select>
                                    <el-button
                                        type="primary"
                                        size="small"
                                        text
                                        @click="
                                            bus.emit('nav:goto', {
                                                to: 'CustomerAnalysis',
                                                props: { from: 'BusinessAnalysis' }
                                            })
                                        "
                                    >
                                        客户分析页
                                    </el-button>
                                </div>
                            </div>
                        </template>

                        <div class="chart" ref="refCustomerChart"></div>

                        <vxe-table :data="tops.customers.rows" height="320" border show-overflow @cell-dblclick="(row) => toCustomerAnalytics(row.row)">
                            <vxe-column field="rank" title="#" width="56" align="center" />
                            <vxe-column field="customer" title="客户/商标" width="220">
                                <template #default="{ row }">
                                    <el-link
                                        type="primary"
                                        :underline="false"
                                        @click.stop="
                                            bus.emit('nav:goto', {
                                                to: 'CustomerAnalysis',
                                                props: { initialScope: 'brand', initialCustomerId: row.customer_id, from: 'BusinessAnalysis' }
                                            })
                                        "
                                    >
                                        {{ row.customer || '-' }}
                                    </el-link>
                                </template>
                            </vxe-column>
                            <vxe-column field="orders" title="订单数" width="100" />
                            <vxe-column field="gmv" title="GMV" :formatter="moneyFmt" />
                            <vxe-column field="gross_profit" title="毛利" :formatter="moneyFmt" />
                            <vxe-column field="gross_margin" title="毛利率" :formatter="percentFmt" width="120" />
                        </vxe-table>
                        <div class="table-footer no-print">
                            <el-pagination
                                background
                                layout="prev, pager, next, jumper"
                                :total="tops.customers.total"
                                :page-size="tops.customers.size"
                                v-model:current-page="tops.customers.page"
                                @current-change="loadTopCustomers"
                            />
                        </div>
                    </el-card>
                </el-col>
            </el-row>

            <el-row :gutter="16" class="mb-3">
                <!-- 供应商榜 -->
                <el-col :span="12">
                    <el-card shadow="never" class="rank-card">
                        <template #header>
                            <div class="card-head">
                                <div class="card-title-row">
                                    <span class="card-title">供应商 Top 排名</span>
                                </div>
                                <div class="head-actions compact-actions no-print">
                                    <el-space alignment="center" size="default">
                                        <el-select v-model="metrics.supplier" size="small" class="w-160" @change="loadTopSuppliers" placeholder="选择指标">
                                            <el-option label="按使用次数" value="usage_count" />
                                            <el-option label="按关联GMV" value="related_gmv" />
                                        </el-select>
                                        <div class="inline-filter">
                                            <span class="label">大类</span>
                                            <el-radio-group v-model="supplierActiveCat" size="small" @change="reloadSuppliersSection">
                                                <el-radio-button v-for="op in supplierCatOptions" :key="op" :label="op" />
                                            </el-radio-group>
                                        </div>
                                        <el-button size="small" text type="primary" @click="toSupplierAnalytics()"> 供应商分析 </el-button>
                                    </el-space>
                                </div>
                            </div>
                        </template>

                        <div class="chart" ref="refSupplierChart"></div>

                        <vxe-table :data="tops.suppliers.rows" height="320" border show-overflow @cell-dblclick="(row) => toSupplierAnalytics(row.row)">
                            <vxe-column field="rank" title="#" width="56" align="center" />
                            <vxe-column field="supplier_name" title="供应商" width="220" />
                            <vxe-column field="usage_count" title="使用次数" width="120" />
                            <vxe-column field="related_gmv" title="关联GMV" :formatter="moneyFmt" />
                            <vxe-column field="top_category" title="主要品类" width="120" />
                        </vxe-table>

                        <div class="table-footer no-print">
                            <el-pagination
                                background
                                layout="prev, pager, next, jumper"
                                :total="tops.suppliers.total"
                                :page-size="tops.suppliers.size"
                                v-model:current-page="tops.suppliers.page"
                                @current-change="loadTopSuppliers"
                            />
                        </div>
                    </el-card>
                </el-col>

                <!-- 鞋型榜 -->
                <el-col :span="12">
                    <el-card shadow="never" class="rank-card">
                        <template #header>
                            <div class="card-head">
                                <span class="card-title">鞋型 Top 排名</span>
                                <div class="head-actions no-print">
                                    <el-select v-model="metrics.shoe" size="small" style="width: 160px" @change="loadTopShoes">
                                        <el-option label="按使用次数" value="count" />
                                        <el-option label="按平均单价" value="avg_unit_price" />
                                        <el-option label="按GMV" value="gmv" />
                                        <el-option label="按毛利" value="gross_profit" />
                                    </el-select>
                                    <el-button size="small" text type="primary" @click="toShoeAnalytics()">鞋型分析</el-button>
                                </div>
                            </div>
                        </template>

                        <div class="chart" ref="refShoeChart"></div>

                        <vxe-table :data="tops.shoes.rows" height="320" border show-overflow @cell-dblclick="(row) => toShoeAnalytics(row.row)">
                            <vxe-column field="rank" title="#" width="56" align="center" />
                            <vxe-column field="shoe_type" title="鞋型" width="220" />
                            <vxe-column field="count" title="次数" width="100" />
                            <vxe-column field="avg_unit_price" title="平均单价" :formatter="moneyFmt" />
                            <vxe-column field="gmv" title="GMV" :formatter="moneyFmt" />
                            <vxe-column field="gross_profit" title="毛利" :formatter="moneyFmt" />
                        </vxe-table>
                        <div class="table-footer no-print">
                            <el-pagination
                                background
                                layout="prev, pager, next, jumper"
                                :total="tops.shoes.total"
                                :page-size="tops.shoes.size"
                                v-model:current-page="tops.shoes.page"
                                @current-change="loadTopShoes"
                            />
                        </div>
                    </el-card>
                </el-col>
            </el-row>
        </div>
        <!-- ===== 打印区域结束 ===== -->
    </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onBeforeUnmount, nextTick, watch, getCurrentInstance } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import dayjs from 'dayjs'
import * as echarts from 'echarts'
import { bus } from '../../hooks/bus'
import { fromCallback } from 'cypress/types/bluebird'

const router = useRouter()
const { $apiBaseUrl } = getCurrentInstance().appContext.config.globalProperties

/** ========== 接口路径 ========== */
const apiPath = {
    kpis: `${$apiBaseUrl}/businessanalysis/kpis/overview`,
    topOrders: `${$apiBaseUrl}/businessanalysis/top/orders`,
    topCustomers: `${$apiBaseUrl}/businessanalysis/top/customers`,
    topSuppliers: `${$apiBaseUrl}/businessanalysis/top/suppliers`,
    topShoes: `${$apiBaseUrl}/businessanalysis/top/shoes`,
    ordersSeries: `${$apiBaseUrl}/businessanalysis/orders/series`,
    shoesSeries: `${$apiBaseUrl}/businessanalysis/shoes/series`,
    productionSeries: `${$apiBaseUrl}/businessanalysis/production/series`
}

/** ========== 筛选/加载状态 ========== */
const orderStatusOptions = [
    { label: '全部', value: '' },
    { label: '进行中', value: 'in_progress' },
    { label: '完结', value: 'finished' },
    { label: '逾期', value: 'delayed' }
]
const filters = reactive({
    dateRange: [dayjs().startOf('year').format('YYYY-MM-DD'), dayjs().format('YYYY-MM-DD')] as string[] | null,
    status: '' as string | ''
})
const loading = ref(false)

/** ========== 打印 ========== */
const refPrintArea = ref<HTMLDivElement | null>(null)
function printAll() {
    // 先确保图表按打印尺寸计算好布局
    resizeAllCharts()
    window.print()
}
// 确保 before/after print 时图表不会被压缩
function handleBeforePrint() {
    setTimeout(resizeAllCharts, 50)
}
function handleAfterPrint() {
    setTimeout(resizeAllCharts, 50)
}

/** ========== KPI ========== */
const kpis = reactive<any>({
    orders: 0,
    customers: 0,
    suppliers: 0,
    gmv: 0,
    gross_profit: 0,
    gross_margin: 0
})
const kpiCards = [
    { key: 'orders', title: '订单数' },
    { key: 'customers', title: '客户数' },
    { key: 'suppliers', title: '供应商数' },
    { key: 'gmv', title: 'GMV', isMoney: true },
    { key: 'gross_profit', title: '毛利', isMoney: true },
    { key: 'gross_margin', title: '毛利率', isPercent: true }
]

/** ========== 排名：指标选择 + 分页容器 ========== */
const metrics = reactive({
    order: 'gross_profit',
    customer: 'gmv',
    supplier: 'usage_count',
    shoe: 'count'
})
const tops = reactive({
    orders: { rows: [] as any[], page: 1, size: 10, total: 0 },
    customers: { rows: [] as any[], page: 1, size: 10, total: 0 },
    suppliers: { rows: [] as any[], page: 1, size: 10, total: 0 },
    shoes: { rows: [] as any[], page: 1, size: 10, total: 0 }
})

/** ========== 通用格式化 ========== */
const formatMoney = (v: any) => {
    const n = Number(v ?? 0)
    if (Number.isNaN(n)) return '-'
    return n.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}
const formatPercent = (v: any) => {
    if (v == null) return '-'
    const n = Number(v)
    if (Number.isNaN(n)) return '-'
    return (n * 100).toFixed(1) + '%'
}
const moneyFmt = ({ cellValue }: any) => formatMoney(cellValue)
const percentFmt = ({ cellValue }: any) => formatPercent(cellValue)

/** ========== ECharts 主题/工具 ========== */
const PALETTE = ['#5B8FF9', '#61DDAA', '#65789B', '#F6BD16', '#7262FD', '#78D3F8', '#FF99C3', '#FB8D34', '#9AE65C', '#F690BA']
const THEME_KEY = '__ECHARTS_THEME_CLEAN_BUSINESS__'
const g: any = typeof window !== 'undefined' ? window : globalThis
if (!g[THEME_KEY]) {
    echarts.registerTheme('clean', {
        color: PALETTE,
        textStyle: { fontFamily: 'Inter, system-ui, -apple-system, Segoe UI, Roboto, Arial' },
        grid: { left: 40, right: 24, top: 40, bottom: 40, containLabel: true },
        tooltip: { backgroundColor: '#1f2937', borderWidth: 0, textStyle: { color: '#fff' } },
        legend: { top: 8, itemWidth: 12, itemHeight: 12 },
        valueAxis: { splitLine: { lineStyle: { color: '#E5E7EB' } } }
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
    return labels.length > 12 ? [{ type: 'slider', height: 14, bottom: 0 }, { type: 'inside' }] : []
}

/** ========== 图表 refs & 实例 ========== */
const refOrderChart = ref<HTMLDivElement>()
const refCustomerChart = ref<HTMLDivElement>()
const refSupplierChart = ref<HTMLDivElement>()
const refShoeChart = ref<HTMLDivElement>()
let chartOrder: echarts.ECharts | null = null
let chartCustomer: echarts.ECharts | null = null

/** ========== 渲染函数（省略逻辑不变） ========== */
function renderOrderChart(rows: any[]) {
    /* ……原实现保持不变 …… */
    chartOrder = initChart(refOrderChart.value, chartOrder)
    if (!rows?.length) {
        chartOrder?.clear()
        return
    }
    const isPct = metrics.order === 'gross_margin'
    const fullCats = rows.map((r) => `${r.order_rid}`)
    const cats = fullCats.map((s) => wrapEllipsis(s, 14, 2))
    const vals = rows.map((r) => r[metrics.order] ?? 0)
    const valid = vals.filter((v) => Number.isFinite(v))
    const avg = valid.length ? valid.reduce((a, b) => a + b, 0) / valid.length : 0
    const sorted = [...valid].sort((a, b) => a - b)
    const mid = sorted.length ? (sorted.length % 2 ? sorted[(sorted.length - 1) / 2] : (sorted[sorted.length / 2 - 1] + sorted[sorted.length / 2]) / 2) : 0
    chartOrder!.setOption({
        toolbox: TB,
        grid: { top: 16, bottom: 36, right: 20, left: leftPaddingFor(fullCats, 120, 6, 260), containLabel: true },
        dataZoom: addZoomIfLong(cats),
        tooltip: {
            confine: true,
            appendToBody: true,
            trigger: 'axis',
            axisPointer: { type: 'shadow' },
            formatter: (p: any) => {
                const v = p[0]?.value ?? 0
                const title = fullCats[p[0]?.dataIndex ?? 0]
                const line1 = `<div style="font-weight:600;margin-bottom:4px">${title}</div>`
                const line2 = isPct ? `毛利率：${percentShort(v)}` : `数值：${formatMoney(v)}`
                return line1 + line2
            }
        },
        xAxis: { type: 'value', name: isPct ? '毛利率' : '金额', splitLine: { lineStyle: { type: 'dashed', color: '#E5E7EB' } }, axisLine: { show: false }, axisLabel: { margin: 8 } },
        yAxis: { type: 'category', inverse: true, data: cats, axisTick: { show: false }, axisLine: { show: false }, axisLabel: { interval: 0, lineHeight: 16, margin: 8, overflow: 'break' } },
        series: [
            {
                type: 'bar',
                data: vals.map((v) => ({
                    value: v,
                    itemStyle: { color: linearGrad(PALETTE[0], 0.95, 0.18), borderRadius: 10 },
                    emphasis: { itemStyle: { shadowBlur: 10, shadowColor: 'rgba(0,0,0,.18)' } }
                })),
                barMaxWidth: 22,
                showBackground: true,
                backgroundStyle: { color: 'rgba(0,0,0,0.035)', borderRadius: 10 },
                label: { show: true, position: 'right', distance: 6, formatter: (p: any) => (isPct ? percentShort(p.value) : moneyShort(p.value)) },
                animationDuration: 500,
                animationEasing: 'cubicOut'
            }
        ],
        markLine: {
            symbol: 'none',
            label: {
                formatter: (p: any) => `${p?.name}${isPct ? `：${percentShort(p?.value ?? 0)}` : `：${moneyShort(p?.value ?? 0)}`}`,
                padding: [2, 6],
                backgroundColor: 'rgba(31,41,55,.75)',
                color: '#fff',
                borderRadius: 4
            },
            lineStyle: { type: 'dashed', width: 1.2, opacity: 0.85 },
            data: [
                { name: '均值', xAxis: avg },
                { name: '中位数', xAxis: mid }
            ]
        }
    })
    chartOrder!.resize()
}
function renderCustomerChart(rows: any[]) {
    /* ……原实现保持不变 …… */
    chartCustomer = initChart(refCustomerChart.value, chartCustomer)
    if (!rows?.length) {
        chartCustomer?.clear()
        return
    }
    const isPct = metrics.customer === 'gross_margin'
    const isOrders = metrics.customer === 'orders'
    const fullCats = rows.map((r) => r.customer || '-')
    const cats = fullCats.map((s) => wrapEllipsis(s, 12, 2))
    const vals = rows.map((r) => r[metrics.customer] ?? 0)
    const valid = vals.filter((v) => Number.isFinite(v))
    const avg = valid.length ? valid.reduce((a, b) => a + b, 0) / valid.length : 0
    const sorted = [...valid].sort((a, b) => a - b)
    const mid = sorted.length ? (sorted.length % 2 ? sorted[(sorted.length - 1) / 2] : (sorted[sorted.length / 2 - 1] + sorted[sorted.length / 2]) / 2) : 0
    chartCustomer!.setOption({
        toolbox: TB,
        grid: { top: 16, bottom: 36, right: 20, left: leftPaddingFor(fullCats, 120, 6, 240), containLabel: true },
        dataZoom: addZoomIfLong(cats),
        tooltip: {
            confine: true,
            appendToBody: true,
            trigger: 'axis',
            axisPointer: { type: 'shadow' },
            formatter: (p: any) => {
                const v = p[0]?.value ?? 0
                const title = fullCats[p[0]?.dataIndex ?? 0]
                const line1 = `<div style="font-weight:600;margin-bottom:4px">${title}</div>`
                let line2 = ''
                if (isOrders) line2 = `订单数：${v}`
                else if (isPct) line2 = `毛利率：${percentShort(v)}`
                else line2 = `数值：${formatMoney(v)}`
                return line1 + line2
            }
        },
        xAxis: { type: 'value', splitLine: { lineStyle: { type: 'dashed', color: '#E5E7EB' } }, axisLine: { show: false }, axisLabel: { margin: 8 } },
        yAxis: { type: 'category', inverse: true, data: cats, axisTick: { show: false }, axisLine: { show: false }, axisLabel: { interval: 0, lineHeight: 16, margin: 8, overflow: 'break' } },
        series: [
            {
                type: 'bar',
                data: vals.map((v) => ({
                    value: v,
                    itemStyle: { color: linearGrad(PALETTE[1], 0.95, 0.18), borderRadius: 10 },
                    emphasis: { itemStyle: { shadowBlur: 10, shadowColor: 'rgba(0,0,0,.18)' } }
                })),
                barMaxWidth: 22,
                showBackground: true,
                backgroundStyle: { color: 'rgba(0,0,0,0.035)', borderRadius: 10 },
                label: {
                    show: true,
                    position: 'right',
                    distance: 6,
                    formatter: (p: any) => {
                        if (isOrders) return p.value
                        if (isPct) return percentShort(p.value)
                        return moneyShort(p.value)
                    }
                },
                animationDuration: 500,
                animationEasing: 'cubicOut'
            }
        ],
        markLine: {
            symbol: 'none',
            label: {
                formatter: (p: any) => {
                    const name = p?.name,
                        val = p?.value ?? 0
                    return isOrders ? `${name}：${val}` : `${name}：${isPct ? percentShort(val) : moneyShort(val)}`
                },
                padding: [2, 6],
                backgroundColor: 'rgba(31,41,55,.75)',
                color: '#fff',
                borderRadius: 4
            },
            lineStyle: { type: 'dashed', width: 1.2, opacity: 0.85 },
            data: [
                { name: '均值', xAxis: avg },
                { name: '中位数', xAxis: mid }
            ]
        }
    })
    chartCustomer!.resize()
}
const supplierCatOptions = ['全部', '面料', '里料', '辅料', '底材'] as const
type SupplierCat = (typeof supplierCatOptions)[number]
const supplierActiveCat = ref<SupplierCat>('全部')
let chartSupplier: echarts.ECharts | null = null
let chartShoe: echarts.ECharts | null = null
function renderSupplierChart(rows: any[]) {
    /* ……原实现保持不变 …… */
    chartSupplier = initChart(refSupplierChart.value, chartSupplier)
    if (!rows?.length) {
        chartSupplier?.clear()
        return
    }
    const name = (r: any) => r.supplier_name || '-'
    const value = (r: any) => (metrics.supplier === 'usage_count' ? r.usage_count || 0 : r.related_gmv || 0)
    const show = (r: any) => (metrics.supplier === 'usage_count' ? r.usage_count : formatMoney(r.related_gmv))
    const data = rows.map((r: any, i: number) => ({ name: `${name(r)}\n${show(r)}`, value: value(r), itemStyle: { color: PALETTE[i % PALETTE.length] } }))
    chartSupplier!.setOption({
        tooltip: {
            formatter: (p: any) => {
                const row = rows[p.dataIndex]
                return `<div style="font-weight:600;margin-bottom:6px">${name(row)}</div>${metrics.supplier === 'usage_count' ? `使用次数：${row.usage_count}` : `关联GMV：${formatMoney(row.related_gmv)}`}`
            }
        },
        series: [{ type: 'treemap', roam: true, breadcrumb: { show: false }, nodeClick: false, label: { show: true, formatter: '{b}', overflow: 'truncate' }, upperLabel: { show: false }, data }]
    })
}
function renderShoeChart(rows: any[]) {
    /* ……原实现保持不变 …… */
    chartShoe = initChart(refShoeChart.value, chartShoe)
    if (!rows?.length) {
        chartShoe?.clear()
        return
    }
    const cats = rows.map((r) => r.shoe_type || '-')
    const vals = rows.map((r) => r[metrics.shoe] ?? 0)
    const moneyMetrics = ['avg_unit_price', 'gmv', 'gross_profit']
    chartShoe!.setOption({
        toolbox: TB,
        tooltip: { trigger: 'axis', valueFormatter: (v: any) => (moneyMetrics.includes(metrics.shoe) ? formatMoney(v) : v) },
        grid: { top: 46, left: 48, right: 24, bottom: 60, containLabel: true },
        xAxis: { type: 'category', data: cats, axisLabel: { interval: 0, rotate: cats.length > 12 ? 28 : 0 } },
        yAxis: { type: 'value', name: moneyMetrics.includes(metrics.shoe) ? '金额' : '次数' },
        dataZoom: addZoomIfLong(cats),
        series: [
            {
                type: 'bar',
                data: vals.map((v, i) => ({ value: v, itemStyle: { color: linearGrad(PALETTE[(i + 2) % PALETTE.length]) } })),
                barMaxWidth: 32,
                itemStyle: { borderRadius: [8, 8, 0, 0] },
                label: { show: true, position: 'top', formatter: (p: any) => (moneyMetrics.includes(metrics.shoe) ? formatMoney(p.value) : p.value) }
            }
        ]
    })
}

/** ========== 参数与加载 ========== */
function baseRange() {
    const [from, to] = filters.dateRange || [null, null]
    return { date_from: from, date_to: to, status: filters.status || '' }
}
async function loadKpis() {
    const { data } = await axios.get(apiPath.kpis, { params: { ...baseRange() } })
    Object.assign(kpis, data || {})
}
async function loadTopOrders() {
    const params = { ...baseRange(), metric: metrics.order, page: tops.orders.page, size: tops.orders.size }
    const { data } = await axios.get(apiPath.topOrders, { params })
    tops.orders.rows = (data?.rows || []).map((r: any, i: number) => ({ rank: (tops.orders.page - 1) * tops.orders.size + i + 1, ...r }))
    tops.orders.total = data?.total || 0
    await nextTick()
    renderOrderChart(tops.orders.rows)
}
async function loadTopCustomers() {
    const params = { ...baseRange(), metric: metrics.customer, page: tops.customers.page, size: tops.customers.size }
    const { data } = await axios.get(apiPath.topCustomers, { params })
    tops.customers.rows = (data?.rows || []).map((r: any, i: number) => ({ rank: (tops.customers.page - 1) * tops.customers.size + i + 1, ...r }))
    tops.customers.total = data?.total || 0
    await nextTick()
    renderCustomerChart(tops.customers.rows)
}
async function loadTopSuppliers() {
    const params = { ...baseRange(), metric: metrics.supplier, page: tops.suppliers.page, size: tops.suppliers.size, material_cat: supplierActiveCat.value }
    const { data } = await axios.get(apiPath.topSuppliers, { params })
    tops.suppliers.rows = (data?.rows || []).map((r: any, i: number) => ({ rank: (tops.suppliers.page - 1) * tops.suppliers.size + i + 1, ...r }))
    tops.suppliers.total = data?.total || 0
    await nextTick()
    renderSupplierChart(tops.suppliers.rows)
}
async function loadTopShoes() {
    const params = { ...baseRange(), metric: metrics.shoe, page: tops.shoes.page, size: tops.shoes.size }
    const { data } = await axios.get(apiPath.topShoes, { params })
    tops.shoes.rows = (data?.rows || []).map((r: any, i: number) => ({ rank: (tops.shoes.page - 1) * tops.shoes.size + i + 1, ...r }))
    tops.shoes.total = data?.total || 0
    await nextTick()
    renderShoeChart(tops.shoes.rows)
}
const refOrderTimeChart = ref<HTMLDivElement>()
let chartOrderTime: echarts.ECharts | null = null
const orderTimeAgg = ref<'day' | 'week' | 'month'>('week')
let orderSeries: Array<{ date: string; order_count: number; shoe_count: number }> = []
let shoeSeries: Array<{ date: string; count: number }> = []
const refCustomerComboChart = ref<HTMLDivElement>()
let chartCustomerCombo: echarts.ECharts | null = null
const customerMetricShow = reactive({ gmv: true, margin: true })
function renderOrderTimeChart(data: Array<{ date: string; order_count: number; shoe_count: number }>) {
    chartOrderTime = initChart(refOrderTimeChart.value, chartOrderTime)
    if (!data?.length) {
        chartOrderTime?.clear()
        return
    }

    const x = data.map((d) => d.date)
    const yOrders = data.map((d) => d.order_count ?? 0)
    const yShoes = data.map((d) => d.shoe_count ?? 0)

    chartOrderTime!.setOption({
        toolbox: TB,
        grid: { top: 28, left: 40, right: 48, bottom: 40, containLabel: true },
        legend: { top: 2, data: ['订单数', '下单鞋数量'] },
        tooltip: {
            trigger: 'axis',
            axisPointer: { type: 'shadow' },
            formatter: (params: any[]) => {
                const title = params?.[0]?.axisValueLabel ?? ''
                const pOrder = params.find((p) => p.seriesName === '订单数')
                const pShoe = params.find((p) => p.seriesName === '下单鞋数量')
                const l1 = `<div style="font-weight:600;margin-bottom:4px">${title}</div>`
                const l2 = pOrder ? `订单数：${pOrder.value}` : ''
                const l3 = pShoe ? `下单鞋数量：${pShoe.value}` : ''
                return [l1, l2, l3].filter(Boolean).join('<br/>')
            }
        },
        xAxis: { type: 'category', data: x, axisLabel: { rotate: x.length > 16 ? 30 : 0 } },
        yAxis: [
            { type: 'value', name: '订单数' },
            { type: 'value', name: '下单鞋数量' }
        ],
        dataZoom: addZoomIfLong(x),
        series: [
            {
                name: '订单数',
                type: 'bar',
                yAxisIndex: 0,
                barMaxWidth: 24,
                itemStyle: { borderRadius: [6, 6, 0, 0], color: linearGrad(PALETTE[3], 0.95, 0.18) },
                data: yOrders
            },
            {
                name: '下单鞋数量',
                type: 'line',
                yAxisIndex: 1,
                smooth: true,
                symbol: 'circle',
                symbolSize: 6,
                lineStyle: { width: 2 },
                areaStyle: { opacity: 0.12 },
                data: yShoes
            }
        ]
    })
}
const refProdChart = ref<HTMLDivElement>()
let chartProd: echarts.ECharts | null = null
const prodAgg = ref<'day' | 'week' | 'month'>('week')
let prodSeries: Array<{ date: string; order_in_prod: number; shoe_pairs_in_prod: number }> = []
function renderProductionChart(data: Array<{ date: string; order_in_prod: number; shoe_pairs_in_prod: number }>) {
    const x = data.map((d) => d.date)
    const orders = data.map((d) => d.order_in_prod ?? 0)
    const pairs = data.map((d) => d.shoe_pairs_in_prod ?? 0)
    chartProd = initChart(refProdChart.value, chartProd)
    if (!x.length) {
        chartProd?.clear()
        return
    }

    chartProd!.setOption({
        toolbox: TB,
        grid: { top: 28, left: 44, right: 60, bottom: 40, containLabel: true },
        tooltip: {
            trigger: 'axis',
            valueFormatter: (v: any, s: any) => (s?.seriesName === '在产鞋双数' ? String(v) : String(v))
        },
        legend: { top: 0, data: ['在产订单数', '在产鞋双数'] },
        xAxis: { type: 'category', data: x, axisLabel: { rotate: x.length > 16 ? 30 : 0 } },
        yAxis: [
            { type: 'value', name: '订单数', minInterval: 1 },
            { type: 'value', name: '双数', minInterval: 1 }
        ],
        dataZoom: addZoomIfLong(x),
        series: [
            { name: '在产订单数', type: 'bar', yAxisIndex: 0, barMaxWidth: 24, itemStyle: { borderRadius: [6, 6, 0, 0], color: linearGrad(PALETTE[0], 0.95, 0.18) }, data: orders },
            { name: '在产鞋双数', type: 'line', yAxisIndex: 1, smooth: true, symbol: 'circle', symbolSize: 6, lineStyle: { width: 2 }, areaStyle: { opacity: 0.12 }, data: pairs }
        ]
    })
}

function renderCustomerCombo() {
    chartCustomerCombo = initChart(refCustomerComboChart.value, chartCustomerCombo)
    const rows = tops.customers.rows || []
    if (!rows.length || (!customerMetricShow.gmv && !customerMetricShow.margin)) {
        chartCustomerCombo?.clear()
        return
    }
    const cats = rows.map((r: any) => wrapEllipsis(r.customer || '-', 12, 2))
    const gmv = rows.map((r: any) => r.gmv ?? 0)
    const margin = rows.map((r: any) => r.gross_margin ?? 0)
    chartCustomerCombo!.setOption({
        toolbox: TB,
        grid: { top: 18, left: 48, right: 48, bottom: 60, containLabel: true },
        tooltip: { trigger: 'axis', valueFormatter: (v: any, s: any) => (s?.seriesName === '毛利率' ? percentShort(Number(v)) : formatMoney(Number(v))) },
        legend: { top: 0, data: ['GMV', '毛利率'] },
        xAxis: { type: 'category', data: cats, axisLabel: { interval: 0, rotate: cats.length > 12 ? 28 : 0 } },
        yAxis: [
            { type: 'value', name: 'GMV', axisLabel: { formatter: (v: number) => moneyShort(v as number) } },
            { type: 'value', name: '毛利率', min: 0, max: 1, axisLabel: { formatter: (v: number) => percentShort(v as number) } }
        ],
        dataZoom: addZoomIfLong(cats),
        series: [
            ...(customerMetricShow.gmv
                ? [
                      {
                          name: 'GMV',
                          type: 'bar',
                          yAxisIndex: 0,
                          barMaxWidth: 28,
                          itemStyle: { borderRadius: [8, 8, 0, 0], color: linearGrad(PALETTE[2], 0.95, 0.18) },
                          label: { show: true, position: 'top', formatter: (p: any) => moneyShort(p.value) },
                          data: gmv
                      }
                  ]
                : []),
            ...(customerMetricShow.margin
                ? [
                      {
                          name: '毛利率',
                          type: 'line',
                          yAxisIndex: 1,
                          smooth: true,
                          symbol: 'circle',
                          symbolSize: 6,
                          lineStyle: { width: 2 },
                          label: { show: true, position: 'top', formatter: (p: any) => percentShort(p.value) },
                          data: margin
                      }
                  ]
                : [])
        ]
    })
}
async function loadOrderSeries() {
    const params: any = { ...baseRange(), agg: orderTimeAgg.value }
    const { data } = await axios.get(apiPath.ordersSeries, { params })
    // 兼容字段名：后端已返回 order_count / shoe_count；若老字段仅有 count，则把其当作订单数
    orderSeries = (data?.rows || data || []).map((d: any) => ({
        date: d.date,
        order_count: Number(d.order_count ?? d.count ?? 0),
        shoe_count: Number(d.shoe_count ?? d.count_shoes ?? d.shoeCount ?? 0)
    }))
    await nextTick()
    renderOrderTimeChart(orderSeries)
}
async function loadProductionSeries() {
    const params: any = { ...baseRange(), agg: prodAgg.value }
    const { data } = await axios.get(apiPath.productionSeries, { params })
    prodSeries = (data?.rows || data || []).map((d: any) => ({
        date: d.date,
        order_in_prod: Number(d.order_in_prod ?? 0),
        shoe_pairs_in_prod: Number(d.shoe_pairs_in_prod ?? 0)
    }))
    await nextTick()
    renderProductionChart(prodSeries)
}

async function loadAll() {
    loading.value = true
    try {
        await Promise.all([loadKpis(), loadTopOrders(), loadTopCustomers(), loadTopSuppliers(), loadTopShoes(), loadOrderSeries(), loadProductionSeries()])
        renderCustomerCombo()
    } finally {
        loading.value = false
    }
}

function resetFilters() {
    filters.dateRange = [dayjs().startOf('year').format('YYYY-MM-DD'), dayjs().format('YYYY-MM-DD')]
    filters.status = ''
    tops.orders.page = tops.customers.page = tops.suppliers.page = tops.shoes.page = 1
    loadAll()
}

/** ========== 跳转 ========== */
function toDetail(_type: 'orders', row?: any) {
    router.push({ name: 'OrderList', query: { date_from: baseRange().date_from, date_to: baseRange().date_to, status: baseRange().status, order_rid: row?.order_rid } })
}
function toCustomerAnalytics(row?: any) {
    router.push({ name: 'CustomerAnalytics', query: { scope: 'brand', customerId: row?.customer_id } })
}
function toSupplierAnalytics(row?: any) {
    router.push({ name: 'SupplierAnalytics', query: { supplier_id: row?.supplier_id } })
}
function toShoeAnalytics(row?: any) {
    router.push({ name: 'ShoeAnalytics', query: { shoe_type: row?.shoe_type } })
}
async function reloadSuppliersSection() {
    tops.suppliers.page = 1
    await loadTopSuppliers()
}

/** ========== 自适应 & 生命周期 ========== */
function resizeAllCharts() {
    chartOrder?.resize()
    chartCustomer?.resize()
    chartSupplier?.resize()
    chartShoe?.resize()
    chartOrderTime?.resize()
    chartCustomerCombo?.resize()
    chartProd?.resize()
}
window.addEventListener('resize', resizeAllCharts)
window.addEventListener('beforeprint', handleBeforePrint)
window.addEventListener('afterprint', handleAfterPrint)
onBeforeUnmount(() => {
    window.removeEventListener('resize', resizeAllCharts)
    window.removeEventListener('beforeprint', handleBeforePrint)
    window.removeEventListener('afterprint', handleAfterPrint)
    chartOrder?.dispose()
    chartOrder = null
    chartCustomer?.dispose()
    chartCustomer = null
    chartSupplier?.dispose()
    chartSupplier = null
    chartShoe?.dispose()
    chartShoe = null
})
function moneyShort(n: number) {
    if (!Number.isFinite(n)) return '-'
    const abs = Math.abs(n)
    if (abs >= 1e8) return (n / 1e8).toFixed(2).replace(/\.00$/, '') + '亿'
    if (abs >= 1e4) return (n / 1e4).toFixed(2).replace(/\.00$/, '') + '万'
    return n.toFixed(2).replace(/\.00$/, '')
}
function percentShort(n: number) {
    if (!Number.isFinite(n)) return '-'
    return (n * 100).toFixed(1).replace(/\.0$/, '') + '%'
}
function wrapEllipsis(text: string, perLine = 12, maxLines = 2) {
    if (!text) return ''
    const chunks: string[] = []
    for (let i = 0; i < text.length && chunks.length < maxLines; i += perLine) chunks.push(text.slice(i, i + perLine))
    if (text.length > perLine * maxLines) {
        const last = chunks[chunks.length - 1]
        chunks[chunks.length - 1] = last.slice(0, Math.max(0, last.length - 1)) + '…'
    }
    return chunks.join('\n')
}
function leftPaddingFor(labels: string[], base = 120, perChar = 6, max = 240) {
    const maxLen = Math.max(0, ...labels.map((s) => (s || '').length))
    return Math.min(max, base + maxLen * perChar)
}

onMounted(() => {
    // 某些浏览器支持 matchMedia('print') 变更
    const mq = window.matchMedia ? window.matchMedia('print') : null
    mq?.addEventListener?.('change', () => setTimeout(resizeAllCharts, 50))
    loadAll()
})

watch(
    () => metrics.order,
    () => {
        tops.orders.page = 1
        loadTopOrders()
    }
)
watch(
    () => metrics.customer,
    () => {
        tops.customers.page = 1
        loadTopCustomers()
    }
)
watch(
    () => metrics.supplier,
    () => {
        tops.suppliers.page = 1
        loadTopSuppliers()
    }
)
watch(
    () => metrics.shoe,
    () => {
        tops.shoes.page = 1
        loadTopShoes()
    }
)
watch(
    () => tops.customers.rows,
    () => {
        renderCustomerCombo()
    }
)
watch(
    () => [customerMetricShow.gmv, customerMetricShow.margin],
    () => {
        renderCustomerCombo()
    }
)
watch(
    () => orderTimeAgg.value,
    () => {
        loadOrderSeries()
    }
)
watch(
    () => prodAgg.value,
    () => {
        loadProductionSeries()
    }
)
</script>

<style scoped>
/* —— 屏幕样式 —— */
.business-analytics .kpi-card {
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

.rank-card :deep(.el-card__header) {
    font-weight: 600;
}
.card-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
}
.card-title {
    font-weight: 600;
}

.chart {
    width: 100%;
    height: 260px;
    margin-bottom: 10px;
}
.print-taller {
    /* 屏幕也稍微高一点更舒服；打印里会再覆盖 */
    height: 300px;
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
.w-160 {
    width: 160px;
}

/* —— 打印样式 —— */
@media print {
    @page {
        size: A4 portrait;
        margin: 12mm;
    }
    :root {
        -webkit-print-color-adjust: exact;
        print-color-adjust: exact;
    }

    /* 只打印 #print-area */
    body * {
        visibility: hidden;
    }
    #print-area,
    #print-area * {
        visibility: visible;
    }
    #print-area {
        position: absolute;
        left: 0;
        top: 0;
        width: 100%;
    }

    /* 隐藏不需要的交互控件 */
    .no-print {
        display: none !important;
    }
    .el-pagination,
    .el-checkbox,
    .el-select,
    .el-button {
        display: none !important;
    }

    /* 卡片/表格分页优化 */
    .el-card,
    .kpi-card,
    .rank-card {
        break-inside: avoid;
        page-break-inside: avoid;
    }
    .vxe-table,
    table {
        break-inside: auto;
        page-break-inside: auto;
    }

    /* 提升图表高度（画布更清晰） */
    .chart,
    .print-taller {
        height: 340px !important;
    }

    /* 手动分页断点（在大图后换页更美观） */
    .print-break {
        page-break-after: always;
    }
}
</style>
