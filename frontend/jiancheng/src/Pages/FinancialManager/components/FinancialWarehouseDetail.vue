<template>
    <el-row :gutter="20">
        <<el-select v-model="currentWarehouse" clearable filterable @change="updateDisplayRecord">
        <el-option v-for="item in warehouseOptions"
            :key="item.warehouseId"
            :label="item.warehouseName"
            :value="item.warehouseId">
        </el-option>
    </el-select>
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
        :page-sizes="[20, 40, 80, 100]"
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
const displayRecords = ref([{"id":"1","name":"b"}])
const totalNum = ref(0)
const checkedColumnValues = ref([])
const selectedColumns = ref([])
const allColumns = ref([])
interface WarehouseEntity{
    warehouseId:number
    warehouseName:string
}
let warehouseOptions = ref([{'warehouseId':1, 'warehouseName':'a'}])


const $api_baseUrl = getCurrentInstance().appContext.config.globalProperties.$apiBaseUrl

onMounted(() => {
    getWarehouseInfo()
    getSelectableColumns()
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
    return {'pageNumber':currentPage.value,
            'pageSize':pageSize.value,
    }
}
function pageSizeChange(newSize)
{
    pageSize.value = newSize
    updateDisplayRecord()
}
async function pageCurrentChange(page)
{
    currentPage.value = page
    await updateDisplayRecord()
}
async function paginationChange(){
    console.log("pagination change")
    console.log(getCurrentPageInfo())
    await updateDisplayRecord()
}
async function getSelectableColumns()
{
    const res = await axios.get($api_baseUrl + `/accounting/get_display_columns`)
    allColumns.value = res.data.selectableColumns
    console.log(allColumns.value)
    console.log(res.data.selectableColumns)
}
async function updateDisplayRecord()
{
    const apiParams = getCurrentPageInfo()
    console.log("update records")
    console.log(apiParams)
    apiParams['selectedWarehouse'] = currentWarehouse.value
    const res = await axios.get($api_baseUrl + `/accounting/get_warehouse_inbound_record`
        ,{params:apiParams}
    )
    totalNum.value = res.data.total
    displayRecords.value = res.data.inboundRecords
}

async function getWarehouseInfo()
{
    const res = await axios.get($api_baseUrl + `/accounting/get_warehouse_info`)
    warehouseOptions.value = res.data.warehouseInfo
}
</script>
<style>

    
</style>


