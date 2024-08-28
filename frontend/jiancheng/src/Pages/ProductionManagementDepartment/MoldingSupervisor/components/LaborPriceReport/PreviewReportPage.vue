<template>
    <el-dialog :title="currentTitle" v-model="previewVis" width="90%" @close="handleClose">
        <el-table :data="tableData" border>
            <el-table-column prop="rowId" label="序号" />
            <el-table-column prop="procedure" label="工序"></el-table-column>
            <el-table-column prop="price" label="单位价格"></el-table-column>
            <el-table-column prop="note" label="备注"></el-table-column>
        </el-table>
        <template #footer>
            <span>
                <el-button @click="handleClose">退出</el-button>
                <el-button type="primary" @click="handleExport">保存为Excel</el-button>
            </span>
        </template>
    </el-dialog>
</template>
<script setup>
import { onMounted, ref } from 'vue';
import axios from 'axios'
import { exportTableToExcel } from '@/Pages/ProductionManagementDepartment/utils';
const props = defineProps(['currentRowData', 'handleClose'])
const previewVis = ref(true)
const columns = ref([])
const tableData = ref([])
const currentTitle = ref('')
onMounted(async () => {
    currentTitle.value = "鞋型号" + props.currentRowData.shoeRId + "工价单"
    let params = { reportId: props.currentRowData.reportId }
    const response = await axios.get("http://localhost:8000/production/getpricereportdetail", { params })
    tableData.value = response.data
    let obj = [
        { prop: "rowId", label: "序号" },
        { prop: "procedure", label: "工序" },
        { prop: "price", label: "单位价格" },
        { prop: "note", label: "备注" },
    ]
    columns.value = obj
})

const handleExport = () => {
    exportTableToExcel(tableData.value, columns.value, currentTitle.value + ".xlsx")
}

const handleClose = () => {
    previewVis.value = false
    props.handleClose(1)
}
</script>