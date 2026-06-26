<template>
    <el-table :data="tableData" border style="width: 100%">
        <el-table-column type="index"></el-table-column>
        <el-table-column prop="materialType" label="材料类型" />
        <!-- <el-table-column prop="materialDetailType" label="材料二级类型">
        </el-table-column> -->
        <el-table-column prop="supplierName" label="厂家名称">
        </el-table-column>
        <el-table-column prop="materialName" label="材料名称" />
        <el-table-column prop="materialModel" label="材料型号">
        </el-table-column>
        <el-table-column prop="materialSpecification" label="材料规格">
        </el-table-column>
        <el-table-column prop="craftName" label="工艺名称"></el-table-column>
        <el-table-column prop="color" label="颜色">
        </el-table-column>
        <!-- <el-table-column prop="unit" label="单位">
        </el-table-column> -->
        <el-table-column prop="comment" label="备注">
        </el-table-column>
        <el-table-column prop="processingRemark" label="加工备注">
        </el-table-column>
        <el-table-column v-if="hasZipperPairData" label="配对组" width="80" align="center">
            <template #default="scope">
                <el-tag v-if="scope.row.zipperPairId != null" type="info" size="small">{{ scope.row.zipperPairId }}</el-tag>
                <span v-else style="color:#c0c4cc">—</span>
            </template>
        </el-table-column>
    </el-table>
</template>
<script>
export default {
    props: ["tableData"],
    computed: {
        hasZipperPairData() {
            return this.tableData.some(row => row.materialName &&
                (row.materialName.includes('拉链') || row.materialName.includes('鞋眼') || row.materialName.includes('垫片')))
        }
    }
}
</script>