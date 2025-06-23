<template>
     <el-row>
        <el-col>
            <div style="display: flex; align-items: center; gap: 10px;">
                <el-select v-model="currentWarehouse" clearable filterable @change="updateInventoryDisplay"
                    placeholder="仓库搜索" style="width: 200px;">
                    <el-option v-for="item in warehouseOptions" :key="item.warehouseId" :label="item.warehouseName"
                        :value="item.warehouseId">
                    </el-option>
                </el-select>
                <el-input v-model="supplierNameFilter" placeholder="供应商搜索" clearable
                    @change="updateInventoryDisplay" style="width: 200px;"></el-input>
            </div>

        </el-col>
    </el-row>
    <el-row :gutter="20">
            <el-col>
                <div style="display: flex; align-items: center; gap: 10px;">
                    <el-input v-model="materialNameFilter" placeholder="材料名称搜索" clearable
                        @change="updateInventoryDisplay" style="width: 200px;"></el-input>
                    <el-input v-model="materialModelFilter" placeholder="材料型号搜索" clearable
                        @change="updateInventoryDisplay" style="width: 200px;"></el-input>
                        <el-input v-model="materialColorFilter" placeholder="材料颜色搜索" clearable
                        @change="updateInventoryDisplay" style="width: 200px;"></el-input>
                    <el-input v-model="materialSpecificationFilter" placeholder="材料规格搜索" clearable
                        @change="updateInventoryDisplay" style="width: 200px;"></el-input>
                    <el-input v-model="orderRidFilter" placeholder="订单号搜索" clearable
                        @change="updateInventoryDisplay" style="width: 200px;"></el-input>
                    <el-input v-model="customerProductNameFilter" placeholder="客户鞋型号搜索" clearable
                        @change="updateInventoryDisplay" style="width: 200px;"></el-input>
                    <el-input v-model="shoeRidFilter" placeholder="工厂型号搜索" clearable
                        @change="updateInventoryDisplay" style="width: 200px;"></el-input>
                    <!-- <el-select v-model="statusFilter" multiple style="width:200px；"
                        @change="updateInboundDisplayRecord">
                        <el-option v-for="statusOption in statusFilterOptions"
                        :key="statusOption.key"
                        :label="statusOption.label"
                        :value="statusOption.key"></el-option>
                    </el-select> -->
                    <!-- <el-button type="primary" @click="createAndDownloadInboundExcel">生成并下载excel</el-button> -->
                    <el-button type="primary" @click="toggleDisplayZero">更改空库存显示</el-button>
                </div>

            </el-col>
        </el-row>
    <el-row :gutter="20">
        <el-col :span=20>
            <el-checkbox-group v-model="checkedColumnValues" @change="updateCheckBox">
                <el-checkbox-button v-for="col in allColumns" :key="col.id" :value="col.id">
                    {{ col.labelName }}
                </el-checkbox-button>
            </el-checkbox-group>
        </el-col>
        <el-col :span="4">
            <el-button type="primary" @click="deselectAllColumns">
                清空选择
            </el-button>
            <el-button @click="selectAllColumns">
                全选
            </el-button>
        </el-col>
    </el-row>

    <el-row :gutter="20">
        <el-col>
            <el-table :data="displayData" border stripe height="tabledisplayHeight" style="width: 90vw">
                <el-table-column v-for="col in selectedColumns" :prop="col.attrName" :key="col.id"
                    :label="col.labelName" :min-width="col.width">
                </el-table-column>
            </el-table>
        </el-col>
    </el-row>

    <el-row :gutter="20">
        <el-col>
            <el-pagination @size-change="pageSizeChange" @current-change="pageCurrentChange" :current-page="currentPage"
                :page-sizes="[10, 20, 40, 80, 100]" :page-size="pageSize"
                layout="total, sizes, prev, pager, next, jumper" :total="totalNum" background>
                :pager-count="7">
            </el-pagination>
        </el-col>
    </el-row>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { ref, onMounted, getCurrentInstance, nextTick } from 'vue'
import axios from 'axios'
import useSetAxiosToken from '../hooks/useSetAxiosToken'

const displayData = ref([])
const allColumns = ref([])
const checkedColumnValues = ref([])
const selectedColumns = ref([])
const currentPage = ref(1)
const pageSize = ref(20)
const totalNum = ref(0)
const currentWarehouse = ref('')
const supplierNameFilter = ref('')
const materialNameFilter = ref('')
const materialModelFilter = ref('')
const materialSpecificationFilter = ref('')
const materialColorFilter = ref('')
const orderRidFilter = ref('')
const customerProductNameFilter = ref('')
const shoeRidFilter = ref('')
const displayZeroInventory = ref(true)

interface WarehouseEntity {
    warehouseId: number
    warehouseName: string
}
let warehouseOptions = ref([])

const $api_baseUrl = getCurrentInstance().appContext.config.globalProperties.$apiBaseUrl

onMounted(async () => {
    getWarehouseInfo()
    await getSelectableColumns()
    selectAllColumns()
    updateInventoryDisplay()    // mountApi()
})
async function apiCall() {
    const res = await axios.get($api_baseUrl + `/accounting/get_warehouse_inventory`)
    console.log(res.data)
    displayData.value = res.data.currentInventory
}

async function getSelectableColumns() {
    const res = await axios.get($api_baseUrl + `/accounting/get_inventory_display_columns`)
    allColumns.value = res.data.selectableColumns
}
async function getWarehouseInfo() {
    const res = await axios.get($api_baseUrl + `/accounting/get_warehouse_info`)
    warehouseOptions.value = res.data.warehouseInfo
}
async function toggleDisplayZero(){
    console.log(displayZeroInventory.value)
    displayZeroInventory.value = !displayZeroInventory.value
    console.log(displayZeroInventory.value)
    updateInventoryDisplay()
}
function deselectAllColumns() {
    checkedColumnValues.value = []
    updateCheckBox()
}
function selectAllColumns() {
    checkedColumnValues.value = allColumns.value.map((col) => col.id)
    updateCheckBox()
}
function updateCheckBox() {
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
function pageSizeChange(newSize) {
    pageSize.value = newSize
    updateInventoryDisplay()
}
async function pageCurrentChange(page) {
    currentPage.value = page
    await updateInventoryDisplay()

}
async function updateInventoryDisplay(){
    const apiParams = getCurrentPageInfo()  
    console.log(apiParams) 
    const res = await axios.get($api_baseUrl + `/accounting/get_warehouse_inventory`
            , { params: apiParams }
        )
        totalNum.value = res.data.total
        displayData.value = res.data.currentInventory
        console.log(res.data)
}
function getCurrentPageInfo() {
    // if (dateRangeFilter.value == null) {
    //     dateRangeFilter.value = ['', '']
    // }

    return {
        'pageNumber': currentPage.value,
        'pageSize': pageSize.value,
        'selectedWarehouse': currentWarehouse.value,
        // 'dateRangeFilterStart': dateRangeFilter.value[0],
        // 'dateRangeFilterEnd': dateRangeFilter.value[1],
        // 'inboundRIdFilter': inboundRIdFilter.value,
        'supplierNameFilter': supplierNameFilter.value,
        'materialNameFilter': materialNameFilter.value,
        'materialModelFilter': materialModelFilter.value,
        'materialSpecificationFilter': materialSpecificationFilter.value,
        'materialColorFilter': materialColorFilter.value,
        'orderRidFilter': orderRidFilter.value,
        'customerProductNameFilter': customerProductNameFilter.value,
        'shoeRidFilter':shoeRidFilter.value,
        'includeZeroFilter':displayZeroInventory.value
        // 'statusFilter':statusFilter.value
        // 'approvalStatusFilter':[0,1,2]
    }
}

</script>