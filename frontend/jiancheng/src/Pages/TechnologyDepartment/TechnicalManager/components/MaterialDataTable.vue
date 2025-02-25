<template>
    <el-table :data="tableData" border style="width: 100%">
        <el-table-column type="index"></el-table-column>
        <el-table-column prop="materialType" label="材料类型" />
        <el-table-column prop="supplierName" label="厂家名称">
        </el-table-column>
        <el-table-column prop="materialName" label="材料名称" />
        <el-table-column prop="materialModel" label="材料型号">
        </el-table-column>
        <el-table-column prop="materialSpecification" label="材料规格">
        </el-table-column>
        <el-table-column prop="materialCraftName" label="工艺名称"></el-table-column>
        <el-table-column prop="color" label="颜色">
        </el-table-column>
        <el-table-column prop="comment" label="备注">
        </el-table-column>
        <el-table-column prop="processingRemark" label="加工备注">
        </el-table-column>
    </el-table>

    <el-dialog title="尺码材料" :visible.sync="sizeMaterialDialogVisible" width="30%">
        <el-table :data="sizeMaterialData" border style="width: 100%">
            <el-table-column type="index"></el-table-column>
            <el-table-column prop="size" label="尺码" />
            <el-table-column prop="pairs" label="双数" />
            <el-table-column prop="unitUsage" label="单位用量" />
            <el-table-column prop="totalUsage" label="总用量" />
        </el-table>
    </el-dialog>
</template>
<script>
export default {
    props: {
        tableData: {type: Array, required: true},
    },
    data() {
        return {
            sizeMaterialDialogVisible: false,
            sizeMaterialData: [],
        }
    },
    methods: {
        showSizeMaterial(row) {
            console.log(row)
        }
    }
}
</script>