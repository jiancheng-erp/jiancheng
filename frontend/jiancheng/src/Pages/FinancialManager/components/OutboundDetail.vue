<template>
    <!-- <el-tabs style="">
        <el-tab-pane label="入库记录">

        </el-tab-pane>
        <el-tab-pane lable="出库记录">

        </el-tab-pane>
    </el-tabs> -->

    <el-row >
        <el-col :span="4" :offset="0">
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
        <el-col :span="2" :offset="1">
            <el-select v-model="outboundTypeFilter" 
            placeholder="出库类型选择" clearable @change="updateInboundDisplayRecord">
            <el-option v-for="option in outboundTypeOptions" :key="option.key" :label="option.label" :value="option.value">

            </el-option>
        </el-select>
        </el-col>
        <el-col :span="4" :offset="1">
            <el-input v-model="supplierNameFilter" placeholder="材料供应商搜索" clearable @change="updateInboundDisplayRecord"></el-input>
        </el-col>

           <el-col :span="4" :offset="2">
            <el-button type="primary" @click="deselectAllColumns">
                清空选择
            </el-button>
            <el-button @click="selectAllColumns">
                全选
            </el-button>
        </el-col>
        
    </el-row>

 
    
    <el-row :gutter="20">
        < <el-checkbox-group v-model="checkedColumnValues"  @change="updateCheckBox">
        <el-checkbox-button v-for="col in allColumns" :key="col.id" :value="col.id">
            {{col.labelName}}
        </el-checkbox-button>
    </el-checkbox-group>
    </el-row>
    
   
    <el-row :gutter="20">
        <el-table :data="displayRecords" border stripe style="width: 90vw; height: 60vh;">
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
const outboundTypeFilter = ref('')
const outboundTypeOptions = ref([
    {
        key:0,
        value:'0',
        label:"自产出库"
    },
    {
        key:1,
        value:'1',
        label:'废料出库'
    },
    {
        key:2,
        value:'2',
        label:'外包出库'
    },
    {
        key:3,
        value:'3',
        label:'复合出库'
    }
])
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

onMounted(async () => {
    getWarehouseInfo()
    await getSelectableColumns()
    selectAllColumns()
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
            'supplierNameFilter':supplierNameFilter.value,
            'outboundTypeFilter':outboundTypeFilter.value
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
function deselectAllColumns() {
    checkedColumnValues.value = []
    updateCheckBox()
}
function selectAllColumns() {
    checkedColumnValues.value = allColumns.value.map((col) => col.id)
    updateCheckBox()
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


