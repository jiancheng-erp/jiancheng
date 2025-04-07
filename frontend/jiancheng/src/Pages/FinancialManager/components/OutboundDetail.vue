<template>
    <!-- <el-tabs style="">
        <el-tab-pane label="入库记录">

        </el-tab-pane>
        <el-tab-pane lable="出库记录">

        </el-tab-pane>
    </el-tabs> -->

    <el-row >
        <el-col :span="4" :offset="0">
            <el-select v-model="currentWarehouse" clearable filterable @change="updateInboundDisplayRecord">
            <el-option v-for="item in warehouseOptions"
            :key="item.warehouseId"
            :label="item.warehouseName"
            :value="item.warehouseId">
            </el-option>
            </el-select>
        </el-col>

        <el-col :span="4" :offset="1">
            <el-input v-model="supplierNameFilter" placeholder="供应商搜索" size="normal" clearable @change="updateInboundDisplayRecord"></el-input>
        </el-col>
        
        <el-col :span="4" :offset="1">
            <el-date-picker
                v-model="dateRangeFilter"
                type="daterange"
                value-format="YYYY-MM-DD"
                unlink-panels
                range-separator="至"
                start-placeholder="时间范围起始"
                end-placeholder="时间范围结束"
                size="default"
                clearable
                @change="updateInboundDisplayRecord"
                @clear="updateInboundDisplayRecord"
            />
            

        </el-col>
        
        
    </el-row>

    <!-- <<el-row :gutter="20">
        <el-col :span="12" :offset="0"></el-col>
            <el-option v-for="selectedWarehouse in warehouseOptions" :key="selectedWarehouse.warehouseId" :label="selectedWarehouse.warehouseName" 
            :value="selectedWarehouse.warehouseId"></el-option>
            
        <el-col :span="12" :offset="0"></el-col>
    </el-row>
     -->
    
    
    <el-row :gutter="20">
        < <el-checkbox-group v-model="checkedColumnValues" size="normal"  @change="updateCheckBox">
        <el-checkbox-button v-for="col in allColumns" :key="col.id" :label="col.id">
            {{col.labelName}}
        </el-checkbox-button>
    </el-checkbox-group>
    </el-row>
    
   
    <el-row :gutter="20">
        <el-table :data="displayRecords" border stripe>
        <el-table-column v-for="col in selectedColumns"
            :prop="col.attrName"
            :key="col.id"
            :label="col.labelName"
            >
        </el-table-column>
            <!-- <el-table-column label="abc" prop="attrname"></el-table-column> -->
        
        </el-table>
    </el-row>
    
    <el-row :gutter="20">
        <<el-pagination
        @size-change="pageSizeChange"
        @current-change="pageCurrentChange"
        :current-page="currentPage"
        :page-sizes="[10, 20, 40, 80, 100]"
        :page-size="pageSize"
        layout="total, sizes, prev, pager, next, jumper"
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
const dateRangeFilter = ref(['',''])
const supplierNameFilter = ref('')
// const shortcuts: [
//                 {
//                     text: '过去一周',
//                     value: () => {
//                         const end = new Date()
//                         const start = new Date()
//                         start.setTime(start.getTime() - 3600 * 1000 * 24 * 7)
//                         return [start, end]
//                     }
//                 },
//                 {
//                     text: '过去一月',
//                     value: () => {
//                         const end = new Date()
//                         const start = new Date()
//                         start.setTime(start.getTime() - 3600 * 1000 * 24 * 30)
//                         return [start, end]
//                     }
//                 }
//             ]
interface WarehouseEntity{
    warehouseId:number
    warehouseName:string
}
let warehouseOptions = ref([])


const $api_baseUrl = getCurrentInstance().appContext.config.globalProperties.$apiBaseUrl

onMounted(() => {
    getWarehouseInfo()
    getSelectableColumns()
    updateInboundDisplayRecord()
    console.log(warehouseOptions.value)
})

function updateCheckBox(){
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
function getCurrentPageInfo()
{
    if (dateRangeFilter.value == null){
        dateRangeFilter.value = ['', '']
    }

    return {'pageNumber':currentPage.value,
            'pageSize':pageSize.value,
            'selectedWarehouse':currentWarehouse.value,
            'dateRangeFilterStart':dateRangeFilter.value[0],
            'dateRangeFilterEnd':dateRangeFilter.value[1],
            'supplierNameFilter':supplierNameFilter.value
    }
}
function pageSizeChange(newSize)
{
    pageSize.value = newSize
    updateInboundDisplayRecord()
}
async function pageCurrentChange(page)
{
    currentPage.value = page
    await updateInboundDisplayRecord()
}
async function paginationChange(){
    console.log("pagination change")
    console.log(getCurrentPageInfo())
    await updateInboundDisplayRecord()
}
async function getSelectableColumns()
{
    const res = await axios.get($api_baseUrl + `/accounting/get_outbound_display_columns`)
    allColumns.value = res.data.selectableColumns
    console.log(allColumns.value)
    console.log(res.data.selectableColumns)
}
async function updateInboundDisplayRecord()
{
    const apiParams = getCurrentPageInfo()
    console.log("update out records")
    console.log(apiParams)
    const res = await axios.get($api_baseUrl + `/accounting/get_warehouse_outbound_record`
        ,{params:apiParams}
    )
    totalNum.value = res.data.total
    displayRecords.value = res.data.outboundRecords
}

async function getWarehouseInfo()
{
    const res = await axios.get($api_baseUrl + `/accounting/get_warehouse_info`)
    warehouseOptions.value = res.data.warehouseInfo
}

async function filterByDate(){
    console.log(dateRangeFilter.value)
    const apiParams = getCurrentPageInfo()
    console.log(apiParams)
}
</script>
<style>

    
</style>


