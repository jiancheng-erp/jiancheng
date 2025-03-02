<template>
    <el-container direction="vertical">
        <el-main style="height: 100vh;">
            <el-row :gutter="20" style="text-align: center;">
                <el-col :span="24" :offset="0" style="font-size: xx-large; text-align: center;">
                    {{ `包材采购` }}
                </el-col>
            </el-row>
            <el-row :gutter="20">
                <el-col :span="1" :offset="0">
                    <el-text style="white-space: nowrap;">订单筛选：</el-text>
                </el-col>
                <el-col :span="4" :offset="0">
                    <el-input v-model="orderSearch" placeholder="请输入订单号" clearable @input="handleFilter"></el-input>        
                </el-col>
                <el-col :span="4" :offset="0">
                    <el-input v-model="customerSearch" placeholder="请输入客户名" clearable @input="handleFilter"></el-input>
                </el-col>
                <el-col :span="4" :offset="0">
                    <el-radio-group v-model="orderPackagingStatus" size="medium" @change="handleFilter">
                        <el-radio-button label="0">未采购</el-radio-button>
                        <el-radio-button label="1">已保存</el-radio-button>
                        <el-radio-button label="2">已采购</el-radio-button>
                    </el-radio-group>
                </el-col>
            </el-row>
            <el-row :gutter="20">
                <el-col :span="24" :offset="0">
                    <el-table :data="paginatedList" border stripe height="250" style="width: 100%">
                        <el-table-column prop="orderRid" label="订单号"></el-table-column>
                        <el-table-column prop="orderCid" label="客户订单号"></el-table-column>
                        <el-table-column prop="customerName" label="客户名"></el-table-column>
                        <el-table-column prop="orderStartDate" label="下单日期"></el-table-column>
                        <el-table-column prop="orderStatus" label="订单状态"></el-table-column>
                        <el-table-column prop="orderPackagingStatus" label="包材采购状态" :formatter="packageStatusFormatter"></el-table-column>
                        <el-table-column label="操作" width="400">
                            <template #default="scope">
                                <div v-if="scope.row.orderPackagingStatus === '0'">
                                    <el-button type="primary" size="mini" @click="viewPackagingInfo(scope.row)">查看包装资料</el-button>
                                    <el-button type="primary" size="mini" @click="createPackagePurchaseOrder(scope.row)">创建包装材料采购订单</el-button>
                                </div>
                                <div v-else-if="scope.row.orderPackagingStatus === '1'">
                                    <el-button type="primary" size="mini" @click="viewPackagingInfo(scope.row)">查看包装资料</el-button>
                                    <el-button type="primary" size="mini" @click="editPackagePurchaseOrder(scope.row)">编辑包装材料采购订单</el-button>
                                </div>
                                <div v-else>
                                    <el-button type="primary" size="mini" @click="viewPackagingInfo(scope.row)">查看包装资料</el-button>
                                </div>
                            </template>
                        </el-table-column>
                    </el-table>
                </el-col>
            </el-row>
            <el-row :gutter="20">
                <el-col :span="24" :offset="0">
                    <el-pagination
                        @size-change="handleSizeChange"
                        @current-change="handleCurrentChange"
                        :current-page="currentPage"
                        :page-sizes="[10, 20, 30, 40]"
                        :page-size="pageSize"
                        layout="total, sizes, prev, pager, next, jumper"
                        :total="filteredList.length">
                    </el-pagination>
                </el-col>
            </el-row>
            <el-divider></el-divider>
            <el-row :gutter="20">
                <el-col :span="8" :offset="0" :key="currentEditPurchaseOrderRid">
                    采购订单创建 {{ currentEditPurchaseOrderRid }}
                </el-col>
            </el-row>
            <div v-if="currentEditPurchaseOrderRid !== ''">
                <el-row :gutter="20">
                    <el-col :span="24" :offset="0">
                        <el-form ref="purchaseForm" :model="assetForm" :rules="rules">
                            <purchase-items-table 
                                :material-type-options="materialTypeOptions" 
                                @update-items="updateNewPurchaseData"
                                :batch-info-visible="0"
                                :purchaseData.sync="assetForm.purchaseData"
                                :type-limit="[6]"
                            ></purchase-items-table>
                        </el-form>
                    </el-col>
                </el-row>
                <el-row :gutter="20">
                    <el-col :span="4" :offset="22">
                        <el-button type="primary" size="medium" @click="savePackagePurchaseOrder" :disabled="currentEditPurchaseOrderRid === ''">保存采购订单</el-button>

                    </el-col>
                </el-row>
            </div>
            
            
            
        </el-main>
    </el-container>
</template>

<script>
import axios from 'axios'
import PurchaseItemsTable from '@/Pages/LogisticsControlDepartment/LogisticsControlManager/components/VariousPurchaseTables/PurchaseItemsTable.vue';
import { ElMessage } from 'element-plus';
export default {
    components: {
        PurchaseItemsTable
    },
    data() {
        return {
            orderSearch: '',
            customerSearch: '',
            orderList: [],
            filteredList: [],
            currentPage: 1,
            pageSize: 10,
            orderPackagingStatus: '0',
            materialTypeOptions: [],
            currentEditPurchaseOrderRid: '',
            currentEditPurchaseOrderId: 0,
            createEditSymbol: 0,
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
        this.getAllOrders();
        this.getAllMaterialTypes();
    },
    methods: {
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
        packageStatusFormatter(row) {
            switch (row.orderPackagingStatus) {
                case '0':
                    return '未采购';
                case '1':
                    return '已保存';
                case '2':
                    return '已采购';
            }
        },
        viewPackagingInfo(row) {
            window.open(`${this.$apiBaseUrl}/orderimport/downloadorderdoc?orderrid=${row.orderRid}&filetype=2`);
        },
        async createPackagePurchaseOrder(row) {
            if (this.currentEditPurchaseOrderRid != '') {
                this.$confirm('当前有未保存的采购订单，是否放弃编辑?', '提示', {
                    confirmButtonText: '确定',
                    cancelButtonText: '取消',
                    type: 'warning'
                }).then(async () => {
                    this.currentEditPurchaseOrderRid = '';
                    const response = await axios.get(`${this.$apiBaseUrl}/logistics/getnewpackagepurchaseorderid`, {
                        params: {
                            orderid: row.orderDbId
                        }
                    });
                    this.currentEditPurchaseOrderRid = response.data.purchaseOrderRid;
                    this.createEditSymbol = 0;
                    this.assetForm.purchaseData = [];
                    this.assetForm.orderId = row.orderDbId;
                    this.assetForm.purchaseOrderType = 'P';
                    console.log(this.currentEditPurchaseOrderRid);
                    return
                }).catch(() => {
                    return;
                });
            }
            else {
                const response = await axios.get(`${this.$apiBaseUrl}/logistics/getnewpackagepurchaseorderid`, {
                    params: {
                        orderid: row.orderDbId
                    }
                });
                this.currentEditPurchaseOrderRid = response.data.purchaseOrderRid;
                this.createEditSymbol = 0;
                this.assetForm.purchaseData = [];
                this.assetForm.orderId = row.orderDbId;
                this.assetForm.purchaseOrderType = 'P';
                console.log(this.currentEditPurchaseOrderRid);
            }
        },
        async editPackagePurchaseOrder(row) {
            if (this.currentEditPurchaseOrderRid != '') {
                this.$confirm('当前有未保存的采购订单，是否放弃编辑?', '提示', {
                    confirmButtonText: '确定',
                    cancelButtonText: '取消',
                    type: 'warning'
                }).then(async () => {
                    this.currentEditPurchaseOrderRid = '';
                    const response = await axios.get(`${this.$apiBaseUrl}/logistics/getpackagepurchaseorderitems`, {
                        params: {
                            orderid: row.orderDbId
                        }
                    });
                    this.currentEditPurchaseOrderRid = response.data.purchaseOrderRid;
                    this.createEditSymbol = 1;
                    this.assetForm.purchaseData = response.data.purchaseOrderItems;
                    this.assetForm.orderId = row.orderDbId;
                    this.assetForm.purchaseOrderType = 'P';
                    console.log(this.currentEditPurchaseOrderRid);
                    return
                }).catch(() => {
                    return;
                });
            }
            else {
                this.createEditSymbol = 1;
                const response = await axios.get(`${this.$apiBaseUrl}/logistics/getpackagepurchaseorderitems`, {
                    params: {
                        orderid: row.orderDbId
                    }
                });
                this.currentEditPurchaseOrderRid = response.data.purchaseOrderRid;
                this.assetForm.purchaseData = response.data.purchaseOrderItems;
                this.assetForm.orderId = row.orderDbId;
                this.assetForm.purchaseOrderType = 'P';
                console.log(this.currentEditPurchaseOrderRid);
            }
        },
        updateNewPurchaseData(updatedItems) {
            this.assetForm.purchaseData = [...updatedItems]

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
                                    batchInfoType : this.assetForm.batchInfoType,
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
                                    batchInfoType : this.assetForm.batchInfoType,
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
            })
        },

        handleFilter() {
            this.currentPage = 1;
            this.filteredList = this.orderList.filter(order => {
                return (
                    (!this.orderSearch || order.orderRid.includes(this.orderSearch)) &&
                    (!this.customerSearch || order.customerName.includes(this.customerSearch)) &&
                    (order.orderPackagingStatus === this.orderPackagingStatus)
                );
            });
        },
        handleSizeChange(newSize) {
            this.pageSize = newSize;
            this.currentPage = 1;
        },
        handleCurrentChange(newPage) {
            this.currentPage = newPage;
        }
    }
}
</script>
