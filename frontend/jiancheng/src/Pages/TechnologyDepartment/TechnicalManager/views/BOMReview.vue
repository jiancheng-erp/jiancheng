<template>
    <el-container direction="vertical">
        <el-header height="">
            <AllHeader></AllHeader>
        </el-header>
        <el-main style="overflow-x: hidden">
            <el-row :gutter="20" style="text-align: center">
                <el-col :span="24" :offset="0" style="font-size: xx-large; text-align: center">生产BOM用量审批</el-col>
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
                                <el-descriptions-item label="订单鞋型当前状态" align="center">{{
                                    orderData.currentOrderShoeStatus
                                    }}</el-descriptions-item>
                                <el-descriptions-item label="前序订单鞋型状态" align="center">{{
                                    orderData.previousOrderShoeStatus
                                    }}</el-descriptions-item>
                                <el-descriptions-item label="前序下发时间" align="center">{{
                                    orderData.previousOrderShoeStatusTime
                                    }}</el-descriptions-item>
                                <el-descriptions-item label="迟滞时间" align="center">{{
                                    orderData.delayTime
                                    }}</el-descriptions-item>
                                <el-descriptions-item label="退回订单" align="center">
                                    <el-button type="danger" size="default"
                                        @click="openReturnOrderDialog">退回流程</el-button>
                                </el-descriptions-item>
                            </el-descriptions>
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
                                            <el-table-column prop="firstPurchaseOrderId"
                                                label="一次采购订单"></el-table-column>
                                            <el-table-column prop="secondBomId" label="二次BOM表"></el-table-column>
                                            <el-table-column prop="secondPurchaseOrderId"
                                                label="二次采购订单"></el-table-column>
                                        </el-table>
                                    </template>
                                </el-table-column>
                                <el-table-column prop="inheritId" label="工厂型号" align="center"
                                    width="100"></el-table-column>
                                <el-table-column prop="customerId" label="客户型号" align="center"></el-table-column>
                                <el-table-column prop="designer" label="设计员" align="center"></el-table-column>
                                <el-table-column prop="status" label="状态" align="center"></el-table-column>
                                <el-table-column label="操作" align="center">
                                    <template #default="scope">
                                        <span
                                            v-if="scope.row.status === '未上传' || scope.row.status === '已上传' || scope.row.status === '等待用量填写'">
                                            材料用量尚未提交
                                        </span>
                                        <div v-else-if="scope.row.status === '完成用量填写'">
                                            <el-button type="primary"
                                                @click="openPreviewDialog(scope.row)">查看</el-button>
                                            <!-- <el-button
                                        type="success"
                                        @click="downloadProductionInstruction(scope.row)"
                                        >下载工艺单（生产指令单）EXCEL</el-button
                                    >
                                    <el-button
                                        type="warning"
                                        @click="downloadProductionInstructionImage(scope.row)"
                                        >下载备注图片</el-button
                                    > -->
                                        </div>
                                        <div v-else-if="scope.row.status === '已审核并下发'">
                                            <el-button type="primary"
                                                @click="openPreviewDialog(scope.row)">查看</el-button>
                                            <!-- <el-button
                                        type="success"
                                        @click="downloadProductionInstruction(scope.row)"
                                        >下载工艺单（生产指令单）EXCEL</el-button
                                    >
                                    <el-button
                                        type="warning"
                                        @click="downloadProductionInstructionImage(scope.row)"
                                        >下载备注图片</el-button
                                    > -->
                                            <el-button type="success"
                                                @click="downloadCraftSheet(scope.row)">下载工艺单EXCEL</el-button>
                                        </div>

                                    </template>
                                </el-table-column>
                            </el-table>
                        </el-col>
                    </el-row>
                    <el-row :gutter="22" style="margin-top: 10px">
                        <el-col :span="6" :offset="20"><el-button type="primary" size="default"
                                @click="openIssueDialog">下发生产BOM</el-button>
                        </el-col>
                    </el-row>
                    <el-dialog title="生产BOM下发页面" v-model="isFinalBOM" width="90%">
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
                                        <el-table-column prop="customerId" label="客户型号"
                                            align="center"></el-table-column>
                                        <el-table-column prop="designer" label="设计员" align="center"></el-table-column>
                                        <el-table-column prop="editter" label="调版员" align="center"></el-table-column>
                                        <el-table-column label="操作" align="center">
                                            <template #default="scope">
                                                <el-button type="primary" size="default"
                                                    @click="openPreviewDialog(scope.row)">查看生产BOM</el-button>
                                            </template>
                                        </el-table-column>
                                    </el-table>
                                </el-col>
                            </el-row>
                        </div>
                        <template #footer>
                            <span>
                                <el-button @click="isFinalBOM = false">取消</el-button>
                                <el-button type="primary" @click="confirmBOMIssue(selectedShoe)">下发选定生产BOM</el-button>
                            </span>
                        </template>
                    </el-dialog>
                    <el-dialog :title="`工艺单预览 ${newcraftSheetId}`" v-model="isPreviewDialogVisible" width="100%"
                        fullscreen>
                        <el-row :gutter="20">
                            <el-col :span="24" :offset="0">
                                <el-descriptions title="鞋型基本信息" border direction="vertical" :column="4"
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
                            <el-col :span="24" :offset="0">
                                <el-descriptions title="工艺单公用信息" border :column="3" direction="vertical">
                                    <el-descriptions-item label="备注图片" :rowspan="2" width="200">
                                        <el-image :src="craftSheetDetail.picNoteImgPath" fit="fill"
                                            :lazy="true"></el-image>
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
                                    <el-col :span="24" :offset="0">
                                        <MaterialDataTable :tableData="getMaterialDataByType('surfaceMaterialData')
                                            " />
                                    </el-col>
                                </el-row>
                                <el-row :gutter="20">
                                    <el-col :span="2" :offset="0"> 里料： </el-col>
                                </el-row>
                                <el-row :gutter="20">
                                    <el-col :span="24" :offset="0">
                                        <MaterialDataTable :tableData="getMaterialDataByType('insideMaterialData')
                                            " />
                                    </el-col>
                                </el-row>
                                <el-row :gutter="20">
                                    <el-col :span="2" :offset="0"> 辅料： </el-col>
                                </el-row>
                                <el-row :gutter="20">
                                    <el-col :span="24" :offset="0">
                                        <MaterialDataTable :tableData="getMaterialDataByType('accessoryMaterialData')
                                            " />
                                    </el-col>
                                </el-row>
                                <el-row :gutter="20">
                                    <el-col :span="2" :offset="0"> 大底： </el-col>
                                </el-row>
                                <el-row :gutter="20">
                                    <el-col :span="24" :offset="0">
                                        <MaterialDataTable :tableData="getMaterialDataByType('outsoleMaterialData')"
                                            :isSizeMaterial="true" />
                                    </el-col>
                                </el-row>
                                <el-row :gutter="20">
                                    <el-col :span="2" :offset="0"> 中底： </el-col>
                                </el-row>
                                <el-row :gutter="20">
                                    <el-col :span="24" :offset="0">
                                        <MaterialDataTable :tableData="getMaterialDataByType('midsoleMaterialData')"
                                            :isSizeMaterial="true" />
                                    </el-col>
                                </el-row>
                                <!-- <el-row :gutter="20">
                                        <el-col :span="2" :offset="0"> 楦头： </el-col>
                                    </el-row>
                                    <el-row :gutter="20">
                                        <el-col :span="24" :offset="0">
                                            <MaterialDataTable :tableData="getMaterialDataByType('lastMaterialData')
                                                " />
                                        </el-col>
                                    </el-row> -->
                                <el-row :gutter="20">
                                    <el-col :span="2" :offset="0"> 烫底： </el-col>
                                </el-row>
                                <el-row :gutter="20">
                                    <el-col :span="24" :offset="0">
                                        <MaterialDataTable :tableData="getMaterialDataByType('hotsoleMaterialData')
                                            " />
                                    </el-col>
                                </el-row>
                            </el-tab-pane>
                        </el-tabs>
                        <el-row :gutter="20">
                            <el-col :span="24" :offset="0"> 刀模图： </el-col>
                        </el-row>
                        <el-row :gutter="20">
                            <el-col :span="24" :offset="0">
                                <el-image :src="craftSheetDetail.cutDieImgPath" style="width: 800px"></el-image>
                            </el-col>
                        </el-row>


                        <template #footer>
                            <span>
                                <el-button type="primary" @click="isPreviewDialogVisible = false">确认</el-button>
                            </span>
                        </template>
                    </el-dialog>
                </el-col>
            </el-row>
        </el-main>
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
                <el-button type="primary" :disabled="revertForm.revertToStatus === ''"  @click="saveRevertForm">确认</el-button>
            </span>
        </template>
    </el-dialog>
    </el-container>
</template>

<script>
import AllHeader from '@/components/AllHeader.vue'
import Arrow from '@/components/OrderArrowView.vue'
import MaterialDataTable from '../components/MaterialDataTable.vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'
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
                manualSymbol: 1
            },
            craftSheetDetail: {
                adjuster: '',
                cutDie: '',
                reviewer: '',
                productionRemark: '',
                cuttingSpecialCraft: '',
                sewingSpecialCraft: '',
                moldingSpecialCraft: '',
                postProcessing: '',
                oilyGlue: '',
                cutDieImgPath: '',
                picNoteImgPath: ''
            },
            isCraftDialogVisible: false,
            syncMaterialButtonText: '同步该材料表格至所有颜色',
            inputCrafts: [], // 手动输入的工艺列表
            currentRow: null, // 当前编辑的行,
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
    async created() {
        this.$setAxiosToken()
        await this.getOrderInfo()
        this.getAllShoeListInfo()
        this.getAllDepartmentOptions()
        await this.getAllRevertStatusReasonOptions()
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
        async getOrderInfo() {
            const response = await axios.get(
                `${this.$apiBaseUrl}/order/getorderInfo?orderid=${this.orderId}&status=13`
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
        async getCraftSheetData(row) {
            const response = await axios.get(
                `${this.$apiBaseUrl}/craftsheetreview/getcraftsheetinfo?orderid=${this.orderData.orderId}&ordershoeid=${row.inheritId}`
            )
            this.craftSheetDetail = response.data.craftSheetDetail
            this.materialWholeData = response.data.uploadData
            this.newcraftSheetId = response.data.craftSheetId
            console.log(this.newcraftSheetId)
        },
        getMaterialDataByType(type) {
            const activeData = this.materialWholeData.find((item) => item.color === this.activeTab)
            if (activeData) {
                return activeData[type]
            }
            return []
        },
        openIssueDialog() {
            this.isFinalBOM = true
            this.unIssueBOMData = this.testTableData.filter((row) => row.status === '完成用量填写')
            console.log(this.unIssueBOMData)
        },
        handleShoeSelectionChange(selection) {
            this.selectedShoe = selection
            console.log(this.selectedShoe)
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
            const response = await axios.post(`${this.$apiBaseUrl}/craftsheetreview/issue`, {
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
        downloadCraftSheet(row) {
            window.open(
                `${this.$apiBaseUrl}/craftsheet/downloadcraftsheet?orderid=${this.orderData.orderId}&ordershoeid=${row.inheritId}`
            )
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
                    flow: 3,
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
        async getAllRevertStatusReasonOptions() {
            const response = await axios.get(`${this.$apiBaseUrl}/revertorder/getrevertorderreason`,
                { params: { orderId: this.orderData.orderDBId, flow: 3 } }
            )
            this.revertStatusReasonOptions = response.data
        },  
    }
}
</script>
