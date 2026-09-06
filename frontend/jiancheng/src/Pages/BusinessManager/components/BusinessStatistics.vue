<template>
    <div class="stat-page">
        <el-row :gutter="20">
            <el-col class="u-page-title" :span="24" :offset="0">业务统计看板</el-col>
        </el-row>

        <el-row :gutter="12" class="stat-toolbar">
            <el-col :span="24">
                <div class="toolbar-wrap">
                    <span class="toolbar-label">统计维度：</span>
                    <el-radio-group v-model="period" size="default" @change="onPeriodChange">
                        <el-radio-button label="近一周" value="week" />
                        <el-radio-button label="近一月" value="month" />
                        <el-radio-button label="近半年" value="halfyear" />
                        <el-radio-button label="近一年" value="year" />
                    </el-radio-group>
                    <span class="toolbar-label">自定义：</span>
                    <el-date-picker v-model="customRange" type="daterange" unlink-panels range-separator="至"
                        start-placeholder="开始日期" end-placeholder="结束日期" value-format="YYYY-MM-DD" size="default"
                        @change="onCustomRangeChange" />
                    <span v-if="periodStart" class="toolbar-range">统计区间：{{ periodStart }} 至 {{ periodEnd }}</span>
                    <el-button type="primary" :loading="loading" @click="fetchStatistics" style="margin-left:auto">刷新</el-button>
                </div>
            </el-col>
        </el-row>

        <!-- 概览卡片 -->
        <el-row :gutter="20" class="stat-cards">
            <el-col :span="12">
                <div class="stat-card">
                    <div class="stat-card-title">手上未完成订单总双数</div>
                    <div class="stat-card-value pairs">{{ unfinishedTotalPairs }}</div>
                </div>
            </el-col>
            <el-col :span="12">
                <div class="stat-card">
                    <div class="stat-card-title">手上未完成订单数</div>
                    <div class="stat-card-value count">{{ unfinishedOrderCount }}</div>
                </div>
            </el-col>
        </el-row>

        <!-- 客户下单情况 -->
        <el-card class="stat-block" shadow="never">
            <template #header>
                <div class="block-header">
                    <span class="block-title">客户下单情况（{{ rangeLabel }}）</span>
                    <div class="block-controls">
                        <el-radio-group v-model="customerMetric" size="small">
                            <el-radio-button label="按双数" value="totalPairs" />
                            <el-radio-button label="按订单数" value="orderCount" />
                        </el-radio-group>
                        <el-input v-model="customerSearch" placeholder="搜索客户名" size="small" clearable class="block-search" />
                    </div>
                </div>
            </template>
            <el-row :gutter="20">
                <el-col :span="10">
                    <el-table :data="pageSlice(customerProcessed, customerPage)" border stripe height="360" size="small"
                        @row-click="row => openDetail('customer', row.customerId)" class="clickable-table">
                        <el-table-column type="index" label="#" width="50" :index="i => indexBase(customerPage) + i" />
                        <el-table-column prop="customerName" label="客户名" />
                        <el-table-column prop="customerBrand" label="客户商标" />
                        <el-table-column prop="orderCount" label="订单数" width="90" sortable />
                        <el-table-column prop="totalPairs" label="总双数" width="100" sortable />
                    </el-table>
                    <el-pagination small layout="total,prev,pager,next" :total="customerProcessed.length"
                        :page-size="pageSize" :current-page="customerPage" @current-change="p => customerPage = p"
                        class="block-pager" />
                </el-col>
                <el-col :span="14">
                    <div ref="customerChart" class="chart-box"></div>
                </el-col>
            </el-row>
        </el-card>

        <!-- 业务员下单情况 -->
        <el-card class="stat-block" shadow="never">
            <template #header>
                <div class="block-header">
                    <span class="block-title">业务员下单情况（{{ rangeLabel }}）</span>
                    <div class="block-controls">
                        <el-radio-group v-model="salesmanMetric" size="small">
                            <el-radio-button label="按双数" value="totalPairs" />
                            <el-radio-button label="按订单数" value="orderCount" />
                        </el-radio-group>
                        <el-input v-model="salesmanSearch" placeholder="搜索业务员" size="small" clearable class="block-search" />
                    </div>
                </div>
            </template>
            <el-row :gutter="20">
                <el-col :span="10">
                    <el-table :data="pageSlice(salesmanProcessed, salesmanPage)" border stripe height="360" size="small"
                        @row-click="row => openDetail('salesman', row.salesmanId)" class="clickable-table">
                        <el-table-column type="index" label="#" width="50" :index="i => indexBase(salesmanPage) + i" />
                        <el-table-column prop="salesmanName" label="业务员" />
                        <el-table-column prop="orderCount" label="订单数" width="90" sortable />
                        <el-table-column prop="totalPairs" label="总双数" width="100" sortable />
                    </el-table>
                    <el-pagination small layout="total,prev,pager,next" :total="salesmanProcessed.length"
                        :page-size="pageSize" :current-page="salesmanPage" @current-change="p => salesmanPage = p"
                        class="block-pager" />
                </el-col>
                <el-col :span="14">
                    <div ref="salesmanChart" class="chart-box"></div>
                </el-col>
            </el-row>
        </el-card>

        <!-- 手上未完成订单 -->
        <el-card class="stat-block" shadow="never">
            <template #header>
                <div class="block-header">
                    <span class="block-title">手上未完成订单（按客户）</span>
                    <div class="block-controls">
                        <el-radio-group v-model="unfinishedMetric" size="small">
                            <el-radio-button label="按双数" value="totalPairs" />
                            <el-radio-button label="按订单数" value="orderCount" />
                        </el-radio-group>
                        <el-input v-model="unfinishedSearch" placeholder="搜索客户名" size="small" clearable class="block-search" />
                    </div>
                </div>
            </template>
            <el-row :gutter="20">
                <el-col :span="10">
                    <el-table :data="pageSlice(unfinishedProcessed, unfinishedPage)" border stripe height="360" size="small"
                        @row-click="row => openDetail('customer', row.customerId)" class="clickable-table">
                        <el-table-column type="index" label="#" width="50" :index="i => indexBase(unfinishedPage) + i" />
                        <el-table-column prop="customerName" label="客户名" />
                        <el-table-column prop="customerBrand" label="客户商标" />
                        <el-table-column prop="orderCount" label="未完成订单数" width="110" sortable />
                        <el-table-column prop="totalPairs" label="未完成总双数" width="120" sortable />
                    </el-table>
                    <el-pagination small layout="total,prev,pager,next" :total="unfinishedProcessed.length"
                        :page-size="pageSize" :current-page="unfinishedPage" @current-change="p => unfinishedPage = p"
                        class="block-pager" />
                </el-col>
                <el-col :span="14">
                    <div ref="unfinishedChart" class="chart-box"></div>
                </el-col>
            </el-row>
        </el-card>

        <!-- 近半年热门款式 -->
        <el-card class="stat-block" shadow="never">
            <template #header>
                <div class="block-header">
                    <span class="block-title">近半年下单频率最高的款式（工厂型号）</span>
                    <div class="block-controls">
                        <el-radio-group v-model="hotMetric" size="small">
                            <el-radio-button label="按下单次数" value="orderCount" />
                            <el-radio-button label="按双数" value="totalPairs" />
                        </el-radio-group>
                        <el-input v-model="hotSearch" placeholder="搜索工厂型号" size="small" clearable class="block-search" />
                    </div>
                </div>
            </template>
            <el-row :gutter="20">
                <el-col :span="10">
                    <el-table :data="pageSlice(hotProcessed, hotPage)" border stripe height="360" size="small"
                        @row-click="row => openDetail('shoe', row.shoeRId)" class="clickable-table">
                        <el-table-column type="index" label="排名" width="60" :index="i => indexBase(hotPage) + i" />
                        <el-table-column prop="shoeRId" label="工厂型号" />
                        <el-table-column prop="orderCount" label="下单次数" width="100" sortable />
                        <el-table-column prop="totalPairs" label="总双数" width="100" sortable />
                    </el-table>
                    <el-pagination small layout="total,prev,pager,next" :total="hotProcessed.length"
                        :page-size="pageSize" :current-page="hotPage" @current-change="p => hotPage = p"
                        class="block-pager" />
                </el-col>
                <el-col :span="14">
                    <div ref="hotChart" class="chart-box"></div>
                </el-col>
            </el-row>
        </el-card>

        <!-- 详情弹窗 -->
        <el-dialog v-model="detailVisible" :title="detailTitle" width="70%" top="6vh">
            <div v-loading="detailLoading">
                <div class="detail-summary">
                    <div class="detail-metric"><span>订单总数</span><strong>{{ detailData.orderCount || 0 }}</strong></div>
                    <div class="detail-metric"><span>总双数</span><strong class="pairs">{{ detailData.totalPairs || 0 }}</strong></div>
                    <div class="detail-metric"><span>未完成订单</span><strong class="count">{{ detailData.unfinishedOrderCount || 0 }}</strong></div>
                    <div class="detail-metric"><span>统计区间</span><strong>{{ detailData.periodStart }} ~ {{ detailData.periodEnd }}</strong></div>
                </div>

                <div v-if="detailData.type === 'shoe' && detailData.images && detailData.images.length" class="detail-images">
                    <div v-for="(img, idx) in detailData.images" :key="idx" class="detail-image-item">
                        <el-image :src="img.imageUrl" fit="contain" style="width:120px;height:120px"
                            :preview-src-list="detailData.images.map(i => i.imageUrl)" :initial-index="idx" />
                        <div class="detail-image-color">{{ img.colorName }}</div>
                    </div>
                </div>

                <div class="detail-toolbar">
                    <el-input class="u-w-280" v-model="detailSearch" placeholder="搜索订单号/客户/业务员" size="small" clearable />
                </div>
                <el-table :data="pageSlice(detailProcessed, detailPage)" border stripe size="small" max-height="420">
                    <el-table-column prop="orderRid" label="订单号" />
                    <el-table-column v-if="detailData.type !== 'customer'" prop="customerName" label="客户名" />
                    <el-table-column v-if="detailData.type !== 'salesman'" prop="salesmanName" label="业务员" />
                    <el-table-column prop="totalPairs" label="总双数" width="100" sortable />
                    <el-table-column prop="orderStartDate" label="开始日期" width="120" />
                    <el-table-column label="结束日期" width="130">
                        <template #default="s">
                            <span :style="deliveryDateStyle(s.row.orderEndDate)">{{ s.row.orderEndDate }}</span>
                        </template>
                    </el-table-column>
                    <el-table-column prop="orderStatus" label="订单状态" />
                </el-table>
                <el-pagination small layout="total,prev,pager,next" :total="detailProcessed.length"
                    :page-size="pageSize" :current-page="detailPage" @current-change="p => detailPage = p"
                    class="block-pager" />
            </div>
        </el-dialog>
    </div>
</template>

<script>
import axios from 'axios'
import * as echarts from 'echarts'

export default {
    name: 'BusinessStatistics',
    data() {
        return {
            loading: false,
            period: 'month',
            customRange: null,
            periodStart: '',
            periodEnd: '',
            pageSize: 8,
            customerStats: [],
            salesmanStats: [],
            unfinishedByCustomer: [],
            unfinishedTotalPairs: 0,
            unfinishedOrderCount: 0,
            hotShoes: [],
            customerMetric: 'totalPairs',
            salesmanMetric: 'totalPairs',
            unfinishedMetric: 'totalPairs',
            hotMetric: 'orderCount',
            customerSearch: '',
            salesmanSearch: '',
            unfinishedSearch: '',
            hotSearch: '',
            customerPage: 1,
            salesmanPage: 1,
            unfinishedPage: 1,
            hotPage: 1,
            customerChart: null,
            salesmanChart: null,
            unfinishedChart: null,
            hotChart: null,
            detailVisible: false,
            detailLoading: false,
            detailData: {},
            detailSearch: '',
            detailPage: 1
        }
    },
    computed: {
        rangeLabel() {
            if (this.customRange && this.customRange.length === 2) return '自定义'
            return { week: '近一周', month: '近一月', halfyear: '近半年', year: '近一年' }[this.period] || ''
        },
        detailTitle() {
            const typeLabel = { customer: '客户', salesman: '业务员', shoe: '工厂型号' }[this.detailData.type] || ''
            return `${typeLabel}详情 - ${this.detailData.title || ''}`
        },
        customerProcessed() {
            return this.processList(this.customerStats, this.customerSearch, ['customerName', 'customerBrand'], this.customerMetric)
        },
        salesmanProcessed() {
            return this.processList(this.salesmanStats, this.salesmanSearch, ['salesmanName'], this.salesmanMetric)
        },
        unfinishedProcessed() {
            return this.processList(this.unfinishedByCustomer, this.unfinishedSearch, ['customerName', 'customerBrand'], this.unfinishedMetric)
        },
        hotProcessed() {
            return this.processList(this.hotShoes, this.hotSearch, ['shoeRId'], this.hotMetric)
        },
        detailProcessed() {
            const orders = (this.detailData.orders || [])
            const kw = this.detailSearch.trim().toLowerCase()
            if (!kw) return orders
            return orders.filter(o =>
                String(o.orderRid || '').toLowerCase().includes(kw)
                || String(o.customerName || '').toLowerCase().includes(kw)
                || String(o.salesmanName || '').toLowerCase().includes(kw))
        }
    },
    watch: {
        customerProcessed() { this.customerPage = 1; this.$nextTick(this.renderCharts) },
        salesmanProcessed() { this.salesmanPage = 1; this.$nextTick(this.renderCharts) },
        hotProcessed() { this.hotPage = 1; this.$nextTick(this.renderCharts) },
        unfinishedProcessed() { this.unfinishedPage = 1; this.$nextTick(this.renderCharts) },
        detailProcessed() { this.detailPage = 1 }
    },
    mounted() {
        this.$setAxiosToken()
        this.fetchStatistics()
        window.addEventListener('resize', this.resizeCharts)
    },
    beforeUnmount() {
        window.removeEventListener('resize', this.resizeCharts)
        this.disposeCharts()
    },
    methods: {
        onPeriodChange() {
            this.customRange = null
            this.fetchStatistics()
        },
        onCustomRangeChange(val) {
            if (val && val.length === 2) this.fetchStatistics()
        },
        buildRangeParams() {
            const params = { period: this.period }
            if (this.customRange && this.customRange.length === 2) {
                params.startDate = this.customRange[0]
                params.endDate = this.customRange[1]
            }
            return params
        },
        async fetchStatistics() {
            this.loading = true
            try {
                const response = await axios.get(`${this.$apiBaseUrl}/order/businessstatistics`, {
                    params: this.buildRangeParams()
                })
                const data = response.data
                this.periodStart = data.periodStart
                this.periodEnd = data.periodEnd
                this.customerStats = data.customerStats || []
                this.salesmanStats = data.salesmanStats || []
                this.unfinishedByCustomer = data.unfinishedByCustomer || []
                this.unfinishedTotalPairs = data.unfinishedTotalPairs || 0
                this.unfinishedOrderCount = data.unfinishedOrderCount || 0
                this.hotShoes = data.hotShoes || []
                this.customerPage = this.salesmanPage = this.unfinishedPage = this.hotPage = 1
                this.$nextTick(this.renderCharts)
            } catch (error) {
                this.$message.error('获取统计数据失败')
                console.error(error)
            } finally {
                this.loading = false
            }
        },
        async openDetail(type, key) {
            if (key === undefined || key === null || key === '') return
            this.detailVisible = true
            this.detailLoading = true
            this.detailSearch = ''
            this.detailPage = 1
            this.detailData = { type }
            try {
                const params = this.buildRangeParams()
                params.type = type
                params.key = key
                const response = await axios.get(`${this.$apiBaseUrl}/order/businessstatisticsdetail`, { params })
                this.detailData = response.data
            } catch (error) {
                this.$message.error('获取详情失败')
                console.error(error)
            } finally {
                this.detailLoading = false
            }
        },
        processList(list, search, keyFields, metric) {
            const kw = (search || '').trim().toLowerCase()
            let rows = list
            if (kw) {
                rows = list.filter(item => keyFields.some(f => String(item[f] || '').toLowerCase().includes(kw)))
            }
            return [...rows].sort((a, b) => (b[metric] || 0) - (a[metric] || 0))
        },
        pageSlice(list, page) {
            const start = (page - 1) * this.pageSize
            return list.slice(start, start + this.pageSize)
        },
        indexBase(page) {
            return (page - 1) * this.pageSize
        },
        deliveryDateStyle(endDate) {
            const days = this.daysToDelivery(endDate)
            if (days === null) return {}
            if (days < 15) return { backgroundColor: '#F56C6C', color: '#fff', fontWeight: 'bold', padding: '2px 6px', borderRadius: '4px' }
            if (days < 30) return { backgroundColor: '#E6A23C', color: '#fff', fontWeight: 'bold', padding: '2px 6px', borderRadius: '4px' }
            return {}
        },
        daysToDelivery(endDate) {
            if (!endDate) return null
            const end = new Date(endDate)
            if (isNaN(end.getTime())) return null
            const today = new Date()
            today.setHours(0, 0, 0, 0)
            end.setHours(0, 0, 0, 0)
            return Math.ceil((end - today) / (1000 * 60 * 60 * 24))
        },
        metricLabel(metric) {
            return { totalPairs: '总双数', orderCount: '订单数' }[metric] || ''
        },
        barOption(rows, labelFn, metric, color) {
            const items = rows.slice(0, 15).reverse()
            return {
                tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
                grid: { left: 8, right: 24, top: 24, bottom: 8, containLabel: true },
                xAxis: { type: 'value', name: metric === 'orderCount' ? '订单/下单次数' : '总双数' },
                yAxis: {
                    type: 'category',
                    data: items.map(labelFn),
                    axisLabel: { interval: 0 }
                },
                series: [{
                    type: 'bar',
                    data: items.map(r => r[metric]),
                    itemStyle: { color },
                    label: { show: true, position: 'right' }
                }]
            }
        },
        renderCharts() {
            const customerLabel = r => (r.customerName || '未知') + (r.customerBrand ? `（${r.customerBrand}）` : '')
            this.customerChart = this.ensureChart(this.$refs.customerChart, this.customerChart)
            if (this.customerChart) {
                this.customerChart.setOption(this.barOption(this.customerProcessed, customerLabel, this.customerMetric, '#409EFF'), true)
            }
            this.salesmanChart = this.ensureChart(this.$refs.salesmanChart, this.salesmanChart)
            if (this.salesmanChart) {
                this.salesmanChart.setOption(this.barOption(this.salesmanProcessed, r => r.salesmanName || '未知', this.salesmanMetric, '#67C23A'), true)
            }
            this.unfinishedChart = this.ensureChart(this.$refs.unfinishedChart, this.unfinishedChart)
            if (this.unfinishedChart) {
                this.unfinishedChart.setOption(this.barOption(this.unfinishedProcessed, customerLabel, this.unfinishedMetric, '#F56C6C'), true)
            }
            this.hotChart = this.ensureChart(this.$refs.hotChart, this.hotChart)
            if (this.hotChart) {
                this.hotChart.setOption(this.barOption(this.hotProcessed, r => r.shoeRId || '未知', this.hotMetric, '#E6A23C'), true)
            }
        },
        ensureChart(el, instance) {
            if (!el) return instance
            if (!instance) return echarts.init(el)
            return instance
        },
        resizeCharts() {
            this.customerChart && this.customerChart.resize()
            this.salesmanChart && this.salesmanChart.resize()
            this.unfinishedChart && this.unfinishedChart.resize()
            this.hotChart && this.hotChart.resize()
        },
        disposeCharts() {
            this.customerChart && this.customerChart.dispose()
            this.salesmanChart && this.salesmanChart.dispose()
            this.unfinishedChart && this.unfinishedChart.dispose()
            this.hotChart && this.hotChart.dispose()
            this.customerChart = this.salesmanChart = this.unfinishedChart = this.hotChart = null
        }
    }
}
</script>

<style scoped>
.stat-page {
    padding: 8px 4px;
}

.stat-toolbar {
    margin-top: 16px;
}

.toolbar-wrap {
    display: flex;
    align-items: center;
    gap: 12px;
    flex-wrap: wrap;
}

.toolbar-label {
    font-weight: 600;
}

.toolbar-range {
    color: var(--color-text-3);
    font-size: 13px;
}

.stat-cards {
    margin-top: 16px;
}

.stat-card {
    background: var(--el-fill-color-light);
    border-radius: 8px;
    padding: 18px 20px;
    text-align: center;
}

.stat-card-title {
    color: var(--color-text-2);
    font-size: 14px;
    margin-bottom: 8px;
}

.stat-card-value {
    font-size: 34px;
    font-weight: 700;
}

.stat-card-value.pairs {
    color: var(--el-color-primary);
}

.stat-card-value.count {
    color: var(--color-warning);
}

.stat-block {
    margin-top: 18px;
}

.block-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 8px;
}

.block-title {
    font-size: 16px;
    font-weight: 600;
}

.block-controls {
    display: flex;
    align-items: center;
    gap: 10px;
}

.block-search {
    width: 160px;
}

.block-pager {
    margin-top: 8px;
    justify-content: flex-end;
}

.chart-box {
    width: 100%;
    height: 360px;
}

.clickable-table :deep(.el-table__row) {
    cursor: pointer;
}

.detail-summary {
    display: flex;
    gap: 32px;
    flex-wrap: wrap;
    margin-bottom: 12px;
}

.detail-metric {
    display: flex;
    flex-direction: column;
}

.detail-metric span {
    color: var(--color-text-3);
    font-size: 12px;
}

.detail-metric strong {
    font-size: 20px;
}

.detail-metric strong.pairs {
    color: var(--el-color-primary);
}

.detail-metric strong.count {
    color: var(--color-warning);
}

.detail-images {
    display: flex;
    gap: 16px;
    flex-wrap: wrap;
    margin-bottom: 12px;
}

.detail-image-item {
    text-align: center;
    border: 1px solid var(--el-border-color-lighter);
    border-radius: 6px;
    padding: 6px;
}

.detail-image-color {
    font-size: 12px;
    color: var(--color-text-2);
    margin-top: 4px;
}

.detail-toolbar {
    margin-bottom: 8px;
}
</style>
