<template>
    <el-row :gutter="20">
        <el-col :span="6" :offset="0">
            <el-button-group>
                <el-button type="primary" size="default" @click="isMaterialDialogVisible = true">搜索条件设置</el-button>
                <el-button v-if="isMultipleSelection" @click="confirmOrderShoesToOutbound">
                    出库
                </el-button>
                <el-button v-if="isMultipleSelection" @click="openFinishOutboundDialog">
                    完成出库
                </el-button>
                <el-button @click="toggleSelectionMode">
                    {{ isMultipleSelection ? "退出" : "选择材料" }}
                </el-button>
            </el-button-group>
        </el-col>
        <MaterialSearchDialog :visible="isMaterialDialogVisible" :materialSupplierOptions="materialSupplierOptions"
            :materialTypeOptions="materialTypeOptions" :material-name-options="materialNameOptions" :searchForm="searchForm" @update-visible="updateDialogVisible"
            @confirm="handleSearch" />
    </el-row>
    <el-row :gutter="20">
        <el-col :span="24">
            <el-table :data="materialTableData" border stripe height="600" @sort-change="sortData"
                @selection-change="handleSelectionChange">
                <el-table-column v-if="isMultipleSelection" type="selection" width="55" />
                <el-table-column prop="totalPurchaseOrderCreateDate" label="采购订单日期" width="120" sortable="custom">
                </el-table-column>
                <el-table-column label="采购订单号" width="100">
                    <template #default="scope">
                        <el-tooltip effect="dark" :content="scope.row.totalPurchaseOrderRId" placement="bottom">
                            <span class="truncate-text">
                                {{ scope.row.totalPurchaseOrderRId }}
                            </span>
                        </el-tooltip>
                    </template>
                </el-table-column>
                <el-table-column prop="materialType" label="材料类型"></el-table-column>
                <el-table-column prop="materialName" label="材料名称"></el-table-column>
                <el-table-column prop="materialModel" label="材料型号"></el-table-column>
                <el-table-column prop="materialSpecification" label="材料规格"></el-table-column>
                <el-table-column prop="craftName" label="复合工艺" width="120">
                    <template #default="scope">
                        <el-tooltip effect="dark" :content="scope.row.craftName" placement="bottom">
                            <span class="truncate-text">
                                {{ scope.row.craftName }}
                            </span>
                        </el-tooltip>
                    </template>
                </el-table-column>
                <el-table-column prop="colorName" label="颜色"></el-table-column>
                <!-- <el-table-column prop="materialUnit" label="材料单位"></el-table-column> -->
                <el-table-column label="材料应入库数量">
                    <template #default="scope">
                        {{ Number(scope.row.estimatedInboundAmount).toFixed(2) + scope.row.materialUnit }}
                    </template>
                </el-table-column>
                <el-table-column label="材料实入库数量">
                    <template #default="scope">
                        {{ Number(scope.row.actualInboundAmount).toFixed(2) + scope.row.actualInboundUnit }}
                    </template>
                </el-table-column>
                <el-table-column prop="currentAmount" label="材料库存" :formatter="formatDecimal"></el-table-column>
                <el-table-column prop="unitPrice" label="材料单价" :formatter="formatDecimal"></el-table-column>
                <el-table-column prop="totalPrice" label="材料总价" :formatter="formatDecimal"></el-table-column>
                <el-table-column prop="supplierName" label="材料供应商"></el-table-column>
                <el-table-column prop="orderRId" label="材料订单号"></el-table-column>
                <el-table-column prop="shoeRId" label="材料鞋型号"></el-table-column>
            </el-table>
        </el-col>
    </el-row>
    <el-row :gutter="20">
        <el-col :span="12" :offset="14">
            <el-pagination @size-change="handleSizeChange" @current-change="handlePageChange"
                :current-page="currentPage" :page-sizes="[10, 20, 30, 40]" :page-size="pageSize"
                layout="total, sizes, prev, pager, next, jumper" :total="materialTableData.length" />
        </el-col>
    </el-row>

    <el-dialog title="多选材料出库" v-model="isMultiOutboundDialogVisible" width="70%" :close-on-click-modal="false">
        <el-tabs v-model="activeTab">
            <el-tab-pane v-for="(group, index) in outboundForm.groupedSelectedRows" :key="group.orderShoeId"
                :label="`订单鞋型 ${group.items[0].selectedOrderRId} - ${group.items[0].selectedShoeRId}`"
                :name="group.orderShoeId">
                <el-form :model="group" :rules="rules" :ref="'outboundForm' + index" :key="index">
                    <el-form-item prop="timestamp" label="出库日期">
                        <el-date-picker v-model="group.timestamp" type="datetime" placeholder="选择日期时间"
                            style="width: 50%" value-format="YYYY-MM-DD HH:mm:ss" :default-value="new Date()"
                            @change="syncTimestamp(group)">
                        </el-date-picker>
                    </el-form-item>
                    <el-form-item prop="outboundType" label="出库类型">
                        <el-radio-group v-model="group.outboundType">
                            <el-radio :value="0">生产使用</el-radio>
                            <el-radio :value="3">外发复合</el-radio>
                            <el-radio :value="2">外包发货</el-radio>
                            <el-radio :value="1">废料处理</el-radio>
                        </el-radio-group>
                    </el-form-item>
                    <!-- 生产使用的form item -->
                    <div v-if="group.outboundType == 0">
                        <el-form-item prop="section" label="出库工段">
                            <el-select v-model="group.section" placeholder="请输入出库工段" style="width: 240px">
                                <el-option v-for="item in departmentOptions" :label="item.label"
                                    :value="item.value"></el-option>
                            </el-select>
                        </el-form-item>
                        <el-form-item prop="receiver" label="领料人">
                            <el-input v-model="group.receiver" placeholder="请输入领料人"></el-input>
                        </el-form-item>
                    </div>
                    <!-- 外包发货的form item -->
                    <div v-else-if="group.outboundType == 2">
                        <el-form-item prop="selectedOutsourceId" label="现有外包">
                            <el-table border stripe :data="group.outsourceInfo" style="width: 100%">
                                <el-table-column width="55">
                                    <template #default="scope">
                                        <el-radio v-model="group.selectedOutsourceId" :value="scope.row.outsourceInfoId"
                                            @change="(arg) => handleFactoryChange(arg, scope.row)" />
                                    </template>
                                </el-table-column>
                                <el-table-column prop="outsourceFactory.value" label="工厂名称" />
                                <el-table-column prop="outsourceAmount" label="外包数量" />
                                <el-table-column prop="outsourceType" label="外包类型" />
                            </el-table>
                        </el-form-item>
                    </div>
                    <!-- 外发复合的form item -->
                    <div v-else-if="group.outboundType == 3">
                        <el-form-item prop="selectedCompositeSupplier" label="供应商">
                            <div style="display: flex; align-items: center; gap: 10px;">
                                <el-select v-model="group.selectedCompositeSupplier" placeholder="请输入供应商"
                                    style="width: 240px">
                                    <el-option v-for="item in compositeSuppliersOptions" :label="item.supplierName"
                                        :value="item.supplierId"></el-option>
                                </el-select>
                            </div>
                        </el-form-item>
                    </div>

                    <el-form-item prop="outboundAddress" v-if="[2, 3].includes(group.outboundType)" label="发货地址">
                        <el-input v-model="group.outboundAddress" placeholder="请输入发货地址"></el-input>
                    </el-form-item>
                    <el-form-item prop="items" label="出库数量" v-if="group.outboundType != 3">
                        <el-table :data="group.items" style="width: 100%" border stripe>
                            <el-table-column prop="materialName" label="材料名称" />
                            <el-table-column prop="materialModel" label="材料型号" />
                            <el-table-column prop="materialSpecification" label="材料规格" />
                            <el-table-column prop="colorName" label="颜色" />
                            <el-table-column label="库存">
                                <template #default="scope">
                                    <span>{{ scope.row.currentAmount + scope.row.actualInboundUnit }}</span>
                                </template>
                            </el-table-column>
                            <el-table-column prop="outboundQuantity" label="出库数量">
                                <template #default="scope">
                                    <el-input-number v-if="scope.row.materialCategory == 0" size="small"
                                        v-model="scope.row.outboundQuantity" :min="0" :precision="5"
                                        :step="0.00001"></el-input-number>
                                    <el-button v-else type="primary"
                                        @click="openSizeMaterialQuantityDialog(scope.row)">打开</el-button>
                                </template>
                            </el-table-column>
                            <el-table-column prop="remark" label="备注">
                                <template #default="scope">
                                    <el-input v-model="scope.row.remark" :maxlength="40" show-word-limit size="small">

                                    </el-input>
                                </template>
                            </el-table-column>
                        </el-table>
                    </el-form-item>
                    <el-form-item prop="items" label="选择材料" v-if="group.outboundType == 3">
                        <el-table :data="getMaterialsWithCraftNames(group.items)" style="width: 100%" border stripe
                            default-expand-all>
                            <el-table-column type="expand">
                                <template #default="props">
                                    <el-table :data="props.row.craftNameList" border stripe
                                        @selection-change="handleCompositeSelectionChange">
                                        <el-table-column prop="craftName" label="复合工艺" />
                                        <el-table-column prop="outboundQuantity" label="出库数量">
                                            <template #default="scope">
                                                <el-input-number size="small" v-model="scope.row.outboundQuantity"
                                                    :min="0" :max="Number(props.row.currentAmount)" :precision="5"
                                                    :step="0.00001"
                                                    @change="(newVal, oldVal) => handleCompositeAmountChange(newVal, oldVal, props.row)"></el-input-number>
                                            </template>
                                        </el-table-column>
                                        <el-table-column prop="remark" label="备注">
                                            <template #default="scope">
                                                <el-input v-model="scope.row.remark" :maxlength="40" show-word-limit
                                                    type="textarea"></el-input>
                                            </template>
                                        </el-table-column>
                                    </el-table>
                                </template>
                            </el-table-column>
                            <el-table-column prop="materialName" label="材料名称" />
                            <el-table-column prop="materialModel" label="材料型号" />
                            <el-table-column prop="materialSpecification" label="材料规格" />
                            <el-table-column prop="colorName" label="颜色" />
                            <el-table-column prop="currentAmount" label="库存" />
                            <el-table-column prop="materialUnit" label="单位" />
                        </el-table>
                    </el-form-item>
                </el-form>
            </el-tab-pane>
        </el-tabs>
        <template #footer>
            <span>
                <el-button @click="isMultiOutboundDialogVisible = false">取消</el-button>
                <el-button type="primary" @click="submitOutboundForm">出库</el-button>
            </span>
        </template>
    </el-dialog>

    <el-dialog title="多鞋码材料出库数量" v-model="isOpenSizeMaterialQuantityDialogVisible" width="50%">
        <el-form>
            <el-form-item>
                <el-table :data="filteredData" border stripe>
                    <el-table-column prop="shoeSizeName" label="鞋码"></el-table-column>
                    <el-table-column prop="currentQuantity" label="库存"></el-table-column>
                    <el-table-column label="单位">
                        <template #default="scope">
                            <span>{{ this.currentSizeMaterialQuantityRow.actualInboundUnit }}</span>
                        </template>
                    </el-table-column>
                    <el-table-column label="出库数量">
                        <template #default="scope">
                            <el-input-number v-model="scope.row.outboundQuantity" size="small" :min="0"
                                :max="Number(scope.row.currentQuantity)"
                                @change="updateSizeMaterialTotal"></el-input-number>
                        </template>
                    </el-table-column>
                </el-table>
            </el-form-item>
        </el-form>
        <template #footer>
            <el-button type="primary" @click="isOpenSizeMaterialQuantityDialogVisible = false">
                确认
            </el-button>
        </template>
    </el-dialog>

    <el-dialog title="确认订单鞋型" v-model="isConfirmOrderShoesDialogOpen" width="50%" :close-on-click-modal="false">
        <el-table :data="outboundForm.assetRows" border stripe>
            <el-table-column prop="selectedOrderRId" label="订单号"></el-table-column>
            <el-table-column prop="selectedShoeRId" label="鞋型号"></el-table-column>
            <el-table-column prop="materialName" label="材料名称"></el-table-column>
            <el-table-column prop="materialSpecification" label="材料规格"></el-table-column>
            <el-table-column prop="materialModel" label="材料型号"></el-table-column>
            <el-table-column prop="colorName" label="颜色"></el-table-column>
            <el-table-column label="操作">
                <template #default="scope">
                    <el-button type="primary" size="small" @click="openSelectOrderDialog(scope.row)">选择订单</el-button>
                </template>
            </el-table-column>
        </el-table>
        <template #footer>
            <!-- <el-button @click="isConfirmOrderShoesDialogOpen = false">返回</el-button> -->
            <el-button type="primary" @click="openMultipleOutboundDialog">继续</el-button>
        </template>
    </el-dialog>

    <el-dialog title="选择订单" v-model="isSelectOrderDialogOpen" width="50%" :close-on-click-modal="false">
        <el-input v-model="shoeSearch" placeholder="搜索订单号或工厂型号" class="mb-2" clearable>
        </el-input>
        <el-table :data="filterOrderShoes(currentSelectedAssetRow.orderId)" border stripe>
            <el-table-column width="55">
                <template #default="scope">
                    <el-radio-group v-model="currentSelectedAssetRow.orderShoeId">
                        <el-radio :value="scope.row.orderShoeId" @change="handleShoeSelection(scope.row)">
                        </el-radio>
                    </el-radio-group>
                </template>
            </el-table-column>
            <el-table-column prop="orderRId" label="订单号"></el-table-column>
            <el-table-column prop="shoeRId" label="工厂型号"></el-table-column>
        </el-table>
        <el-pagination :current-page="currentShoePage" :page-size="shoePageSize" :total="filteredOrderShoes.length"
            @current-change="handleShoePageChange" layout="prev, pager, next"></el-pagination>
        <!-- <div v-else>
            <el-descriptions :column="2" border>
                <el-descriptions-item label="订单号"> {{ currentSelectedAssetRow.orderRId }}</el-descriptions-item>
                <el-descriptions-item label="工厂型号"> {{ currentSelectedAssetRow.shoeRId }}</el-descriptions-item>
            </el-descriptions>
        </div> -->
        <template #footer>
            <el-button @click="confirmSelectOrderShoe">确定</el-button>
        </template>
    </el-dialog>

    <el-dialog title="推进出库流程" v-model="isFinishOutboundDialogOpen" width="50%" :close-on-click-modal="false">
        <el-descriptions title="已选择订单鞋型" style="margin-top: 20px;">
        </el-descriptions>
        <el-table :data="selectedRows" border stripe>
            <el-table-column prop="orderRId" label="订单号">
            </el-table-column>
            <el-table-column prop="shoeRId" label="鞋型号">
            </el-table-column>
            <el-table-column prop="materialName" label="材料名称">
            </el-table-column>
        </el-table>
        <template #footer>
            <el-button @click="isFinishOutboundDialogOpen = false">返回</el-button>
            <el-button @click="finishOutbound">完成出库</el-button>
        </template>
    </el-dialog>
</template>
<script>
import axios from 'axios';
import { ElMessage, ElMessageBox } from 'element-plus';
import { getShoeSizesName } from '@/Pages/utils/getShoeSizesName';
import MaterialSearchDialog from './MaterialSearchDialog.vue';
export default {
    components: {
        MaterialSearchDialog
    },
    props: {
        materialTypeOptions: {
            type: Array,
            required: true,
        },
        materialSupplierOptions: {
            type: Array,
            required: true
        },
        materialNameOptions: {
            type: Array,
            required: true
        },
    },
    data() {
        return {
            searchForm: {
                orderNumberSearch: '',
                shoeNumberSearch: '',
                materialTypeSearch: '',
                materialNameSearch: '',
                materialSpecificationSearch: '',
                materialModelSearch: '',
                materialColorSearch: '',
                materialSupplierSearch: '',
                totalPurchaseOrderRIdSearch: "",
            },
            outboundForm: {
                // groupedSelectedRows contains formItemTemplate,
                // selectedOrderShoeId, selectedOrderId, selectedOrderRId, and selectedShoeId
                // because some materials don't have orderId or orderShoeId
                groupedSelectedRows: [],
                assetRows: [],
            },
            formItemTemplate: {
                timestamp: null,
                outboundType: null,
                outboundQuantity: 0,
                section: null,
                receiver: null,
                outboundAddress: null,
                deadlineDate: null,
                outsourceInfoId: null,
                outsourceInfo: [],
                selectedOutsourceId: '',
                selectedOutsourceFactory: '',
                materials: [],
                selectedCompositeSupplier: null,
            },
            currentPage: 1,
            pageSize: 10,
            materialTableData: [],
            isMaterialDialogVisible: false,
            materialDialogData: {},
            // for example, {"value": 1, "label": "部门1"}
            departmentOptions: [],
            totalRows: 0,
            currentRow: {},
            isMultipleSelection: false,
            selectedRows: [],
            isSelectedRowsEmpty: false,
            getShoeSizesName,
            isMultiOutboundDialogVisible: false,
            isOpenSizeMaterialQuantityDialogVisible: false,
            selectedSizeMaterialData: [],
            isFinishOutboundDialogOpen: false,
            uniqueSelectedRows: [],
            rules: {
                timestamp: [
                    { required: true, message: '此项为必填项', trigger: 'change' },
                ],
                outboundType: [
                    { required: true, message: '此项为必填项', trigger: 'change' },
                ],
                section: [
                    {
                        required: true,
                        validator: (rule, value, callback) => {
                            const relatedIndex = this.outboundForm.groupedSelectedRows.findIndex(
                                (group) => group.section === value
                            );
                            if (this.outboundForm.groupedSelectedRows[relatedIndex].outboundType == 0 && value === null) {
                                callback(new Error('此项为必填项'));
                            } else {
                                callback();
                            }
                        },
                        trigger: 'change'
                    }
                ],
                // outboundAddress: [
                //     {
                //         required: true,
                //         validator: (rule, value, callback) => {
                //             const relatedIndex = this.outboundForm.groupedSelectedRows.findIndex(
                //                 (group) => group.outboundAddress === value
                //             );
                //             if ([2, 3].includes(this.outboundForm.groupedSelectedRows[relatedIndex].outboundType) && !value) {
                //                 callback(new Error('此项为必填项'));
                //             } else {
                //                 callback();
                //             }
                //         },
                //         trigger: 'change'
                //     }
                // ],
                items: [
                    {
                        required: true,
                        validator: (rule, value, callback) => {
                            let flag = true;
                            for (let row of value) {
                                if (row.outboundQuantity == 0) {
                                    flag = false;
                                    break;
                                }
                            }
                            if (!flag) {
                                callback(new Error("出库数量不能零"));
                            } else {
                                callback();
                            }
                        },
                        trigger: "change",
                    },
                ],
                selectedCompositeSupplier: [
                    {
                        required: true,
                        validator: (rule, value, callback) => {
                            const relatedIndex = this.outboundForm.groupedSelectedRows.findIndex(
                                (group) => group.selectedCompositeSupplier === value
                            );
                            if ([2, 3].includes(this.outboundForm.groupedSelectedRows[relatedIndex].outboundType) && !value) {
                                callback(new Error('此项为必填项'));
                            } else {
                                callback();
                            }
                        },
                        trigger: 'change'
                    }
                ],
                selectedOutsourceId: [
                    { required: true, message: '此项为必填项', trigger: 'change' },
                ],
            },
            selectedCompositeRows: [],
            compositeSuppliersOptions: [],
            activeOrderShoes: [],
            filteredOrderShoes: [],
            currentShoePage: 1,
            shoePageSize: 5,
            shoeSearch: "",
            currentSelectedAssetRow: {},
            isSelectOrderDialogOpen: false,
            isConfirmOrderShoesDialogOpen: false,
            activeTab: null,
            selectedRowsCopy: [],
            currentSizeMaterialQuantityRow: {},
            isReceiptDialogVisible: false,
        }
    },
    computed: {
        filteredData() {
            return this.currentSizeMaterialQuantityRow.sizeMaterialOutboundTable.filter((row) => {
                return (
                    row.predictQuantity > 0
                );
            });
        },
    },
    mounted() {
        this.getAllCompositeSuppliers()
        this.getActiveOrderShoes()
        this.getMaterialTableData()
        this.getAllDeparments()
    },
    methods: {
        handleFactoryChange(value, row) {
            this.outboundForm.selectedOutsourceFactory = row.outsourceFactory.value
        },
        syncTimestamp(source_group) {
            return this.outboundForm.groupedSelectedRows.map(group => {
                group.timestamp = source_group.timestamp
            })
        },
        findCompositeSupplierName(supplierId) {
            let supplier = this.compositeSuppliersOptions.find(supplier => supplier.supplierId == supplierId)
            return supplier ? supplier.supplierName : ""
        },
        findDepartmentName(departmentId) {
            let department = this.departmentOptions.find(department => department.value == departmentId)
            return department ? department.label : ""
        },
        getCompositeMaterials(groupData) {
            let compositeMaterials = []
            groupData.items.forEach(item => {
                item.craftNameList.forEach(craftRow => {
                    if (craftRow.outboundQuantity > 0) {
                        compositeMaterials.push({
                            materialName: item.materialName,
                            craftName: craftRow.craftName,
                            materialModel: item.materialModel,
                            materialSpecification: item.materialSpecification,
                            colorName: item.colorName,
                            materialUnit: item.materialUnit,
                            craftOutboundQuantity: craftRow.outboundQuantity,
                            remark: craftRow.remark
                        })
                    }
                })
            })
            return compositeMaterials
        },
        filterZeroQuantityMaterial(data) {
            return data.filter(item => {
                return item.outboundQuantity > 0
            })
        },
        goBackToOutboundDialog() {
            this.isReceiptDialogVisible = false
            this.isMultiOutboundDialogVisible = true
        },
        getOutboundName(type) {
            switch (type) {
                case 0:
                    return "生产使用"
                case 1:
                    return "废料处理"
                case 2:
                    return "外包发货"
                case 3:
                    return "外发复合"
            }
        },
        openReceiptDialog() {
            let isValid = true;
            const validationPromises = this.outboundForm.groupedSelectedRows.map((group, index) => {
                return new Promise((resolve) => {
                    this.$refs[`outboundForm${index}`][0].validate((valid) => {
                        if (!valid) {
                            isValid = false;
                        }
                        resolve();
                    });
                });
            });

            Promise.all(validationPromises).then(() => {
                if (isValid) {
                    console.log(this.outboundForm.groupedSelectedRows)
                    this.isMultiOutboundDialogVisible = false;
                    this.isReceiptDialogVisible = true;
                } else {
                    console.log("invalid");
                }
            });
        },
        confirmSelectOrderShoe() {
            this.isSelectOrderDialogOpen = false
        },
        handleShoePageChange(val) {
            this.currentShoePage = val
        },
        getMaterialsWithCraftNames(items) {
            return items.filter(item => item.craftNameList.length > 0)
        },
        async getAllDeparments() {
            let response = await axios.get(`${this.$apiBaseUrl}/general/getalldepartments`)
            this.departmentOptions = response.data
        },
        filterOrderShoes(orderId = null) {
            if (orderId !== null) {
                this.filteredOrderShoes = this.activeOrderShoes.filter(shoe =>
                    shoe.orderId == orderId
                )
            }
            else {
                this.filteredOrderShoes = this.activeOrderShoes
            }
            let filtered = []
            if (orderId === null) {
                filtered = this.filteredOrderShoes.filter(shoe =>
                    shoe.orderRId.includes(this.shoeSearch) ||
                    shoe.shoeRId.includes(this.shoeSearch)
                )
            }
            else {
                filtered = this.filteredOrderShoes.filter(shoe =>
                    shoe.shoeRId.includes(this.shoeSearch)
                );
            }
            const start = (this.currentShoePage - 1) * this.shoePageSize;
            return filtered.slice(start, start + this.shoePageSize);
        },
        openSelectOrderDialog(row) {
            this.currentSelectedAssetRow = row
            this.isSelectOrderDialogOpen = true
        },
        handleShoeSelection(selectedShoe) {
            this.currentSelectedAssetRow.selectedOrderShoeId = selectedShoe.orderShoeId
            this.currentSelectedAssetRow.selectedOrderRId = selectedShoe.orderRId
            this.currentSelectedAssetRow.selectedShoeRId = selectedShoe.shoeRId
            this.currentSelectedAssetRow.selectedOrderId = selectedShoe.orderId
        },
        async getActiveOrderShoes() {
            let response = await axios.get(`${this.$apiBaseUrl}/order/getactiveordershoes`)
            this.activeOrderShoes = response.data
        },
        updateDialogVisible(newVal) {
            this.isMaterialDialogVisible = newVal

        },
        handleSearch(values) {
            this.searchForm = { ...values }
            this.getMaterialTableData()
        },
        handleCompositeAmountChange(newVal, oldVal, rowData) {
            rowData.outboundQuantity = Number((Number(rowData.outboundQuantity) - oldVal + newVal).toFixed(5))
        },
        handleCompositeSelectionChange(selection) {
            this.selectedCompositeRows = selection
        },
        updateSizeMaterialTotal() {
            this.currentSizeMaterialQuantityRow.sizeMaterialOutboundTable.forEach((element, index) => {
                this.currentSizeMaterialQuantityRow[`amount${index}`] = element.outboundQuantity
            })
            this.currentSizeMaterialQuantityRow.outboundQuantity = this.filteredData.reduce((acc, row) => {
                return acc + row.outboundQuantity;
            }, 0);
        },
        openSizeMaterialQuantityDialog(row) {
            this.currentSizeMaterialQuantityRow = row
            this.isOpenSizeMaterialQuantityDialogVisible = true
        },
        async confirmOrderShoesToOutbound() {
            // reset all ref variables
            this.currentSelectedAssetRow = {}
            this.filteredOrderShoes = []
            this.currentShoePage = 1
            this.shoeSearch = ""

            if (this.selectedRows.length == 0) {
                ElMessage.error("未选择材料")
                return
            }
            this.selectedRowsCopy = JSON.parse(JSON.stringify(this.selectedRows))
            // collect all orderShoeId that are null
            let assetRows = []
            this.selectedRowsCopy.forEach(row => {
                row["selectedOrderShoeId"] = row.orderShoeId
                row["selectedOrderId"] = row.orderId
                row["selectedShoeRId"] = row.shoeRId
                row["selectedOrderRId"] = row.orderRId
                if (row.orderShoeId === null) {
                    assetRows.push(row)
                }
            })
            if (assetRows.length > 0) {
                this.outboundForm.assetRows = assetRows
                this.isConfirmOrderShoesDialogOpen = true
                return
            }
            this.openMultipleOutboundDialog()
        },
        async openMultipleOutboundDialog() {
            if (this.selectedRows.length == 0) {
                ElMessage.error("未选择材料")
                return
            }
            await this.groupSelectedRows()
            this.isMultiOutboundDialogVisible = true
        },
        toggleSelectionMode() {
            this.isMultipleSelection = !this.isMultipleSelection;
        },
        handleSelectionChange(selection) {
            this.selectedRows = selection
        },
        async groupSelectedRows() {
            let groupedData = [];
            for (let item of this.selectedRowsCopy) {
                let templateObj = JSON.parse(JSON.stringify(this.formItemTemplate))
                let craftNameList = []
                if (item.craftName) {
                    craftNameList = item.craftName.split("@")
                }
                let newItem = { ...item, outboundQuantity: 0, remark: "", sizeMaterialOutboundTable: [], craftNameList: [] }
                craftNameList.forEach(craftName => {
                    newItem.craftNameList.push({ craftName: craftName, outboundQuantity: 0, remark: "" })
                })
                let shoeSizeColumns = []
                let sizeTypeId = null
                if (item.materialCategory == 1) {
                    let params = { "sizeMaterialStorageId": item.materialStorageId, "orderId": item.selectedOrderId, "purchaseDivideOrderId": item.purchaseDivideOrderId }
                    let response = await axios.get(`${this.$apiBaseUrl}/warehouse/warehousemanager/getsizematerialbyid`, { params })
                    sizeTypeId = response.data[0].typeId
                    console.log(sizeTypeId)
                    newItem["sizeMaterialOutboundTable"] = response.data
                    newItem["sizeMaterialOutboundTable"].forEach(row => {
                        row.outboundQuantity = 0
                    })
                    newItem.sizeMaterialOutboundTable.forEach((element, index) => {
                        newItem[`amount${index}`] = element.outboundQuantity
                    })
                    // insert shoe size columns into current row
                    newItem.sizeMaterialOutboundTable.forEach((element, index) => {
                        // for display
                        if (element.predictQuantity > 0) {
                            shoeSizeColumns.push({
                                "prop": `amount${index}`,
                                "label": element.shoeSizeName
                            })
                        }
                    })
                    newItem["shoeSizeColumns"] = shoeSizeColumns
                }
                let group = groupedData.find(g => g.orderShoeId === item.selectedOrderShoeId);

                if (group) {
                    group.items.push(newItem);
                } else {
                    group = {
                        orderShoeId: item.selectedOrderShoeId,
                        items: [newItem],
                        ...templateObj,
                        // for display in receipt dialog
                        nonSizedItems: [],
                        subGroups: {},
                        compositeMaterials: []
                    };
                    groupedData.push(group);
                }
                // Separate non-sized and sized items
                if (newItem.materialCategory == 0) {
                    group.nonSizedItems.push(newItem);
                }
                else {
                    // Further group items by shoeSizeColumns within each orderShoeId group
                    let key = sizeTypeId;
                    if (!group.subGroups[key]) {
                        group.subGroups[key] = [];
                    }
                    group.subGroups[key].push(newItem);
                }
            }
            this.outboundForm.groupedSelectedRows = groupedData;
            this.activeTab = groupedData[0].orderShoeId
            console.log(this.outboundForm.groupedSelectedRows)
            await this.getOutsourceInfo()
        },
        async getAllCompositeSuppliers() {
            const response = await axios.get(`${this.$apiBaseUrl}/warehouse/warehousemanager/getallcompositesuppliers`)
            this.compositeSuppliersOptions = response.data
        },
        async getMaterialTableData(sortColumn, sortOrder) {
            const params = {
                "page": this.currentPage,
                "pageSize": this.pageSize,
                "opType": 2,
                "materialType": this.searchForm.materialTypeSearch,
                "materialName": this.searchForm.materialNameSearch,
                "materialSpec": this.searchForm.materialSpecificationSearch,
                "materialModel": this.searchForm.materialModelSearch,
                "materialColor": this.searchForm.materialColorSearch,
                "supplier": this.searchForm.materialSupplierSearch,
                "orderRId": this.searchForm.orderNumberSearch,
                "shoeRId": this.searchForm.shoeNumberSearch,
                "totalPurchaseOrderRId": this.searchForm.totalPurchaseOrderRIdSearch,
                "sortColumn": sortColumn,
                "sortOrder": sortOrder
            }
            const response = await axios.get(`${this.$apiBaseUrl}/warehouse/warehousemanager/getallmaterialinfo`, { params })
            this.materialTableData = response.data.result
            this.totalRows = response.data.total
        },
        async submitOutboundForm() {
            let isValid = true;
            const validationPromises = this.outboundForm.groupedSelectedRows.map((group, index) => {
                return new Promise((resolve) => {
                    this.$refs[`outboundForm${index}`][0].validate((valid) => {
                        if (!valid) {
                            isValid = false;
                        }
                        resolve();
                    });
                });
            });

            Promise.all(validationPromises).then(async () => {
                if (isValid) {
                    console.log("Form is valid. Proceeding with submission.");
                    console.log(this.outboundForm.groupedSelectedRows)
                    let data = []
                    for (let row of this.outboundForm.groupedSelectedRows) {
                        let outsourceInfoId = null
                        if (row.outboundType == 2 && row.selectedOutsourceId) {
                            outsourceInfoId = row.selectedOutsourceId.outsourceInfoId
                        }
                        let obj = {
                            "outboundTimestamp": row.timestamp,
                            "outboundType": row.outboundType,
                            "outboundDepartment": row.section,
                            "outboundAddress": row.outboundAddress,
                            "picker": row.receiver,
                            "outsourceInfoId": outsourceInfoId,
                            "compositeSupplierId": row.selectedCompositeSupplier,
                            "orderShoeId": row.orderShoeId,
                            "nonSizedItems": [],
                            // key: sizeTypeId, value: items
                            // because one outbound row can have multiple sizeTypeId
                            "sizedItems": {},
                        }
                        for (let item of row.nonSizedItems) {
                            let detail = {
                                "materialStorageId": item.materialStorageId,
                                "outboundQuantity": item.outboundQuantity,
                                "remark": item.remark,
                                "sizeMaterialOutboundList": null,
                                "craftNameList": item.craftNameList,
                                "materialCategory": item.materialCategory,
                            }
                            obj.nonSizedItems.push(detail)
                        }
                        for (let [sizeTypeId, items] of Object.entries(row.subGroups)) {
                            obj.sizedItems[sizeTypeId] = []
                            for (let item of items) {
                                let amountList = []
                                for (let i = 0; i < item.sizeMaterialOutboundTable.length; i++) {
                                    amountList.push(item[`amount${i}`])
                                }
                                let detail = {
                                    "materialStorageId": item.materialStorageId,
                                    "outboundQuantity": item.outboundQuantity,
                                    "remark": item.remark,
                                    "sizeMaterialOutboundList": amountList,
                                    "craftNameList": item.craftNameList,
                                    "materialCategory": item.materialCategory,
                                }
                                obj.sizedItems[sizeTypeId].push(detail)
                            }
                        }
                        data.push(obj)
                    }
                    try {
                        console.log(data)
                        await axios.patch(`${this.$apiBaseUrl}/warehouse/warehousemanager/outboundmaterial`, data)
                        ElMessage.success("出库成功")
                    }
                    catch (error) {
                        console.log(error)
                        ElMessage.error(error.response.data.message)
                    }
                    this.isMultiOutboundDialogVisible = false
                    this.getMaterialTableData()
                } else {
                    console.log("invalid");
                }
            });
        },

        openFinishOutboundDialog() {
            if (this.selectedRows.length == 0) {
                ElMessage.error("未选择材料")
                return
            }
            this.isFinishOutboundDialogOpen = true
        },
        handleSizeChange(val) {
            this.pageSize = val
            this.getMaterialTableData()
        },
        handlePageChange(val) {
            this.page = val
            this.getMaterialTableData()
        },
        formatDecimal(row, column, cellValue, index) {
            return Number(cellValue).toFixed(2)
        },
        async getOutsourceInfo() {
            this.outboundForm.groupedSelectedRows.forEach(async (group) => {
                let params = { "orderShoeId": group.orderShoeId }
                let response = await axios.get(`${this.$apiBaseUrl}/production/productionmanager/getordershoeoutsourceinfo`, { params })
                console.log(response.data)
                response.data.forEach(element => {
                    if ((element.outsourceStatus == '已审批' || element.outsourceStatus == '材料出库') && element.materialRequired) {
                        group.outsourceInfo.push(element)
                    }
                });
            })
        },
        async finishOutsourceOutbound(row) {
            try {
                let data = { "outsourceInfoId": row.outsourceInfoId }
                await axios.patch(`${this.$apiBaseUrl}/warehouse/warehousemanager/finishoutsourceoutbound`, data)
                await this.getOutsourceInfo()
                ElMessage.success("外包出库成功")
            }
            catch (error) {
                console.log(error)
                ElMessage.error("外包出库失败")
            }
        },
        async finishOutbound() {
            ElMessageBox.alert('该操作完成对选择鞋型材料出库', '提示', {
                confirmButtonText: '确认',
                showCancelButton: true,
                cancelButtonText: '取消'
            }).then(async () => {
                let data = []
                this.selectedRows.forEach(row => {
                    data.push({ storageId: row.materialStorageId, materialCategory: row.materialCategory })
                })
                try {
                    await axios.patch(`${this.$apiBaseUrl}/warehouse/warehousemanager/finishoutboundmaterial`, data)
                    ElMessage.success("操作成功")
                }
                catch (error) {
                    console.log(error)
                    ElMessage.error("操作异常")
                }
                this.isFinishOutboundDialogOpen = false
                this.getMaterialTableData()
            })
        },
        async sortData({ prop, order }) {
            await this.getMaterialTableData(prop, order)
        }
    }
}
</script>
