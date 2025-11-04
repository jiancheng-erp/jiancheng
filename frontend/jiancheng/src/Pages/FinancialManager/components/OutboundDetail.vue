<template>
    <el-row>
        <el-col>
            <div style="display: flex; align-items: center; gap: 10px;">
                <el-input v-if="detailOrSummary == true" v-model="outboundRIdFilter" placeholder="出库单号搜索" clearable @change="updateOutboundDisplayRecord"
                    style="width: 200px;"></el-input>
                <!-- <el-select v-model="currentWarehouse" clearable filterable @change="updateOutboundDisplayRecord"
                    placeholder="仓库搜索" style="width: 200px;">
                    <el-option v-for="item in warehouseOptions" :key="item.warehouseId" :label="item.warehouseName"
                        :value="item.warehouseId">
                    </el-option>
                </el-select> -->
                <el-input v-model="supplierNameFilter" placeholder="供应商搜索" clearable
                    @change="updateOutboundDisplayRecord" style="width: 200px;"></el-input>
                <el-select v-model="outboundTypeFilter" multiple clearable @change="updateOutboundDisplayRecord"
                    placeholder="出库类型搜索" style="width: 300px;">
                    <el-option v-for="item in outboundTypeOptions" :key="item.value" :label="item.label"
                        :value="item.value">
                    </el-option>
                </el-select>
                <el-date-picker v-model="dateRangeFilter" type="daterange"
                    value-format="YYYY-MM-DD" unlink-panels range-separator="至" start-placeholder="时间范围起始"
                    end-placeholder="时间范围结束" size="default" clearable @change="updateOutboundDisplayRecord"
                    @clear="updateOutboundDisplayRecord" style="width: 200px;" />
            </div>

        </el-col>
    </el-row>
    <el-row :gutter="20">
        <el-col>
            <div style="display: flex; align-items: center; gap: 10px;">
                <el-input v-model="materialNameFilter" placeholder="材料名称搜索" clearable
                    @change="updateOutboundDisplayRecord" style="width: 200px;"></el-input>
                <el-input v-model="materialModelFilter" placeholder="材料型号搜索" clearable
                    @change="updateOutboundDisplayRecord" style="width: 200px;"></el-input>
                <el-input v-model="materialSpecificationFilter" placeholder="材料规格搜索" clearable
                    @change="updateOutboundDisplayRecord" style="width: 200px;"></el-input>
                <el-input v-model="materialColorFilter" placeholder="材料颜色搜索" clearable
                    @change="updateOutboundDisplayRecord" style="width: 200px;"></el-input>
                <!-- <el-input v-model="orderRidFilter" placeholder="订单号搜索" clearable
                    @change="updateOutboundDisplayRecord" style="width: 200px;"></el-input> -->
                <el-select v-model="statusFilter" multiple style="width:200px;"
                    placeholder="审核状态搜索" clearable
                    @change="updateOutboundDisplayRecord">
                    <el-option v-for="statusOption in statusFilterOptions"
                    :key="statusOption.key"
                    :label="statusOption.label"
                    :value="statusOption.key"></el-option>
                </el-select>
                <!-- <el-button type="primary" @click="createAndDownloadOutboundExcel">生成并下载excel</el-button> -->
            </div>

        </el-col>
    </el-row>
    <el-row :gutter="20">
        < <el-checkbox-group v-model="checkedColumnValues" @change="updateCheckBox">
            <el-checkbox-button v-for="col in allColumns" :key="col.id" :value="col.id">
                {{ col.labelName }}
            </el-checkbox-button>
            </el-checkbox-group>
    </el-row>


    <el-row :gutter="20">
        <el-table :data="displayRecords" border stripe style="width: 90vw; height: 60vh;">
            <el-table-column v-for="col in selectedColumns" :prop="col.attrName" :key="col.id" :label="col.labelName">
            </el-table-column>
        </el-table>
    </el-row>

    <el-row :gutter="20">
        <<el-pagination @size-change="pageSizeChange" @current-change="pageCurrentChange" :current-page="currentPage"
            :page-sizes="[10, 20, 40, 80, 100]" :page-size="pageSize" layout="total, sizes, prev, pager, next, jumper"
            :total="totalNum" background>
            :pager-count="7">
            </el-pagination>
    </el-row>



</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { ref, onMounted, getCurrentInstance } from 'vue'
import axios from 'axios'
import useSetAxiosToken from '../hooks/useSetAxiosToken'
import { ElRow } from 'element-plus'


const { setAxiosToken } = useSetAxiosToken()
const router = useRouter()
const currentPage = ref(1)
const pageSize = ref(20)
const currentWarehouse = ref('')
const displayRecords = ref([])
const totalNum = ref(0)
const checkedColumnValues = ref([])
const selectedColumns = ref([])
const allColumns = ref([])
const dateRangeFilter = ref(['', ''])
const supplierNameFilter = ref('')
const outboundTypeFilter = ref('')
const outboundTypeOptions = ref([
    {
        key: 0,
        value: '0',
        label: "自产出库"
    },
    {
        key: 1,
        value: '1',
        label: '废料出库'
    },
    {
        key: 2,
        value: '2',
        label: '外包出库'
    },
    {
        key: 3,
        value: '3',
        label: '复合出库'
    },
    {
        key: 4,
        value: '4',
        label: '材料退回'
    },
    {
        key: 5,
        value: '5',
        label: '盘库出库'
    },
])
interface WarehouseEntity {
    warehouseId: number
    warehouseName: string
}
let warehouseOptions = ref([])
const detailOrSummary = ref(true)
const outboundRIdFilter = ref('')
const materialNameFilter = ref('')
const materialModelFilter = ref('')
const materialSpecificationFilter = ref('')
const materialColorFilter = ref('')
const orderRidFilter = ref('')
const statusFilter = ref([])
const statusFilterOptions = ref([
    {
        key:0,
        value:'0',
        label:'待审核'
    },
    {
        key:1,
        value:'1',
        label:'已审核'
    },
    {
        key:2,
        value:'2',
        label:'已驳回'
    },
])


const $api_baseUrl = getCurrentInstance().appContext.config.globalProperties.$apiBaseUrl

onMounted(async () => {
    getWarehouseInfo()
    await getSelectableColumns()
    selectAllColumns()
    updateOutboundDisplayRecord()
    console.log(warehouseOptions.value)
})

function updateCheckBox() {
    console.log(checkedColumnValues.value)
    let temp = []
    allColumns.value.forEach(element => {
        checkedColumnValues.value.forEach(element2 => {
            if (element.id == element2) {
                temp.push(element)
            }
        });
    });
    selectedColumns.value = temp;
    console.log(selectedColumns.value)
}
function getCurrentPageInfo() {
    if (dateRangeFilter.value == null) {
        dateRangeFilter.value = ['', '']
    }

    return {
        'pageNumber': currentPage.value,
        'pageSize': pageSize.value,
        'selectedWarehouse': currentWarehouse.value,
        'dateRangeFilterStart': dateRangeFilter.value[0],
        'dateRangeFilterEnd': dateRangeFilter.value[1],
        'supplierNameFilter': supplierNameFilter.value,
        'outboundTypeFilter': outboundTypeFilter.value,
        'outboundRIdFilter': outboundRIdFilter.value,
        'auditStatusFilter': statusFilter.value,
        'materialNameFilter': materialNameFilter.value,
        "materialModelFilter": materialModelFilter.value,
        "materialSpecificationFilter": materialSpecificationFilter.value,
        "materialColorFilter": materialColorFilter.value
    }
}
function pageSizeChange(newSize) {
    pageSize.value = newSize
    updateOutboundDisplayRecord()
}
async function pageCurrentChange(page) {
    currentPage.value = page
    await updateOutboundDisplayRecord()
}
async function paginationChange() {
    await updateOutboundDisplayRecord()
}
async function getSelectableColumns() {
    const res = await axios.get($api_baseUrl + `/accounting/get_outbound_display_columns`)
    allColumns.value = res.data.selectableColumns
    console.log(allColumns.value)
    console.log(res.data.selectableColumns)
}
async function updateOutboundDisplayRecord() {
    const apiParams = getCurrentPageInfo()
    console.log("update out records")
    console.log(apiParams)
    const res = await axios.get($api_baseUrl + `/accounting/get_warehouse_outbound_record`
        , { params: apiParams }
    )
    totalNum.value = res.data.total
    displayRecords.value = res.data.outboundRecords
}
function deselectAllColumns() {
    checkedColumnValues.value = []
    updateCheckBox()
}
function selectAllColumns() {
    checkedColumnValues.value = allColumns.value.map((col) => col.id)
    updateCheckBox()
}
async function getWarehouseInfo() {
    const res = await axios.get($api_baseUrl + `/accounting/get_warehouse_info`)
    warehouseOptions.value = res.data.warehouseInfo
}

async function filterByDate() {
    console.log(dateRangeFilter.value)
    const apiParams = getCurrentPageInfo()
    console.log(apiParams)
}
</script>
<style></style>
