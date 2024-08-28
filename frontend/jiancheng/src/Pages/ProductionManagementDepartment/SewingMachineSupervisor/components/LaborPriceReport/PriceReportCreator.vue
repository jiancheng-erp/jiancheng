<template>
    <el-dialog title="针车工价表格" v-model="createVis" width="90%" :before-close="handleGenerateClose">
        <el-tabs v-model="activeName">
            <el-tab-pane label="针车预备" name="针车预备">
                <!-- <el-input v-model="searchOrder" placeholder="请输入工序名称" style="width: 240px"
                    :suffix-icon="Search" clearable @input="filterData"></el-input> -->
                <el-table :data="preSewingTableData" border>
                    <el-table-column prop="rowId" label="序号" />
                    <el-table-column prop="procedure" label="工序">
                        <template #default="scope">
                            <el-select v-model="scope.row.procedure" filterable placeholder="请选择" style="width: 240px">
                                <el-option v-for="(value, key) in preSewingProcedures" :value="key" />
                            </el-select>
                        </template>
                    </el-table-column>
                    <el-table-column prop="unitPrice" label="单位价格">
                        <template #default="scope">
                            <p>{{ preSewingProcedures[scope.row.procedure] ?
                                preSewingProcedures[scope.row.procedure]["price"] : '' }}</p>
                        </template>
                    </el-table-column>
                    <el-table-column prop="note" label="备注">
                        <template #default="scope">
                            <el-input v-model="scope.row.note" placeholder="" clearable></el-input>
                        </template>
                    </el-table-column>
                    <el-table-column label="操作">
                        <template #default="scope">
                            <el-button type="danger" @click="deleteRow(preSewingTableData, scope.$index)">删除</el-button>
                        </template>
                    </el-table-column>
                </el-table>
                <el-button type="primary" size="default" @click="addRow(preSewingTableData)">添加新一行</el-button>
            </el-tab-pane>
            <el-tab-pane label="针车" name="针车">
                <el-table :data="sewingTableData" border>
                    <el-table-column prop="rowId" label="序号" />
                    <el-table-column prop="procedure" label="工序">
                        <template #default="scope">
                            <el-select v-model="scope.row.procedure" filterable placeholder="请选择" style="width: 240px">
                                <el-option v-for="(value, key) in sewingProcedures" :value="key" />
                            </el-select>
                        </template>
                    </el-table-column>
                    <el-table-column prop="unitPrice" label="单位价格">
                        <template #default="scope">
                            <p>{{ sewingProcedures[scope.row.procedure] ?
                                sewingProcedures[scope.row.procedure]["price"] : '' }}</p>
                        </template>
                    </el-table-column>
                    <el-table-column prop="note" label="备注">
                        <template #default="scope">
                            <el-input v-model="scope.row.note" placeholder="" clearable></el-input>
                        </template>
                    </el-table-column>
                    <el-table-column label="操作">
                        <template #default="scope">
                            <el-button type="danger" @click="deleteRow(sewingTableData, scope.$index)">删除</el-button>
                        </template>
                    </el-table-column>
                </el-table>
                <el-button type="primary" size="default" @click="addRow(sewingTableData)">添加新一行</el-button>
            </el-tab-pane>
        </el-tabs>
        <template #footer>
            <span>
                <el-button @click="handleGenerateClose">取消</el-button>
                <el-button type="primary" @click="handleSaveData">保存</el-button>
            </span>
        </template>
    </el-dialog>
</template>

<script setup>
import { onMounted, ref } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Search } from '@element-plus/icons-vue'
import axios from 'axios'
const props = defineProps(['currentRowData', 'handleClose'])
const preSewingTableData = ref([])
const sewingTableData = ref([])
const preSewingProcedures = ref({})
const sewingProcedures = ref({})
const createVis = ref(true)
const activeName = ref('针车预备')

onMounted(async () => {
    let response = null
    // 获取工价
    try {
        response = await axios.get("http://localhost:8000/production/getallprocedures", {
            params: {
                teams: ['针车预备', '针车'].toString()
            }
        })
        response.data.forEach(row => {
            if (row.team == "针车预备") {
                preSewingProcedures.value[row.procedureName] = { "price": row.price, "id": row.procedureId }
            }
            else {
                sewingProcedures.value[row.procedureName] = { "price": row.price, "id": row.procedureId }
            }
        });
    }
    catch (error) {
        console.error('There was an error!', error);
    }
    // 获取工价单具体信息
    try {
        response = await axios.get("http://localhost:8000/production/getpricereportdetail", {
            params: {
                reportId: props.currentRowData["针车预备"],
            }
        })
        preSewingTableData.value = response.data

        response = await axios.get("http://localhost:8000/production/getpricereportdetail", {
            params: {
                reportId: props.currentRowData["针车"],
            }
        })
        sewingTableData.value = response.data
    }
    catch (error) {
        console.error('There was an error!', error);
    }
})

const addRow = (arrRef) => {
    const newRowId = arrRef.length + 1;
    arrRef.push(
        {
            "rowId": newRowId,
            "procedure": "",
            "price": "",
            "note": ""
        }
    )
}

const deleteRow = (tableData, index) => {
    tableData.splice(index, 1)
    tableData.forEach((row, index) => {
        row.rowId = index + 1
    })
}

// const handleClickEnter = (event) => {
//     if (event.key === 'Enter') {
//         addRow()
//     }
// }

const handleSaveData = () => {
    ElMessageBox.confirm('确定保存数据吗？', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
    }).then(async () => {
        
        // insert price to table data
        preSewingTableData.value.forEach(row => {
            row["price"] = preSewingProcedures.value[row.procedure]["price"]
            row["procedureId"] = preSewingProcedures.value[row.procedure]["id"]
        })
        await axios.post("http://localhost:8000/production/storepricereportdetail",
            { reportId: props.currentRowData["针车预备"], newData: preSewingTableData.value })
        
        sewingTableData.value.forEach(row => {
            row["price"] = sewingProcedures.value[row.procedure]["price"]
            row["procedureId"] = sewingProcedures.value[row.procedure]["id"]
        })
        await axios.post("http://localhost:8000/production/storepricereportdetail",
            { reportId: props.currentRowData["针车"], newData: sewingTableData.value })

        ElMessage({
            type: 'success',
            message: '保存成功!'
        });
    }).catch(() => {
        ElMessage({
            type: 'info',
            message: '已取消保存'
        });
    });
}
const handleGenerateClose = () => {
    ElMessageBox.confirm('确定退出编辑表格吗？', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
    }).then(() => {
        createVis.value = false
        props.handleClose(0)
    }).catch(() => { })
}
</script>