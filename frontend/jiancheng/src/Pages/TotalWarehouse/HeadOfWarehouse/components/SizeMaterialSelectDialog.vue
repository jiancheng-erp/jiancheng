<template>
    <el-dialog title="选择材料" v-model="localVisible" fullscreen @close="handleClose" destroy-on-close>
        <div v-if="selectionPage == 0">
            <el-input v-model="localSearchParams.orderRIdSearch" placeholder="搜索订单号" style="width: 300px; margin-bottom: 10px;" clearable
                @change="fetchSizeMaterialData" @clear="fetchSizeMaterialData"></el-input>
            <el-input v-model="localSearchParams.materialNameSearch" placeholder="搜索材料名称" style="width: 300px; margin-bottom: 10px;"
                clearable @change="fetchSizeMaterialData" @clear="fetchSizeMaterialData"></el-input>
            <el-input v-model="localSearchParams.materialModelSearch" placeholder="搜索材料型号" style="width: 300px; margin-bottom: 10px;"
                clearable @change="fetchSizeMaterialData" @clear="fetchSizeMaterialData"></el-input>
            <el-input v-model="localSearchParams.materialSpecificationSearch" placeholder="搜索材料规格"
                style="width: 300px; margin-bottom: 10px;" clearable @change="fetchSizeMaterialData"
                @clear="fetchSizeMaterialData"></el-input>
            <el-input v-model="localSearchParams.materialColorSearch" placeholder="搜索材料颜色" style="width: 300px; margin-bottom: 10px;"
                clearable @change="fetchSizeMaterialData" @clear="fetchSizeMaterialData"></el-input>
            <el-input v-model="localSearchParams.supplierNameSearch" placeholder="搜索供应商" style="width: 300px; margin-bottom: 10px;"
                clearable @change="fetchSizeMaterialData" @clear="fetchSizeMaterialData"></el-input>
            <el-switch v-model="localSearchParams.showUnfinishedOrders" active-text="仅显示未入库订单" inactive-text="显示所有订单"
                style="margin-bottom: 10px;" @change="fetchSizeMaterialData"></el-switch>

            <div style="display:flex; flex-wrap: wrap; gap: 10px;">
                <div style="font-size: medium">已选择订单：{{orderSelection.map(item => item.orderRId)}}</div>
                <el-button type="primary" @click="resetSelectedOrders" style="margin-bottom: 10px;">重置</el-button>
            </div>
            <el-table ref="originTableData" :data="originTableData" style="width: 100%;"
                @selection-change="handleOriginSelectionChange" border stripe height="600">
                <el-table-column type="selection" width="55"></el-table-column>
                <el-table-column prop="orderRId" label="订单号" sortable></el-table-column>
                <el-table-column prop="shoeRId" label="工厂鞋型"></el-table-column>
                <el-table-column prop="supplierName" label="供货单位"></el-table-column>
                <el-table-column prop="materialTypeName" label="材料类型"></el-table-column>
                <el-table-column prop="materialName" label="材料名称"></el-table-column>
                <el-table-column prop="materialModel" label="材料型号"></el-table-column>
                <el-table-column prop="materialSpecification" label="材料规格"></el-table-column>
                <el-table-column prop="materialColor" label="材料颜色"></el-table-column>
                <el-table-column prop="remainingAmount">
                    <template #header>
                        <span>剩余入库数量</span>
                        <el-tooltip content="采购数量 - 已入库数量" placement="top" :show-after="150">
                            <el-icon class="help-icon">
                                <QuestionFilled />
                            </el-icon>
                        </el-tooltip>
                    </template>
                    <template #default="{ row }">{{ row.remainingAmount }}</template>
                </el-table-column>
                <el-table-column prop="remainingAmountRealTime">
                    <template #header>
                        <span>实时剩余数量</span>
                        <el-tooltip content="采购数量 - 已入库数量 - 当前表单已填数量（同一明细）" placement="top" :show-after="150">
                            <el-icon class="help-icon">
                                <QuestionFilled />
                            </el-icon>
                        </el-tooltip>
                    </template>
                    <template #default="{ row }">{{ row.remainingAmountRealTime }}</template>
                </el-table-column>
            </el-table>
            <el-pagination
                :current-page="localSearchParams.currentPage"
                :page-size="localSearchParams.pageSize"
                :total="totalRows"
                layout="total, sizes, prev, pager, next, jumper"
                @current-change="pageChange"
                @size-change="pageSizeChange">
            </el-pagination>
        </div>
        <div v-else>
            <el-row :gutter="20" style="margin-bottom: 20px;">
                <el-col :span="24">
                    <div style="display:flex; flex-wrap: wrap; gap: 10px;">
                        <div v-for="(shoeSize, index) in shoeSizeColumns">
                            <span>{{ shoeSize.label }}码到货数量：</span>
                            <el-input-number v-model="shoeSizeColumns[index].inboundQuantity"
                                style="width: 150px; margin-right: 10px;" :min="0" :precision="5" :step="0.0001"
                                size="small" @change="updateTotalShoes"
                                :disabled="isAmountInputBlock"></el-input-number>
                        </div>
                        <el-button size="small" type="primary" @click="autoSelectOrders">自动选择</el-button>
                        <el-button size="small" type="primary" @click="revertInboundQuantityData">重置到货数量数据</el-button>
                        <span>材料单价：</span>
                        <el-input-number v-model="unitPrice" style="width: 150px;" :min="0" :precision="4"
                            :step="0.0001" size="small"></el-input-number>
                        <span>到货数量：</span>
                        <el-input-number v-model="totalInboundQuantity" style="width: 200px; margin-right: 10px;"
                            :min="0" :precision="5" :step="0.0001" size="small" disabled></el-input-number>
                        <el-button size="small" type="primary" @click="reset">重置自动分配表格数据</el-button>
                    </div>
                </el-col>
            </el-row>

            <div class="transfer-tables">
                <!-- Top Table -->
                <h2>自动分配表格</h2>
                <el-table :data="topTableData" style="width: 100%; margin-bottom: 20px;"
                    @selection-change="handleTopTableSelectionChange" border stripe height="300">
                    <el-table-column type="selection" width="55"></el-table-column>
                    <el-table-column prop="orderRId" label="订单号" sortable></el-table-column>
                    <el-table-column prop="shoeRId" label="工厂鞋型"></el-table-column>
                    <el-table-column prop="materialName" label="材料名称"></el-table-column>
                    <el-table-column prop="materialModel" label="材料型号"></el-table-column>
                    <el-table-column prop="materialSpecification" label="材料规格"></el-table-column>
                    <el-table-column prop="materialColor" label="颜色"></el-table-column>
                    <el-table-column prop="inboundQuantity" label="入库数量"></el-table-column>
                    <el-table-column v-for="item in topTableShoeSizeColumns" :label=item.label
                        :prop="item.prop"></el-table-column>
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
                <h2>已选择订单表格</h2>
                <el-table :data="bottomTableData" style="width: 100%;"
                    @selection-change="handleBottomTableSelectionChange" border stripe height="300">
                    <el-table-column type="selection" width="55"></el-table-column>
                    <el-table-column prop="orderRId" label="订单号" sortable></el-table-column>
                    <el-table-column prop="shoeRId" label="工厂鞋型"></el-table-column>
                    <el-table-column prop="materialName" label="材料名称"></el-table-column>
                    <el-table-column prop="materialModel" label="材料型号"></el-table-column>
                    <el-table-column prop="materialSpecification" label="材料规格"></el-table-column>
                    <el-table-column prop="materialColor" label="颜色"></el-table-column>
                    <el-table-column prop="remainingAmountRealTime" label="待入库数量"></el-table-column>
                    <el-table-column v-for="item in bottomTableShoeSizeColumns" :label=item.label
                        :prop="item.prop"></el-table-column>
                </el-table>
            </div>
        </div>

        <template #footer>
            <el-button v-if="selectionPage > 0" @click="previousPage">上一步</el-button>
            <el-button v-if="selectionPage < 1" @click="nextPage">下一步</el-button>
            <el-button v-if="selectionPage == 1" @click="confirmSelection">确定</el-button>
        </template>
    </el-dialog>
</template>
<script>
import axios from 'axios';
import { ElMessage, ElMessageBox } from 'element-plus';
import Decimal from 'decimal.js';
import XEUtils from 'xe-utils'
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
        tableData: {
            type: Array,
            required: true,
        },
    },
    emits: ['confirm', 'update-visible'],
    data() {
        return {
            isAmountInputBlock: false,
            localVisible: this.visible,
            orderSelection: [],
            selectionPage: 0,
            bottomTableData: [],
            bottomTableDataCopy: [],
            topTableData: [],
            totalInboundQuantity: 0,
            unitPrice: 0,
            bottomTableShoeSizeColumns: [],
            topTableShoeSizeColumns: [],
            remainQuantityList: [],
            searchOrderRId: null,
            shoeSizeColumns: [],
            originTableData: [],
            topSelected: [],
            downSelected: [],
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
            searchedSizeMaterials: [],
            inboundTableMap: {},
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
        this.constructInboundTableMap();
        await this.fetchSizeMaterialData();
    },
    methods: {
        constructInboundTableMap() {
            for (let i = 0; i < this.$props.tableData.length; i++) {
                const item = this.$props.tableData[i];
                if (!item.shoeSizeColumns) {
                    continue;
                }
                let string = `${item.orderRId}-${item.materialName}-${item.inboundModel}-${item.inboundSpecification}-${item.materialColor}-${item.actualInboundUnit}`
                if (!(string in this.inboundTableMap)) {
                    this.inboundTableMap[string] = {"inboundQuantity": 0};
                    for (let j = 0; j < item.shoeSizeColumns.length; j++) {
                        this.inboundTableMap[string][`inboundQuantity${j}`] = 0;
                    }

                }
                this.inboundTableMap[string].inboundQuantity += item.inboundQuantity;
                for (let j = 0; j < item.shoeSizeColumns.length; j++) {
                    this.inboundTableMap[string][`inboundQuantity${j}`] += item[`amount${j}`] || 0;
                }
            }
        },
        pageChange(page) {
            this.localSearchParams.currentPage = page
            this.fetchSizeMaterialData()
        },
        pageSizeChange(size) {
            this.localSearchParams.pageSize = size
            this.fetchSizeMaterialData()
        },
        async fetchSizeMaterialData() {
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
            this.searchedSizeMaterials = response.data.result
            this.totalRows = response.data.total
            // add unique id to each row
            this.searchedSizeMaterials.forEach(item => {
                item.id = XEUtils.uniqueId()
            })
            this.originTableData = this.searchedSizeMaterials

            // 计算实时剩余数量
            this.originTableData.forEach(item => {
                let string = `${item.orderRId}-${item.materialName}-${item.materialModel}-${item.materialSpecification}-${item.materialColor}-${item.actualInboundUnit}`
                item.remainingAmountRealTime = item.remainingAmount;
                if (this.inboundTableMap[string]) {
                    item.remainingAmountRealTime = item.remainingAmount - (this.inboundTableMap[string].inboundQuantity || 0);
                }

                for (let i = 0; i < item.shoeSizeColumns.length; i++) {
                    item[`remainingAmountRealTime${i}`] = item[`remainingAmount${i}`]
                    if (this.inboundTableMap[string]) {
                        item[`remainingAmountRealTime${i}`] = item[`remainingAmount${i}`] - (this.inboundTableMap[string][`inboundQuantity${i}`] || 0);
                    }
                    
                }
            });
        },
        handleOriginSelectionChange(selection) {
            // concat and remove duplicates
            this.orderSelection = [...new Set([...this.orderSelection, ...selection])];
        },
        reset() {
            this.topTableData = [];
            this.bottomTableData = JSON.parse(JSON.stringify(this.bottomTableDataCopy));
        },
        resetSelectedOrders() {
            this.orderSelection = [];
            this.originTableData = this.searchedSizeMaterials;
        },
        handleTopTableSelectionChange(selection) {
            this.topSelected = selection;
        },
        handleBottomTableSelectionChange(selection) {
            this.downSelected = selection;
        },
        moveUp() {
            if (this.downSelected.length === 0) {
                ElMessage.warning('请先选择一行材料')
                return
            }
            for (let i = 0; i < this.downSelected.length; i++) {
                this.downSelected[i].inboundQuantity = 0;
                for (let j = 0; j < this.shoeSizeColumns.length; j++) {
                    let remainingAmountRealTime = this.downSelected[i][`remainingAmountRealTime${j}`] || 0;
                    this.downSelected[i][`amount${j}`] = remainingAmountRealTime;
                    this.downSelected[i].inboundQuantity += this.downSelected[i][`amount${j}`];
                }
            }
            this.topTableData.push(...this.downSelected);
            this.bottomTableData = this.bottomTableData.filter(item => !this.downSelected.includes(item));
            this.downSelected = [];
            this.updateQuantityInputs();
        },
        moveDown() {
            if (this.topSelected.length === 0) {
                ElMessage.warning('请先选择一行材料')
                return
            }
            this.bottomTableData.push(...this.topSelected);
            this.topTableData = this.topTableData.filter(item => !this.topSelected.includes(item));
            this.topSelected = [];
            this.updateQuantityInputs();
        },
        updateQuantityInputs() {
            this.shoeSizeColumns.forEach((item, index) => {
                item.inboundQuantity = this.topTableData.reduce((acc, row) => {
                    return acc + (row[`amount${index}`] || 0);
                }, 0);
            });
            this.updateTotalShoes();
        },
        previousPage() {
            this.selectionPage = 0;
            this.resetVariables();
        },
        nextPage() {
            let selectedOrders = this.orderSelection
            if (selectedOrders.length === 0) {
                ElMessage.warning('至少选择一个订单')
                return
            }
            this.shoeSizeColumns = selectedOrders[0].shoeSizeColumns.map((item, index) => {
                return {
                    label: item,
                    prop: `amount${index}`,
                    inboundQuantity: 0
                }
            });
            this.topTableShoeSizeColumns = this.shoeSizeColumns.map((item, index) => {
                return {
                    label: item.label,
                    prop: `amount${index}`
                }
            });
            this.bottomTableShoeSizeColumns = this.shoeSizeColumns.map((item, index) => {
                return {
                    label: item.label,
                    prop: `remainingAmountRealTime${index}`
                }
            });
            this.bottomTableDataCopy = JSON.parse(JSON.stringify(selectedOrders));
            this.bottomTableData = JSON.parse(JSON.stringify(selectedOrders));
            this.selectionPage = 1;
        },
        updateTotalShoes() {
            this.totalInboundQuantity = this.shoeSizeColumns.reduce((acc, item) => {
                return acc + (item.inboundQuantity || 0);
            }, 0);
        },
        autoSelectForSize() {
            this.remainQuantityList = JSON.parse(JSON.stringify(this.shoeSizeColumns))
            for (let i = 0; i < this.bottomTableData.length; i++) {
                let appended = false
                for (let j = 0; j < this.remainQuantityList.length; j++) {
                    let subTotal = this.remainQuantityList[j].inboundQuantity
                    let remain = this.bottomTableData[i][`remainingAmountRealTime${j}`]
                    if (subTotal <= 0 || remain <= 0) {
                        continue
                    }
                    this.bottomTableData[i][`amount${j}`] = remain <= subTotal ? remain : subTotal
                    this.remainQuantityList[j].inboundQuantity -= this.bottomTableData[i][`amount${j}`]
                    appended = true
                }
                if (appended) {
                    this.topTableData.push({ ...this.bottomTableData[i] })
                }
            }
            for (let i = 0; i < this.topTableData.length; i++) {
                this.topTableData[i].inboundQuantity = 0
                for (let j = 0; j < this.shoeSizeColumns.length; j++) {
                    this.topTableData[i][`amount${j}`] = this.topTableData[i][`amount${j}`] || 0
                    this.topTableData[i].inboundQuantity += this.topTableData[i][`amount${j}`]
                }
            }
        },
        autoSelectOrders() {
            if (this.totalInboundQuantity <= 0) {
                ElMessage.warning('请先输入到货数量')
                return
            }
            this.topTableData = []
            this.bottomTableData = JSON.parse(JSON.stringify(this.bottomTableDataCopy));
            this.autoSelectForSize()
            // filter out items that were moved to the top table by id
            let idSet = new Set(this.topTableData.map(item => item.id));
            this.bottomTableData = this.bottomTableData.filter(
                item => !idSet.has(item.id)
            );
            this.isAmountInputBlock = true;
        },
        resetVariables() {
            this.searchOrderRId = null
            this.orderSelection = []
            this.selectionPage = 0
            this.bottomTableData = []
            this.topTableData = []
            this.totalInboundQuantity = 0
            this.topTableShoeSizeColumns = []
            this.bottomTableShoeSizeColumns = []
            this.topSelected = []
            this.downSelected = []
            this.unitPrice = 0
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
            // Add remaining quantities for each shoe size
            let remainTotalQuantity = this.remainQuantityList.reduce((acc, item) => {
                return acc + (item.inboundQuantity || 0);
            }, 0);
            if (remainTotalQuantity > 0) {
                let remainObject = {
                    ...this.orderSelection[0],
                    orderRId: null,
                    shoeRId: null,
                    id: XEUtils.uniqueId(),
                    inboundQuantity: new Decimal(remainTotalQuantity).toDecimalPlaces(5).toNumber(),
                    unitPrice: this.unitPrice,
                    itemTotalPrice: new Decimal(remainTotalQuantity).times(new Decimal(this.unitPrice)).toDecimalPlaces(4).toNumber(),
                    inboundModel: this.orderSelection[0].materialModel,
                    inboundSpecification: this.orderSelection[0].materialSpecification,
                }
                for (let i = 0; i < this.remainQuantityList.length; i++) {
                    remainObject[`amount${i}`] = this.remainQuantityList[i].inboundQuantity
                }
                this.topTableData.push(remainObject)
            }
            this.isAmountInputBlock = false;
            this.$emit("confirm", this.topTableData);
            this.handleClose();
        },
        handleClose() {
            this.$emit("update-visible", false);
            this.resetVariables();
            this.localVisible = false;
        },
        revertInboundQuantityData() {
            this.shoeSizeColumns.forEach(item => {
                item.inboundQuantity = 0;
            });
            this.isAmountInputBlock = false;
            this.updateTotalShoes();
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
