<template>
    <!-- 统计卡片 -->
    <el-row :gutter="20" style="margin-top: 20px">
        <el-col :span="6" v-for="item in statisticList" :key="item.title">
            <el-card shadow="hover" style="border-radius: 12px; text-align: center">
                <el-statistic :title="item.title" :value="item.value" :prefix-icon="item.icon" />
            </el-card>
        </el-col>
    </el-row>

    <!-- 图表区域 -->
    <el-row :gutter="20" style="margin-top: 30px">
        <el-col :span="12">
            <el-card shadow="hover" style="border-radius: 12px">
                <div style="font-weight: bold; margin-bottom: 10px">订单状态业务流程</div>
                <div ref="businessChartRef" style="width: 100%; height: 225px" />
            </el-card>
        </el-col>
        <el-col :span="12">
            <el-card shadow="hover" style="border-radius: 12px">
                <div style="font-weight: bold; margin-bottom: 10px">订单状态生产流程</div>
                <div ref="productionChartRef" style="width: 100%; height: 225px" />
            </el-card>
        </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px">
        <el-col :span="12">
            <el-card shadow="hover" style="border-radius: 12px">
                <div style="font-weight: bold; margin-bottom: 10px">近期每月订单数变化</div>
                <div ref="monthlyOrderLineChartRef" style="width: 100%; height: 225px" />
            </el-card>
        </el-col>
        <el-col :span="12">
            <el-card shadow="hover" style="border-radius: 12px">
                <div style="font-weight: bold; margin-bottom: 10px">各阶段排产月度数量</div>
                <div ref="productionStageChartRef" style="width: 100%; height: 225px" />
            </el-card>
        </el-col>
    </el-row>
</template>

<script setup>
import { ref, onMounted, getCurrentInstance } from 'vue'
import * as echarts from 'echarts'
import axios from 'axios'
const $api_baseUrl = getCurrentInstance().appContext.config.globalProperties.$apiBaseUrl
let statisticList = ref([])

const businessChartRef = ref(null)
const productionChartRef = ref(null)
const businessChartData = ref([])
const productionChartData = ref([])
async function getStatisticListValue() {
    const response = await axios.get(`${$api_baseUrl}/headmanager/getdashboardstatistic`)
    statisticList.value = response.data.map((item) => ({
        title: item.title,
        value: item.value
    }))
}
async function getBusinessChartData() {
    const response = await axios.get(`${$api_baseUrl}/headmanager/businessorderstatuspiechartoption`)
    businessChartData.value = response.data
}
async function getProductionChartData() {
    const response = await axios.get(`${$api_baseUrl}/headmanager/productionorderstatuspieoption`)
    productionChartData.value = response.data
}

const renderPieChart = (dom, title, data) => {
    const chart = echarts.init(dom)
    chart.setOption({
        title: {
            text: title,
            left: 'center',
            top: 10,
            textStyle: {
                fontSize: 14
            }
        },
        tooltip: {
            trigger: 'item'
        },
        legend: {
            bottom: 0,
            left: 'center'
        },
        series: [
            {
                type: 'pie',
                radius: '50%',
                data,
                emphasis: {
                    itemStyle: {
                        shadowBlur: 10,
                        shadowOffsetX: 0,
                        shadowColor: 'rgba(0, 0, 0, 0.3)'
                    }
                }
            }
        ]
    })
}
const renderLineChart = (dom, title, xData, yData) => {
    const chart = echarts.init(dom)
    chart.setOption({
        title: {
            text: title,
            left: 'center',
            top: 10,
            textStyle: {
                fontSize: 14
            }
        },
        tooltip: {
            trigger: 'axis'
        },
        xAxis: {
            type: 'category',
            data: xData
        },
        yAxis: {
            type: 'value',
            name: '数量'
        },
        series: [
            {
                name: '订单数量',
                type: 'line',
                smooth: true,
                data: yData
            }
        ]
    })
}
const renderMultiLineChart = (dom, title, xData, seriesList) => {
  const chart = echarts.init(dom)
  chart.setOption({
    title: {
      text: title,
      left: 'center',
      top: 10,
      textStyle: { fontSize: 14 }
    },
    tooltip: {
      trigger: 'axis'
    },
    legend: {
      top: 'top'
    },
    xAxis: {
      type: 'category',
      data: xData
    },
    yAxis: {
      type: 'value',
      name: '数量'
    },
    series: seriesList.map(item => ({
      name: item.name,
      type: 'line',
      smooth: true,
      data: item.data
    }))
  })
}
const monthlyOrderLineChartRef = ref(null)

async function getMonthlyOrderData() {
    const response = await axios.get(`${$api_baseUrl}/headmanager/newordermonthlylinechart`)
    const rawData = response.data

    const now = new Date()
    const currentMonth = now.getMonth() + 1 // JS中是0-based，所以要+1

    const xData = Array.from({ length: currentMonth }, (_, i) => `${i + 1}月`)
    const countMap = Object.fromEntries(rawData.map((item) => [item.month, item.orderCount]))
    const yData = Array.from({ length: currentMonth }, (_, i) => countMap[i + 1] || 0)

    renderLineChart(monthlyOrderLineChartRef.value, '', xData, yData)
}
const productionStageChartRef = ref(null)
async function getProductionStageLineData () {
  const response = await axios.get(`${$api_baseUrl}/headmanager/scheduleproductionordermothlylinechart`)
  const rawData = response.data

  const xData = Array.from({ length: 12 }, (_, i) => `${i + 1}月`)
  const monthIndexMap = Object.fromEntries(xData.map((label, i) => [i + 1, label]))

  const cuttingData = []
  const presewingData = []
  const sewingData = []
  const moldingData = []

  for (let i = 1; i <= 12; i++) {
    const monthData = rawData.find(item => item.month === i) || {}
    cuttingData.push(monthData.cutting || 0)
    presewingData.push(monthData.presewing || 0)
    sewingData.push(monthData.sewing || 0)
    moldingData.push(monthData.molding || 0)
  }

  renderMultiLineChart(
    productionStageChartRef.value,
    '',
    xData,
    [
      { name: '裁断', data: cuttingData },
      { name: '针车预备', data: presewingData },
      { name: '针车', data: sewingData },
      { name: '成型', data: moldingData }
    ]
  )
}

onMounted(() => {
    getStatisticListValue()
    getBusinessChartData().then(() => {
        renderPieChart(businessChartRef.value, '', businessChartData.value)
    })
    getProductionChartData().then(() => {
        renderPieChart(productionChartRef.value, '', productionChartData.value)
    })
    getMonthlyOrderData()
    getProductionStageLineData()
})
</script>
