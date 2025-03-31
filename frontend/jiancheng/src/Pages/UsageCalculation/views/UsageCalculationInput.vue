<template>
    <el-container direction="vertical">
        <el-header height="">
            <AllHeader></AllHeader>
        </el-header>
        <el-main style="overflow-x: hidden">
            <el-row :gutter="20" style="text-align: center">
                <el-col :span="24" :offset="0" style="font-size: xx-large; text-align: center"
                    >材料用量填写</el-col
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
                                <el-descriptions-item label="订单预计截止日期" align="center">{{
                                    orderData.deadlineTime
                                }}</el-descriptions-item>
                                <el-descriptions-item label="退回订单" align="center">
                                    <el-button
                                        type="danger"
                                        size="default"
                                        @click="openReturnOrderDialog"
                                        >退回流程</el-button
                                    >
                                </el-descriptions-item>
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
                            :suffix-icon="searchIcon"
                            clearable
                            @input="tableWholeFilter"
                        ></el-input>
                    </div>
                </el-col>
            </el-row>

            <el-row :gutter="20" style="margin-top: 20px">
                <el-col :span="24" :offset="0">
                    <el-table
                        :data="testTableFilterData"
                        border
                        style="height: 400px"
                        :default-expand-all="true"
                    >
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
                                    <el-table-column label="操作" align="center" width="400">
                                        <template #default="scope">
                                            <div v-if="role == 1">
                                                <el-button
                                                    type="primary"
                                                    @click="openEditDialog(scope.row)"
                                                    >编辑</el-button
                                                >
                                            </div>
                                            <div v-else>
                                                <el-button
                                                    v-if="
                                                        parentScope.row.status.includes(
                                                            '面料单位用量计算'
                                                        ) &&
                                                        scope.row.firstBomStatus === '等待用量填写'
                                                    "
                                                    type="primary"
                                                    @click="handleGenerate(scope.row)"
                                                    >填写</el-button
                                                >
                                                <div
                                                    v-else-if="
                                                        scope.row.firstBomStatus ===
                                                            '用量填写已下发' ||
                                                        scope.row.firstBomStatus === 'BOM完成'
                                                    "
                                                >
                                                    <el-button
                                                        type="primary"
                                                        @click="openPreviewDialog(scope.row)"
                                                        >查看</el-button
                                                    >
                                                    <el-button
                                                        type="success"
                                                        @click="downloadfirstBOM(scope.row)"
                                                    >
                                                        下载一次BOM
                                                    </el-button>
                                                </div>
                                                <div
                                                    v-else-if="
                                                        scope.row.firstBomStatus === '已提交' ||
                                                        scope.row.firstBomStatus ===
                                                            '用量填写已提交'
                                                    "
                                                >
                                                    <el-button
                                                        type="primary"
                                                        @click="openPreviewDialog(scope.row)"
                                                        >查看</el-button
                                                    >
                                                </div>

                                                <div
                                                    v-else-if="
                                                        parentScope.row.status.includes(
                                                            '面料单位用量计算'
                                                        ) &&
                                                        scope.row.firstBomStatus ===
                                                            '用量填写已保存'
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
                                                        type="normal"
                                                        @click="handleCopyToOtherColor(scope.row)"
                                                        >复制到其他颜色</el-button
                                                    >
                                                    <el-button
                                                        type="warning"
                                                        @click="submitBOMUsage(scope.row)"
                                                        >提交</el-button
                                                    >
                                                </div>
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
                :title="`一次BOM用量填写 ${newBomId}`"
                v-model="createVis"
                width="100%"
                @close="handleGenerateClose"
                fullscreen
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
                    <!-- <el-descriptions-item label="生产订单" align="center"><el-button type="primary" size="default"
                            @click="downloadProductionOrder">查看生产订单</el-button>
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
                            <el-table-column
                                v-for="column in filteredColumns"
                                :key="column.prop"
                                :prop="column.prop"
                                :label="column.label"
                            ></el-table-column>
                            <el-table-column prop="total" label="合计" />
                        </el-table>
                    </el-row>
                    <el-row>
                        <el-button type="primary" size="default" @click="confirmLoadPastUsage"
                            >加载过往该鞋型用量</el-button
                        >
                    </el-row>
                    <el-row style="margin-top: 10px">
                        <el-table :data="bomTestData" border>
                            <el-table-column prop="materialType" label="材料类型">
                            </el-table-column>
                            <!-- <el-table-column prop="materialDetailType" label="材料二级类型"></el-table-column> -->
                            <el-table-column prop="supplierName" label="厂家名称"></el-table-column>
                            <el-table-column prop="materialName" label="材料名称">
                            </el-table-column>
                            <el-table-column prop="materialModel" label="材料型号" />
                            <el-table-column prop="materialSpecification" label="材料规格">
                            </el-table-column>
                            <el-table-column prop="color" label="颜色"> </el-table-column>
                            <el-table-column prop="unit" label="单位"> </el-table-column>
                            <el-table-column prop="unitUsage" label="单位用量">
                                <template #default="scope">
                                    <el-input-number
                                        v-if="scope.row.materialCategory == 0"
                                        v-model="scope.row.unitUsage"
                                        :step="0.001"
                                        size="default"
                                        @change="calculateApprovalUsage(scope.row)"
                                    />
                                    <el-button
                                        v-else-if="scope.row.materialCategory == 1"
                                        type="primary"
                                        size="default"
                                        @click="openSizeDialog(scope.row, scope.$index)"
                                        >尺码用量填写</el-button
                                    >
                                </template>
                            </el-table-column>
                            <el-table-column prop="approvalUsage" label="核定用量">
                                <template #default="scope">
                                    <el-input-number
                                        v-if="scope.row.materialCategory == 0"
                                        v-model="scope.row.approvalUsage"
                                        :step="0.001"
                                        size="default"
                                    />
                                </template>
                            </el-table-column>
                            <el-table-column prop="remark" label="备注" />
                        </el-table>
                    </el-row>
                </div>

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
                    <!-- <el-descriptions-item label="生产订单" align="center"><el-button type="primary" size="default"
                            @click="downloadProductionOrder">查看生产订单</el-button>
                    </el-descriptions-item> -->
                </el-descriptions>
                <div style="height: 600px; overflow-y: scroll; overflow-x: hidden">
                    <el-row :gutter="20" style="margin-bottom: 20px">
                        <el-col :span="24">
                            <el-table
                                :data="orderProduceInfo"
                                border
                                style="width: 100%"
                                :span-method="arraySpanMethod"
                            >
                                <el-table-column
                                    v-for="column in filteredColumns"
                                    :key="column.prop"
                                    :prop="column.prop"
                                    :label="column.label"
                                ></el-table-column>
                                <el-table-column prop="total" label="合计" />
                            </el-table>
                        </el-col>
                    </el-row>
                    <el-row :gutter="20" style="margin-bottom: 20px">
                        <el-col :span="24">
                            <el-table :data="bomPreviewData" border style="width: 100%">
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
                    <!-- <el-descriptions-item label="生产订单" align="center"><el-button type="primary" size="default"
                            @click="downloadProductionOrder">查看生产订单</el-button>
                    </el-descriptions-item> -->
                </el-descriptions>
                <div style="height: 400px; overflow-y: scroll; overflow-x: hidden">
                    <el-row :gutter="20" style="margin-bottom: 20px">
                        <el-col :span="24">
                            <el-table
                                :data="unIssueBOMData"
                                border
                                style="height: 400px"
                                @selection-change="handleShoeSelectionChange"
                                :default-expand-all="true"
                            >
                                <el-table-column type="selection" width="55"></el-table-column>
                                <el-table-column type="expand">
                                    <template #default="parentScope">
                                        <el-table :data="parentScope.row.typeInfos" border>
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
                                                    <div
                                                        v-if="
                                                            parentScope.row.status.includes(
                                                                '面料单位用量计算'
                                                            ) &&
                                                            scope.row.firstBomStatus ===
                                                                '等待用量填写'
                                                        "
                                                    >
                                                        <el-button
                                                            type="primary"
                                                            @click="handleGenerate(scope.row)"
                                                            >填写</el-button
                                                        >
                                                    </div>

                                                    <el-button
                                                        v-else-if="
                                                            scope.row.firstBomStatus === '已下发' ||
                                                            scope.row.firstBomStatus === '已提交' ||
                                                            scope.row.firstBomStatus ===
                                                                '用量填写已提交' ||
                                                            scope.row.firstBomStatus === 'BOM完成'
                                                        "
                                                        type="primary"
                                                        @click="openPreviewDialog(scope.row)"
                                                        >查看</el-button
                                                    >
                                                    <div
                                                        v-else-if="
                                                            parentScope.row.status.includes(
                                                                '面料单位用量计算'
                                                            ) &&
                                                            scope.row.firstBomStatus ===
                                                                '用量填写已保存'
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
                                                            @click="submitBOMUsage(scope.row)"
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
            <el-dialog
                title="尺码数量填写"
                v-model="isSizeDialogVisible"
                width="60%"
                :close-on-click-modal="false"
            >
                <el-table :data="sizeData" border stripe>
                    <el-table-column prop="size" label="尺码"></el-table-column>
                    <el-table-column prop="approvalAmount" label="采购数量">
                        <template #default="scope">
                            <el-input-number
                                v-if="createEditSymbol == 0"
                                v-model="scope.row.approvalAmount"
                                :min="0"
                                size="small"
                            />
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
                title="退回流程"
                v-model="isRevertDialogVisable"
                width="20%"
                :close-on-click-modal="false"
            >
                <span>
                    <span>退回流程</span>
                    <el-row :gutter="20">
                        <el-col :span="24" :offset="0">
                            <el-form
                                :model="revertForm"
                                :rules="revertRules"
                                ref="revertForm"
                                label-width="100px"
                            >
                                <el-form-item label="退回至状态" prop="revertToStatus">
                                    <el-select
                                        v-model="revertForm.revertToStatus"
                                        placeholder="请选择退回至状态"
                                        clearable
                                        @change="handleStatusSelect"
                                    >
                                        <el-option
                                            v-for="item in revertStatusReasonOptions"
                                            :key="item.status"
                                            :label="item.statusName"
                                            :value="item.status"
                                        ></el-option>
                                    </el-select>
                                </el-form-item>
                                <el-form-item label="需要中间流程" prop="isNeedMiddleProcess">
                                    <el-radio-group v-model="revertForm.isNeedMiddleProcess">
                                        <el-radio label="1">是</el-radio>
                                        <el-radio label="0">否</el-radio>
                                    </el-radio-group>
                                </el-form-item>
                                <el-form-item label="退回原因" prop="revertReason">
                                    <el-input
                                        v-model="revertForm.revertReason"
                                        :rows="4"
                                        placeholder="请输入退回原因"
                                        disabled
                                    ></el-input>
                                </el-form-item>
                                <el-form-item label="退回详细原因" prop="revertDetail">
                                    <el-input
                                        v-model="revertForm.revertDetail"
                                        type="textarea"
                                        :rows="4"
                                        placeholder="请输入退回原因"
                                    ></el-input>
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
        </el-main>
    </el-container>
</template>

<script>
import AllHeader from '@/components/AllHeader.vue'
import Arrow from '@/components/OrderArrowView.vue'
import { Search } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import axios from 'axios'
import { getShoeSizesName } from '@/Pages/utils/getShoeSizesName'

export default {
    components: {
        AllHeader,
        Arrow
    },
    props: ['orderId'],
    computed: {
        searchIcon() {
            return Search
        },
        filteredColumns() {
            return this.shoeSizeColumns.filter((column) =>
                this.orderProduceInfo.some(
                    (row) =>
                        row[column.prop] !== undefined &&
                        row[column.prop] !== null &&
                        row[column.prop] !== 0
                )
            )
        }
    },
    data() {
        return {
            role: localStorage.getItem('role'),
            getShoeSizesName,
            shoeSizeColumns: [],
            createEditSymbol: 0,
            sizeData: [],
            currentSizeData: [],
            currentColor: '',
            currentSizeIndex: 0,
            isSizeDialogVisible: false,
            selectedShoe: '',
            unIssueBOMData: [],
            updateKey: 0,
            editVis: false,
            editBomId: '',
            previewBomId: '',
            newBomId: '',
            currentBomShoeId: '',
            materialSelectRow: null,
            materialAddfinished: false,
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
                { materialName: '黑色超软镜面PU', factoryName: '一一鞋材' },
                { materialName: '黑色超软镜面PU', factoryName: '深源皮革' },
                { materialName: '黑色超软镜面PU', factoryName: '嘉泰皮革' }
                // Add more options here
            ],
            isPreviewDialogVisible: false,
            selectedFile: null,
            inheritIdSearch: '',
            isFinalBOM: false,
            orderProduceInfo: [],
            defaultUnitOptions: [
                { value: '米', label: '米' },
                { value: '个', label: '个' },
                { value: '双', label: '双' },
                { value: '条', label: '条' }
            ],
            isRevertDialogVisable: false,
            revertForm: {
                revertToStatus: '',
                revertReason: '',
                revertDetail: '',
                isNeedMiddleProcess: '0'
            }
        }
    },
    async mounted() {
        this.$setAxiosToken()
        await this.getOrderInfo()
        this.getAllShoeBomInfo()
        this.getAllColorOptions()
        this.getAllDepartmentOptions()
        await this.getAllRevertStatusReasonOptions()
    },

    methods: {
        async getAllRevertStatusReasonOptions() {
            const response = await axios.get(
                `${this.$apiBaseUrl}/revertorder/getrevertorderreason`,
                { params: { orderId: this.orderData.orderDBId, flow: 1 } }
            )
            this.revertStatusReasonOptions = response.data
        },
        async getBatchTypeList() {
            const response = await axios.get(`${this.$apiBaseUrl}/shoe/getshoebatchinfotype`, {})
            this.batchInfoTypeList = response.data
        },
        async getAllDepartmentOptions() {
            const response = await this.$axios.get(`${this.$apiBaseUrl}/general/getalldepartments`)
            this.departmentOptions = response.data
        },
        async getAllColorOptions() {
            const response = await this.$axios.get(`${this.$apiBaseUrl}/general/allcolors`)
            this.colorOptions = response.data
        },
        async getMaterialFilterData() {
            this.materialAddfinished = true
            const response = await this.$axios.get(
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
            const response = await this.$axios.get(
                `${this.$apiBaseUrl}/logistics/getmaterialtypeandname`
            )
            this.assetTable = response.data
            this.assetFilterTable = this.assetTable
        },
        async getOrderInfo() {
            const response = await this.$axios.get(
                `${this.$apiBaseUrl}/order/getorderInfo?orderid=${this.$props.orderId}`
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
            this.shoeSizeColumns = await this.getShoeSizesName(this.$props.orderId)
        },
        async getAllShoeBomInfo() {
            const response = await axios.get(
                `${this.$apiBaseUrl}/usagecalculation/getallboms?orderid=${this.$props.orderId}`
            )
            this.testTableData = response.data
            this.tableWholeFilter()
        },
        async getBOMDetails(row) {
            const response = await axios.get(
                `${this.$apiBaseUrl}/usagecalculation/getshoebomitems`,
                {
                    params: {
                        bomrid: row.firstBomId
                    }
                }
            )
            this.bomPreviewData = response.data
            this.bomTestData = response.data
        },

        async handleGenerate(row) {
            this.newBomId = row.firstBomId
            this.createVis = true
            await this.getOrderShoeBatchInfo(this.orderData.orderId, row.orderShoeRid, row.color)
            await this.getBOMDetails(row)
            if (this.orderProduceInfo[0]) {
                console.log(this.orderProduceInfo[0])
                this.bomTestData.forEach((item) => {
                    if (item.materialCategory === 1) {
                        let totalApprovalAmount = 0

                        item.sizeInfo.forEach((sizeRow) => {
                            let sizeKey = sizeRow.size
                            let trueKey = this.shoeSizeColumns.find(
                                (column) => column.label === sizeKey
                            ).prop
                            if (this.orderProduceInfo[0][trueKey] !== undefined) {
                                sizeRow.approvalAmount = this.orderProduceInfo[0][trueKey]
                                console.log(sizeRow.approvalAmount)
                                totalApprovalAmount += this.orderProduceInfo[0][trueKey]
                            }
                        })
                        console.log(totalApprovalAmount)
                        // Update the approvalUsage with the total approval amount
                        item.approvalUsage = totalApprovalAmount
                    }
                })
            }
            this.currentBomShoeId = row.orderShoeRid
            this.createEditSymbol = 0
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
            await this.getOrderShoeBatchInfo(this.orderData.orderId, row.orderShoeRid, row.color)
            loadingInstance.close()
            this.newBomId = row.firstBomId
            this.createVis = true
            this.currentBomShoeId = row.orderShoeRid
            this.currentColor = row.color
            this.createEditSymbol = 0
        },
        async openPreviewDialog(row) {
            await this.getOrderShoeBatchInfo(this.orderData.orderId, row.orderShoeRid, row.color)
            await this.getBOMDetails(row)
            this.previewBomId = row.firstBomId
            this.createEditSymbol = 1
            this.updateKey += 1
            this.currentColor = row.color
            this.currentBomShoeId = row.orderShoeRid

            // Replace this with the actual logic to get the file

            this.isPreviewDialogVisible = true
        },
        openIssueDialog() {
            this.isFinalBOM = true
            // Filter testTableData to find rows where all colors have firstBomStatus as '已提交'
            this.unIssueBOMData = this.testTableData.filter((row) => {
                // Check if any of the colors in typeInfos have '已提交' status
                return row.typeInfos.every(
                    (typeInfo) => typeInfo.firstBomStatus === '用量填写已提交'
                )
            })
        },
        openSizeDialog(row, index) {
            this.sizeData = row.sizeInfo
            console.log(this.sizeData)
            this.isSizeDialogVisible = true
            this.currentSizeIndex = index
        },
        confirmSizeAmount() {
            this.bomTestData[this.currentSizeIndex].sizeInfo = this.sizeData
            const totalApprovalAmount = this.sizeData.reduce(
                (total, item) => total + item.approvalAmount,
                0
            )
            this.bomTestData[this.currentSizeIndex].approvalUsage = totalApprovalAmount
            this.isSizeDialogVisible = false
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
            this.materialAddfinished = false
            await this.getAllMaterialList()
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
        async saveUsageBOM() {
            // Validate that all existing rows have non-empty fields
            for (const row of this.bomTestData) {
                if (row.approvalUsage === null || row.approvalUsage === undefined) {
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
                `${this.$apiBaseUrl}/usagecalculation/savebomusage`,
                {
                    bomRid: this.newBomId,
                    bomItems: this.bomTestData
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
            this.getAllShoeBomInfo()
        },
        async submitBOMUsage(row) {
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
                    const response = await this.$axios.post(
                        `${this.$apiBaseUrl}/usagecalculation/submitbomusage`,
                        {
                            bomRid: row.firstBomId
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
            if (selectedShoe.length == 0) {
                ElMessage.error('未选中鞋型')
                return
            }
            const loadingInstance = this.$loading({
                lock: true,
                text: '等待中，请稍后...',
                background: 'rgba(0, 0, 0, 0.7)'
            })
            const response = await this.$axios.post(
                `${this.$apiBaseUrl}/usagecalculation/issuebomusage`,
                {
                    orderId: this.orderData.orderId,
                    orderShoeIds: selectedShoe.map((shoe) => shoe.inheritId),
                    colors: selectedShoe.map((shoe) =>
                        shoe.typeInfos.map((typeInfo) => typeInfo.color)
                    )
                }
            )
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
                    this.saveUsageBOM()
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
        handleCopyToOtherColor(row) {
            console.log(row)
            this.$confirm('确定复制到其他颜色吗？', '提示', {
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                type: 'warning'
            })
                .then(async () => {
                    const response = await axios.get(
                        `${this.$apiBaseUrl}/usagecalculation/copyusagetoallcheck`,
                        {
                            params: {
                                orderShoeTypeId: row.orderShoeTypeId
                            }
                        }
                    )
                    const checkResult = response.data.checkResult
                    const reason = response.data.reason
                    if (checkResult == 0) {
                        this.$confirm(reason, '提示', {
                            confirmButtonText: '确定',
                            cancelButtonText: '取消',
                            type: 'success'
                        }).then(async () => {
                            const response = await axios.post(
                                `${this.$apiBaseUrl}/usagecalculation/copyusagetoall`,
                                {
                                    orderShoeTypeId: row.orderShoeTypeId
                                }
                            )
                            if (response.status !== 200) {
                                this.$message({
                                    type: 'error',
                                    message: '复制失败'
                                })
                                return
                            }
                            this.$message({
                                type: 'success',
                                message: '复制成功'
                            })
                            this.getAllShoeBomInfo()
                        })
                    } else if (checkResult == 1) {
                        this.$confirm(reason, '提示', {
                            confirmButtonText: '确定',
                            cancelButtonText: '取消',
                            type: 'warning'
                        })
                            .then(async () => {
                                const response = await axios.post(
                                    `${this.$apiBaseUrl}/usagecalculation/copyusagetoall`,
                                    {
                                        orderShoeTypeId: row.orderShoeTypeId
                                    }
                                )
                                if (response.status !== 200) {
                                    this.$message({
                                        type: 'error',
                                        message: '复制失败'
                                    })
                                    return
                                }
                                this.$message({
                                    type: 'success',
                                    message: '复制成功'
                                })
                                this.getAllShoeBomInfo()
                            })
                            .catch(() => {
                                this.$message({
                                    type: 'info',
                                    message: '已取消复制'
                                })
                            })
                    }
                })
                .catch(() => {
                    this.$message({
                        type: 'info',
                        message: '已取消复制'
                    })
                })
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
        calculateApprovalUsage(row) {
            if (row.unitUsage) {
                row.approvalUsage = (row.unitUsage * this.orderProduceInfo[0].total).toFixed(3)
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
        },
        downloadfirstBOM(row) {
            window.open(
                `${this.$apiBaseUrl}/firstbom/download?ordershoerid=${row.orderShoeRid}&orderid=${this.orderData.orderId}`
            )
        },
        openReturnOrderDialog() {
            this.revertForm.revertToStatus = ''
            this.revertForm.revertDetail = ''
            this.revertForm.revertReason = ''
            this.revertForm.isNeedMiddleProcess = '0'
            this.isRevertDialogVisable = true
        },
        saveRevertForm() {
            this.$confirm(
                `确定退回此订单吗？退回至 ${this.revertForm.revertToStatus}, 原因是 ${this.revertForm.revertReason}`,
                '提示',
                {
                    confirmButtonText: '确定',
                    cancelButtonText: '取消',
                    type: 'warning'
                }
            )
                .then(() => {
                    this.revertOrder()
                })
                .catch(() => {
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
                const response = await axios.post(
                    `${this.$apiBaseUrl}/revertorder/revertordersave`,
                    {
                        orderId: this.orderData.orderDBId,
                        flow: 1,
                        revertToStatus: this.revertForm.revertToStatus,
                        revertReason: this.revertForm.revertReason,
                        revertDetail: this.revertForm.revertDetail,
                        isNeedMiddleProcess: this.revertForm.isNeedMiddleProcess
                    }
                )
                if (response.status === 200) {
                    this.$message({
                        type: 'success',
                        message: '退回成功'
                    })
                    this.isRevertDialogVisable = false
                    this.getAllShoeListInfo()
                } else {
                    this.$message({
                        type: 'error',
                        message: '退回失败'
                    })
                }
            })
        },
        handleStatusSelect() {
            //when select status, make the revertReason to be the reason field of the selected status
            const selectedStatus = this.revertStatusReasonOptions.find(
                (item) => item.status === this.revertForm.revertToStatus
            )
            this.revertForm.revertReason = selectedStatus.reason
        },
        confirmLoadPastUsage() {
            this.$confirm('确定加载历史用量吗？', '提示', {
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                type: 'warning'
            })
                .then(() => {
                    this.loadPastUsageData()
                })
                .catch(() => {
                    this.$message({
                        type: 'info',
                        message: '已取消加载'
                    })
                })
        },
        async loadPastUsageData() {
            try {
                const response = await axios.get(
                    `${this.$apiBaseUrl}/usagecalculation/loadpastusage`,
                    {
                        params: {
                            currentBomRid: this.newBomId
                        }
                    }
                )
                if (response.status === 200) {
                    if (response.data.status === 'failed') {
                        this.$message({
                            type: 'warning',
                            message: '没有历史用量数据'
                        })
                        return
                    }
                    this.$message({
                        type: 'success',
                        message: '加载成功'
                    })
                    const pastUsageData = response.data.data
                    // match the material_name, material_model, material_specification, and color with the current BOM data
                    this.bomTestData.forEach((item) => {
                        const matchedData = pastUsageData.find(
                            (data) =>
                                data.materialName === item.materialName &&
                                data.materialSpecification === item.materialSpecification &&
                                data.color === item.color
                        )
                        if (matchedData) {
                            item.unitUsage = matchedData.unitUsage
                            item.approvalUsage = item.unitUsage * this.orderProduceInfo[0].total
                            if (item.materialCategory === 1) {
                                let totalApprovalAmount = 0

                                item.sizeInfo.forEach((sizeRow) => {
                                    let sizeKey = sizeRow.size
                                    let trueKey = this.shoeSizeColumns.find(
                                        (column) => column.label === sizeKey
                                    ).prop
                                    if (this.orderProduceInfo[0][trueKey] !== undefined) {
                                        sizeRow.approvalAmount = this.orderProduceInfo[0][trueKey]
                                        console.log(sizeRow.approvalAmount)
                                        totalApprovalAmount += this.orderProduceInfo[0][trueKey]
                                    }
                                })
                                console.log(totalApprovalAmount)
                                // Update the approvalUsage with the total approval amount
                                item.approvalUsage = totalApprovalAmount
                            }
                        }
                    })
                } else {
                    this.$message({
                        type: 'error',
                        message: '加载失败'
                    })
                }
            } catch (error) {
                console.error('Error loading past usage data:', error)
                this.$message({
                    type: 'error',
                    message: '加载失败'
                })
            }
        }
    }
}
</script>

<style scoped>
/* Add your styles here */
</style>
