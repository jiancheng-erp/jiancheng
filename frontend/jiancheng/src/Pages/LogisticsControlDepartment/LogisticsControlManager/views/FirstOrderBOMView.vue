<template>
    <el-container direction="vertical">
        <el-header height="">
            <AllHeader></AllHeader>
        </el-header>
        <el-main height="">
            <el-row :gutter="20" style="text-align: center">
                <el-col :span="24" :offset="0" style="font-size: xx-large; text-align: center"
                    >一次采购订单创建</el-col
                >
            </el-row>
            <el-row :gutter="20">
                <el-col :span="24" :offset="0">
                    <span style="font-weight: bold; font-size: larger">订单信息：</span>
                    <Arrow :status="orderData.status" :key="updateArrowKey"></Arrow>
                    <el-descriptions title="" :column="2" border>
                        <el-descriptions-item label="订单编号" align="center">{{
                            orderData.orderId
                        }}</el-descriptions-item>
                        <el-descriptions-item label="订单创建时间" align="center">{{
                            orderData.createTime
                        }}</el-descriptions-item>
                        <el-descriptions-item label="客户名称" align="center">{{
                            orderData.customerName
                        }}</el-descriptions-item>
                        <el-descriptions-item label="订单预计截止日期" align="center">{{
                            orderData.deadlineTime
                        }}</el-descriptions-item>
                    </el-descriptions>
                </el-col>
            </el-row>
            <el-row :gutter="20" style="margin-top: 10px">
                <el-col :span="4" :offset="0">
                    <div style="display: flex; align-items: center; white-space: nowrap">
                        工厂型号搜索：<el-input
                            v-model="inheritIdSearch"
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
                    <el-table :data="testTableFilterData" border style="height: 400px">
                        <el-table-column type="expand">
                            <template #default="parentScope">
                                <el-table :data="parentScope.row.typeInfos" border>
                                    <el-table-column prop="color" label="颜色"></el-table-column>
                                    <el-table-column label="鞋图">
                                        <template #default="scope">
                                            <el-image
                                                style="width: 150px; height: 100px"
                                                :src="scope.row.image"
                                                fit="contain"
                                            />
                                        </template>
                                    </el-table-column>
                                    <el-table-column
                                        prop="firstBomStatus"
                                        label="一次BOM表"
                                    ></el-table-column>
                                    <el-table-column
                                        prop="firstPurchaseOrderStatus"
                                        label="一次采购订单"
                                    ></el-table-column>
                                    <el-table-column
                                        prop="secondBomStatus"
                                        label="二次BOM表"
                                    ></el-table-column>
                                    <el-table-column
                                        prop="secondPurchaseOrderStatus"
                                        label="二次采购订单"
                                    ></el-table-column>
                                    <el-table-column label="操作">
                                        <template #default="scope">
                                            <el-button
                                                type="primary"
                                                @click="openFirstBOMPreviewDialog(scope.row)"
                                                >查看采购BOM表
                                            </el-button>
                                        </template>
                                    </el-table-column>
                                </el-table>
                            </template>
                        </el-table-column>
                        <el-table-column
                            prop="inheritId"
                            label="工厂型号"
                            align="center"
                            width="100"
                        ></el-table-column>
                        <el-table-column
                            prop="customerId"
                            label="客户型号"
                            align="center"
                        ></el-table-column>
                        <el-table-column
                            prop="designer"
                            label="设计员"
                            align="center"
                        ></el-table-column>
                        <el-table-column
                            prop="editter"
                            label="调版员"
                            align="center"
                        ></el-table-column>
                        <el-table-column
                            prop="totalBomId"
                            label="总BOM编号"
                            align="center"
                        ></el-table-column>
                        <el-table-column
                            prop="purchaseOrderId"
                            label="采购订单编号"
                            align="center"
                        ></el-table-column>
                        <el-table-column
                            prop="currentStatus"
                            label="当前采购订单状态"
                            align="center"
                        ></el-table-column>
                        <el-table-column
                            prop="status"
                            label="状态"
                            align="center"
                        ></el-table-column>
                        <el-table-column label="操作" align="center" width="500">
                            <template #default="scope">
                                <div v-if="scope.row.currentStatus === '已保存'">
                                    <el-button type="primary" @click="openEditDialog(scope.row)"
                                        >编辑</el-button
                                    >
                                    <el-button type="success" @click="openPreviewDialog(scope.row)"
                                        >预览</el-button
                                    >
                                    <el-button type="warning" @click="openSubmitDialog(scope.row)"
                                        >提交</el-button
                                    >
                                </div>
                                <div v-else-if="scope.row.currentStatus === '已提交'">
                                    <el-button type="primary" @click="openPreviewDialog(scope.row)"
                                        >预览</el-button
                                    >
                                    <el-button
                                        type="success"
                                        @click="downloadPurchaseOrderZip(scope.row)"
                                        >下载采购订单压缩包</el-button
                                    >
                                    <el-button
                                        type="success"
                                        @click="downloadMaterialStasticExcel(scope.row)"
                                        >下载材料统计单</el-button
                                    >
                                </div>
                                <div
                                    v-else-if="
                                        scope.row.currentStatus === '未填写' &&
                                        scope.row.status.includes('一次采购订单创建')
                                    "
                                >
                                    <el-button type="primary" @click="handleGenerate(scope.row)"
                                        >填写</el-button
                                    >
                                </div>
                            </template>
                        </el-table-column>
                    </el-table></el-col
                >
            </el-row>
            <el-dialog
                :title="`一次采购订单创建 ${newPurchaseOrderId}`"
                v-model="createVis"
                width="100%"
                @close="handleGenerateClose"
            >
                <el-descriptions title="订单信息" :column="2">
                    <el-descriptions-item label="订单编号" align="center">{{
                        orderData.orderId
                    }}</el-descriptions-item>
                    <el-descriptions-item label="订单创建时间" align="center">{{
                        orderData.createTime
                    }}</el-descriptions-item>
                    <el-descriptions-item label="客户名称" align="center">{{
                        orderData.customerName
                    }}</el-descriptions-item>
                    <el-descriptions-item label="订单预计截止日期" align="center">{{
                        orderData.deadlineTime
                    }}</el-descriptions-item>
                    <el-descriptions-item label="投产指令单" align="center">
                        <el-button
                            type="primary"
                            size="default"
                            @click="downloadProductionOrderList"
                        >
                            查看投产指令单
                        </el-button>
                    </el-descriptions-item>
                    <!-- <el-descriptions-item label="生产订单" align="center">
                        <el-button type="primary" size="default" @click="downloadProductionOrder">查看生产订单
                        </el-button>
                    </el-descriptions-item> -->
                </el-descriptions>

                <div style="height: 600px; overflow-y: scroll; overflow-x: hidden">
                    <el-row gutter="20">
                        <el-col :span="24">
                            <el-button type="text" @click="toggleOrderInfo">
                                {{ orderInfoVisible ? '折叠' : '展开' }} 订单鞋型数量
                            </el-button>
                        </el-col>
                    </el-row>
                    <el-row style="margin-top: 10px">
                        <el-col :span="24">
                            <transition name="fade">
                                <div v-if="orderInfoVisible">
                                    <el-table
                                        :data="orderProduceInfo"
                                        border
                                        style="width: 100%"
                                        :span-method="batchInfoSpanMethod"
                                    >
                                        <el-table-column prop="colorName" label="颜色" />
                                        <el-table-column prop="totalAmount" label="合计" />
                                        <el-table-column
                                            v-for="column in filteredColumns(orderProduceInfo)"
                                            :key="column.prop"
                                            :prop="column.prop"
                                            :label="column.label"
                                        ></el-table-column>
                                    </el-table>
                                </div>
                            </transition>
                        </el-col>
                    </el-row>
                    <el-row style="margin-top: 10px">
                        采购信息
                        <el-table :data="bomTestData" border>
                            <el-table-column
                                prop="materialProductionInstructionType"
                                label="材料开发部标注类型"
                                :formatter="translateProductionInstructionType"
                            ></el-table-column>
                            <el-table-column prop="materialType" label="材料类型"></el-table-column>
                            <el-table-column prop="materialName" label="材料名称"></el-table-column>
                            <el-table-column prop="materialModel" label="材料型号" />
                            <el-table-column
                                prop="materialSpecification"
                                label="材料规格"
                            ></el-table-column>
                            <el-table-column prop="color" label="颜色"></el-table-column>
                            <el-table-column prop="unit" label="单位"></el-table-column>
                            <el-table-column prop="supplierName" label="厂家名称"></el-table-column>
                            <el-table-column prop="unitUsage" label="单位用量"></el-table-column>
                            <el-table-column
                                prop="approvalUsage"
                                label="核定用量"
                            ></el-table-column>
                            <el-table-column prop="purchaseAmount" label="采购数量" width="150">
                                <template #default="scope">
                                    <el-input-number
                                        v-if="scope.row.materialCategory == 0"
                                        v-model="scope.row.purchaseAmount"
                                        :min="0"
                                        size="small"
                                    />
                                    <el-button
                                        v-if="scope.row.materialCategory == 1"
                                        type="primary"
                                        size="default"
                                        @click="openSizeDialog(scope.row, scope.$index)"
                                        >尺码用量填写</el-button
                                    >
                                </template>
                            </el-table-column>
                            <el-table-column prop="remark" label="开发部备注"></el-table-column>
                        </el-table>
                    </el-row>
                </div>
                <template #footer>
                    <span>
                        <el-button @click="handleGenerateClose">取消</el-button>
                        <el-button
                            v-if="createEditSymbol == 0"
                            type="primary"
                            @click="confirmPurchaseSave"
                            >保存</el-button
                        >
                        <el-button
                            v-else-if="createEditSymbol == 1"
                            type="primary"
                            @click="confirmPurchaseEdit"
                            >编辑保存</el-button
                        >
                    </span>
                </template>
            </el-dialog>
            <el-dialog
                :title="`预览BOM表 ${previewFirstBomId}`"
                v-model="isPreviewFirstDialogVisible"
                width="90%"
                :key="updateKey"
            >
                <el-descriptions title="订单信息" :column="2" border>
                    <el-descriptions-item label="订单编号" align="center">{{
                        orderData.orderId
                    }}</el-descriptions-item>
                    <el-descriptions-item label="订单创建时间" align="center">{{
                        orderData.createTime
                    }}</el-descriptions-item>
                    <el-descriptions-item label="客户名称" align="center">{{
                        orderData.customerName
                    }}</el-descriptions-item>
                    <el-descriptions-item label="订单预计截止日期" align="center">{{
                        orderData.deadlineTime
                    }}</el-descriptions-item>
                    <!-- <el-descriptions-item label="生产订单" align="center"><el-button type="primary" size="default"
                            @click="downloadProductionOrder">查看生产订单</el-button>
                    </el-descriptions-item> -->
                </el-descriptions>
                <div style="height: 600px; overflow-y: scroll; overflow-x: hidden">
                    <el-row :gutter="20" style="margin-bottom: 20px">
                        <el-col :span="24">
                            <el-table :data="firstBomPreviewData" border style="width: 100%">
                                <el-table-column prop="materialType" label="材料类型" />
                                <el-table-column prop="materialDetailType" label="材料二级类型" />
                                <el-table-column prop="materialName" label="材料名称" />
                                <el-table-column prop="materialModel" label="材料型号" />
                                <el-table-column prop="materialSpecification" label="材料规格" />
                                <el-table-column prop="color" label="颜色"> </el-table-column>
                                <el-table-column prop="unit" label="单位" />
                                <el-table-column prop="supplierName" label="厂家名称" />
                                <el-table-column prop="unitUsage" label="单位用量">
                                    <template #default="scope">
                                        <el-button
                                            v-if="scope.row.materialCategory == 1"
                                            type="primary"
                                            size="default"
                                            @click="openSizeDialog(scope.row, scope.$index)"
                                            >尺码用量查看</el-button
                                        >
                                    </template>
                                </el-table-column>
                                <el-table-column prop="approvalUsage" label="核定用量">
                                </el-table-column>
                                <el-table-column prop="remark" label="备注" />
                                <el-table-column prop="isInboundSperate" label="入库单位是否不同"></el-table-column>
                            <el-table-column prop="materialInboundName" label="入库材料名称">

                            </el-table-column>
                            <el-table-column prop="materialInboundUnit" label="入库单位"></el-table-column>
                            <el-table-column prop="remark" label="开发部备注"></el-table-column>
                            </el-table>
                        </el-col>
                    </el-row>
                </div>
                <template #footer>
                    <span>
                        <el-button type="primary" @click="isPreviewFirstDialogVisible = false"
                            >确认</el-button
                        >
                    </span>
                </template>
            </el-dialog>

            <el-dialog
                :title="`一次采购订单 ${previewBomId} 预览`"
                v-model="isPreviewDialogVisible"
                width="90%"
                :close-on-click-modal="false"
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
                                    <span
                                        >交货周期: {{ purchaseDivideOrder.shipmentDeadline }}
                                    </span>
                                </el-col>
                            </el-row>
                            <div
                                v-if="
                                    factoryFieldJudge(purchaseDivideOrder.purchaseDivideOrderType)
                                "
                            >
                                <el-table
                                    :data="purchaseDivideOrder.assetsItems"
                                    border
                                    style="width: 100%"
                                >
                                    <el-table-column type="index" label="编号" />
                                    <el-table-column
                                        prop="materialType"
                                        label="材料类型"
                                    ></el-table-column>
                                    <el-table-column prop="materialName" label="材料名称" />
                                    <el-table-column prop="materialModel" label="材料型号" />
                                    <el-table-column
                                        prop="materialSpecification"
                                        label="材料规格"
                                    ></el-table-column>
                                    <el-table-column prop="unit" label="单位" />

                                    <el-table-column prop="purchaseAmount" label="采购数量" />
                                    <el-table-column :label="`分码数量 (${currentShoeSizeType})`">
                                        <el-table-column
                                            v-for="column in filteredColumns(
                                                purchaseDivideOrder.assetsItems
                                            )"
                                            :key="column.prop"
                                            :prop="column.prop"
                                            :label="column.label"
                                        ></el-table-column>
                                    </el-table-column>
                                </el-table>
                            </div>
                            <div v-else>
                                <el-table
                                    :data="purchaseDivideOrder.assetsItems"
                                    border
                                    style="width: 100%"
                                >
                                    <el-table-column type="index" label="编号" />
                                    <el-table-column
                                        prop="materialType"
                                        label="材料类型"
                                    ></el-table-column>
                                    <el-table-column prop="materialName" label="材料名称" />
                                    <el-table-column prop="materialModel" label="材料型号" />
                                    <el-table-column
                                        prop="materialSpecification"
                                        label="材料规格"
                                    ></el-table-column>
                                    <el-table-column prop="color" label="颜色" />
                                    <el-table-column prop="unit" label="单位" />
                                    <el-table-column prop="purchaseAmount" label="采购数量" />
                                    <el-table-column prop="remark" label="开发部备注" />
                                </el-table>
                            </div>
                        </el-col>
                    </el-row>
                </div>
                <template #footer>
                    <span>
                        <el-button type="primary" @click="isPreviewDialogVisible = false"
                            >确认</el-button
                        >
                    </span>
                </template>
            </el-dialog>

            <!-- Main content -->
        </el-main>
    </el-container>
    <el-dialog
        title="尺码数量填写"
        v-model="isSizeDialogVisible"
        width="60%"
        :close-on-click-modal="false"
    >
        <span>{{ `尺码名称: ${currentShoeSizeType}` }}</span>
        <el-table :data="sizeData" border stripe>
            <el-table-column prop="size" label="尺码"></el-table-column>
            <el-table-column prop="approvalAmount" label="核定用量"> </el-table-column>
            <el-table-column prop="purchaseAmount" label="采购数量">
                <template #default="scope">
                    <el-input-number v-model="scope.row.purchaseAmount" :min="0" size="small" />
                </template>
            </el-table-column>
        </el-table>

        <template #footer>
            <span>
                <el-button type="primary" @click="confirmSizeAmount()">确认</el-button>
            </span>
        </template>
    </el-dialog>
    <el-dialog
        title="采购订单创建页面"
        v-model="purchaseOrderCreateVis"
        width="80%"
        :close-on-click-modal="false"
    >
        <span v-if="activeTab === ''"> 无需购买材料，推进流程即可。 </span>
        <el-tabs v-if="activeTab !== ''" v-model="activeTab" type="card" tab-position="top">
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
                                clearable
                            ></el-input>
                        </span>
                    </el-col>
                </el-row>
                <el-row :gutter="20" style="margin-top: 20px">
                    <el-col :span="24" :offset="0">
                        <div v-if="factoryFieldJudge(item.purchaseDivideOrderType)">
                            <el-table
                                :data="item.assetsItems"
                                border
                                style="width: 100%"
                                height="500"
                            >
                                <el-table-column type="index" label="编号" />
                                <el-table-column
                                    prop="materialType"
                                    label="材料类型"
                                ></el-table-column>
                                <el-table-column prop="materialName" label="材料名称" />
                                <el-table-column prop="materialModel" label="材料型号" />
                                <el-table-column
                                    prop="materialSpecification"
                                    label="材料规格"
                                ></el-table-column>
                                <el-table-column prop="unit" label="单位" />

                                <el-table-column prop="amount" label="采购数量" />
                                <el-table-column :label="`分码数量(${currentShoeSizeType})`">
                                    <el-table-column
                                        v-for="column in filteredColumns(item.assetsItems)"
                                        :key="column.prop"
                                        :prop="column.prop"
                                        :label="column.label"
                                    ></el-table-column>
                                </el-table-column>
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
                                <el-table-column prop="materialModel" label="材料型号" />
                                <el-table-column
                                    prop="materialSpecification"
                                    label="材料规格"
                                ></el-table-column>
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
</template>

<script>
import AllHeader from '@/components/AllHeader.vue'
import Arrow from '@/components/OrderArrowView.vue'
import axios from 'axios'
import { getShoeSizesName } from '@/Pages/utils/getShoeSizesName'
import { shoeBatchInfoTableSpanMethod } from '@/Pages/ProductionManagementDepartment/utils'
export default {
    props: ['orderId'],
    components: {
        AllHeader,
        Arrow
    },
    data() {
        return {
            batchInfoSpanMethod: null,
            currentSizeIndex: 0,
            purchaseOrderCreateVis: false,
            createEditSymbol: 0,
            newPurchaseOrderId: '',
            activeTab: '',
            isPurchaseOrderVis: false,
            createVis: false,
            isSizeDialogVisible: false,
            sizeData: [],
            tabPlaneData: [],
            orderData: {},
            testTableData: [],
            testTableFilterData: [],
            orderProduceInfo: [],
            bomTestData: [],
            firstBomPreviewData: [],
            previewFirstBomId: '',
            isPreviewFirstDialogVisible: false,
            originalBomTestData: [],
            factoryOptions: [
                { materialName: '黑色超软镜面PU', factoryName: '一一鞋材' },
                { materialName: '黑色超软镜面PU', factoryName: '深源皮革' },
                { materialName: '黑色超软镜面PU', factoryName: '嘉泰皮革' }
                // Add more options here
            ],
            currentBOMId: '',
            departmentOptions: [],
            colorOptions: [],
            purchaseTestData: [],
            isPreviewDialogVisible: false,
            selectedFile: null,
            inheritIdSearch: '',
            currentShoeSizeType: '',
            getShoeSizesName,
            shoeSizeColumns: [],
            orderInfoVisible: true
        }
    },
    async mounted() {
        this.shoeSizeColumns = await this.getShoeSizesName(this.$props.orderId)
        this.currentShoeSizeType = this.shoeSizeColumns[0].type
        this.getAllColorOptions()
        this.getAllDepartmentOptions()
        this.$setAxiosToken()
        this.getOrderInfo()
        this.getAllShoeListInfo()
    },
    computed: {
        processedBomTestData() {
            const customOrder = ['S', 'I', 'A', 'O', 'M', 'H']
            const typeMap = {
                S: '面料',
                I: '里料',
                A: '辅料',
                M: '中底',
                O: '大底',
                H: '烫底'
            }

            return this.bomTestData
                .slice()
                .sort((a, b) => {
                    const orderA = customOrder.indexOf(a.productionInstructionType)
                    const orderB = customOrder.indexOf(b.productionInstructionType)
                    return orderA - orderB
                })
                .map((item) => ({
                    ...item,
                    materialProductionInstructionType:
                        typeMap[item.productionInstructionType] || item.productionInstructionType
                }))
        }
    },
    methods: {
        translateProductionInstructionType(row) {
            const typeMap = {
                S: '面料',
                I: '里料',
                A: '辅料',
                M: '中底',
                O: '大底',
                H: '烫底'
            }
            console.log(typeMap[row.materialProductionInstructionType])
            return typeMap[row.materialProductionInstructionType] || row.materialProductionInstructionType
        },
        toggleOrderInfo() {
            this.orderInfoVisible = !this.orderInfoVisible
        },
        filteredColumns(array) {
            return this.shoeSizeColumns.filter((column) =>
                array.some(
                    (row) =>
                        row[column.prop] !== undefined &&
                        row[column.prop] !== null &&
                        row[column.prop] !== 0
                )
            )
        },
        async getAllDepartmentOptions() {
            const response = await this.$axios.get(`${this.$apiBaseUrl}/general/getalldepartments`)
            this.departmentOptions = response.data
        },
        async getAllColorOptions() {
            const response = await this.$axios.get(`${this.$apiBaseUrl}/general/allcolors`)
            this.colorOptions = response.data
        },
        async getNewPurchaseOrderId() {
            const response = await axios.get(
                `${this.$apiBaseUrl}/firstpurchase/getnewpurchaseorderid`
            )
            this.newPurchaseOrderId = response.data.purchaseOrderId
        },
        async getFirstBomPreviewData(row) {
            const response = await axios.get(
                `${this.$apiBaseUrl}/usagecalculation/getshoebomitems`,
                {
                    params: {
                        bomrid: row.firstBomId
                    }
                }
            )
            this.firstBomPreviewData = response.data
        },
        async getOrderInfo() {
            const response = await axios.get(
                `${this.$apiBaseUrl}/order/getorderInfo?orderid=${this.orderId}`
            )
            this.orderData = response.data
            console.log(this.orderData)
            this.updateArrowKey += 1
        },
        async getAllShoeListInfo() {
            const response = await axios.get(
                `${this.$apiBaseUrl}/firstpurchase/getordershoelist?orderid=${this.orderId}`
            )
            this.testTableData = response.data
            this.tableWholeFilter()
        },
        async getOrderShoeBatchInfo(orderShoeId) {
            const response = await axios.get(
                `${this.$apiBaseUrl}/production/getordershoebatchinfo`,
                {
                    params: {
                        orderShoeId: orderShoeId
                    }
                }
            )
            this.orderProduceInfo = response.data
            this.batchInfoSpanMethod = shoeBatchInfoTableSpanMethod(this.orderProduceInfo)
        },
        async getBOMDetails(row) {
            const response = await this.$axios.get(
                `${this.$apiBaseUrl}/firstpurchase/getshoebomitems`,
                {
                    params: {
                        bomrid: row.totalBomId,
                        orderid: this.$props.orderId
                    }
                }
            )
            console.log(response.data)
            this.bomPreviewData = response.data
            this.bomTestData = response.data
        },
        tableWholeFilter() {
            if (!this.inheritIdSearch) {
                this.testTableFilterData = this.testTableData
                return
            }

            this.testTableFilterData = this.testTableData.filter((task) => {
                const inheritMatch = task.inheritId.includes(this.inheritIdSearch)
                return inheritMatch
            })
        },
        factoryFieldJudge(field) {
            if (field === 'N') {
                return false
            }
            return true
        },
        openSizeDialog(row, index) {
            this.sizeData = row.sizeInfo
            this.isSizeDialogVisible = true
            this.currentSizeIndex = index
        },
        confirmSizeAmount() {
            this.bomTestData[this.currentSizeIndex].sizeInfo = this.sizeData
            const totalApprovalAmount = this.sizeData.reduce(
                (total, item) => total + item.purchaseAmount,
                0
            )
            this.bomTestData[this.currentSizeIndex].purchaseAmount = totalApprovalAmount
            this.isSizeDialogVisible = false
        },
        async handleGenerate(row) {
            await this.getNewPurchaseOrderId()
            await this.getOrderShoeBatchInfo(row.orderShoeId)
            await this.getBOMDetails(row)
            this.currentBOMId = row.totalBomId
            this.currentPurchaseShoeId = row.inheritId
            if (this.bomTestData && Array.isArray(this.bomTestData)) {
                this.bomTestData.forEach((item) => {
                    // Set the item-level purchaseAmount to match approvalAmount
                    item.purchaseAmount = parseFloat(item.approvalUsage) || 0

                    // Update sizeInfo purchaseAmount to match approvalAmount
                    if (item.sizeInfo && Array.isArray(item.sizeInfo)) {
                        item.sizeInfo.forEach((sizeRow) => {
                            sizeRow.purchaseAmount = parseFloat(sizeRow.approvalAmount) || 0
                        })
                    }
                })
            }
            this.createEditSymbol = 0
            this.createVis = true
        },
        handleGenerateClose() {
            this.createVis = false
        },
        getFilteredFactoryOptions(materialName) {
            const filteredOptions = this.factoryOptions.filter(
                (option) => option.materialName === materialName
            )
            return [{ factoryName: '询价' }, ...filteredOptions]
        },
        async openPreviewDialog(row) {
            this.previewBomId = row.purchaseOrderId
            try {
                const response = await axios.get(
                    `${this.$apiBaseUrl}/firstpurchase/getpurchasedivideorders`,
                    {
                        params: {
                            purchaseOrderId: row.purchaseOrderId
                        }
                    }
                )
                this.purchaseTestData = response.data
                console.log(this.purchaseTestData)
            } catch (error) {
                console.log(error)
            }
            this.isPreviewDialogVisible = true
        },
        async openFirstBOMPreviewDialog(row) {
            this.previewFirstBomId = row.firstBomId
            await this.getFirstBomPreviewData(row)
            this.isPreviewFirstDialogVisible = true
        },
        async openEditDialog(row) {
            const loadingInstance = this.$loading({
                lock: true,
                text: '等待中，请稍后...',
                background: 'rgba(0, 0, 0, 0.7)'
            })
            this.currentBOMId = row.totalBomId
            await this.getOrderShoeBatchInfo(row.orderShoeId)
            await this.getBOMDetails(row)
            loadingInstance.close()

            this.createVis = true
            this.currentPurchaseShoeId = row.inheritId
            this.createEditSymbol = 1
        },
        async openSubmitDialog(row) {
            const response = await axios.get(
                `${this.$apiBaseUrl}/firstpurchase/getpurchasedivideorders`,
                {
                    params: {
                        purchaseOrderId: row.purchaseOrderId
                    }
                }
            )
            this.currentSubmitPurchaseOrderId = row.purchaseOrderId
            this.tabPlaneData = response.data
            console.log(this.tabPlaneData)
            if (this.tabPlaneData.length > 0) {
                this.activeTab = this.tabPlaneData[0].purchaseDivideOrderId
            }
            this.purchaseOrderCreateVis = true
        },
        closePreviewDialog() {
            this.isPreviewDialogVisible = false
        },
        async saveEditUsagePurchase() {
            console.log(this.bomTestData)
            // Validate that all existing rows have non-empty fields
            for (const row of this.bomTestData) {
                if (!row.purchaseAmount) {
                    this.$message({
                        type: 'warning',
                        message: '请填写所有字段'
                    })
                    return
                }
            }
            const loadingInstance = this.$loading({
                lock: true,
                text: '等待中，请稍后...',
                background: 'rgba(0, 0, 0, 0.7)'
            })
            console.log(this.bomTestData)
            const response = await this.$axios.post(
                `${this.$apiBaseUrl}/firstpurchase/editpurchaseitems`,
                {
                    purchaseItems: this.bomTestData
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
            this.createVis = false
            this.getAllShoeListInfo()
        },
        async submitBOMUsage(row) {
            const response = await this.$axios.get(
                `${this.$apiBaseUrl}/firstpurchase/getpurchasedivideorders`,
                {
                    params: {
                        purchaseOrderId: row.purchaseOrderId
                    }
                }
            )
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
            this.purchaseOrderCreateVis = true
        },
        async saveUsagePurchase() {
            // Validate that all existing rows have non-empty fields
            for (const row of this.bomTestData) {
                if (!row.purchaseAmount) {
                    this.$message({
                        type: 'warning',
                        message: '请填写所有字段'
                    })
                    return
                }
            }
            const loadingInstance = this.$loading({
                lock: true,
                text: '等待中，请稍后...',
                background: 'rgba(0, 0, 0, 0.7)'
            })
            const response = await this.$axios.post(
                `${this.$apiBaseUrl}/firstpurchase/savepurchase`,
                {
                    purchaseRid: this.newPurchaseOrderId,
                    purchaseItems: this.bomTestData,
                    bomRid: this.currentBOMId
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
            this.createVis = false
            this.getAllShoeListInfo()
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
        async submitPurchaseDivideOrder() {
            const loadingInstance = this.$loading({
                lock: true,
                text: '等待中，请稍后...',
                background: 'rgba(0, 0, 0, 0.7)'
            })
            const response = await this.$axios.post(
                `${this.$apiBaseUrl}/firstpurchase/submitpurchasedivideorders`,
                {
                    purchaseOrderId: this.currentSubmitPurchaseOrderId
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
            this.getAllShoeListInfo()
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
                    purchaseOrderId: this.currentSubmitPurchaseOrderId,
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
        confirmPurchaseSave() {
            this.$confirm('确定保存此采购总订单吗？', '提示', {
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                type: 'warning'
            })
                .then(() => {
                    this.saveUsagePurchase()
                })
                .catch(() => {
                    this.$message({
                        type: 'info',
                        message: '已取消保存'
                    })
                })
        },
        confirmPurchaseEdit() {
            this.$confirm('确定保存此采购总订单吗？', '提示', {
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                type: 'warning'
            })
                .then(() => {
                    this.saveEditUsagePurchase()
                })
                .catch(() => {
                    this.$message({
                        type: 'info',
                        message: '已取消保存'
                    })
                })
        },
        downloadProductionOrderList() {
            window.open(
                `${this.$apiBaseUrl}/devproductionorder/download?ordershoerid=${this.currentPurchaseShoeId}&orderid=${this.orderData.orderId}`
            )
        },
        downloadProductionOrder() {
            window.open(
                `${this.$apiBaseUrl}/orderimport/downloadorderdoc?orderrid=${this.orderData.orderId}&filetype=0`
            )
        },
        downloadPurchaseOrderZip(row) {
            window.open(
                `${this.$apiBaseUrl}/firstpurchase/downloadpurchaseorderzip?orderrid=${this.orderData.orderId}&ordershoerid=${row.inheritId}`
            )
        },
        downloadMaterialStasticExcel(row) {
            window.open(
                `${this.$apiBaseUrl}/firstpurchase/downloadmaterialstatistics?orderrid=${this.orderData.orderId}&ordershoerid=${row.inheritId}`
            )
        }
    }
}
</script>

<style scoped>
/* Add your styles here */
</style>
