<template>
    <el-row :gutter="20">
        <el-col :span="24" :offset="0" style="font-size: xx-large; text-align: center"
            >固定资产/耗材采购订单生成</el-col
        >
    </el-row>
    <el-row :gutter="20" style="margin-top: 20px">
        <el-col :span="4" :offset="0"
            ><el-button-group>
                <el-button type="primary" size="default" @click="openCreatePage(null, 0)"
                    >新建耗材/固定资产采购订单</el-button
                >
            </el-button-group>
        </el-col>
        <el-col :span="2" :offset="0"
            ><el-button-group>
                <el-button type="primary" size="default" @click="openPackagePage"
                    >新建包材采购订单</el-button
                >
            </el-button-group>
        </el-col>
        <el-col :span="2" :offset="1"
            ><el-button type="primary" size="default" @click="openLastPage"
                    >新建楦头采购订单</el-button
                >
        </el-col>
        <el-col :span="2" :offset="1"
            ><el-button type="primary" size="default" @click="openCutModelPage"
                    >新建刀模采购订单</el-button
                >
        </el-col>
        <el-col :span="4" :offset="4"
            ><el-button type="warning" size="large" @click="openUnsubmitDialog"
                >待提交订单</el-button
            >
        </el-col>
    </el-row>
    <el-row :gutter="20" style="margin-top: 20px">
        <el-col :span="6" :offset="0">
            <div style="display: flex; align-items: center; white-space: nowrap">
                采购订单编号查询：<el-input
                    v-model="orderSearch"
                    placeholder=""
                    size="default"
                    :suffix-icon="Search"
                    clearable
                    @input="tableWholeFilter"
                ></el-input>
            </div>
        </el-col>
        <el-col :span="6" :offset="0">
            <div style="display: flex; align-items: center; white-space: nowrap">
                采购类型查询：
                <el-select
                    v-model="isPurchaseOrderFilter"
                    value-key=""
                    placeholder=""
                    clearable
                    filterable
                    @change="tableWholeFilter"
                >
                    <el-option
                        v-for="item in isPurchaseOrderOptions"
                        :key="item.value"
                        :label="item.label"
                        :value="item.value"
                    >
                    </el-option>
                </el-select>
            </div>
        </el-col>
        <el-col :span="6" :offset="0">
            <div style="display: flex; align-items: center; white-space: nowrap">
                订单号查询：
                <el-input
                    v-model="orderRIdSearch"
                    placeholder=""
                    size="default"
                    :suffix-icon="Search"
                    clearable
                    @input="tableWholeFilter"
                ></el-input>
            </div>
        </el-col>
        <el-col :span="6" :offset="0">
            <div style="display: flex; align-items: center; white-space: nowrap">
                工厂型号查询：<el-input
                    v-model="shoeRIdSearch"
                    placeholder=""
                    size="default"
                    :suffix-icon="Search"
                    clearable
                    @input="tableWholeFilter"
                ></el-input>
            </div>
        </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px">
        <el-col :span="24" :offset="0">
            <el-table
                v-loading="datafinished"
                :data="paginatedMaterialPurchaseData"
                border
                style="height: 450px"
                ref="singleSelectTable"
                @selection-change="handleSelectionChange"
            >
                <el-table-column type="selection" width="55"></el-table-column>
                <el-table-column prop="purchaseOrderRId" label="采购订单编号"></el-table-column>
                <el-table-column prop="createDate" label="采购下发日期"></el-table-column>
                <el-table-column prop="purchaseOrderType" label="采购类型"></el-table-column>
                <el-table-column prop="orderRId" label="订单编号"></el-table-column>
                <el-table-column prop="shoeRId" label="工厂型号"></el-table-column>
                <el-table-column label="操作" width="300">
                    <template #default="scope">
                        <el-button type="primary" @click="openPreviewDialog(scope.row)"
                            >查看</el-button
                        >
                        <el-button type="success" @click="downloadZip(scope.row)"
                            >下载采购订单压缩包</el-button
                        >
                    </template>
                </el-table-column>
            </el-table>
            <el-pagination
                background
                :total="filteredMaterialPurchaseData.length"
                :current-page="currentPage"
                :page-size="pageSize"
                layout="total, sizes, prev, pager, next, jumper"
                @size-change="handleSizeChange"
                @current-change="handlePageChange"
            ></el-pagination>
        </el-col>
    </el-row>
    <!-- TODO -->
    <!-- <el-row :gutter="20">
        <el-col>
            <el-pagination background :total="materialPurchaseFilterData.length" :current-page="currentPage" :page-sizes="[10, 20, 30, 40]" :page-size="pageSize"
                layout="total, sizes, prev, pager, next, jumper" :total="totalRows"></el-pagination>
        </el-col>
    </el-row> -->
    <!--未提交订单对话框-->
    <el-dialog
        title="未提交订单一览"
        v-model="unsubmitVis"
        width="90%"
        :close-on-click-modal="false"
    >
        <el-row :gutter="20" style="margin-top: 20px">
            <el-col :span="24" :offset="0">
                <el-table :data="unsubmitPurchaseOrder" border style="height: 600px">
                    <el-table-column prop="purchaseOrderRId" label="采购订单编号"></el-table-column>
                    <el-table-column prop="purchaseOrderType" label="采购类型"></el-table-column>
                    <el-table-column prop="orderRId" label="订单编号"></el-table-column>
                    <el-table-column prop="shoeRId" label="工厂型号"></el-table-column>
                    <el-table-column label="操作">
                        <template #default="scope">
                            <!-- <el-button type="primary" @click="openPreviewDialog(scope.row)">查看</el-button> -->
                            <el-button type="primary" @click="openCreatePage(scope.row, 1)"
                                >编辑</el-button
                            >
                            <el-button type="success" @click="openSubmitDialog(scope.row)"
                                >提交</el-button
                            >
                            <el-button type="danger" @click="deleteUnsubmitPurchaseOrder(scope.row)"
                                >删除</el-button
                            >
                        </template></el-table-column
                    >
                </el-table>
            </el-col>
        </el-row>
        <template #footer>
            <span>
                <el-button type="primary" @click="unsubmitVis = false">确认</el-button>
            </span>
        </template>
    </el-dialog>

    <!--采购材料对话框-->
    <el-dialog
        title="添加新采购材料"
        v-model="newMaterialVis"
        width="60%"
        :close-on-click-modal="false"
    >
        <el-row :gutter="20">
            <el-col :span="6" :offset="0">
                <div style="display: flex; align-items: center; white-space: nowrap">
                    材料类型查询：<el-input
                        v-model="addMaterialDialogField.materialTypeSearch"
                        placeholder=""
                        size="default"
                        :suffix-icon="Search"
                        clearable
                        @change="getMaterialFilterData(currentCreateViewId)"
                    ></el-input>
                </div>
            </el-col>
            <el-col :span="6" :offset="0">
                <div style="display: flex; align-items: center; white-space: nowrap">
                    材料名称查询：<el-input
                        v-model="addMaterialDialogField.materialSearch"
                        placeholder=""
                        size="default"
                        :suffix-icon="Search"
                        clearable
                        @change="getMaterialFilterData(currentCreateViewId)"
                    ></el-input>
                </div>
            </el-col>
            <el-col :span="6" :offset="0">
                <div style="display: flex; align-items: center; white-space: nowrap">
                    工厂名查询：<el-input
                        v-model="addMaterialDialogField.factorySearch"
                        placeholder=""
                        size="default"
                        :suffix-icon="Search"
                        clearable
                        @change="getMaterialFilterData(currentCreateViewId)"
                    ></el-input>
                </div>
            </el-col>
        </el-row>
        <el-table
            :data="assetFilterTable"
            border
            ref="materialSelectTable"
            @selection-change="handleMaterialSelectionChange"
            style="height: 400px"
            v-loading="materialAddfinished"
        >
            <el-table-column type="selection" width="55"></el-table-column>
            <el-table-column prop="materialType" label="材料类型" />
            <el-table-column prop="materialName" label="材料名称" />
            <el-table-column prop="warehouseName" label="所属仓库" />
            <el-table-column prop="unit" label="单位" />
            <el-table-column prop="supplierName" label="工厂名称" />
        </el-table>

        <template #footer>
            <span>
                <el-button @click="newMaterialVis = false">取消</el-button>
                <el-button
                    v-if="currentCreateViewId == 0"
                    type="primary"
                    @click="confirmNewMaterialAdd"
                    >确认</el-button
                >
                <el-button
                    v-else-if="currentCreateViewId == 1"
                    type="primary"
                    @click="confirmNewSizeMaterialAdd"
                    >确认</el-button
                >
                <el-button
                    v-else-if="currentCreateViewId == 2"
                    type="primary"
                    @click="confirmEditNewMaterialAdd"
                    >确认</el-button
                >
                <el-button
                    v-else-if="currentCreateViewId == 3"
                    type="primary"
                    @click="confirmEditSizeNewMaterialAdd"
                    >确认</el-button
                >
            </span>
        </template>
    </el-dialog>
    <!--采购订单预览-->
    <el-dialog
        :title="`耗材/固定资产采购订单 ${currentViewPurchaseOrderId} 预览`"
        v-model="purchaseOrderVis"
        width="90%"
        :close-on-click-modal="false"
        :key="currentViewPurchaseOrderId"
    >
        <div style="height: 500px; overflow-y: scroll; overflow-x: hidden">
            <el-row
                v-for="purchaseDivideOrder in purchaseTestData"
                :key="purchaseDivideOrder"
                :gutter="20"
                style="margin-bottom: 20px"
            >
                <el-col :span="23">
                    <h3>分采购订单编号 {{ purchaseDivideOrder.purchaseDivideOrderId }}</h3>
                    <h3>工厂名称: {{ purchaseDivideOrder.supplierName }}</h3>
                    <el-row :gutter="20">
                        <el-col :span="12" :offset="0"
                            ><span
                                >订单备注：
                                {{ purchaseDivideOrder.remark }}
                            </span></el-col
                        >
                        <el-col :span="12" :offset="0">
                            <span
                                >环境要求：
                                {{ purchaseDivideOrder.evironmentalRequest }}
                            </span>
                        </el-col>
                    </el-row>
                    <el-row :gutter="20">
                        <el-col :span="12" :offset="0"
                            ><span
                                >发货地址: {{ purchaseDivideOrder.shipmentAddress }}
                            </span></el-col
                        >
                        <el-col :span="12" :offset="0">
                            <span>交货周期: {{ purchaseDivideOrder.shipmentDeadline }} </span>
                        </el-col>
                    </el-row>
                    <div v-if="factoryFieldJudge(purchaseDivideOrder.purchaseDivideOrderType)">
                        <el-table
                            :data="purchaseDivideOrder.assetsItems"
                            border
                            style="width: 100%"
                        >
                            <el-table-column type="index" label="编号" />
                            <el-table-column prop="materialType" label="材料类型"></el-table-column>
                            <el-table-column prop="materialName" label="材料名称" />
                            <el-table-column
                                prop="materialSpecification"
                                label="材料规格"
                            ></el-table-column>
                            <el-table-column prop="unit" label="单位" />

                            <el-table-column prop="purchaseAmount" label="采购数量" />
                            <el-table-column prop="sizeType" label="分码类型"></el-table-column>
                            <el-table-column label="分码数量">
                                <el-table-column
                                    v-for="size in dynamicSizes"
                                    :key="size"
                                    :label="size"
                                    width="60"
                                >
                                    <template #default="scope">
                                        {{ scope.row[size] || 0 }}
                                    </template>
                                </el-table-column>
                            </el-table-column>
                            <el-table-column prop="comment" label="备注" />
                        </el-table>
                    </div>
                    <div v-else>
                        <el-table
                            :data="purchaseDivideOrder.assetsItems"
                            border
                            style="width: 100%"
                        >
                            <el-table-column type="index" label="编号" />
                            <el-table-column prop="materialType" label="材料类型"></el-table-column>
                            <el-table-column prop="materialName" label="材料名称" />
                            <el-table-column
                                prop="materialSpecification"
                                label="材料规格"
                            ></el-table-column>
                            <el-table-column prop="color" label="颜色" />
                            <el-table-column prop="unit" label="单位" />
                            <el-table-column prop="purchaseAmount" label="采购数量" />
                            <el-table-column prop="remark" label="备注" />
                        </el-table>
                    </div>
                </el-col>
            </el-row>
        </div>
        <template #footer>
            <span>
                <el-button type="primary" @click="purchaseOrderVis = false">确认</el-button>
            </span>
        </template>
    </el-dialog>
    <el-dialog
        :title="`创建尺码型号采购订单 ${newSizePurchaseOrderId}`"
        v-model="isLastPurchaseOrderDialogVisible"
        :close-on-click-modal="false"
        width="80%"
    >
        <el-table :data="lastData" border stripe>
            <el-table-column prop="materialType" label="材料类型" />
            <el-table-column prop="materialName" label="材料名称" />
            <el-table-column prop="materialSpecification" label="材料规格">
                <template #default="scope">
                    <el-input
                        v-model="scope.row.materialSpecification"
                        placeholder=""
                        size="default"
                        clearable
                    ></el-input>
                </template>
            </el-table-column>
            <el-table-column label="颜色">
                <template #default="scope">
                    <el-input v-model="scope.row.color" placeholder=""> </el-input>
                </template>
            </el-table-column>
            <el-table-column prop="warehouseName" label="所属仓库" />
            <el-table-column prop="unit" label="单位" />
            <el-table-column prop="supplierName" label="工厂名称"> </el-table-column>
            <el-table-column label="型号填写">
                <template #default="scope">
                    {{ scope.row.sizeStatus }}
                    <el-button
                        type="primary"
                        size="default"
                        @click="openSizeDialog(scope.row, scope.$index, 0)"
                        >尺码信息</el-button
                    >
                </template>
            </el-table-column>
            <el-table-column label="备注">
                <template #default="scope">
                    <el-input
                        v-model="scope.row.comment"
                        placeholder=""
                        size="default"
                        clearable
                    ></el-input>
                </template>
            </el-table-column>
            <el-table-column label="操作">
                <template #default="scope">
                    <el-button type="danger" @click="deleteCurrentRow(scope.$index, lastData)"
                        >删除</el-button
                    >
                </template>
            </el-table-column>
        </el-table>
        <el-button type="primary" size="default" @click="openNewMaterialDialog(1)"
            >添加新材料</el-button
        >
        <template #footer>
            <span>
                <el-button @click="isLastPurchaseOrderDialogVisible = false">取消</el-button>
                <el-button type="primary" @click="newSizePurchaseOrderSave">保存</el-button>
            </span>
        </template>
    </el-dialog>
    <el-dialog
        title="尺码数量填写"
        v-model="isSizeDialogVisible"
        width="60%"
        :close-on-click-modal="false"
    >
        <el-table :data="sizeData" border stripe>
            <el-table-column prop="size" label="尺码"></el-table-column>
            <el-table-column prop="innerSize" label="内码"></el-table-column>
            <el-table-column prop="outterSize" label="外显"></el-table-column>
            <el-table-column label="采购数量">
                <template #default="scope">
                    <el-input-number v-model="scope.row.purchaseAmount" :min="0" size="small" />
                </template>
            </el-table-column>
        </el-table>

        <template #footer>
            <span>
                <el-button type="primary" @click="confirmSizeAmount(currentSizeData)"
                    >确认</el-button
                >
            </span>
        </template>
    </el-dialog>
    <el-dialog title="采购订单创建页面" v-model="isPurchaseOrderVis" width="90%">
        <el-tabs v-model="activeTab" type="card" tab-position="top">
            <el-tab-pane
                v-for="item in tabPlaneData"
                :key="item.purchaseDivideOrderId"
                :label="item.purchaseDivideOrderId + '    ' + item.supplierName"
                :name="item.purchaseDivideOrderId"
                style="min-height: 500px"
            >
                <el-row :gutter="20">
                    <el-col :span="12" :offset="0"
                        ><span
                            >订单备注：
                            <el-input
                                v-model="item.remark"
                                placeholder=""
                                type="textarea"
                                resize="none"
                                size=""
                                clearable
                            ></el-input> </span
                    ></el-col>
                    <el-col :span="12" :offset="0">
                        <span
                            >环境要求：
                            <el-input
                                v-model="item.evironmentalRequest"
                                placeholder=""
                                type="textarea"
                                resize="none"
                                size=""
                                clearable
                            ></el-input>
                        </span>
                    </el-col>
                </el-row>
                <el-row :gutter="20">
                    <el-col :span="12" :offset="0">
                        <span
                            >发货地址：
                            <el-input
                                v-model="item.shipmentAddress"
                                placeholder=""
                                type="textarea"
                                resize="none"
                                size=""
                                clearable
                            ></el-input>
                        </span>
                    </el-col>
                    <el-col :span="12" :offset="0">
                        <span
                            >交货周期：
                            <el-input
                                v-model="item.shipmentDeadline"
                                placeholder=""
                                type="textarea"
                                resize="none"
                                size=""
                                clearable
                            ></el-input>
                        </span>
                    </el-col>
                </el-row>
                <el-row :gutter="20" style="margin-top: 20px">
                    <el-col :span="24" :offset="0">
                        <div v-if="factoryFieldJudge(item.purchaseDivideOrderType)">
                            <el-table :data="item.assetsItems" border height="500">
                                <el-table-column type="index" label="编号" />
                                <el-table-column
                                    prop="materialType"
                                    label="材料类型"
                                ></el-table-column>
                                <el-table-column prop="materialName" label="材料名称" />
                                <el-table-column
                                    prop="materialSpecification"
                                    label="材料规格"
                                ></el-table-column>
                                <el-table-column prop="unit" label="单位" />

                                <el-table-column prop="purchaseAmount" label="采购数量" />
                                <el-table-column prop="sizeType" label="分码类型"></el-table-column>
                                <el-table-column label="分码数量">
                                    <el-table-column
                                        v-for="size in dynamicSizes"
                                        :key="size"
                                        :label="size"
                                        width="60"
                                    >
                                        <template #default="scope">
                                            {{ scope.row[size] || 0 }}
                                        </template>
                                    </el-table-column>
                                </el-table-column>
                                <el-table-column prop="comment" label="备注" />
                            </el-table>
                        </div>
                        <div v-else>
                            <el-table :data="item.assetsItems" border stripe height="500">
                                <el-table-column type="index"></el-table-column>
                                <el-table-column
                                    prop="materialType"
                                    label="材料类型"
                                ></el-table-column>
                                <el-table-column prop="materialName" label="材料名称" />
                                <el-table-column
                                    prop="materialModel"
                                    label="材料型号"
                                ></el-table-column>
                                <el-table-column
                                    prop="materialSpecification"
                                    label="材料规格"
                                ></el-table-column>
                                <el-table-column prop="color" label="颜色" />
                                <el-table-column prop="unit" label="单位" />
                                <el-table-column prop="purchaseAmount" label="数量" />
                                <el-table-column prop="remark" label="备注" />
                            </el-table>
                        </div>
                    </el-col>
                </el-row>
            </el-tab-pane>
        </el-tabs>

        <template #footer>
            <span>
                <el-button @click="isPurchaseOrderVis = false">取消</el-button>
                <el-button type="primary" @click="saveUnsubmitPurchaseOrder">保存</el-button>
                <el-button type="success" @click="confirmSubmitPurchaseOrder">提交</el-button>
            </span>
        </template>
    </el-dialog>
    <el-dialog
        :title="`编辑尺码型号采购订单 ${editPurchaseOrderId}`"
        v-model="editLastPurchaseOrderDialogVisible"
        :close-on-click-modal="false"
        width="80%"
    >
        <el-table :data="editLastData" border stripe>
            <el-table-column prop="materialType" label="材料类型" />
            <el-table-column prop="materialName" label="材料名称" />
            <el-table-column prop="materialSpecification" label="材料规格">
                <template #default="scope">
                    <el-input
                        v-model="scope.row.materialSpecification"
                        placeholder=""
                        size="default"
                        clearable
                    ></el-input>
                </template>
            </el-table-column>
            <el-table-column label="颜色">
                <template #default="scope">
                    <el-input v-model="scope.row.color" placeholder=""> </el-input>
                </template>
            </el-table-column>
            <el-table-column prop="warehouseName" label="所属仓库" />
            <el-table-column prop="unit" label="单位" />
            <el-table-column prop="supplierName" label="工厂名称"> </el-table-column>
            <el-table-column label="型号填写">
                <template #default="scope">
                    {{ scope.row.sizeStatus }}
                    <el-button
                        type="primary"
                        size="default"
                        @click="openSizeDialog(scope.row, scope.$index, 1)"
                        >尺码信息</el-button
                    >
                </template>
            </el-table-column>
            <el-table-column label="备注">
                <template #default="scope">
                    <el-input
                        v-model="scope.row.comment"
                        placeholder=""
                        size="default"
                        clearable
                    ></el-input>
                </template>
            </el-table-column>
            <el-table-column label="操作">
                <template #default="scope">
                    <el-button type="danger" @click="deleteCurrentRow(scope.$index, editLastData)"
                        >删除</el-button
                    >
                </template>
            </el-table-column>
        </el-table>
        <el-button type="primary" size="default" @click="openNewMaterialDialog(3)"
            >添加新材料</el-button
        >
        <template #footer>
            <span>
                <el-button @click="editLastPurchaseOrderDialogVisible = false">取消</el-button>
                <el-button type="primary" @click="editSizePurchaseOrderSave">保存</el-button>
            </span>
        </template>
    </el-dialog>
</template>
<script>
import { Search } from '@element-plus/icons-vue'
import { markRaw } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import axios from 'axios'
import PurchaseForOrderTable from './VariousPurchaseTables/PurchaseItemsTable.vue'
export default {
    components: {
        PurchaseForOrderTable
    },
    data() {
        return {
            currentPage: 1,
            pageSize: 10,
            currentPurchaseTab: 0,
            currentSizeData: 0,
            editVis: false,
            editPurchaseOrderId: '',
            editAssetPurchaseData: [],
            editLastPurchaseOrderDialogVisible: false,
            editLastData: [],
            currentSizeIndex: 0,
            currentViewPurchaseOrderId: '',
            currentSubmitPurchaseOrderId: '',
            currentCreateViewId: 0,
            unsubmitfinished: true,
            materialAddfinished: true,
            newPurchaseOrderId: '',
            newSizePurchaseOrderId: '',
            datafinished: true,
            activeTab: '',
            isPurchaseOrderVis: false,
            isSizeDialogVisible: false,
            isLastPurchaseOrderDialogVisible: false,
            sizeData: [],
            lastData: [],
            finishedNum: 1,
            unsubmitVis: false,
            createVis: false,
            newMaterialVis: false,
            purchaseOrderVis: false,
            orderSearch: '',
            assetsTypeSearch: '',
            isPurchaseOrderFilter: '',
            isPurchaseOrderOptions: [
                { value: '随订单采购', label: '随订单采购' },
                { value: '随订单鞋型采购', label: '随订单鞋型采购' },
                { value: '独立采购', label: '独立采购' }
            ],
            assetTable: [],
            assetFilterTable: [],
            unsubmitPurchaseOrder: [],
            Search: markRaw(Search),
            materialPurchaseTestData: [],
            materialPurchaseFilterData: [],
            selectedRow: null,
            materialSelectRow: null,
            newAssetPurchaseData: [],
            factoryOptions: [],
            tabPlaneData: [],
            orderRIdSearch: '',
            shoeRIdSearch: '',
            addMaterialDialogField: {},
            addMaterialTemplate: {
                materialTypeSearch: '',
                materialSearch: '',
                factorySearch: ''
            },
            materialTypeOptions: [],
            selectedOrderIdRef: null,
            dynamicSizes: []
        }
    },
    mounted() {
        this.getMaterialPurchaseData()
    },
    computed: {
        // Filtered data based on search inputs
        filteredMaterialPurchaseData() {
            return this.materialPurchaseTestData.filter((item) => {
                const orderSearchMatch = item.purchaseOrderRId
                    ?.toString()
                    .includes(this.orderSearch.trim())
                const isPurchaseOrderMatch = this.isPurchaseOrderFilter
                    ? item.purchaseOrderType === this.isPurchaseOrderFilter
                    : true
                const orderRIdMatch = this.orderRIdSearch.trim()
                    ? item.orderRId && item.orderRId.toString().includes(this.orderRIdSearch.trim()) // Exclude nulls
                    : true // Include all if filter is empty
                const shoeRIdMatch = this.shoeRIdSearch.trim()
                    ? item.shoeRId && item.shoeRId.toString().includes(this.shoeRIdSearch.trim()) // Exclude nulls
                    : true // Include all if filter is empty

                return orderSearchMatch && isPurchaseOrderMatch && orderRIdMatch && shoeRIdMatch
            })
        },

        // Paginated data for the table
        paginatedMaterialPurchaseData() {
            const startIndex = (this.currentPage - 1) * this.pageSize
            const endIndex = this.currentPage * this.pageSize
            return this.filteredMaterialPurchaseData.slice(startIndex, endIndex)
        }
    },
    methods: {
        handleSizeChange(size) {
            this.pageSize = size
        },
        // Handle pagination page change
        handlePageChange(page) {
            this.currentPage = page
        },
        // Filter table when search inputs change
        tableWholeFilter() {
            this.currentPage = 1 // Reset to first page when filters change
        },
        async getMaterialPurchaseData() {
            this.datafinished = true
            const response = await axios.get(
                `${this.$apiBaseUrl}/logistics/assetsmaterialpurchaseorder`,
                {
                    params: {
                        purchaseorderstatus: '2'
                    }
                }
            )
            this.materialPurchaseTestData = response.data
            this.materialPurchaseFilterData = this.materialPurchaseTestData
            this.datafinished = false
        },
        async getUnsubmitPurchaseOrder() {
            this.unsubmitfinished = true
            const response = await axios.get(
                `${this.$apiBaseUrl}/logistics/assetsmaterialpurchaseorder`,
                {
                    params: {
                        purchaseorderstatus: '1'
                    }
                }
            )
            this.unsubmitPurchaseOrder = response.data
            this.unsubmitfinished = false
        },
        async getSizeMaterialList() {
            const response = await axios.get(
                `${this.$apiBaseUrl}/logistics/getmaterialtypeandname`,
                {
                    params: {
                        materialcategory: 1
                    }
                }
            )
            this.assetTable = response.data
            this.assetFilterTable = this.assetTable
        },
        async getMaterialList() {
            const response = await axios.get(
                `${this.$apiBaseUrl}/logistics/getmaterialtypeandname`,
                {
                    params: {
                        materialcategory: 0
                    }
                }
            )
            this.assetTable = response.data
            this.assetFilterTable = this.assetTable
        },
        async getSizeMaterialFilterData() {
            this.materialAddfinished = true
            const response = await axios.get(
                `${this.$apiBaseUrl}/logistics/getmaterialtypeandname`,
                {
                    params: {
                        materialtype: this.addMaterialDialogField.materialTypeSearch,
                        materialname: this.addMaterialDialogField.materialSearch,
                        suppliername: this.addMaterialDialogField.factorySearch,
                        materialcategory: 1
                    }
                }
            )
            this.assetFilterTable = response.data
            this.materialAddfinished = false
        },
        async getMaterialFilterData() {
            this.materialAddfinished = true
            const response = await axios.get(
                `${this.$apiBaseUrl}/logistics/getmaterialtypeandname`,
                {
                    params: {
                        materialtype: this.addMaterialDialogField.materialTypeSearch,
                        materialname: this.addMaterialDialogField.materialSearch,
                        suppliername: this.addMaterialDialogField.factorySearch,
                        materialcategory: this.currentCreateViewId
                    }
                }
            )
            this.assetFilterTable = response.data
            this.materialAddfinished = false
        },
        factoryFieldJudge(type) {
            console.log(type)
            return type !== 'N'
        },
        openUnsubmitDialog() {
            this.unsubmitVis = true
            this.getUnsubmitPurchaseOrder()
        },
        openSizeDialog(row, index, type) {
            this.sizeData = row.sizeInfo
            this.isSizeDialogVisible = true
            this.currentSizeIndex = index
            this.currentSizeData = type
        },
        confirmSizeAmount(type) {
            if (type === 0) {
                this.lastData[this.currentSizeIndex].sizeInfo = this.sizeData
            }
            if (type === 1) {
                this.editLastData[this.currentSizeIndex].sizeInfo = this.sizeData
            }

            this.isSizeDialogVisible = false
        },
        handleSelectionChange(selection) {
            if (selection.length > 1) {
                // Ensure only one row is selected
                this.$refs.singleSelectTable.clearSelection()
                this.$refs.singleSelectTable.toggleRowSelection(
                    selection[selection.length - 1],
                    true
                )
            } else {
                this.selectedRow = selection[0]
            }
            console.log(this.selectedRow)
        },
        handleMaterialSelectionChange(selection) {
            if (selection.length > 1) {
                // Ensure only one row is selected
                this.$refs.materialSelectTable.clearSelection()
                this.$refs.materialSelectTable.toggleRowSelection(
                    selection[selection.length - 1],
                    true
                )
            } else {
                this.materialSelectRow = selection[0]
            }
            console.log(this.materialSelectRow)
        },
        openCreatePage(row, operation) {
            // if create new order
            let url
            if (operation == 0) {
                url = `${window.location.origin}/logistics/createassetpurchase/purchaseorderid=null`
            }
            // if edit order
            else if (operation == 1) {
                url = `${window.location.origin}/logistics/createassetpurchase/purchaseorderid=${row.purchaseOrderId}`
            }
            window.open(url, '_blank')
        },
        openPackagePage(row) {
            const url = `${window.location.origin}/packagepurchase/`
            window.open(url, '_blank')
        },
        openLastPage(row) {
            const url = `${window.location.origin}/lastpurchase/`
            window.open(url, '_blank')
        },
        openCutModelPage(row) {
            const url = `${window.location.origin}/cutmodelpurchase/`
            window.open(url, '_blank')
        },
        manualAddMaterial() {
            const newItem = {
                materialName: null,
                materialType: null,
                supplierName: null,
                materialSpecification: null,
                materialModel: null,
                color: '',
                unit: '',
                purchaseAmount: 0,
                isPurchaseOrder: 'G',
                comment: '',
                option: this.currentPurchaseTab,
                orderInfo: {},
                orderShoeInfo: {}
            }
            this.newAssetPurchaseData = [...this.newAssetPurchaseData, newItem]
        },
        async openNewMaterialDialog(type) {
            this.newMaterialVis = true
            this.materialAddfinished = true
            this.getActiveOrders()
            this.getActiveOrderShoes()
            if (type == 1 || type == 3) {
                await this.getSizeMaterialList()
            } else if (type == 0 || type == 2) {
                await this.getMaterialList()
            }
            this.addMaterialDialogField = JSON.parse(JSON.stringify(this.addMaterialTemplate))
            this.materialAddfinished = false
        },
        async openPreviewDialog(row) {
            this.currentViewPurchaseOrderId = row.purchaseOrderRId
            try {
                const response = await axios.get(
                    `${this.$apiBaseUrl}/logistics/getassetspurchasedivideorders`,
                    {
                        params: {
                            purchaseOrderId: row.purchaseOrderId
                        }
                    }
                )
                this.purchaseTestData = response.data
                const uniqueSizes = new Set()
                response.data.forEach((divideOrder) => {
                    divideOrder.assetsItems.forEach((item) => {
                        Object.keys(item).forEach((key) => {
                            // Match size keys that start with "size" or are purely numeric (integer or decimal)
                            if (/^[0-9]+(\.[0-9]+)?$/.test(key)) {
                                uniqueSizes.add(key)
                            }
                        })
                    })
                })

                // Convert to array and sort numerically
                this.dynamicSizes = Array.from(uniqueSizes).sort((a, b) => {
                    const sizeA = parseFloat(a.replace(/^size/, '')) // Remove "size" prefix if present
                    const sizeB = parseFloat(b.replace(/^size/, ''))
                    return sizeA - sizeB // Sort numerically
                })
                console.log(this.purchaseTestData)
            } catch (error) {
                console.log(error)
            }
            this.purchaseOrderVis = true
        },
        async openSubmitDialog(row) {
            console.log(row)
            const response = await axios.get(
                `${this.$apiBaseUrl}/logistics/getassetspurchasedivideorders`,
                {
                    params: {
                        purchaseOrderId: row.purchaseOrderId
                    }
                }
            )
            const uniqueSizes = new Set()
            response.data.forEach((divideOrder) => {
                divideOrder.assetsItems.forEach((item) => {
                    Object.keys(item).forEach((key) => {
                        // Match size keys that start with "size" or are purely numeric (integer or decimal)
                        if (/^[0-9]+(\.[0-9]+)?$/.test(key)) {
                            uniqueSizes.add(key)
                        }
                    })
                })
            })

            // Convert to array and sort numerically
            this.dynamicSizes = Array.from(uniqueSizes).sort((a, b) => {
                const sizeA = parseFloat(a.replace(/^size/, '')) // Remove "size" prefix if present
                const sizeB = parseFloat(b.replace(/^size/, ''))
                return sizeA - sizeB // Sort numerically
            })

            // Store the extracted sizes and table data
            this.currentSubmitPurchaseOrderId = row.purchaseOrderId
            this.tabPlaneData = response.data
            this.activeTab = this.tabPlaneData[0].purchaseDivideOrderId
            this.isPurchaseOrderVis = true
        },
        async openEditDialog(row) {
            this.editPurchaseOrderId = row.purchaseOrderId
            const response = await axios.get(
                `${this.$apiBaseUrl}/logistics/getassetspurchaseorderitems`,
                {
                    params: {
                        purchaseOrderId: row.purchaseOrderId
                    }
                }
            )
            if (response.data.purchaseDivideOrderType === 'N') {
                console.log(response.data)
                this.editAssetPurchaseData = response.data.data
                this.editVis = true
                this.currentCreateViewId = 2
            } else {
                this.editLastData = response.data.data
                this.editLastPurchaseOrderDialogVisible = true
                this.currentCreateViewId = 3
            }
        },
        confirmNewSizeMaterialAdd() {
            if (this.materialSelectRow === null) {
                ElMessageBox.alert('材料不能为空！', '警告', { confirmButtonText: '确认' })
                return
            }

            const isDuplicate = this.lastData.some(
                (item) => item.materialName === this.materialSelectRow.materialName
            )

            if (isDuplicate) {
                ElMessageBox.alert('材料名称必须唯一！', '警告', { confirmButtonText: '确认' })
                return
            }

            this.lastData.push({
                materialName: this.materialSelectRow.materialName,
                materialType: this.materialSelectRow.materialType,
                warehouseName: this.materialSelectRow.warehouseName,
                supplierName: this.materialSelectRow.supplierName,
                materialSpecification: this.materialSelectRow.materialSpecification,
                color: '',
                unit: this.materialSelectRow.unit,
                isPurchaseOrder: 'G',
                orderId: '',
                comment: '',
                sizeInfo: [
                    {
                        size: '35',
                        innerSize: '7',
                        outterSize: '7',
                        purchaseAmount: 0
                    },
                    {
                        size: '36',
                        innerSize: '7',
                        outterSize: '7.5',
                        purchaseAmount: 0
                    },
                    {
                        size: '37',
                        innerSize: '8',
                        outterSize: '8',
                        purchaseAmount: 0
                    },
                    {
                        size: '38',
                        innerSize: '8',
                        outterSize: '8.5',
                        purchaseAmount: 0
                    },
                    {
                        size: '39',
                        innerSize: '9',
                        outterSize: '9',
                        purchaseAmount: 0
                    },
                    {
                        size: '40',
                        innerSize: '9',
                        outterSize: '9.5',
                        purchaseAmount: 0
                    },
                    {
                        size: '41',
                        innerSize: '10',
                        outterSize: '10',
                        purchaseAmount: 0
                    },
                    {
                        size: '42',
                        innerSize: '10',
                        outterSize: '10.5',
                        purchaseAmount: 0
                    },
                    {
                        size: '43',
                        innerSize: '11',
                        outterSize: '11',
                        purchaseAmount: 0
                    },
                    {
                        size: '44',
                        innerSize: '12',
                        outterSize: '12',
                        purchaseAmount: 0
                    },
                    {
                        size: '45',
                        innerSize: '13',
                        outterSize: '13',
                        purchaseAmount: 0
                    }
                ]
            })
            this.addMaterialDialogField = JSON.parse(JSON.stringify(this.addMaterialTemplate))
            this.newMaterialVis = false
        },
        async saveUnsubmitPurchaseOrder() {
            try {
                await axios.post(`${this.$apiBaseUrl}/logistics/unsubmitpurchaseordersave`, {
                    data: this.tabPlaneData
                })
                ElMessage.success('保存成功')
            } catch (error) {
                this.$message({
                    type: 'error',
                    message: '保存失败'
                })
            }
        },
        async confirmSubmitPurchaseOrder() {
            this.$confirm('确定提交吗？', '提示', {
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                type: 'warning'
            })
                .then(async () => {
                    try {
                        await axios.post(`${this.$apiBaseUrl}/logistics/submitpurchaseorder`, {
                            purchaseOrderId: this.currentSubmitPurchaseOrderId
                        })
                        this.isPurchaseOrderVis = false
                        this.getUnsubmitPurchaseOrder()
                        this.getMaterialPurchaseData()
                        ElMessage.success('提交成功')
                    } catch (error) {
                        console.log(error)
                        ElMessage.error('提交失败')
                    }
                })
                .catch(() => {
                    this.$message({
                        type: 'info',
                        message: '已取消提交'
                    })
                })
        },
        confirmEditNewMaterialAdd() {
            if (this.materialSelectRow === null) {
                ElMessageBox.alert('材料不能为空！', '警告', { confirmButtonText: '确认' })
                return
            }

            const isDuplicate = this.editAssetPurchaseData.some(
                (item) => item.materialName === this.materialSelectRow.materialName
            )

            if (isDuplicate) {
                ElMessageBox.alert('材料名称必须唯一！', '警告', { confirmButtonText: '确认' })
                return
            }

            this.editAssetPurchaseData.push({
                materialName: this.materialSelectRow.materialName,
                materialType: this.materialSelectRow.materialType,
                warehouseName: this.materialSelectRow.warehouseName,
                supplierName: this.materialSelectRow.supplierName,
                materialSpecification: this.materialSelectRow.materialSpecification,
                color: '',
                unit: this.materialSelectRow.unit,
                purchaseAmount: 0,
                isPurchaseOrder: 'G',
                orderId: '',
                comment: ''
            })
            this.newMaterialVis = false
            this.addMaterialDialogField = JSON.parse(JSON.stringify(this.addMaterialTemplate))
        },
        confirmEditSizeNewMaterialAdd() {
            if (this.materialSelectRow === null) {
                ElMessageBox.alert('材料不能为空！', '警告', { confirmButtonText: '确认' })
                return
            }

            const isDuplicate = this.editLastData.some(
                (item) => item.materialName === this.materialSelectRow.materialName
            )

            if (isDuplicate) {
                ElMessageBox.alert('材料名称必须唯一！', '警告', { confirmButtonText: '确认' })
                return
            }

            this.editLastData.push({
                materialName: this.materialSelectRow.materialName,
                materialType: this.materialSelectRow.materialType,
                warehouseName: this.materialSelectRow.warehouseName,
                supplierName: this.materialSelectRow.supplierName,
                materialSpecification: this.materialSelectRow.materialSpecification,
                color: '',
                unit: this.materialSelectRow.unit,
                isPurchaseOrder: 'G',
                orderId: '',
                comment: '',
                sizeInfo: [
                    {
                        size: '35',
                        innerSize: '7',
                        outterSize: '7',
                        purchaseAmount: 0
                    },
                    {
                        size: '36',
                        innerSize: '7',
                        outterSize: '7.5',
                        purchaseAmount: 0
                    },
                    {
                        size: '37',
                        innerSize: '8',
                        outterSize: '8',
                        purchaseAmount: 0
                    },
                    {
                        size: '38',
                        innerSize: '8',
                        outterSize: '8.5',
                        purchaseAmount: 0
                    },
                    {
                        size: '39',
                        innerSize: '9',
                        outterSize: '9',
                        purchaseAmount: 0
                    },
                    {
                        size: '40',
                        innerSize: '9',
                        outterSize: '9.5',
                        purchaseAmount: 0
                    },
                    {
                        size: '41',
                        innerSize: '10',
                        outterSize: '10',
                        purchaseAmount: 0
                    },
                    {
                        size: '42',
                        innerSize: '10',
                        outterSize: '10.5',
                        purchaseAmount: 0
                    },
                    {
                        size: '43',
                        innerSize: '11',
                        outterSize: '11',
                        purchaseAmount: 0
                    },
                    {
                        size: '44',
                        innerSize: '12',
                        outterSize: '12',
                        purchaseAmount: 0
                    },
                    {
                        size: '45',
                        innerSize: '13',
                        outterSize: '13',
                        purchaseAmount: 0
                    }
                ]
            })
            this.newMaterialVis = false
            this.addMaterialDialogField = JSON.parse(JSON.stringify(this.addMaterialTemplate))
        },
        confirmNewMaterialAdd() {
            if (this.materialSelectRow === null) {
                ElMessageBox.alert('材料不能为空！', '警告', { confirmButtonText: '确认' })
                return
            }

            const isDuplicate = this.newAssetPurchaseData.some(
                (item) => item.materialName === this.materialSelectRow.materialName
            )

            if (isDuplicate) {
                ElMessageBox.alert('材料名称必须唯一！', '警告', { confirmButtonText: '确认' })
                return
            }

            this.newAssetPurchaseData.push({
                materialName: this.materialSelectRow.materialName,
                materialType: this.materialSelectRow.materialType,
                warehouseName: this.materialSelectRow.warehouseName,
                supplierName: this.materialSelectRow.supplierName,
                materialSpecification: null,
                color: '',
                unit: this.materialSelectRow.unit,
                purchaseAmount: 0,
                isPurchaseOrder: 'G',
                orderInfo: {},
                orderShoeInfo: {},
                comment: '',
                option: this.currentPurchaseTab
            })
            console.log(this.newAssetPurchaseData)
            this.newMaterialVis = false
            this.addMaterialDialogField = JSON.parse(JSON.stringify(this.addMaterialTemplate))
        },
        getFilteredFactoryOptions(materialName) {
            const filteredOptions = this.factoryOptions.filter(
                (option) => option.materialName === materialName
            )
            return [{ supplierName: '询价' }, ...filteredOptions]
        },
        deleteCurrentRow(index, datafield) {
            this.$confirm('确定删除此行吗？', '提示', {
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                type: 'warning'
            })
                .then(() => {
                    datafield.splice(index, 1)
                    this.$message({
                        type: 'success',
                        message: '删除成功!'
                    })
                })
                .catch(() => {
                    this.$message({
                        type: 'info',
                        message: '已取消删除'
                    })
                })
        },
        async newSizePurchaseOrderSave() {
            console.log(this.lastData)
            const response = await axios.post(
                `${this.$apiBaseUrl}/logistics/newpurchaseordersave`,
                {
                    data: this.lastData,
                    purchaseOrderId: this.newSizePurchaseOrderId,
                    purchaseDivideOrderType: 'S'
                }
            )
            if (response.status === 200) {
                this.$message({
                    type: 'success',
                    message: '保存成功'
                })
                this.lastData = []
                this.isLastPurchaseOrderDialogVisible = false
                this.newSizePurchaseOrderId = ''
            } else {
                this.$message({
                    type: 'error',
                    message: '保存失败'
                })
            }
        },
        async editSizePurchaseOrderSave() {
            const response = await axios.post(
                `${this.$apiBaseUrl}/logistics/editsavedpurchaseorderitems`,
                {
                    data: this.editLastData,
                    purchaseOrderId: this.editPurchaseOrderId,
                    purchaseDivideOrderType: 'S'
                }
            )
            if (response.status === 200) {
                this.$message({
                    type: 'success',
                    message: '保存成功'
                })
                this.editLastData = []
                this.editLastPurchaseOrderDialogVisible = false
                this.editSizePurchaseOrderId = ''
            } else {
                this.$message({
                    type: 'error',
                    message: '保存失败'
                })
            }
        },
        async deleteUnsubmitPurchaseOrder(row) {
            this.$confirm('确定删除此订单吗？', '提示', {
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                type: 'warning'
            })
                .then(async () => {
                    const response = await axios.delete(
                        `${this.$apiBaseUrl}/logistics/deleteunsubmitpurchaseorder`,
                        {
                            params: {
                                purchaseOrderId: row.purchaseOrderId
                            }
                        }
                    )
                    if (response.status === 200) {
                        this.$message({
                            type: 'success',
                            message: '删除成功'
                        })
                        this.getUnsubmitPurchaseOrder()
                    } else {
                        this.$message({
                            type: 'error',
                            message: '删除失败'
                        })
                    }
                })
                .catch(() => {
                    this.$message({
                        type: 'info',
                        message: '已取消删除'
                    })
                })
        },
        async downloadZip(row) {
            window.open(
                `${this.$apiBaseUrl}/logistics/downloadassetzip?purchaseOrderRId=${row.purchaseOrderRId}`
            )
        }
    }
}
</script>
