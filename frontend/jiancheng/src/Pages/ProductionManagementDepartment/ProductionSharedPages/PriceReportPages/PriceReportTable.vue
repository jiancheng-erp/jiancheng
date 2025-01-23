<template>
    <el-table :data="tableData" border stripe>
        <el-table-column prop="rowId" label="序号" />
        <el-table-column v-if="props.team === '成型'" prop="productionSection" label="工段">
            <template v-if="!readOnly" #default="scope">
                <el-select v-model="scope.row.productionSection" placeholder="请选择" clearable>
                    <el-option v-for="item in ['前段', '中段', '后段']" :value="item" :label="item"></el-option>
                </el-select>
            </template>
        </el-table-column>
        <el-table-column prop="procedure" label="工序">
            <template v-if="!readOnly" #default="scope">
                <el-autocomplete v-model="scope.row.procedure" :fetch-suggestions="querySearch" placeholder=""
                    @select="(args) => onProductSelect(args, scope.row)" clearable>
                </el-autocomplete>
            </template>
        </el-table-column>
        <el-table-column v-if="props.team !== '成型'" prop="price" label="工价">
            <template v-if="!readOnly" #default="scope">
                <el-input-number v-model="scope.row.price" clearable :min="0" :precision="2" :step="0.01"></el-input-number>
            </template>
        </el-table-column>
        <el-table-column prop="note" label="备注">
            <template v-if="!readOnly" #default="scope">
                <el-input v-model="scope.row.note" placeholder="" clearable></el-input>
            </template>
        </el-table-column>
        <el-table-column v-if="!readOnly" label="操作">
            <template #default="scope">
                <el-button type="danger" @click="deleteRow(scope.$index)">删除</el-button>
            </template>
        </el-table-column>
    </el-table>
    <el-button v-if="!readOnly" type="primary" size="default" @click="addRow()">添加新一行</el-button>
</template>
<script setup>
import { defineModel } from 'vue';
const props = defineProps(['procedureInfo', 'readOnly', 'team'])
const tableData = defineModel('tableData')
const addRow = () => {
    const newRowId = tableData.value.length + 1;
    const newItem = {
        "rowId": newRowId,
        "procedure": "",
        "price": "",
        "note": ""
    }
    tableData.value.push(newItem)
}

const deleteRow = (index) => {
    tableData.value.splice(index, 1);
    tableData.value.forEach((row, index) => {
        row.rowId = index + 1
    })
}

const querySearch = (queryString, cb) => {
    const matchObj = queryString
        ? props.procedureInfo.filter(procedure =>
            procedure.procedureName.toLowerCase().indexOf(queryString.toLowerCase()) === 0
        )
        : []
    // call callback function to return suggestions
    let result = []
    matchObj.forEach(row => {
        result.push({ value: row.procedureName, price: row.price })
    })
    cb(result)
}

const onProductSelect = (info, row) => {
    row.procedureName = info.value
    row.price = info.price
}
// const handleClickEnter = (event) => {
//     if (event.key === 'Enter') {
//         addRow()
//     }
// }

</script>
