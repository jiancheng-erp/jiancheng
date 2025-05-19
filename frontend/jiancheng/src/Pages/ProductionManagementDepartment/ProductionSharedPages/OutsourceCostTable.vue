<template>
    <el-table :data="tableData" border stripe :max-height="500">
        <el-table-column prop="itemName" label="明细">
            <template #default="scope">
                <el-input v-model="scope.row.itemName" placeholder="" clearable></el-input>
            </template>
        </el-table-column>
        <el-table-column prop="itemCost" label="单价">
            <template #default="scope">
                <el-input-number v-model="scope.row.itemCost" :min="0" :precision="4" :step="0.0001" clearable type="number" @input="handleInputChange(scope.row)"></el-input-number>
            </template>
        </el-table-column>
        <el-table-column prop="itemTotalCost" label="总价">
            <template #default="scope">
                <span>{{ scope.row.itemTotalCost }}</span>
            </template>
        </el-table-column>
        <el-table-column prop="remark" label="备注">
            <template #default="scope">
                <el-input v-model="scope.row.remark" placeholder="" clearable></el-input>
            </template>
        </el-table-column>
        <el-table-column label="操作">
            <template #default="scope">
                <el-button type="danger" @click="deleteRow(scope.$index)">删除</el-button>
            </template>
        </el-table-column>
    </el-table>
    <el-button type="primary" size="default" @click="addRow()">添加新一行</el-button>
</template>
<script>
export default {
    props: ["tableData", "outsourceInfoId", 'totalShoes'],
    methods: {
        addRow() {
            this.tableData.push(
                {
                    "itemName": "",
                    "itemCost": 0,
                    "remark": "",
                    "outsourceInfoId": this.$props.outsourceInfoId
                }
            )
        },
        deleteRow(index) {
            this.tableData.splice(index, 1)
        },
        handleInputChange(row) {
            row.itemTotalCost = Math.round(row.itemCost * this.$props.totalShoes * 100) / 100
        },
    }
}
</script>