<template>
    <el-container :direction="vertical">
        <el-header height="">
            <AllHeader></AllHeader>
        </el-header>
        <el-main style="overflow-x: hidden;">
            <el-row :gutter="20" style="text-align: center;">
                <el-col :span="24" :offset="0" style="font-size: xx-large; text-align: center;">一次BOM填写</el-col>
            </el-row>
            <el-row :gutter="20">
                <el-col :span="24" :offset="0">
                    <span style="font-weight: bold; font-size: larger;">订单信息：</span>
                    <el-row :gutter="20">
                        <el-col :span="24" :offset="0">
                            <Arrow :status="11"></Arrow>
                        </el-col>
                    </el-row>
                    <el-descriptions title="" :column="2">

                        <el-descriptions-item label="订单编号">{{ orderId }}</el-descriptions-item>
                        <el-descriptions-item label="订单创建时间">{{ testOrderData.createTime }}</el-descriptions-item>
                        <el-descriptions-item label="前序流程下发时间">{{ testOrderData.prevTime }}</el-descriptions-item>
                        <el-descriptions-item label="前序处理部门">{{ testOrderData.prevDepart }}</el-descriptions-item>
                        <el-descriptions-item label="前序处理人">{{ testOrderData.prevUser }}</el-descriptions-item>
                        <el-descriptions-item label="订单状态">{{ testOrderData.orderStatus }}</el-descriptions-item>
                    </el-descriptions>
                </el-col>
            </el-row>
            <el-row :gutter="20" style="margin-top: 10px;">
                <el-col :span="4" :offset="0">
                    <div style="display: flex; align-items: center; white-space: nowrap;">工厂型号搜索：<el-input
                            v-model="inheritIdSearch" placeholder="" size="default" :suffix-icon="Search" clearable
                            @input="tableWholeFilter"></el-input></div>
                </el-col>

            </el-row>

            <el-row :gutter="20" style="margin-top: 20px;">
                <el-col :span="24" :offset="0">
                    <el-table :data="testTableFilterData" border style="height: 400px;">
                        <el-table-column prop="inheritId" label="工厂型号" align="center" width="100"></el-table-column>
                        <el-table-column prop="customerId" label="客户型号" align="center"></el-table-column>
                        <el-table-column label="鞋图" align="center">
                            <template #default="scope">
                                <el-image style="width: 150px; height: 100px" :src="scope.row.image" :fit="contain" />
                            </template>
                        </el-table-column>
                        <el-table-column prop="designer" label="设计员" align="center"></el-table-column>
                        <el-table-column prop="editter" label="调版员" align="center"></el-table-column>
                        <el-table-column prop="Status" label="状态" align="center"></el-table-column>
                        <el-table-column label="操作" align="center"> <template #default="scope">
                                <el-button v-if="scope.row.Status === '未填写'" type="primary"
                                    @click="handleGenerate(scope.row)">填写</el-button>
                                <el-button v-else-if="scope.row.Status === '已下发' || scope.row.Status === '已提交'"
                                    type="primary" @click="openPreviewDialog(scope.row)">查看</el-button>
                                <div v-else-if="scope.row.Status === '已保存'">
                                    <el-button type="primary" @click="handleGenerate(scope.row)">编辑</el-button>
                                    <el-button type="success" @click="openPreviewDialog(scope.row)">预览</el-button>
                                    <el-button type="warning" @click="handleConfirm(scope.row)">提交</el-button>
                                </div>
                            </template></el-table-column>
                    </el-table></el-col>
            </el-row>
            <el-row :gutter="22" style="margin-top: 10px;">
                <el-col :span="6" :offset="20"><el-button type="primary" size="default"
                        @click="openBOMCreate">下发BOM</el-button>
                </el-col>
            </el-row>

            <el-dialog title="一次BOM填写 0E20620-VRA-1020" v-model="createVis" width="100%" @close="handleGenerateClose">
                <el-descriptions title="订单信息" :column="2">
                    <el-descriptions-item label="订单编号">{{ orderId }}</el-descriptions-item>
                    <el-descriptions-item label="订单创建时间">{{ testOrderData.createTime }}</el-descriptions-item>
                    <el-descriptions-item label="前序流程下发时间">{{ testOrderData.prevTime }}</el-descriptions-item>
                    <el-descriptions-item label="前序处理部门">{{ testOrderData.prevDepart }}</el-descriptions-item>
                    <el-descriptions-item label="前序处理人">{{ testOrderData.prevUser }}</el-descriptions-item>
                    <el-descriptions-item label="订单状态">{{ testOrderData.orderStatus }}</el-descriptions-item>
                    <el-descriptions-item label="工艺单"><el-button type="primary" size="default"
                            @click="">查看工艺单</el-button>
                    </el-descriptions-item>
                    <el-descriptions-item label="工艺单"><el-button type="primary" size="default"
                            @click="">查看生产订单</el-button>
                    </el-descriptions-item>
                </el-descriptions>

                <div style="height: 600px; overflow-y: scroll; overflow-x: hidden">
                    <el-row>
                        <el-table :data="orderProduceInfo" border style="width: 100%" :span-method="arraySpanMethod">
                            <el-table-column prop="color" label="颜色" />
                            <el-table-column prop="size" label="配码" />
                            <el-table-column prop="35" label="35" />
                            <el-table-column prop="36" label="36" />
                            <el-table-column prop="37" label="37" />
                            <el-table-column prop="38" label="38" />
                            <el-table-column prop="39" label="39" />
                            <el-table-column prop="40" label="40" />
                            <el-table-column prop="41" label="41" />
                            <el-table-column prop="pairAmount" label="双数" />
                            <el-table-column prop="total" label="合计" />
                        </el-table>
                    </el-row>
                    <el-row style="margin-top: 10px;">
                        <el-table :data="bomTestData" border>
                            <el-table-column prop="partName" label="部件名称">
                                <template #default="scope">
                                    <el-input v-model="scope.row.partName" size="default" />
                                </template>
                            </el-table-column>
                            <el-table-column prop="color" label="颜色">
                                <template #default="scope">
                                    <el-input v-model="scope.row.color" size="default" />
                                </template>
                            </el-table-column>
                            <el-table-column prop="materialType" label="材料类型">
                                <template #default="scope">
                                    <el-input v-model="scope.row.materialType" size="default" />
                                </template>
                            </el-table-column>
                            <el-table-column prop="materialName" label="材料名称">
                                <template #default="scope">
                                    <el-input v-model="scope.row.materialName" size="default" />
                                </template>
                            </el-table-column>
                            <el-table-column prop="materialSpecification" label="材料规格">
                                <template #default="scope">
                                    <el-input v-model="scope.row.materialSpecification" size="default" />
                                </template>
                            </el-table-column>
                            <el-table-column prop="unit" label="单位">
                                <template #default="scope">
                                    <el-input v-model="scope.row.unit" size="default" />
                                </template>
                            </el-table-column>
                            <el-table-column prop="unitUsage" label="单位用量">
                                <template #default="scope">
                                    <el-input v-model="scope.row.unitAmount" type="number" size="default" />
                                </template>
                            </el-table-column>
                            <el-table-column prop="approvedUsage" label="核定用量">
                                <template #default="scope">
                                    <el-input v-model="scope.row.approvedAmount" type="number" size="default" />
                                </template>
                            </el-table-column>
                            <el-table-column prop="useDepart" label="使用工段">
                                <template #default="scope">
                                    <el-input v-model="scope.row.useDepart" size="default" />
                                </template>
                            </el-table-column>
                            <el-table-column label="备注">
                                <template #default="scope">
                                    <el-input v-model="scope.row.comment" size="default" />
                                </template>
                            </el-table-column>
                            <el-table-column label="操作"> <template #default="scope">
                                    <el-button type="danger"
                                        @click="deleteCurrentRow(scope.$index, bomTestData)">删除</el-button>
                                </template></el-table-column>
                        </el-table>
                    </el-row>
                </div>
                <el-button type="primary" size="default" @click="addNewMaterial">添加新部件</el-button>


                <template #footer>
                    <span>
                        <el-button @click="handleGenerateClose">取消</el-button>
                        <el-button type="primary" @click="">保存</el-button>
                    </span>
                </template>
            </el-dialog>

            <el-dialog title="预览BOM表 K2402121116202024061101F" v-model="isPreviewDialogVisible" width="90%">
                <el-descriptions title="订单信息" :column="2">
                    <el-descriptions-item label="订单编号">{{ orderId }}</el-descriptions-item>
                </el-descriptions>
                <div style="height: 600px; overflow-y: scroll; overflow-x: hidden">
                    <el-row :gutter="20" style="margin-bottom: 20px;">
                        <el-col :span="23">
                            <el-table :data="orderProduceInfo" border style="width: 100%"
                                :span-method="arraySpanMethod">
                                <el-table-column prop="color" label="颜色" />
                                <el-table-column prop="size" label="配码" />
                                <el-table-column prop="35" label="35" />
                                <el-table-column prop="36" label="36" />
                                <el-table-column prop="37" label="37" />
                                <el-table-column prop="38" label="38" />
                                <el-table-column prop="39" label="39" />
                                <el-table-column prop="40" label="40" />
                                <el-table-column prop="41" label="41" />
                                <el-table-column prop="pairAmount" label="双数" />
                                <el-table-column prop="total" label="合计" />
                            </el-table>
                        </el-col>
                    </el-row>
                    <el-row :gutter="20" style="margin-bottom: 20px;">
                        <el-col :span="23">
                            <el-table :data="bomTestData" border style="width: 100%">
                                <el-table-column prop="partName" label="部件名称" />
                                <el-table-column prop="color" label="颜色" />
                                <el-table-column prop="materialName" label="材料名称" />
                                <el-table-column prop="unit" label="单位" />
                                <el-table-column prop="unitAmount" label="单位用量" />
                                <el-table-column prop="approvedAmount" label="核定用量" />
                                <el-table-column prop="comment" label="备注" />
                            </el-table>
                        </el-col>
                    </el-row>
                </div>
                <template #footer>
                    <span>
                        <el-button type="primary" @click="closePreviewDialog">确认</el-button>
                    </span>
                </template>
            </el-dialog>

            <el-dialog title="正式BOM表下发页面" v-model="isFinalBOM" width="90%">
                <el-descriptions title="订单信息" :column="2">

                    <el-descriptions-item label="订单编号">{{ orderId }}</el-descriptions-item>
                    <el-descriptions-item label="订单创建时间">{{ testOrderData.createTime }}</el-descriptions-item>
                    <el-descriptions-item label="前序流程下发时间">{{ testOrderData.prevTime }}</el-descriptions-item>
                    <el-descriptions-item label="前序处理部门">{{ testOrderData.prevDepart }}</el-descriptions-item>
                    <el-descriptions-item label="前序处理人">{{ testOrderData.prevUser }}</el-descriptions-item>
                    <el-descriptions-item label="订单状态">{{ testOrderData.orderStatus }}</el-descriptions-item>
                </el-descriptions>
                <div style="height: 400px; overflow-y: scroll; overflow-x: hidden">
                    <el-row :gutter="20" style="margin-bottom: 20px;">
                        <el-col :span="24">
                            <el-table :data="testTableFilterData" border style="height: 400px;">
                                <el-table-column type="selection" width="55"></el-table-column>
                                <el-table-column prop="inheritId" label="工厂型号" align="center"
                                    width="100"></el-table-column>
                                <el-table-column prop="customerId" label="客户型号" align="center"></el-table-column>
                                <el-table-column label="鞋图" align="center">
                                    <template #default="scope">
                                        <el-image style="width: 150px; height: 100px" :src="scope.row.image"
                                            :fit="contain" />
                                    </template>
                                </el-table-column>
                                <el-table-column prop="designer" label="设计员" align="center"></el-table-column>
                                <el-table-column prop="editter" label="调版员" align="center"></el-table-column>
                                <el-table-column label="操作" align="center">
                                    <el-button type="primary" size="default"
                                        @click="openPreviewDialog">查看单独BOM表</el-button>
                                </el-table-column>
                            </el-table>
                        </el-col>
                    </el-row>
                </div>
                <template #footer>
                    <span>
                        <el-button @click="">取消</el-button>
                        <el-button type="primary" @click="">下发选定BOM表</el-button>
                    </span>
                </template>
            </el-dialog>

            <!-- Main content -->
        </el-main>

    </el-container>

</template>

<script>
import AllHeader from '@/components/AllHeader.vue';
import Arrow from '@/components/OrderArrowView.vue'
export default {
    props: ['orderId'],
    components: {
        AllHeader,
        Arrow
    },
    data() {
        return {
            createVis: false,
            testOrderData: {
                orderId: "123456",
                createTime: "2024-06-11",
                prevTime: "2024-06-11 12:00:00",
                prevDepart: "技术部",
                prevUser: "XXX",
                orderStatus: '未完成'
            },
            testTableData: [{
                inheritId: "0E20620",
                customerId: "VRA-1020",
                image: "/src/components/images/testShoe1.png",
                designer: "杨明清",
                editter: "潘璟",
                Status: "未填写"
            },
            {
                inheritId: "0E20620",
                customerId: "VRA-1020",
                image: "/src/components/images/testShoe1.png",
                designer: "杨明清",
                editter: "潘璟",
                Status: "已保存"
            },
            {
                inheritId: "0E20620",
                customerId: "VRA-1020",
                image: "/src/components/images/testShoe1.png",
                designer: "杨明清",
                editter: "潘璟",
                Status: "已提交"
            },],
            testTableFilterData: [],
            bomTestData: [],
            originalBomTestData: [],
            factoryOptions: [
                { materialName: '黑色超软镜面PU', factoryName: '一一鞋材' },
                { materialName: '黑色超软镜面PU', factoryName: '深源皮革' },
                { materialName: '黑色超软镜面PU', factoryName: '嘉泰皮革' },
                // Add more options here
            ],
            purchaseTestData: [
                {
                    factoryName: '一一鞋材', data: [{ num: 1, materialName: '黑色超软镜面PU', unit: '米', amount: '200', customerId: 'K24', internalModel: '0E202620', customerModel: "VRA-1020", comment: "" },
                    { num: 1, materialName: '白色超软镜面PU', unit: '米', amount: '250', customerId: 'K24', internalModel: '0E202620', customerModel: "VRA-1020", comment: "" },
                    { num: 1, materialName: '蓝色超软镜面PU', unit: '米', amount: '140', customerId: 'K24', internalModel: '0E202620', customerModel: "VRA-1020", comment: "" }]
                },
                {
                    factoryName: '深源皮革', data: [{ num: 1, materialName: '黑色超软镜面PU', unit: '米', amount: '200', customerId: 'K24', internalModel: '0E202620', customerModel: "VRA-1020", comment: "" },
                    { num: 1, materialName: '白色超软镜面PU', unit: '米', amount: '250', customerId: 'K24', internalModel: '0E202620', customerModel: "VRA-1020", comment: "" },
                    { num: 1, materialName: '蓝色超软镜面PU', unit: '米', amount: '140', customerId: 'K24', internalModel: '0E202620', customerModel: "VRA-1020", comment: "" }]
                },
                {
                    factoryName: '嘉泰皮革', data: [{ num: 1, materialName: '黑色超软镜面PU', unit: '米', amount: '200', customerId: 'K24', internalModel: '0E202620', customerModel: "VRA-1020", comment: "" },
                    { num: 1, materialName: '白色超软镜面PU', unit: '米', amount: '250', customerId: 'K24', internalModel: '0E202620', customerModel: "VRA-1020", comment: "" },
                    { num: 1, materialName: '蓝色超软镜面PU', unit: '米', amount: '140', customerId: 'K24', internalModel: '0E202620', customerModel: "VRA-1020", comment: "" }]
                },
                {
                    factoryName: '一一皮革', data: [{ num: 1, materialName: '黑色超软镜面PU', unit: '米', amount: '200', customerId: 'K24', internalModel: '0E202620', customerModel: "VRA-1020", comment: "" },
                    { num: 1, materialName: '白色超软镜面PU', unit: '米', amount: '250', customerId: 'K24', internalModel: '0E202620', customerModel: "VRA-1020", comment: "" },
                    { num: 1, materialName: '蓝色超软镜面PU', unit: '米', amount: '140', customerId: 'K24', internalModel: '0E202620', customerModel: "VRA-1020", comment: "" }]
                },
            ],
            isPreviewDialogVisible: false,
            selectedFile: null,
            inheritIdSearch: "",
            isFinalBOM: false,
            orderProduceInfo: [{
                color: '黑色',
                size: 'S12A',
                35: '0',
                36: '64',
                37: '128',
                38: '192',
                39: '192',
                40: '128',
                41: '64',
                pairAmount: 768,
                total: 1020
            },
            {
                color: '黑色',
                size: 'S12B',
                35: '0',
                36: '64',
                37: '128',
                38: '192',
                39: '192',
                40: '128',
                41: '64',
                pairAmount: 768,
                total: 1020
            },
            {
                color: '黑色',
                size: 'S6A1',
                35: '0',
                36: '64',
                37: '128',
                38: '192',
                39: '192',
                40: '128',
                41: '64',
                pairAmount: 768,
                total: 1020
            },
            {
                color: '驼色',
                size: 'S6A1',
                35: '0',
                36: '64',
                37: '128',
                38: '192',
                39: '192',
                40: '128',
                41: '64',
                pairAmount: 768,
                total: 768
            },]
        }
    },
    mounted() {
        this.tableWholeFilter()
    },
    methods: {
        openBOMCreate() {
            this.isFinalBOM = true
        },
        handleGenerate(row) {
            this.createVis = true
        },
        handleGenerateClose() {
            this.createVis = false;
        },
        getFilteredFactoryOptions(materialName) {
            const filteredOptions = this.factoryOptions.filter(option => option.materialName === materialName);
            return [{ factoryName: '询价' }, ...filteredOptions];
        },
        openPreviewDialog() {
            // Replace this with the actual logic to get the file
            this.isPreviewDialogVisible = true;
        },
        closePreviewDialog() {
            this.isPreviewDialogVisible = false
        },
        tableWholeFilter() {
            if (!this.inheritIdSearch) {
                this.testTableFilterData = this.testTableData;
                return;
            }

            this.testTableFilterData = this.testTableData.filter(task => {
                const inheritMatch = task.inheritId.includes(this.inheritIdSearch);
                return inheritMatch
            });
        },
        addNewMaterial() {
            // Validate that all existing rows have non-empty fields
            for (const row of this.bomTestData) {
                if (!row.partName || !row.color || !row.unit || !row.materialName || row.unitAmount == 0 || row.approvedAmount == 0) {
                    this.$message({
                        type: 'warning',
                        message: '请填写所有字段'
                    });
                    return;
                }
            }
            // If validation passes, add a new row
            this.bomTestData.push({
                partName: '',
                color: '',
                materialName: '',
                unit: '',
                unitAmount: 0,
                useDepart: '',
                approvedAmount: 0,
                comment: ''
            });
        },
        deleteCurrentRow(index, datafield) {
            this.$confirm('确定删除此行吗？', '提示', {
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                type: 'warning'
            }).then(() => {
                datafield.splice(index, 1);
                this.$message({
                    type: 'success',
                    message: '删除成功!'
                });
            }).catch(() => {
                this.$message({
                    type: 'info',
                    message: '已取消删除'
                });
            });
        },
        arraySpanMethod({ row, column, rowIndex, columnIndex }) {
            if (columnIndex === 0) {
                if (rowIndex > 0 && row.color === this.orderProduceInfo[rowIndex - 1].color) {
                    return [0, 0];
                }
                let rowspan = 1;
                for (let i = rowIndex + 1; i < this.orderProduceInfo.length; i++) {
                    if (this.orderProduceInfo[i].color === row.color) {
                        rowspan++;
                    } else {
                        break;
                    }
                }
                return [rowspan, 1];
            }
            if (column.property === 'total') {
                let firstOccurrenceIndex = rowIndex;
                for (let i = rowIndex - 1; i >= 0; i--) {
                    if (this.orderProduceInfo[i].color === row.color) {
                        firstOccurrenceIndex = i;
                    } else {
                        break;
                    }
                }
                if (rowIndex !== firstOccurrenceIndex) {
                    return [0, 0];
                }
                let rowspan = 1;
                for (let i = firstOccurrenceIndex + 1; i < this.orderProduceInfo.length; i++) {
                    if (this.orderProduceInfo[i].color === row.color) {
                        rowspan++;
                    } else {
                        break;
                    }
                }
                return [rowspan, 1];
            }
        }
    }
}
</script>

<style scoped>
/* Add your styles here */
</style>