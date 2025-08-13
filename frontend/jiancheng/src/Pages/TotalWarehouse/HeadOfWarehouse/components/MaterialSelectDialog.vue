<template>
    <el-dialog title="选择材料" v-model="localVisible" fullscreen @close="handleClose" destroy-on-close>
        <div v-if="selectionPage == 0">
            <el-input v-model="localSearchParams.orderRIdSearch" placeholder="搜索订单号" style="width: 300px; margin-bottom: 10px;" clearable
                @change="fetchMaterialData" @clear="fetchMaterialData"></el-input>
            <el-input v-model="localSearchParams.materialNameSearch" placeholder="搜索材料名称" style="width: 300px; margin-bottom: 10px;" clearable
                @change="fetchMaterialData" @clear="fetchMaterialData"></el-input>
            <el-input v-model="localSearchParams.materialModelSearch" placeholder="搜索材料型号" style="width: 300px; margin-bottom: 10px;" clearable
                @change="fetchMaterialData" @clear="fetchMaterialData"></el-input>
            <el-input v-model="localSearchParams.materialSpecificationSearch" placeholder="搜索材料规格" style="width: 300px; margin-bottom: 10px;" clearable
                @change="fetchMaterialData" @clear="fetchMaterialData"></el-input>
            <el-input v-model="localSearchParams.materialColorSearch" placeholder="搜索材料颜色" style="width: 300px; margin-bottom: 10px;" clearable
                @change="fetchMaterialData" @clear="fetchMaterialData"></el-input>
            <el-input v-model="localSearchParams.supplierNameSearch" placeholder="搜索供应商" style="width: 300px; margin-bottom: 10px;" clearable
                @change="fetchMaterialData" @clear="fetchMaterialData"></el-input>
            <el-switch v-model="localSearchParams.showUnfinishedOrders"
                active-text="仅显示未入库订单" inactive-text="显示所有订单" style="margin-bottom: 10px;"
                @change="fetchMaterialData"></el-switch>

            <div style="display:flex; flex-wrap: wrap; gap: 10px;">
                <div style="font-size: medium">已选择订单：{{orderSelection.map(item => item.orderRId)}}</div>
                <el-button type="primary" @click="resetSelectedOrders" style="margin-bottom: 10px;">重置</el-button>
            </div>
            <el-table :data="originTableData" border stripe height="600" @selection-change="handleSelectMaterials">
                <el-table-column type="selection" width="55"></el-table-column>
                <el-table-column prop="orderRId" label="订单号"></el-table-column>
                <el-table-column prop="shoeRId" label="工厂型号"></el-table-column>
                <el-table-column prop="materialTypeName" label="材料类型"></el-table-column>
                <el-table-column prop="supplierName" label="供货单位"></el-table-column>
                <el-table-column prop="materialName" label="材料名称"></el-table-column>
                <el-table-column prop="materialModel" label="材料型号"></el-table-column>
                <el-table-column prop="materialSpecification" label="材料规格"></el-table-column>
                <el-table-column prop="materialColor" label="颜色"></el-table-column>
                <el-table-column prop="actualInboundUnit" label="计量单位"></el-table-column>
                <el-table-column prop="remainingAmount" label="剩余入库数量"></el-table-column>
            </el-table>
            <el-pagination :current-page="localSearchParams.currentPage" :page-size="localSearchParams.pageSize"
                :total="totalRows" layout="total, sizes, prev, pager, next, jumper" @current-change="pageChange"
                @size-change="pageSizeChange">
            </el-pagination>
        </div>
        <div v-else-if="selectionPage == 1">
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
                        :precision="4" :step="0.0001" size="small"></el-input-number>
                </el-col>
                <!-- <el-col :span="12">
                    <span style="margin-right: 50px;">订单入库数量：{{ selectedInboundQuantity }}</span>
                    <span>剩余到货数量：{{ (totalInboundQuantity - selectedInboundQuantity).toFixed(5) }}</span>
                </el-col> -->
            </el-row>

            <div class="transfer-tables">
                <!-- Top Table -->
                <el-table ref="topTableData" :data="topTableData" style="width: 100%; margin-bottom: 20px;"
                    @selection-change="handleBottomSelectionChange" border stripe height="300">
                    <el-table-column type="selection" width="55"></el-table-column>
                    <el-table-column prop="orderRId" label="订单号" sortable></el-table-column>
                    <el-table-column prop="shoeRId" label="工厂型号"></el-table-column>
                    <el-table-column prop="materialName" label="材料名"></el-table-column>
                    <el-table-column prop="materialModel" label="型号"></el-table-column>
                    <el-table-column prop="materialSpecification" label="规格"></el-table-column>
                    <el-table-column prop="materialColor" label="颜色"></el-table-column>
                    <el-table-column prop="estimatedInboundAmount" label="采购数量"></el-table-column>
                    <el-table-column prop="actualInboundAmount" label="已入库数量"></el-table-column>
                    <el-table-column prop="currentAmount" label="库存"></el-table-column>
                    <el-table-column label="入库数量">
                        <template #default="scope">
                            <el-input-number v-model="scope.row.inboundQuantity" :min="0" size="small" :precision="5"
                                :step="0.0001" @change="updateSelectedInboundQuantity"></el-input-number>
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

                <!-- Bottom Table -->
                <el-table ref="bottomTableData" :data="bottomTableData" style="width: 100%;"
                    @selection-change="handleTopSelectionChange" border stripe height="300">
                    <el-table-column type="selection" width="55"></el-table-column>
                    <el-table-column prop="orderRId" label="订单号" sortable></el-table-column>
                    <el-table-column prop="shoeRId" label="工厂型号"></el-table-column>
                    <el-table-column prop="materialName" label="材料名"></el-table-column>
                    <el-table-column prop="materialModel" label="型号"></el-table-column>
                    <el-table-column prop="materialSpecification" label="规格"></el-table-column>
                    <el-table-column prop="materialColor" label="颜色"></el-table-column>
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
import Decimal from 'decimal.js';
import XEUtils from 'xe-utils';
export default {
    props: {
        visible: {
            type: Boolean,
            required: true,
        },
        searchParams: {
            type: Object,
            required: true,
        },
    },
    emits: ['confirm', 'update-visible'],
    data() {
        return {
            localVisible: this.visible,
            orderSelection: [],
            selectionPage: 0,
            bottomTableData: [],
            bottomTableDataCopy: [],
            topTableData: [],
            totalInboundQuantity: 0,
            downSelected: [],
            topSelected: [],
            selectedInboundQuantity: 0,
            unitPrice: 0,
            originTableData: [],
            searchedMaterials: [],
            localSearchParams: {
                orderRIdSearch: null,
                materialNameSearch: null,
                materialModelSearch: null,
                materialSpecificationSearch: null,
                materialColorSearch: null,
                supplierNameSearch: null,
                showUnfinishedOrders: true,
                currentPage: 1,
                pageSize: 20,
            },
            totalRows: 0,
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
    async mounted() {
        this.localSearchParams = {...this.localSearchParams, ...this.searchParams}
        await this.fetchMaterialData();
    },
    methods: {
        resetSelectedOrders() {
            this.orderSelection = [];
            this.originTableData = this.searchedMaterials;
        },
        pageChange(page) {
            this.localSearchParams.currentPage = page
            this.fetchMaterialData()
        },
        pageSizeChange(size) {
            this.localSearchParams.pageSize = size
            this.fetchMaterialData()
        },
        async fetchMaterialData() {
            const params = {
                "orderRId": this.localSearchParams.orderRIdSearch,
                "materialName": this.localSearchParams.materialNameSearch,
                "materialSpec": this.localSearchParams.materialSpecificationSearch,
                "materialModel": this.localSearchParams.materialModelSearch,
                "materialColor": this.localSearchParams.materialColorSearch,
                "supplier": this.localSearchParams.supplierNameSearch,
                "materialTypeId": this.localSearchParams.materialTypeId,
                "page": this.localSearchParams.currentPage,
                "pageSize": this.localSearchParams.pageSize,
                "showUnfinishedOrders": this.localSearchParams.showUnfinishedOrders,
            }
            const response = await axios.get(`${this.$apiBaseUrl}/warehouse/getmaterials`, { params })
            this.searchedMaterials = response.data.result
            this.totalRows = response.data.total
            // add unique id to each row
            this.searchedMaterials.forEach(item => {
                item.id = XEUtils.uniqueId()
            })
            this.originTableData = this.searchedMaterials
        },
        autoSelectOrders() {
            if (this.totalInboundQuantity <= 0) {
                ElMessage.warning('请先输入到货数量')
                return
            }
            this.topTableData = []
            this.bottomTableData = JSON.parse(JSON.stringify(this.bottomTableDataCopy))
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
        updateTotalInboundQuantity() {
            this.totalInboundQuantity = this.topTableData.reduce((acc, item) => {
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
            this.updateTotalInboundQuantity();
            this.updateSelectedInboundQuantity();
        },
        // Move selected items from bottom to top
        moveUp() {
            if (this.downSelected.length === 0) {
                ElMessage.warning('请先选择一行材料')
                return
            }
            for (let i = 0; i < this.downSelected.length; i++) {
                let remain = this.downSelected[i].estimatedInboundAmount - this.downSelected[i].actualInboundAmount
                this.downSelected[i].inboundQuantity = remain
            }
            this.topTableData = this.topTableData.concat(this.downSelected);
            this.bottomTableData = this.bottomTableData.filter(
                item => !this.downSelected.includes(item)
            );
            this.$refs.bottomTableData.clearSelection();
            this.downSelected = [];
            this.updateTotalInboundQuantity();
            this.updateSelectedInboundQuantity();
        },
        handleSelectMaterials(selection) {
            this.orderSelection = [...new Set([...this.orderSelection, ...selection])];
        },
        previousPage() {
            this.selectionPage = 0
            this.topTableData = []
            this.bottomTableData = []
            this.topSelected = []
            this.downSelected = []
            this.selectedInboundQuantity = 0
            this.totalInboundQuantity = 0
            this.unitPrice = 0
        },
        async nextPage() {
            if (this.orderSelection.length === 0) {
                ElMessage.warning('请先选择一行材料')
                return
            }
            try {
                this.bottomTableData = JSON.parse(JSON.stringify(this.orderSelection))
                this.bottomTableDataCopy = JSON.parse(JSON.stringify(this.orderSelection))
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
        confirmSelection() {
            if (this.topTableData.length === 0) {
                ElMessage.warning('请先选择一行材料')
                return
            }
            for (let i = 0; i < this.topTableData.length; i++) {
                let formatItemTotalPrice = new Decimal(this.topTableData[i].inboundQuantity).times(new Decimal(this.unitPrice)).toDecimalPlaces(4).toNumber()
                let formatInboundQuantity = new Decimal(this.topTableData[i].inboundQuantity).toDecimalPlaces(5).toNumber()
                this.topTableData[i] = {
                    ...this.topTableData[i],
                    unitPrice: this.unitPrice,
                    inboundQuantity: formatInboundQuantity,
                    itemTotalPrice: formatItemTotalPrice,
                }
            }
            let remainTotalQuantity = new Decimal(this.totalInboundQuantity).minus(new Decimal(this.selectedInboundQuantity)).toDecimalPlaces(5).toNumber()
            let remainTotalPrice = new Decimal(remainTotalQuantity).times(new Decimal(this.unitPrice)).toDecimalPlaces(4).toNumber()
            if (remainTotalQuantity > 0) {
                this.topTableData.push({
                    ...this.orderSelection[0],
                    id: XEUtils.uniqueId(),
                    orderRId: null,
                    shoeRId: null,
                    inboundQuantity: remainTotalQuantity,
                    unitPrice: this.unitPrice,
                    itemTotalPrice: remainTotalPrice,
                    inboundModel: this.orderSelection[0].materialModel,
                    inboundSpecification: this.orderSelection[0].materialSpecification,
                })
            }
            this.$emit("confirm", this.topTableData);
            this.handleClose();
        },
        handleClose() {
            this.$emit("update-visible", false);
            this.localVisible = false;
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
