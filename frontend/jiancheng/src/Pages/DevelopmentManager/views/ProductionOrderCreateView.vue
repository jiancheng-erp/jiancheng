<template>
    <el-container direction="vertical">
        <el-header height="">
            <AllHeader></AllHeader>
        </el-header>
        <el-main style="overflow-x: hidden">
            <el-row :gutter="20" style="text-align: center">
                <el-col :span="24" :offset="0" style="font-size: xx-large; text-align: center"
                    >投产指令单创建</el-col
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
                            :suffix-icon="SearchIcon"
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
                            <template #default="scope">
                                <el-table :data="scope.row.typeInfos" border>
                                    <el-table-column prop="color" label="颜色"></el-table-column>
                                    <el-table-column label="鞋图" align="center">
                                        <template #default="scope">
                                            <el-image
                                                style="width: 150px; height: 100px"
                                                :src="scope.row.image"
                                                fit="contain"
                                            />
                                        </template>
                                    </el-table-column>
                                    <el-table-column
                                        prop="firstBomId"
                                        label="一次BOM表"
                                    ></el-table-column>
                                    <el-table-column
                                        prop="firstPurchaseOrderId"
                                        label="一次采购订单"
                                    ></el-table-column>
                                    <el-table-column
                                        prop="secondBomId"
                                        label="二次BOM表"
                                    ></el-table-column>
                                    <el-table-column
                                        prop="secondPurchaseOrderId"
                                        label="二次采购订单"
                                    ></el-table-column>
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
                            prop="status"
                            label="状态"
                            align="center"
                        ></el-table-column>
                        <el-table-column label="操作" align="center">
                            <template #default="scope">
                                <el-button
                                    v-if="scope.row.status === '未上传'"
                                    type="primary"
                                    @click="openUploadDialog(scope.row)"
                                    >上传投产指令单</el-button
                                >
                                <div v-else-if="scope.row.status === '已下发'">
                                    <el-button type="primary" @click="openPreviewDialog(scope.row)"
                                        >查看</el-button
                                    >
                                    <el-button
                                        type="success"
                                        @click="downloadProductionInstruction(scope.row)"
                                        >下载投产指令单EXCEL</el-button
                                    >
                                    <el-button
                                        type="warning"
                                        @click="downloadProductionInstructionImage(scope.row)"
                                        >下载备注图片</el-button
                                    >
                                </div>

                                <div v-else-if="scope.row.status === '已上传'">
                                    <el-button type="primary" @click="openEditDialog(scope.row)"
                                        >编辑投产指令单</el-button
                                    >
                                    <el-button type="success" @click="openPreviewDialog(scope.row)"
                                        >预览投产指令单</el-button
                                    >
                                    <el-button type="warning" @click="uploadNoteImage(scope.row)"
                                        >上传图片备注</el-button
                                    >
                                </div>
                            </template></el-table-column
                        >
                    </el-table></el-col
                >
            </el-row>
            <el-row :gutter="22" style="margin-top: 10px">
                <el-col :span="6" :offset="20"
                    ><el-button type="primary" size="default" @click="openIssueDialog"
                        >下发投产指令单</el-button
                    >
                </el-col>
            </el-row>
            <el-dialog v-model="isUploadImageDialogVisible" title="上传投产指令单备注图片">
                <el-upload
                    ref="uploadImage"
                    class="upload-image"
                    :action="`${this.$apiBaseUrl}/devproductionorder/uploadpicnotes`"
                    :on-success="handleUploadSuccess"
                    :on-error="handleUploadError"
                    :headers="uploadHeaders"
                    :before-upload="beforeUpload"
                    :file-list="fileList"
                    list-type="picture-card"
                    accept="image/*"
                    :auto-upload="false"
                    :data="{ orderId: orderData.orderId, orderShoeRId: currentShoeId }"
                >
                </el-upload>
                <el-button size="small" type="primary" @click="submitUpload">点击上传</el-button>
                <div slot="tip" class="el-upload__tip">只能上传图片文件</div>
            </el-dialog>

            <el-dialog title="正式投产指令单下发页面" v-model="isFinalBOM" width="90%">
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
                            <el-table
                                :data="unIssueBOMData"
                                border
                                style="height: 400px"
                                @selection-change="handleShoeSelectionChange"
                            >
                                <el-table-column type="selection" width="55"></el-table-column>
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
                                <el-table-column label="操作" align="center">
                                    <template #default="scope">
                                        <el-button
                                            type="primary"
                                            size="default"
                                            @click="openPreviewDialog(scope.row)"
                                            >查看投产指令单</el-button
                                        >
                                    </template>
                                </el-table-column>
                            </el-table>
                        </el-col>
                    </el-row>
                </div>
                <template #footer>
                    <span>
                        <el-button @click="isFinalBOM = false">取消</el-button>
                        <el-button type="primary" @click="issueBOMs(selectedShoe)"
                            >下发选定投产指令单</el-button
                        >
                    </span>
                </template>
            </el-dialog>
            <el-dialog
                :title="`投产指令单创建 ${newProductionInstructionId}`"
                v-model="isProductionOrderCreateDialogVisible"
                width="90%"
                style="height: 700px; overflow-y: scroll"
            >
                <el-descriptions title="投产指令单公用信息" border :column="2">
                    <el-descriptions-item label="本码">
                        <el-input
                            v-model="productionInstructionDetail.originSize"
                            size="default"
                        ></el-input>
                    </el-descriptions-item>
                    <el-descriptions-item label="配码">
                        <el-input
                            v-model="productionInstructionDetail.sizeRange"
                            size="default"
                        ></el-input>
                    </el-descriptions-item>
                    <el-descriptions-item label="码差">
                        <el-input
                            v-model="productionInstructionDetail.sizeDifference"
                            size="default"
                        ></el-input>
                    </el-descriptions-item>
                    <el-descriptions-item label="设计师">
                        <el-input
                            v-model="productionInstructionDetail.designer"
                            size="default"
                        ></el-input>
                    </el-descriptions-item>
                    <el-descriptions-item label="楦型">
                        <el-input
                            v-model="productionInstructionDetail.lastType"
                            size="default"
                        ></el-input>
                    </el-descriptions-item>
                    <el-descriptions-item label="工艺备注">
                        <el-input
                            type="textarea"
                            autosize
                            maxlength="150"
                            show-word-limit
                            v-model="productionInstructionDetail.craftRemark"
                            size="default"
                        ></el-input>
                    </el-descriptions-item>
                </el-descriptions>
                <el-row :gutter="20">
                    <el-col :span="12" :offset="0"
                        ><el-button type="primary" size="default" @click="openLoadMaterialDialog"
                            >加载过往订单</el-button
                        ></el-col
                    >
                </el-row>
                <el-tabs v-model="activeTab">
                    <!-- Generate tabs from backend-provided tabcolor array -->
                    <el-tab-pane
                        v-for="color in tabcolor"
                        :label="color"
                        :key="color"
                        :name="color"
                    >
                        <!-- <el-row>
                            <el-col :span="2" :offset="20">
                                <el-button @click="syncAllMaterials">同步所有材料至所有颜色</el-button>
                            </el-col>
                        </el-row> -->
                        <el-row :gutter="20">
                            <el-col :span="2" :offset="0"> 面料： </el-col>
                            <el-col :span="4" :offset="0">
                                <el-button type="primary" size="default" @click="addMaterial(0)"
                                    >添加面料</el-button
                                >
                                <el-button
                                    type="primary"
                                    size="default"
                                    @click="addMaterialByManual(0)"
                                    >手动添加面料</el-button
                                >
                            </el-col>
                            <el-col :span="2" :offset="0">
                                <el-button @click="syncMaterials(0)">{{
                                    this.syncMaterialButtonText
                                }}</el-button>
                            </el-col>
                        </el-row>
                        <el-row :gutter="20">
                            <el-col :span="23" :offset="0">
                                <el-table
                                    :data="getMaterialDataByType('surfaceMaterialData')"
                                    border
                                    style="width: 100%"
                                >
                                    <el-table-column type="index"></el-table-column>
                                    <el-table-column prop="materialType" label="材料类型" />
                                    <el-table-column prop="materialDetailType" label="材料二级类型">
                                        <template #default="scope">
                                            <el-input
                                                v-model="scope.row.materialDetailType"
                                            ></el-input>
                                        </template>
                                    </el-table-column>
                                    <el-table-column prop="supplierName" label="厂家名称">
                                        <template #default="scope">
                                            <el-autocomplete
                                                v-if="
                                                    scope !== undefined &&
                                                    scope.row.manualSymbol === 1
                                                "
                                                v-model="scope.row.supplierName"
                                                size="default"
                                                :fetch-suggestions="querySupplierNames"
                                                placeholder="输入厂家名称"
                                                @select="
                                                    handleSupplierNameSelect(scope.row, $event)
                                                "
                                            ></el-autocomplete>
                                        </template>
                                    </el-table-column>
                                    <el-table-column prop="materialName" label="材料名称">
                                        <template #default="scope">
                                            <el-select
                                                v-if="
                                                    scope !== undefined &&
                                                    scope.row.manualSymbol === 1
                                                "
                                                v-model="scope.row.materialName"
                                                filterable
                                                @change="
                                                    handleMaterialNameSelect(scope.row, $event)
                                                "
                                            >
                                                <el-option
                                                    v-for="item in materialNameOptions"
                                                    :key="item.value"
                                                    :value="item.value"
                                                    :label="item.label"
                                                >
                                                </el-option>
                                            </el-select>
                                            <!-- <el-autocomplete
                                                v-if="
                                                    scope !== undefined &&
                                                    scope.row.manualSymbol === 1
                                                "
                                                v-model="scope.row.materialName"
                                                size="default"
                                                :fetch-suggestions="queryMaterialNames"
                                                placeholder="输入材料名称"
                                                @select="
                                                    handleMaterialNameSelect(scope.row, $event)
                                                "
                                            ></el-autocomplete> -->
                                        </template>
                                    </el-table-column>
                                    <el-table-column prop="materialModel" label="材料型号">
                                        <template #default="scope">
                                            <el-input
                                                type="textarea"
                                                autosize
                                                v-model="scope.row.materialModel"
                                                size="default"
                                            ></el-input>
                                        </template>
                                    </el-table-column>
                                    <el-table-column prop="materialSpecification" label="材料规格">
                                        <template #default="scope">
                                            <el-input
                                                type="textarea"
                                                autosize
                                                v-model="scope.row.materialSpecification"
                                                size="default"
                                            ></el-input>
                                        </template>
                                    </el-table-column>
                                    <el-table-column prop="color" label="颜色">
                                        <template #default="scope">
                                            <el-input
                                                v-model="scope.row.color"
                                                size="default"
                                            ></el-input>
                                        </template>
                                    </el-table-column>
                                    <el-table-column prop="unit" label="单位"></el-table-column>
                                    <el-table-column prop="comment" label="备注">
                                        <template #default="scope">
                                            <el-input
                                                type="textarea"
                                                autosize
                                                v-model="scope.row.comment"
                                                size="default"
                                            ></el-input>
                                        </template>
                                    </el-table-column>
                                    <el-table-column label="操作">
                                        <template #default="scope">
                                            <el-button
                                                type="danger"
                                                size="small"
                                                @click="deleteMaterial(scope.$index, 0)"
                                                >删除</el-button
                                            >
                                        </template>
                                    </el-table-column>
                                </el-table>
                            </el-col>
                        </el-row>

                        <el-row :gutter="20">
                            <el-col :span="2" :offset="0"> 里料： </el-col>
                            <el-col :span="4" :offset="0">
                                <el-button type="primary" size="default" @click="addMaterial(1)"
                                    >添加里料</el-button
                                >
                                <el-button
                                    type="primary"
                                    size="default"
                                    @click="addMaterialByManual(1)"
                                    >手动添加里料</el-button
                                >
                            </el-col>
                            <el-col :span="2" :offset="0">
                                <el-button @click="syncMaterials(1)">{{
                                    this.syncMaterialButtonText
                                }}</el-button>
                            </el-col>
                        </el-row>
                        <el-row :gutter="20">
                            <el-col :span="23" :offset="0">
                                <el-table
                                    :data="getMaterialDataByType('insideMaterialData')"
                                    border
                                    style="width: 100%"
                                >
                                    <el-table-column type="index"></el-table-column>
                                    <el-table-column prop="materialType" label="材料类型" />
                                    <el-table-column prop="materialDetailType" label="材料二级类型">
                                        <template #default="scope">
                                            <el-input
                                                v-model="scope.row.materialDetailType"
                                            ></el-input>
                                        </template>
                                    </el-table-column>
                                    <el-table-column prop="supplierName" label="厂家名称">
                                        <template #default="scope">
                                            <el-autocomplete
                                                v-if="
                                                    scope !== undefined &&
                                                    scope.row.manualSymbol === 1
                                                "
                                                v-model="scope.row.supplierName"
                                                size="default"
                                                :fetch-suggestions="querySupplierNames"
                                                placeholder="输入厂家名称"
                                                @select="
                                                    handleSupplierNameSelect(scope.row, $event)
                                                "
                                            ></el-autocomplete>
                                        </template>
                                    </el-table-column>
                                    <el-table-column prop="materialName" label="材料名称">
                                        <template #default="scope">
                                            <el-select
                                                v-if="
                                                    scope !== undefined &&
                                                    scope.row.manualSymbol === 1
                                                "
                                                v-model="scope.row.materialName"
                                                filterable
                                                @change="
                                                    handleMaterialNameSelect(scope.row, $event)
                                                "
                                            >
                                                <el-option
                                                    v-for="item in materialNameOptions"
                                                    :key="item.value"
                                                    :value="item.value"
                                                    :label="item.label"
                                                >
                                                </el-option>
                                            </el-select>
                                        </template>
                                    </el-table-column>
                                    <el-table-column prop="materialModel" label="材料型号">
                                        <template #default="scope">
                                            <el-input
                                                type="textarea"
                                                autosize
                                                v-model="scope.row.materialModel"
                                                size="default"
                                            ></el-input>
                                        </template>
                                    </el-table-column>
                                    <el-table-column prop="materialSpecification" label="材料规格">
                                        <template #default="scope">
                                            <el-input
                                                type="textarea"
                                                autosize
                                                v-model="scope.row.materialSpecification"
                                                size="default"
                                            ></el-input>
                                        </template>
                                    </el-table-column>
                                    <el-table-column prop="color" label="颜色">
                                        <template #default="scope">
                                            <el-input
                                                v-model="scope.row.color"
                                                size="default"
                                            ></el-input>
                                        </template>
                                    </el-table-column>
                                    <el-table-column prop="unit" label="单位"></el-table-column>
                                    <el-table-column prop="comment" label="备注">
                                        <template #default="scope">
                                            <el-input
                                                type="textarea"
                                                autosize
                                                v-model="scope.row.comment"
                                                size="default"
                                            ></el-input>
                                        </template>
                                    </el-table-column>
                                    <el-table-column label="操作">
                                        <template #default="scope">
                                            <el-button
                                                type="danger"
                                                size="small"
                                                @click="deleteMaterial(scope.$index, 1)"
                                                >删除</el-button
                                            >
                                        </template>
                                    </el-table-column>
                                </el-table>
                            </el-col>
                        </el-row>
                        <el-row :gutter="20">
                            <el-col :span="2" :offset="0"> 辅料： </el-col>
                            <el-col :span="4" :offset="0">
                                <el-button type="primary" size="default" @click="addMaterial(2)"
                                    >添加辅料</el-button
                                >
                                <el-button
                                    type="primary"
                                    size="default"
                                    @click="addMaterialByManual(2)"
                                    >手动添加辅料</el-button
                                >
                            </el-col>
                            <el-col :span="2" :offset="0">
                                <el-button @click="syncMaterials(2)">{{
                                    this.syncMaterialButtonText
                                }}</el-button>
                            </el-col>
                        </el-row>
                        <el-row :gutter="20">
                            <el-col :span="23" :offset="0">
                                <el-table
                                    :data="getMaterialDataByType('accessoryMaterialData')"
                                    border
                                    style="width: 100%"
                                >
                                    <el-table-column type="index"></el-table-column>
                                    <el-table-column prop="materialType" label="材料类型" />
                                    <el-table-column prop="materialDetailType" label="材料二级类型">
                                        <template #default="scope">
                                            <el-input
                                                v-model="scope.row.materialDetailType"
                                            ></el-input>
                                        </template>
                                    </el-table-column>
                                    <el-table-column prop="supplierName" label="厂家名称">
                                        <template #default="scope">
                                            <el-autocomplete
                                                v-if="
                                                    scope !== undefined &&
                                                    scope.row.manualSymbol === 1
                                                "
                                                v-model="scope.row.supplierName"
                                                size="default"
                                                :fetch-suggestions="querySupplierNames"
                                                placeholder="输入厂家名称"
                                                @select="
                                                    handleSupplierNameSelect(scope.row, $event)
                                                "
                                            ></el-autocomplete>
                                        </template>
                                    </el-table-column>
                                    <el-table-column prop="materialName" label="材料名称">
                                        <template #default="scope">
                                            <el-select
                                                v-if="
                                                    scope !== undefined &&
                                                    scope.row.manualSymbol === 1
                                                "
                                                v-model="scope.row.materialName"
                                                filterable
                                                @change="
                                                    handleMaterialNameSelect(scope.row, $event)
                                                "
                                            >
                                                <el-option
                                                    v-for="item in materialNameOptions"
                                                    :key="item.value"
                                                    :value="item.value"
                                                    :label="item.label"
                                                >
                                                </el-option>
                                            </el-select>
                                        </template>
                                    </el-table-column>
                                    <el-table-column prop="materialModel" label="材料型号">
                                        <template #default="scope">
                                            <el-input
                                                type="textarea"
                                                autosize
                                                v-model="scope.row.materialModel"
                                                size="default"
                                            ></el-input>
                                        </template>
                                    </el-table-column>
                                    <el-table-column prop="materialSpecification" label="材料规格">
                                        <template #default="scope">
                                            <el-input
                                                type="textarea"
                                                autosize
                                                v-model="scope.row.materialSpecification"
                                                size="default"
                                            ></el-input>
                                        </template>
                                    </el-table-column>
                                    <el-table-column prop="color" label="颜色">
                                        <template #default="scope">
                                            <el-input
                                                v-model="scope.row.color"
                                                size="default"
                                            ></el-input>
                                        </template>
                                    </el-table-column>
                                    <el-table-column prop="unit" label="单位"></el-table-column>
                                    <el-table-column prop="comment" label="备注">
                                        <template #default="scope">
                                            <el-input
                                                type="textarea"
                                                autosize
                                                v-model="scope.row.comment"
                                                size="default"
                                            ></el-input>
                                        </template>
                                    </el-table-column>
                                    <el-table-column label="操作">
                                        <template #default="scope">
                                            <el-button
                                                type="danger"
                                                size="small"
                                                @click="deleteMaterial(scope.$index, 2)"
                                                >删除</el-button
                                            >
                                        </template>
                                    </el-table-column>
                                </el-table>
                            </el-col>
                        </el-row>
                        <el-row :gutter="20">
                            <el-col :span="2" :offset="0"> 大底： </el-col>
                            <el-col :span="4" :offset="0">
                                <el-button type="primary" size="default" @click="addMaterial(3)"
                                    >添加大底</el-button
                                >
                                <el-button
                                    type="primary"
                                    size="default"
                                    @click="addMaterialByManual(3)"
                                    >手动添加大底</el-button
                                >
                            </el-col>
                            <el-col :span="2" :offset="0">
                                <el-button @click="syncMaterials(3)">{{
                                    this.syncMaterialButtonText
                                }}</el-button>
                            </el-col>
                        </el-row>
                        <el-row :gutter="20">
                            <el-col :span="23" :offset="0">
                                <el-table
                                    :data="getMaterialDataByType('outsoleMaterialData')"
                                    border
                                    style="width: 100%"
                                >
                                    <el-table-column type="index"></el-table-column>
                                    <el-table-column prop="materialType" label="材料类型" />
                                    <el-table-column prop="materialDetailType" label="材料二级类型">
                                        <template #default="scope">
                                            <el-input
                                                v-model="scope.row.materialDetailType"
                                            ></el-input>
                                        </template>
                                    </el-table-column>
                                    <el-table-column prop="supplierName" label="厂家名称">
                                        <template #default="scope">
                                            <el-autocomplete
                                                v-if="
                                                    scope !== undefined &&
                                                    scope.row.manualSymbol === 1
                                                "
                                                v-model="scope.row.supplierName"
                                                size="default"
                                                :fetch-suggestions="querySupplierNames"
                                                placeholder="输入厂家名称"
                                                @select="
                                                    handleSupplierNameSelect(scope.row, $event)
                                                "
                                            ></el-autocomplete>
                                        </template>
                                    </el-table-column>
                                    <el-table-column prop="materialName" label="材料名称">
                                        <template #default="scope">
                                            <el-select
                                                v-if="
                                                    scope !== undefined &&
                                                    scope.row.manualSymbol === 1
                                                "
                                                v-model="scope.row.materialName"
                                                filterable
                                                @change="
                                                    handleMaterialNameSelect(scope.row, $event)
                                                "
                                            >
                                                <el-option
                                                    v-for="item in materialNameOptions"
                                                    :key="item.value"
                                                    :value="item.value"
                                                    :label="item.label"
                                                >
                                                </el-option>
                                            </el-select>
                                        </template>
                                    </el-table-column>
                                    <el-table-column prop="materialModel" label="材料型号">
                                        <template #default="scope">
                                            <el-input
                                                type="textarea"
                                                autosize
                                                v-model="scope.row.materialModel"
                                                size="default"
                                            ></el-input>
                                        </template>
                                    </el-table-column>
                                    <el-table-column prop="materialSpecification" label="材料规格">
                                        <template #default="scope">
                                            <el-input
                                                type="textarea"
                                                autosize
                                                v-model="scope.row.materialSpecification"
                                                size="default"
                                            ></el-input>
                                        </template>
                                    </el-table-column>
                                    <el-table-column prop="color" label="颜色">
                                        <template #default="scope">
                                            <el-input
                                                v-model="scope.row.color"
                                                size="default"
                                            ></el-input>
                                        </template>
                                    </el-table-column>
                                    <el-table-column prop="unit" label="单位"></el-table-column>
                                    <el-table-column prop="comment" label="备注">
                                        <template #default="scope">
                                            <el-input
                                                type="textarea"
                                                autosize
                                                v-model="scope.row.comment"
                                                size="default"
                                            ></el-input>
                                        </template>
                                    </el-table-column>
                                    <el-table-column label="操作">
                                        <template #default="scope">
                                            <el-button
                                                type="danger"
                                                size="small"
                                                @click="deleteMaterial(scope.$index, 3)"
                                                >删除</el-button
                                            >
                                        </template>
                                    </el-table-column>
                                </el-table>
                            </el-col>
                        </el-row>
                        <el-row :gutter="20">
                            <el-col :span="2" :offset="0"> 中底： </el-col>
                            <el-col :span="4" :offset="0">
                                <el-button type="primary" size="default" @click="addMaterial(4)"
                                    >添加中底</el-button
                                >
                                <el-button
                                    type="primary"
                                    size="default"
                                    @click="addMaterialByManual(4)"
                                    >手动添加中底</el-button
                                >
                            </el-col>
                            <el-col :span="2" :offset="0">
                                <el-button @click="syncMaterials(4)">{{
                                    this.syncMaterialButtonText
                                }}</el-button>
                            </el-col>
                        </el-row>
                        <el-row :gutter="20">
                            <el-col :span="23" :offset="0">
                                <el-table
                                    :data="getMaterialDataByType('midsoleMaterialData')"
                                    border
                                    style="width: 100%"
                                >
                                    <el-table-column type="index"></el-table-column>
                                    <el-table-column prop="materialType" label="材料类型" />
                                    <el-table-column prop="materialDetailType" label="材料二级类型">
                                        <template #default="scope">
                                            <el-input
                                                v-model="scope.row.materialDetailType"
                                            ></el-input>
                                        </template>
                                    </el-table-column>
                                    <el-table-column prop="supplierName" label="厂家名称">
                                        <template #default="scope">
                                            <el-autocomplete
                                                v-if="
                                                    scope !== undefined &&
                                                    scope.row.manualSymbol === 1
                                                "
                                                v-model="scope.row.supplierName"
                                                size="default"
                                                :fetch-suggestions="querySupplierNames"
                                                placeholder="输入厂家名称"
                                                @select="
                                                    handleSupplierNameSelect(scope.row, $event)
                                                "
                                            ></el-autocomplete>
                                        </template>
                                    </el-table-column>
                                    <el-table-column prop="materialName" label="材料名称">
                                        <template #default="scope">
                                            <el-select
                                                v-if="
                                                    scope !== undefined &&
                                                    scope.row.manualSymbol === 1
                                                "
                                                v-model="scope.row.materialName"
                                                filterable
                                                @change="
                                                    handleMaterialNameSelect(scope.row, $event)
                                                "
                                            >
                                                <el-option
                                                    v-for="item in materialNameOptions"
                                                    :key="item.value"
                                                    :value="item.value"
                                                    :label="item.label"
                                                >
                                                </el-option>
                                            </el-select>
                                        </template>
                                    </el-table-column>
                                    <el-table-column prop="materialModel" label="材料型号">
                                        <template #default="scope">
                                            <el-input
                                                type="textarea"
                                                autosize
                                                v-model="scope.row.materialModel"
                                                size="default"
                                            ></el-input>
                                        </template>
                                    </el-table-column>
                                    <el-table-column prop="materialSpecification" label="材料规格">
                                        <template #default="scope">
                                            <el-input
                                                type="textarea"
                                                autosize
                                                v-model="scope.row.materialSpecification"
                                                size="default"
                                            ></el-input>
                                        </template>
                                    </el-table-column>
                                    <el-table-column prop="color" label="颜色">
                                        <template #default="scope">
                                            <el-input
                                                v-model="scope.row.color"
                                                size="default"
                                            ></el-input>
                                        </template>
                                    </el-table-column>
                                    <el-table-column prop="unit" label="单位"></el-table-column>
                                    <el-table-column prop="comment" label="备注">
                                        <template #default="scope">
                                            <el-input
                                                type="textarea"
                                                autosize
                                                v-model="scope.row.comment"
                                                size="default"
                                            ></el-input>
                                        </template>
                                    </el-table-column>
                                    <el-table-column label="操作">
                                        <template #default="scope">
                                            <el-button
                                                type="danger"
                                                size="small"
                                                @click="deleteMaterial(scope.$index, 4)"
                                                >删除</el-button
                                            >
                                        </template>
                                    </el-table-column>
                                </el-table>
                            </el-col>
                        </el-row>
                        <el-row :gutter="20">
                            <el-col :span="2" :offset="0"> 烫底： </el-col>
                            <el-col :span="6" :offset="0">
                                <el-button type="primary" size="default" @click="addMaterial(6)"
                                    >添加烫底</el-button
                                >
                                <el-button
                                    type="primary"
                                    size="default"
                                    @click="addMaterialByManual(6)"
                                    >手动添加独立烫底</el-button
                                >
                                <el-button
                                    type="primary"
                                    size="default"
                                    @click="addMaterialByManual(7)"
                                    >手动添加加工烫底</el-button
                                >
                            </el-col>
                            <el-col :span="2" :offset="0">
                                <el-button @click="syncMaterials(6)">{{
                                    this.syncMaterialButtonText
                                }}</el-button>
                            </el-col>
                        </el-row>
                        <el-row :gutter="20">
                            <el-col :span="23" :offset="0">
                                <el-table
                                    :data="getMaterialDataByType('hotsoleMaterialData')"
                                    border
                                    style="width: 100%"
                                >
                                    <el-table-column type="index"></el-table-column>
                                    <el-table-column prop="materialType" label="材料类型" />
                                    <el-table-column prop="materialDetailType" label="材料二级类型">
                                        <template #default="scope">
                                            <el-input
                                                v-model="scope.row.materialDetailType"
                                            ></el-input>
                                        </template>
                                    </el-table-column>
                                    <el-table-column prop="supplierName" label="厂家名称">
                                        <template #default="scope">
                                            <el-autocomplete
                                                v-if="
                                                    scope !== undefined &&
                                                    scope.row.manualSymbol === 1
                                                "
                                                v-model="scope.row.supplierName"
                                                size="default"
                                                :fetch-suggestions="querySupplierNames"
                                                placeholder="输入厂家名称"
                                                @select="
                                                    handleSupplierNameSelect(scope.row, $event)
                                                "
                                            ></el-autocomplete>
                                        </template>
                                    </el-table-column>
                                    <el-table-column prop="materialName" label="材料名称">
                                        <template #default="scope">
                                            <el-select
                                                v-if="
                                                    scope !== undefined &&
                                                    scope.row.manualSymbol === 1
                                                "
                                                v-model="scope.row.materialName"
                                                filterable
                                                @change="
                                                    handleMaterialNameSelect(scope.row, $event)
                                                "
                                            >
                                                <el-option
                                                    v-for="item in materialNameOptions"
                                                    :key="item.value"
                                                    :value="item.value"
                                                    :label="item.label"
                                                >
                                                </el-option>
                                            </el-select>
                                        </template>
                                    </el-table-column>
                                    <el-table-column prop="materialModel" label="材料型号">
                                        <template #default="scope">
                                            <el-input
                                                type="textarea"
                                                autosize
                                                v-model="scope.row.materialModel"
                                                size="default"
                                            ></el-input>
                                        </template>
                                    </el-table-column>
                                    <el-table-column prop="materialSpecification" label="材料规格">
                                        <template #default="scope">
                                            <el-input
                                                type="textarea"
                                                autosize
                                                v-model="scope.row.materialSpecification"
                                                size="default"
                                            ></el-input>
                                        </template>
                                    </el-table-column>
                                    <el-table-column prop="craftName" label="工艺名称">
                                        <template #default="scope">
                                            <el-input
                                                type="textarea"
                                                autosize
                                                v-model="scope.row.craftName"
                                                size="default"
                                            ></el-input>
                                        </template>
                                    </el-table-column>
                                    <el-table-column prop="color" label="颜色">
                                        <template #default="scope">
                                            <el-input
                                                v-model="scope.row.color"
                                                size="default"
                                            ></el-input>
                                        </template>
                                    </el-table-column>
                                    <el-table-column prop="unit" label="单位"></el-table-column>
                                    <el-table-column prop="comment" label="备注">
                                        <template #default="scope">
                                            <el-input
                                                type="textarea"
                                                autosize
                                                v-model="scope.row.comment"
                                                size="default"
                                            ></el-input>
                                        </template>
                                    </el-table-column>
                                    <el-table-column label="操作">
                                        <template #default="scope">
                                            <el-button
                                                type="danger"
                                                size="small"
                                                @click="deleteMaterial(scope.$index, 6)"
                                                >删除</el-button
                                            >
                                        </template>
                                    </el-table-column>
                                </el-table>
                            </el-col>
                        </el-row>
                    </el-tab-pane>
                </el-tabs>

                <template #footer>
                    <span>
                        <el-button @click="isProductionOrderCreateDialogVisible = false"
                            >取消</el-button
                        >
                        <el-button type="primary" @click="saveProductionInstruction"
                            >确认保存</el-button
                        >
                    </span>
                </template>
            </el-dialog>
            <el-dialog title="加载过往鞋型材料" v-model="isLoadMaterialDialogVisible" width="50%">
                <el-table :data="pastShoeInfoTable" border>
                    <el-table-column type="expand">
                        <template #default="scope">
                            <el-table
                                ref="orderShoeTypeTable"
                                :data="scope.row.shoeColors"
                                border
                                @selection-change="handleShoeTypeSelectionChange"
                            >
                                <el-table-column type="selection"></el-table-column>
                                <el-table-column prop="color" label="颜色"></el-table-column>
                                <el-table-column label="鞋图">
                                    <template #default="scope">
                                        <el-image
                                            style="width: 100px; height: 50px"
                                            :src="scope.row.shoeImageUrl"
                                        />
                                    </template>
                                </el-table-column>
                                <el-table-column label="操作">
                                    <template #default="scope">
                                        <el-button
                                            type="primary"
                                            size="default"
                                            @click="openLoadMaterialDialogByColor(scope.row)"
                                            >查看材料</el-button
                                        >
                                    </template>
                                </el-table-column>
                            </el-table>
                        </template>
                    </el-table-column>
                    <el-table-column prop="inheritId" label="工厂型号"></el-table-column>
                    <el-table-column prop="designer" label="设计员"></el-table-column>
                </el-table>
                <template #footer>
                    <span>
                        <el-button
                            @click="
                                isLoadMaterialDialogVisible = false;
                                selectShoeTypeRow = {}
                            "
                            >取消</el-button
                        >
                        <el-button type="primary" @click="addPastMaterialToCurrent"
                            >确认加载</el-button
                        >
                    </span>
                </template>
            </el-dialog>
            <el-dialog
                title="过往订单材料查看"
                v-model="isPastShoeMaterialDetailDialogVisible"
                width="80%"
            >
                <el-descriptions title="鞋型基本信息" border column="2">
                    <el-descriptions-item label="鞋图" rowspan="2" align="center">
                        <el-image
                            style="width: 150px; height: 75px"
                            :src="pastShoeDescription.shoeImageUrl"
                        />
                    </el-descriptions-item>
                    <el-descriptions-item label="工厂型号" align="center">{{
                        pastShoeDescription.shoeId
                    }}</el-descriptions-item>
                    <el-descriptions-item label="颜色" align="center">{{
                        pastShoeDescription.color
                    }}</el-descriptions-item>
                </el-descriptions>
                <el-table :data="pastMaterialData" border>
                    <el-table-column prop="materialType" label="材料类型"></el-table-column>
                    <el-table-column
                        prop="materialDetailType"
                        label="材料二级类型"
                    ></el-table-column>
                    <el-table-column prop="supplierName" label="厂家名称"></el-table-column>
                    <el-table-column prop="materialName" label="材料名称"></el-table-column>
                    <el-table-column prop="materialModel" label="材料型号"></el-table-column>
                    <el-table-column
                        prop="materialSpecification"
                        label="材料规格"
                    ></el-table-column>
                    <el-table-column prop="craftName" label="工艺名称"></el-table-column>
                    <el-table-column prop="color" label="颜色"></el-table-column>
                    <el-table-column prop="unit" label="单位"></el-table-column>
                    <el-table-column prop="comment" label="备注"></el-table-column>
                </el-table>
                <template #footer>
                    <span>
                        <el-button
                            type="primary"
                            @click="isPastShoeMaterialDetailDialogVisible = false"
                            >确认</el-button
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
                                :suffix-icon="SearchIcon"
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
                                :suffix-icon="SearchIcon"
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
                                :suffix-icon="SearchIcon"
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
                        <el-button type="primary" @click="confirmNewMaterialAdd(typeSymbol)"
                            >保存</el-button
                        >
                    </span>
                </template>
            </el-dialog>
            <el-dialog
                :title="`投产指令单预览 ${newProductionInstructionId}`"
                v-model="isPreviewDialogVisible"
                width="90%"
            >
                <div style="height: 650px; overflow-y: scroll">
                    <el-row :gutter="20">
                        <el-col :span="23" :offset="0">
                            <el-descriptions
                                title="鞋型基本信息"
                                border
                                direction="vertical"
                                column="4"
                                style="margin-top: 20px"
                            >
                                <el-descriptions-item
                                    label="鞋图"
                                    :rowspan="3"
                                    align="center"
                                    :width="200"
                                >
                                    <el-image
                                        style="width: 200px; height: 100px"
                                        :src="currentShoeImageUrl"
                                    />
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
                            <el-descriptions title="投产指令单公用信息" border :column="2">
                                <el-descriptions-item label="本码">
                                    {{ productionInstructionDetail.originSize }}
                                </el-descriptions-item>
                                <el-descriptions-item label="配码">
                                    {{ productionInstructionDetail.sizeRange }}
                                </el-descriptions-item>
                                <el-descriptions-item label="码差">
                                    {{ productionInstructionDetail.sizeDifference }}
                                </el-descriptions-item>
                                <el-descriptions-item label="楦型">
                                    {{ productionInstructionDetail.lastType }}
                                </el-descriptions-item>
                                <el-descriptions-item label="设计师">
                                    {{ productionInstructionDetail.designer }}
                                </el-descriptions-item>
                                <el-descriptions-item label="烫底工艺">
                                    {{ productionInstructionDetail.burnSoleCraft }}
                                </el-descriptions-item>
                                <el-descriptions-item label="工艺备注">
                                    {{ productionInstructionDetail.craftRemark }}
                                </el-descriptions-item>
                            </el-descriptions>
                        </el-col>
                    </el-row>

                    <el-tabs v-model="activeTab">
                        <!-- Generate tabs from backend-provided tabcolor array -->
                        <el-tab-pane
                            v-for="color in tabcolor"
                            :label="color"
                            :key="color"
                            :name="color"
                            style="overflow-y: scroll"
                        >
                            <el-row :gutter="20">
                                <el-col :span="2" :offset="0"> 面料： </el-col>
                            </el-row>
                            <el-row :gutter="20">
                                <el-col :span="23" :offset="0">
                                    <MaterialDataTable
                                        :tableData="getMaterialDataByType('surfaceMaterialData')"
                                    />
                                </el-col>
                            </el-row>
                            <el-row :gutter="20">
                                <el-col :span="2" :offset="0"> 里料： </el-col>
                            </el-row>
                            <el-row :gutter="20">
                                <el-col :span="23" :offset="0">
                                    <MaterialDataTable
                                        :tableData="getMaterialDataByType('insideMaterialData')"
                                    />
                                </el-col>
                            </el-row>
                            <el-row :gutter="20">
                                <el-col :span="2" :offset="0"> 辅料： </el-col>
                            </el-row>
                            <el-row :gutter="20">
                                <el-col :span="23" :offset="0">
                                    <MaterialDataTable
                                        :tableData="getMaterialDataByType('accessoryMaterialData')"
                                    />
                                </el-col>
                            </el-row>
                            <el-row :gutter="20">
                                <el-col :span="2" :offset="0"> 大底： </el-col>
                            </el-row>
                            <el-row :gutter="20">
                                <el-col :span="23" :offset="0">
                                    <MaterialDataTable
                                        :tableData="getMaterialDataByType('outsoleMaterialData')"
                                    />
                                </el-col>
                            </el-row>
                            <el-row :gutter="20">
                                <el-col :span="2" :offset="0"> 中底： </el-col>
                            </el-row>
                            <el-row :gutter="20">
                                <el-col :span="23" :offset="0">
                                    <MaterialDataTable
                                        :tableData="getMaterialDataByType('midsoleMaterialData')"
                                    />
                                </el-col>
                            </el-row>
                            <el-row :gutter="20">
                                <el-col :span="2" :offset="0"> 烫底： </el-col>
                            </el-row>
                            <el-row :gutter="20">
                                <el-col :span="23" :offset="0">
                                    <MaterialDataTable
                                        :tableData="getMaterialDataByType('hotsoleMaterialData')"
                                    />
                                </el-col>
                            </el-row>
                        </el-tab-pane>
                    </el-tabs>
                </div>

                <template #footer>
                    <span>
                        <el-button type="primary" @click="isPreviewDialogVisible = false"
                            >确认</el-button
                        >
                    </span>
                </template>
            </el-dialog>
            <el-dialog
                :title="`编辑投产指令单 ${newProductionInstructionId}`"
                v-model="isEditDialogVisible"
                width="90%"
                style="height: 700px; overflow-y: scroll"
            >
                <el-descriptions title="投产指令单公用信息" border :column="2">
                    <el-descriptions-item label="本码">
                        <el-input
                            v-model="productionInstructionDetail.originSize"
                            size="default"
                        ></el-input>
                    </el-descriptions-item>
                    <el-descriptions-item label="配码">
                        <el-input
                            v-model="productionInstructionDetail.sizeRange"
                            size="default"
                        ></el-input>
                    </el-descriptions-item>
                    <el-descriptions-item label="码差">
                        <el-input
                            v-model="productionInstructionDetail.sizeDifference"
                            size="default"
                        ></el-input>
                    </el-descriptions-item>
                    <el-descriptions-item label="设计师">
                        <el-input
                            v-model="productionInstructionDetail.designer"
                            size="default"
                        ></el-input>
                    </el-descriptions-item>
                    <el-descriptions-item label="楦型">
                        <el-input
                            v-model="productionInstructionDetail.lastType"
                            size="default"
                        ></el-input>
                    </el-descriptions-item>
                    <el-descriptions-item label="工艺备注">
                        <el-input
                            type="textarea"
                            autosize
                            maxlength="150"
                            show-word-limit
                            v-model="productionInstructionDetail.craftRemark"
                            size="default"
                        ></el-input>
                    </el-descriptions-item>
                </el-descriptions>
                <el-row :gutter="20">
                    <el-col :span="12" :offset="0"
                        ><el-button type="primary" size="default" @click="openLoadMaterialDialog"
                            >加载过往订单</el-button
                        ></el-col
                    >
                </el-row>
                <el-tabs v-model="activeTab">
                    <!-- Generate tabs from backend-provided tabcolor array -->
                    <el-tab-pane
                        v-for="color in tabcolor"
                        :label="color"
                        :key="color"
                        :name="color"
                    >
                        <!-- <el-row>
                            <el-col :span="2" :offset="20">
                                <el-button>同步所有材料至所有颜色</el-button>
                            </el-col>
                        </el-row> -->
                        <el-row :gutter="20">
                            <el-col :span="2" :offset="0"> 面料： </el-col>
                            <el-col :span="4" :offset="0">
                                <el-button type="primary" size="default" @click="addMaterial(0)"
                                    >添加面料</el-button
                                >
                                <el-button
                                    type="primary"
                                    size="default"
                                    @click="addMaterialByManual(0)"
                                    >手动添加面料</el-button
                                >
                            </el-col>
                            <el-col :span="2" :offset="0">
                                <el-button @click="syncMaterials(0)">{{
                                    this.syncMaterialButtonText
                                }}</el-button>
                            </el-col>
                        </el-row>
                        <el-row :gutter="20">
                            <el-col :span="23" :offset="0">
                                <el-table
                                    :data="getMaterialDataByType('surfaceMaterialData')"
                                    border
                                    style="width: 100%"
                                >
                                    <el-table-column type="index"></el-table-column>
                                    <el-table-column prop="materialType" label="材料类型" />
                                    <el-table-column prop="materialDetailType" label="材料二级类型">
                                        <template #default="scope">
                                            <el-input
                                                v-model="scope.row.materialDetailType"
                                            ></el-input>
                                        </template>
                                    </el-table-column>
                                    <el-table-column prop="supplierName" label="厂家名称">
                                        <template #default="scope">
                                            <el-autocomplete
                                                v-if="
                                                    scope !== undefined &&
                                                    scope.row.manualSymbol === 1
                                                "
                                                v-model="scope.row.supplierName"
                                                size="default"
                                                :fetch-suggestions="querySupplierNames"
                                                placeholder="输入厂家名称"
                                                @select="
                                                    handleSupplierNameSelect(scope.row, $event)
                                                "
                                            ></el-autocomplete>
                                        </template>
                                    </el-table-column>
                                    <el-table-column prop="materialName" label="材料名称">
                                        <template #default="scope">
                                            <el-select
                                                v-if="
                                                    scope !== undefined &&
                                                    scope.row.manualSymbol === 1
                                                "
                                                v-model="scope.row.materialName"
                                                filterable
                                                @change="
                                                    handleMaterialNameSelect(scope.row, $event)
                                                "
                                            >
                                                <el-option
                                                    v-for="item in materialNameOptions"
                                                    :key="item.value"
                                                    :value="item.value"
                                                    :label="item.label"
                                                >
                                                </el-option>
                                            </el-select>
                                        </template>
                                    </el-table-column>
                                    <el-table-column prop="materialModel" label="材料型号">
                                        <template #default="scope">
                                            <el-input
                                                type="textarea"
                                                autosize
                                                v-model="scope.row.materialModel"
                                                size="default"
                                            ></el-input>
                                        </template>
                                    </el-table-column>
                                    <el-table-column prop="materialSpecification" label="材料规格">
                                        <template #default="scope">
                                            <el-input
                                                type="textarea"
                                                autosize
                                                v-model="scope.row.materialSpecification"
                                                size="default"
                                            ></el-input>
                                        </template>
                                    </el-table-column>
                                    <el-table-column prop="color" label="颜色">
                                        <template #default="scope">
                                            <el-input
                                                v-model="scope.row.color"
                                                size="default"
                                            ></el-input>
                                        </template>
                                    </el-table-column>
                                    <el-table-column prop="unit" label="单位"></el-table-column>

                                    <el-table-column prop="comment" label="备注">
                                        <template #default="scope">
                                            <el-input
                                                type="textarea"
                                                autosize
                                                v-model="scope.row.comment"
                                                size="default"
                                            ></el-input>
                                        </template>
                                    </el-table-column>

                                    <el-table-column label="操作">
                                        <template #default="scope">
                                            <el-button
                                                type="danger"
                                                size="small"
                                                @click="deleteMaterial(scope.$index, 0)"
                                                >删除</el-button
                                            >
                                        </template>
                                    </el-table-column>
                                </el-table>
                            </el-col>
                        </el-row>

                        <el-row :gutter="20">
                            <el-col :span="2" :offset="0"> 里料： </el-col>
                            <el-col :span="4" :offset="0">
                                <el-button type="primary" size="default" @click="addMaterial(1)"
                                    >添加里料</el-button
                                >
                                <el-button
                                    type="primary"
                                    size="default"
                                    @click="addMaterialByManual(1)"
                                    >手动添加里料</el-button
                                >
                            </el-col>
                            <el-col :span="2" :offset="0">
                                <el-button @click="syncMaterials(1)">{{
                                    this.syncMaterialButtonText
                                }}</el-button>
                            </el-col>
                        </el-row>
                        <el-row :gutter="20">
                            <el-col :span="23" :offset="0">
                                <el-table
                                    :data="getMaterialDataByType('insideMaterialData')"
                                    border
                                    style="width: 100%"
                                >
                                    <el-table-column type="index"></el-table-column>
                                    <el-table-column prop="materialType" label="材料类型" />
                                    <el-table-column prop="materialDetailType" label="材料二级类型">
                                        <template #default="scope">
                                            <el-input
                                                v-model="scope.row.materialDetailType"
                                            ></el-input>
                                        </template>
                                    </el-table-column>
                                    <el-table-column prop="supplierName" label="厂家名称">
                                        <template #default="scope">
                                            <el-autocomplete
                                                v-if="
                                                    scope !== undefined &&
                                                    scope.row.manualSymbol === 1
                                                "
                                                v-model="scope.row.supplierName"
                                                size="default"
                                                :fetch-suggestions="querySupplierNames"
                                                placeholder="输入厂家名称"
                                                @select="
                                                    handleSupplierNameSelect(scope.row, $event)
                                                "
                                            ></el-autocomplete>
                                        </template>
                                    </el-table-column>
                                    <el-table-column prop="materialName" label="材料名称">
                                        <template #default="scope">
                                            <el-select
                                                v-if="
                                                    scope !== undefined &&
                                                    scope.row.manualSymbol === 1
                                                "
                                                v-model="scope.row.materialName"
                                                filterable
                                                @change="
                                                    handleMaterialNameSelect(scope.row, $event)
                                                "
                                            >
                                                <el-option
                                                    v-for="item in materialNameOptions"
                                                    :key="item.value"
                                                    :value="item.value"
                                                    :label="item.label"
                                                >
                                                </el-option>
                                            </el-select>
                                        </template>
                                    </el-table-column>
                                    <el-table-column prop="materialModel" label="材料型号">
                                        <template #default="scope">
                                            <el-input
                                                type="textarea"
                                                autosize
                                                v-model="scope.row.materialModel"
                                                size="default"
                                            ></el-input>
                                        </template>
                                    </el-table-column>
                                    <el-table-column prop="materialSpecification" label="材料规格">
                                        <template #default="scope">
                                            <el-input
                                                type="textarea"
                                                autosize
                                                v-model="scope.row.materialSpecification"
                                                size="default"
                                            ></el-input>
                                        </template>
                                    </el-table-column>
                                    <el-table-column prop="color" label="颜色">
                                        <template #default="scope">
                                            <el-input
                                                v-model="scope.row.color"
                                                size="default"
                                            ></el-input>
                                        </template>
                                    </el-table-column>
                                    <el-table-column prop="unit" label="单位"></el-table-column>
                                    <el-table-column prop="comment" label="备注">
                                        <template #default="scope">
                                            <el-input
                                                type="textarea"
                                                autosize
                                                v-model="scope.row.comment"
                                                size="default"
                                            ></el-input>
                                        </template>
                                    </el-table-column>

                                    <el-table-column label="操作">
                                        <template #default="scope">
                                            <el-button
                                                type="danger"
                                                size="small"
                                                @click="deleteMaterial(scope.$index, 1)"
                                                >删除</el-button
                                            >
                                        </template>
                                    </el-table-column>
                                </el-table>
                            </el-col>
                        </el-row>
                        <el-row :gutter="20">
                            <el-col :span="2" :offset="0"> 辅料： </el-col>
                            <el-col :span="4" :offset="0">
                                <el-button type="primary" size="default" @click="addMaterial(2)"
                                    >添加辅料</el-button
                                >
                                <el-button
                                    type="primary"
                                    size="default"
                                    @click="addMaterialByManual(2)"
                                    >手动添加辅料</el-button
                                >
                            </el-col>
                            <el-col :span="2" :offset="0">
                                <el-button @click="syncMaterials(2)">{{
                                    this.syncMaterialButtonText
                                }}</el-button>
                            </el-col>
                        </el-row>
                        <el-row :gutter="20">
                            <el-col :span="23" :offset="0">
                                <el-table
                                    :data="getMaterialDataByType('accessoryMaterialData')"
                                    border
                                    style="width: 100%"
                                >
                                    <el-table-column type="index"></el-table-column>
                                    <el-table-column prop="materialType" label="材料类型" />
                                    <el-table-column prop="materialDetailType" label="材料二级类型">
                                        <template #default="scope">
                                            <el-input
                                                v-model="scope.row.materialDetailType"
                                            ></el-input>
                                        </template>
                                    </el-table-column>
                                    <el-table-column prop="supplierName" label="厂家名称">
                                        <template #default="scope">
                                            <el-autocomplete
                                                v-if="
                                                    scope !== undefined &&
                                                    scope.row.manualSymbol === 1
                                                "
                                                v-model="scope.row.supplierName"
                                                size="default"
                                                :fetch-suggestions="querySupplierNames"
                                                placeholder="输入厂家名称"
                                                @select="
                                                    handleSupplierNameSelect(scope.row, $event)
                                                "
                                            ></el-autocomplete>
                                        </template>
                                    </el-table-column>
                                    <el-table-column prop="materialName" label="材料名称">
                                        <template #default="scope">
                                            <el-select
                                                v-if="
                                                    scope !== undefined &&
                                                    scope.row.manualSymbol === 1
                                                "
                                                v-model="scope.row.materialName"
                                                filterable
                                                @change="
                                                    handleMaterialNameSelect(scope.row, $event)
                                                "
                                            >
                                                <el-option
                                                    v-for="item in materialNameOptions"
                                                    :key="item.value"
                                                    :value="item.value"
                                                    :label="item.label"
                                                >
                                                </el-option>
                                            </el-select>
                                        </template>
                                    </el-table-column>
                                    <el-table-column prop="materialModel" label="材料型号">
                                        <template #default="scope">
                                            <el-input
                                                type="textarea"
                                                autosize
                                                v-model="scope.row.materialModel"
                                                size="default"
                                            ></el-input>
                                        </template>
                                    </el-table-column>
                                    <el-table-column prop="materialSpecification" label="材料规格">
                                        <template #default="scope">
                                            <el-input
                                                type="textarea"
                                                autosize
                                                v-model="scope.row.materialSpecification"
                                                size="default"
                                            ></el-input>
                                        </template>
                                    </el-table-column>
                                    <el-table-column prop="color" label="颜色">
                                        <template #default="scope">
                                            <el-input
                                                v-model="scope.row.color"
                                                size="default"
                                            ></el-input>
                                        </template>
                                    </el-table-column>
                                    <el-table-column prop="unit" label="单位"></el-table-column>
                                    <el-table-column prop="comment" label="备注">
                                        <template #default="scope">
                                            <el-input
                                                type="textarea"
                                                autosize
                                                v-model="scope.row.comment"
                                                size="default"
                                            ></el-input>
                                        </template>
                                    </el-table-column>

                                    <el-table-column label="操作">
                                        <template #default="scope">
                                            <el-button
                                                type="danger"
                                                size="small"
                                                @click="deleteMaterial(scope.$index, 2)"
                                                >删除</el-button
                                            >
                                        </template>
                                    </el-table-column>
                                </el-table>
                            </el-col>
                        </el-row>
                        <el-row :gutter="20">
                            <el-col :span="2" :offset="0"> 大底： </el-col>
                            <el-col :span="4" :offset="0">
                                <el-button type="primary" size="default" @click="addMaterial(3)"
                                    >添加大底</el-button
                                >
                                <el-button
                                    type="primary"
                                    size="default"
                                    @click="addMaterialByManual(3)"
                                    >手动添加大底</el-button
                                >
                            </el-col>
                            <el-col :span="2" :offset="0">
                                <el-button @click="syncMaterials(3)">{{
                                    this.syncMaterialButtonText
                                }}</el-button>
                            </el-col>
                        </el-row>
                        <el-row :gutter="20">
                            <el-col :span="23" :offset="0">
                                <el-table
                                    :data="getMaterialDataByType('outsoleMaterialData')"
                                    border
                                    style="width: 100%"
                                >
                                    <el-table-column type="index"></el-table-column>
                                    <el-table-column prop="materialType" label="材料类型" />
                                    <el-table-column prop="materialDetailType" label="材料二级类型">
                                        <template #default="scope">
                                            <el-input
                                                v-model="scope.row.materialDetailType"
                                            ></el-input>
                                        </template>
                                    </el-table-column>
                                    <el-table-column prop="supplierName" label="厂家名称">
                                        <template #default="scope">
                                            <el-autocomplete
                                                v-if="
                                                    scope !== undefined &&
                                                    scope.row.manualSymbol === 1
                                                "
                                                v-model="scope.row.supplierName"
                                                size="default"
                                                :fetch-suggestions="querySupplierNames"
                                                placeholder="输入厂家名称"
                                                @select="
                                                    handleSupplierNameSelect(scope.row, $event)
                                                "
                                            ></el-autocomplete>
                                        </template>
                                    </el-table-column>
                                    <el-table-column prop="materialName" label="材料名称">
                                        <template #default="scope">
                                            <el-input
                                                v-model="scope.row.materialName"
                                                size="default"
                                            ></el-input>
                                        </template>
                                    </el-table-column>
                                    <el-table-column prop="materialModel" label="材料型号">
                                        <template #default="scope">
                                            <el-input
                                                type="textarea"
                                                autosize
                                                v-model="scope.row.materialModel"
                                                size="default"
                                            ></el-input>
                                        </template>
                                    </el-table-column>
                                    <el-table-column prop="materialSpecification" label="材料规格">
                                        <template #default="scope">
                                            <el-input
                                                type="textarea"
                                                autosize
                                                v-model="scope.row.materialSpecification"
                                                size="default"
                                            ></el-input>
                                        </template>
                                    </el-table-column>
                                    <el-table-column prop="color" label="颜色">
                                        <template #default="scope">
                                            <el-input
                                                v-model="scope.row.color"
                                                size="default"
                                            ></el-input>
                                        </template>
                                    </el-table-column>
                                    <el-table-column prop="unit" label="单位">
                                        <template #default="scope">
                                            <el-input
                                                v-model="scope.row.unit"
                                                size="default"
                                            ></el-input>
                                        </template>
                                    </el-table-column>

                                    <el-table-column prop="comment" label="备注">
                                        <template #default="scope">
                                            <el-input
                                                type="textarea"
                                                autosize
                                                v-model="scope.row.comment"
                                                size="default"
                                            ></el-input>
                                        </template>
                                    </el-table-column>

                                    <el-table-column label="操作">
                                        <template #default="scope">
                                            <el-button
                                                type="danger"
                                                size="small"
                                                @click="deleteMaterial(scope.$index, 3)"
                                                >删除</el-button
                                            >
                                        </template>
                                    </el-table-column>
                                </el-table>
                            </el-col>
                        </el-row>
                        <el-row :gutter="20">
                            <el-col :span="2" :offset="0"> 中底： </el-col>
                            <el-col :span="4" :offset="0">
                                <el-button type="primary" size="default" @click="addMaterial(4)"
                                    >添加中底</el-button
                                >
                                <el-button
                                    type="primary"
                                    size="default"
                                    @click="addMaterialByManual(4)"
                                    >手动添加中底</el-button
                                >
                            </el-col>
                            <el-col :span="2" :offset="0">
                                <el-button @click="syncMaterials(4)">{{
                                    this.syncMaterialButtonText
                                }}</el-button>
                            </el-col>
                        </el-row>
                        <el-row :gutter="20">
                            <el-col :span="23" :offset="0">
                                <el-table
                                    :data="getMaterialDataByType('midsoleMaterialData')"
                                    border
                                    style="width: 100%"
                                >
                                    <el-table-column type="index"></el-table-column>
                                    <el-table-column prop="materialType" label="材料类型" />
                                    <el-table-column prop="materialDetailType" label="材料二级类型">
                                        <template #default="scope">
                                            <el-input
                                                v-model="scope.row.materialDetailType"
                                            ></el-input>
                                        </template>
                                    </el-table-column>
                                    <el-table-column prop="supplierName" label="厂家名称">
                                        <template #default="scope">
                                            <el-autocomplete
                                                v-if="
                                                    scope !== undefined &&
                                                    scope.row.manualSymbol === 1
                                                "
                                                v-model="scope.row.supplierName"
                                                size="default"
                                                :fetch-suggestions="querySupplierNames"
                                                placeholder="输入厂家名称"
                                                @select="
                                                    handleSupplierNameSelect(scope.row, $event)
                                                "
                                            ></el-autocomplete>
                                        </template>
                                    </el-table-column>
                                    <el-table-column prop="materialName" label="材料名称">
                                        <template #default="scope">
                                            <el-input
                                                v-model="scope.row.materialName"
                                                size="default"
                                            ></el-input>
                                        </template>
                                    </el-table-column>
                                    <el-table-column prop="materialModel" label="材料型号">
                                        <template #default="scope">
                                            <el-input
                                                type="textarea"
                                                autosize
                                                v-model="scope.row.materialModel"
                                                size="default"
                                            ></el-input>
                                        </template>
                                    </el-table-column>
                                    <el-table-column prop="materialSpecification" label="材料规格">
                                        <template #default="scope">
                                            <el-input
                                                type="textarea"
                                                autosize
                                                v-model="scope.row.materialSpecification"
                                                size="default"
                                            ></el-input>
                                        </template>
                                    </el-table-column>
                                    <el-table-column prop="color" label="颜色">
                                        <template #default="scope">
                                            <el-input
                                                v-model="scope.row.color"
                                                size="default"
                                            ></el-input>
                                        </template>
                                    </el-table-column>
                                    <el-table-column prop="unit" label="单位">
                                        <template #default="scope">
                                            <el-input
                                                v-model="scope.row.unit"
                                                size="default"
                                            ></el-input>
                                        </template>
                                    </el-table-column>

                                    <el-table-column prop="comment" label="备注">
                                        <template #default="scope">
                                            <el-input
                                                type="textarea"
                                                autosize
                                                v-model="scope.row.comment"
                                                size="default"
                                            ></el-input>
                                        </template>
                                    </el-table-column>

                                    <el-table-column label="操作">
                                        <template #default="scope">
                                            <el-button
                                                type="danger"
                                                size="small"
                                                @click="deleteMaterial(scope.$index, 4)"
                                                >删除</el-button
                                            >
                                        </template>
                                    </el-table-column>
                                </el-table>
                            </el-col>
                        </el-row>
                        <el-row :gutter="20">
                            <el-col :span="2" :offset="0"> 烫底： </el-col>
                            <el-col :span="6" :offset="0">
                                <el-button type="primary" size="default" @click="addMaterial(6)"
                                    >添加烫底</el-button
                                >
                                <el-button
                                    type="primary"
                                    size="default"
                                    @click="addMaterialByManual(6)"
                                    >手动添加独立烫底</el-button
                                >
                                <el-button
                                    type="primary"
                                    size="default"
                                    @click="addMaterialByManual(7)"
                                    >手动添加加工烫底</el-button
                                >
                            </el-col>
                            <el-col :span="2" :offset="0">
                                <el-button @click="syncMaterials(6)">{{
                                    this.syncMaterialButtonText
                                }}</el-button>
                            </el-col>
                        </el-row>
                        <el-row :gutter="20">
                            <el-col :span="23" :offset="0">
                                <el-table
                                    :data="getMaterialDataByType('hotsoleMaterialData')"
                                    border
                                    style="width: 100%"
                                >
                                    <el-table-column type="index"></el-table-column>
                                    <el-table-column prop="materialType" label="材料类型" />
                                    <el-table-column prop="materialDetailType" label="材料二级类型">
                                        <template #default="scope">
                                            <el-input
                                                v-model="scope.row.materialDetailType"
                                            ></el-input>
                                        </template>
                                    </el-table-column>
                                    <el-table-column prop="supplierName" label="厂家名称">
                                        <template #default="scope">
                                            <el-autocomplete
                                                v-if="
                                                    scope !== undefined &&
                                                    scope.row.manualSymbol === 1
                                                "
                                                v-model="scope.row.supplierName"
                                                size="default"
                                                :fetch-suggestions="querySupplierNames"
                                                placeholder="输入厂家名称"
                                                @select="
                                                    handleSupplierNameSelect(scope.row, $event)
                                                "
                                            ></el-autocomplete>
                                        </template>
                                    </el-table-column>
                                    <el-table-column prop="materialName" label="材料名称">
                                        <template #default="scope">
                                            <el-input
                                                v-model="scope.row.materialName"
                                                size="default"
                                            ></el-input>
                                        </template>
                                    </el-table-column>
                                    <el-table-column prop="materialModel" label="材料型号">
                                        <template #default="scope">
                                            <el-input
                                                type="textarea"
                                                autosize
                                                v-model="scope.row.materialModel"
                                                size="default"
                                            ></el-input>
                                        </template>
                                    </el-table-column>
                                    <el-table-column prop="materialSpecification" label="材料规格">
                                        <template #default="scope">
                                            <el-input
                                                type="textarea"
                                                autosize
                                                v-model="scope.row.materialSpecification"
                                                size="default"
                                            ></el-input>
                                        </template>
                                    </el-table-column>
                                    <el-table-column prop="craftName" label="工艺名称">
                                        <template #default="scope">
                                            <el-input
                                                type="textarea"
                                                autosize
                                                v-model="scope.row.craftName"
                                                size="default"
                                            ></el-input>
                                        </template>
                                    </el-table-column>
                                    <el-table-column prop="color" label="颜色">
                                        <template #default="scope">
                                            <el-input
                                                v-model="scope.row.color"
                                                size="default"
                                            ></el-input>
                                        </template>
                                    </el-table-column>
                                    <el-table-column prop="unit" label="单位">
                                        <template #default="scope">
                                            <el-input
                                                v-model="scope.row.unit"
                                                size="default"
                                            ></el-input>
                                        </template>
                                    </el-table-column>
                                    <el-table-column prop="comment" label="备注">
                                        <template #default="scope">
                                            <el-input
                                                type="textarea"
                                                autosize
                                                v-model="scope.row.comment"
                                                size="default"
                                            ></el-input>
                                        </template>
                                    </el-table-column>

                                    <el-table-column label="操作">
                                        <template #default="scope">
                                            <el-button
                                                type="danger"
                                                size="small"
                                                @click="deleteMaterial(scope.$index, 6)"
                                                >删除</el-button
                                            >
                                        </template>
                                    </el-table-column>
                                </el-table>
                            </el-col>
                        </el-row>
                    </el-tab-pane>
                </el-tabs>
                <template #footer>
                    <span>
                        <el-button @click="isEditDialogVisible = false">取消</el-button>
                        <el-button type="primary" @click="editProductionInstrucion">确认</el-button>
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
import MaterialDataTable from '../components/MaterialDataTable.vue'
import { withTimeout } from '@/Pages/utils/timeout'
import axios from 'axios'
export default {
    components: {
        AllHeader,
        Arrow,
        MaterialDataTable
    },
    props: ['orderId'],
    data() {
        return {
            orderShoeData: {},
            departmentOptions: [],
            activeTab: '',
            tabcolor: [],
            materialWholeData: [],
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
            isEditDialogVisible: false,
            isPastShoeMaterialDetailDialogVisible: false,
            isProductionOrderCreateDialogVisible: false,
            isPastShoeMaterialDialogVisible: false,
            isPreviewDialogVisible: false,
            isLoadMaterialDialogVisible: false,
            token: localStorage.getItem('token'),
            currentShoeId: '',
            currentColor: '',
            currentShoeImageUrl: '',
            pastMaterialData: [],
            fileList: [],
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
            pastShoeInfoTable: [],
            newProductionInstructionId: '',
            pastShoeDescription: {
                shoeId: '',
                color: '',
                shoeImageUrl: ''
            },
            defaultManuallyAddedMaterial: {
                materialType: '',
                materialDetailType: '',
                materialName: '',
                materialModel: '',
                materialSpecification: '',
                craftName: '',
                color: '',
                unit: '',
                supplierName: '',
                comment: '',
                isPurchase: false,
                manualSymbol: 1
            },
            productionInstructionDetail: {
                sizeRange: '',
                originSize: '',
                lastType: '',
                sizeDifference: '',
                craftRemark: '',
                burnSoleCraft: '',
                designer: '',
                defaultBOMStatus: ''
            },
            syncMaterialButtonText: '同步该材料表格至所有颜色',
            defaultUnitOptions: [
                { value: '米', label: '米' },
                { value: '个', label: '个' },
                { value: '双', label: '双' },
                { value: '条', label: '条' }
            ],
            selectShoeTypeRow: {
                shoeTypeId: '',
                color: ''
            },
            materialNameOptions: []
        }
    },
    async mounted() {
        this.$setAxiosToken()
        this.getOrderInfo()
        this.getAllShoeListInfo()
        this.getAllDepartmentOptions()
        this.getAllMaterialName()
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
        async getAllDepartmentOptions() {
            const response = await axios.get(`${this.$apiBaseUrl}/general/getalldepartments`)
            this.departmentOptions = response.data
            console.log(this.departmentOptions)
        },
        async getAllMaterialList() {
            const response = await axios.get(`${this.$apiBaseUrl}/logistics/getmaterialtypeandname`)
            this.assetTable = response.data
            this.assetFilterTable = this.assetTable
        },
        async getAllMaterialName() {
            const response = await axios.get(`${this.$apiBaseUrl}/logistics/getallmaterialname`)
            this.materialNameOptions = response.data
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
                `${this.$apiBaseUrl}/devproductionorder/getordershoelist?orderid=${this.orderId}`
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
        async getNewProductionInstructionId() {
            const response = await axios.get(
                `${this.$apiBaseUrl}/devproductionorder/getnewproductioninstructionid`
            )
            this.newProductionInstructionId = response.data.productionInstructionId
        },
        async getPastMaterialData(row) {
            const response = await axios.get(
                `${this.$apiBaseUrl}/devproductionorder/getpastmaterialdata?shoetypeid=${row.shoeTypeId}`
            )
            this.pastMaterialData = response.data
        },
        syncMaterials(materialTypeNumber) {
            switch (materialTypeNumber) {
                case 0:
                    let surfaceMaterialData = this.getMaterialDataByType('surfaceMaterialData')
                    this.materialWholeData.forEach((shoeTypeData) => {
                        if (shoeTypeData.color !== this.activeTab) {
                            shoeTypeData.surfaceMaterialData = JSON.parse(
                                JSON.stringify(surfaceMaterialData)
                            )
                        }
                    })
                    break
                case 1:
                    let insideMaterialData = this.getMaterialDataByType('insideMaterialData')
                    this.materialWholeData.forEach((shoeTypeData) => {
                        if (shoeTypeData.color !== this.activeTab) {
                            shoeTypeData.insideMaterialData = JSON.parse(
                                JSON.stringify(insideMaterialData)
                            )
                        }
                    })
                    break
                case 2:
                    let accessoryMaterialData = this.getMaterialDataByType('accessoryMaterialData')
                    this.materialWholeData.forEach((shoeTypeData) => {
                        if (shoeTypeData.color !== this.activeTab) {
                            shoeTypeData.accessoryMaterialData = JSON.parse(
                                JSON.stringify(accessoryMaterialData)
                            )
                        }
                    })
                    break
                case 3:
                    let outsoleMaterialData = this.getMaterialDataByType('outsoleMaterialData')
                    this.materialWholeData.forEach((shoeTypeData) => {
                        if (shoeTypeData.color !== this.activeTab) {
                            shoeTypeData.outsoleMaterialData = JSON.parse(
                                JSON.stringify(outsoleMaterialData)
                            )
                        }
                    })
                    break
                case 4:
                    let midsoleMaterialData = this.getMaterialDataByType('midsoleMaterialData')
                    this.materialWholeData.forEach((shoeTypeData) => {
                        if (shoeTypeData.color !== this.activeTab) {
                            shoeTypeData.midsoleMaterialData = JSON.parse(
                                JSON.stringify(midsoleMaterialData)
                            )
                        }
                    })
                    break
                case 6:
                    let hotsoleMaterialData = this.getMaterialDataByType('hotsoleMaterialData')
                    this.materialWholeData.forEach((shoeTypeData) => {
                        if (shoeTypeData.color !== this.activeTab) {
                            shoeTypeData.hotsoleMaterialData = JSON.parse(
                                JSON.stringify(hotsoleMaterialData)
                            )
                        }
                    })
                    break
            }
            ElMessage.success('复制成功')
        },
        async addPastMaterialToCurrent() {
            console.log(this.selectShoeTypeRow[0].shoeTypeId)
            const response = await axios.get(
                `${this.$apiBaseUrl}/devproductionorder/getformatpastmaterialdata`,
                {
                    params: {
                        shoeTypeId: this.selectShoeTypeRow[0].shoeTypeId
                    }
                }
            )
            const pastMaterialData = response.data
            console.log(this.materialWholeData)
            this.materialWholeData[0].surfaceMaterialData = pastMaterialData.surfaceMaterialData
            this.materialWholeData[0].insideMaterialData = pastMaterialData.insideMaterialData
            this.materialWholeData[0].accessoryMaterialData = pastMaterialData.accessoryMaterialData
            this.materialWholeData[0].outsoleMaterialData = pastMaterialData.outsoleMaterialData
            this.materialWholeData[0].midsoleMaterialData = pastMaterialData.midsoleMaterialData
            this.materialWholeData[0].hotsoleMaterialData = pastMaterialData.hotsoleMaterialData
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

            switch (typeSymbol) {
                case 0:
                    this.defaultManuallyAddedMaterial.materialType = '面料'
                    activeMaterialData.surfaceMaterialData.push(this.defaultManuallyAddedMaterial)
                    this.defaultManuallyAddedMaterial = {
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
                        manualSymbol: 1
                    }
                    break
                case 1:
                    this.defaultManuallyAddedMaterial.materialType = '里料'
                    activeMaterialData.insideMaterialData.push(this.defaultManuallyAddedMaterial)
                    this.defaultManuallyAddedMaterial = {
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
                        manualSymbol: 1
                    }
                    break
                case 2:
                    this.defaultManuallyAddedMaterial.materialType = '辅料'
                    activeMaterialData.accessoryMaterialData.push(this.defaultManuallyAddedMaterial)
                    this.defaultManuallyAddedMaterial = {
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
                        manualSymbol: 1
                    }
                    break
                case 3:
                    this.defaultManuallyAddedMaterial.materialType = '底材'
                    activeMaterialData.outsoleMaterialData.push(this.defaultManuallyAddedMaterial)
                    this.defaultManuallyAddedMaterial = {
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
                        manualSymbol: 1
                    }
                    break
                case 4:
                    this.defaultManuallyAddedMaterial.materialType = '底材'
                    activeMaterialData.midsoleMaterialData.push(this.defaultManuallyAddedMaterial)
                    this.defaultManuallyAddedMaterial = {
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
                        manualSymbol: 1
                    }
                    break
                case 6:
                    this.defaultManuallyAddedMaterial.materialType = '烫底'
                    activeMaterialData.hotsoleMaterialData.push(this.defaultManuallyAddedMaterial)
                    this.defaultManuallyAddedMaterial = {
                        materialType: '',
                        materialDetailType: '',
                        materialName: '',
                        materialModel: '',
                        materialSpecification: '',
                        craftName: '',
                        color: '',
                        unit: '',
                        supplierName: '',
                        comment: '',
                        isPurchase: false,
                        manualSymbol: 1
                    }
                    break
                case 7:
                    this.defaultManuallyAddedMaterial.materialType = '里料'
                    activeMaterialData.hotsoleMaterialData.push(this.defaultManuallyAddedMaterial)
                    this.defaultManuallyAddedMaterial = {
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
                        manualSymbol: 1
                    }
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
                case 6:
                    this.currentCreateViewId = 6
                    this.materialTypeSearch = '烫底'
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
        async getInstructionData(row) {
            const response = await axios.get(
                `${this.$apiBaseUrl}/devproductionorder/getproductioninstruction?orderid=${this.orderData.orderId}&ordershoeid=${row.inheritId}`
            )
            this.newProductionInstructionId = response.data.productionInstructionId
            this.materialWholeData = response.data.instructionData
            this.productionInstructionDetail = response.data.productionInstructionDetail
        },
        async openPreviewDialog(row) {
            this.newProductionInstructionId = ''
            this.materialWholeData = []
            this.currentShoeId = row.inheritId
            this.currentShoeImageUrl = row.typeInfos[0].image
            await this.getOrderShoeInfo(row.inheritId)
            this.getInstructionData(row)
            this.tabcolor = row.typeInfos.map((info) => info.color)
            this.activeTab = this.tabcolor[0]
            this.isPreviewDialogVisible = true
        },

        openIssueDialog() {
            this.isFinalBOM = true
            this.unIssueBOMData = this.testTableData.filter((row) => row.status === '已上传')
            console.log(this.unIssueBOMData)
        },
        async openUploadDialog(row) {
            this.newProductionInstructionId = ''
            this.materialWholeData = []
            this.currentShoeId = row.inheritId
            await this.getNewProductionInstructionId()
            this.tabcolor = row.typeInfos.map((info) => info.color)
            this.activeTab = this.tabcolor[0]
            this.productionInstructionDetail.designer = row.designer
            for (let i = 0; i < this.tabcolor.length; i++) {
                this.materialWholeData.push({
                    color: this.tabcolor[i],
                    surfaceMaterialData: [],
                    insideMaterialData: [],
                    accessoryMaterialData: [],
                    outsoleMaterialData: [],
                    midsoleMaterialData: [],
                    hotsoleMaterialData: []
                })
            }
            this.isProductionOrderCreateDialogVisible = true
        },
        async openEditDialog(row) {
            this.newProductionInstructionId = ''
            this.currentShoeId = row.inheritId
            await this.getInstructionData(row)
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
                        hotsoleMaterialData: []
                    }
                    this.materialWholeData.push(obj)
                })
            }
            this.productionInstructionDetail.designer = row.designer
            this.activeTab = this.tabcolor[0]
            this.isEditDialogVisible = true
        },
        async openLoadMaterialDialog() {
            this.getPastOrderShoeData()
            this.isLoadMaterialDialogVisible = true
        },
        async getPastOrderShoeData() {
            const response = await axios.get(
                `${this.$apiBaseUrl}/devproductionorder/getpastshoeinfo?ordershoeid=${this.currentShoeId}`
            )
            this.pastShoeInfoTable = response.data
            console.log(this.pastShoeInfoTable)
        },
        async openLoadMaterialDialogByColor(row) {
            this.pastShoeDescription.shoeId = row.shoeId
            this.pastShoeDescription.color = row.color
            this.pastShoeDescription.shoeImageUrl = row.shoeImageUrl
            await this.getPastMaterialData(row)
            this.isPastShoeMaterialDetailDialogVisible = true
        },
        getMaterialDataByType(type) {
            const activeData = this.materialWholeData.find((item) => item.color === this.activeTab)
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
                const response = await axios.post(
                    `${this.$apiBaseUrl}/devproductionorder/editproductioninstruction`,
                    {
                        orderId: this.orderData.orderId,
                        productionInstructionId: this.newProductionInstructionId,
                        orderShoeId: this.currentShoeId,
                        uploadData: this.materialWholeData,
                        productionInstructionDetail: this.productionInstructionDetail
                    }
                )

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
                this.isEditDialogVisible = false
                this.getAllShoeListInfo()
            } catch (error) {
                this.$message({
                    type: 'error',
                    message: error.message || '请求失败，请稍后再试'
                })
            } finally {
                loadingInstance.close()
            }
        },
        async saveProductionInstruction() {
            // Check if all items have non-null supplierName and materialName
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
                const response = await axios.post(
                    `${this.$apiBaseUrl}/devproductionorder/saveproductioninstruction`,
                    {
                        orderId: this.orderData.orderId,
                        productionInstructionId: this.newProductionInstructionId,
                        orderShoeId: this.currentShoeId,
                        uploadData: this.materialWholeData,
                        productionInstructionDetail: this.productionInstructionDetail
                    }
                )

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
                this.isProductionOrderCreateDialogVisible = false
                this.getAllShoeListInfo()
            } catch (error) {
                this.$message({
                    type: 'error',
                    message: error.message || '保存失败，请稍后再试'
                })
            } finally {
                loadingInstance.close()
            }
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
            this.$confirm('确定上传投产指令单吗？', '提示', {
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
            this.UploadVis = false
            this.getAllShoeListInfo()
        },
        handleUploadError() {
            this.$message.error('上传失败')
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
            const response = await axios.post(`${this.$apiBaseUrl}/devproductionorder/issue`, {
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
            this.$confirm('确定下发选定投产指令单吗？', '提示', {
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
        handleShoeTypeSelectionChange(selection) {
            if (selection.length > 1) {
                // Ensure only one row is selected
                this.$refs.orderShoeTypeTable.clearSelection()
                this.$refs.orderShoeTypeTable.toggleRowSelection(
                    selection[selection.length - 1],
                    true
                )
            } else {
                this.selectShoeTypeRow = selection
                console.log(this.selectShoeTypeRow)
            }
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
                case 6:
                    activeMaterialData.hotsoleMaterialData.splice(index, 1)
                    break
                default:
                    break
            }
        },
        uploadNoteImage(row) {
            this.isUploadImageDialogVisible = true
            this.currentShoeId = row.inheritId
        },
        submitUpload() {
            this.$refs.uploadImage.submit()
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
        async querySupplierNames(queryString, callback) {
            if (queryString.trim()) {
                await axios
                    .get(
                        `${this.$apiBaseUrl}/devproductionorder/getautofinishedsuppliername?supplierName=${queryString}`
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
            row.unit = response.data.unit
            row.materialType = response.data.materialType
        },
        handleSupplierNameSelect(row, selectedItem) {
            row.supplierName = selectedItem.value
        },
        downloadProductionInstruction(row) {
            window.open(
                `${this.$apiBaseUrl}/devproductionorder/downloadproductioninstruction?orderid=${this.orderData.orderId}&ordershoerid=${row.inheritId}`
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
