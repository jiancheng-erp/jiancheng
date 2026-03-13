<template>
    <div class="linger-dashboard">
        <el-row :gutter="16" class="toolbar-row">
            <el-col :span="8">
                <div class="toolbar-label">滞留阶段筛选</div>
                <el-select v-model="lingerStageValue" clearable filterable placeholder="全部阶段" @change="loadDashboard">
                    <el-option v-for="item in stageOptions" :key="item.value" :label="item.label" :value="item.value" />
                </el-select>
            </el-col>
            <el-col :span="6">
                <div class="toolbar-label">最少滞留天数</div>
                <el-input-number v-model="minStayDays" :min="0" :step="1" @change="loadDashboard" />
            </el-col>
            <el-col :span="4" class="toolbar-action">
                <el-button type="primary" @click="loadDashboard">刷新看板</el-button>
            </el-col>
        </el-row>

        <el-row :gutter="16" class="summary-row">
            <el-col v-for="item in summary" :key="item.title" :span="6">
                <el-card shadow="hover" class="summary-card">
                    <div class="summary-title">{{ item.title }}</div>
                    <div class="summary-value">{{ item.value }}</div>
                </el-card>
            </el-col>
        </el-row>

        <el-row :gutter="16" class="chart-row">
            <el-col :span="12">
                <el-card shadow="hover" class="panel-card">
                    <template #header>阶段滞留分布</template>
                    <div ref="stageChartRef" class="chart-box" />
                </el-card>
            </el-col>
            <el-col :span="12">
                <el-card shadow="hover" class="panel-card">
                    <template #header>订单/鞋型滞留占比</template>
                    <div ref="typeChartRef" class="chart-box" />
                </el-card>
            </el-col>
        </el-row>

        <el-row :gutter="16" class="table-row">
            <el-col :span="24">
                <el-card shadow="hover" class="panel-card">
                    <template #header>滞留排行 Top 20</template>
                    <el-table :data="topRecords" border stripe height="320">
                        <el-table-column prop="orderRid" label="订单号" width="140" />
                        <el-table-column prop="customerName" label="客人名称" min-width="140" />
                        <el-table-column prop="lingerStageType" label="类型" width="100" />
                        <el-table-column prop="lingerStage" label="滞留阶段" min-width="180" />
                        <el-table-column prop="shoeRid" label="工厂型号" width="140" />
                        <el-table-column prop="lingerSince" label="进入时间" width="180" />
                        <el-table-column prop="delayText" label="滞留时长" width="100" />
                    </el-table>
                </el-card>
            </el-col>
        </el-row>

        <el-row :gutter="16" class="table-row">
            <el-col :span="24">
                <el-card shadow="hover" class="panel-card">
                    <template #header>全部滞留明细</template>
                    <el-table :data="records" border stripe height="420">
                        <el-table-column prop="orderRid" label="订单号" width="140" />
                        <el-table-column prop="customerName" label="客人名称" min-width="140" />
                        <el-table-column prop="lingerStageType" label="类型" width="100" />
                        <el-table-column prop="lingerStage" label="滞留阶段" min-width="180" />
                        <el-table-column prop="shoeRid" label="工厂型号" width="140" />
                        <el-table-column prop="customerProductName" label="客户型号" min-width="140" />
                        <el-table-column prop="lingerSince" label="进入时间" width="180" />
                        <el-table-column prop="delayText" label="滞留时长" width="100" />
                    </el-table>
                </el-card>
            </el-col>
        </el-row>
    </div>
</template>

<script setup>
import { ref, onMounted, nextTick, getCurrentInstance } from 'vue'
import axios from 'axios'
import * as echarts from 'echarts'

const { appContext } = getCurrentInstance()
const apiBaseUrl = appContext.config.globalProperties.$apiBaseUrl

const stageOptions = ref([])
const lingerStageValue = ref('')
const minStayDays = ref(0)
const summary = ref([])
const topRecords = ref([])
const records = ref([])

const stageChartRef = ref(null)
const typeChartRef = ref(null)

let stageChart = null
let typeChart = null

const defaultSummary = [
    { title: '滞留总数', value: 0 },
    { title: '订单阶段滞留', value: 0 },
    { title: '鞋型阶段滞留', value: 0 },
    { title: '超7天', value: 0 },
]

async function loadStageOptions() {
    const response = await axios.get(`${apiBaseUrl}/order/getordershoestatusoptions`)
    stageOptions.value = response.data.options || []
}

function renderStageChart(data) {
    if (!stageChartRef.value) {
        return
    }
    if (stageChart) {
        stageChart.dispose()
    }
    stageChart = echarts.init(stageChartRef.value)
    stageChart.setOption({
        tooltip: { trigger: 'axis' },
        grid: { left: 48, right: 20, top: 20, bottom: 80 },
        xAxis: {
            type: 'category',
            data: data.map((item) => item.name),
            axisLabel: { rotate: 30, interval: 0 },
        },
        yAxis: { type: 'value', name: '数量' },
        series: [
            {
                type: 'bar',
                data: data.map((item) => item.value),
                itemStyle: {
                    color: '#1f7a8c',
                    borderRadius: [6, 6, 0, 0],
                },
            },
        ],
    })
}

function renderTypeChart(data) {
    if (!typeChartRef.value) {
        return
    }
    if (typeChart) {
        typeChart.dispose()
    }
    typeChart = echarts.init(typeChartRef.value)
    typeChart.setOption({
        tooltip: { trigger: 'item' },
        legend: { bottom: 0 },
        series: [
            {
                type: 'pie',
                radius: ['45%', '72%'],
                data,
                label: { formatter: '{b}: {c}' },
            },
        ],
    })
}

async function loadDashboard() {
    const response = await axios.get(`${apiBaseUrl}/order/getlingerdashboard`, {
        params: {
            lingerStageValue: lingerStageValue.value,
            minStayDays: minStayDays.value,
        },
    })
    summary.value = response.data.summary?.length ? response.data.summary : defaultSummary
    topRecords.value = response.data.topRecords || []
    records.value = response.data.records || []

    await nextTick()
    renderStageChart(response.data.stageDistribution || [])
    renderTypeChart(response.data.typeDistribution || [])
}

onMounted(async () => {
    await loadStageOptions()
    await loadDashboard()
})
</script>

<style scoped>
.linger-dashboard {
    padding: 8px 4px 20px;
}

.toolbar-row,
.summary-row,
.chart-row,
.table-row {
    margin-top: 16px;
}

.toolbar-label {
    margin-bottom: 8px;
    font-size: 13px;
    color: #4b5563;
}

.toolbar-action {
    display: flex;
    align-items: end;
}

.summary-card {
    border-radius: 12px;
}

.summary-title {
    font-size: 13px;
    color: #6b7280;
}

.summary-value {
    margin-top: 10px;
    font-size: 28px;
    font-weight: 700;
    color: #0f172a;
}

.panel-card {
    border-radius: 12px;
}

.chart-box {
    width: 100%;
    height: 320px;
}
</style>