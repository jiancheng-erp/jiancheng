<template>
    <el-dialog title="确认订单鞋型" v-model="localVisible" width="80%" :close-on-click-modal="false" @close="handleClose">
        <div v-if="page == 1">
            <el-table :data="selectedRows" border stripe>
                <el-table-column prop="selectedOrderRId" label="订单号"></el-table-column>
                <el-table-column prop="selectedShoeRId" label="鞋型号"></el-table-column>
                <el-table-column prop="materialName" label="材料名称"></el-table-column>
                <el-table-column prop="materialSpecification" label="材料规格"></el-table-column>
                <el-table-column prop="materialModel" label="材料型号"></el-table-column>
                <el-table-column prop="colorName" label="颜色"></el-table-column>
                <el-table-column label="操作">
                    <template #default="scope">
                        <el-button type="primary" size="small"
                            @click="openSelectOrderDialog(scope.row)">选择订单</el-button>
                    </template>
                </el-table-column>
            </el-table>
        </div>

        <div v-else-if="page == 2">
            <div>
                <el-descriptions border>
                    <el-descriptions-item label="出库时间">
                        {{ outboundForm.currentDateTime }}
                    </el-descriptions-item>
                    <el-descriptions-item label="出库类型">
                        {{ getOutboundName(outboundForm.outboundType) }}
                    </el-descriptions-item>
                    <el-descriptions-item label="出库至">
                        {{ getDestination }}
                    </el-descriptions-item>
                </el-descriptions>
            </div>
            <!-- 外包发货的form item -->
            <!-- 外发复合的form item -->
            <el-table :data="outboundForm.items" style="width: 100%" border stripe>
                <el-table-column prop="selectedOrderRId" label="订单号" />
                <el-table-column prop="selectedShoeRId" label="工厂型号" />
                <el-table-column prop="materialName" label="材料名称" />
                <el-table-column prop="materialModel" label="材料型号" />
                <el-table-column prop="materialSpecification" label="材料规格" />
                <el-table-column prop="colorName" label="颜色" />
                <el-table-column prop="actualInboundUnit" label="单位" />
                <el-table-column prop="currentAmount" label="库存" />
                <el-table-column prop="outboundQuantity" label="出库数量">
                    <template #default="scope">
                        <el-input-number v-if="scope.row.materialName !== '大底'" size="small"
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
        </div>
        <template #footer>
            <el-button v-if="page != 1" @click="prevPage()">上一页</el-button>
            <el-button v-if="page != 2" @click="nextPage()">下一页</el-button>
            <el-button v-else-if="page == 2" type="primary" @click="submitOutboundForm">出库</el-button>
            <el-button @click="test">123</el-button>
        </template>
    </el-dialog>

    <el-dialog title="选择订单" v-model="isSelectOrderDialogOpen" width="50%" :close-on-click-modal="false">
        <el-row>
            <el-col :span="6">
                <el-input v-model="orderRIdSearh" placeholder="搜索订单号" class="mb-2" clearable @change="handleShoeSearch">
                </el-input>
            </el-col>
            <el-col :span="6">
                <el-input v-model="shoeRIdSearch" placeholder="搜索工厂型号" class="mb-2" clearable
                    @change="handleShoeSearch">
                </el-input>
            </el-col>
        </el-row>
        <el-table :data="filteredOrderShoes" border stripe height="400">
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
        <template #footer>
            <el-button @click="confirmSelectOrderShoe">确定</el-button>
        </template>
    </el-dialog>

    <el-dialog title="多鞋码材料出库数量" v-model="isOpenSizeMaterialQuantityDialogVisible" width="50%">
        <el-form>
            <el-form-item>
                <el-table :data="currentSizeMaterialQuantityRow.sizeMaterialOutboundTable" border stripe>
                    <el-table-column prop="shoeSizeName" label="鞋码"></el-table-column>
                    <el-table-column prop="currentQuantity" label="库存"></el-table-column>
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
        parentOutboundForm: {
            type: Object,
            required: true
        },
        selectedRows: {
            type: Array,
            required: true
        },
        outboundOptions: {
            type: Array,
            required: true
        },
        departmentOptions: {
            type: Array,
            required: true
        },
    },
    emits: ["update-visible", "update-outbound-form"],
    watch: {
        visible(newVal) {
            this.localVisible = newVal;
        },
        parentOutboundForm: {
            handler(newVal) {
                // Update the local form whenever the parent's outboundForm changes.
                this.outboundForm = { ...newVal };
            },
            immediate: true, // Runs the handler immediately on watcher setup
            deep: true       // Watches for changes in nested properties
        }
    },
    computed: {
        getDestination() {
            if (this.outboundForm.outboundType == 0) {
                const result = this.departmentOptions.filter(item => {
                    return item.value == this.outboundForm.departmentId
                })
                if (result.length == 0) {
                    return ""
                }
                return result[0].label
            } else if (this.outboundForm.outboundType == 3) {
                return this.outboundForm.supplierName
            }
        }
    },
    data() {
        return {
            // reset all ref variables
            currentSelectedAssetRow: {},
            filteredOrderShoes: [],
            currentShoePage: 1,
            orderRIdSearh: "",
            shoeRIdSearch: "",
            shoeSearch: "",
            totalOrderShoeCount: 0,
            isSelectOrderDialogOpen: false,
            isOpenSizeMaterialQuantityDialogVisible: false,
            activeTab: "",
            localVisible: this.visible,
            activeOrderShoes: [],
            currentSizeMaterialQuantityRow: {},
            outboundForm: {},
            page: 1
        }
    },
    methods: {
        test() {
            console.log(this.outboundForm)
            console.log(this.parentOutboundForm)
            this.outboundForm = JSON.parse(JSON.stringify(this.parentOutboundForm))
            console.log(this.outboundForm)
        },
        prevPage() {
            this.page = 1
        },
        async nextPage() {
            await this.groupSelectedRows()
            this.page = 2
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
        handleCompositeAmountChange(newVal, oldVal, rowData) {
            rowData.outboundQuantity = Number((Number(rowData.outboundQuantity) - oldVal + newVal).toFixed(5))
        },
        handleCompositeSelectionChange(selection) {
            this.selectedCompositeRows = selection
        },
        getMaterialsWithCraftNames(items) {
            return items.filter(item => item.craftNameList.length > 0)
        },
        updateSizeMaterialTotal() {
            this.currentSizeMaterialQuantityRow.sizeMaterialOutboundTable.forEach((element, index) => {
                this.currentSizeMaterialQuantityRow[`amount${index}`] = element.outboundQuantity
            })
            this.currentSizeMaterialQuantityRow.outboundQuantity = this.currentSizeMaterialQuantityRow.sizeMaterialOutboundTable.reduce((acc, row) => {
                return acc + row.outboundQuantity;
            }, 0);
        },
        openSizeMaterialQuantityDialog(row) {
            this.currentSizeMaterialQuantityRow = row
            this.isOpenSizeMaterialQuantityDialogVisible = true
        },
        // async getOutsourceInfo() {
        //     this.outboundForm.groupedSelectedRows.forEach(async (group) => {
        //         let params = { "orderShoeId": group.orderShoeId }
        //         let response = await axios.get(`${this.$apiBaseUrl}/production/productionmanager/getordershoeoutsourceinfo`, { params })
        //         console.log(response.data)
        //         response.data.forEach(element => {
        //             if ((element.outsourceStatus == '已审批' || element.outsourceStatus == '材料出库') && element.materialRequired) {
        //                 group.outsourceInfo.push(element)
        //             }
        //         });
        //     })
        // },
        handleShoeSelection(selectedShoe) {
            this.currentSelectedAssetRow.selectedOrderShoeId = selectedShoe.orderShoeId
            this.currentSelectedAssetRow.selectedOrderRId = selectedShoe.orderRId
            this.currentSelectedAssetRow.selectedShoeRId = selectedShoe.shoeRId
            this.currentSelectedAssetRow.selectedOrderId = selectedShoe.orderId
        },
        confirmSelectOrderShoe() {
            this.isSelectOrderDialogOpen = false
        },
        handleShoeSearch() {
            this.filteredOrderShoes = JSON.parse(JSON.stringify(this.activeOrderShoes))
            this.filteredOrderShoes = this.filteredOrderShoes.filter(row => {
                return row.orderRId.includes(this.orderRIdSearh) && row.shoeRId.includes(this.shoeRIdSearch)
            })
        },
        async getActiveOrderShoes() {
            let response = await axios.get(`${this.$apiBaseUrl}/order/getactiveordershoes`)
            this.activeOrderShoes = response.data
            this.filteredOrderShoes = response.data
        },
        openSelectOrderDialog(row) {
            this.currentSelectedAssetRow = row
            this.getActiveOrderShoes()
            this.isSelectOrderDialogOpen = true
        },
        async groupSelectedRows() {
            console.log(this.outboundForm)
            let groupedData = [];
            for (let item of this.selectedRows) {
                let newItem = { ...item, outboundQuantity: 0, remark: "", sizeMaterialOutboundTable: [] }
                if (item.materialCategory == 1) {
                    console.log(item)
                    let params = { "sizeMaterialStorageId": item.materialStorageId, orderId: item.orderId, purchaseDivideOrderId: item.purchaseDivideOrderId }
                    let response = await axios.get(`${this.$apiBaseUrl}/warehouse/warehousemanager/getsizematerialbyid`, { params })
                    newItem["sizeMaterialOutboundTable"] = response.data
                    newItem["sizeMaterialOutboundTable"].forEach((row, index) => {
                        row.outboundQuantity = 0
                        newItem[`amount${index}`] = 0
                    })
                }
                groupedData.push(newItem);
            }
            this.outboundForm.items = groupedData;
            console.log(this.outboundForm)
            // await this.getOutsourceInfo()
        },
        async submitOutboundForm() {
            console.log(this.parentOutboundForm)
            for (let item of this.outboundForm.items) {
                if (item.outboundQuantity <= 0) {
                    ElMessage.error("出库数量必须大于0")
                    return
                }
            }
            let data = {
                "currentDateTime": this.outboundForm.currentDateTime,
                "outboundType": this.outboundForm.outboundType,
                "department": this.outboundForm.departmentId,
                "outboundAddress": this.outboundForm.outboundAddress,
                "picker": this.outboundForm.picker,
                "outsourceInfoId": null,
                "supplierName": this.outboundForm.supplierName,
                "items": this.outboundForm.items,
                "remark": this.outboundForm.remark,
            }
            try {
                console.log(data)
                await axios.post(`${this.$apiBaseUrl}/warehouse/outboundmaterial`, data)
                ElMessage.success("出库成功")
            }
            catch (error) {
                console.log(error)
                ElMessage.error(error.response.data.message)
            }
            this.$emit("update-outbound-form", this.outboundForm)
            this.handleClose()
        },
        handleClose() {
            this.page = 1
            this.outboundForm = {}
            this.$emit("update-visible", false);
        },
    }
}
</script>