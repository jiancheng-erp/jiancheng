<template>
    <!-- <el-tabs style="">
        <el-tab-pane label="入库记录">

        </el-tab-pane>
        <el-tab-pane lable="出库记录">

        </el-tab-pane>
    </el-tabs> -->

    <el-row >
        <el-col :span="2" :offset="0">
            <el-select v-model="currentWarehouse" clearable filterable @change="updateInboundDisplayRecord">
            <el-option v-for="item in warehouseOptions"
            :key="item.warehouseId"
            :label="item.warehouseName"
            :value="item.warehouseId">
            </el-option>
            </el-select>
        </el-col>

        <el-col :span="2" :offset="0">
            <el-input v-model="supplierNameFilter" placeholder="供应商搜索" size="normal" clearable @change="updateInboundDisplayRecord"></el-input>
        </el-col>
        <el-col :span="4" :offset="0">
            <el-input v-model="materialModelFilter" placeholder="材料型号搜索" size="normal" clearable @change="updateInboundDisplayRecord"></el-input>
            
        </el-col>
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
        <el-col :span="2" :offset="4">
            <el-switch v-model="summaryOrDetail" :active-value="true" :inactive-value="false" @change="switchColumnNDisplay">
            </el-switch>
        </el-col>
        <el-col :span="2" :offset="0">
            <el-button type="primary" @click="createAndDownloadInboundExcel">生成并下载excel</el-button>
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
    
    <el-col :span=22>

    
    <el-checkbox-group v-model="checkedColumnValues" size="normal"  @change="updateCheckBox">
        <el-checkbox-button v-for="col in allColumns" :key="col.id" :label="col.id">
            {{col.labelName}}
        </el-checkbox-button>
    </el-checkbox-group>
    </el-col>

    <el-col :span="2">
        <el-button type="primary" @click="deselectAllColumns">
        清空选择
        </el-button>

        <el-button @click="selectAllColumns">
            全选
        </el-button>
    </el-col>
    

    </el-row>
    

    <el-row :gutter="20">
        <el-table :data="displayRecords" border stripe>
        <el-table-column v-for="col in selectedColumns"
            :prop="col.attrName"
            :key="col.id"
            :label="col.labelName"
            sortable
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
import { ref, onMounted, getCurrentInstance, nextTick } from 'vue'
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
const materialModelFilter = ref('')
const summaryOrDetail= ref(true)
const currentApi = ref('')
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
//                         starselectAllColumnst.setTime(start.getTime() - 3600 * 1000 * 24 * 30)
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
    mountApi()
    console.log(warehouseOptions.value)
})
function deselectAllColumns(){
    checkedColumnValues.value = []
    updateCheckBox()
}
function selectAllColumns(){
    checkedColumnValues.value = allColumns.value.map((col) => col.id)
    updateCheckBox()
}
function mountApi(){
    currentApi.value = "detail"
}
async function switchColumnNDisplay(){
    deselectAllColumns()
    await getSelectableColumns()
    currentPage.value = 1
    await updateInboundDisplayRecord()
    selectAllColumns()    
}
function updateCheckBox(){
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
            'materialModelFilter': materialModelFilter.value,
            // 'approvalStatusFilter':[0,1,2]
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
    
    if(summaryOrDetail.value == true){
        const res = await axios.get($api_baseUrl + `/accounting/get_inbound_display_columns`)
        allColumns.value = res.data.selectableColumns
    }
    else{
        const res = await axios.get($api_baseUrl + `/accounting/get_inbound_summary_display_columns`)
        allColumns.value = res.data.selectableColumns
    }
}
async function updateInboundDisplayRecord()
{
    const apiParams = getCurrentPageInfo()
    if(summaryOrDetail.value == true){
        const res = await axios.get($api_baseUrl + `/accounting/get_warehouse_inbound_record`
        ,{params:apiParams}
    )
    totalNum.value = res.data.total
    displayRecords.value = res.data.inboundRecords
    }
    else{
        const res = await axios.get($api_baseUrl + `/accounting/get_warehouse_inbound_summery`
            ,{params:apiParams}
        )
    totalNum.value = res.data.total
    displayRecords.value = res.data.inboundSummary
    console.log(displayRecords.value)
    }

    
}

async function getWarehouseInfo()
{
    const res = await axios.get($api_baseUrl + `/accounting/get_warehouse_info`)
    warehouseOptions.value = res.data.warehouseInfo
}

async function filterByDate(){
    const apiParams = getCurrentPageInfo()
}
async function createAndDownloadInboundExcel() {
    const apiParams = getCurrentPageInfo();
    if (summaryOrDetail.value == true) {
        try {
        const res = await axios.get($api_baseUrl + `/accounting/createinboundexcelanddownload`, {
            params: apiParams,
            responseType: 'blob', // Important: this tells Axios to handle binary data
        });

        // Create a Blob from the response data
        const blob = new Blob([res.data], { type: res.headers['content-type'] });

        // Use the filename from the Content-Disposition header if available
        const disposition = res.headers['content-disposition'];
        let filename = '财务部入库明细单.xlsx'; // fallback name
        if (disposition && disposition.includes('filename=')) {
            const match = disposition.match(/filename="?(.+?)"?$/);
            if (match.length > 1) {
                filename = decodeURIComponent(match[1]);
            }
        }

        // Create a link and trigger the download
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(link.href);
    } catch (error) {
        console.error("Failed to download Excel:", error);
    }
    } else {
        try {
            const res = await axios.get($api_baseUrl + `/accounting/createinboundsummaryexcelanddownload`, {
                params: apiParams,
                responseType: 'blob', // Important: this tells Axios to handle binary data
            });

            // Create a Blob from the response data
            const blob = new Blob([res.data], { type: res.headers['content-type'] });

            // Use the filename from the Content-Disposition header if available
            const disposition = res.headers['content-disposition'];
            let filename = '财务部入库汇总单.xlsx'; // fallback name
            if (disposition && disposition.includes('filename=')) {
                const match = disposition.match(/filename="?(.+?)"?$/);
                if (match.length > 1) {
                    filename = decodeURIComponent(match[1]);
                }
            }

            // Create a link and trigger the download
            const link = document.createElement('a');
            link.href = URL.createObjectURL(blob);
            link.download = filename;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            URL.revokeObjectURL(link.href);
        } catch (error) {
            console.error("Failed to download Excel:", error);
        }
        
    }
}
</script>
<style>

    
</style>


