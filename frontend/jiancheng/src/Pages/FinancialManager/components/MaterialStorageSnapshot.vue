<template>
    <el-row>
        <el-col>
            <div style="display: flex; align-items: center; gap: 10px;">
                <el-date-picker v-model="dateFilter" type="date" placeholder="选择日期" value-format="YYYY-MM-DD"
                    :disabled-date="disableAfterYesterday" @change="updateInventoryDisplay" />
                <el-select v-model="currentWarehouse" clearable filterable @change="updateInventoryDisplay"
                    placeholder="仓库搜索" style="width: 200px;">
                    <el-option v-for="item in warehouseOptions" :key="item.warehouseId" :label="item.warehouseName"
                        :value="item.warehouseId">
                    </el-option>
                </el-select>
                <el-input v-model="supplierNameFilter" placeholder="供应商搜索" clearable @change="updateInventoryDisplay"
                    style="width: 200px;"></el-input>
            </div>

        </el-col>
    </el-row>
    <el-row :gutter="20">
        <el-col>
            <div style="display: flex; align-items: center; gap: 10px;">
                <el-input v-model="materialNameFilter" placeholder="材料名称搜索" clearable @change="updateInventoryDisplay"
                    style="width: 200px;"></el-input>
                <el-input v-model="materialModelFilter" placeholder="材料型号搜索" clearable @change="updateInventoryDisplay"
                    style="width: 200px;"></el-input>
                <el-input v-model="materialSpecificationFilter" placeholder="材料规格搜索" clearable
                    @change="updateInventoryDisplay" style="width: 200px;"></el-input>
                <el-input v-model="materialColorFilter" placeholder="材料颜色搜索" clearable @change="updateInventoryDisplay"
                    style="width: 200px;"></el-input>
                <el-input v-model="orderRidFilter" placeholder="订单号搜索" clearable @change="updateInventoryDisplay"
                    style="width: 200px;"></el-input>
                <el-input v-model="customerProductNameFilter" placeholder="客户鞋型号搜索" clearable
                    @change="updateInventoryDisplay" style="width: 200px;"></el-input>
                <el-input v-model="shoeRidFilter" placeholder="工厂型号搜索" clearable @change="updateInventoryDisplay"
                    style="width: 200px;"></el-input>
                <el-radio-group v-model="displayZeroInventory" @change="toggleDisplayZero">
                    <el-radio-button :value="false">现有库存</el-radio-button>
                    <el-radio-button :value="true">所有库存</el-radio-button>
                </el-radio-group>
                <el-button type="primary" @click="createAndDownloadWarehouseExcel">生成并下载excel</el-button>
            </div>
        </el-col>
    </el-row>
    <el-row :gutter="20">
        <el-col>
            <el-table :data="displayData" border stripe style="width: 90vw; height: 65vh;">
                <el-table-column prop="warehouseName" label="仓库" />
                <el-table-column prop="supplierName" label="供应商" />
                <el-table-column prop="materialType" label="材料类型" />
                <el-table-column prop="materialName" label="材料名称" />
                <el-table-column prop="materialModel" label="材料型号" />
                <el-table-column prop="materialSpecification" label="材料规格" />
                <el-table-column prop="materialColor" label="材料颜色" />
                <el-table-column prop="orderRId" label="订单号" />
                <el-table-column prop="customerProductName" label="客户鞋型号" />
                <el-table-column prop="shoeRId" label="工厂型号" />
                <el-table-column prop="pendingInbound" label="未审核入库数" />
                <el-table-column prop="pendingOutbound" label="未审核出库数" />
                <el-table-column prop="inboundAmount" label="已审核入库数" />
                <el-table-column prop="outboundAmount" label="已审核出库数" />
                <el-table-column prop="currentAmount" label="库存数量" />
                <el-table-column prop="actualInboundUnit" label="入库单位" />
                <el-table-column prop="unitPrice" label="最新采购单价" />
                <el-table-column prop="averagePrice" label="库存均价" />
                <el-table-column prop="currentItemTotalPrice" label="余量总金额" />
            </el-table>
        </el-col>
    </el-row>

    <el-row :gutter="20">
        <el-col>
            <el-pagination @size-change="pageSizeChange" @current-change="pageCurrentChange" :current-page="currentPage"
                :page-sizes="[20, 40, 60, 100]" :page-size="pageSize" layout="total, sizes, prev, pager, next, jumper"
                :total="totalNum" />
        </el-col>
    </el-row>
</template>

<script setup lang="ts">
import { ref, onMounted, getCurrentInstance, nextTick } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'

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
const dateFilter = ref(null)
const displayZeroInventory = ref(false)

let warehouseOptions = ref([])

const $api_baseUrl = getCurrentInstance().appContext.config.globalProperties.$apiBaseUrl

onMounted(async () => {
    getWarehouseInfo()
    await getSelectableColumns()
    selectAllColumns()
    setDateFilter()
    updateInventoryDisplay()
})

async function toggleDisplayZero() {
    updateInventoryDisplay()
}

const setDateFilter = () => {
    const yesterday = new Date()
    yesterday.setDate(yesterday.getDate() - 1)
    dateFilter.value = yesterday.toISOString().split('T')[0]

}

const disableAfterYesterday = (date: Date) => {
    const endYesterday = new Date()
    endYesterday.setDate(endYesterday.getDate() - 1)
    endYesterday.setHours(23, 59, 59, 999)
    return date.getTime() > endYesterday.getTime()
}

async function getSelectableColumns() {
    const res = await axios.get($api_baseUrl + `/accounting/get_inventory_display_columns`)
    allColumns.value = res.data.selectableColumns
}

async function getWarehouseInfo() {
    const res = await axios.get($api_baseUrl + `/accounting/get_warehouse_info`)
    warehouseOptions.value = res.data.warehouseInfo
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
}

function pageSizeChange(newSize) {
    pageSize.value = newSize
    updateInventoryDisplay()
}

function pageCurrentChange(page) {
    currentPage.value = page
    updateInventoryDisplay()

}

async function updateInventoryDisplay() {
    const apiParams = getCurrentPageInfo()
    try {
        const res = await axios.get($api_baseUrl + `/warehouse/getmaterialstroagebydate`, { params: apiParams })
        totalNum.value = res.data.data.total
        displayData.value = res.data.data.items
    }
    catch (error) {
        console.log(error)
        const message = error.response.data.message ? error.response.data : error
        ElMessage.error(message)
    }
}
function getCurrentPageInfo() {
    return {
        'page': currentPage.value,
        'pageSize': pageSize.value,
        'warehouseIdFilter': currentWarehouse.value,
        'supplierNameFilter': supplierNameFilter.value,
        'materialNameFilter': materialNameFilter.value,
        'materialModelFilter': materialModelFilter.value,
        'materialSpecificationFilter': materialSpecificationFilter.value,
        'materialColorFilter': materialColorFilter.value,
        'orderRidFilter': orderRidFilter.value,
        'customerProductNameFilter': customerProductNameFilter.value,
        'shoeRidFilter': shoeRidFilter.value,
        "snapshotDate": dateFilter.value,
        "displayZeroInventory": displayZeroInventory.value
    }
}
async function createAndDownloadWarehouseExcel() {
    const apiParams = getCurrentPageInfo();
    try {
        const res = await axios.get($api_baseUrl + `/warehouse/exportinventoryhistory`, {
            params: apiParams,
            responseType: 'blob', // Important: this tells Axios to handle binary data
        });

        // Create a Blob from the response data
        const blob = new Blob([res.data], { type: res.headers['content-type'] });

        // Use the filename from the Content-Disposition header if available
        const disposition = res.headers['content-disposition'];
        let filename = '财务部历史库存总单.xlsx'; // fallback name
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
</script>