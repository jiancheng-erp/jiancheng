<template>
    <el-container direction="vertical">
        <el-header class="app-header">
            <AllHeader></AllHeader>
        </el-header>
        <el-main style="overflow-x: hidden">
            <el-row :gutter="20" style="text-align: center">
                <el-col :span="24" :offset="0" style="font-size: xx-large; text-align: center"
                    >一次BOM填写</el-col
                >
            </el-row>
            <el-row :gutter="20">
                <el-col :span="24" :offset="0">
                    <span style="font-weight: bold; font-size: larger">订单信息：</span>
                    <el-row :gutter="20">
                        <el-col :span="24" :offset="0">
                            <Arrow :status="orderData.status" :key="updateArrowKey"></Arrow>
                        </el-col>
                    </el-row>
                    <el-row :gutter="20">
                        <el-col :span="24" :offset="0">
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
                                <!-- <el-descriptions-item label="前序流程下发时间">{{ testOrderData.prevTime }}</el-descriptions-item>
                                <el-descriptions-item label="前序处理部门">{{ testOrderData.prevDepart }}</el-descriptions-item>
                                <el-descriptions-item label="前序处理人">{{ testOrderData.prevUser }}</el-descriptions-item> -->
                                <el-descriptions-item label="订单预计截止日期" align="center">{{
                                    orderData.deadlineTime
                                }}</el-descriptions-item>
                            </el-descriptions>
                        </el-col>
                    </el-row>
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
                                    <el-table-column label="操作" align="center">
                                        <template #default="scope">
                                            <el-button
                                                v-if="parentScope.row.status.includes('一次BOM填写') && scope.row.firstBomStatus === '未填写'"
                                                type="primary"
                                                @click="handleGenerate(scope.row)"
                                                >填写</el-button
                                            >
                                            <el-button
                                                v-else-if="
                                                    (scope.row.firstBomStatus === '已下发' ||
                                                    scope.row.firstBomStatus === '已提交' ||
                                                    scope.row.firstBomStatus === '等待用量填写' ||
                                                    scope.row.firstBomStatus === '已用量填写' ||
                                                    scope.row.firstBomStatus === 'BOM完成')
                                                "
                                                type="primary"
                                                @click="openPreviewDialog(scope.row)"
                                                >查看</el-button
                                            >
                                            <div v-else-if="parentScope.row.status.includes('一次BOM填写') && scope.row.firstBomStatus === '已保存'">
                                                <el-button
                                                    type="primary"
                                                    @click="openEditDialog(scope.row)"
                                                    >编辑</el-button
                                                >
                                                <el-button
                                                    type="success"
                                                    @click="openPreviewDialog(scope.row)"
                                                    >预览</el-button
                                                >
                                                <el-button
                                                    type="warning"
                                                    @click="submitBOM(scope.row)"
                                                    >提交</el-button
                                                >
                                            </div>
                                        </template></el-table-column
                                    >
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
                            prop="status"
                            label="状态"
                            align="center"
                        ></el-table-column> </el-table
                ></el-col>
            </el-row>
            <el-row :gutter="22" style="margin-top: 10px">
                <el-col :span="6" :offset="20"
                    ><el-button type="primary" size="default" @click="openIssueDialog"
                        >下发BOM</el-button
                    >
                </el-col>
            </el-row>

            <el-dialog
                :title="`一次BOM填写 ${newBomId}`"
                v-model="createVis"
                width="100%"
                @close="handleGenerateClose"
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
                    <!-- <el-descriptions-item label="前序流程下发时间">{{ testOrderData.prevTime }}</el-descriptions-item>
                                <el-descriptions-item label="前序处理部门">{{ testOrderData.prevDepart }}</el-descriptions-item>
                                <el-descriptions-item label="前序处理人">{{ testOrderData.prevUser }}</el-descriptions-item> -->
                    <el-descriptions-item label="订单预计截止日期" align="center">{{
                        orderData.deadlineTime
                    }}</el-descriptions-item>
                    <el-descriptions-item label="鞋型号" align="center">{{
                        currentBomShoeId
                    }}</el-descriptions-item>
                    <el-descriptions-item label="颜色" align="center">{{
                        currentColor
                    }}</el-descriptions-item>
                    <el-descriptions-item label="工艺单" align="center">
                        <el-button
                            type="primary"
                            size="default"
                            @click="downloadProductionOrderList"
                            >查看投产指令单</el-button
                        >
                    </el-descriptions-item>
                    <!-- <el-descriptions-item label="生产订单" align="center"
                        ><el-button type="primary" size="default" @click="downloadProductionOrder"
                            >查看生产订单</el-button
                        >
                    </el-descriptions-item> -->
                </el-descriptions>
                <div style="height: 600px; overflow-y: scroll; overflow-x: hidden">
                    <el-row>
                        <el-table
                            :data="orderProduceInfo"
                            border
                            style="width: 100%"
                            :span-method="arraySpanMethod"
                        >
                            <el-table-column prop="35" label="35" />
                            <el-table-column prop="36" label="36" />
                            <el-table-column prop="37" label="37" />
                            <el-table-column prop="38" label="38" />
                            <el-table-column prop="39" label="39" />
                            <el-table-column prop="40" label="40" />
                            <el-table-column prop="41" label="41" />
                            <el-table-column prop="42" label="42" />
                            <el-table-column prop="43" label="43" />
                            <el-table-column prop="44" label="44" />
                            <el-table-column prop="45" label="45" />
                            <el-table-column prop="total" label="合计" />
                        </el-table>
                    </el-row>
                    <el-row>
                        <el-button type="primary" size="default" @click="">加载默认材料</el-button>
                    </el-row>
                    <el-row style="margin-top: 10px">
                        <el-table :data="bomTestData" border>
                            <el-table-column prop="materialType" label="材料类型">
                            </el-table-column>
                            <el-table-column prop="materialName" label="材料名称">
                            </el-table-column>
                            <el-table-column prop="materialModel" label="材料型号">
                                <template #default="scope">
                                    <el-input
                                        v-model="scope.row.materialModel"
                                        placeholder="请输入型号"
                                        size="default"
                                    />
                                </template>
                            </el-table-column>
                            <el-table-column prop="materialSpecification" label="材料规格">
                                <template #default="scope">
                                    <el-input
                                        v-model="scope.row.materialSpecification"
                                        placeholder="请输入规格"
                                        size="default"
                                    />
                                </template>
                            </el-table-column>
                            <el-table-column prop="color" label="颜色">
                                <template #default="scope">
                                    <el-input
                                        v-model="scope.row.color"
                                        placeholder="请输入颜色"
                                        size="default"
                                    />
                                </template>
                            </el-table-column>
                            <el-table-column prop="unit" label="单位"> </el-table-column>
                            <el-table-column prop="supplierName" label="厂家名称"></el-table-column>
                            <el-table-column
                                prop="materialCategory"
                                label="材料数量类型"
                                :formatter="categroryFormatter"
                            ></el-table-column>
                            <el-table-column prop="useDepart" label="使用工段">
                                <template #default="scope">
                                    <el-select v-model="scope.row.useDepart" size="default">
                                        <el-option
                                            v-for="item in departmentOptions"
                                            :key="item.value"
                                            :label="item.label"
                                            :value="item.value"
                                        ></el-option>
                                    </el-select>
                                </template>
                            </el-table-column>
                            <el-table-column label="备注">
                                <template #default="scope">
                                    <el-input v-model="scope.row.comment" size="default" />
                                </template>
                            </el-table-column>
                            <el-table-column label="操作">
                                <template #default="scope">
                                    <el-button
                                        type="danger"
                                        @click="deleteCurrentRow(scope.$index, bomTestData)"
                                        >删除</el-button
                                    >
                                </template></el-table-column
                            >
                        </el-table>
                    </el-row>
                </div>
                <el-button type="primary" size="default" @click="openNewMaterialDialog"
                    >添加新部件</el-button
                >

                <template #footer>
                    <span>
                        <el-button @click="handleGenerateClose">取消</el-button>
                        <el-button type="primary" @click="confirmBOMSave">保存</el-button>
                    </span>
                </template>
            </el-dialog>

            <el-dialog
                :title="`预览BOM表 ${previewBomId}`"
                v-model="isPreviewDialogVisible"
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
                    <!-- <el-descriptions-item label="前序流程下发时间">{{ testOrderData.prevTime }}</el-descriptions-item>
                                <el-descriptions-item label="前序处理部门">{{ testOrderData.prevDepart }}</el-descriptions-item>
                                <el-descriptions-item label="前序处理人">{{ testOrderData.prevUser }}</el-descriptions-item> -->
                    <el-descriptions-item label="订单预计截止日期" align="center">{{
                        orderData.deadlineTime
                    }}</el-descriptions-item>
                </el-descriptions>
                <div style="height: 600px; overflow-y: scroll; overflow-x: hidden">
                    <el-row :gutter="20" style="margin-bottom: 20px">
                        <el-col :span="23">
                            <el-table
                                :data="orderProduceInfo"
                                border
                                style="width: 100%"
                                :span-method="arraySpanMethod"
                            >
                                <el-table-column prop="35" label="35" />
                                <el-table-column prop="36" label="36" />
                                <el-table-column prop="37" label="37" />
                                <el-table-column prop="38" label="38" />
                                <el-table-column prop="39" label="39" />
                                <el-table-column prop="40" label="40" />
                                <el-table-column prop="41" label="41" />
                                <el-table-column prop="42" label="42" />
                                <el-table-column prop="43" label="43" />
                                <el-table-column prop="44" label="44" />
                                <el-table-column prop="45" label="45" />
                                <el-table-column prop="total" label="合计" />
                            </el-table>
                        </el-col>
                    </el-row>
                    <el-row :gutter="20" style="margin-bottom: 20px">
                        <el-col :span="23">
                            <el-table :data="bomPreviewData" border style="width: 100%">
                                <el-table-column prop="materialType" label="材料类型" />
                                <el-table-column prop="materialName" label="材料名称" />
                                <el-table-column prop="materialModel" label="材料型号" />
                                <el-table-column prop="materialSpecification" label="材料规格" />
                                <el-table-column prop="color" label="颜色">
                                </el-table-column>
                                <el-table-column prop="unit" label="单位" />
                                <el-table-column prop="supplierName" label="厂家名称" />
                                <el-table-column prop="useDepart" label="使用工段">
                                    <template #default="scope">
                                        <el-select
                                            v-model="scope.row.useDepart"
                                            size="default"
                                            disabled
                                        >
                                            <el-option
                                                v-for="item in departmentOptions"
                                                :key="item.value"
                                                :label="item.label"
                                                :value="item.value"
                                            ></el-option>
                                        </el-select>
                                    </template>
                                </el-table-column>
                                <el-table-column prop="comment" label="备注" />
                            </el-table>
                        </el-col>
                    </el-row>
                </div>
                <template #footer>
                    <span>
                        <el-button type="primary" @click="closePreviewDialog">确认</el-button>
                    </span>
                </template>
            </el-dialog>

            <el-dialog title="正式BOM表下发页面" v-model="isFinalBOM" width="90%">
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
                    <!-- <el-descriptions-item label="前序流程下发时间">{{ testOrderData.prevTime }}</el-descriptions-item>
                                <el-descriptions-item label="前序处理部门">{{ testOrderData.prevDepart }}</el-descriptions-item>
                                <el-descriptions-item label="前序处理人">{{ testOrderData.prevUser }}</el-descriptions-item> -->
                    <el-descriptions-item label="订单预计截止日期" align="center">{{
                        orderData.deadlineTime
                    }}</el-descriptions-item>
                </el-descriptions>
                <div style="height: 400px; overflow-y: scroll; overflow-x: hidden">
                    <el-row :gutter="20" style="margin-bottom: 20px">
                        <el-col :span="24">
                            <el-table
                                :data="unIssueBOMData"
                                border
                                style="height: 400px"
                                @selection-change="handleShoeSelectionChange"
                            >
                                <el-table-column type="selection" width="55"></el-table-column>
                                <el-table-column type="expand">
                                    <template #default="scope">
                                        <el-table :data="scope.row.typeInfos" border>
                                            <el-table-column
                                                prop="color"
                                                label="颜色"
                                            ></el-table-column>
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
                                            <el-table-column label="操作" align="center">
                                                <template #default="scope">
                                                    <el-button
                                                        v-if="scope.row.firstBomStatus === '未填写'"
                                                        type="primary"
                                                        @click="handleGenerate(scope.row)"
                                                        >填写</el-button
                                                    >
                                                    <el-button
                                                        v-else-if="
                                                            scope.row.firstBomStatus === '已下发' ||
                                                            scope.row.firstBomStatus === '已提交' ||
                                                            scope.row.firstBomStatus ===
                                                                '等待用量填写' ||
                                                            scope.row.firstBomStatus ===
                                                                '已用量填写' ||
                                                            scope.row.firstBomStatus === 'BOM完成'
                                                        "
                                                        type="primary"
                                                        @click="openPreviewDialog(scope.row)"
                                                        >查看</el-button
                                                    >
                                                    <div
                                                        v-else-if="
                                                            scope.row.firstBomStatus === '已保存'
                                                        "
                                                    >
                                                        <el-button
                                                            type="primary"
                                                            @click="openEditDialog(scope.row)"
                                                            >编辑</el-button
                                                        >
                                                        <el-button
                                                            type="success"
                                                            @click="openPreviewDialog(scope.row)"
                                                            >预览</el-button
                                                        >
                                                        <el-button
                                                            type="warning"
                                                            @click="submitBOM(scope.row)"
                                                            >提交</el-button
                                                        >
                                                    </div>
                                                </template></el-table-column
                                            >
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
                            </el-table>
                        </el-col>
                    </el-row>
                </div>
                <template #footer>
                    <span>
                        <el-button @click="isFinalBOM = false">取消</el-button>
                        <el-button type="primary" @click="issueBOMs(selectedShoe)"
                            >下发选定BOM表</el-button
                        >
                    </span>
                </template>
            </el-dialog>
            <el-dialog title="添加新材料" v-model="newMaterialVis" width="50%">
                <el-row :gutter="20">
                    <el-col :span="6" :offset="0">
                        <div style="display: flex; align-items: center; white-space: nowrap">
                            材料类型查询：<el-input
                                v-model="materialTypeSearch"
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
                                v-model="materialSearch"
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
                                v-model="factorySearch"
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
                        <el-button @click="handleGenerateClose">取消</el-button>
                        <el-button
                            v-if="createVis == true"
                            type="primary"
                            @click="confirmNewMaterialAdd(0)"
                            >保存</el-button
                        >
                        <el-button
                            v-else-if="editVis == true"
                            type="primary"
                            @click="confirmNewMaterialAdd(1)"
                            >保存</el-button
                        >
                    </span>
                </template>
            </el-dialog>
            <el-dialog :title="`一次BOM编辑 ${editBomId}`" v-model="editVis" width="100%">
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
                    <!-- <el-descriptions-item label="前序流程下发时间">{{ testOrderData.prevTime }}</el-descriptions-item>
                                <el-descriptions-item label="前序处理部门">{{ testOrderData.prevDepart }}</el-descriptions-item>
                                <el-descriptions-item label="前序处理人">{{ testOrderData.prevUser }}</el-descriptions-item> -->
                    <el-descriptions-item label="订单预计截止日期" align="center">{{
                        orderData.deadlineTime
                    }}</el-descriptions-item>
                </el-descriptions>
                <div style="height: 600px; overflow-y: scroll; overflow-x: hidden">
                    <el-row>
                        <el-table
                            :data="orderProduceInfo"
                            border
                            style="width: 100%"
                            :span-method="arraySpanMethod"
                            height="300"
                        >
                            <el-table-column prop="35" label="35" />
                            <el-table-column prop="36" label="36" />
                            <el-table-column prop="37" label="37" />
                            <el-table-column prop="38" label="38" />
                            <el-table-column prop="39" label="39" />
                            <el-table-column prop="40" label="40" />
                            <el-table-column prop="41" label="41" />
                            <el-table-column prop="42" label="42" />
                            <el-table-column prop="43" label="43" />
                            <el-table-column prop="44" label="44" />
                            <el-table-column prop="45" label="45" />
                            <el-table-column prop="total" label="合计" />
                        </el-table>
                    </el-row>
                    <el-row style="margin-top: 10px">
                        <el-table :data="editBomData" border>
                            <el-table-column prop="materialType" label="材料类型">
                            </el-table-column>
                            <el-table-column prop="materialName" label="材料名称">
                            </el-table-column>
                            <el-table-column prop="materialModel" label="材料型号">
                                <template #default="scope">
                                    <el-input v-model="scope.row.materialModel" size="default" />
                                </template>
                            </el-table-column>
                            <el-table-column prop="materialSpecification" label="材料规格">
                                <template #default="scope">
                                    <el-input
                                        v-model="scope.row.materialSpecification"
                                        size="default"
                                    />
                                </template>
                            </el-table-column>
                            <el-table-column prop="color" label="颜色">
                                <template #default="scope">
                                    <el-input
                                        v-model="scope.row.color"
                                        size="default"
                                        placeholder="请输入颜色"
                                    />
                                </template>
                            </el-table-column>
                            <el-table-column prop="unit" label="单位"> </el-table-column>
                            <el-table-column prop="supplierName" label="厂家名称"></el-table-column>
                            <el-table-column
                                prop="materialCategory"
                                label="材料数量类型"
                                :formatter="categroryFormatter"
                            ></el-table-column>
                            <el-table-column prop="useDepart" label="使用工段">
                                <template #default="scope">
                                    <el-select v-model="scope.row.useDepart" size="default">
                                        <el-option
                                            v-for="item in departmentOptions"
                                            :key="item.value"
                                            :label="item.label"
                                            :value="item.value"
                                        ></el-option>
                                    </el-select>
                                </template>
                            </el-table-column>
                            <el-table-column label="备注">
                                <template #default="scope">
                                    <el-input v-model="scope.row.comment" size="default" />
                                </template>
                            </el-table-column>
                            <el-table-column label="操作">
                                <template #default="scope">
                                    <el-button
                                        type="danger"
                                        @click="deleteCurrentRow(scope.row, editBomData)"
                                        >删除
                                    </el-button>
                                </template></el-table-column
                            >
                        </el-table>
                    </el-row>
                </div>
                <el-button type="primary" size="default" @click="openNewMaterialDialog"
                    >添加新部件</el-button
                >
                <template #footer>
                    <span>
                        <el-button @click="handleGenerateClose">取消</el-button>
                        <el-button type="primary" @click="confirmBOMEdit">保存</el-button>
                    </span>
                </template>
            </el-dialog>
        </el-main>
    </el-container>
</template>

<script>
import AllHeader from '@/components/AllHeader.vue'
import Arrow from '@/components/OrderArrowView.vue'
import { Search } from '@element-plus/icons-vue'
import { ElMessageBox } from 'element-plus'

import axios from 'axios'
export default {
    components: {
        AllHeader,
        Arrow
    },
    props: ['orderId'],
    data() {
        return {
            selectedShoe: '',
            unIssueBOMData: [],
            updateKey: 0,
            editVis: false,
            editBomId: '',
            previewBomId: '',
            newBomId: '',
            currentColor: '',
            currentBomShoeId: '',
            materialSelectRow: null,
            Search,
            materialAddfinished: true,
            materialTypeSearch: '',
            materialSearch: '',
            factorySearch: '',
            assetFilterTable: [],
            colorOptions: [],
            newMaterialVis: false,
            updateArrowKey: 0,
            orderData: {},
            createVis: false,
            testTableData: [],
            testTableFilterData: [],
            bomTestData: [],
            editBomData: [],
            originalBomTestData: [],
            factoryOptions: [
                // Add more options here
            ],
            isPreviewDialogVisible: false,
            selectedFile: null,
            inheritIdSearch: '',
            isFinalBOM: false,
            orderProduceInfo: [],
            currentOrderShoeId: ''
        }
    },
    async mounted() {
        this.getOrderInfo()
        this.getAllShoeBomInfo()
        this.getAllColorOptions()
        this.getAllDepartmentOptions()
    },
    methods: {
        async getNewBomId() {
            const response = await axios.get(`${this.$apiBaseUrl}/firstbom/getnewbomid`)
            this.newBomId = response.data.bomId
        },
        async getAllDepartmentOptions() {
            const response = await axios.get(`${this.$apiBaseUrl}/general/getalldepartments`)
            this.departmentOptions = response.data
        },
        async getAllColorOptions() {
            const response = await axios.get(`${this.$apiBaseUrl}/general/allcolors`)
            this.colorOptions = response.data
        },
        async getMaterialFilterData() {
            this.materialAddfinished = true
            const response = await axios.get(
                `${this.$apiBaseUrl}/logistics/getmaterialtypeandname`,
                {
                    params: {
                        materialtype: this.materialTypeSearch,
                        materialname: this.materialSearch,
                        suppliername: this.factorySearch
                    }
                }
            )
            this.assetFilterTable = response.data
            this.materialAddfinished = false
        },
        async getAllMaterialList() {
            const response = await axios.get(`${this.$apiBaseUrl}/logistics/getmaterialtypeandname`)
            this.assetTable = response.data
            this.assetFilterTable = this.assetTable
        },
        async getOrderInfo() {
            const response = await axios.get(
                `${this.$apiBaseUrl}/order/getorderInfo?orderid=${this.orderId}`
            )
            this.orderData = response.data
            console.log(this.orderData)
            this.updateArrowKey += 1
        },
        async getOrderShoeBatchInfo(orderId, orderShoeId, color) {
            const response = await axios.get(`${this.$apiBaseUrl}/order/getordershoesizetotal`, {
                params: {
                    orderid: orderId,
                    ordershoeid: orderShoeId,
                    color: color
                }
            })
            this.orderProduceInfo = response.data
        },
        async getAllShoeBomInfo() {
            const response = await axios.get(
                `${this.$apiBaseUrl}/firstbom/getordershoes?orderid=${this.orderId}`
            )
            this.testTableData = response.data
            this.tableWholeFilter()
        },
        async getBOMDetails(row) {
            const response = await axios.get(`${this.$apiBaseUrl}/firstbom/getbomdetails`, {
                params: {
                    orderid: this.orderData.orderId,
                    ordershoeid: row.orderShoeRid,
                    color: row.color
                }
            })
            this.bomPreviewData = response.data.bomData
            this.previewBomId = response.data.bomId
        },

        async handleGenerate(row) {
            await this.getNewBomId()
            this.createVis = true
            this.getOrderShoeBatchInfo(this.orderData.orderId, row.orderShoeRid, row.color)
            this.currentBomShoeId = row.orderShoeRid
            this.currentColor = row.color
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
        async openEditDialog(row) {
            const loadingInstance = this.$loading({
                lock: true,
                text: '等待中，请稍后...',
                background: 'rgba(0, 0, 0, 0.7)'
            })
            await this.getBOMDetails(row)

            this.editBomId = this.previewBomId
            await this.getOrderShoeBatchInfo(this.orderData.orderId, row.orderShoeRid, row.color)
            loadingInstance.close()
            this.editBomId = this.previewBomId
            this.editVis = true
            this.editBomData = this.bomPreviewData
            this.currentBomShoeId = row.orderShoeRid
            this.currentColor = row.color
        },
        async openPreviewDialog(row) {
            await this.getOrderShoeBatchInfo(this.orderData.orderId, row.orderShoeRid, row.color)
            await this.getBOMDetails(row)
            this.updateKey += 1

            // Replace this with the actual logic to get the file

            this.isPreviewDialogVisible = true
        },
        openIssueDialog() {
            this.isFinalBOM = true
            // Filter testTableData to find rows where all colors have firstBomStatus as '已提交'
            this.unIssueBOMData = this.testTableData.filter((row) => {
                // Check if any of the colors in typeInfos have '已提交' status
                return row.typeInfos.every((typeInfo) => typeInfo.firstBomStatus === '已提交')
            })
        },
        closePreviewDialog() {
            this.isPreviewDialogVisible = false
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
        async openNewMaterialDialog() {
            this.newMaterialVis = true
            this.materialAddfinished = true
            await this.getAllMaterialList()
            this.materialAddfinished = false
        },
        confirmNewMaterialAdd(type) {
            if (this.materialSelectRow === null) {
                ElMessageBox.alert('材料不能为空！', '警告', { confirmButtonText: '确认' })
                return
            }
            console.log('nosize')
            if (type === 0) {
                this.bomTestData.push({
                    materialName: this.materialSelectRow.materialName,
                    materialType: this.materialSelectRow.materialType,
                    warehouseName: this.materialSelectRow.warehouseName,
                    supplierName: this.materialSelectRow.supplierName,
                    materialModel: this.materialSelectRow.materialModel,
                    materialSpecification: this.materialSelectRow.materialSpecification,
                    color: '',
                    unit: this.materialSelectRow.unit,
                    materialCategory: this.materialSelectRow.materialCategory,
                    comment: ''
                })
            } else {
                this.editBomData.push({
                    materialName: this.materialSelectRow.materialName,
                    materialType: this.materialSelectRow.materialType,
                    warehouseName: this.materialSelectRow.warehouseName,
                    supplierName: this.materialSelectRow.supplierName,
                    materialModel: this.materialSelectRow.materialModel,
                    materialSpecification: this.materialSelectRow.materialSpecification,
                    color: '',
                    unit: this.materialSelectRow.unit,
                    materialCategory: this.materialSelectRow.materialCategory,
                    comment: ''
                })
            }

            this.newMaterialVis = false
            this.materialTypeSearch = ''
            this.materialSearch = ''
            this.factorySearch = ''
        },
        async saveUnsubmittedBOM() {
            // Validate that all existing rows have non-empty fields
            for (const row of this.bomTestData) {
                if (!row.materialType || !row.materialName) {
                    this.$message({
                        type: 'warning',
                        message: '请填写所有字段'
                    })
                    return
                }
            }
            const uniqueRows = new Set()
            for (const row of this.bomTestData) {
                const rowIdentifier = `${row.materialType}-${row.materialName}-${row.color}-${row.supplierName}`
                if (uniqueRows.has(rowIdentifier)) {
                    this.$message({
                        type: 'warning',
                        message: '存在重复的物料条目'
                    })
                    return
                }
                uniqueRows.add(rowIdentifier)
            }
            const loadingInstance = this.$loading({
                lock: true,
                text: '等待中，请稍后...',
                background: 'rgba(0, 0, 0, 0.7)'
            })
            const response = await axios.post(`${this.$apiBaseUrl}/firstbom/savebom`, {
                orderId: this.orderData.orderId,
                orderShoeId: this.currentBomShoeId,
                bomData: this.bomTestData,
                bomId: this.newBomId,
                color: this.currentColor
            })
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
            this.getAllShoeBomInfo()
        },
        async editUnsubmittedBOM() {
            // Validate that all existing rows have non-empty fields
            for (const row of this.editBomData) {
                if (!row.materialType || !row.materialName) {
                    this.$message({
                        type: 'warning',
                        message: '请填写所有字段'
                    })
                    return
                }
            }
            const uniqueRows = new Set()
            for (const row of this.editBomData) {
                const rowIdentifier = `${row.materialType}-${row.materialName}-${row.color}-${row.supplierName}`
                if (uniqueRows.has(rowIdentifier)) {
                    this.$message({
                        type: 'warning',
                        message: '存在重复的物料条目'
                    })
                    return
                }
                uniqueRows.add(rowIdentifier)
            }
            const loadingInstance = this.$loading({
                lock: true,
                text: '等待中，请稍后...',
                background: 'rgba(0, 0, 0, 0.7)'
            })
            const response = await axios.post(`${this.$apiBaseUrl}/firstbom/editbom`, {
                orderId: this.orderData.orderId,
                orderShoeId: this.currentBomShoeId,
                bomData: this.editBomData,
                bomId: this.editBomId,
                color: this.currentColor
            })
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
            this.editVis = false
            this.getAllShoeBomInfo()
        },
        async submitBOM(row) {
            this.$confirm('确定提交此BOM表吗？', '提示', {
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                type: 'warning'
            })
                .then(async () => {
                    const loadingInstance = this.$loading({
                        lock: true,
                        text: '等待中，请稍后...',
                        background: 'rgba(0, 0, 0, 0.7)'
                    })
                    const response = await axios.post(`${this.$apiBaseUrl}/firstbom/submitbom`, {
                        orderId: this.orderData.orderId,
                        orderShoeId: row.orderShoeRid,
                        color: row.color
                    })
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
                    this.getAllShoeBomInfo()
                })
                .catch(() => {
                    this.$message({
                        type: 'info',
                        message: '已取消提交'
                    })
                })
        },
        async issueBOMs(selectedShoe) {
            const loadingInstance = this.$loading({
                lock: true,
                text: '等待中，请稍后...',
                background: 'rgba(0, 0, 0, 0.7)'
            })
            const response = await axios.post(`${this.$apiBaseUrl}/firstbom/issueboms`, {
                orderId: this.orderData.orderId,
                orderShoeIds: selectedShoe.map((shoe) => shoe.inheritId),
                colors: selectedShoe.map((shoe) => shoe.typeInfos.map((typeInfo) => typeInfo.color))
            })
            loadingInstance.close()
            if (response.status !== 200) {
                this.$message({
                    type: 'error',
                    message: '下发失败'
                })
                return
            }
            this.$message({
                type: 'success',
                message: '下发成功'
            })
            this.isFinalBOM = false
            this.getAllShoeBomInfo()
        },
        confirmBOMSave() {
            this.$confirm('确定保存此BOM表吗？', '提示', {
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                type: 'warning'
            })
                .then(() => {
                    this.saveUnsubmittedBOM()
                })
                .catch(() => {
                    this.$message({
                        type: 'info',
                        message: '已取消保存'
                    })
                })
        },
        confirmBOMEdit() {
            this.$confirm('确定保存此BOM表吗？', '提示', {
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                type: 'warning'
            })
                .then(() => {
                    this.editUnsubmittedBOM()
                })
                .catch(() => {
                    this.$message({
                        type: 'info',
                        message: '已取消保存'
                    })
                })
        },
        confirmBOMIssue() {
            this.$confirm('确定下发选定BOM表吗？', '提示', {
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                type: 'warning'
            })
                .then(() => {
                    this.issueBOMs(this.selectedShoe)
                })
                .catch(() => {
                    this.$message({
                        type: 'info',
                        message: '已取消下发'
                    })
                })
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
        handleShoeSelectionChange(selection) {
            this.selectedShoe = selection
            console.log(this.selectedShoe)
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
        arraySpanMethod({ row, column, rowIndex, columnIndex }) {
            if (columnIndex === 0) {
                if (rowIndex > 0 && row.color === this.orderProduceInfo[rowIndex - 1].color) {
                    return [0, 0]
                }
                let rowspan = 1
                for (let i = rowIndex + 1; i < this.orderProduceInfo.length; i++) {
                    if (this.orderProduceInfo[i].color === row.color) {
                        rowspan++
                    } else {
                        break
                    }
                }
                return [rowspan, 1]
            }
            if (column.property === 'total') {
                let firstOccurrenceIndex = rowIndex
                for (let i = rowIndex - 1; i >= 0; i--) {
                    if (this.orderProduceInfo[i].color === row.color) {
                        firstOccurrenceIndex = i
                    } else {
                        break
                    }
                }
                if (rowIndex !== firstOccurrenceIndex) {
                    return [0, 0]
                }
                let rowspan = 1
                for (let i = firstOccurrenceIndex + 1; i < this.orderProduceInfo.length; i++) {
                    if (this.orderProduceInfo[i].color === row.color) {
                        rowspan++
                    } else {
                        break
                    }
                }
                return [rowspan, 1]
            }
        },
        categroryFormatter(row) {
            if (row.materialCategory == 0) {
                return '无配码'
            } else {
                return '有配码'
            }
        },
        downloadProductionOrderList() {
            window.open(
                `${this.$apiBaseUrl}/devproductionorder/download?ordershoerid=${this.currentBomShoeId}&orderid=${this.orderData.orderId}`
            )
        },
        downloadProductionOrder() {
            window.open(
                `${this.$apiBaseUrl}/orderimport/downloadorderdoc?orderrid=${this.orderData.orderId}&filetype=0`
            )
        }
    }
}
</script>

<style scoped>
/* Add your styles here */
</style>
