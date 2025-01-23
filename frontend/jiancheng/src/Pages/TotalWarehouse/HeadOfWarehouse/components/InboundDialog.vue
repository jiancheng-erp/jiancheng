<template>
    <el-dialog title="多选材料入库" v-model="localVisible" width="80%">
        <el-form :model="inboundForm" :rules="inboundRules" ref="inboundForm">
            <el-form-item prop="date" label="入库日期">
                <el-date-picker v-model="inboundForm.date" type="datetime" placeholder="选择日期时间" style="width: 100%"
                    value-format="YYYY-MM-DD HH:mm:ss"></el-date-picker>
            </el-form-item>
            <el-form-item prop="inboundType" label="入库类型">
                <el-radio-group v-model="inboundForm.inboundType">
                    <el-radio :value="0">采购入库</el-radio>
                    <el-radio :value="1">生产剩余</el-radio>
                </el-radio-group>
            </el-form-item>
            <el-form-item prop="groupedSelectedRows" label="入库材料">
                <div v-for="(group, index) in inboundForm.groupedSelectedRows" :key="index" style="width: 100%;">
                    <el-card :header="`采购订单号: ${group.totalPurchaseOrderRId} - 供应商: ${group.supplierName}`">
                        <el-table :data="group.items" border stripe width="100%">
                            <el-table-column prop="materialName" label="材料名称"></el-table-column>
                            <el-table-column prop="materialModel" label="材料型号"></el-table-column>
                            <el-table-column prop="materialSpecification" label="材料规格"></el-table-column>
                            <el-table-column prop="colorName" label="颜色" width="80"></el-table-column>
                            <el-table-column prop="materialUnit" label="单位" width="80"></el-table-column>
                            <el-table-column prop="orderRId" label="订单号"></el-table-column>
                            <el-table-column label="入库数量" width="150">
                                <template #default="scope">
                                    <el-input-number v-if="scope.row.materialCategory == 0"
                                        v-model="scope.row.inboundQuantity" :min="0" size="small"></el-input-number>
                                    <el-button v-else type="primary"
                                        @click="openSizeMaterialQuantityDialog(scope.row)">打开</el-button>
                                </template>
                            </el-table-column>
                            <el-table-column label="单价" width="150">
                                <template #default="scope">
                                    <el-input-number v-model="scope.row.unitPrice" :min="0" :precision="2" size="small"
                                        :step="0.01"></el-input-number>
                                </template>
                            </el-table-column>
                            <el-table-column label="总价" width="100">
                                <template #default="scope">
                                    {{ scope.row.inboundQuantity * scope.row.unitPrice }}
                                </template>
                            </el-table-column>
                            <el-table-column label="备注">
                                <template #default="scope">
                                    <el-input v-model="scope.row.remark" placeholder="请输入备注" type="textarea"></el-input>
                                </template>
                            </el-table-column>
                        </el-table>
                    </el-card>
                </div>
            </el-form-item>
        </el-form>
        <template #footer>
            <el-button @click="handleClose">取消</el-button>
            <el-button type="primary" @click="submitInboundForm">入库</el-button>
        </template>
    </el-dialog>

    <el-dialog title="多鞋码入库对话框" v-model="isOpenSizeMaterialQuantityDialogVisible" width="50%">
        <el-table :data="filteredData" border stripe>
            <el-table-column prop="shoeSizeName" label="鞋码" width="100"></el-table-column>
            <el-table-column prop="predictQuantity" label="预计数量"></el-table-column>
            <el-table-column prop="actualQuantity" label="实际数量"></el-table-column>
            <el-table-column prop="currentQuantity" label="库存"></el-table-column>
            <el-table-column prop="inboundQuantity" label="入库数量">
                <template #default="scope">
                    <el-input-number v-model="scope.row.inboundQuantity" size="small" :min="0"
                        @change="updateSizeMaterialTotal"></el-input-number>
                </template>
            </el-table-column>
        </el-table>
        <template #footer>
            <span>
                <el-button @click="confirmSizeMaterialQuantity">确定</el-button>
            </span>
        </template>
    </el-dialog>
</template>
<script>
import axios from "axios";
import { ElMessage, ElMessageBox } from "element-plus";
export default {
    props: {
        visible: {
            type: Boolean,
            required: true
        },
        inboundForm: {
            type: Object,
            required: true
        },
    },
    emits: ["update-visible", "get-material-table-data"],
    data() {
        return {
            currentSizeMaterialQuantityRow: {},
            isOpenSizeMaterialQuantityDialogVisible: false,
            localVisible: this.visible,
            inboundRules: {
                date: [
                    { required: true, message: '此项为必填项', trigger: 'change' },
                ],
                inboundType: [
                    { required: true, message: '此项为必填项', trigger: 'change' },
                ],
                groupedSelectedRows: [
                    {
                        required: true,
                        validator: (rule, value, callback) => {
                            value.forEach(group => {
                                group.items.forEach(row => {
                                    if (row.inboundQuantity == 0) {
                                        callback(new Error("入库数量不能零"));
                                    } else {
                                        callback();
                                    }
                                });
                            });
                        },
                        trigger: "change",
                    },
                ],
            },
        }
    },
    watch: {
        visible(newVal) {
            this.localVisible = newVal;
        },
        localVisible(newVal) {
            this.$emit("update-visible", newVal);
        },
    },
    computed: {
        filteredData() {
            return this.currentSizeMaterialQuantityRow.sizeMaterialInboundTable.filter((row) => {
                return (
                    row.predictQuantity > 0
                );
            });
        },
    },
    methods: {
        handleClose() {
            this.localVisible = false;
        },
        async submitInboundForm() {
            this.$refs.inboundForm.validate(async (valid) => {
                if (valid) {
                    ElMessageBox.confirm('确定入库吗?', '提示', {
                        confirmButtonText: '确定',
                        cancelButtonText: '取消',
                        type: 'warning'
                    }).then(async () => {
                        try {
                            let data = []
                            for (let row of this.inboundForm.groupedSelectedRows) {
                                let obj = {
                                    inboundTimestamp: this.inboundForm.date,
                                    inboundType: this.inboundForm.inboundType,
                                    items: []
                                }
                                for (let item of row.items) {
                                    let detail = {
                                        materialStorageId: item.materialStorageId,
                                        inboundQuantity: item.inboundQuantity,
                                        unitPrice: item.unitPrice,
                                        materialCategory: item.materialCategory,
                                        remark: item.remark,
                                        materialCategory: item.materialCategory,
                                    }
                                    for (let i = 0; i < item.sizeMaterialInboundTable.length; i++) {
                                        detail[`amount${i}`] = item[`amount${i}`]
                                    }
                                    obj.items.push(detail)
                                }
                                data.push(obj)
                            }
                            console.log(data)
                            await axios.patch(`${this.$apiBaseUrl}/warehouse/warehousemanager/inboundmaterial`, data);
                            ElMessage.success("入库成功");
                            this.$emit("get-material-table-data");
                            this.handleClose();
                        } catch (error) {
                            ElMessage.error("入库失败");
                        }
                    }
                    ).catch(() => {
                        ElMessage.info("取消入库");
                    });
                } else {
                    ElMessage.error("请填写完整信息");
                }
            });
        },
        confirmSizeMaterialQuantity() {
            this.isOpenSizeMaterialQuantityDialogVisible = false
        },
        updateSizeMaterialTotal() {
            this.currentSizeMaterialQuantityRow.sizeMaterialInboundTable.forEach((element, index) => {
                this.currentSizeMaterialQuantityRow[`amount${index}`] = element.inboundQuantity
            })
            this.currentSizeMaterialQuantityRow.inboundQuantity = this.filteredData.reduce((acc, row) => {
                return acc + row.inboundQuantity;
            }, 0);
        },
        openSizeMaterialQuantityDialog(row) {
            this.currentSizeMaterialQuantityRow = row
            this.isOpenSizeMaterialQuantityDialogVisible = true
        },
    },
}
</script>