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
                <el-input v-model="supplierNameFilter" placeholder="供应商搜索" clearable @change="updateInventoryDisplay"
                    style="width: 200px;"></el-input>
                <el-cascader v-model="quantityFilters" :options="quantityFilterOptions" :props="cascaderProps" @change="updateInventoryDisplay"
                    placeholder="请选择数量筛选条件" clearable style="width: 400px;">
                </el-cascader>
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
                <el-input v-model="materialColorFilter" placeholder="材料颜色搜索" clearable @change="updateInventoryDisplay"
                    style="width: 200px;"></el-input>
                <el-input v-model="materialSpecificationFilter" placeholder="材料规格搜索" clearable
                    @change="updateInventoryDisplay" style="width: 200px;"></el-input>
                <el-input v-model="orderRidFilter" placeholder="订单号搜索" clearable @change="updateInventoryDisplay"
                    style="width: 200px;"></el-input>
                <el-input v-model="customerProductNameFilter" placeholder="客户鞋型号搜索" clearable
                    @change="updateInventoryDisplay" style="width: 200px;"></el-input>
                <el-input v-model="shoeRidFilter" placeholder="工厂型号搜索" clearable @change="updateInventoryDisplay"
                    style="width: 200px;"></el-input>
                <!-- <el-select v-model="statusFilter" multiple style="width:200px；"
                        @change="updateInboundDisplayRecord">
                        <el-option v-for="statusOption in statusFilterOptions"
                        :key="statusOption.key"
                        :label="statusOption.label"
                        :value="statusOption.key"></el-option>
                    </el-select> -->
                <!-- <el-button type="primary" @click="createAndDownloadInboundExcel">生成并下载excel</el-button> -->
                <el-button type="primary" @click="createAndDownloadWarehouseExcel">生成并下载excel</el-button>
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
            <el-table :data="displayData" border stripe height="tabledisplayHeight" style="width: 90vw; height: 65vh;">
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
import { ref, onMounted, getCurrentInstance, nextTick, computed } from 'vue'
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
const quantityFilters = ref([])
const filterConditions = [
    { value: 'eq_zero', label: '等于 0' },
    { value: 'neq_zero', label: '不等于 0' }
]
const quantityFilterOptions = [
    {
        value: 'pending_inbound',
        label: '未审核入库数',
        children: filterConditions
    },
    {
        value: 'pending_outbound',
        label: '未审核出库数',
        children: filterConditions
    },
    {
        value: 'inbound_amount',
        label: '采购入库数',
        children: filterConditions
    },
    {
        value: 'outbound_amount',
        label: '生产出库数',
        children: filterConditions
    },
    {
        value: 'current_amount',
        label: '库存数',
        children: filterConditions
    },
    {
        value: 'make_inventory_inbound',
        label: '盘库入库数',
        children: filterConditions
    },
    {
        value: 'make_inventory_outbound',
        label: '盘库出库数',
        children: filterConditions
    },
]

const cascaderProps = {
    multiple: true,        // 允许多选
    expandTrigger: 'hover',
    emitPath: true,        // 返回整条路径 ['pending_inbound','gt_zero']
    value: 'value',
    label: 'label',
    checkStrictly: false   // 只允许勾选叶子
}

// 把 Cascader 的值转换成更好用的结构，方便发给后端
const parsedQuantityFilters = computed(() => {
    return quantityFilters.value.map(path => {
        const [field, op] = path
        return { field, op }
    })
})

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
async function updateInventoryDisplay() {
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
    return {
        'pageNumber': currentPage.value,
        'pageSize': pageSize.value,
        'selectedWarehouse': currentWarehouse.value,
        'supplierNameFilter': supplierNameFilter.value,
        'materialNameFilter': materialNameFilter.value,
        'materialModelFilter': materialModelFilter.value,
        'materialSpecificationFilter': materialSpecificationFilter.value,
        'materialColorFilter': materialColorFilter.value,
        'orderRidFilter': orderRidFilter.value,
        'customerProductNameFilter': customerProductNameFilter.value,
        'shoeRidFilter': shoeRidFilter.value,
        'quantityFilters': JSON.stringify(parsedQuantityFilters.value),
    }
}
async function createAndDownloadWarehouseExcel() {
    const apiParams = getCurrentPageInfo();
    try {
        const res = await axios.get($api_baseUrl + `/accounting/createinventoryexcelanddownload`, {
            params: apiParams,
            responseType: 'blob', // Important: this tells Axios to handle binary data
        });

        // Create a Blob from the response data
        const blob = new Blob([res.data], { type: res.headers['content-type'] });

        // Use the filename from the Content-Disposition header if available
        const disposition = res.headers['content-disposition'];
        let filename = '财务部库存总单.xlsx'; // fallback name
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