<template>
    <el-container direction="vertical">
        <el-header height="">
            <AllHeader></AllHeader>
        </el-header>
        <el-main height="">
            <el-row :gutter="20" style="text-align: center">
                <el-col :span="24" :offset="0" style="font-size: xx-large; text-align: center">二次采购订单创建</el-col>
            </el-row>
            <el-row :gutter="20">
                <el-col :span="24" :offset="0">
                    <span style="font-weight: bold; font-size: larger">订单信息：</span>
                    <Arrow :status="orderData.status"></Arrow>
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
                        <el-descriptions-item label="楦头采购状态" align="center">{{
                            orderData.lastStatus === '0' ? '未采购' : orderData.lastStatus === '1' ? '已保存' : '已采购'
                            }}
                            <el-button v-if="orderData.lastStatus === ('0' || '1')" type="primary" size="default"
                                @click="openLastPurchasePage(orderData.orderDBId)">采购</el-button>
                            <el-button v-else type="primary" size="default"
                                @click="downloadLastZip(orderData.orderDBId)">下载楦头采购订单</el-button>
                        </el-descriptions-item>
                        <el-descriptions-item label="刀模采购状态 " align="center">{{
                            orderData.cuttingModelStatus === '0' ? '未采购' : orderData.cuttingModelStatus === '1' ? '已保存'
                                : '已采购'
                            }}
                            <el-button v-if="orderData.cuttingModelStatus === ('0' || '1')" type="primary"
                                size="default" @click="openCutModelPurchasePage(orderData.orderDBId)">采购</el-button>
                            <el-button v-else type="primary" size="default" @click="">下载刀模采购订单</el-button>
                        </el-descriptions-item>
                        <el-descriptions-item label="包材采购状态" align="center">{{
                            orderData.packagingStatus === '0' ? '未采购' : orderData.packagingStatus === '1' ? '已保存' :
                                '已采购'
                            }}
                            <el-button v-if="orderData.packagingStatus === ('0' || '1')" type="primary" size="default"
                                @click="openPackagePurchasePage(orderData.orderDBId)">采购</el-button>
                            <el-button v-else type="primary" size="default"
                                @click="downloadPackageZip(orderData.orderDBId)">下载包材采购订单</el-button>
                        </el-descriptions-item>
                        <el-descriptions-item label="尺码数量对照表" align="center">
                            <el-button type="primary" size="default" @click="openSizeComparisonDialog">查看</el-button>
                        </el-descriptions-item>
                        <el-descriptions-item label="退回订单" align="center">
                            <el-button type="danger" size="default" @click="openReturnOrderDialog">退回流程</el-button>
                        </el-descriptions-item>
                    </el-descriptions>
                </el-col>
            </el-row>
            <el-row :gutter="20" style="margin-top: 10px">
                <el-col :span="4" :offset="0">
                    <div style="display: flex; align-items: center; white-space: nowrap">
                        工厂型号搜索：<el-input v-model="inheritIdSearch" placeholder="" size="default" :suffix-icon="Search"
                            clearable @input="tableWholeFilter"></el-input>
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
                                            <el-image style="width: 150px; height: 100px" :src="scope.row.image"
                                                fit="contain" />
                                        </template>
                                    </el-table-column>
                                    <el-table-column prop="firstBomStatus" label="一次BOM表"></el-table-column>
                                    <el-table-column prop="firstPurchaseOrderStatus" label="一次采购订单"></el-table-column>
                                    <el-table-column prop="secondBomStatus" label="二次BOM表"></el-table-column>
                                    <el-table-column prop="secondPurchaseOrderStatus" label="二次采购订单"></el-table-column>
                                    <el-table-column label="操作">
                                        <template #default="scope">
                                            <el-button type="primary"
                                                @click="openSecondBOMPreviewDialog(scope.row)">查看采购BOM表
                                            </el-button>
                                        </template>
                                    </el-table-column>
                                </el-table>
                            </template>
                        </el-table-column>
                        <el-table-column prop="inheritId" label="工厂型号" align="center" width="100"></el-table-column>
                        <el-table-column prop="customerId" label="客户型号" align="center"></el-table-column>
                        <el-table-column prop="designer" label="设计员" align="center"></el-table-column>
                        <el-table-column prop="editter" label="调版员" align="center"></el-table-column>
                        <el-table-column prop="totalBomId" label="总BOM编号" align="center"></el-table-column>
                        <el-table-column prop="purchaseOrderId" label="采购订单编号" align="center"></el-table-column>
                        <el-table-column prop="currentStatus" label="当前采购订单状态" align="center"></el-table-column>
                        <el-table-column prop="status" label="状态" align="center"></el-table-column>
                        <el-table-column label="操作" align="center" width="500">
                            <template #default="scope">
                                <div v-if="role == 1">
                                    <el-button type="primary" @click="openEditDialog(scope.row)">编辑</el-button>
                                </div>
                                <div v-else>
                                    <div v-if="scope.row.currentStatus === '已保存'">
                                        <el-button type="primary" @click="openEditDialog(scope.row)">编辑</el-button>
                                        <el-button type="success" @click="openPreviewDialog(scope.row)">预览</el-button>
                                        <el-button type="warning" @click="openSubmitDialog(scope.row)">提交</el-button>
                                    </div>
                                    <div v-else-if="scope.row.currentStatus === '已提交'">
                                        <el-button type="primary" @click="openPreviewDialog(scope.row)">预览</el-button>
                                        <el-button type="success"
                                            @click="downloadPurchaseOrderZip(scope.row)">下载采购订单压缩包</el-button>
                                        <el-button type="success"
                                            @click="downloadMaterialStasticExcel(scope.row)">下载材料统计单</el-button>
                                    </div>
                                    <div v-else-if="
                                        scope.row.currentStatus === '未填写' &&
                                        scope.row.status.includes('总仓采购订单创建')
                                    ">
                                        <el-button type="primary" @click="handleGenerate(scope.row)">填写</el-button>
                                    </div>
                                </div>
                            </template>
                        </el-table-column>
                    </el-table></el-col>
            </el-row>
            <el-dialog :title="`二次采购订单创建 ${newPurchaseOrderId}`" v-model="createVis" width="100%" fullscreen
                @close="handleGenerateClose">
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
                    <el-descriptions-item label="投产指令单" align="center">
                        <el-button type="primary" size="default" @click="downloadProductionOrderList">
                            查看投产指令单
                        </el-button>
                    </el-descriptions-item>
                    <!-- <el-descriptions-item label="生产订单" align="center">
                        <el-button type="primary" size="default" @click="downloadProductionOrder">查看生产订单
                        </el-button>
                    </el-descriptions-item> -->
                </el-descriptions>

                <el-row :gutter="20">
                    <el-col :span="24">
                        <el-button type="primary" link @click="toggleOrderInfo">
                            {{ orderInfoVisible ? '折叠' : '展开' }} 订单鞋型数量
                        </el-button>
                    </el-col>
                </el-row>
                <el-row style="margin-top: 10px">
                    <el-col :span="24">
                        <transition name="fade">
                            <div v-if="orderInfoVisible">
                                <el-table :data="orderProduceInfo" border style="width: 100%"
                                    :span-method="batchInfoSpanMethod">
                                    <el-table-column prop="colorName" label="颜色" />
                                    <el-table-column prop="totalAmount" label="合计" />
                                    <el-table-column v-for="column in filteredColumns(orderProduceInfo)"
                                        :key="column.prop" :prop="column.prop" :label="column.label"></el-table-column>
                                </el-table>
                            </div>
                        </transition>
                    </el-col>
                </el-row>
                <el-row :gutter="20">
                    <el-col :span="24">
                        <el-button-group v-if="!isEditEnabled">
                            <el-button type="primary" @click="changeEditMode">替换材料</el-button>
                        </el-button-group>
                        <el-button-group v-else>
                            <el-button type="warning" @click="revertMaterialChanges">还原</el-button>
                            <el-button @click="isEditEnabled = false">返回</el-button>
                        </el-button-group>
                    </el-col>
                </el-row>
                <el-row style="margin-top: 10px">
                    <el-col :span="24">
                        <el-table :data="bomTestData" border stripe width="100%" height="400">
                            <el-table-column prop="materialProductionInstructionType" label="材料开发部标注类型"
                                :formatter="translateProductionInstructionType"></el-table-column>
                            <el-table-column prop="materialType" label="材料类型" />
                            <el-table-column label="厂家名称">
                                <template #default="scope">
                                    <el-select v-if="isEditEnabled" v-model="scope.row.supplierName" placeholder="请选择"
                                        clearable filterable>
                                        <el-option v-for="item in supplierNameOptions" :key="item.supplierName"
                                            :label="item.supplierName" :value="item.supplierName" />
                                    </el-select>
                                    <span v-else>{{ scope.row.supplierName }}</span>
                                </template>
                            </el-table-column>
                            <el-table-column label="材料名称">
                                <template #default="scope">
                                    <el-select v-if="isEditEnabled" v-model="scope.row.inboundMaterialName"
                                        placeholder="请选择" @change="handleMaterialNameSelect(scope.row)" clearable
                                        filterable>
                                        <el-option v-for="item in materialNameOptions" :key="item.materialName"
                                            :label="item.label" :value="item.value" />
                                    </el-select>
                                    <span v-else>{{ scope.row.inboundMaterialName }}</span>
                                </template>
                            </el-table-column>
                            <el-table-column label="材料型号">
                                <template #default="scope">
                                    <el-input v-if="isEditEnabled" v-model="scope.row.materialModel" placeholder="请输入"
                                        clearable />
                                    <span v-else>{{ scope.row.materialModel }}</span>
                                </template>
                            </el-table-column>
                            <el-table-column label="材料规格">
                                <template #default="scope">
                                    <el-input v-if="isEditEnabled" v-model="scope.row.materialSpecification"
                                        placeholder="请输入" clearable />
                                    <span v-else>{{ scope.row.materialSpecification }}</span>
                                </template>
                            </el-table-column>
                            <el-table-column label="颜色">
                                <template #default="scope">
                                    <el-input v-if="isEditEnabled" v-model="scope.row.color" placeholder="请输入"
                                        clearable />
                                    <span v-else>{{ scope.row.color }}</span>
                                </template>
                            </el-table-column>
                            <el-table-column label="单位">
                                <template #default="scope">
                                    <el-select v-model="scope.row.inboundUnit" placeholder="请选择" filterable
                                        @change="handleUnitChange(scope.row)"
                                        :disabled="!isEditEnabled && scope.row.unit === '双' && scope.row.materialCategory === 1">
                                        <el-option v-for="item in unitOptions" :key="item.value" :label="item.label"
                                            :value="item.value" />
                                    </el-select>
                                </template>
                            </el-table-column>
                            <el-table-column prop="unitUsage" label="单位用量"></el-table-column>
                            <el-table-column prop="approvalUsage" label="核定用量"></el-table-column>
                            <el-table-column prop="purchaseAmount" label="采购数量" width="150">
                                <template #default="scope">
                                    <el-input-number v-if="scope.row.materialCategory == 0"
                                        v-model="scope.row.purchaseAmount" :min="0" size="small"
                                        :ref="'purchaseInput-' + scope.$index"
                                        @keydown="handleKeydown($event, scope.$index)" />
                                    <el-button v-if="scope.row.materialCategory == 1" type="primary" size="default"
                                        @click="openSizeDialog(scope.row, scope.$index)">尺码用量填写</el-button>
                                </template>
                            </el-table-column>
                            <el-table-column prop="storageAmount" label="使用仓库数量"></el-table-column>
                            <el-table-column prop="remark" label="开发部备注"></el-table-column>
                            <el-table-column label="操作">
                                <template #default="scope">
                                    <el-button type="primary"
                                        @click="openSimiliarMaterialDialog(scope.row, scope.$index)">库存相似材料</el-button>
                                </template>
                            </el-table-column>
                        </el-table>
                    </el-col>

                </el-row>
                <template #footer>
                    <span>
                        <el-button @click="handleGenerateClose">取消</el-button>
                        <el-button v-if="createEditSymbol == 0" type="primary"
                            @click="confirmPurchaseSave">保存</el-button>
                        <el-button v-else-if="createEditSymbol == 1" type="primary"
                            @click="confirmPurchaseEdit">编辑保存</el-button>
                    </span>
                </template>
            </el-dialog>
            <el-dialog :title="`预览BOM表 ${previewSecondBomId}`" v-model="isPreviewSecondDialogVisible" width="90%">
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
                            <el-table :data="secondBomPreviewData" border style="width: 100%">
                                <el-table-column prop="materialType" label="材料类型" />
                                <!-- <el-table-column prop="materialDetailType" label="材料二级类型" /> -->
                                <el-table-column prop="materialName" label="材料名称" />
                                <el-table-column prop="materialModel" label="材料型号" />
                                <el-table-column prop="materialSpecification" label="材料规格" />
                                <el-table-column prop="color" label="颜色"> </el-table-column>
                                <el-table-column prop="unit" label="单位" />
                                <el-table-column prop="supplierName" label="厂家名称" />
                                <el-table-column prop="unitUsage" label="单位用量">
                                    <template #default="scope">
                                        <el-button v-if="scope.row.materialCategory == 1" type="primary" size="default"
                                            @click="openSizeDialog(scope.row, scope.$index)">尺码用量查看</el-button>
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
                        <el-button type="primary" @click="isPreviewSecondDialogVisible = false">确认</el-button>
                    </span>
                </template>
            </el-dialog>

            <el-dialog :title="`二次采购订单 ${previewBomId} 预览`" v-model="isPreviewDialogVisible" width="90%"
                :close-on-click-modal="false">
                <div style="height: 500px; overflow-y: scroll; overflow-x: hidden">
                    <el-row :gutter="20">
                        <el-col :span="6" :offset="0">
                            <el-button type="primary" size="default" :disabled="!allPurchaseDivideOrderIssued"
                                @click="advanceProcess">推进二次采购流程</el-button>

                        </el-col>
                    </el-row>

                    <el-row v-for="purchaseDivideOrder in purchaseTestData" :key="purchaseDivideOrder" :gutter="20"
                        style="margin-bottom: 20px">
                        <el-col :span="23">
                            <h3>分采购订单编号 {{ purchaseDivideOrder.purchaseDivideOrderId }}</h3>
                            <h3>工厂名称: {{ purchaseDivideOrder.supplierName }}</h3>
                            <el-row :gutter="20">
                                <el-col :span="12" :offset="0"><span>订单备注：
                                        {{ purchaseDivideOrder.remark }}
                                    </span></el-col>
                                <el-col :span="12" :offset="0">
                                    <span>环境要求：
                                        {{ purchaseDivideOrder.evironmentalRequest }}
                                    </span>
                                </el-col>
                            </el-row>
                            <el-row :gutter="20">
                                <el-col :span="12" :offset="0"><span>发货地址: {{ purchaseDivideOrder.shipmentAddress }}
                                    </span></el-col>
                                <el-col :span="12" :offset="0">
                                    <span>交货周期: {{ purchaseDivideOrder.shipmentDeadline }}
                                    </span>
                                </el-col>
                            </el-row>
                            <el-row :gutter="20">
                                <el-col :span="6" :offset="0">
                                    <span style="color: red; font-weight: bolder;">订单状态: {{
                                        purchaseDivideOrder.purchaseDivideOrderStatus }}</span>
                                </el-col>
                            </el-row>

                            <div v-if="
                                factoryFieldJudge(purchaseDivideOrder.purchaseDivideOrderType)
                            ">
                                <el-table :data="purchaseDivideOrder.assetsItems" border style="width: 100%">
                                    <el-table-column type="index" label="编号" />
                                    <el-table-column prop="materialType" label="材料类型"></el-table-column>
                                    <el-table-column prop="materialName" label="材料名称" />
                                    <el-table-column prop="materialModel" label="材料型号" />
                                    <el-table-column prop="materialSpecification" label="材料规格"></el-table-column>
                                    <el-table-column prop="unit" label="单位" />

                                    <el-table-column prop="purchaseAmount" label="采购数量" />
                                    <el-table-column :label="`分码数量 (${currentShoeSizeType})`">
                                        <el-table-column v-for="column in filteredColumns(
                                            purchaseDivideOrder.assetsItems
                                        )" :key="column.prop" :prop="column.prop"
                                            :label="column.label"></el-table-column>
                                    </el-table-column>
                                </el-table>
                            </div>
                            <div v-else>
                                <el-table :data="purchaseDivideOrder.assetsItems" border style="width: 100%">
                                    <el-table-column type="index" label="编号" />
                                    <el-table-column prop="materialType" label="材料类型"></el-table-column>
                                    <el-table-column prop="materialName" label="材料名称" />
                                    <el-table-column prop="materialModel" label="材料型号" />
                                    <el-table-column prop="materialSpecification" label="材料规格"></el-table-column>
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
                        <el-button type="primary" @click="isPreviewDialogVisible = false">确认</el-button>
                    </span>
                </template>
            </el-dialog>

            <!-- Main content -->
        </el-main>
    </el-container>
    <el-dialog title="尺码数量填写" v-model="isSizeDialogVisible" width="60%" :close-on-click-modal="false">
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
                            <el-input v-model="item.evironmentalRequest" placeholder="" type="textarea" resize="none"
                                clearable></el-input>
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

                                <el-table-column prop="amount" label="采购数量" />
                                <el-table-column :label="`分码数量(${currentShoeSizeType})`">
                                    <el-table-column v-for="column in filteredColumns(item.assetsItems)"
                                        :key="column.prop" :prop="column.prop" :label="column.label"></el-table-column>
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
    <el-dialog title="查看库存相似材料" v-model="isSimiliarMaterialDialogVisible" :draggable="true" :modal="false"
        :before-close="closeSimiliarDialog" width="80%">
        <span>
            <span>已选库存相似材料</span>
            <el-table :data="selectSimiliarData" border stripe>
                <el-table-column prop="orderRid" label="订单编号"></el-table-column>
                <el-table-column prop="orderShoeRid" label="订单鞋型编号"></el-table-column>
                <el-table-column prop="supplierName" label="厂家名称"></el-table-column>
                <el-table-column prop="materialName" label="材料名称"></el-table-column>
                <el-table-column prop="materialModel" label="材料型号"></el-table-column>
                <el-table-column prop="materialSpecification" label="材料规格"></el-table-column>
                <el-table-column prop="color" label="颜色"></el-table-column>
                <el-table-column prop="unit" label="单位"></el-table-column>
                <el-table-column prop="purchaseAmount" label="库存数量"></el-table-column>
                <el-table-column label="使用数量">
                    <template #default="scope">
                        <el-input-number v-model="scope.row.useAmount" :min="0" :step="0.001" size="small" />
                    </template>
                </el-table-column>
                <el-table-column label="操作">
                    <template #default="scope">
                        <el-button type="primary" @click="handleSimiliarMaterialDelete(scope.row)">删除</el-button>
                    </template>
                </el-table-column>
            </el-table>
            <span>相似库存材料</span>
            <el-table :data="similiarData" border stripe>
                <el-table-column prop="orderRid" label="订单编号"></el-table-column>
                <el-table-column prop="orderShoeRid" label="订单鞋型编号"></el-table-column>
                <el-table-column prop="supplierName" label="厂家名称"></el-table-column>
                <el-table-column prop="materialName" label="材料名称"></el-table-column>
                <el-table-column prop="materialModel" label="材料型号"></el-table-column>
                <el-table-column prop="materialSpecification" label="材料规格"></el-table-column>
                <el-table-column prop="color" label="颜色"></el-table-column>
                <el-table-column prop="unit" label="单位"></el-table-column>
                <el-table-column prop="purchaseAmount" label="库存数量"></el-table-column>
                <el-table-column label="操作">
                    <template #default="scope">
                        <el-button type="primary" @click="handleSimiliarMaterial(scope.row)">使用该库存材料</el-button>
                    </template>
                </el-table-column>

            </el-table>
        </span>
        <template #footer>
            <span>
                <el-button @click="closeSimiliarDialog">取消</el-button>
                <el-button type="primary" @click="saveSimiliarData">确认</el-button>
            </span>
        </template>
    </el-dialog>
    <el-dialog :title="`订单 ${orderData.orderId} 开发部尺码对照表`" v-model="isSizeComparisonDialogVisible" width="80%"
        draggable="true">
        <span>
            <el-row justify="center" align="middle">
                <h3>码数对照表</h3>
            </el-row>
            <el-row :gutter="20">
                <el-col :span="24" :offset="0">
                    <vxe-grid v-bind="sizeGridOptions">

                    </vxe-grid>
                </el-col>
            </el-row>
        </span>
        <template #footer>
            <span>
                <el-button @click="isSizeComparisonDialogVisible = false">Cancel</el-button>
                <el-button type="primary" @click="">OK</el-button>
            </span>
        </template>
    </el-dialog>
    <el-dialog title="退回流程" v-model="isRevertDialogVisable" width="20%" :close-on-click-modal="false">
        <span>
            <span>退回流程</span>
            <el-row :gutter="20">
                <el-col :span="24" :offset="0">
                    <el-form :model="revertForm" :rules="revertRules" ref="revertForm" label-width="100px">
                        <el-form-item label="退回至状态" prop="revertToStatus">
                            <el-select v-model="revertForm.revertToStatus" placeholder="请选择退回至状态" clearable
                                @change="handleStatusSelect">
                                <el-option v-for="item in revertStatusReasonOptions" :key="item.status"
                                    :label="item.statusName" :value="item.status"></el-option>
                            </el-select>
                        </el-form-item>
                        <el-form-item label="需要中间流程" prop="isNeedMiddleProcess">
                            <el-radio-group v-model="revertForm.isNeedMiddleProcess">
                                <el-radio label="1">是</el-radio>
                                <el-radio label="0">否</el-radio>
                            </el-radio-group>
                        </el-form-item>
                        <el-form-item label="退回原因" prop="revertReason">
                            <el-input v-model="revertForm.revertReason" :rows="4" placeholder="请输入退回原因"
                                disabled></el-input>
                        </el-form-item>
                        <el-form-item label="退回详细原因" prop="revertDetail">
                            <el-input v-model="revertForm.revertDetail" type="textarea" :rows="4"
                                placeholder="请输入退回原因"></el-input>
                        </el-form-item>
                    </el-form>
                </el-col>
            </el-row>
        </span>
        <template #footer>
            <span>
                <el-button @click="isRevertDialogVisable = false">取消</el-button>
                <el-button type="primary" @click="saveRevertForm">确认</el-button>
            </span>
        </template>
    </el-dialog>

</template>

<script>
import { Search } from '@element-plus/icons-vue'
import AllHeader from '@/components/AllHeader.vue'
import Arrow from '@/components/OrderArrowView.vue'
import axios from 'axios'
import { getShoeSizesName } from '@/Pages/utils/getShoeSizesName'
import { shoeBatchInfoTableSpanMethod } from '@/Pages/ProductionManagementDepartment/utils'
import { ElMessage, ElMessageBox } from 'element-plus'
import { markRaw } from 'vue'
export default {
    props: ['orderId'],
    components: {
        AllHeader,
        Arrow
    },
    data() {
        return {
            role: localStorage.getItem('role'),
            batchInfoSpanMethod: null,
            currentSizeIndex: 0,
            currentSimiliarIndex: 0,
            purchaseOrderCreateVis: false,
            createEditSymbol: 0,
            newPurchaseOrderId: '',
            activeTab: '',
            isPurchaseOrderVis: false,
            createVis: false,
            isSizeDialogVisible: false,
            isSizeComparisonDialogVisible: false,
            sizeGridOptions: [],
            sizeData: [],
            tabPlaneData: [],
            orderData: {},
            testTableData: [],
            testTableFilterData: [],
            orderProduceInfo: [],
            bomTestData: [],
            secondBomPreviewData: [],
            previewSecondBomId: '',
            isPreviewSecondDialogVisible: false,
            supplierNameOptions: [],
            currentBOMId: '',
            purchaseTestData: [],
            isPreviewDialogVisible: false,
            selectedFile: null,
            inheritIdSearch: '',
            currentShoeSizeType: '',
            getShoeSizesName,
            shoeSizeColumns: [],
            orderInfoVisible: true,
            isEditEnabled: false,
            materialTypeOptions: [],
            materialNameOptions: [],
            currentOrderShoeRow: {},
            previewBomId: '',
            Search: markRaw(Search),
            previewAdvanceSymbol: true,
            unitOptions: [],
            isSimiliarMaterialDialogVisible: false,
            selectSimiliarData: [],
            similiarData: [],
            revertForm: {
                revertToStatus: '',
                revertReason: '',
                revertDetail: '',
                isNeedMiddleProcess: '0'
            },
            revertStatusReasonOptions: [],
            isRevertDialogVisable: false
        }
    },
    async mounted() {
        this.shoeSizeColumns = await this.getShoeSizesName(this.$props.orderId)
        this.currentShoeSizeType = this.shoeSizeColumns[0].type
        this.getAllMaterialNames()
        this.querySupplierNames()
        this.$setAxiosToken()
        await this.getOrderInfo()
        this.getAllShoeListInfo()
        await this.getAllPurchaseUnit()
        await this.getRevertStatusReason()

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
        },
        allPurchaseDivideOrderIssued() {
            return this.purchaseTestData.every(item => item.purchaseDivideOrderStatus === "已下发") && this.previewAdvanceSymbol;
        }
    },
    methods: {
        handleKeydown(event, index) {
            if (event.key === "Enter") {
                event.preventDefault(); // Stop default behavior

                this.focusNextInput(index + 1);
            }
        },

        focusNextInput(startIndex) {
            this.$nextTick(() => {
                let nextIndex = startIndex;
                const maxIndex = this.bomTestData.length;

                // Find the next available input (skip rows with buttons)
                while (nextIndex < maxIndex && !this.$refs["purchaseInput-" + nextIndex]) {
                    nextIndex++; // Move to next row
                }

                const inputComponent = this.$refs["purchaseInput-" + nextIndex];

                if (inputComponent) {
                    // Focus the input inside el-input-number
                    const inputElement = inputComponent.$el.querySelector("input");
                    if (inputElement) {
                        inputElement.focus();
                        inputElement.select(); // Optional: Select text for easier editing
                    }
                }
            });
        },
        async revertMaterialChanges() {
            ElMessageBox.confirm('确定要还原所有材料更改吗？', '提示', {
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                type: 'warning'
            }).then(async () => {
                let params = []
                for (let i = 0; i < this.bomTestData.length; i++) {
                    params.push(this.bomTestData[i].bomItemId)
                }
                try {
                    await axios.patch(`${this.$apiBaseUrl}/purchaseorder/reverttooriginalbomitem`, params)
                    await this.getBOMDetails(this.currentOrderShoeRow)
                    ElMessage.success('还原成功')
                }
                catch (error) {
                    console.log(error)
                    ElMessage.error('还原失败')
                }

            })
        },
        handleSupplierNameSelect(row) {
            row.supplierId = this.supplierNameOptions.find(
                (option) => option.supplierName === row.supplierName
            ).supplierId
        },
        handleMaterialNameSelect(row) {
            const selectedMaterial = this.materialNameOptions.find(
                (option) => option.value === row.materialName
            )
            row.materialId = selectedMaterial.materialId
            row.materialTypeId = selectedMaterial.type
            row.materialType = selectedMaterial.materialTypeName
            row.unit = selectedMaterial.unit
        },
        async handleUnitChange(row) {
            if (row.inboundUnit !== row.unit) {
                row.inboundMaterialName = row.materialName + '-' + row.inboundUnit
            }
            else {
                row.inboundMaterialName = row.materialName
            }

            console.log(row.inboundMaterialName)
        },
        handleSimiliarMaterial(row) {
            this.selectSimiliarData.push(row)
            this.similiarData = this.similiarData.filter(item => item !== row)
        },
        handleSimiliarMaterialDelete(row) {
            this.similiarData.push(row)
            this.selectSimiliarData = this.selectSimiliarData.filter(item => item !== row)
        },
        async openSizeComparisonDialog(row) {
            await this.getSizeTableData(row);
            this.sizeGridOptions.editConfig = false;
            for (let item of this.sizeGridOptions.columns) {
                item.width = 125;
            }
            this.isSizeComparisonDialogVisible = true;
        },
        async getSizeTableData(row) {
            const response = await axios.get(
                `${this.$apiBaseUrl}/devproductionorder/getsizetable?orderId=${this.orderData.orderDBId}`
            )

            this.sizeGridOptions = response.data
            console.log(this.sizeGridOptions)
        },
        closeSimiliarDialog() {
            this.similiarData = []
            this.selectSimiliarData = []
            this.isSimiliarMaterialDialogVisible = false
        },
        saveSimiliarData() {
            if (this.selectSimiliarData.length === 0) {
                this.bomTestData[this.currentSimiliarIndex].similiarMaterial = []
                this.isSimiliarMaterialDialogVisible = false
                return
            }
            // add a json object to bomTestData, like {type：0/1, ,materialstorageid: , useAmount: }
            // transform the selectSimiliarData to the format json object
            const similiarMaterial = this.selectSimiliarData.map(item => {
                return {
                    type: item.similiarType,
                    materialStorageId: item.materialStorageId,
                    useAmount: item.useAmount
                }
            })
            this.bomTestData[this.currentSimiliarIndex].warehouseUsageInfo = similiarMaterial
            this.isSimiliarMaterialDialogVisible = false

        },
        async getAllMaterialNames() {
            const params = { department: 0 }
            const response = await axios.get(`${this.$apiBaseUrl}/logistics/getallmaterialname`, { params })
            this.materialNameOptions = response.data
        },
        changeEditMode() {
            this.isEditEnabled = !this.isEditEnabled
        },
        async querySupplierNames() {
            const response = await axios.get(`${this.$apiBaseUrl}/logistics/allsuppliers`)
            this.supplierNameOptions = response.data
        },
        translateProductionInstructionType(row) {
            const typeMap = {
                S: '面料',
                I: '里料',
                A: '辅料',
                M: '中底',
                O: '大底',
                H: '烫底'
            }
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
        async getNewPurchaseOrderId() {
            const response = await axios.get(
                `${this.$apiBaseUrl}/secondpurchase/getnewpurchaseorderid`
            )
            this.newPurchaseOrderId = response.data.purchaseOrderId
        },
        async getSecondBomPreviewData(row) {
            const response = await axios.get(
                `${this.$apiBaseUrl}/usagecalculation/getshoebomitems`,
                {
                    params: {
                        bomrid: row.secondBomId
                    }
                }
            )
            this.secondBomPreviewData = response.data
        },
        async getOrderInfo() {
            const response = await axios.get(
                `${this.$apiBaseUrl}/order/getorderInfo?orderid=${this.orderId}`
            )
            this.orderData = response.data
        },
        async getAllShoeListInfo() {
            const response = await axios.get(
                `${this.$apiBaseUrl}/secondpurchase/getordershoelist?orderid=${this.orderId}`
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
                `${this.$apiBaseUrl}/secondpurchase/getshoebomitems`,
                {
                    params: {
                        bomrid: row.totalBomId,
                        orderid: this.$props.orderId
                    }
                }
            )
            this.bomPreviewData = response.data
            this.bomTestData = response.data
            for (const item of this.bomTestData) {
                item.purchaseAmount = Number(item.purchaseAmount)
            }
        },
        async getAllPurchaseUnit() {
            const response = await axios.get(`${this.$apiBaseUrl}/logistics/getallunit`)
            this.unitOptions = response.data
            console.log(this.unitOptions)
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
            for (const sizeRow of this.sizeData) {
                sizeRow.purchaseAmount = parseFloat(sizeRow.approvalAmount) || 0
            }
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
            this.currentOrderShoeRow = row
            await this.getNewPurchaseOrderId()
            await this.getOrderShoeBatchInfo(row.orderShoeId)
            await this.getBOMDetails(row)
            this.currentBOMId = row.totalBomId
            this.currentPurchaseShoeId = row.inheritId
            this.bomTestData.forEach((item) => {
                item.storageAmount = item.warehouseUsageInfo.reduce(
                    (total, item) => total + item.useAmount,
                    0
                )
            })
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
        async openSimiliarMaterialDialog(row, index) {
            const response = await axios.get(
                `${this.$apiBaseUrl}/logistics/getmaterialstoragesimiliar`,
                {
                    params: {
                        materialId: row.materialId,
                        materialModel: row.materialModel,
                        materialSpecification: row.materialSpecification,

                    }
                }
            )
            this.similiarData = response.data
            if (row.warehouseUsageInfo.length > 0) {
                const response = await axios.get(
                    `${this.$apiBaseUrl}/logistics/getselectedmaterialstorage`,
                    {
                        params: {
                            warehouseUsageInfo: row.warehouseUsageInfo
                        }
                    }
                )
                this.selectSimiliarData = response.data
            }
            else {
                this.selectSimiliarData = []
            }
            this.currentSizeIndex = index
            this.isSimiliarMaterialDialogVisible = true
        },
        async openPreviewDialog(row) {
            if (row.currentStatus === '已提交') {
                this.previewAdvanceSymbol = false
            }
            else {
                this.previewAdvanceSymbol = true
            }
            this.previewBomId = row.purchaseOrderId
            try {
                const response = await axios.get(
                    `${this.$apiBaseUrl}/secondpurchase/getpurchasedivideorders`,
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
        async openSecondBOMPreviewDialog(row) {
            this.previewSecondBomId = row.secondBomId
            await this.getSecondBomPreviewData(row)
            this.isPreviewSecondDialogVisible = true
        },
        async openEditDialog(row) {
            const loadingInstance = this.$loading({
                lock: true,
                text: '等待中，请稍后...',
                background: 'rgba(0, 0, 0, 0.7)'
            })
            this.currentOrderShoeRow = row
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
                `${this.$apiBaseUrl}/secondpurchase/getpurchasedivideorders`,
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
                `${this.$apiBaseUrl}/secondpurchase/editpurchaseitems`,
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
            // this.createVis = false
            this.getAllShoeListInfo()
        },
        async submitBOMUsage(row) {
            const response = await this.$axios.get(
                `${this.$apiBaseUrl}/secondpurchase/getpurchasedivideorders`,
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
                `${this.$apiBaseUrl}/secondpurchase/savepurchase`,
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
                `${this.$apiBaseUrl}/secondpurchase/submitpurchasedivideorders`,
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
                `${this.$apiBaseUrl}/secondpurchase/savepurchasedivideorders`,
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
        advanceProcess() {
            this.$confirm('确定推进二次采购流程吗？', '提示', {
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                type: 'warning'
            })
                .then(async () => {
                    const response = await axios.post(
                        `${this.$apiBaseUrl}/secondpurchase/advanceprocess`,
                        {
                            purchaseOrderId: this.previewBomId
                        }
                    )
                    if (response.status !== 200) {
                        this.$message({
                            type: 'error',
                            message: '推进失败'
                        })
                        return
                    }
                    this.$message({
                        type: 'success',
                        message: '推进成功'
                    })
                    this.isPreviewDialogVisible = false
                    this.getAllShoeListInfo()
                })
                .catch(() => {
                    this.$message({
                        type: 'info',
                        message: '已取消推进'
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
                `${this.$apiBaseUrl}/secondpurchase/downloadpurchaseorderzip?orderrid=${this.orderData.orderId}&ordershoerid=${row.inheritId}`
            )
        },
        downloadMaterialStasticExcel(row) {
            window.open(
                `${this.$apiBaseUrl}/secondpurchase/downloadmaterialstatistics?orderrid=${this.orderData.orderId}&ordershoerid=${row.inheritId}`
            )
        },
        openLastPurchasePage(orderId) {
            //open a new page named lastpurchase
            window.open(`${window.location.origin}/lastpurchase/orderid=${orderId}`, '_blank')
        },
        openPackagePurchasePage(orderId) {
            //open a new page named packagepurchase
            window.open(`${window.location.origin}/packagepurchase/orderid=${orderId}`, '_blank')
        },
        openCutModelPurchasePage(orderId) {
            //open a new page named cutmodelpurchase
            window.open(`${window.location.origin}/cutmodelpurchase/orderid=${orderId}`, '_blank')
        },
        openReturnOrderDialog() {
            this.revertForm.revertToStatus = ''
            this.revertForm.revertDetail = ''
            this.revertForm.revertReason = ''
            this.revertForm.isNeedMiddleProcess = '0'
            this.isRevertDialogVisable = true
        },
        handleStatusSelect() {
            //when select status, make the revertReason to be the reason field of the selected status
            const selectedStatus = this.revertStatusReasonOptions.find(item => item.status === this.revertForm.revertToStatus)
            this.revertForm.revertReason = selectedStatus.reason
        },
        saveRevertForm() {
            this.$confirm(`确定退回此订单吗？退回至 ${this.revertForm.revertToStatus}, 原因是 ${this.revertForm.revertReason}`, '提示', {
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                type: 'warning'
            }).then(() => {
                this.revertOrder()
            }).catch(() => {
                this.$message({
                    type: 'info',
                    message: '已取消退回'
                })
            })
        },
        async revertOrder() {
            this.$refs.revertForm.validate(async (valid) => {
                if (!valid) {
                    return
                }
                const response = await axios.post(`${this.$apiBaseUrl}/revertorder/revertordersave`, {
                    orderId: this.orderData.orderDBId,
                    flow: 2,
                    revertToStatus: this.revertForm.revertToStatus,
                    revertReason: this.revertForm.revertReason,
                    revertDetail: this.revertForm.revertDetail,
                    isNeedMiddleProcess: this.revertForm.isNeedMiddleProcess
                })
                if (response.status === 200) {
                    this.$message({
                        type: 'success',
                        message: '退回成功'
                    })
                    this.isRevertDialogVisable = false
                    this.getAllShoeListInfo()
                }
                else {
                    this.$message({
                        type: 'error',
                        message: '退回失败'
                    })
                }
            })
        },

        downloadLastZip(orderId) {
            window.open(
                `${this.$apiBaseUrl}/logistics/downloadlastpurchaseorders?orderId=${orderId}`
            )
        },
        downloadPackageZip(orderId) {
            window.open(
                `${this.$apiBaseUrl}/logistics/downloadpackagepurchaseorders?orderId=${orderId}`
            )
        },
        downloadCutModelZip(orderId) {
            window.open(
                `${this.$apiBaseUrl}/logistics/downloadcutmodelpurchaseorders?orderId=${orderId}`
            )
        },
        async getAllRevertStatusReasonOptions() {
            const response = await axios.get(`${this.$apiBaseUrl}/revertorder/getrevertorderreason`,
                { params: { orderId: this.orderData.orderDBId, flow: 2 } }
            )
            this.revertStatusReasonOptions = response.data
        },

    }
}
</script>

<style scoped>
/* Add your styles here */
</style>
