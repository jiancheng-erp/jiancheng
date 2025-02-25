<template>
    <el-container direction="vertical">
        <el-header height="">
            <AllHeader></AllHeader>
        </el-header>
        <el-main style="overflow-x: hidden">
            <el-row :gutter="20" style="text-align: center">
                <el-col :span="24" :offset="0" style="font-size: xx-large; text-align: center">工艺单信息</el-col>
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
                        工厂型号搜索：<el-input v-model="inheritIdSearch" placeholder="" size="default"
                            :suffix-icon="SearchIcon" clearable @input="tableWholeFilter"></el-input>
                    </div>
                </el-col>
            </el-row>

            <el-row :gutter="20" style="margin-top: 20px">
                <el-col :span="24" :offset="0">
                    <el-table :data="testTableFilterData" border style="height: 400px">
                        <el-table-column type="expand">
                            <template #default="scope">
                                <el-table :data="scope.row.typeInfos" border>
                                    <el-table-column prop="color" label="颜色"></el-table-column>
                                    <el-table-column label="鞋图" align="center">
                                        <template #default="scope">
                                            <el-image style="width: 150px; height: 100px" :src="scope.row.image"
                                                fit="contain" />
                                        </template>
                                    </el-table-column>
                                    <el-table-column prop="firstBomId" label="一次BOM表"></el-table-column>
                                    <el-table-column prop="firstPurchaseOrderId" label="一次采购订单"></el-table-column>
                                    <el-table-column prop="secondBomId" label="二次BOM表"></el-table-column>
                                    <el-table-column prop="secondPurchaseOrderId" label="二次采购订单"></el-table-column>
                                </el-table>
                            </template>
                        </el-table-column>
                        <el-table-column prop="inheritId" label="工厂型号" align="center" width="100"></el-table-column>
                        <el-table-column prop="customerId" label="客户型号" align="center"></el-table-column>
                        <el-table-column prop="designer" label="设计员" align="center"></el-table-column>
                        <el-table-column prop="status" label="状态" align="center"></el-table-column>
                        <el-table-column label="操作" align="center">
                            <template #default="scope">
                                <div v-if="scope.row.status === '未上传'">
                                    <el-button v-if="isEditor()" type="primary"
                                        @click="openUploadDialog(scope.row)">创建工艺单</el-button>
                                    <span v-else>工艺单未下发</span>
                                </div>
                                <div v-else-if="scope.row.status === '已上传'">
                                    <el-button v-if="isEditor()" type="primary"
                                        @click="openEditDialog(scope.row)">编辑工艺单</el-button>
                                    <el-button v-if="isEditor()" type="success"
                                        @click="openPreviewDialog(scope.row)">预览工艺单</el-button>
                                </div>
                                <div v-else-if="scope.row.status === '完成用量填写'">
                                    <el-button type="primary" @click="openPreviewDialog(scope.row)">查看</el-button>
                                </div>
                                <div v-else-if="
                                    scope.row.status === '等待用量填写' ||
                                    scope.row.status === '已审核并下发'
                                ">
                                    <el-button type="primary" @click="openPreviewDialog(scope.row)">查看</el-button>
                                </div>
                                <div v-if="scope.row.status === '已审核并下发'">
                                    <el-button type="success"
                                        @click="downloadCraftSheet(scope.row)">下载工艺单EXCEL</el-button>
                                    <el-button type="warning"
                                        @click="downloadProductionInstructionImage(scope.row)">下载备注图片
                                    </el-button>
                                </div>
                            </template>
                        </el-table-column>
                    </el-table></el-col>
            </el-row>
            <el-row :gutter="22" style="margin-top: 10px">
                <el-col :span="6" :offset="20">
                    <el-button v-if="isEditor()" type="primary" size="default" @click="openIssueDialog">下发工艺单（生产指令单）
                    </el-button>
                </el-col>
            </el-row>
            <el-dialog title="正式工艺单下发页面" v-model="isFinalBOM" width="90%">
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
                </el-descriptions>
                <div style="height: 400px; overflow-y: scroll; overflow-x: hidden">
                    <el-row :gutter="20" style="margin-bottom: 20px">
                        <el-col :span="24">
                            <el-table :data="unIssueBOMData" border style="height: 400px"
                                @selection-change="handleShoeSelectionChange">
                                <el-table-column type="selection" width="55"></el-table-column>
                                <el-table-column prop="inheritId" label="工厂型号" align="center"
                                    width="100"></el-table-column>
                                <el-table-column prop="customerId" label="客户型号" align="center"></el-table-column>
                                <el-table-column prop="designer" label="设计员" align="center"></el-table-column>
                                <el-table-column prop="editter" label="调版员" align="center"></el-table-column>
                                <el-table-column label="操作" align="center">
                                    <template #default="scope">
                                        <el-button type="primary" size="default"
                                            @click="openPreviewDialog(scope.row)">查看工艺单（生产指令单）</el-button>
                                    </template>
                                </el-table-column>
                            </el-table>
                        </el-col>
                    </el-row>
                </div>
                <template #footer>
                    <span>
                        <el-button @click="isFinalBOM = false">取消</el-button>
                        <el-button v-if="isEditor()" type="primary"
                            @click="issueBOMs(selectedShoe)">下发选定工艺单（生产指令单）</el-button>
                    </span>
                </template>
            </el-dialog>
            <el-dialog :title="`工艺单创建 ${newcraftSheetId}`" v-model="isProductionOrderCreateDialogVisible" width="90%"
                style="max-height: 700px; overflow-y: scroll">
                <el-descriptions title="工艺单公用信息" border :column="2">
                    <el-descriptions-item label="调版员">
                        <el-input v-model="craftSheetDetail.adjuster" size="default"></el-input>
                    </el-descriptions-item>
                    <el-descriptions-item label="刀模">
                        <el-input v-model="craftSheetDetail.cutDie" size="default"></el-input>
                    </el-descriptions-item>
                    <el-descriptions-item label="生产额外数量要求">
                        <el-input v-model="craftSheetDetail.productionRemark" size="default"></el-input>
                    </el-descriptions-item>
                    <el-descriptions-item label="审核人">
                        <el-input v-model="craftSheetDetail.reviewer" size="default"></el-input>
                    </el-descriptions-item>
                </el-descriptions>
                <el-descriptions title="工艺单特殊工艺信息" border :column="1">
                    <el-descriptions-item label="裁断特殊工艺">
                        <el-input type="textarea" v-model="craftSheetDetail.cuttingSpecialCraft" size="default"
                            maxlength="300" autosize show-word-limit></el-input>
                    </el-descriptions-item>
                    <el-descriptions-item label="针车特殊工艺">
                        <el-input type="textarea" v-model="craftSheetDetail.sewingSpecialCraft" size="default"
                            maxlength="300" autosize show-word-limit></el-input>
                    </el-descriptions-item>
                    <el-descriptions-item label="成型特殊工艺">
                        <el-input type="textarea" v-model="craftSheetDetail.moldingSpecialCraft" size="default"
                            maxlength="300" autosize show-word-limit></el-input>
                    </el-descriptions-item>
                    <el-descriptions-item label="后处理备注">
                        <el-input type="textarea" v-model="craftSheetDetail.postProcessing" maxlength="150" autosize
                            show-word-limit size="default"></el-input>
                    </el-descriptions-item>
                    <el-descriptions-item label="科盛油性胶">
                        <el-input type="textarea" v-model="craftSheetDetail.oilyGlue" maxlength="300" autosize
                            show-word-limit size="default"></el-input>
                    </el-descriptions-item>
                </el-descriptions>
                <el-button type="primary" size="default" @click="openMaterialCraftDialog">打开材料工艺编辑页面</el-button>
                <el-button type="primary" size="default" @click="openCutDieDialog">打开刀模图上传页面</el-button>
                <el-button type="primary" size="default" @click="openPicNoteDialog">打开工艺单图片备注上传页面</el-button>
                <el-button type="primary" size="default" @click="openCraftSheetDialog">打开工艺单备注上传页面</el-button>

                <template #footer>
                    <span>
                        <el-button @click="isProductionOrderCreateDialogVisible = false">取消</el-button>
                        <el-button type="primary" @click="saveProductionInstruction">确认保存</el-button>
                    </span>
                </template>
            </el-dialog>
            <el-dialog title="材料工艺填写及更改页面" v-model="isMaterialCraftVisDialog" width="100%" :close-on-click-modal="false"
                fullscreen style="overflow-y: scroll">
                <el-tabs v-model="activeTab">
                    <!-- Generate tabs from backend-provided tabcolor array -->
                    <el-tab-pane v-for="color in tabcolor" :label="color" :key="color" :name="color">
                        <el-row>
                            <el-col :push="21">
                                <el-button type="success" @click="syncAllMaterials">同步所有材料至所有颜色</el-button>
                            </el-col>
                        </el-row>
                        <el-row :gutter="20">
                            <el-col :span="22" :offset="0">
                                <span>面料：</span>
                                <el-button type="primary" size="default" @click="addMaterial(0)">添加面料</el-button>
                                <el-button type="primary" size="default"
                                    @click="addMaterialByManual(0)">手动添加面料</el-button>
                                <el-button type="success" @click="syncMaterials(0)">{{ this.syncMaterialButtonText
                                }}</el-button>
                            </el-col>
                        </el-row>
                        <el-row :gutter="20">
                            <el-col :span="24" :offset="0">
                                <vxe-table :data="getMaterialDataByType('surfaceMaterialData')" border
                                    :edit-config="{ mode: 'row', trigger: 'click' }"
                                    :column-config="{ resizable: true }"
                                    :row-config="{ resizable: true, isHover: true }">
                                    <vxe-column type="seq" width="55" row-resize></vxe-column>
                                    <vxe-column field="materialType" title="材料类型" width="80"></vxe-column>
                                    <vxe-column field="supplierName" title="厂家名称" width="150" :edit-render="{}">
                                        <template #default="{ row }">
                                            <span>{{ row.supplierName }}</span>
                                        </template>
                                        <template #edit="{ row }">
                                            <el-select v-model="row.supplierName" filterable
                                                :disabled="row.materialSource === 'P'">
                                                <el-option v-for="item in supplierNameOptions" :key="item.supplierName"
                                                    :value="item.supplierName" :label="item.supplierName"></el-option>
                                            </el-select>
                                        </template>
                                    </vxe-column>
                                    <vxe-column title="材料名称" field="materialName" width="150" :edit-render="{}">
                                        <template #default="{ row }">
                                            <span>{{ row.materialName }}</span>
                                        </template>
                                        <template #edit="{ row }">
                                            <el-select v-model="row.materialName"
                                                @change="handleMaterialNameSelect(row, $event)" filterable
                                                :disabled="row.materialSource === 'P'">
                                                <el-option v-for="item in filterByTypes(materialNameOptions, [1])"
                                                    :key="item.value" :value="item.value"
                                                    :label="item.label"></el-option>
                                            </el-select>
                                        </template>
                                    </vxe-column>
                                    <vxe-column field="materialModel" title="材料型号"
                                        :edit-render="{ autoFocus: 'input' }">
                                        <template #edit="{ row }">
                                            <vxe-input v-model="row.materialModel"
                                                :disabled="row.materialSource === 'P'" clearable
                                                :max-length="wordLengths.MODEL_LENGTH"
                                                :showWordCount="row.materialSource !== 'P'"></vxe-input>
                                        </template>
                                    </vxe-column>
                                    <vxe-column field="materialSpecification" title="材料规格"
                                        :edit-render="{ autoFocus: 'input' }">
                                        <template #edit="{ row }">
                                            <vxe-input v-model="row.materialSpecification" clearable :max-length="wordLengths.SPECIFICATION_LENGTH" showWordCount></vxe-input>
                                        </template>
                                    </vxe-column>
                                    <vxe-column field="materialCraftName" title="复合工艺">
                                        <template #default="{ row }">
                                            <vxe-button status="primary" size="small" @click="openCraftDialog(row)">
                                                编辑工艺
                                            </vxe-button>
                                        </template>
                                    </vxe-column>
                                    <vxe-column field="color" title="颜色"
                                        :edit-render="{ autoFocus: 'input' }">
                                        <template #edit="{ row }">
                                            <vxe-input v-model="row.color" clearable :max-length="wordLengths.COLOR_LENGTH" showWordCount></vxe-input>
                                        </template>
                                    </vxe-column>

                                    <vxe-column field="useDepart" title="使用工段" :edit-render="departmentRender">
                                    </vxe-column>
                                    <vxe-column field="comment" title="备注" :edit-render="{ autoFocus: 'input' }">
                                        <template #edit="{ row }">
                                            <vxe-input v-model="row.comment" clearable :max-length="wordLengths.COMMENT_LENGTH" showWordCount></vxe-input>
                                        </template>
                                    </vxe-column>
                                    <vxe-column field="processingRemark" title="加工备注">
                                    </vxe-column>
                                    <vxe-column title="操作" width="80">
                                        <template #default="scope">
                                            <vxe-button status="danger" size="small"
                                                :disabled="scope.row.materialSource === 'P'"
                                                @click="deleteMaterial(scope.$rowIndex, 0)">
                                                删除
                                            </vxe-button>
                                        </template>
                                    </vxe-column>
                                </vxe-table>
                            </el-col>
                        </el-row>

                        <el-row :gutter="20">
                            <el-col :span="22" :offset="0">
                                <span>里料：</span>
                                <el-button type="primary" size="default" @click="addMaterial(1)">添加里料</el-button>
                                <el-button type="primary" size="default"
                                    @click="addMaterialByManual(1)">手动添加里料</el-button>
                                <el-button type="success" @click="syncMaterials(1)">{{ this.syncMaterialButtonText
                                }}</el-button>
                            </el-col>
                        </el-row>
                        <el-row :gutter="20">
                            <el-col :span="24" :offset="0">
                                <vxe-table :data="getMaterialDataByType('insideMaterialData')" border
                                    :edit-config="{ mode: 'row', trigger: 'click' }" style="width: 100%"
                                    :column-config="{ resizable: true }"
                                    :row-config="{ resizable: true, isHover: true }"
                                    :resizable-config="{ isDblclickAutoWidth: true, isDblclickAutoHeight: true }">
                                    <vxe-column type="seq" width="55"></vxe-column>
                                    <vxe-column field="materialType" title="材料类型" width="80"></vxe-column>
                                    <vxe-column field="supplierName" title="厂家名称" width="150" :edit-render="{}">
                                        <template #default="{ row }">
                                            <span>{{ row.supplierName }}</span>
                                        </template>
                                        <template #edit="{ row }">
                                            <el-select v-model="row.supplierName" filterable
                                                :disabled="row.materialSource === 'P'">
                                                <el-option v-for="item in supplierNameOptions" :key="item.supplierName"
                                                    :value="item.supplierName" :label="item.supplierName"></el-option>
                                            </el-select>
                                        </template>
                                    </vxe-column>
                                    <vxe-column title="材料名称" field="materialName" width="150" :edit-render="{}">
                                        <template #default="{ row }">
                                            <span>{{ row.materialName }}</span>
                                        </template>
                                        <template #edit="{ row }">
                                            <el-select v-model="row.materialName"
                                                @change="handleMaterialNameSelect(row, $event)" filterable
                                                :disabled="row.materialSource === 'P'">
                                                <el-option v-for="item in filterByTypes(materialNameOptions, [2])"
                                                    :key="item.value" :value="item.value"
                                                    :label="item.label"></el-option>
                                            </el-select>
                                        </template>
                                    </vxe-column>
                                    <vxe-column field="materialModel" title="材料型号"
                                        :edit-render="{ autoFocus: 'input' }">
                                        <template #edit="{ row }">
                                            <vxe-input v-model="row.materialModel"
                                                :disabled="row.materialSource === 'P'" clearable
                                                :max-length="wordLengths.MODEL_LENGTH"
                                                :showWordCount="row.materialSource !== 'P'"></vxe-input>
                                        </template>
                                    </vxe-column>
                                    <vxe-column field="materialSpecification" title="材料规格"
                                        :edit-render="{ autoFocus: 'input' }">
                                        <template #edit="{ row }">
                                            <vxe-input v-model="row.materialSpecification" clearable :max-length="wordLengths.SPECIFICATION_LENGTH" showWordCount></vxe-input>
                                        </template>
                                    </vxe-column>
                                    <vxe-column field="materialCraftName" title="复合工艺">
                                        <template #default="{ row }">
                                            <vxe-button status="primary" size="small" @click="openCraftDialog(row)">
                                                编辑工艺
                                            </vxe-button>
                                        </template>
                                    </vxe-column>
                                    <vxe-column field="color" title="颜色"
                                        :edit-render="{ autoFocus: 'input' }">
                                        <template #edit="{ row }">
                                            <vxe-input v-model="row.color" clearable :max-length="wordLengths.COLOR_LENGTH" showWordCount></vxe-input>
                                        </template>
                                    </vxe-column>

                                    <vxe-column field="useDepart" title="使用工段" :edit-render="departmentRender">
                                    </vxe-column>
                                    <vxe-column field="comment" title="备注" :edit-render="{ autoFocus: 'input' }">
                                        <template #edit="{ row }">
                                            <vxe-input v-model="row.comment" clearable :max-length="wordLengths.COMMENT_LENGTH" showWordCount></vxe-input>
                                        </template>
                                    </vxe-column>
                                    <vxe-column field="processingRemark" title="加工备注">
                                    </vxe-column>
                                    <vxe-column title="操作" width="80">
                                        <template #default="scope">
                                            <vxe-button status="danger" size="small"
                                                :disabled="scope.row.materialSource === 'P'"
                                                @click="deleteMaterial(scope.$rowIndex, 1)">
                                                删除
                                            </vxe-button>
                                        </template>
                                    </vxe-column>
                                </vxe-table>
                            </el-col>
                        </el-row>
                        <el-row :gutter="20">
                            <el-col :span="22" :offset="0">
                                <span>辅料：</span>
                                <el-button type="primary" size="default" @click="addMaterial(2)">添加辅料</el-button>
                                <el-button type="primary" size="default"
                                    @click="addMaterialByManual(2)">手动添加辅料</el-button>
                                <el-button type="success" @click="syncMaterials(2)">{{ this.syncMaterialButtonText
                                }}</el-button>
                            </el-col>
                        </el-row>
                        <el-row :gutter="20">
                            <el-col :span="24" :offset="0">
                                <vxe-table :data="getMaterialDataByType('accessoryMaterialData')" border
                                    :edit-config="{ mode: 'row', trigger: 'click' }" style="width: 100%"
                                    :column-config="{ resizable: true }"
                                    :row-config="{ resizable: true, isHover: true }"
                                    :resizable-config="{ isDblclickAutoWidth: true, isDblclickAutoHeight: true }"
                                    max-height="350">
                                    <vxe-column type="seq" width="55"></vxe-column>
                                    <vxe-column field="materialType" title="材料类型" width="80"></vxe-column>
                                    <vxe-column field="supplierName" title="厂家名称" width="150" :edit-render="{}">
                                        <template #default="{ row }">
                                            <span>{{ row.supplierName }}</span>
                                        </template>
                                        <template #edit="{ row }">
                                            <el-select v-model="row.supplierName" filterable
                                                :disabled="row.materialSource === 'P'">
                                                <el-option v-for="item in supplierNameOptions" :key="item.supplierName"
                                                    :value="item.supplierName" :label="item.supplierName"></el-option>
                                            </el-select>
                                        </template>
                                    </vxe-column>
                                    <vxe-column title="材料名称" field="materialName" width="150" :edit-render="{}">
                                        <template #default="{ row }">
                                            <span>{{ row.materialName }}</span>
                                        </template>
                                        <template #edit="{ row }">
                                            <el-select v-model="row.materialName"
                                                @change="handleMaterialNameSelect(row, $event)" filterable
                                                :disabled="row.materialSource === 'P'">
                                                <el-option v-for="item in filterByTypes(materialNameOptions, [3, 5])"
                                                    :key="item.value" :value="item.value"
                                                    :label="item.label"></el-option>
                                            </el-select>
                                        </template>
                                    </vxe-column>
                                    <vxe-column field="materialModel" title="材料型号"
                                        :edit-render="{ autoFocus: 'input' }">
                                        <template #edit="{ row }">
                                            <vxe-input v-model="row.materialModel"
                                                :disabled="row.materialSource === 'P'" clearable
                                                :max-length="wordLengths.MODEL_LENGTH"
                                                :showWordCount="row.materialSource !== 'P'"></vxe-input>
                                        </template>
                                    </vxe-column>
                                    <vxe-column field="materialSpecification" title="材料规格"
                                        :edit-render="{ autoFocus: 'input' }">
                                        <template #edit="{ row }">
                                            <vxe-input v-model="row.materialSpecification" clearable :max-length="wordLengths.SPECIFICATION_LENGTH" showWordCount></vxe-input>
                                        </template>
                                    </vxe-column>
                                    <vxe-column field="materialCraftName" title="复合工艺">
                                        <template #default="{ row }">
                                            <vxe-button status="primary" size="small" @click="openCraftDialog(row)">
                                                编辑工艺
                                            </vxe-button>
                                        </template>
                                    </vxe-column>
                                    <vxe-column field="color" title="颜色"
                                        :edit-render="{ autoFocus: 'input' }">
                                        <template #edit="{ row }">
                                            <vxe-input v-model="row.color" clearable :max-length="wordLengths.COLOR_LENGTH" showWordCount></vxe-input>
                                        </template>
                                    </vxe-column>

                                    <vxe-column field="useDepart" title="使用工段" :edit-render="departmentRender">
                                    </vxe-column>
                                    <vxe-column field="comment" title="备注" :edit-render="{ autoFocus: 'input' }">
                                        <template #edit="{ row }">
                                            <vxe-input v-model="row.comment" clearable :max-length="wordLengths.COMMENT_LENGTH" showWordCount></vxe-input>
                                        </template>
                                    </vxe-column>
                                    <vxe-column field="processingRemark" title="加工备注">
                                    </vxe-column>
                                    <vxe-column title="操作" width="80">
                                        <template #default="scope">
                                            <vxe-button status="danger" size="small"
                                                :disabled="scope.row.materialSource === 'P'"
                                                @click="deleteMaterial(scope.$rowIndex, 2)">
                                                删除
                                            </vxe-button>
                                        </template>
                                    </vxe-column>
                                </vxe-table>
                            </el-col>
                        </el-row>
                        <el-row :gutter="20">
                            <el-col :span="22" :offset="0">
                                <span>大底：</span>
                                <el-button type="primary" size="default" @click="addMaterial(3)">添加大底</el-button>
                                <el-button type="primary" size="default"
                                    @click="addMaterialByManual(3)">手动添加大底</el-button>
                                <el-button type="success" @click="syncMaterials(3)">{{ this.syncMaterialButtonText
                                }}</el-button>
                            </el-col>
                        </el-row>
                        <el-row :gutter="20">
                            <el-col :span="24" :offset="0">
                                <vxe-table :data="getMaterialDataByType('outsoleMaterialData')" border
                                    :edit-config="{ mode: 'row', trigger: 'click' }" style="width: 100%"
                                    :column-config="{ resizable: true }"
                                    :row-config="{ resizable: true, isHover: true }"
                                    :resizable-config="{ isDblclickAutoWidth: true, isDblclickAutoHeight: true }">
                                    <vxe-column type="seq" width="55"></vxe-column>
                                    <vxe-column field="materialType" title="材料类型" width="80"></vxe-column>
                                    <vxe-column field="supplierName" title="厂家名称" width="150" :edit-render="{}">
                                        <template #default="{ row }">
                                            <span>{{ row.supplierName }}</span>
                                        </template>
                                        <template #edit="{ row }">
                                            <el-select v-model="row.supplierName" filterable
                                                :disabled="row.materialSource === 'P'">
                                                <el-option v-for="item in supplierNameOptions" :key="item.supplierName"
                                                    :value="item.supplierName" :label="item.supplierName"></el-option>
                                            </el-select>
                                        </template>
                                    </vxe-column>
                                    <vxe-column title="材料名称" field="materialName" width="150" :edit-render="{}">
                                        <template #default="{ row }">
                                            <span>{{ row.materialName }}</span>
                                        </template>
                                        <template #edit="{ row }">
                                            <el-select v-model="row.materialName"
                                                @change="handleMaterialNameSelect(row, $event)" filterable
                                                :disabled="row.materialSource === 'P'">
                                                <el-option v-for="item in filterByTypes(materialNameOptions, [7])"
                                                    :key="item.value" :value="item.value"
                                                    :label="item.label"></el-option>
                                            </el-select>
                                        </template>
                                    </vxe-column>
                                    <vxe-column field="materialModel" title="材料型号"
                                        :edit-render="{ autoFocus: 'input' }">
                                        <template #edit="{ row }">
                                            <vxe-input v-model="row.materialModel"
                                                :disabled="row.materialSource === 'P'" clearable
                                                :max-length="wordLengths.MODEL_LENGTH"
                                                :showWordCount="row.materialSource !== 'P'"></vxe-input>
                                        </template>
                                    </vxe-column>
                                    <vxe-column field="materialSpecification" title="材料规格"
                                        :edit-render="{ autoFocus: 'input' }">
                                        <template #edit="{ row }">
                                            <vxe-input v-model="row.materialSpecification" clearable :max-length="wordLengths.SPECIFICATION_LENGTH" showWordCount></vxe-input>
                                        </template>
                                    </vxe-column>
                                    <vxe-column field="materialCraftName" title="复合工艺">
                                        <template #default="{ row }">
                                            <vxe-button status="primary" size="small" @click="openCraftDialog(row)">
                                                编辑工艺
                                            </vxe-button>
                                        </template>
                                    </vxe-column>
                                    <vxe-column field="color" title="颜色"
                                        :edit-render="{ autoFocus: 'input' }">
                                        <template #edit="{ row }">
                                            <vxe-input v-model="row.color" clearable :max-length="wordLengths.COLOR_LENGTH" showWordCount></vxe-input>
                                        </template>
                                    </vxe-column>

                                    <vxe-column field="useDepart" title="使用工段" :edit-render="departmentRender">
                                    </vxe-column>
                                    <vxe-column field="comment" title="备注" :edit-render="{ autoFocus: 'input' }">
                                        <template #edit="{ row }">
                                            <vxe-input v-model="row.comment" clearable :max-length="wordLengths.COMMENT_LENGTH" showWordCount></vxe-input>
                                        </template>
                                    </vxe-column>
                                    <vxe-column field="processingRemark" title="加工备注">
                                    </vxe-column>
                                    <vxe-column title="操作" width="80">
                                        <template #default="scope">
                                            <vxe-button status="danger" size="small"
                                                :disabled="scope.row.materialSource === 'P'"
                                                @click="deleteMaterial(scope.$rowIndex, 3)">
                                                删除
                                            </vxe-button>
                                        </template>
                                    </vxe-column>
                                </vxe-table>
                            </el-col>
                        </el-row>
                        <el-row :gutter="20">
                            <el-col :span="22" :offset="0">
                                <span>中底：</span>
                                <el-button type="primary" size="default" @click="addMaterial(4)">添加中底</el-button>
                                <el-button type="primary" size="default"
                                    @click="addMaterialByManual(4)">手动添加中底</el-button>
                                <el-button type="success" @click="syncMaterials(4)">{{ this.syncMaterialButtonText
                                }}</el-button>
                            </el-col>
                        </el-row>
                        <el-row :gutter="20">
                            <el-col :span="24" :offset="0">
                                <vxe-table :data="getMaterialDataByType('midsoleMaterialData')" border
                                    :edit-config="{ mode: 'row', trigger: 'click' }" style="width: 100%"
                                    :column-config="{ resizable: true }"
                                    :row-config="{ resizable: true, isHover: true }"
                                    :resizable-config="{ isDblclickAutoWidth: true, isDblclickAutoHeight: true }">
                                    <vxe-column type="seq" width="55"></vxe-column>
                                    <vxe-column field="materialType" title="材料类型" width="80"></vxe-column>
                                    <vxe-column field="supplierName" title="厂家名称" width="150" :edit-render="{}">
                                        <template #default="{ row }">
                                            <span>{{ row.supplierName }}</span>
                                        </template>
                                        <template #edit="{ row }">
                                            <el-select v-model="row.supplierName" filterable
                                                :disabled="row.materialSource === 'P'">
                                                <el-option v-for="item in supplierNameOptions" :key="item.supplierName"
                                                    :value="item.supplierName" :label="item.supplierName"></el-option>
                                            </el-select>
                                        </template>
                                    </vxe-column>
                                    <vxe-column title="材料名称" field="materialName" width="150" :edit-render="{}">
                                        <template #default="{ row }">
                                            <span>{{ row.materialName }}</span>
                                        </template>
                                        <template #edit="{ row }">
                                            <el-select v-model="row.materialName"
                                                @change="handleMaterialNameSelect(row, $event)" filterable
                                                :disabled="row.materialSource === 'P'">
                                                <el-option v-for="item in filterByTypes(materialNameOptions, [7])"
                                                    :key="item.value" :value="item.value"
                                                    :label="item.label"></el-option>
                                            </el-select>
                                        </template>
                                    </vxe-column>
                                    <vxe-column field="materialModel" title="材料型号"
                                        :edit-render="{ autoFocus: 'input' }">
                                        <template #edit="{ row }">
                                            <vxe-input v-model="row.materialModel"
                                                :disabled="row.materialSource === 'P'" clearable
                                                :max-length="wordLengths.MODEL_LENGTH"
                                                :showWordCount="row.materialSource !== 'P'"></vxe-input>
                                        </template>
                                    </vxe-column>
                                    <vxe-column field="materialSpecification" title="材料规格"
                                        :edit-render="{ autoFocus: 'input' }">
                                        <template #edit="{ row }">
                                            <vxe-input v-model="row.materialSpecification" clearable :max-length="wordLengths.SPECIFICATION_LENGTH" showWordCount></vxe-input>
                                        </template>
                                    </vxe-column>
                                    <vxe-column field="materialCraftName" title="复合工艺">
                                        <template #default="{ row }">
                                            <vxe-button status="primary" size="small" @click="openCraftDialog(row)">
                                                编辑工艺
                                            </vxe-button>
                                        </template>
                                    </vxe-column>
                                    <vxe-column field="color" title="颜色"
                                        :edit-render="{ autoFocus: 'input' }">
                                        <template #edit="{ row }">
                                            <vxe-input v-model="row.color" clearable :max-length="wordLengths.COLOR_LENGTH" showWordCount></vxe-input>
                                        </template>
                                    </vxe-column>

                                    <vxe-column field="useDepart" title="使用工段" :edit-render="departmentRender">
                                    </vxe-column>
                                    <vxe-column field="comment" title="备注" :edit-render="{ autoFocus: 'input' }">
                                        <template #edit="{ row }">
                                            <vxe-input v-model="row.comment" clearable :max-length="wordLengths.COMMENT_LENGTH" showWordCount></vxe-input>
                                        </template>
                                    </vxe-column>
                                    <vxe-column field="processingRemark" title="加工备注">
                                    </vxe-column>
                                    <vxe-column title="操作" width="80">
                                        <template #default="scope">
                                            <vxe-button status="danger" size="small"
                                                :disabled="scope.row.materialSource === 'P'"
                                                @click="deleteMaterial(scope.$rowIndex, 4)">
                                                删除
                                            </vxe-button>
                                        </template>
                                    </vxe-column>
                                </vxe-table>
                            </el-col>
                        </el-row>
                        <el-row :gutter="20">
                            <el-col :span="24" :offset="0">
                                <span>烫底：</span>
                                <el-button type="primary" size="default"
                                    @click="addMaterialByManual(6)">添加成品烫底</el-button>
                                <el-button type="primary" size="default"
                                    @click="addMaterialByManual(7)">添加烫底原材料(外发或自加工)</el-button>
                                <el-button type="success" @click="syncMaterials(6)">{{ this.syncMaterialButtonText
                                }}</el-button>
                            </el-col>
                        </el-row>
                        <el-row :gutter="20">
                            <el-col :span="24" :offset="0">
                                <vxe-table :data="getMaterialDataByType('hotsoleMaterialData')" border
                                    :edit-config="{ mode: 'row', trigger: 'click' }" style="width: 100%"
                                    :column-config="{ resizable: true }"
                                    :row-config="{ resizable: true, isHover: true }"
                                    :resizable-config="{ isDblclickAutoWidth: true, isDblclickAutoHeight: true }">
                                    <vxe-column type="seq" width="55"></vxe-column>
                                    <vxe-column field="materialType" title="材料类型" width="80"></vxe-column>
                                    <!-- <vxe-column field="materialDetailType" title="材料二级类型"
                                        :edit-render="{ autoFocus: 'input' }">
                                        <template #edit="{ row }">
                                            <vxe-input v-model="row.materialDetailType" clearable></vxe-input>
                                        </template>
                                    </vxe-column> -->
                                    <vxe-column field="supplierName" title="厂家名称" width="150" :edit-render="{}">
                                        <template #default="{ row }">
                                            <span>{{ row.supplierName }}</span>
                                        </template>
                                        <template #edit="{ row }">
                                            <el-select v-model="row.supplierName" filterable
                                                :disabled="row.materialSource === 'P'">
                                                <el-option v-for="item in supplierNameOptions" :key="item.supplierName"
                                                    :value="item.supplierName" :label="item.supplierName"></el-option>
                                            </el-select>
                                        </template>
                                    </vxe-column>
                                    <vxe-column title="材料名称" field="materialName" width="150" :edit-render="{}">
                                        <template #default="{ row }">
                                            <span>{{ row.materialName }}</span>
                                        </template>
                                        <template #edit="{ row }">
                                            <el-select v-model="row.materialName" filterable @change="
                                                handleMaterialNameSelect(row, $event)"
                                                :disabled="row.materialSource === 'P'">
                                                <div v-if="row.materialType === '里料'">
                                                    <el-option v-for="item in filterByTypes(
                                                        materialNameOptions,
                                                        [2]
                                                    )" :key="item.value" :value="item.value" :label="item.label">
                                                    </el-option>
                                                </div>
                                                <div v-else-if="row.materialType === '烫底'">
                                                    <el-option v-for="item in filterByTypes(
                                                        materialNameOptions,
                                                        [16]
                                                    )" :key="item.value" :value="item.value" :label="item.label">
                                                    </el-option>
                                                </div>
                                            </el-select>
                                        </template>
                                    </vxe-column>
                                    <vxe-column field="materialModel" title="材料型号"
                                        :edit-render="{ autoFocus: 'input' }">
                                        <template #edit="{ row }">
                                            <vxe-input v-model="row.materialModel"
                                                :disabled="row.materialSource === 'P'" clearable
                                                :max-length="wordLengths.MODEL_LENGTH"
                                                :showWordCount="row.materialSource !== 'P'"></vxe-input>
                                        </template>
                                    </vxe-column>
                                    <vxe-column field="materialSpecification" title="材料规格"
                                        :edit-render="{ autoFocus: 'input' }">
                                        <template #edit="{ row }">
                                            <vxe-input v-model="row.materialSpecification" clearable :max-length="wordLengths.SPECIFICATION_LENGTH" showWordCount></vxe-input>
                                        </template>
                                    </vxe-column>
                                    <vxe-column field="materialCraftName" title="复合工艺">
                                        <template #default="{ row }">
                                            <vxe-button status="primary" size="small" @click="openCraftDialog(row)"
                                                :disabled="row.materialType === '烫底'">
                                                编辑工艺
                                            </vxe-button>
                                        </template>
                                    </vxe-column>
                                    <vxe-column field="color" title="颜色"
                                        :edit-render="{ autoFocus: 'input' }">
                                        <template #edit="{ row }">
                                            <vxe-input v-model="row.color" clearable :max-length="wordLengths.COLOR_LENGTH" showWordCount></vxe-input>
                                        </template>
                                    </vxe-column>

                                    <vxe-column field="useDepart" title="使用工段" :edit-render="departmentRender">
                                    </vxe-column>
                                    <vxe-column field="comment" title="备注" :edit-render="{ autoFocus: 'input' }">
                                        <template #edit="{ row }">
                                            <vxe-input v-model="row.comment" clearable :max-length="wordLengths.COMMENT_LENGTH" showWordCount></vxe-input>
                                        </template>
                                    </vxe-column>
                                    <vxe-column field="processingRemark" title="加工备注">
                                    </vxe-column>
                                    <vxe-column title="操作" width="80">
                                        <template #default="scope">
                                            <vxe-button status="danger" size="small"
                                                :disabled="scope.row.materialSource === 'P'"
                                                @click="deleteMaterial(scope.$rowIndex, 6)">
                                                删除
                                            </vxe-button>
                                        </template>
                                    </vxe-column>
                                </vxe-table>
                            </el-col>
                        </el-row>
                    </el-tab-pane>
                </el-tabs>
                <template #footer>
                    <span>
                        <el-button @click="isMaterialCraftVisDialog = false">取消</el-button>
                        <el-button type="primary" @click="isMaterialCraftVisDialog = false">确认</el-button>
                    </span>
                </template>
            </el-dialog>
            <el-dialog title="添加新材料" v-model="newMaterialVis" width="50%">
                <el-row :gutter="20">
                    <el-col :span="6" :offset="0">
                        <div style="display: flex; align-items: center; white-space: nowrap">
                            材料类型查询：<el-input v-model="materialTypeSearch" placeholder="" size="default"
                                :suffix-icon="SearchIcon" clearable
                                @change="getMaterialFilterData(currentCreateViewId)"></el-input>
                        </div>
                    </el-col>
                    <el-col :span="6" :offset="0">
                        <div style="display: flex; align-items: center; white-space: nowrap">
                            材料名称查询：<el-input v-model="materialSearch" placeholder="" size="default"
                                :suffix-icon="SearchIcon" clearable
                                @change="getMaterialFilterData(currentCreateViewId)"></el-input>
                        </div>
                    </el-col>
                    <el-col :span="6" :offset="0">
                        <div style="display: flex; align-items: center; white-space: nowrap">
                            工厂名查询：<el-input v-model="factorySearch" placeholder="" size="default"
                                :suffix-icon="SearchIcon" clearable
                                @change="getMaterialFilterData(currentCreateViewId)"></el-input>
                        </div>
                    </el-col>
                </el-row>
                <el-table :data="assetFilterTable" border ref="materialSelectTable"
                    @selection-change="handleMaterialSelectionChange" style="height: 400px"
                    v-loading="materialAddfinished">
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
                        <el-button type="primary" @click="confirmNewMaterialAdd(typeSymbol)">保存</el-button>
                    </span>
                </template>
            </el-dialog>
            <el-dialog title="输入工艺名称" v-model="isCraftDialogVisible" width="70%">
                <div v-for="(craft, index) in inputCrafts" :key="index">
                    <el-row :gutter="20">
                        <el-col :span="20" :offset="0">
                            <el-input type="textarea" resize="both" v-model="inputCrafts[index]" placeholder="请输入工艺名称"
                                size="default"></el-input></el-col>
                        <el-col :span="4" :offset="0">
                            <el-button type="danger" size="small" @click="removeCraft(index)">删除工艺</el-button></el-col>
                    </el-row>
                </div>
                <el-row :gutter="20">
                    <el-col :span="12" :offset="0">
                        <el-button type="primary" size="default" @click="addCraft">添加工艺
                        </el-button></el-col>
                </el-row>

                <template #footer>
                    <span>
                        <el-button @click="isCraftDialogVisible = false">取消</el-button>
                        <el-button type="primary" @click="confirmCraftInput"> 确定 </el-button>
                    </span>
                </template>
            </el-dialog>
            <el-dialog :title="`工艺单预览 ${newcraftSheetId}`" v-model="isPreviewDialogVisible" width="90%">
                <div style="height: 650px; overflow-y: scroll">
                    <el-row :gutter="20">
                        <el-col :span="23" :offset="0">
                            <el-descriptions title="鞋型基本信息" border direction="vertical" column="4"
                                style="margin-top: 20px">
                                <el-descriptions-item label="鞋图" :rowspan="3" align="center" :width="200">
                                    <el-image style="width: 200px; height: 100px" :src="currentShoeImageUrl" />
                                </el-descriptions-item>
                                <el-descriptions-item label="型号" align="center">{{
                                    currentShoeId
                                    }}</el-descriptions-item>
                                <el-descriptions-item label="客户号" align="center">{{
                                    orderShoeData.customerProductName
                                    }}</el-descriptions-item>
                                <el-descriptions-item label="色号" align="center">{{
                                    orderShoeData.color
                                    }}</el-descriptions-item>
                                <el-descriptions-item label="设计师" align="center">{{
                                    orderShoeData.shoeDesigner
                                    }}</el-descriptions-item>
                                <el-descriptions-item label="调版员" align="center">{{
                                    orderShoeData.shoeAdjuster
                                    }}</el-descriptions-item>
                                <el-descriptions-item label="商标" align="center">{{
                                    orderShoeData.brandName
                                    }}</el-descriptions-item>
                            </el-descriptions>
                        </el-col>
                    </el-row>
                    <el-row :gutter="20">
                        <el-col :span="23" :offset="0">
                            <el-descriptions title="工艺单公用信息" border :column="3" direction="vertical">
                                <el-descriptions-item label="备注图片" :rowspan="2" width="200">
                                    <el-image :src="craftSheetDetail.picNoteImgPath" fit="fill" :lazy="true"></el-image>
                                </el-descriptions-item>
                                <el-descriptions-item label="调版员" width="500">
                                    {{ craftSheetDetail.adjuster }}
                                </el-descriptions-item>
                                <el-descriptions-item label="刀模">
                                    {{ craftSheetDetail.cutDie }}
                                </el-descriptions-item>
                                <el-descriptions-item label="生产额外数量要求">
                                    {{ craftSheetDetail.productionRemark }}
                                </el-descriptions-item>
                                <el-descriptions-item label="审核人">
                                    {{ craftSheetDetail.reviewer }}
                                </el-descriptions-item>
                            </el-descriptions>
                            <el-descriptions title="工艺单特殊工艺信息" border :column="1">
                                <el-descriptions-item label="裁断特殊工艺">
                                    {{ craftSheetDetail.cuttingSpecialCraft }}
                                </el-descriptions-item>
                                <el-descriptions-item label="针车特殊工艺">
                                    {{ craftSheetDetail.sewingSpecialCraft }}
                                </el-descriptions-item>
                                <el-descriptions-item label="成型特殊工艺">
                                    {{ craftSheetDetail.moldingSpecialCraft }}
                                </el-descriptions-item>
                                <el-descriptions-item label="后处理备注">
                                    {{ craftSheetDetail.postProcessing }}
                                </el-descriptions-item>
                                <el-descriptions-item label="科盛油性胶">
                                    {{ craftSheetDetail.oilyGlue }}
                                </el-descriptions-item>
                            </el-descriptions>
                        </el-col>
                    </el-row>

                    <el-tabs v-model="activeTab">
                        <!-- Generate tabs from backend-provided tabcolor array -->
                        <el-tab-pane v-for="color in tabcolor" :label="color" :key="color" :name="color"
                            style="overflow-y: scroll">
                            <el-row :gutter="20">
                                <el-col :span="2" :offset="0"> 面料： </el-col>
                            </el-row>
                            <el-row :gutter="20">
                                <el-col :span="23" :offset="0">
                                    <MaterialDataTable :tableData="getMaterialDataByType('surfaceMaterialData')" />
                                </el-col>
                            </el-row>
                            <el-row :gutter="20">
                                <el-col :span="2" :offset="0"> 里料： </el-col>
                            </el-row>
                            <el-row :gutter="20">
                                <el-col :span="23" :offset="0">
                                    <MaterialDataTable :tableData="getMaterialDataByType('insideMaterialData')" />
                                </el-col>
                            </el-row>
                            <el-row :gutter="20">
                                <el-col :span="2" :offset="0"> 辅料： </el-col>
                            </el-row>
                            <el-row :gutter="20">
                                <el-col :span="23" :offset="0">
                                    <MaterialDataTable :tableData="getMaterialDataByType('accessoryMaterialData')" />
                                </el-col>
                            </el-row>
                            <el-row :gutter="20">
                                <el-col :span="2" :offset="0"> 大底： </el-col>
                            </el-row>
                            <el-row :gutter="20">
                                <el-col :span="23" :offset="0">
                                    <MaterialDataTable :tableData="getMaterialDataByType('outsoleMaterialData')" />
                                </el-col>
                            </el-row>
                            <el-row :gutter="20">
                                <el-col :span="2" :offset="0"> 中底： </el-col>
                            </el-row>
                            <el-row :gutter="20">
                                <el-col :span="23" :offset="0">
                                    <MaterialDataTable :tableData="getMaterialDataByType('midsoleMaterialData')" />
                                </el-col>
                            </el-row>
                            <el-row :gutter="20">
                                <el-col :span="2" :offset="0"> 烫底： </el-col>
                            </el-row>
                            <el-row :gutter="20">
                                <el-col :span="23" :offset="0">
                                    <MaterialDataTable :tableData="getMaterialDataByType('hotsoleMaterialData')" />
                                </el-col>
                            </el-row>
                        </el-tab-pane>
                    </el-tabs>
                    <el-row :gutter="20">
                        <el-col :span="23" :offset="0"> 刀模图： </el-col>
                    </el-row>
                    <el-row :gutter="20">
                        <el-col :span="23" :offset="0">
                            <el-image :src="craftSheetDetail.cutDieImgPath" style="width: 800px"></el-image>
                        </el-col>
                    </el-row>
                </div>

                <template #footer>
                    <span>
                        <el-button type="primary" @click="isPreviewDialogVisible = false">确认</el-button>
                    </span>
                </template>
            </el-dialog>
            <el-dialog :title="`编辑生产工艺单 ${newcraftSheetId}`" v-model="isEditDialogVisible" width="90%"
                style="height: 700px; overflow-y: scroll">
                <el-descriptions title="工艺单公用信息" border :column="2">
                    <el-descriptions-item label="调版员">
                        <el-input v-model="craftSheetDetail.adjuster" size="default"></el-input>
                    </el-descriptions-item>
                    <el-descriptions-item label="刀模">
                        <el-input v-model="craftSheetDetail.cutDie" size="default"></el-input>
                    </el-descriptions-item>
                    <el-descriptions-item label="生产额外数量要求">
                        <el-input v-model="craftSheetDetail.productionRemark" size="default"></el-input>
                    </el-descriptions-item>
                    <el-descriptions-item label="审核人">
                        <el-input v-model="craftSheetDetail.reviewer" size="default"></el-input>
                    </el-descriptions-item>
                </el-descriptions>
                <el-descriptions title="工艺单特殊工艺信息" border :column="1">
                    <el-descriptions-item label="裁断特殊工艺">
                        <el-input type="textarea" v-model="craftSheetDetail.cuttingSpecialCraft" size="default"
                            maxlength="150" autosize show-word-limit></el-input>
                    </el-descriptions-item>
                    <el-descriptions-item label="针车特殊工艺">
                        <el-input type="textarea" v-model="craftSheetDetail.sewingSpecialCraft" size="default"
                            maxlength="150" autosize show-word-limit></el-input>
                    </el-descriptions-item>
                    <el-descriptions-item label="成型特殊工艺">
                        <el-input type="textarea" v-model="craftSheetDetail.moldingSpecialCraft" size="default"
                            maxlength="200" autosize show-word-limit></el-input>
                    </el-descriptions-item>
                    <el-descriptions-item label="后处理备注">
                        <el-input type="textarea" v-model="craftSheetDetail.postProcessing" maxlength="150" autosize
                            show-word-limit size="default"></el-input>
                    </el-descriptions-item>
                    <el-descriptions-item label="科盛油性胶">
                        <el-input type="textarea" v-model="craftSheetDetail.oilyGlue" maxlength="300" autosize
                            show-word-limit size="default"></el-input>
                    </el-descriptions-item>
                </el-descriptions>
                <el-button type="primary" size="default" @click="openMaterialCraftDialog">打开材料工艺编辑页面</el-button>
                <el-button type="primary" size="default" @click="openCutDieDialog">打开刀模图上传页面</el-button>
                <el-button type="primary" size="default" @click="openPicNoteDialog">打开工艺单图片备注上传页面</el-button>
                <el-button type="primary" size="default" @click="openCraftSheetDialog">打开工艺单备注上传页面</el-button>
                <template #footer>
                    <span>
                        <el-button @click="isEditDialogVisible = false">取消</el-button>
                        <el-button type="primary" @click="editProductionInstrucion">确认</el-button>
                    </span>
                </template>
            </el-dialog>
            <el-dialog v-model="isUploadImageDialogVisible" title="上传刀模图">
                <el-upload ref="uploadImage" class="upload-image"
                    :action="`${this.$apiBaseUrl}/craftsheet/uploadcutdieimg`" :on-success="handleUploadSuccess"
                    :on-error="handleUploadError" :headers="uploadHeaders" :before-upload="beforeUpload"
                    :file-list="fileList" list-type="picture-card" accept="image/*" :auto-upload="false"
                    @remove="handleFileRemove" :data="cutDieImgData">
                </el-upload>
                <div slot="tip" class="el-upload__tip">只能上传图片文件</div>
                <el-button type="primary" size="default" @click="pasteClipboardImage('main')">粘贴剪切板内容</el-button>
            </el-dialog>
            <el-dialog v-model="isUploadImageNoteDialogVisible" title="上传图片备注">
                <el-upload ref="uploadImageNote" class="upload-image"
                    :action="`${this.$apiBaseUrl}/craftsheet/uploadpicnoteimg`" :on-success="handleUploadSuccessPicNote"
                    :on-error="handleUploadError" :headers="uploadHeaders" :before-upload="beforeUpload"
                    :file-list="fileListPicNote" list-type="picture-card" accept="image/*" :auto-upload="false"
                    :data="picNoteImgData" @remove="handleFileRemovePicNote">
                </el-upload>
                <div slot="tip" class="el-upload__tip">只能上传图片文件</div>
                <el-button type="primary" size="default" @click="pasteClipboardImage('note')">粘贴剪切板内容</el-button>
            </el-dialog>
            <el-dialog v-model="isUploadProcessSheetVisable" title="上传工艺单EXCEL">
                <el-upload ref="uploadProcessSheet" class="upload-image"
                    :action="`${this.$apiBaseUrl}/craftsheet/uploadprocesssheet`"
                    :on-success="handleUploadSuccessProcessSheet" :on-error="handleUploadError" :headers="uploadHeaders"
                    :limit="1" :before-upload="beforeUpload" :file-list="fileListProcessSheet" accept=".xls,.xlsx"
                    :auto-upload="false" :data="craftSheetData" @remove="handleFileRemoveProcessSheet">
                    <template #trigger>
                        <el-button type="primary">选择文件</el-button>
                    </template>
                </el-upload>
                <div slot="tip" class="el-upload__tip">只能上传EXCEL文件</div>
            </el-dialog>
        </el-main>
    </el-container>
</template>

<script>
import AllHeader from '@/components/AllHeader.vue'
import Arrow from '@/components/OrderArrowView.vue'
import { Search } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import MaterialDataTable from '../components/MaterialDataTable.vue'
import axios from 'axios'
import { useRoute } from 'vue-router'
import * as constants from '@/Pages/utils/constants'
export default {
    components: {
        AllHeader,
        Arrow,
        MaterialDataTable
    },
    props: ['orderId'],
    data() {
        return {
            userRole: localStorage.getItem('role'),
            orderShoeData: {},
            departmentOptions: [],
            activeTab: '',
            tabcolor: [],
            materialWholeData: [],
            universalMaterialWholeData: [],
            surfaceMaterialData: [],
            insideMaterialData: [],
            accessoryMaterialData: [],
            outsoleMaterialData: [],
            midsoleMaterialData: [],
            lastMaterialData: [],
            typeSymbol: 0,
            materialTypeSearch: '',
            materialSearch: '',
            factorySearch: '',
            isUploadProcessSheetVisable: false,
            isUniversalMaterialCraftVisDialog: false,
            isEditDialogVisible: false,
            isProductionOrderCreateDialogVisible: false,
            isUploadImageNoteDialogVisible: false,
            isMaterialCraftVisDialog: false,
            isPreviewDialogVisible: false,
            token: localStorage.getItem('token'),
            currentShoeId: '',
            currentColor: '',
            currentShoeImageUrl: '',
            fileList: [],
            fileListPicNote: [],
            fileListProcessSheet: [],
            isUploadImageDialogVisible: false,
            createEditSymbol: 0,
            sizeData: [],
            currentSizeData: [],
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
            assetFilterTable: [],
            colorOptions: [],
            newMaterialVis: false,
            updateArrowKey: 0,
            orderData: {},
            testTableData: [],
            testTableFilterData: [],
            bomTestData: [],
            editBomData: [],
            originalBomTestData: [],
            selectedFile: null,
            inheritIdSearch: '',
            isFinalBOM: false,
            orderProduceInfo: [],
            newcraftSheetId: '',
            cutDieImgData: {
                orderId: '',
                orderShoeId: '',
                craftSheetId: ''
            },
            picNoteImgData: {
                orderId: '',
                orderShoeId: '',
                craftSheetId: ''
            },
            craftSheetData: {
                orderId: '',
                orderShoeId: '',
                craftSheetId: ''
            },
            defaultManuallyAddedMaterial: {
                materialType: '',
                materialDetailType: '',
                materialName: '',
                materialModel: '',
                materialSpecification: '',
                color: '',
                unit: '',
                supplierName: '',
                comment: '',
                isPurchase: false,
                materialSource: 'C',
            },
            craftSheetDetail: {
                adjuster: '',
                cutDie: '',
                reviewer: '',
                productionRemark: '大货产前小做每码5双',
                cuttingSpecialCraft:
                    '7.5码用7码刀模/8.5码用8码刀模/9.5码用9码刀模/10.5码用10码刀模,其它码数不变',
                sewingSpecialCraft: `车线针距：面料合缝1.5MM,PU里合缝1.5MM,布里合缝2-3MM,贴里布要服贴帮面，贴子根包头放到位.鞋口里要抓弧度贴。鞋口放保险丝。7.5码用7码鞋包/8.5码用8码鞋包/9.5码用9码鞋包/10.5码用10码鞋包,其它码数不变`,
                moldingSpecialCraft: `所有后跟合缝的鞋款后帮定型机定过再夹包，所有后跟包脚13MM，组合底：80℃ TPR:90℃，PU:85℃ 冬季温度高5℃ 压合7秒13公斤 8码后高70mm 7.5码复7码底(内显7.外显7.5码)8.5码复8码底(内显8.外显8.5码)9.5码复9码底(内显9.外显9.5码半)10.5码复10码底(内显10.外显10.5码)其它码数不变`,
                postProcessing: '',
                oilyGlue: `TPR底：894K处理剂，PU底：892R处理剂，EVA底：895E处理剂-使用时加15%E-750, 橡胶底：①黑色用893R处理剂加3%粉1000ML加30克，②白色底用893S处理剂加2%粉1000ML加20克，PU革面：892R处理剂，尼龙布.绒皮：798P无色尼龙处理剂使用加15%E-750`,
                cutDieImgPath: '',
                picNoteImgPath: ''
            },
            isCraftDialogVisible: false,
            syncMaterialButtonText: '同步该材料表格至所有颜色',
            inputCrafts: [], // 手动输入的工艺列表
            currentRow: null, // 当前编辑的行,
            materialNameOptions: [],
            supplierNameOptions: [],
            departmentRender: {
                name: 'ElSelect',
                options: [],
                props: {
                    filterable: true
                }
            },
            wordLengths: {
                MODEL_LENGTH: constants.MODEL_LENGTH,
                SPECIFICATION_LENGTH: constants.SPECIFICATION_LENGTH,
                COLOR_LENGTH: constants.COLOR_LENGTH,
                CRAFT_NAME_LENGTH: constants.CRAFT_NAME_LENGTH,
                COMMENT_LENGTH: constants.COMMENT_LENGTH,
                PROCESSING_REMARK_LENGTH: constants.PROCESSING_REMARK_LENGTH,
                SUPPLIER_NAME_LENGTH: constants.SUPPLIER_NAME_LENGTH
            }
        }
    },
    async mounted() {
        this.$setAxiosToken()
        this.getOrderInfo()
        this.getAllShoeListInfo()
        this.getAllDepartmentOptions()
        this.getAllMaterialList()
        this.getAllMaterialName()
        this.querySupplierNames()
        document.addEventListener('paste', this.handlePaste)
    },
    beforeUnmounted() {
        document.removeEventListener('paste', this.handlePaste)
    },
    computed: {
        uploadHeaders() {
            return {
                Authorization: `Bearer ${this.token}`
            }
        },
        SearchIcon() {
            return Search
        }
    },
    methods: {
        filterByTypes(options, types) {
            return options.filter((option) => types.includes(option.type))
        },
        async querySupplierNames() {
            const response = await axios.get(
                `${this.$apiBaseUrl}/logistics/allsuppliers`
            )
            this.supplierNameOptions = response.data
        },
        async getAllMaterialName() {
            const params = { department: 0 }
            const response = await axios.get(`${this.$apiBaseUrl}/logistics/getallmaterialname`, { params })
            this.materialNameOptions = response.data
        },
        async pasteClipboardImage(target) {
            try {
                // Access clipboard data
                const clipboardItems = await navigator.clipboard.read()
                for (const item of clipboardItems) {
                    if (item.types.includes('image/png') || item.types.includes('image/jpeg')) {
                        const blob = await item.getType(item.types[0])
                        const file = new File([blob], 'pasted-image.png', { type: blob.type })

                        if (target === 'main') {
                            this.addImageToFileList(file, 'main')
                        } else if (target === 'note') {
                            this.addImageToFileList(file, 'note')
                        }
                        return
                    }
                }
                this.$message.error('剪贴板中没有图片！')
            } catch (error) {
                console.error('Failed to read clipboard:', error)
                this.$message.error('无法从剪贴板读取图片！')
            }
        },
        handlePaste(event) {
            const items = (event.clipboardData || window.clipboardData).items

            for (const item of items) {
                if (item.type.startsWith('image/')) {
                    const file = item.getAsFile()
                    if (file) {
                        if (this.isUploadImageDialogVisible) {
                            this.addImageToFileList(file, 'main')
                        } else if (this.isUploadImageNoteDialogVisible) {
                            this.addImageToFileList(file, 'note')
                        }
                    }
                }
            }
        },
        addImageToFileList(file, target) {
            const newFile = {
                uid: Date.now(),
                name: file.name || 'pasted-image.png',
                size: file.size,
                type: file.type,
                status: 'ready',
                url: URL.createObjectURL(file),
                raw: file
            }

            if (target === 'main') {
                this.fileList.push(newFile)
                if (this.$refs.uploadImage) {
                    this.$refs.uploadImage.uploadFiles = this.fileList
                }
            } else if (target === 'note') {
                this.fileListPicNote.push(newFile)
                if (this.$refs.uploadImageNote) {
                    this.$refs.uploadImageNote.uploadFiles = this.fileListPicNote
                }
            }
        },
        handleFileRemove(file, fileList) {
            console.log('File removed:', file)
            this.fileList = fileList // Keep fileList in sync
        },
        handleFileRemoveProcessSheet(file, fileList) {
            this.fileListProcessSheet = fileList // Sync file list for process sheet upload
        },
        handleFileRemovePicNote(file, fileList) {
            this.fileListPicNote = fileList // Sync file list for note upload
        },
        isEditor() {
            return this.userRole == 5
        },
        async getAllDepartmentOptions() {
            const response = await axios.get(`${this.$apiBaseUrl}/general/getalldepartments`)
            this.departmentOptions = response.data
            this.departmentRender.options = this.departmentOptions.map((item) => ({
                value: item.value,
                label: item.label
            }))
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
        async getAllShoeListInfo() {
            const response = await axios.get(
                `${this.$apiBaseUrl}/craftsheet/getordershoelist?orderid=${this.orderId}`
            )
            this.testTableData = response.data
            this.tableWholeFilter()
        },
        async getOrderShoeInfo(orderShoeId) {
            const response = await axios.get(
                `${this.$apiBaseUrl}/devproductionorder/getordershoeinfo?orderid=${this.orderId}&ordershoeid=${orderShoeId}`
            )
            this.orderShoeData = response.data
        },
        async getNewcraftSheetId() {
            const response = await axios.get(`${this.$apiBaseUrl}/craftsheet/getnewcraftsheetid`)
            this.newcraftSheetId = response.data.craftSheetId
            console.log(this.newcraftSheetId)
        },
        syncAllMaterials() {
            ElMessageBox.alert('确认复制所有材料至所有颜色吗', '警告', {
                confirmButtonText: '确认',
                showCancelButton: true,
                cancelButtonText: '取消'
            })
                .then(async () => {
                    try {
                        for (let i = 0; i < 7; i++) {
                            this.syncMaterials(i, true)
                        }
                        ElMessage.success('复制成功')
                    } catch (error) {
                        console.log(error)
                        ElMessage.error('复制异常')
                    }
                })
                .catch(() => {
                    ElMessage.info('取消复制')
                })
        },
        concatMaterialData(tableName) {
            let dataToCopy = this.getMaterialDataByType(tableName)
            this.materialWholeData.forEach((shoeTypeData) => {
                if (shoeTypeData.color !== this.activeTab) {
                    // keep the data of materialSource 'P'
                    let developmentData = shoeTypeData[tableName].filter(
                        (materialData) => materialData.materialSource === 'P'
                    )
                    // if materialSource is 'C', then it can be copied
                    let newAddedData = dataToCopy.filter(
                        (materialData) => materialData.materialSource === 'C'
                    )
                    // add development data to newAddedData
                    developmentData = developmentData.concat(newAddedData)
                    shoeTypeData[tableName] = JSON.parse(
                        JSON.stringify(developmentData)
                    )
                }
            })
        },
        syncMaterials(materialTypeNumber, isSyncAll = false) {
            switch (materialTypeNumber) {
                case 0:
                    this.concatMaterialData('surfaceMaterialData')
                    break
                case 1:
                    this.concatMaterialData('insideMaterialData')
                    break
                case 2:
                    this.concatMaterialData('accessoryMaterialData')
                    break
                case 3:
                    this.concatMaterialData('outsoleMaterialData')
                    break
                case 4:
                    this.concatMaterialData('midsoleMaterialData')
                    break
                case 6:
                    this.concatMaterialData('hotsoleMaterialData')
                    break
            }
            if (!isSyncAll) {
                ElMessage.success('复制成功')
            }
        },
        addMaterialByManual(typeSymbol) {
            const preActiveMaterialData = this.materialWholeData.find(
                (item) => item.color === this.activeTab
            )
            if (!preActiveMaterialData) {
                this.materialWholeData.push({
                    color: this.activeTab,
                    surfaceMaterialData: [],
                    insideMaterialData: [],
                    accessoryMaterialData: [],
                    outsoleMaterialData: [],
                    midsoleMaterialData: [],
                    lastMaterialData: [],
                    hotsoleMaterialData: []
                })
            }
            const activeMaterialData = this.materialWholeData.find(
                (item) => item.color === this.activeTab
            )
            let newEntry = {
                materialType: '',
                materialDetailType: '',
                materialName: '',
                materialModel: '',
                materialSpecification: '',
                color: '',
                unit: '',
                supplierName: '',
                materialSource: 'C',
                comment: '',
                isPurchase: false,
            }
            switch (typeSymbol) {
                case 0:
                    this.defaultManuallyAddedMaterial.materialType = '面料'
                    activeMaterialData.surfaceMaterialData.push(this.defaultManuallyAddedMaterial)
                    this.defaultManuallyAddedMaterial = newEntry
                    break
                case 1:
                    this.defaultManuallyAddedMaterial.materialType = '里料'
                    activeMaterialData.insideMaterialData.push(this.defaultManuallyAddedMaterial)
                    this.defaultManuallyAddedMaterial = newEntry
                    break
                case 2:
                    this.defaultManuallyAddedMaterial.materialType = '辅料'
                    activeMaterialData.accessoryMaterialData.push(this.defaultManuallyAddedMaterial)
                    this.defaultManuallyAddedMaterial = newEntry
                    break
                case 3:
                    this.defaultManuallyAddedMaterial.materialType = '底材'
                    activeMaterialData.outsoleMaterialData.push(this.defaultManuallyAddedMaterial)
                    this.defaultManuallyAddedMaterial = newEntry
                    break
                case 4:
                    this.defaultManuallyAddedMaterial.materialType = '底材'
                    activeMaterialData.midsoleMaterialData.push(this.defaultManuallyAddedMaterial)
                    this.defaultManuallyAddedMaterial = newEntry
                    break
                case 5:
                    this.defaultManuallyAddedMaterial.materialType = '楦头'
                    activeMaterialData.lastMaterialData.push(this.defaultManuallyAddedMaterial)
                    this.defaultManuallyAddedMaterial = newEntry
                    break
                case 6:
                    this.defaultManuallyAddedMaterial.materialType = '烫底'
                    activeMaterialData.hotsoleMaterialData.push(this.defaultManuallyAddedMaterial)
                    this.defaultManuallyAddedMaterial = newEntry
                    break
                case 7:
                    this.defaultManuallyAddedMaterial.materialType = '里料'
                    activeMaterialData.hotsoleMaterialData.push(this.defaultManuallyAddedMaterial)
                    this.defaultManuallyAddedMaterial = newEntry
                    break
                default:
                    break
            }
        },
        addMaterial(typeSymbol) {
            this.typeSymbol = typeSymbol
            this.newMaterialVis = true
            switch (typeSymbol) {
                case 0:
                    this.currentCreateViewId = 0
                    this.materialTypeSearch = '面料'
                    this.getMaterialFilterData()
                    break
                case 1:
                    this.currentCreateViewId = 1
                    this.materialTypeSearch = '里料'
                    this.getMaterialFilterData()
                    break
                case 2:
                    this.currentCreateViewId = 2
                    this.materialTypeSearch = '辅料'
                    this.getMaterialFilterData()
                    break
                case 3:
                    this.currentCreateViewId = 3
                    this.materialTypeSearch = '底材'
                    this.getMaterialFilterData()
                    break
                case 4:
                    this.currentCreateViewId = 4
                    this.materialTypeSearch = '底材'
                    this.getMaterialFilterData()
                    break
                case 5:
                    this.currentCreateViewId = 5
                    this.materialTypeSearch = '楦头'
                    this.getMaterialFilterData()
                    break
                case 6:
                    this.currentCreateViewId = 6
                    this.materialTypeSearch = '复合'
                    this.getMaterialFilterData()
                    break
                default:
                    break
            }
        },
        confirmNewMaterialAdd(typeSymbol) {
            this.newMaterialVis = false

            // Find the data for the current active tab
            const preActiveMaterialData = this.materialWholeData.find(
                (item) => item.color === this.activeTab
            )
            const preActiveUniversalMaterialData = this.universalMaterialWholeData.find(
                (item) => item.color === this.activeTab
            )
            console.log(this.materialWholeData)
            console.log(this.activeTab)

            if (!preActiveMaterialData) {
                this.materialWholeData.push({
                    color: this.activeTab,
                    surfaceMaterialData: [],
                    insideMaterialData: [],
                    accessoryMaterialData: [],
                    outsoleMaterialData: [],
                    midsoleMaterialData: [],
                    lastMaterialData: [],
                    hotsoleMaterialData: []
                })
            }
            const activeMaterialData = this.materialWholeData.find(
                (item) => item.color === this.activeTab
            )

            // Determine the correct array to push into based on typeSymbol
            switch (typeSymbol) {
                case 0:
                    activeMaterialData.surfaceMaterialData.push(this.materialSelectRow)
                    break
                case 1:
                    activeMaterialData.insideMaterialData.push(this.materialSelectRow)
                    break
                case 2:
                    activeMaterialData.accessoryMaterialData.push(this.materialSelectRow)
                    break
                case 3:
                    activeMaterialData.outsoleMaterialData.push(this.materialSelectRow)
                    break
                case 4:
                    activeMaterialData.midsoleMaterialData.push(this.materialSelectRow)
                    break
                case 5:
                    activeMaterialData.lastMaterialData.push(this.materialSelectRow)
                    break
                case 6:
                    activeMaterialData.hotsoleMaterialData.push(this.materialSelectRow)
                    break
                default:
                    break
            }
        },
        handleGenerateClose() {
            this.newMaterialVis = false
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
        async getMaterialOriginData(row) {
            const response = await axios.get(
                `${this.$apiBaseUrl}/craftsheet/getoriginmaterialinfo?orderid=${this.orderData.orderId}&ordershoeid=${row.inheritId}`
            )
            this.materialWholeData = response.data.instructionData
        },
        async getCraftSheetData(row) {
            const response = await axios.get(
                `${this.$apiBaseUrl}/craftsheet/getcraftsheetinfo?orderid=${this.orderData.orderId}&ordershoeid=${row.inheritId}`
            )
            console.log(response.data)
            this.craftSheetDetail = response.data.craftSheetDetail
            this.materialWholeData = response.data.uploadData
            this.newcraftSheetId = response.data.craftSheetId
            console.log(this.newcraftSheetId)
        },
        async openCutDieDialog() {
            this.cutDieImgData.orderId = this.orderData.orderId
            this.cutDieImgData.orderShoeId = this.currentShoeId
            this.cutDieImgData.craftSheetId = this.newcraftSheetId
            this.isUploadImageDialogVisible = true
        },
        async openPicNoteDialog() {
            this.picNoteImgData.orderId = this.orderData.orderId
            this.picNoteImgData.orderShoeId = this.currentShoeId
            this.picNoteImgData.craftSheetId = this.newcraftSheetId
            this.isUploadImageNoteDialogVisible = true
        },
        async openPreviewDialog(row) {
            this.newcraftSheetId = ''
            this.materialWholeData = []
            this.currentShoeId = row.inheritId
            this.currentShoeImageUrl = row.typeInfos[0].image
            await this.getOrderShoeInfo(row.inheritId)
            this.getCraftSheetData(row)
            this.tabcolor = row.typeInfos.map((info) => info.color)
            this.activeTab = this.tabcolor[0]
            this.isPreviewDialogVisible = true
        },
        openCraftSheetDialog() {
            this.craftSheetData.orderId = this.orderData.orderId
            this.craftSheetData.orderShoeId = this.currentShoeId
            this.craftSheetData.craftSheetId = this.newcraftSheetId
            this.isUploadProcessSheetVisable = true
        },
        openUniversalMaterialCraftDialog() {
            this.isUniversalMaterialCraftVisDialog = true
        },
        openMaterialCraftDialog() {
            this.isMaterialCraftVisDialog = true
        },

        openIssueDialog() {
            this.isFinalBOM = true
            this.unIssueBOMData = this.testTableData.filter((row) => row.status === '已上传')
            console.log(this.unIssueBOMData)
        },
        async openUploadDialog(row) {
            this.newcraftSheetId = ''
            this.materialWholeData = []
            this.currentShoeId = row.inheritId
            await this.getCraftSheetData(row)
            this.craftSheetDetail.productionRemark = '大货产前小做每码5双'
            this.craftSheetDetail.cuttingSpecialCraft =
                '7.5码用7码刀模/8.5码用8码刀模/9.5码用9码刀模/10.5码用10码刀模,其它码数不变'
            this.craftSheetDetail.sewingSpecialCraft =
                '车线针距：面料合缝1.5MM,PU里合缝1.5MM,布里合缝2-3MM,贴里布要服贴帮面，贴子根包头放到位.鞋口里要抓弧度贴。鞋口放保险丝。7.5码用7码鞋包/8.5码用8码鞋包/9.5码用9码鞋包/10.5码用10码鞋包,其它码数不变'
            this.craftSheetDetail.moldingSpecialCraft =
                '所有后跟合缝的鞋款后帮定型机定过再夹包，所有后跟包脚13MM，组合底：80℃ TPR:90℃，PU:85℃ 冬季温度高5℃ 压合7秒13公斤 8码后高70mm 7.5码复7码底(内显7.外显7.5码)8.5码复8码底(内显8.外显8.5码)9.5码复9码底(内显9.外显9.5码半)10.5码复10码底(内显10.外显10.5码)其它码数不变'
            this.craftSheetDetail.postProcessing = ''
            this.craftSheetDetail.oilyGlue =
                'TPR底：894K处理剂，PU底：892R处理剂，EVA底：895E处理剂-使用时加15%E-750, 橡胶底：①黑色用893R处理剂加3%粉1000ML加30克，②白色底用893S处理剂加2%粉1000ML加20克，PU革面：892R处理剂，尼龙布.绒皮：798P无色尼龙处理剂使用加15%E-750'
            this.tabcolor = row.typeInfos.map((info) => info.color)
            this.activeTab = this.tabcolor[0]
            for (let i = 0; i < this.tabcolor.length; i++) {
                this.materialWholeData.push({
                    color: this.tabcolor[i],
                    surfaceMaterialData: [],
                    insideMaterialData: [],
                    accessoryMaterialData: [],
                    outsoleMaterialData: [],
                    midsoleMaterialData: [],
                    lastMaterialData: [],
                    hotsoleMaterialData: []
                })
            }
            this.isProductionOrderCreateDialogVisible = true
        },
        async openEditDialog(row) {
            this.newcraftSheetId = ''
            this.currentShoeId = row.inheritId
            await this.getCraftSheetData(row)
            this.tabcolor = row.typeInfos.map((info) => info.color)
            if (this.materialWholeData.length === 0) {
                // create a empty template for it
                this.tabcolor.forEach((colorName) => {
                    let obj = {
                        color: colorName,
                        surfaceMaterialData: [],
                        insideMaterialData: [],
                        accessoryMaterialData: [],
                        outsoleMaterialData: [],
                        midsoleMaterialData: [],
                        lastMaterialData: [],
                        hotsoleMaterialData: []
                    }
                    this.materialWholeData.push(obj)
                })
            }
            this.activeTab = this.tabcolor[0]
            this.isEditDialogVisible = true
        },
        getMaterialDataByType(type) {
            const activeData = this.materialWholeData.find((item) => item.color === this.activeTab)
            if (activeData) {
                return activeData[type]
            }
            return []
        },
        getUniversalMaterialDataByType(type) {
            const activeData = this.universalMaterialWholeData.find(
                (item) => item.color === this.activeTab
            )
            if (activeData) {
                return activeData[type]
            }
            return []
        },
        async editProductionInstrucion() {
            for (const materialData of this.materialWholeData) {
                for (const materialType of [
                    'surfaceMaterialData',
                    'insideMaterialData',
                    'accessoryMaterialData',
                    'outsoleMaterialData',
                    'midsoleMaterialData',
                    'hotsoleMaterialData'
                ]) {
                    for (const item of materialData[materialType]) {
                        if (!item.supplierName || !item.materialName) {
                            this.$message({
                                type: 'error',
                                message: '所有材料的供应商名称和材料名称不能为空'
                            })
                            return
                        }
                    }
                }
            }
            const loadingInstance = this.$loading({
                lock: true,
                text: '等待中，请稍后...',
                background: 'rgba(0, 0, 0, 0.7)'
            })
            try {
                // save images
                this.uploadCutDieImg()
                this.uploadPicNote()
                this.uploadProcessSheet()
                await axios.post(`${this.$apiBaseUrl}/craftsheet/editcraftsheet`, {
                    orderId: this.orderData.orderId,
                    craftSheetId: this.newcraftSheetId,
                    orderShoeId: this.currentShoeId,
                    uploadData: this.materialWholeData,
                    craftSheetDetail: this.craftSheetDetail
                })
                ElMessage.success('保存成功')
            } catch (error) {
                console.log(error)
                ElMessage.error('保存失败')
            }
            loadingInstance.close()
            this.isEditDialogVisible = false
            this.getAllShoeListInfo()
        },
        async saveProductionInstruction() {
            for (const materialData of this.materialWholeData) {
                for (const materialType of [
                    'surfaceMaterialData',
                    'insideMaterialData',
                    'accessoryMaterialData',
                    'outsoleMaterialData',
                    'midsoleMaterialData',
                    'hotsoleMaterialData'
                ]) {
                    for (const item of materialData[materialType]) {
                        if (!item.supplierName || !item.materialName) {
                            this.$message({
                                type: 'error',
                                message: '所有材料的供应商名称和材料名称不能为空'
                            })
                            return
                        }
                    }
                }
            }
            const loadingInstance = this.$loading({
                lock: true,
                text: '等待中，请稍后...',
                background: 'rgba(0, 0, 0, 0.7)'
            })
            try {
                await axios.post(`${this.$apiBaseUrl}/craftsheet/savecraftsheet`, {
                    orderId: this.orderData.orderId,
                    craftSheetId: this.newcraftSheetId,
                    orderShoeId: this.currentShoeId,
                    uploadData: this.materialWholeData,
                    craftSheetDetail: this.craftSheetDetail
                })
                // save images
                this.uploadCutDieImg()
                this.uploadPicNote()
                this.uploadProcessSheet()

                ElMessage.success('保存成功')
            } catch (error) {
                console.log(error)
                ElMessage.error('保存失败')
            }
            loadingInstance.close()
            this.isProductionOrderCreateDialogVisible = false
            this.getAllShoeListInfo()
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
        confirmUpload() {
            this.$confirm('确定上传生产工艺单吗？', '提示', {
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
                    await this.$refs.productionOrderUpload.submit()
                    loadingInstance.close()
                })
                .catch(() => {
                    this.$message({
                        type: 'info',
                        message: '已取消上传'
                    })
                })
        },
        handleUploadSuccess(response, file, fileList) {
            this.$message({
                message: '上传成功',
                type: 'success'
            })
            this.craftSheetDetail.cutDieImgPath = response.filePath
            console.log(this.craftSheetDetail.cutDieImgPath)
            this.isUploadImageDialogVisible = false
        },
        handleUploadSuccessPicNote(response, file, fileList) {
            this.$message({
                message: '上传成功',
                type: 'success'
            })
            this.craftSheetDetail.picNoteImgPath = response.filePath
            console.log(this.craftSheetDetail.picNoteImgPath)
            this.isUploadImageDialogVisible = false
        },
        handleUploadError() {
            this.$message.error('上传失败')
        },
        handleUploadSuccessProcessSheet(response, file, fileList) {
            this.$message({
                message: '上传成功',
                type: 'success'
            })
            fileList = []
            this.isUploadProcessSheetVisable = false
        },
        async issueBOMs(selectedShoe) {
            if (selectedShoe.length == 0) {
                ElMessage.error('未选择鞋型')
                return
            }
            const loadingInstance = this.$loading({
                lock: true,
                text: '等待中，请稍后...',
                background: 'rgba(0, 0, 0, 0.7)'
            })
            const response = await axios.post(`${this.$apiBaseUrl}/craftsheet/issue`, {
                orderId: this.orderData.orderId,
                orderShoeIds: selectedShoe.map((shoe) => shoe.inheritId)
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
            this.getAllShoeListInfo()
        },
        confirmBOMIssue() {
            this.$confirm('确定下发选定生产工艺单吗？', '提示', {
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
        deleteMaterial(index, typeSymbol) {
            console.log(index, typeSymbol)
            // Find the material data for the currently active color
            const activeMaterialData = this.materialWholeData.find(
                (item) => item.color === this.activeTab
            )

            if (!activeMaterialData) return

            // Delete the material based on typeSymbol
            switch (typeSymbol) {
                case 0:
                    activeMaterialData.surfaceMaterialData.splice(index, 1)
                    break
                case 1:
                    activeMaterialData.insideMaterialData.splice(index, 1)
                    break
                case 2:
                    activeMaterialData.accessoryMaterialData.splice(index, 1)
                    break
                case 3:
                    activeMaterialData.outsoleMaterialData.splice(index, 1)
                    break
                case 4:
                    activeMaterialData.midsoleMaterialData.splice(index, 1)
                    break
                case 5:
                    activeMaterialData.lastMaterialData.splice(index, 1)
                    break
                case 6:
                    activeMaterialData.hotsoleMaterialData.splice(index, 1)
                    break
                default:
                    break
            }
        },
        uploadCutDieImg() {
            if (this.$refs.uploadImage) {
                this.$refs.uploadImage.submit()
            }
        },
        uploadPicNote() {
            if (this.$refs.uploadImageNote) {
                this.$refs.uploadImageNote.submit()
            }
        },
        uploadProcessSheet() {
            if (this.$refs.uploadProcessSheet) {
                this.$refs.uploadProcessSheet.submit()
            }
        },
        async queryMaterialNames(queryString, callback) {
            if (queryString.trim()) {
                await axios
                    .get(
                        `${this.$apiBaseUrl}/devproductionorder/getautofinishedmaterialname?materialName=${queryString}`
                    )
                    .then((response) => {
                        const suggestions = response.data.map((item) => ({
                            value: item.name
                        }))
                        callback(suggestions)
                    })
                    .catch((error) => {
                        console.error('Failed to fetch material names:', error)
                    })
            } else {
                callback([])
            }
        },
        async handleMaterialNameSelect(row, selectedItem) {
            const response = await axios.get(
                `${this.$apiBaseUrl}/devproductionorder/getmaterialdetail?materialName=${row.materialName}`
            )
            row.materialId = response.data.materialId
            row.unit = response.data.unit
            row.materialType = response.data.materialType
        },
        openCraftDialog(row) {
            this.currentRow = row
            this.inputCrafts = row.materialCraftNameList || []
            this.isCraftDialogVisible = true
        },
        // 添加新的工艺输入框
        addCraft() {
            this.inputCrafts.push('')
        },
        // 移除某个工艺输入框
        removeCraft(index) {
            this.inputCrafts.splice(index, 1)
        },
        // 确认输入
        confirmCraftInput() {
            if (this.currentRow) {
                this.currentRow.materialCraftName = this.inputCrafts
                    .filter((craft) => craft.trim() !== '') // 移除空值
                    .join(', ')
                this.currentRow.materialCraftNameList = this.inputCrafts.filter(
                    (craft) => craft.trim() !== ''
                ) // 移除空值
            }
            this.isCraftDialogVisible = false
        },
        downloadCraftSheet(row) {
            window.open(
                `${this.$apiBaseUrl}/craftsheet/downloadcraftsheet?orderid=${this.orderData.orderId}&ordershoeid=${row.inheritId}`
            )
        },
        downloadProductionInstructionImage(row) {
            window.open(
                `${this.$apiBaseUrl}/devproductionorder/downloadpicnotes?orderid=${this.orderData.orderId}&ordershoerid=${row.inheritId}`
            )
        }
    }
}
</script>

<style scoped>
/* Add your styles here */
</style>
