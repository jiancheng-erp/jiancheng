<template>
    <el-container direction="vertical">
        <el-main style="height: 100vh;">
            <el-row :gutter="20" style="text-align: center;">
                <el-col :span="24" :offset="0" style="font-size: xx-large; text-align: center;">
                    {{ `包装采购 ${currentOrderRid} ${currentEditPurchaseOrderRid}` }}
                </el-col>
            </el-row>
            <el-divider></el-divider>
            <el-row :gutter="20">
                <el-col :span="8" :offset="0" :key="currentEditPurchaseOrderRid">
                    包装信息
                </el-col>
            </el-row>
            <el-row :gutter="20">
                <el-col :span="12" :offset="6">
                    <el-descriptions border column="3">
                        <el-descriptions-item label="包装信息">
                            <el-button type="primary" size="default" @click="viewPackagingInfo"
                                :disabled="currentEditPurchaseOrderRid === ''">查看</el-button>
                        </el-descriptions-item>
                    </el-descriptions>
                </el-col>
            </el-row>
            <div v-if="currentEditPurchaseOrderRid !== ''">
                <el-row :gutter="20">
                    <el-col :span="24" :offset="0">
                        <el-form ref="purchaseForm" :model="assetForm" :rules="rules">
                            <purchase-items-table :material-type-options="materialTypeOptions"
                                @update-items="updateNewPurchaseData" :purchase-data="assetForm.purchaseData"
                                :type-limit="[6]" :order-id="orderid"></purchase-items-table>
                        </el-form>
                    </el-col>
                </el-row>
                <el-row :gutter="20">
                    <el-col :span="8" :offset="18">
                        <el-button type="primary" size="medium" @click="savePackagePurchaseOrder"
                            :disabled="currentEditPurchaseOrderRid === ''">保存采购订单</el-button>
                        <el-button type="warning" size="medium" @click="openSubmitDialog"
                            :disabled="currentEditPurchaseOrderRid === ''">提交采购订单</el-button>

                    </el-col>
                </el-row>
            </div>
        </el-main>
        <el-dialog title="采购订单创建页面" v-model="purchaseOrderCreateVis" width="80%" :close-on-click-modal="false">
            <span v-if="activeTab === ''"> 无需购买材料，推进流程即可。 </span>
            <el-tabs v-if="activeTab !== ''" v-model="activeTab" type="card" tab-position="top">
                <el-tab-pane v-for="(item, index) in tabPlaneData" :key="index"
                    :label="item.purchaseDivideOrderId + '    ' + item.supplierName" :name="item.purchaseDivideOrderId"
                    style="min-height: 500px">
                    <el-row :gutter="20">
                        <el-col :span="12" :offset="0"><span>订单备注：
                                <el-input v-model="item.remark" placeholder="" type="textarea" resize="none"
                                    clearable></el-input> </span></el-col>
                        <el-col :span="12" :offset="0">
                            <span>环境要求：
                                <el-input v-model="item.evironmentalRequest" placeholder="" type="textarea"
                                    resize="none" clearable></el-input>
                            </span>
                        </el-col>
                    </el-row>
                    <el-row :gutter="20">
                        <el-col :span="12" :offset="0">
                            <span>发货地址：
                                <el-input v-model="item.shipmentAddress" placeholder="" type="textarea" resize="none"
                                    clearable></el-input>
                            </span>
                        </el-col>
                        <el-col :span="12" :offset="0">
                            <span>交货周期：
                                <el-input v-model="item.shipmentDeadline" placeholder="" type="textarea" resize="none"
                                    clearable></el-input>
                            </span>
                        </el-col>
                    </el-row>
                    <el-row :gutter="20" style="margin-top: 20px">
                        <el-col :span="24" :offset="0">
                            <div v-if="factoryFieldJudge(item.purchaseDivideOrderType)">
                                <el-table :data="item.assetsItems" border stripe>
                                    <el-table-column type="index" label="编号" />
                                    <el-table-column prop="materialType" label="材料类型"></el-table-column>
                                    <el-table-column prop="materialName" label="材料名称" />
                                    <el-table-column prop="materialModel" label="材料型号" />
                                    <el-table-column prop="materialSpecification" label="材料规格"></el-table-column>
                                    <el-table-column prop="unit" label="单位" />

                                    <el-table-column prop="purchaseAmount" label="采购数量" />
                                    <el-table-column :label="`分码数量`">
                                        <el-table-column v-for="column in filteredColumns(item.assetsItems)"
                                            :key="column.prop" :prop="column.prop"
                                            :label="column.label"></el-table-column>
                                    </el-table-column>
                                </el-table>
                            </div>
                            <div v-else>
                                <el-table :data="item.assetsItems" border stripe>
                                    <el-table-column type="index"></el-table-column>
                                    <el-table-column prop="materialType" label="材料类型"></el-table-column>
                                    <el-table-column prop="materialName" label="材料名称" />
                                    <el-table-column prop="materialModel" label="材料型号" />
                                    <el-table-column prop="materialSpecification" label="材料规格"></el-table-column>
                                    <el-table-column prop="color" label="颜色" />
                                    <el-table-column prop="unit" label="单位" />
                                    <el-table-column prop="purchaseAmount" label="数量" />
                                    <el-table-column prop="remark" label="开发部备注" />
                                </el-table>
                            </div>
                        </el-col>
                    </el-row>
                </el-tab-pane>
            </el-tabs>

            <template #footer>
                <span>
                    <el-button @click="purchaseOrderCreateVis = false">取消</el-button>
                    <el-button type="primary" @click="confirmPurchaseDivideOrderSave">保存</el-button>
                    <el-button type="success" @click="confirmPurchaseDivideOrderSubmit">提交</el-button>
                </span>
            </template>
        </el-dialog>
    </el-container>
</template>

<script>
import axios from 'axios'
import PurchaseItemsTable from '@/Pages/LogisticsControlDepartment/LogisticsControlManager/components/VariousPurchaseTables/PurchaseItemsTable.vue';
import { ElMessage } from 'element-plus';
import { getShoeSizesName } from '@/Pages/utils/getShoeSizesName'
export default {
    props: ['orderid'],
    components: {
        PurchaseItemsTable
    },
    data() {
        return {
            getShoeSizesName,
            purchaseOrderCreateVis: false,
            activeTab: '',
            tabPlaneData: [],
            isPackageSearchDialogVisable: false,
            isSizeComparisonDialogVisible: false,
            orderSearch: '',
            customerSearch: '',
            currentOrderRid: '',
            packageNameSearch: '',
            filteredMaterialList: [],
            orderList: [],
            filteredList: [],
            currentPage: 1,
            pageSize: 10,
            currentPackageType: '',
            orderPackageStatus: '0',
            materialTypeOptions: [],
            currentEditPurchaseOrderRid: '',
            currentEditPurchaseOrderId: 0,
            createEditSymbol: 0,
            currentShoeSizeType: '',
            currentOrderDBId: 0,
            sizeGridOptions: [],
            shoeSizeColumns: [],
            sizeLabelColumns: [],
            assetForm: {
                purchaseOrderType: 'P',
                orderId: null,
                orderShoeId: null,
                purchaseData: [],
                batchInfoType: null
            },
            rules: {
                purchaseOrderType: { required: true, message: '此项为必填项', trigger: 'change' },
                orderId: [
                    {
                        required: true,
                        validator: (rule, value, callback) => {
                            if (this.assetForm.purchaseOrderType == 'P' && !value) {
                                callback(new Error("尚未选择订单"));
                            } else {
                                callback();
                            }
                        },
                        trigger: "change",
                    },
                ],
                orderShoeId: [
                    {
                        required: true,
                        validator: (rule, value, callback) => {
                            if (this.assetForm.purchaseOrderType == 'X' && !value) {
                                callback(new Error("尚未选择订单鞋型"));
                            } else {
                                callback();

                            }

                        },
                        trigger: "change",
                    },
                ],
            },
        }
    },
    computed: {
        paginatedList() {
            const start = (this.currentPage - 1) * this.pageSize;
            return this.filteredList.slice(start, start + this.pageSize);
        }
    },
    mounted() {
        this.getOrderInfo(this.orderid);
        this.getAllMaterialTypes();
        this.getCurrentPurchaseOrder();
        this.getBatchTypeList();

    },
    methods: {
        async getCurrentPurchaseOrder() {
            const response = await axios.get(`${this.$apiBaseUrl}/logistics/getpackagepurchaseorderitems`, {
                params: {
                    orderid: this.orderid
                }
            });
            this.currentEditPurchaseOrderRid = response.data.purchaseOrderRid || '';
            this.currentEditPurchaseOrderId = response.data.purchaseOrderId || null;
            this.assetForm.purchaseData = response.data.purchaseOrderItems;
            this.assetForm.orderId = this.orderid;
            this.assetForm.purchaseOrderType = 'P';
            if (this.currentEditPurchaseOrderId === null) {
                {
                    this.createPackagePurchaseOrder(this.orderid)
                }
            }
            else {
                this.createEditSymbol = 1
            }
        },
        async openSubmitDialog() {
            const response = await axios.get(
                `${this.$apiBaseUrl}/logistics/getindividualpurchaseorders`,
                {
                    params: {
                        purchaseOrderId: this.currentEditPurchaseOrderId
                    }
                }
            )
            this.tabPlaneData = response.data
            console.log(this.tabPlaneData)
            if (this.tabPlaneData.length > 0) {
                this.activeTab = this.tabPlaneData[0].purchaseDivideOrderId
            }
            this.purchaseOrderCreateVis = true
        },
        async getOrderInfo(orderId) {
            const response = await axios.get(`${this.$apiBaseUrl}/order/getorderInfo`, {
                params: {
                    orderid: orderId
                }
            });
            this.currentOrderRid = response.data.orderId;
            this.currentOrderDBId = response.data.orderDBId;
        },
        async getAllOrders() {
            try {
                const response = await axios.get(`${this.$apiBaseUrl}/order/getallorders`);
                this.orderList = response.data;
                this.filteredList = this.orderList;
            } catch (error) {
                console.log(error);
            }
        },
        async getAllMaterialTypes() {
            let response = await axios.get(`${this.$apiBaseUrl}/logistics/getallmaterialtypes`)
            console.log(response.data);
            this.materialTypeOptions = response.data.filter(materialType => materialType.materialTypeName === '包材');
        },
        async searchPackage() {
            this.filteredMaterialList = [];
            const response = await axios.get(`${this.$apiBaseUrl}/logistics/searchpackagematerialinfo`, {
                params: {
                    materialModel: this.packageNameSearch
                }
            });
            this.filteredMaterialList = response.data.data;
        },
        async openPackageSearchDialog() {
            this.shoeSizeColumns = await this.getShoeSizesName(this.assetForm.orderId)
            this.currentShoeSizeType = this.shoeSizeColumns[0].type
            this.isPackageSearchDialogVisable = true;
            this.packageNameSearch = this.currentPackageType;
            this.packageNameSearch = this.packageNameSearch.replace(/[^a-zA-Z0-9]/g, '');
            this.filteredMaterialList = [];
            const response = await axios.get(`${this.$apiBaseUrl}/logistics/searchpackagematerialinfo`, {
                params: {
                    materialModel: this.packageNameSearch
                }
            });
            this.filteredMaterialList = response.data.data;

        },
        async getSizeTableData() {
            const response = await axios.get(
                `${this.$apiBaseUrl}/devproductionorder/getsizetable?orderId=${this.currentOrderDBId}`
            )

            this.sizeGridOptions = response.data
            console.log(this.sizeGridOptions)
        },
        filteredColumns(array) {
            if (!array || !this.sizeLabelColumns) return [];

            return Object.keys(this.sizeLabelColumns)
                .map((slotKey) => {
                    const amountKey = slotKey.replace("Slot", "Amount"); // Convert size34Slot → size34Amount

                    if (array.some(row => row[amountKey] !== undefined && row[amountKey] !== 0)) {
                        return {
                            prop: amountKey,
                            label: this.sizeLabelColumns[slotKey] // Use size number (e.g., "34", "35")
                        };
                    }
                    return null;
                })
                .filter(column => column !== null); // Remove null values
        },
        packageStatusFormatter(row) {
            switch (row.orderPackageStatus) {
                case '0':
                    return '未采购';
                case '1':
                    return '已保存';
                case '2':
                    return '已采购';
            }
        },
        async createPackagePurchaseOrder(orderid) {
            console.log(this.currentEditPurchaseOrderRid);
            if (this.currentEditPurchaseOrderRid !== '') {
                const response = await axios.get(`${this.$apiBaseUrl}/logistics/getpackagepurchaseorderitems`, {
                    params: {
                        orderid: orderid
                    }
                });
                this.currentEditPurchaseOrderRid = response.data.purchaseOrderRid;
                this.currentEditPurchaseOrderId = response.data.purchaseOrderId;
                console.log(response.data.purchaseOrderItems)
                this.assetForm.purchaseData = response.data.purchaseOrderItems;
                this.assetForm.orderId = orderid;
                this.assetForm.purchaseOrderType = 'P';
                console.log(this.assetForm)
                console.log(this.currentEditPurchaseOrderRid);
            }
            else {
                const response = await axios.get(`${this.$apiBaseUrl}/logistics/getnewpackagepurchaseorderid`, {
                    params: {
                        orderid: orderid
                    }
                });
                this.currentEditPurchaseOrderRid = response.data.purchaseOrderRid;
                this.createEditSymbol = 0;
                this.assetForm.purchaseData = [];
                this.assetForm.orderId = orderid;
                this.assetForm.purchaseOrderType = 'P';
                console.log(this.currentEditPurchaseOrderRid);
            }
        },
        updateNewPurchaseData(updatedItems) {
            this.assetForm.purchaseData = [...updatedItems]; // Ensures Vue detects the change
            console.log("Updated purchaseData:", this.assetForm.purchaseData);
        },
        savePackagePurchaseOrder() {
            this.$refs.purchaseForm.validate(async (valid) => {
                if (valid) {
                    if (this.assetForm.purchaseData.length === 0) {
                        ElMessage.error("采购订单不能为空")
                        return
                    }
                    for (let row of this.assetForm.purchaseData) {
                        let zeroAmount = row.purchaseAmount == 0
                        let noMaterialName = !row.materialName
                        if (zeroAmount) {
                            ElMessage.error("采购数量不能为零")
                            return
                        }
                        if (noMaterialName) {
                            ElMessage.error("材料名称不能为空")
                            return
                        }
                    }
                    try {
                        console.log(this.assetForm)
                        if (this.createEditSymbol === 1) {
                            await axios.post(
                                `${this.$apiBaseUrl}/logistics/editsavedpackagepurchaseorderitems`,
                                {
                                    data: this.assetForm.purchaseData,
                                    purchaseOrderRId: this.currentEditPurchaseOrderRid,
                                    orderId: this.assetForm.orderId,
                                    orderShoeId: this.assetForm.orderShoeId,
                                    batchInfoType: this.assetForm.batchInfoType,
                                    purchaseOrderType: this.assetForm.purchaseOrderType
                                }
                            )
                        }
                        else {
                            await axios.post(
                                `${this.$apiBaseUrl}/logistics/newpackagepurchaseordersave`,
                                {
                                    data: this.assetForm.purchaseData,
                                    purchaseOrderRId: this.currentEditPurchaseOrderRid,
                                    orderId: this.assetForm.orderId,
                                    orderShoeId: this.assetForm.orderShoeId,
                                    batchInfoType: this.assetForm.batchInfoType,
                                    purchaseOrderType: this.assetForm.purchaseOrderType
                                }
                            )
                        }
                        ElMessage.success('保存成功')

                        // Close the current page
                    }
                    catch (error) {
                        console.log(error)
                        ElMessage.error("保存失败")
                    }
                }
                else {
                    console.log("validation error")
                }
                this.getCurrentPurchaseOrder();
            })
        },
        confirmPurchaseDivideOrderSave() {
            this.$confirm('确定保存此分采购订单吗？', '提示', {
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                type: 'warning'
            })
                .then(() => {
                    this.submitPurchaseDivideOrderSave()
                })
                .catch(() => {
                    this.$message({
                        type: 'info',
                        message: '已取消保存'
                    })
                })
        },
        confirmPurchaseDivideOrderSubmit() {
            this.$confirm('确定提交此分采购订单吗？', '提示', {
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                type: 'warning'
            })
                .then(() => {
                    this.submitPurchaseDivideOrder()
                })
                .catch(() => {
                    this.$message({
                        type: 'info',
                        message: '已取消提交'
                    })
                })
        },
        async submitPurchaseDivideOrderSave() {
            const loadingInstance = this.$loading({
                lock: true,
                text: '等待中，请稍后...',
                background: 'rgba(0, 0, 0, 0.7)'
            })
            const response = await this.$axios.post(
                `${this.$apiBaseUrl}/firstpurchase/savepurchasedivideorders`,
                {
                    purchaseOrderId: this.currentEditPurchaseOrderId,
                    purchaseDivideOrders: this.tabPlaneData
                }
            )
            loadingInstance.close()
            if (response.status !== 200) {
                this.$message({
                    type: 'error',
                    message: '保存失败'
                })
                return
            }
            this.$message({
                type: 'success',
                message: '保存成功'
            })
            this.purchaseOrderCreateVis = false
        },
        async submitPurchaseDivideOrder() {
            const loadingInstance = this.$loading({
                lock: true,
                text: '等待中，请稍后...',
                background: 'rgba(0, 0, 0, 0.7)'
            })
            const response = await this.$axios.post(
                `${this.$apiBaseUrl}/logistics/submitpackageindividualpurchaseorders`,
                {
                    purchaseOrderId: this.currentEditPurchaseOrderId
                }
            )
            loadingInstance.close()
            if (response.status !== 200) {
                this.$message({
                    type: 'error',
                    message: '提交失败'
                })
                return
            }
            this.$message({
                type: 'success',
                message: '提交成功'
            })
            this.purchaseOrderCreateVis = false
        },
        handleFilter() {
            this.currentPage = 1;
            this.filteredList = this.orderList.filter(order => {
                return (
                    (!this.orderSearch || order.orderRid.includes(this.orderSearch)) &&
                    (!this.customerSearch || order.customerName.includes(this.customerSearch)) &&
                    (order.orderPackageStatus === this.orderPackageStatus)
                );
            });
        },
        handleSizeChange(newSize) {
            this.pageSize = newSize;
            this.currentPage = 1;
        },
        handleCurrentChange(newPage) {
            this.currentPage = newPage;
        },
        jumpOverPackagePurchase() {
        },
        factoryFieldJudge(field) {
            if (field === 'N') {
                return false
            }
            return true
        },
        async getBatchTypeList() {
            const response = await axios.get(`${this.$apiBaseUrl}/shoe/getshoebatchinfotypebysizetable`, {
                params: {
                    orderId: this.orderid
                }
            })
            console.log(response.data)
            this.sizeLabelColumns = response.data
        },
        viewPackagingInfo() {
            window.open(`${this.$apiBaseUrl}/orderimport/downloadorderdoc?orderrid=${this.currentOrderRid}&filetype=2`);
        },
    }
}
</script>
