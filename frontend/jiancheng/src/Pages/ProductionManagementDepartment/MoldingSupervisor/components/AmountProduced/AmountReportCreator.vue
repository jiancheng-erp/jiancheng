<template>
    <el-dialog title="生产数量表" v-model="createVis" width="90%" :before-close="handleGenerateClose">
        <el-table :data="tableData.uniqueData" show-summary border :style="{ marginBottom: '20px' }">
            <el-table-column prop="rowId" label="序号" />
            <el-table-column prop="name" label="姓名" />
            <el-table-column prop="procedure" label="工序" />
            <el-table-column prop="unitPrice" label="单位价格" />
            <el-table-column prop="totalPrice" label="总价格" />
        </el-table>
        <el-table :data="tableData.shoesizeAmounts" border :style="{ marginBottom: '20px' }">
            <el-table-column prop="title" label="鞋码编号"></el-table-column>
            <el-table-column label="生产数量">
                <template #default="scope">
                    <el-input v-model="scope.row.amount" style="width: 100px" type="number" min="0"
                        :max="scope.row.remain" @blur="() => checkValue(scope.row)"/>
                </template>
            </el-table-column>
            <el-table-column prop="remain" label="剩余数量" />
        </el-table>

        <template #footer>
            <span>
                <el-button @click="handleGenerateClose">取消</el-button>
                <el-button type="primary" @click="handleSaveData">保存</el-button>
            </span>
        </template>
    </el-dialog>
</template>

<script setup>
import { watch, ref } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
const props = defineProps(['tableInput', 'handleSave', 'handleClose', 'shoesizeNumbers'])
const tableData = ref(JSON.parse(JSON.stringify(props.tableInput)))
const createVis = ref(true)
tableData.value.shoesizeAmounts.forEach(row => {
    watch(
        () => row.amount,
        (newVal, oldVal) => {
            newVal = Number(newVal), oldVal = Number(oldVal)
            tableData.value.totalAmount = tableData.value.totalAmount + newVal - oldVal
            tableData.value.uniqueData.forEach((row) => {
                row.totalPrice = (tableData.value.totalAmount * row.unitPrice).toFixed(2)
            })
            row.remain = row.remain + oldVal - newVal
        }
    )
})

const checkValue = (row) => {
    if (row.amount < 0) {
        row.amount = 0
    } else if (row.remain < 0) {
        row.amount = Number(row.amount) + row.remain
    }
}

const handleSaveData = () => {
    ElMessageBox.confirm('确定保存数据吗？', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
    }).then(() => {
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
    props.handleSave(tableData.value)
}
const handleGenerateClose = () => {
    createVis.value = false
    props.handleClose(0)
}
</script>