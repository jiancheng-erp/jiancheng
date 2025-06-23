<template>
    <div class="content">
        <div>
            <el-date-picker
                v-model="timeValue"
                type="datetimerange"
                start-placeholder="开始时间"
                end-placeholder="结束时间"
                format="YYYY-MM-DD HH:mm:ss"
                date-format="YYYY/MM/DD ddd"
                time-format="A hh:mm:ss"
                style="height: 40px"
                :default-time="defaultTime"
            />
            <el-button
                type="primary"
                size="middle"
                style="margin-left: 50px"
                @click="filterData(timeValue)"
                >筛选</el-button
            >
        </div>
        <div
            :id="'histroyTrend_' + materialName"
            class="historyTrend"
            style="
                width: 100%;
                height: 90%;
                display: flex;
                justify-content: center;
                align-items: center;
            "
        ></div>
    </div>
</template>

<script setup>
import { onMounted, watch, ref, nextTick, getCurrentInstance, onUnmounted } from 'vue'
import useHistoryMaterial from '../../hooks/useHistoryMaterial'
import * as echarts from 'echarts'

const { materialStorageId, materialType, materialName, spuMaterialId } = defineProps([
    'materialStorageId',
    'materialType',
    'materialName',
    'spuMaterialId'
])

const { materialData, getMaterialData } = useHistoryMaterial()

const defaultTime = ref([])
let dataArr
let timeValue = ref('')
const $api_baseUrl = getCurrentInstance().appContext.config.globalProperties.$apiBaseUrl
const routeMsg = `${$api_baseUrl}/headmanager/getmaterialinboundcurve`

let myChart

const resizeFun = () => {
        nextTick(() => {
            myChart.resize()
        })
    }
onMounted(() => {
    getMaterialData({ materialStorageId, materialType, spuMaterialId, routeMsg })
    window.addEventListener('resize', resizeFun)
})
onUnmounted(() => {
    window.removeEventListener('resize', resizeFun)
});

watch(
    () => materialData,
    () => {
        dataArr = materialData.value
        // 基于准备好的dom，初始化echarts实例
        let chartDom = document.getElementById('histroyTrend_' + materialName)
        if (!echarts.getInstanceByDom(chartDom)) {
            myChart = echarts.init(chartDom)
        } else {
            myChart = echarts.getInstanceByDom(chartDom)
        }
        updateChart(materialData.value)
    },
    { deep: true }
)

function updateChart(materialData) {
    let xAxisData = []
    let yAxisData = []
    let startTime = stringToDate(materialData[0].date)
    let endTime = stringToDate(materialData[materialData.length - 1].date)
    defaultTime.value.splice(0, 1, startTime)
    defaultTime.value.splice(1, 1, endTime)
    for (let i = 0; i < materialData.length; i++) {
        xAxisData.push(materialData[i].date)
        yAxisData.push(materialData[i].unitPrice)
    }
    // 绘制图表
    myChart.setOption({
        xAxis: {
            type: 'category',
            data: xAxisData,
            name: '时间'
        },
        yAxis: {
            type: 'value',
            name: '单价'
        },
        series: [
            {
                data: yAxisData,
                type: 'line',
                name: '单价'
            }
        ],
        //简单的在图表配置中添加这个工具配置
        toolbox: {
            show: true,
            feature: {
                saveAsImage: {}
            }
        },

        tooltip: {
            trigger: 'axis',
            // 可以在这里添加更多 tooltip 配置
            axisPointer: {
                type: 'cross',
                label: {
                    backgroundColor: '#6a7985'
                }
            }
        }
    })
}

function filterData(timeValue) {
    if (timeValue === null) {
        updateChart(materialData.value)
        return
    }
    const data = materialData.value
    let array = []
    for (let i = 0; i < data.length; i++) {
        if (
            stringToDate(data[i].date) >= timeValue[0] &&
            stringToDate(data[i].date) <= timeValue[1]
        ) {
            array.push(data[i])
        }
    }
    updateChart(array)
}
function stringToDate(dateStr, separator) {
    if (!separator) {
        separator = '-'
    }
    var dateArr = dateStr.split(separator)
    var year = parseInt(dateArr[0])
    var month
    if (dateArr[1].indexOf('0') == 0) {
        month = parseInt(dateArr[1].substring(1))
    } else {
        month = parseInt(dateArr[1])
    }
    var day = parseInt(dateArr[2])
    var date = new Date(year, month - 1, day)
    return date
}
</script>

<style scoped>
.content {
    display: flex;
    width: 100%;
    height: 90%;
    justify-content: center;
    align-items: center;
    flex-direction: column;
}
.historyTrend > div {
    width: 100% !important;
    height: 100% !important;
}
</style>
