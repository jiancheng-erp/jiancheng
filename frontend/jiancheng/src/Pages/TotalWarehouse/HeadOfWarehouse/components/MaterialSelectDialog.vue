<template>
    <el-dialog title="选择材料" v-model="localVisible" fullscreen @close="handleClose">
        <div v-if="selectionPage == 0">
            <el-table :data="searchedMaterials" border stripe height="600">
                <el-table-column label="选择" align="center" width="65">
                    <template #default="scope">
                        <el-radio :label="scope.$index" v-model="selectionIndex"
                            @change="handleSelectMaterials(scope.row)" class="radio-class"></el-radio>
                    </template>
                </el-table-column>
                <el-table-column prop="supplierName" label="供货单位"></el-table-column>
                <el-table-column prop="materialName" label="材料名称"></el-table-column>
                <el-table-column prop="materialModel" label="材料型号"></el-table-column>
                <el-table-column prop="materialSpecification" label="材料规格"></el-table-column>
                <el-table-column prop="materialColor" label="颜色"></el-table-column>
                <el-table-column prop="actualInboundUnit" label="计量单位"></el-table-column>
            </el-table>
        </div>
        <div v-else-if="selectionPage == 1">
            <el-descriptions border style="margin-bottom: 20px;">
                <el-descriptions-item label="名称">{{ materialSelection.materialName }}</el-descriptions-item>
                <el-descriptions-item label="型号">{{ materialSelection.materialModel }}</el-descriptions-item>
                <el-descriptions-item label="规格">{{ materialSelection.materialSpecification }}</el-descriptions-item>
                <el-descriptions-item label="颜色">{{ materialSelection.materialColor }}</el-descriptions-item>
                <el-descriptions-item label="单位">{{ materialSelection.actualInboundUnit }}</el-descriptions-item>
            </el-descriptions>
            <el-row :gutter="20" style="margin-bottom: 20px;">
                <el-col :span="6">
                    <span>到货数量：</span>
                    <el-input-number v-model="totalInboundQuantity" style="width: 200px; margin-right: 10px;" :min="0"
                        :precision="5" :step="0.0001" size="small"></el-input-number>
                    <el-button size="small" type="primary" @click="autoSelectOrders">自动选择</el-button>
                </el-col>
                <el-col :span="6">
                    <span>材料单价：</span>
                    <el-input-number v-model="unitPrice" style="width: 200px;" :min="0"
                        :precision="3" :step="0.001" size="small"></el-input-number>
                </el-col>
                <el-col :span="12">
                    <span style="margin-right: 50px;">订单入库数量：{{ selectedInboundQuantity }}</span>
                    <span>剩余到货数量：{{ totalInboundQuantity - selectedInboundQuantity }}</span>
                </el-col>
            </el-row>

            <div class="transfer-tables">
                <!-- Top Table -->
                <el-table ref="topTableData" :data="sortTopTableData" style="width: 100%; margin-bottom: 20px;"
                    @selection-change="handleBottomSelectionChange" border stripe height="300">
                    <el-table-column type="selection" width="55"></el-table-column>
                    <el-table-column prop="orderRId" label="订单号"></el-table-column>
                    <el-table-column prop="startDate" label="开始日期"></el-table-column>
                    <el-table-column prop="endDate" label="结束日期"></el-table-column>
                    <el-table-column prop="estimatedInboundAmount" label="采购数量"></el-table-column>
                    <el-table-column prop="actualInboundAmount" label="已入库数量"></el-table-column>
                    <el-table-column prop="currentAmount" label="库存"></el-table-column>
                    <el-table-column label="操作">
                        <template #default="scope">
                            <el-input-number v-model="scope.row.inboundQuantity" :min="0" size="small" :precision="5"
                                :step="0.0001" @change="update"></el-input-number>
                        </template>
                    </el-table-column>
                </el-table>

                <!-- Control Buttons -->
                <div class="transfer-buttons" style="text-align: center; margin-bottom: 20px;">
                    <el-button type="primary" @click="moveUp" :disabled="downSelected.length === 0">
                        选择 <el-icon>
                            <Top />
                        </el-icon>
                    </el-button>
                    <el-button type="primary" @click="moveDown" :disabled="topSelected.length === 0"
                        style="margin-left: 20px;">
                        <el-icon>
                            <Bottom />
                        </el-icon> 移除
                    </el-button>
                </div>

                <!-- Search Input for Bottom Table -->

                <!-- <el-input v-model="totalInboundQuantity" placeholder="搜索订单号" style="width: 300px; margin-bottom: 10px;"
                        clearable @change="searchOrderRId" @clear="searchOrderRId"></el-input> -->

                <!-- Bottom Table -->
                <el-table ref="bottomTableData" :data="sortBottomTableData" style="width: 100%;"
                    @selection-change="handleTopSelectionChange" border stripe height="300">
                    <el-table-column type="selection" width="55"></el-table-column>
                    <el-table-column prop="orderRId" label="订单号"></el-table-column>
                    <el-table-column prop="startDate" label="开始日期"></el-table-column>
                    <el-table-column prop="endDate" label="结束日期"></el-table-column>
                    <el-table-column prop="estimatedInboundAmount" label="采购数量"></el-table-column>
                    <el-table-column prop="actualInboundAmount" label="已入库数量"></el-table-column>
                    <el-table-column prop="currentAmount" label="库存"></el-table-column>
                </el-table>
            </div>
        </div>
        <template #footer>
            <el-button v-if="selectionPage == 1" @click="previousPage">上一步</el-button>
            <el-button v-if="selectionPage == 0" @click="nextPage">下一步</el-button>
            <el-button v-else-if="selectionPage == 1" @click="confirmSelection">确定</el-button>
        </template>
    </el-dialog>
</template>
<script>
import axios from 'axios';
import { ElMessage, ElMessageBox } from 'element-plus';
export default {
    props: {
        visible: {
            type: Boolean,
            required: true,
        },
        searchedMaterials: {
            type: Array,
            required: true,
        },
    },
    emits: ['update-visible'],
    computed: {
        sortTopTableData() {

            return this.topTableData.sort(this.naturalSort);
        },
        sortBottomTableData() {
            return this.bottomTableData.sort(this.naturalSort);
        },
    },
    data() {
        return {
            localVisible: this.visible,
            materialSelection: {},
            orderSelection: {},
            currentIndex: -1,
            selectionIndex: null,
            selectionIndex2: null,
            shoeSizeColumns: [],
            selectionPage: 0,
            bottomTableData: [],
            topTableData: [],
            totalInboundQuantity: '',
            downSelected: [],
            topSelected: [],
            selectedInboundQuantity: 0,
            unitPrice: 0,
            originTableData: [],
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
    methods: {
        autoSelectOrders() {
            if (this.totalInboundQuantity <= 0) {
                ElMessage.warning('请先输入到货数量')
                return
            }
            this.topTableData = []
            this.bottomTableData = [...this.originTableData]
            let remainTotalQuantity = this.totalInboundQuantity
            for (let i = 0; i < this.bottomTableData.length; i++) {
                let remain = this.bottomTableData[i].estimatedInboundAmount - this.bottomTableData[i].actualInboundAmount
                if (remain <= 0) {
                    continue
                }
                this.bottomTableData[i].inboundQuantity = remain > remainTotalQuantity ? remainTotalQuantity : remain
                remainTotalQuantity -= this.bottomTableData[i].inboundQuantity
                this.topTableData.push(this.bottomTableData[i])
                if (remainTotalQuantity <= 0) {
                    break
                }
            }
            this.bottomTableData = this.bottomTableData.filter(
                item => !this.topTableData.includes(item)
            );
            this.selectedInboundQuantity = this.topTableData.reduce((acc, item) => {
                return acc + (item.inboundQuantity || 0);
            }, 0);
        },
        naturalSort(a, b) {
            // Split the string into two parts: the prefix and the numeric part
            const [prefixA, numA] = a.orderRId.split('-');
            const [prefixB, numB] = b.orderRId.split('-');
            // First compare the alphabetical prefixes
            if (prefixA < prefixB) return -1;
            if (prefixA > prefixB) return 1;
            // If the prefixes are equal, compare the numeric parts
            return parseInt(numA, 10) - parseInt(numB, 10);
        },
        // Capture selection change for the top table
        handleTopSelectionChange(selection) {
            this.downSelected = selection;
        },
        // Capture selection change for the bottom table
        handleBottomSelectionChange(selection) {
            this.topSelected = selection;
        },
        updateSelectedInboundQuantity() {
            this.selectedInboundQuantity = this.topTableData.reduce((acc, item) => {
                return acc + (item.inboundQuantity || 0);
            }, 0);
        },
        // Move selected items from top to bottom
        moveDown() {
            this.bottomTableData = this.bottomTableData.concat(this.topSelected);
            this.topTableData = this.topTableData.filter(
                item => !this.topSelected.includes(item)
            );
            this.$refs.topTableData.clearSelection();
            this.topSelected = [];
            this.updateSelectedInboundQuantity();
        },
        // Move selected items from bottom to top
        moveUp() {
            let remainTotalQuantity = this.totalInboundQuantity - this.selectedInboundQuantity
            if (remainTotalQuantity <= 0) {
                ElMessage.warning('剩余到货数量不足，请重新选择')
                return
            }
            for (let i = 0; i < this.downSelected.length; i++) {
                let remain = this.downSelected[i].estimatedInboundAmount - this.downSelected[i].actualInboundAmount
                this.downSelected[i].inboundQuantity = remain > remainTotalQuantity ? remainTotalQuantity : remain
                remainTotalQuantity -= this.downSelected[i].inboundQuantity
                if (remainTotalQuantity <= 0) {
                    break
                }
            }
            this.topTableData = this.topTableData.concat(this.downSelected);
            this.bottomTableData = this.bottomTableData.filter(
                item => !this.downSelected.includes(item)
            );
            this.$refs.bottomTableData.clearSelection();
            this.downSelected = [];
            this.updateSelectedInboundQuantity();
        },
        handleSelectMaterials(row) {
            console.log(row)
            this.materialSelection = row;
        },
        previousPage() {
            this.selectionPage = 0
            this.topTableData = []
            this.bottomTableData = []
            this.topSelected = []
            this.downSelected = []
            this.selectedInboundQuantity = 0
            this.totalInboundQuantity = 0
        },
        async nextPage() {
            if (this.selectionIndex == null) {
                ElMessage.warning('请先选择一行材料')
                return
            }
            try {
                console.log(this.materialSelection)
                let params = {
                    "materialName": this.materialSelection.materialName,
                    "materialSpec": this.materialSelection.materialSpecification,
                    "materialModel": this.materialSelection.materialModel,
                    "materialColor": this.materialSelection.materialColor,
                    "supplierName": this.materialSelection.supplierName,
                    "unit": this.materialSelection.actualInboundUnit,
                    "materialCategory": this.materialSelection.materialCategory,
                }
                let response = await axios.get(`${this.$apiBaseUrl}/warehouse/getordersbymaterialinfo`, { params })
                this.originTableData = response.data
                this.bottomTableData = response.data
                this.selectionPage = 1
            }
            catch (error) {
                console.error("Error fetching material details:", error);
                let errorMessage = "服务器异常";
                if (error.response) {
                    // Flask returns error in JSON format
                    errorMessage = error.response.data.message;
                }
                ElMessage.error(errorMessage)

            }
        },
        resetVariables() {
            this.materialSelection = {}
            this.orderSelection = {}
            this.currentIndex = -1
            this.selectionIndex = null
            this.selectionIndex2 = null
            this.shoeSizeColumns = []
            this.selectionPage = 0
            this.bottomTableData = []
            this.topTableData = []
            this.totalInboundQuantity = ''
            this.downSelected = []
            this.topSelected = []
            this.selectedInboundQuantity = 0,
            this.localVisible = false
        },
        confirmSelection() {
            if (this.topTableData.length === 0) {
                ElMessage.warning('请先选择一行材料')
                return
            }
            for (let i = 0; i < this.topTableData.length; i++) {
                this.topTableData[i] = {
                    ...this.topTableData[i],
                    ...this.materialSelection,
                    disableEdit: true,
                    unitPrice: this.unitPrice,
                    itemTotalPrice: (this.topTableData[i].inboundQuantity * this.unitPrice).toFixed(3),
                }
            }
            let remainTotalQuantity = this.totalInboundQuantity - this.selectedInboundQuantity
            if (remainTotalQuantity > 0) {
                this.topTableData.push({
                    orderRId: null,
                    inboundQuantity: remainTotalQuantity,
                    ...this.materialSelection,
                    disableEdit: true,
                    unitPrice: this.unitPrice,
                    itemTotalPrice: (remainTotalQuantity * this.unitPrice).toFixed(3),
                })
            }
            this.$emit("confirm", this.topTableData);
            this.$emit("update-visible", false);
            this.resetVariables()
        },
        handleClose() {
            this.$emit("update-visible", false);
            this.resetVariables()
        },
    },
}
</script>
<style scoped>
.transfer-tables {
    width: 100%;
    margin: 0 auto;
}
</style>
