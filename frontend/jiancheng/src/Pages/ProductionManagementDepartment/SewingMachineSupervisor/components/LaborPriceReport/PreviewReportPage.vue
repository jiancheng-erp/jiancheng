<template>
    <el-dialog :title="currentTitle" v-model="previewVis" width="90%" @close="handleClose">
        <el-tabs v-model="activeName">
            <el-tab-pane label="针车预备" name="针车预备">
                <el-table :data="preSewingTableData" border>
                    <el-table-column prop="rowId" label="序号" />
                    <el-table-column prop="procedure" label="工序"></el-table-column>
                    <el-table-column prop="price" label="单位价格"></el-table-column>
                    <el-table-column prop="note" label="备注"></el-table-column>
                </el-table>
            </el-tab-pane>
            <el-tab-pane label="针车" name="针车">
                <el-table :data="sewingTableData" border>
                    <el-table-column prop="rowId" label="序号" />
                    <el-table-column prop="procedure" label="工序"></el-table-column>
                    <el-table-column prop="price" label="单位价格"></el-table-column>
                    <el-table-column prop="note" label="备注"></el-table-column>
                </el-table>
            </el-tab-pane>
        </el-tabs>

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
const preSewingTableData = ref([])
const sewingTableData = ref([])
const currentTitle = ref('')
const activeName = ref('针车预备')
onMounted(async () => {
    currentTitle.value = "鞋型号" + props.currentRowData.shoeRId + "工价单"
    let params = { reportId: props.currentRowData["针车预备"] }
    let response = await axios.get("http://localhost:8000/production/getpricereportdetail", { params })
    preSewingTableData.value = response.data
    params = { reportId: props.currentRowData["针车"] }
    response = await axios.get("http://localhost:8000/production/getpricereportdetail", { params })
    sewingTableData.value = response.data
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