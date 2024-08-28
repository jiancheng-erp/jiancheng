<template>
    <el-dialog title="工价表格" v-model="createVis" width="90%" :before-close="handleGenerateClose">
        <h1>成型工价单</h1>
        <el-table :data="tableData" border>
            <el-table-column prop="rowId" label="序号" />
            <el-table-column prop="procedure" label="工序">
                <template #default="scope">
                    <el-select v-model="scope.row.procedure" filterable placeholder="请选择" style="width: 240px">
                        <el-option v-for="(value, key) in procedureInfo" :value="key" />
                    </el-select>
                </template>
            </el-table-column>
            <el-table-column prop="price" label="单位价格">
                <template #default="scope">
                    <p>{{ procedureInfo[scope.row.procedure] ? procedureInfo[scope.row.procedure]["price"] : '' }}</p>
                </template>
            </el-table-column>
            <el-table-column prop="note" label="备注">
                <template #default="scope">
                    <el-input v-model="scope.row.note" placeholder="" clearable></el-input>
                </template>
            </el-table-column>
            <el-table-column label="操作">
                <template #default="scope">
                    <el-button type="danger" @click="deleteRow(tableData, scope.$index)">删除</el-button>
                </template>
            </el-table-column>
        </el-table>
        <el-button type="primary" size="default" @click="addRow(tableData)">添加新一行</el-button>
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
import axios from 'axios';
const props = defineProps(['currentRowData', 'handleClose'])
const tableData = ref([])
const createVis = ref(true)
const procedureInfo = ref({})
onMounted(async () => {
    let response = null
    try {
        response = await axios.get("http://localhost:8000/production/getallprocedures", {
            params: {
                teams: ['成型'].toString()
            }
        })
        response.data.forEach(row => {
            procedureInfo.value[row.procedureName] = { "price": row.price, "id": row.procedureId }
        });
    } catch (error) {
        console.error('There was an error!', error);
    }
    try {
        response = await axios.get("http://localhost:8000/production/getpricereportdetail", {
            params: {
                reportId: props.currentRowData.reportId,
            }
        })
        tableData.value = response.data
    } catch (error) {
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

const handleSaveData = () => {
    ElMessageBox.confirm('确定保存数据吗？', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
    }).then(async () => {
        // insert price to table data
        tableData.value.forEach(row => {
            row["price"] = procedureInfo.value[row.procedure]["price"]
            row["procedureId"] = procedureInfo.value[row.procedure]["id"]
        })
        await axios.post("http://localhost:8000/production/storepricereportdetail",
            { reportId: props.currentRowData.reportId, newData: tableData.value })
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