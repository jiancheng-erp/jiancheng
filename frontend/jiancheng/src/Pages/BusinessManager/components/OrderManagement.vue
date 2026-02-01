<template>
    <el-row :gutter="20">
        <el-col :span="24" :offset="0" style="font-size: xx-large; text-align: center">订单管理</el-col>
    </el-row>
    <el-row :gutter="10" style="margin-top: 20px">
        <el-col :span="4" :offset="0">
            <el-button size="default" type="primary" @click="openCreateOrderDialog">创建订单</el-button>
            <!-- <el-button size="default" type="primary" @click="showTemplate"> 模板 </el-button> -->
            <el-select v-model="orderStore.selectedOrderStatus" placeholder="请选择订单类型" size="default"
                :disabled="role === '21'" @change="handleOrderStatusChange" style="width: 200px; width: 150px">
                <el-option v-for="item in orderStore.orderStatusOption" :key="item" :label="item" :value="item" />
            </el-select>
        </el-col>
        <el-col :span="4" :offset="1"><el-input v-model="orderStore.orderRidFilter" placeholder="订单号筛选" size="default"
                :suffix-icon="'el-icon-search'" clearable @input="orderStore.filterDisplayOrder"></el-input>
        </el-col>
        <el-col :span="4"><el-input v-model="orderStore.orderCidFilter" placeholder="客户订单号筛选" size="default"
            :suffix-icon="'el-icon-search'" clearable @input="orderStore.filterDisplayOrder"></el-input>
        </el-col>
        <el-col :span="4"><el-input v-model="orderStore.orderCustomerNameFilter" placeholder="客户名称筛选" size="default"
            :suffix-icon="'el-icon-search'" clearable @input="orderStore.filterDisplayOrder"></el-input>
        </el-col>
        <el-col :span="4">
            <el-date-picker v-model="orderStore.orderStartDateFilter" type="daterange" unlink-panels range-separator="至"
                start-placeholder="订单开始日期起" end-placeholder="订单开始日期终" :shortcuts="shortcuts" size="default"
                @change="orderStore.filterDisplayOrder" />
        </el-col>
    </el-row>
    <el-row :gutter="10" style="margin-top: 20px">
        <el-col :span="5" :offset="0">
            <el-radio-group v-model="orderStore.radio" size="small" @change="orderStore.switchRadio(orderStore.radio)">
                <el-radio-button label="全部订单" value="all" />
                <el-radio-button label="已下发订单" value="已下发" />
                <el-radio-button label="未下发订单" value="未下发" />
            </el-radio-group>
        </el-col>
        <el-col :span="4">
            <el-input v-model="orderStore.customerProductNameFilter" placeholder="客户型号筛选" size="default"
                :suffix-icon="'el-icon-search'" clearable @input="orderStore.filterDisplayOrder"></el-input>
        </el-col>
        <el-col :span="4">
            <el-input v-model="orderStore.shoeRIdSearch" placeholder="工厂型号筛选" size="default"
                :suffix-icon="'el-icon-search'" clearable @input="orderStore.filterDisplayOrder"></el-input>
        </el-col>
        <el-col :span="4"><el-input v-model="orderStore.orderCustomerBrandFilter" placeholder="客户商标筛选" size="default"
                :suffix-icon="'el-icon-search'" clearable @input="orderStore.filterDisplayOrder"></el-input>
        </el-col>

        <el-col :span="4">
            <el-date-picker v-model="orderStore.orderEndDateFilter" type="daterange" unlink-panels range-separator="至"
                start-placeholder="订单结束日期起" end-placeholder="订单结束日期终" :shortcuts="shortcuts" size="default"
                @change="orderStore.filterDisplayOrder" />
        </el-col>
    </el-row>
    <el-row :gutter="20">
        <!-- <el-col :span="4">
            <el-radio-group v-model="sortRadio" size="small" @change="switchSortLogic(sortRadio)">
                <el-radio-button label="升序排列" value="asc" />
                <el-radio-button label="降序排列" value="desc" />
            </el-radio-group>
        </el-col> -->
    </el-row>
    <el-row :gutter="20">
        <el-table :data="orderStore.paginatedDisplayData" border stripe @row-dblclick="orderRowDbClick"
            style="height: 60vh">
            <el-table-column prop="orderRid" label="订单号" sortable />
            <el-table-column label="订单类型" width="120">
                <template #default="scope">
                    <el-tag :type="scope.row.orderType === 'F' ? 'warning' : 'success'">
                        {{ formatOrderType(scope.row.orderType) }}
                    </el-tag>
                </template>
            </el-table-column>
            <el-table-column prop="orderSalesman" label="创建业务员" />
            <el-table-column prop="orderSupervisor" label="审核" />
            <el-table-column prop="orderCid" label="客户订单号" />
            <el-table-column prop="customerName" label="客户名" />
            <el-table-column prop="customerBrand" label="客户商标" />
            <el-table-column prop="customerProductName" label="客户型号" />
            <el-table-column prop="shoeRId" label="工厂型号" />
            <el-table-column prop="orderStartDate" label="订单开始日期" sortable />
            <el-table-column prop="orderEndDate" label="订单结束日期" sortable />
            <el-table-column prop="orderStatus" label="订单状态" />
            <el-table-column label="操作" width="200">
                <template #default="scope">
                    <el-button-group>
                        <el-button type="primary" size="default"
                            @click="openOrderDetail(scope.row.orderDbId)">查看订单详情</el-button>
                        <el-button v-if="scope.row.orderStatusVal < 9 && this.userRole == 4" type="danger"
                            size="default" @click="deleteOrder(scope.row)">删除订单</el-button>
                    </el-button-group>
                </template>
            </el-table-column>
        </el-table>
        <el-pagination :current-page="orderStore.currentPage" :page-size="orderStore.pageSize"
            :total="orderStore.totalItems" @current-change="orderStore.handlePageChange"
            layout="total,prev,pager,next,jumper" style="margin-top: 20px"></el-pagination>
    </el-row>

    <el-dialog title="创建订单鞋型填写" v-model="dialogStore.orderCreationInfoVis" width="100%" fullscreen
        :close-on-click-modal="false">
        <el-form ref="orderCreationForm" :model="newOrderForm" label-width="120px" :inline="false" size="default">
            <el-form-item>
                <el-button type="primary" @click="showOrderTemplates">选择订单模板</el-button>
                <!-- <el-button type="warning" style="margin-left:8px" @click="injectTemplateTestData">注入模板测试数据</el-button> -->
            </el-form-item>
            <el-form-item label="请输入订单号" prop="orderRId" :rules="[
                {
                    required: true,
                    message: '订单号不能为空',
                    trigger: ['blur', 'change']
                },
                {
                    validator: validateOrderRid,
                    trigger: ['blur', 'change']
                }
            ]">
                <el-input @change="checkOrderRidExists" v-model="newOrderForm.orderRId"></el-input>
            </el-form-item>
            <el-form-item label="客户订单号">
                <el-input v-model="newOrderForm.orderCid"></el-input>
            </el-form-item>
            <el-form-item label="请选择客户" prop="customerName" :rules="[
                {
                    required: true,
                    message: '客户不能为空',
                    trigger: ['blur']
                }
            ]">
                <el-select v-model="newOrderForm.customerName" filterable placeholder="请选择客户"
                    @change="updateCustomerBrand">
                    <el-option v-for="item in this.customerNameList" :key="item" :label="item"
                        :value="item"></el-option>
                </el-select>
            </el-form-item>
            <el-form-item label="请选择客户商标" prop="customerBrand" :rules="[
                {
                    required: true,
                    message: '客户商标不能为空',
                    trigger: ['blur']
                }
            ]">
                <el-select v-model="newOrderForm.customerBrand" filterable placeholder="请选择商标"
                    @change="updateCustomerId">
                    <el-option v-for="item in this.customerBrandList" :key="item" :label="item"
                        :value="item"></el-option>
                </el-select>
            </el-form-item>
            <el-form-item label="请选择配码种类" prop="batchInfoTypeName" :rules="[
                {
                    required: true,
                    message: '请选择配码种类',
                    trigger: ['blur']
                }
            ]">
                <el-select v-model="newOrderForm.batchInfoTypeName" filterable placeholder="请选择种类"
                    @change="updateBatchType">
                    <el-option v-for="item in this.batchTypes" :key="item.batchInfoTypeId"
                        :label="item.batchInfoTypeName" :value="item.batchInfoTypeName"> </el-option>
                </el-select>
            </el-form-item>
            <el-form-item label="订单类型" prop="orderType" :rules="[
                {
                    required: true,
                    message: '请选择订单类型',
                    trigger: ['blur', 'change']
                }
            ]">
                <el-select v-model="newOrderForm.orderType" placeholder="请选择订单类型">
                    <el-option label="普通单" value="N"></el-option>
                    <el-option label="预报单" value="F"></el-option>
                </el-select>
            </el-form-item>
            <el-form-item label="订单开始日期" ref="startdatepicker" prop="orderStartDate" :rules="[
                {
                    required: true,
                    message: '请选择订单开始日期',
                    trigger: ['blur']
                }
            ]">
                <el-date-picker v-model="newOrderForm.orderStartDate" type="date" placeholder="选择日期"
                    value-format="YYYY-MM-DD"></el-date-picker>
            </el-form-item>
            <el-form-item label="订单结束日期" prop="orderEndDate" :rules="[
                {
                    required: true,
                    message: '请选择订单结束日期',
                    trigger: ['blur']
                }
            ]">
                <el-date-picker v-model="newOrderForm.orderEndDate" type="date" placeholder="选择日期"
                    value-format="YYYY-MM-DD"></el-date-picker>
            </el-form-item>
            <el-form-item label="业务员" prop="salesman" :rules="[
                {
                    required: true,
                    message: '请选择业务员',
                    trigger: ['blur']
                }
            ]">
                <el-input v-model="newOrderForm.salesman" disabled></el-input>
            </el-form-item>

            <el-form-item label="选择审批经理" prop="supervisorId" :rules="[
                {
                    required: true,
                    message: '内容不能为空',
                    trigger: ['blur']
                }
            ]">
                <el-select v-model="newOrderForm.supervisorId" filterable placeholder="请选择下发经理">
                    <el-option v-for="item in this.departmentNameList" :key="item.staffId" :label="item.staffName"
                        :value="item.staffId"></el-option>
                </el-select>
            </el-form-item>

            <el-row :gutter="20">
                <el-col :span="4" :offset="0" style="white-space: nowrap">
                    请选择鞋型号：
                    <el-input v-model="shoeRidFilter" placeholder="鞋型号搜索" size="default" :suffix-icon="'el-icon-search'"
                        @change="getAllShoes()" @clear="getAllShoes()" clearable> </el-input>
                </el-col>
                <el-col :span="4" :offset="2">
                    <el-input v-model="customerNameFilter" placeholder="客户型号搜索" size="default"
                        :suffix-icon="'el-icon-search'" @change="getAllShoes()" @clear="getAllShoes()" clearable>
                    </el-input>
                </el-col>
                <el-col :span="2" :offset="2">
                    <el-button type="primary" size="default" @click="openAddShoeDialog"> 添加新鞋型 </el-button>
                </el-col>
            </el-row>
            <el-row style="margin-top:10px; margin-bottom:10px">
                <el-col :span="24">
                    <div v-if="newOrderForm.orderShoeTypes && newOrderForm.orderShoeTypes.length">
                        <span style="font-weight:600; margin-right:8px">已选择鞋型：</span>
                        <el-tag v-for="item in newOrderForm.orderShoeTypes" :key="item.shoeTypeId || item.shoeRid" closable @close="removeSelectedShoe(item)" style="margin-right:6px">
                            {{ item.shoeRid }} <span v-if="item.colorName"> - {{ item.colorName }}</span>
                        </el-tag>
                    </div>
                </el-col>
            </el-row>

            <el-table :data="shoeTableData" style="width: 100%" stripe border height="500" row-key="shoeId">
                <el-table-column type="expand">
                    <template #default="props">
                        <el-table :data="props.row.shoeTypeData" border row-key="shoeTypeId"
                            @selection-change="(selection) => handleSelectionShoeType(selection, props.row.shoeId)"
                            ref="shoeSelectionTable">
                            <el-table-column size="small" type="selection" align="center"> </el-table-column>
                            <el-table-column prop="colorName" label="鞋型颜色" width="100px" />
                            <el-table-column prop="shoeImageUrl" label="鞋型图片" align="center">
                                <template #default="scope">
                                    <el-image :src="scope.row.shoeImageUrl" style="width: 150px; height: 100px"
                                        :key="scope.row.shoeImageUrl" />
                                </template>
                            </el-table-column>
                            <el-table-column label="操作">
                                <template #default="scope">
                                    <el-button type="primary"
                                        @click="openReUploadImageDialog(scope.row)">重新上传鞋图</el-button>
                                </template>
                            </el-table-column>
                        </el-table>
                    </template>
                </el-table-column>
                <el-table-column prop="shoeRid" label="鞋型编号"></el-table-column>
                <el-table-column>
                    <template #default="scope">
                        <el-button type="primary" size="default"
                            @click="openAddShoeTypeDialog(scope.row)">添加鞋款</el-button>
                    </template>
                </el-table-column>
            </el-table>
            <el-pagination :current-page="currentOrderCreatePage" :page-size="orderCreatePageSize"
                :total="shoeTotalItems" @current-change="handleOrderCreatePageChange"
                layout="total, prev, pager, next, jumper" style="margin-top: 20px"></el-pagination>
        </el-form>

        <template #footer>
            <span>
                <el-button type="primary" @click="orderCreationSecondStep">下一步</el-button>
            </span>
        </template>
    </el-dialog>

    <AddShoeDialog :color-options="colorOptions" @submit="addNewShoe" />
    <AddShoeTypeDialog :color-options="colorOptions" @submit="addShoeTypes" />
    <AddColorDialog v-model:visible="dialogStore.addColorDialogVis" :shoe-id="dialogStore.addColorForm.shoeId"
        :shoe-rid="dialogStore.addColorForm.shoeRid" :shoe-type-colors="dialogStore.addColorForm.shoeTypeColors"
        :color-options="colorOptions" @submit="handleAddColorDialogSubmit" />
    <el-dialog title="创建订单详情填写" v-model="dialogStore.orderCreationSecondInfoVis" width="90%" fullscreen
        :close-on-click-modal="false" :show-close="true" custom-class="create-order-detail-dialog"
        :close-on-press-escape="true">
        <el-row :gutter="20">
            <el-col :span="24" :offset="0">
                <el-descriptions title="" :column="2" border>
                    <el-descriptions-item label="订单号" align="center">{{ this.newOrderForm.orderRId
                    }}</el-descriptions-item>
                    <el-descriptions-item label="客户订单号" align="center">{{ this.newOrderForm.orderCid
                    }}</el-descriptions-item>
                </el-descriptions>
                <el-descriptions title="" :column="2" border>
                    <el-descriptions-item label="客户名称" align="center">{{ this.newOrderForm.customerName
                    }}</el-descriptions-item>
                    <el-descriptions-item label="客户商标" align="center">{{ this.newOrderForm.customerBrand
                    }}</el-descriptions-item>
                </el-descriptions>
                <div style="margin-top:8px">
                    <el-button type="success" @click="openAddColorDialog">
                        添加颜色
                    </el-button>
                </div>
            </el-col>
        </el-row>
        <el-table class="order-shoe-create-table" :data="this.newOrderForm.orderShoeTypes" border stripe
            style="max-height: 75vh; overflow-y: auto" :row-key="(row) => {
                return row.shoeTypeId || `${row.shoeRid || row.shoeId}-${row.colorId || row.color_id || row.colorName || row.customerColorName || ''}`
            }
                " :row-class-name="'persistent-shadow-row'" :default-expand-all="true">
            <el-table-column type="expand">
                <template #default="props">
                    <el-table :data="props.row.orderShoeTypeBatchInfo" border>
                        <el-table-column prop="packagingInfoName" label="配码名称" sortable />
                        <el-table-column prop="packagingInfoLocale" label="配码地区" sortable />
                        <el-table-column
                            v-for="col in Object.keys(this.attrMapping).filter((key) => this.curBatchType[key] != null)"
                            :label="this.curBatchType[col]" :prop="this.attrMapping[col]"></el-table-column>
                        <el-table-column prop="totalQuantityRatio" label="比例和" />
                        <el-table-column label="单位数量">
                            <template #default="scope">
                                <el-input size="small" v-model="props.row.quantityMapping[scope.row.packagingInfoId]"
                                    @change="updateAmountMapping(props.row, scope.row)" controls-position="right">
                                </el-input>
                            </template>
                        </el-table-column>
                        <el-table-column label="总数量">
                            <template #default="scope">
                                <el-input size="small" v-model="props.row.amountMapping[scope.row.packagingInfoId]"
                                    controls-position="right" :disabled="true"> </el-input>
                            </template>
                        </el-table-column>
                    </el-table>
                </template>
            </el-table-column>
            <el-table-column prop="shoeRid" label="鞋型编号" sortable />
            <el-table-column prop="colorName" label="鞋型颜色" />
            <el-table-column label="鞋型图片">
                <template #default="scope">
                    <el-image :src="scope.row.shoeImageUrl" style="width: 150px; height: 100px"></el-image>
                </template>
            </el-table-column>
            <el-table-column>
                <template #default="scope">
                    <el-button type="primary" size="default"
                        @click="openAddBatchInfoDialog(scope.row)">编辑鞋型配码</el-button>
                    <el-button type="warning" size="default" style="margin-left:8px"
                        @click="openAddColorDialog(scope.row)">更改颜色</el-button>
                    <el-button type="primary" size="default"
                        @click="openLoadBatchTemplateDialog(scope.row)">加载配码模板</el-button>
                    <el-button type="danger" size="default" @click="removeShoeType(scope.row)"
                        style="margin-left:8px">删除</el-button>
                </template>
            </el-table-column>
            <el-table-column label="添加客户鞋型编号">
                <template #default="scope">
                    <el-input size="default" v-model="this.newOrderForm.customerShoeName[scope.row.shoeRid]"></el-input>
                </template>
            </el-table-column>

            <el-table-column label="添加客户鞋型颜色名称">
                <template #default="scope">
                    <el-input size="default" v-model="scope.row.customerColorName"></el-input>
                </template>
            </el-table-column>
        </el-table>
        <template #footer>
            <span>
                <el-button @click="backPreviousStep"> 上一步 </el-button>
                <el-button @click="submitNewOrder"> 添加订单 </el-button>
            </span>
        </template>
    </el-dialog>

    <AddBatchInfoDialog ref="batchInfoDialog" v-model:batchNameFilter="batchNameFilter" :new-order-form="newOrderForm"
        :customer-display-batch-data="customerDisplayBatchData" :attr-mapping="attrMapping"
        :cur-batch-type="curBatchType" @selection-change="handleSelectionBatchData" @close="closeAddBatchInfoDialog"
        @open-add-customer-batch="openAddCustomerBatchDialog" @open-add-color="openAddColorDialog"
        @open-save-template="openSaveBatchTemplateDialog" @save-batch="addShoeTypeBatchInfo"
        @filter-with-selection="filterBatchDataWithSelection" />
    <TemplateSelectDialog v-model:templateFilter="templateFilter" :template-display-data="templateDisplayData"
        @filter="filterTemplateOptions" @create-from-template="openCreateOrderDialogFromTemplate"
        @delete-template="deleteOrderTemplate" @edit-template="editOrderTemplate" />
    <AddCustomerBatchDialog v-model:batchForm="batchForm" :attr-mapping="attrMapping" :cur-batch-type="curBatchType"
        @close="dialogStore.closeCustomerBatchDialog()" @submit="submitAddCustomerBatchForm" />
    <ReUploadImageDialog ref="reUploadImageDialog" :image-url="imageUrl" @file-change="onFileChange"
        @close="dialogStore.closeReUploadImageDialog()" @upload="uploadCroppedImage" />
    <CustomerBatchTemplateDialog :batch-template-display-data="batchTemplateDisplayData" :attr-mapping="attrMapping"
        :cur-batch-type="curBatchType" @selection-change="handleSelectionBatchTemplate"
        @delete-template="deleteBatchTemplateDialog" @confirm-load="confirmLoadBatchTemplate"
        @close="dialogStore.closeBatchTemplateDialog()" />
    <CustomerBatchTemplateSaveDialog v-model:batchTemplateForm="batchTemplateForm" :attr-mapping="attrMapping"
        :cur-batch-type="curBatchType" @close="dialogStore.closeBatchTemplateSaveDialog()" @save="saveBatchTemplate" />
</template>

<script>
import { Download, Upload } from '@element-plus/icons-vue'
import axios from 'axios'
import { ElMessage, ElPagination, ElMessageBox, ElButton } from 'element-plus'
import { toggleRowStatus } from 'element-plus/es/components/table/src/util'
import { Cropper } from 'vue-advanced-cropper'
import { useOrderDialogStore } from '@/Pages/BusinessManager/stores/orderDialog'
import { useOrderManagementStore } from '@/Pages/BusinessManager/stores/orderManagement'
import AddShoeDialog from './orderDialogs/AddShoeDialog.vue'
import AddShoeTypeDialog from './orderDialogs/AddShoeTypeDialog.vue'
import AddBatchInfoDialog from './orderDialogs/AddBatchInfoDialog.vue'
import AddColorDialog from './orderDialogs/AddColorDialog.vue'
import TemplateSelectDialog from './orderDialogs/TemplateSelectDialog.vue'
import AddCustomerBatchDialog from './orderDialogs/AddCustomerBatchDialog.vue'
import ReUploadImageDialog from './orderDialogs/ReUploadImageDialog.vue'
import CustomerBatchTemplateDialog from './orderDialogs/CustomerBatchTemplateDialog.vue'
import CustomerBatchTemplateSaveDialog from './orderDialogs/CustomerBatchTemplateSaveDialog.vue'

export default {
    components: {
        AddShoeDialog,
        AddShoeTypeDialog,
        AddColorDialog,
        AddBatchInfoDialog,
        TemplateSelectDialog,
        AddCustomerBatchDialog,
        ReUploadImageDialog,
        CustomerBatchTemplateDialog,
        CustomerBatchTemplateSaveDialog
    },
    setup() {
        const orderStore = useOrderManagementStore()
        const dialogStore = useOrderDialogStore()
        return { orderStore, dialogStore }
    },
    data() {
        return {
            token: localStorage.getItem('token'),
            staffId: localStorage.getItem('staffid'),
            role: localStorage.getItem('role'),
            submitDocType: 0,
            orderShoePreviewData: [],
            orderData: {},
            orderDocData: {},
            customerNameList: [],
            departmentNameList: [],
            customerBrandList: [],
            customerBatchData: [],
            customerDisplayBatchData: [],
            selectedShoeList: [],
            // orderStatusList: [],
            currentBatch: [],
            expandedRowKeys: [],
            previewOrderVis: false,
            orderInfoVis: false,
            fileList: [],
            isImportVis: false,
            isSubmitDocVis: false,
            parentBoarder: false,
            childBoarder: false,
            Upload,
            batchNameFilter: '',
            templateFilter: '',
            customerNameFilter: '',
            batchTemplateDisplayData: [],
            prevDisplayData: [],
            uploadData: [],
            updatekey: 0,
            tempFileName: '',
            shoeTableData: [],
            shoeTableTemp: [],
            shoeRidFilter: '',
            checkgroup: [],
            curShoeTypeId: '',
            batchTypes: [],
            batchTypeNameList: [],
            curBatchType: {},
            userRole: '',
            userName: '',
            templateData: [],
            templateDisplayData: [],
            templateCustomerBrandMatch: [],
            templateCustomerNameMatch: [],
            customerBatchTemplateVis: false,
            batchTemplateForm: {
                templateName: '',
                customerName: '',
                customerBrand: '',
                templateDescription: '',
                templateDetail: []
            },
            colorOptions: [],
            orderForm: {
                orderRId: '',
                orderCid: '',
                customerId: null,
                orderStartDate: '',
                orderEndDate: '',
                status: '',
                salesman: ''
            },
            orderRidDuplicated: false,
            newOrderForm: {
                orderRId: '',
                orderCid: '',
                customerName: '',
                customerBrand: '',
                customerId: null,
                batchInfoTypeName: '',
                batchInfoTypeId: '',
                orderStartDate: '',
                orderEndDate: '',
                status: '',
                orderType: 'N',
                //显示名字用 建议改为salesmanName
                salesman: '',
                //新参数, 应该为当前用户的staff_id
                salesmanId: '',
                orderShoeTypes: [],
                batchInfoQuantity: [],
                customerShoeName: {},
                customerShoeColorName: {},
                //新参数 应该为被下发经理用户的staff_id
                supervisorId: '',
                sourceOrderRid: null,
                sourceOrderId: null,
                flag: false
            },
            batchForm: {
                customerId: '',
                packagingInfoName: '',
                packagingInfoLocale: '',
                batchInfoTypeId: '',
                size34Ratio: 0,
                size35Ratio: 0,
                size36Ratio: 0,
                size37Ratio: 0,
                size38Ratio: 0,
                size39Ratio: 0,
                size40Ratio: 0,
                size41Ratio: 0,
                size42Ratio: 0,
                size43Ratio: 0,
                size44Ratio: 0,
                size45Ratio: 0,
                size46Ratio: 0,
                totalQuantityRatio: 0
            },
            attrMapping: {
                size34Name: 'size34Ratio',
                size35Name: 'size35Ratio',
                size36Name: 'size36Ratio',
                size37Name: 'size37Ratio',
                size38Name: 'size38Ratio',
                size39Name: 'size39Ratio',
                size40Name: 'size40Ratio',
                size41Name: 'size41Ratio',
                size42Name: 'size42Ratio',
                size43Name: 'size43Ratio',
                size44Name: 'size44Ratio',
                size45Name: 'size45Ratio',
                size46Name: 'size46Ratio'
            },
            shortcuts: [
                {
                    text: '过去一周',
                    value: () => {
                        const end = new Date()
                        const start = new Date()
                        start.setTime(start.getTime() - 3600 * 1000 * 24 * 7)
                        return [start, end]
                    }
                },
                {
                    text: '过去一月',
                    value: () => {
                        const end = new Date()
                        const start = new Date()
                        start.setTime(start.getTime() - 3600 * 1000 * 24 * 30)
                        return [start, end]
                    }
                }
            ],
            sortRadio: 'asc',
            buttonText: '查看所有订单',
            buttonFlag: true,
            shoeTotalItems: 0,
            currentOrderCreatePage: 1,
            orderCreatePageSize: 20,
            currentShoeImageId: '',
            currentShoeColor: '',
            currentShoeColorId: 0,
            currentImageRow: {},
            imageUrl: '',
            selectedBatchTemplate: {}
        }
    },
    computed: {
        allowDeleteOrder(row) {
            return this.userRole == 4
        },
        uploadHeaders() {
            return {
                Authorization: `Bearer ${this.token}`
            }
        },
        computeTotal(row) {
            console.log(row)
        }
    },
    mounted() {
        this.$setAxiosToken()
        this.userInfo()
        // this.getAllOrders()
        this.getAllCutomers()
        // this.getAllOrderStatus()
        this.getAllShoes()
        this.getAllColors()
        this.getAllBatchTypes()
        this.initialStatusFilter()
        // this.getTemplate()
    },
    methods: {
        formatOrderType(orderType) {
            return orderType === 'F' ? '预报单' : '普通单'
        },
        async getAllColors() {
            const response = await axios.get(`${this.$apiBaseUrl}/general/allcolors`)
            this.colorOptions = response.data
        },
        initialStatusFilter() {
            if (this.role === '21') {
                this.orderStore.selectedOrderStatus = '我发起的订单'
                this.handleOrderStatusChange(this.orderStore.selectedOrderStatus)
            } else {
                this.orderStore.selectedOrderStatus = '我审批的订单'
                this.handleOrderStatusChange(this.orderStore.selectedOrderStatus)
            }
        },
        handleOrderCreatePageChange(newPage) {
            this.currentOrderCreatePage = newPage
            this.getAllShoes()
        },
        async userInfo() {
            const response = await axios.get(`${this.$apiBaseUrl}/order/onmount`)
            this.userName = response.data.staffName
            this.userRole = response.data.role
            console.log(this.userRole)
        },
        formatDateToYYYYMMDD(date) {
            const year = date.getFullYear()
            const month = String(date.getMonth() + 1).padStart(2, '0') // months are 0-indexed, so we add 1
            const day = String(date.getDate()).padStart(2, '0') // pad the day with leading zero if needed
            return `${year}-${month}-${day}`
        },
        handlePageChange(newPage) {
            this.orderStore.handlePageChange(newPage)
        },
        findOrderShoeTypeById(id) {
            return this.newOrderForm.orderShoeTypes.find((orderShoeType) => {
                return orderShoeType.shoeTypeId == id
            })
        },
        reselectSelected(ref, selected, displaydataentity, id) {
            console.log('reselectSelected called', { selected, id, displayLen: displaydataentity?.length })
            this.$nextTick(() => {
                selected.forEach((item) => {
                    const foundRow = displaydataentity.find((row) => {
                        return row[id] == item[id]
                    })
                    if (!foundRow) console.warn('reselectSelected: no matching display row for', item[id], 'id field', id)
                    ref.toggleRowSelection(foundRow, true)
                })
            })
        },
        resetBatchForm() {
            this.batchForm = {
                customerId: '',
                packagingInfoName: '',
                packagingInfoLocale: '',
                batchInfoTypeId: '',
                size34Ratio: 0,
                size35Ratio: 0,
                size36Ratio: 0,
                size37Ratio: 0,
                size38Ratio: 0,
                size39Ratio: 0,
                size40Ratio: 0,
                size41Ratio: 0,
                size42Ratio: 0,
                size43Ratio: 0,
                size44Ratio: 0,
                size45Ratio: 0,
                size46Ratio: 0,
                totalQuantityRatio: 0
            }
        },
        openImportDialog() {
            this.isImportVis = true
        },
        openCreateOrderDialogFromTemplate(row) {
            console.log(row)
            // If this row is a saved order template, load full template
            if (row.orderTemplateId) {
                this.loadOrderTemplateAndOpen(row.orderTemplateId)
                return
            }
            this.newOrderForm.batchInfoTypeId = row.batchInfoTypeId
            this.newOrderForm.batchInfoTypeName = row.batchInfoTypeName
            this.newOrderForm.customerId = row.customerId
            this.newOrderForm.customerBrand = row.customerBrand
            this.newOrderForm.customerName = row.customerName
            this.updateBatchType()
            this.openCreateOrderDialog()
            this.templateFilter = ''
            this.dialogStore.closeTemplateDialog()
        },

        async loadOrderTemplateAndOpen(orderTemplateId) {
            try {
                const resp = await axios.get(`${this.$apiBaseUrl}/ordercreate/getordertemplate`, {
                    params: { orderTemplateId }
                })
                const tpl = resp.data.orderTemplate || {}
                const orderData = tpl.orderData || {}
                // backend may expose the template's source order id either inside orderData or at the top level
                const sourceOrderIdFromResp = resp.data && resp.data.sourceOrderId ? resp.data.sourceOrderId : null
                const orderShoeData = tpl.orderShoeData || []

                // Populate basic fields
                this.newOrderForm.orderRId = ''
                this.newOrderForm.orderCid = ''
                this.newOrderForm.customerName = orderData.customerName || ''
                this.newOrderForm.customerBrand = orderData.customerBrand || ''
                this.newOrderForm.customerId = orderData.customerId || null
                this.newOrderForm.batchInfoTypeId = orderData.batchInfoTypeId || ''
                this.newOrderForm.batchInfoTypeName = orderData.batchInfoTypeName || ''
                // ensure batch type metadata and available batches are loaded so UI can auto-select
                if (!this.batchTypes || this.batchTypes.length === 0) {
                    try {
                        await this.getAllBatchTypes()
                    } catch (e) {
                        console.error('getAllBatchTypes failed', e)
                    }
                }
                this.updateBatchType()
                try {
                    if (this.newOrderForm.customerId) {
                        await this.getCustomerBatchInfo(this.newOrderForm.customerId)
                    }
                } catch (e) {
                    console.error('getCustomerBatchInfo failed', e)
                }
                this.newOrderForm.orderStartDate = ''
                this.newOrderForm.orderEndDate = ''
                this.newOrderForm.supervisorId = ''
                this.newOrderForm.salesman = this.userName
                this.newOrderForm.salesmanId = this.staffId
                // preserve source order identifiers when loading from a template
                this.newOrderForm.sourceOrderRid = orderData.sourceOrderRid || orderData.sourceOrderId || orderData.orderRid || null
                this.newOrderForm.sourceOrderId = orderData.sourceOrderId || orderData.sourceOrderRid || sourceOrderIdFromResp || null

                // Fill shoe types and allow editing (copy template data into orderShoeTypes)
                this.newOrderForm.orderShoeTypes = orderShoeData.map((s) => {
                    // normalize to expected orderShoeTypes shape used by creation UI
                    const item = Object.assign({}, s)
                    // ensure identifiers
                    item.shoeTypeId = item.shoeTypeId || item.shoeTypeId || item.shoeRid || item.shoeRid
                    item.shoeRid = item.shoeRid || item.orderShoeRid || item.shoeRid
                    item.shoeImageUrl = item.shoeImageUrl || item.shoeImageUrl || (item.shoeTypeImgUrl && item.shoeTypeImgUrl) || ''

                    // batch info: prefer orderShoeTypeBatchInfo or shoeTypeBatchInfoList
                    item.orderShoeTypeBatchInfo = item.orderShoeTypeBatchInfo || item.shoeTypeBatchInfoList || item.orderShoeTypeBatchInfo || []

                    // initialize mappings
                    item.quantityMapping = item.quantityMapping || {}
                    item.amountMapping = item.amountMapping || {}
                    if (Array.isArray(item.orderShoeTypeBatchInfo)) {
                        item.orderShoeTypeBatchInfo.forEach((batch) => {
                            const pid = batch.packagingInfoId
                            if (!pid) return
                            if (item.quantityMapping[pid] === undefined) {
                                // try to pick up defaults from template batch info
                                if (batch.unitPerRatio !== undefined && batch.unitPerRatio !== null) {
                                    item.quantityMapping[pid] = Number(batch.unitPerRatio) || 0
                                } else if (item.defaultQuantityMapping && item.defaultQuantityMapping[pid] !== undefined) {
                                    item.quantityMapping[pid] = Number(item.defaultQuantityMapping[pid]) || 0
                                } else {
                                    item.quantityMapping[pid] = 0
                                }
                            }
                            // compute amount mapping based on ratio
                            const ratio = batch.totalQuantityRatio || batch.totalQuantityRatio === 0 ? Number(batch.totalQuantityRatio) : 1
                            item.amountMapping[pid] = Number(item.quantityMapping[pid] || 0) * (ratio || 1)
                        })
                    }

                    // customer-provided fields
                    item.customerColorName = item.customerColorName || item.customerColor || ''
                    item.customerShoeName = item.customerShoeName || ''

                    // business remarks (may come from OrderShoe DB fields)
                    item.businessMaterialRemark = item.businessMaterialRemark || item.business_material_remark || ''
                    item.businessTechnicalRemark = item.businessTechnicalRemark || item.business_technical_remark || ''

                    // normalize color display fields used by create UI
                    // prefer explicit colorName, fall back to various possible keys
                    item.colorName = item.colorName || item.shoeTypeColorName || item.shoeColorName || item.color || ''
                    // normalize shoeTypeColors to an array of simple values if template provides objects
                    if (!item.shoeTypeColors) {
                        if (item.shoeTypeColorList && Array.isArray(item.shoeTypeColorList)) {
                            item.shoeTypeColors = item.shoeTypeColorList.map((c) => (typeof c === 'object' ? c.value || c.colorId || c.colorName || '' : c))
                        } else if (item.colors && Array.isArray(item.colors)) {
                            item.shoeTypeColors = item.colors.map((c) => (typeof c === 'object' ? c.value || c.colorId || c.colorName || '' : c))
                        } else {
                            item.shoeTypeColors = item.shoeTypeColors || []
                        }
                    } else {
                        // if shoeTypeColors provided as objects, map to values
                        if (Array.isArray(item.shoeTypeColors) && item.shoeTypeColors.length && typeof item.shoeTypeColors[0] === 'object') {
                            item.shoeTypeColors = item.shoeTypeColors.map((c) => c.value || c.colorId || c.colorName || '')
                        }
                    }

                    return item
                })

                // Map stored batch entries to the customer's batch objects so selection is shown in UI
                if (Array.isArray(this.newOrderForm.orderShoeTypes) && Array.isArray(this.customerDisplayBatchData)) {
                    console.log('mapping template batches to customerDisplayBatchData', { shoeTypesLen: this.newOrderForm.orderShoeTypes.length, batchDataLen: this.customerDisplayBatchData.length })
                    this.newOrderForm.orderShoeTypes.forEach((item) => {
                        if (!Array.isArray(item.orderShoeTypeBatchInfo)) return
                        const mapped = []
                        item.orderShoeTypeBatchInfo.forEach((batch) => {
                            const pid = batch.packagingInfoId || batch.packaging_info_id || batch.id || batch.packagingId
                            if (pid == null) {
                                console.warn('template batch missing packaging id', batch)
                                return
                            }
                            const found = this.customerDisplayBatchData.find((d) => String(d.packagingInfoId) === String(pid))
                            if (found) mapped.push(found)
                            else {
                                console.warn('no matching customer batch found for pid', pid, 'batch:', batch)
                                mapped.push(batch) // fallback to stored object
                            }
                        })
                        item.orderShoeTypeBatchInfo = mapped
                    })
                }

                // Recompute and normalize quantityMapping/amountMapping using the mapped batch objects
                this.newOrderForm.orderShoeTypes.forEach((item) => {
                    item.quantityMapping = item.quantityMapping || {}
                    item.amountMapping = item.amountMapping || {}
                    if (!Array.isArray(item.orderShoeTypeBatchInfo)) return
                    item.orderShoeTypeBatchInfo.forEach((batch) => {
                        const pid = batch.packagingInfoId || batch.packaging_info_id || batch.id || batch.packagingId
                        if (pid == null) return
                        // prefer existing numeric key, else string key
                        let q = item.quantityMapping[pid]
                        if (q === undefined) q = item.quantityMapping[String(pid)]
                        if (q === undefined) {
                            if (batch.unitPerRatio !== undefined && batch.unitPerRatio !== null) q = Number(batch.unitPerRatio) || 0
                            else if (item.defaultQuantityMapping && (item.defaultQuantityMapping[pid] !== undefined || item.defaultQuantityMapping[String(pid)] !== undefined)) {
                                q = Number(item.defaultQuantityMapping[pid] || item.defaultQuantityMapping[String(pid)]) || 0
                            } else {
                                q = 0
                            }
                        }
                        // store both string and numeric keys to be resilient
                        item.quantityMapping[pid] = q
                        item.quantityMapping[String(pid)] = q
                        const ratio = (batch.totalQuantityRatio !== undefined && batch.totalQuantityRatio !== null) ? Number(batch.totalQuantityRatio) : 1
                        item.amountMapping[pid] = Number(q || 0) * (ratio || 1)
                        item.amountMapping[String(pid)] = item.amountMapping[pid]
                    })
                })

                // reset helper maps and set flag so next-step is allowed
                this.newOrderForm.customerShoeName = {}
                this.newOrderForm.customerShoeColorName = {}
                this.newOrderForm.flag = true
                this.openCreateOrderDialog()
                // If template didn't include shoes, inform user and scroll to shoe selection area
                this.$nextTick(() => {
                    if (!this.newOrderForm.orderShoeTypes || this.newOrderForm.orderShoeTypes.length === 0) {
                        ElMessage.info('模板未包含鞋型，请在下方选择鞋型或点击 添加新鞋型')
                        // try to scroll to shoe table
                        const el = document.querySelector('.order-shoe-create-table') || document.querySelector('.el-table')
                        if (el && el.scrollIntoView) el.scrollIntoView({ behavior: 'smooth', block: 'center' })
                    }
                })
                this.dialogStore.closeTemplateDialog()
            } catch (err) {
                console.error('loadOrderTemplateAndOpen error', err)
                ElMessage.error('加载模板失败')
            }
        },

        async showOrderTemplates() {
            try {
                const response = await axios.get(`${this.$apiBaseUrl}/ordercreate/getordertemplates`)
                this.templateData = response.data
                this.templateDisplayData = this.templateData
                this.dialogStore.openTemplateDialog()
            } catch (error) {
                console.error('Error fetching order templates:', error)
                ElMessage.error('加载订单模板失败')
            }
        },
        injectTemplateTestData() {
            console.log('injectTemplateTestData invoked')
            ElMessage.info('开始注入模板测试数据')
            try {
                // Test template JSON provided by user (compact true)
                const tpl = {
                    meta: { customerId: 48, customerName: '15', customerBrand: 'TUOTUO', batchInfoTypeId: null, batchInfoTypeName: 'EU女' },
                    shoes: [
                        { shoeId: 719, colorId: 1, shoeRid: '5E1392', colorName: null, shoeTypeId: 1547, quantityMapping: { '602': 80.0 }, customerShoeName: '26-03', packagingInfoIds: [602], customerColorName: 'NEGRO' },
                        { shoeId: 719, colorId: 3, shoeRid: '5E1392', colorName: null, shoeTypeId: 1548, quantityMapping: { '602': 40.0 }, customerShoeName: '26-03', packagingInfoIds: [602], customerColorName: 'MARRON' }
                    ],
                    compact: true,
                    packagingInfos: [
                        { size34Ratio: 1, size35Ratio: 1, size36Ratio: 2, size37Ratio: 2, size38Ratio: 1, size39Ratio: 1, size40Ratio: 0, size41Ratio: 0, size42Ratio: 0, size43Ratio: 0, size44Ratio: 0, size45Ratio: 0, size46Ratio: 0, packagingInfoId: 602, packagingInfoName: '35-40/112211', totalQuantityRatio: 8 }
                    ]
                }

                // populate customer / batch metadata
                this.newOrderForm.customerName = tpl.meta.customerName
                this.newOrderForm.customerBrand = tpl.meta.customerBrand
                this.newOrderForm.customerId = tpl.meta.customerId
                this.newOrderForm.batchInfoTypeName = tpl.meta.batchInfoTypeName || ''
                this.updateBatchType()

                // set customerDisplayBatchData from packagingInfos
                this.customerDisplayBatchData = tpl.packagingInfos.map((p) => ({
                    packagingInfoId: p.packagingInfoId,
                    packagingInfoName: p.packagingInfoName || p.packagingInfoName || p.packagingInfoName,
                    size34Ratio: p.size34Ratio,
                    size35Ratio: p.size35Ratio,
                    size36Ratio: p.size36Ratio,
                    size37Ratio: p.size37Ratio,
                    size38Ratio: p.size38Ratio,
                    size39Ratio: p.size39Ratio,
                    size40Ratio: p.size40Ratio,
                    size41Ratio: p.size41Ratio,
                    size42Ratio: p.size42Ratio,
                    size43Ratio: p.size43Ratio,
                    size44Ratio: p.size44Ratio,
                    size45Ratio: p.size45Ratio,
                    size46Ratio: p.size46Ratio,
                    totalQuantityRatio: p.totalQuantityRatio,
                    packagingInfoLocale: this.newOrderForm.batchInfoTypeName
                }))

                // map shoes into orderShoeTypes shape
                this.newOrderForm.orderShoeTypes = tpl.shoes.map((s) => {
                    const orderShoe = {
                        shoeRid: s.shoeRid,
                        shoeId: s.shoeId,
                        shoeTypeId: s.shoeTypeId,
                        colorId: s.colorId,
                        colorName: s.colorName || s.customerColorName || '',
                        customerShoeName: s.customerShoeName || '',
                        customerColorName: s.customerColorName || '',
                        quantityMapping: {},
                        amountMapping: {}
                    }
                    // attach batch info objects by matching packagingInfoIds
                    orderShoe.orderShoeTypeBatchInfo = (s.packagingInfoIds || []).map((pid) => {
                        const found = this.customerDisplayBatchData.find((d) => String(d.packagingInfoId) === String(pid))
                        return found || { packagingInfoId: pid }
                    })

                    // populate quantityMapping from template
                    Object.keys(s.quantityMapping || {}).forEach((k) => {
                        orderShoe.quantityMapping[k] = s.quantityMapping[k]
                        orderShoe.quantityMapping[String(k)] = s.quantityMapping[k]
                    })

                    // compute amountMapping using totalQuantityRatio from batch info
                    orderShoe.orderShoeTypeBatchInfo.forEach((batch) => {
                        const pid = batch.packagingInfoId || batch.packaging_info_id || batch.id || batch.packagingId
                        const ratio = Number(batch.totalQuantityRatio || 1)
                        const q = orderShoe.quantityMapping[pid] !== undefined ? orderShoe.quantityMapping[pid] : orderShoe.quantityMapping[String(pid)] || 0
                        orderShoe.amountMapping[pid] = Number(q || 0) * ratio
                        orderShoe.amountMapping[String(pid)] = orderShoe.amountMapping[pid]
                    })

                    return orderShoe
                })

                this.newOrderForm.flag = true
                this.openCreateOrderDialog()
                console.log('injection complete', { orderShoeTypes: this.newOrderForm.orderShoeTypes, customerDisplayBatchData: this.customerDisplayBatchData })
                ElMessage.success('模板测试数据注入完成（查看控制台）')
            } catch (e) {
                console.error('injectTemplateTestData failed', e)
                ElMessage.error('注入失败，请查看控制台')
            }
        },

        async deleteOrderTemplate(row) {
            const id = row.orderTemplateId
            if (!id) {
                ElMessage.error('非整单模板，不支持此删除接口')
                return
            }
            this.$confirm(`确认删除模板 "${row.templateName}"?`, '提示', {
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                type: 'warning'
            }).then(async () => {
                try {
                    const resp = await axios.post(`${this.$apiBaseUrl}/ordercreate/deleteordertemplate`, { orderTemplateId: id })
                    if (resp.status === 200) {
                        ElMessage.success('模板删除成功')
                        await this.showOrderTemplates()
                    }
                } catch (err) {
                    console.error(err)
                    ElMessage.error('模板删除失败')
                }
            })
        },

        async editOrderTemplate(row) {
            const id = row.orderTemplateId
            if (!id) {
                ElMessage.error('仅支持整单模板重命名')
                return
            }
            const { value: name } = await this.$prompt('请输入新的模板名称', '重命名模板', {
                inputValue: row.templateName || '',
                confirmButtonText: '确定',
                cancelButtonText: '取消'
            }).catch(() => ({ value: null }))
            if (!name) return
            try {
                const resp = await axios.post(`${this.$apiBaseUrl}/ordercreate/updateordertemplate`, { orderTemplateId: id, templateName: name })
                if (resp.status === 200) {
                    ElMessage.success('模板重命名成功')
                    await this.showOrderTemplates()
                }
            } catch (err) {
                console.error(err)
                ElMessage.error('模板重命名失败')
            }
        },
        openCreateOrderDialog() {
            this.orderRidDuplicated = false
            this.newOrderForm.orderStartDate = this.formatDateToYYYYMMDD(new Date())
            this.newOrderForm.salesman = this.userName
            this.newOrderForm.salesmanId = this.staffId
            this.dialogStore.openOrderCreationDialog()
        },
        async showTemplate() {
            const response = await axios.get(`${this.$apiBaseUrl}/ordercreate/template`, {
                params: {
                    staffId: this.staffId
                }
            })
            this.dialogStore.openTemplateDialog()
            this.templateData = response.data
            this.templateDisplayData = this.templateData
        },
        // getTemplate(){
        //     const response = axios.get(`${this.$apiBaseUrl}/ordercreate/template`, {params: {
        //             staffId:this.staffId
        //         }})
        //     console.log(response.data)
        // },
        async openPreviewDialog(row) {
            this.orderData = row
            await this.getOrderOrderShoe(row.orderRid)
            await this.getOrderDocInfo(row.orderRid)
            this.previewOrderVis = true
        },
        openSubmitDocDialog(type) {
            this.isSubmitDocVis = true
            if (type == 0) {
                this.submitDocType = 0
            } else {
                this.submitDocType = 1
            }
        },
        async openAddBatchInfoDialog(row) {
            this.curShoeTypeId = row.shoeTypeId
            this.dialogStore.openAddBatchInfoDialog()
            const idField = 'packagingInfoId'

            // wait for child dialog and its internal table ref to be available
            const getTableRef = () => {
                try {
                    const child = this.$refs.batchInfoDialog
                    if (!child) return null
                    // exposed ref object
                    const exposedRef = child.batchTable
                    if (exposedRef) {
                        // if it's a ref object (Composition API), unwrap .value
                        if (exposedRef.value && typeof exposedRef.value.toggleRowSelection === 'function') return exposedRef.value
                        if (typeof exposedRef.toggleRowSelection === 'function') return exposedRef
                    }
                    // fallback to child's $refs
                    if (child.$refs && child.$refs.batchTable && typeof child.$refs.batchTable.toggleRowSelection === 'function') return child.$refs.batchTable
                } catch (e) {
                    // ignore
                }
                return null
            }

            let tableRef = null
            for (let i = 0; i < 10; i++) {
                tableRef = getTableRef()
                if (tableRef) break
                // wait 50ms and retry
                // eslint-disable-next-line no-await-in-loop
                await new Promise((r) => setTimeout(r, 50))
            }

            if (!tableRef) {
                console.warn('openAddBatchInfoDialog: unable to find batchTable ref on batchInfoDialog after retries')
                return
            }

            // use canonical row from newOrderForm to avoid shallow/copy issues
            const canonicalRow = (this.newOrderForm.orderShoeTypes || []).find((r) => r.shoeTypeId == row.shoeTypeId) || row
            // log row batch info for debugging
            console.log('openAddBatchInfoDialog row data for selection (canonical)', { shoeTypeId: canonicalRow.shoeTypeId, orderShoeTypeBatchInfo: canonicalRow.orderShoeTypeBatchInfo, quantityMapping: canonicalRow.quantityMapping, packagingInfoIds: canonicalRow.packagingInfoIds })

            // derive packaging ids from multiple possible sources to maximize chance of matching
            const pidSet = new Set()
            try {
                if (Array.isArray(canonicalRow.orderShoeTypeBatchInfo) && canonicalRow.orderShoeTypeBatchInfo.length) {
                    canonicalRow.orderShoeTypeBatchInfo.forEach((b) => {
                        const v = b.packagingInfoId || b.packaging_info_id || b.id || b.packagingId
                        if (v != null) pidSet.add(String(v))
                    })
                }
                // packagingInfoIds array
                if (Array.isArray(canonicalRow.packagingInfoIds) && canonicalRow.packagingInfoIds.length) {
                    canonicalRow.packagingInfoIds.forEach((v) => pidSet.add(String(v)))
                }
                // quantityMapping keys
                if (canonicalRow.quantityMapping && typeof canonicalRow.quantityMapping === 'object') {
                    Object.keys(canonicalRow.quantityMapping).forEach((k) => pidSet.add(String(k)))
                }
                // amountMapping keys
                if (canonicalRow.amountMapping && typeof canonicalRow.amountMapping === 'object') {
                    Object.keys(canonicalRow.amountMapping).forEach((k) => pidSet.add(String(k)))
                }
                // defaultQuantityMapping
                if (canonicalRow.defaultQuantityMapping && typeof canonicalRow.defaultQuantityMapping === 'object') {
                    Object.keys(canonicalRow.defaultQuantityMapping).forEach((k) => pidSet.add(String(k)))
                }
            } catch (e) {
                console.error('error computing pidSet for selection', e)
            }

            const pids = Array.from(pidSet)
            console.log('openAddBatchInfoDialog: derived packaging ids for selection', pids)
            const selectedForReselect = pids.map((k) => ({ packagingInfoId: isNaN(Number(k)) ? k : Number(k) }))

            this.reselectSelected(tableRef, selectedForReselect || [], this.customerDisplayBatchData, idField)
        },
        openAddShoeDialog() {
            this.dialogStore.openAddShoeDialog()
        },
        openAddShoeTypeDialog(row) {
            let target = row
            if (!target) {
                // prefer the currently selected shoe type in selection table
                if (this.selectedShoeList && this.selectedShoeList.length > 0) target = this.selectedShoeList[0]
                else if (this.newOrderForm.orderShoeTypes && this.newOrderForm.orderShoeTypes.length === 1) target = this.newOrderForm.orderShoeTypes[0]
            }
            if (!target) {
                ElMessage.error('请先选择一个鞋款（在左侧鞋型列表中选择或展开鞋型并勾选）')
                return
            }
            this.shoeIdToAdd = target.shoeRid || target.shoeRid
            const shoeTypeColors = Array.isArray(target.shoeTypeColors) ? target.shoeTypeColors.map((c) => (typeof c === 'object' ? c.value || c.colorId || c.color_name || c.colorName : c)) : []
            this.dialogStore.openAddShoeTypeDialog({
                shoeRid: target.shoeRid,
                shoeId: target.shoeId || target.shoeRid,
                shoeTypeColors: shoeTypeColors
            })
        },
        openAddColorDialog(row) {
            // 订单里现有的鞋型列表（第二步表格的数据）
            const list = Array.isArray(this.newOrderForm.orderShoeTypes)
                ? this.newOrderForm.orderShoeTypes
                : []

            // 1）一个都没有，才提示
            if (list.length === 0) {
                ElMessage.error('当前订单还没有鞋型，请先在第一步选择鞋型')
                return
            }

            let target = null

            // 2）只有一个鞋型：完全自动使用这一行，不需要任何点击
            if (list.length === 1) {
                target = list[0]
            } else {
                // 3）有多个鞋型时的兜底规则：

                // 3.1 如果你以后在表格里加了 row-click 记录当前行，就用这个（可选）
                if (this.currentOrderShoeTypeRow) {
                    target = this.currentOrderShoeTypeRow
                } else {
                    // 3.2 如果虽然有多条，但其实只有一个鞋型编号（同一双鞋不同颜色），也自动用第一个
                    const uniqueRid = [...new Set(list.map(i => i.shoeRid))]
                    if (uniqueRid.length === 1) {
                        target = list[0]
                    } else {
                        // 3.3 真正多鞋型、又没点击时，才让你点行
                        ElMessage.error('当前存在多个鞋型号，请在“订单详情填写”列表中点击选择一个鞋型再添加颜色')
                        return
                    }
                }
            }

            const shoeTypeColorsRaw = Array.isArray(target.shoeTypeColors) ? target.shoeTypeColors : []
            const shoeTypeColorIds = shoeTypeColorsRaw.map((c) => (typeof c === 'object' ? c.value || c.colorId || c.color_name || c.colorName : c))

            // compute already-added color ids for this shoeRid in the create form
            const alreadyAdded = (this.newOrderForm.orderShoeTypes || [])
                .filter((r) => r.shoeRid == target.shoeRid)
                .map((r) => r.colorId || r.color_id || r.color || r.colorName)
            const alreadyAddedStr = alreadyAdded.map((x) => String(x))

            // map to option objects using global colorOptions (loaded during mount)
            const availableOptions = (shoeTypeColorIds || []).reduce((acc, id) => {
                if (id == null) return acc
                if (alreadyAddedStr.includes(String(id))) return acc
                const found = (this.colorOptions || []).find((c) => String(c.value) === String(id) || String(c.label) === String(id))
                acc.push(found || { value: id, label: String(id) })
                return acc
            }, [])

            console.log('openAddColorDialog target =', target, 'availableOptions:', availableOptions)

            // set dialog store form values then open
            // If called with a real row, treat as edit; ignore click event payloads
            const isRow = row && (row.shoeRid || row.shoeId || row.shoeTypeId)
            this.dialogStore.addColorForm.editTargetRow = isRow ? row : null
            const resolvedShoeId = target.shoeId || target.shoeRid
            this.dialogStore.addColorForm.shoeRid = target.shoeRid
            this.dialogStore.addColorForm.shoeId = resolvedShoeId
            this.dialogStore.addColorForm.shoeTypeColors = availableOptions
            this.dialogStore.openAddColorDialog({ shoeRid: target.shoeRid, shoeId: resolvedShoeId, shoeTypeColors: availableOptions })
            this.dialogStore.addColorDialogVis = true
            console.log('addColorDialogVis =', this.dialogStore.addColorDialogVis)
        },

        removeSelectedShoe(item) {
            const id = item.shoeTypeId || item.shoeRid
            const idx = (this.newOrderForm.orderShoeTypes || []).findIndex((r) => ((r.shoeTypeId || r.shoeRid) == id))
            if (idx >= 0) {
                this.newOrderForm.orderShoeTypes.splice(idx, 1)
            }
        },





        async handleAddColorDialogSubmit(payload) {
            try {
                console.debug('handleAddColorDialogSubmit start', { payload, addColorForm: this.dialogStore.addColorForm })
                const colorIds = Array.isArray(payload.colorIds) ? payload.colorIds : []
                if (colorIds.length === 0) {
                    ElMessage.info('未选择颜色')
                    return
                }
                const shoeId = this.dialogStore.addColorForm.shoeId || this.dialogStore.addColorForm.shoeRid
                const shoeRid = this.dialogStore.addColorForm.shoeRid || ''
                if (!shoeId) {
                    ElMessage.error('未找到目标鞋款')
                    return
                }
                // Find master shoe record
                let masterShoe = this.shoeTableData.find((s) => String(s.shoeId) === String(shoeId) || String(s.shoeRid) === String(shoeId) || (shoeRid && String(s.shoeRid) === String(shoeRid)))
                console.debug('handleAddColorDialogSubmit masterShoe', masterShoe)

                // Compute colors already present in the create-order form for this shoeRid
                const alreadyInOrder = (this.newOrderForm.orderShoeTypes || []).filter((r) => String(r.shoeRid) === String(masterShoe?.shoeRid)).map((r) => String(r.colorId || r.color_id || r.color || r.colorName))

                // Determine which selected colors exist on master and which need server add
                let masterColorIds = []
                if (masterShoe && Array.isArray(masterShoe.shoeTypeData) && masterShoe.shoeTypeData.length) {
                    masterColorIds = masterShoe.shoeTypeData.map((t) => String(t.colorId || t.color_id || t.value || t.color || t.colorName || t.label))
                } else if (this.dialogStore?.addColorForm?.shoeTypeColors && Array.isArray(this.dialogStore.addColorForm.shoeTypeColors)) {
                    // fallback: use the shoeTypeColors already passed into the dialog (may be option objects)
                    masterColorIds = this.dialogStore.addColorForm.shoeTypeColors.map((c) => (typeof c === 'object' ? String(c.value || c.colorId || c.color_id || c.label) : String(c)))
                }

                // If we couldn't find master shoe locally, refresh shoe table and retry to avoid constructing invalid shoeTypeIds
                if (!masterShoe) {
                    console.debug('masterShoe not found locally; refreshing shoeTableData')
                    try {
                        await this.getAllShoes()
                        // recompute masterShoe and masterColorIds after refresh
                        const refreshed = this.shoeTableData.find((s) => String(s.shoeId) === String(shoeId) || String(s.shoeRid) === String(shoeId) || (shoeRid && String(s.shoeRid) === String(shoeRid)))
                        if (refreshed) {
                            console.debug('found masterShoe after refresh', refreshed)
                            masterShoe = refreshed
                            if (Array.isArray(masterShoe.shoeTypeData)) {
                                masterColorIds = masterShoe.shoeTypeData.map((t) => String(t.colorId || t.color_id || t.value || t.color || t.colorName || t.label))
                            }
                        } else {
                            console.warn('masterShoe still not found after refresh')
                            if (shoeRid) {
                                try {
                                    const fetched = await this.fetchShoeByRid(shoeRid)
                                    if (fetched) {
                                        masterShoe = fetched
                                        if (Array.isArray(masterShoe.shoeTypeData)) {
                                            masterColorIds = masterShoe.shoeTypeData.map((t) => String(t.colorId || t.color_id || t.value || t.color || t.colorName || t.label))
                                        }
                                        const exists = this.shoeTableData.some((s) => String(s.shoeId) === String(masterShoe.shoeId) || String(s.shoeRid) === String(masterShoe.shoeRid))
                                        if (!exists) this.shoeTableData.push(masterShoe)
                                    }
                                } catch (e) {
                                    console.warn('fetchShoeByRid failed', e)
                                }
                            }
                        }
                    } catch (e) {
                        console.warn('failed to refresh shoeTableData', e)
                    }
                }

                // If dialog was opened to edit a specific existing row, handle single-selection edit here
                const maybeEditTarget = this.dialogStore?.addColorForm?.editTargetRow || null
                const editTarget = maybeEditTarget && (maybeEditTarget.shoeRid || maybeEditTarget.shoeId || maybeEditTarget.shoeTypeId) ? maybeEditTarget : null
                if (editTarget) {
                    // require single selection when editing
                    if (colorIds.length !== 1) {
                        ElMessage.error('编辑颜色时请选择且仅选择一个颜色')
                        return
                    }
                    const selectedCid = String(colorIds[0])
                    const currentCid = String(editTarget.colorId || editTarget.color_id || editTarget.color || '')
                    if (selectedCid === currentCid) {
                        ElMessage.info('颜色未改变')
                        this.dialogStore.closeAddColorDialog()
                        this.dialogStore.resetAddColorForm()
                        return
                    }

                    // If selected color exists on master, apply directly
                    if (masterColorIds.includes(selectedCid)) {
                        let foundType = null
                        if (masterShoe && Array.isArray(masterShoe.shoeTypeData)) {
                            foundType = masterShoe.shoeTypeData.find((t) => {
                                const tvals = [t.colorId, t.color_id, t.value, t.colorName, t.label].map((v) => String(v))
                                return tvals.includes(selectedCid) || String(t.colorName || t.label) === selectedCid
                            })
                        }
                        if (foundType) {
                            const newRow = Object.assign({}, editTarget, {
                                shoeTypeId: foundType.shoeTypeId || foundType.id || null,
                                colorId: foundType.colorId || foundType.color_id || selectedCid,
                                colorName: foundType.colorName || foundType.label || ''
                            })
                            const idx = this.newOrderForm.orderShoeTypes.findIndex((r) => r === editTarget)
                            if (idx !== -1) this.newOrderForm.orderShoeTypes.splice(idx, 1, newRow)
                            else this.newOrderForm.orderShoeTypes = this.newOrderForm.orderShoeTypes.map((r) => (r === editTarget ? newRow : r))
                        } else {
                            const gf = (this.colorOptions || []).find((c) => String(c.value) === selectedCid || String(c.label) === selectedCid)
                            const newRow = Object.assign({}, editTarget, {
                                shoeTypeId: null,
                                colorId: selectedCid,
                                colorName: gf ? gf.label : ''
                            })
                            const idx = this.newOrderForm.orderShoeTypes.findIndex((r) => r === editTarget)
                            if (idx !== -1) this.newOrderForm.orderShoeTypes.splice(idx, 1, newRow)
                            else this.newOrderForm.orderShoeTypes = this.newOrderForm.orderShoeTypes.map((r) => (r === editTarget ? newRow : r))
                        }
                        this.newOrderForm.orderShoeTypes = [...this.newOrderForm.orderShoeTypes]
                        this.newOrderForm.flag = true
                        this.dialogStore.closeAddColorDialog()
                        this.dialogStore.resetAddColorForm()
                        ElMessage.success('颜色修改成功')
                        return
                    }

                    // Otherwise, create color on server then update row
                    const payloadToServerEdit = { shoeId: shoeId, colorId: [selectedCid], shoeTypeColors: [selectedCid] }
                    const resp = await axios.post(`${this.$apiBaseUrl}/shoemanage/addshoetype`, payloadToServerEdit)
                    console.debug('addshoetype (edit) response', resp && resp.data)
                    if (resp && resp.status === 200) {
                        const created = resp.data && resp.data.created ? resp.data.created : []
                        const c = created.find((x) => String(x.colorId) === selectedCid) || created[0]
                        if (c) {
                            // try to get color name from local colorOptions first
                            let colorLabel = ''
                            const foundColor = (this.colorOptions || []).find((co) => String(co.value) === String(c.colorId) || String(co.label) === String(c.colorId))
                            if (foundColor) colorLabel = foundColor.label
                            else {
                                try {
                                    const clrResp = await axios.get(`${this.$apiBaseUrl}/general/allcolors`)
                                    this.colorOptions = clrResp.data || this.colorOptions
                                    const f2 = (this.colorOptions || []).find((co) => String(co.value) === String(c.colorId) || String(co.label) === String(c.colorId))
                                    if (f2) colorLabel = f2.label
                                } catch (e) {
                                    console.warn('failed to refresh colorOptions', e)
                                }
                            }
                            const newRow = Object.assign({}, editTarget, {
                                    shoeTypeId: c.shoeTypeId || null,
                                    colorId: c.colorId,
                                    colorName: colorLabel || ''
                                })
                            const idx = this.newOrderForm.orderShoeTypes.findIndex((r) => r === editTarget)
                            if (idx !== -1) this.newOrderForm.orderShoeTypes.splice(idx, 1, newRow)
                            else this.newOrderForm.orderShoeTypes = this.newOrderForm.orderShoeTypes.map((r) => (r === editTarget ? newRow : r))
                            // try to remap names/ids from refreshed master and populate colorName
                            try {
                                await this.getAllShoes()
                                console.debug('shoeTableData after refresh', this.shoeTableData.find((s) => String(s.shoeId) === String(shoeId) || String(s.shoeRid) === String(editTarget.shoeRid)))
                                await this.remapOrderShoeTypesShoeTypeIds()
                                // attempt to fill colorName for the updated row
                                const updatedIdx = this.newOrderForm.orderShoeTypes.findIndex((r) => String(r.colorId) === String(c.colorId) && (String(r.shoeRid) === String(c.shoeRid) || String(r.shoeId) === String(c.shoeId) || String(r.shoeId) === String(shoeId)))
                                if (updatedIdx !== -1) {
                                    const row = this.newOrderForm.orderShoeTypes[updatedIdx]
                                    const master = this.shoeTableData.find((s) => String(s.shoeRid) === String(row.shoeRid) || String(s.shoeId) === String(row.shoeId))
                                    if (master && Array.isArray(master.shoeTypeData)) {
                                        const match = master.shoeTypeData.find((t) => String(t.colorId || t.color_id || t.value) === String(row.colorId) || String(t.shoeTypeId || t.id) === String(row.shoeTypeId))
                                        if (match) {
                                            const newRow2 = Object.assign({}, row, { colorName: match.colorName || match.label || '' })
                                            this.newOrderForm.orderShoeTypes.splice(updatedIdx, 1, newRow2)
                                        }
                                    }
                                }
                            } catch (e) {
                                console.warn('remap after edit addshoetype failed', e)
                            }
                        }
                        this.newOrderForm.orderShoeTypes = [...this.newOrderForm.orderShoeTypes]
                        this.newOrderForm.flag = true
                        this.dialogStore.closeAddColorDialog()
                        this.dialogStore.resetAddColorForm()
                        ElMessage.success('颜色修改成功')
                        return
                    } else {
                        ElMessage.error('修改颜色失败')
                        return
                    }
                }

                const toAddToOrder = []
                const toCreateOnServer = []

                colorIds.forEach((cid) => {
                    const sCid = String(cid)
                    if (alreadyInOrder.includes(sCid)) return // skip duplicates in order
                    if (masterColorIds.includes(sCid)) {
                        toAddToOrder.push(sCid)
                    } else {
                        toCreateOnServer.push(sCid)
                    }
                })

                console.debug('handleAddColorDialogSubmit computed', { alreadyInOrder, masterColorIds, toAddToOrder, toCreateOnServer })

                // First, add any existing master colors into the order form immediately
                if (masterShoe && Array.isArray(masterShoe.shoeTypeData) && toAddToOrder.length) {
                    const beforeLen = (this.newOrderForm.orderShoeTypes || []).length
                    toAddToOrder.forEach((sCid) => {
                        const foundType = masterShoe.shoeTypeData.find((t) => String(t.colorId || t.color_id || t.value || t.color || t.colorName || t.label) === String(sCid) || String(t.colorName || t.label) === String(sCid))
                        const newRow = {}
                        if (foundType) {
                            Object.assign(newRow, foundType)
                            newRow.shoeRid = masterShoe.shoeRid
                            newRow.shoeId = masterShoe.shoeId
                            newRow.shoeTypeId = foundType.shoeTypeId || foundType.id || null
                            newRow.colorId = foundType.colorId || foundType.color_id || sCid
                            newRow.colorName = foundType.colorName || foundType.label || ''
                        } else {
                            newRow.shoeRid = masterShoe.shoeRid
                            newRow.shoeId = masterShoe.shoeId
                            newRow.shoeTypeId = null
                            newRow.colorId = sCid
                            newRow.colorName = ''
                        }
                        newRow.customerShoeName = ''
                        newRow.customerColorName = ''
                        newRow.quantityMapping = {}
                        newRow.amountMapping = {}
                        newRow.orderShoeTypeBatchInfo = []
                        this.newOrderForm.orderShoeTypes = this.newOrderForm.orderShoeTypes || []
                        this.newOrderForm.orderShoeTypes.push(newRow)
                    })
                    // force vue reactivity refresh
                    this.newOrderForm.orderShoeTypes = [...this.newOrderForm.orderShoeTypes]
                    await this.$nextTick()
                    const afterLen = (this.newOrderForm.orderShoeTypes || []).length
                    console.debug('orderShoeTypes refreshed after adding existing master colors', { beforeLen, afterLen })
                }

                // If masterShoe not available locally, construct rows from dialogStore or global colorOptions
                else if ((!masterShoe || !Array.isArray(masterShoe.shoeTypeData) || masterShoe.shoeTypeData.length === 0) && toAddToOrder.length) {
                    const fallbackRid = this.dialogStore?.addColorForm?.shoeRid || this.dialogStore?.addColorForm?.shoeId || ''
                    const fallbackShoeId = this.dialogStore?.addColorForm?.shoeId || ''
                    const shoeTypeColorsFallback = Array.isArray(this.dialogStore?.addColorForm?.shoeTypeColors) ? this.dialogStore.addColorForm.shoeTypeColors : []
                    const beforeLen = (this.newOrderForm.orderShoeTypes || []).length
                    toAddToOrder.forEach((sCid) => {
                        const newRow = {}
                        let foundOpt = null
                        if (shoeTypeColorsFallback && shoeTypeColorsFallback.length) {
                            foundOpt = shoeTypeColorsFallback.find((c) => String((c && (c.value || c.colorId || c.color_id)) || c) === String(sCid) || String((c && (c.label || c.colorName)) || '') === String(sCid))
                        }
                        if (foundOpt) {
                            newRow.shoeRid = fallbackRid
                            newRow.shoeId = fallbackShoeId
                            newRow.shoeTypeId = foundOpt.shoeTypeId || foundOpt.id || null
                            newRow.colorId = foundOpt.value || foundOpt.colorId || foundOpt.color_id || sCid
                            newRow.colorName = foundOpt.label || foundOpt.colorName || ''
                        } else {
                            const foundGlobal = (this.colorOptions || []).find((c) => String(c.value) === String(sCid) || String(c.label) === String(sCid))
                            newRow.shoeRid = fallbackRid
                            newRow.shoeId = fallbackShoeId
                            newRow.shoeTypeId = null
                            newRow.colorId = sCid
                            newRow.colorName = foundGlobal ? foundGlobal.label : ''
                        }
                        newRow.customerShoeName = ''
                        newRow.customerColorName = ''
                        newRow.quantityMapping = {}
                        newRow.amountMapping = {}
                        newRow.orderShoeTypeBatchInfo = []
                        this.newOrderForm.orderShoeTypes = this.newOrderForm.orderShoeTypes || []
                        this.newOrderForm.orderShoeTypes.push(newRow)
                    })
                    this.newOrderForm.orderShoeTypes = [...this.newOrderForm.orderShoeTypes]
                    await this.$nextTick()
                    const afterLen = (this.newOrderForm.orderShoeTypes || []).length
                    console.debug('orderShoeTypes refreshed after adding fallback colors', { beforeLen, afterLen })
                }

                // If nothing needs server creation, we're done (skip API)
                if (toCreateOnServer.length === 0) {
                    if (toAddToOrder.length === 0) ElMessage.info('选中颜色已存在，不会重复添加')
                    else ElMessage.success('颜色添加成功')
                    this.newOrderForm.flag = true
                    this.dialogStore.closeAddColorDialog()
                    this.dialogStore.resetAddColorForm()
                    return
                }

                // Optimistic UI: add rows immediately so the table updates before服务器响应
                const pendingRows = []
                const pendingKeyPrefix = `tmp_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`
                // refresh colorOptions so we have latest labels for newly created colors
                try {
                    await this.refreshColorOptions()
                } catch (e) {
                    console.warn('refreshColorOptions before optimistic add failed', e)
                }

                toCreateOnServer.forEach((sCid, idx) => {
                    const numericCid = isNaN(Number(sCid)) ? sCid : Number(sCid)
                    const exists = (this.newOrderForm.orderShoeTypes || []).some(
                        (r) =>
                            String(r.colorId || r.color_id) === String(numericCid) &&
                            String(r.shoeRid || r.shoeId) === String(this.dialogStore.addColorForm.shoeRid || shoeId)
                    )
                    if (exists) return
                    const foundGlobal = (this.colorOptions || []).find(
                        (c) => String(c.value) === String(numericCid) || String(c.label) === String(numericCid)
                    )
                    const pendingRow = {
                        shoeRid: this.dialogStore.addColorForm.shoeRid || '',
                        shoeId: shoeId,
                        shoeTypeId: `${pendingKeyPrefix}_${idx}`,
                        colorId: numericCid,
                        colorName: foundGlobal ? foundGlobal.label : String(numericCid),
                        customerShoeName: '',
                        customerColorName: '',
                        quantityMapping: {},
                        amountMapping: {},
                        orderShoeTypeBatchInfo: [],
                        __pendingCreateColorId: numericCid
                    }
                    pendingRows.push(pendingRow)
                })
                if (pendingRows.length) {
                    this.newOrderForm.orderShoeTypes = this.newOrderForm.orderShoeTypes || []
                    this.newOrderForm.orderShoeTypes.push(...pendingRows)
                    this.newOrderForm.orderShoeTypes = [...this.newOrderForm.orderShoeTypes]
                }

                // Otherwise, create missing colors on server then merge results into order form
                const payloadToServer = {
                    shoeId: Number(shoeId),
                    colorId: toCreateOnServer.map((c) => (isNaN(Number(c)) ? c : Number(c))),
                    shoeTypeColors: toCreateOnServer.map((c) => (isNaN(Number(c)) ? c : Number(c)))
                }
                const response = await axios.post(`${this.$apiBaseUrl}/shoemanage/addshoetype`, payloadToServer)
                console.debug('addshoetype response', response && response.data)
                if (response.status === 200) {
                    ElMessage.success('颜色添加成功')
                    // Backend may return created shoe-type records (created: [{shoeTypeId,colorId,shoeId},...])
                    const created = response.data && response.data.created ? response.data.created : []
                    if (created.length) {
                        // merge created items into newOrderForm immediately
                        this.newOrderForm.orderShoeTypes = this.newOrderForm.orderShoeTypes || []
                        created.forEach((c) => {
                            // determine shoeRid from master table or dialogStore
                            const shoeRid = c.shoeRid || this.dialogStore.addColorForm.shoeRid || ''
                            const shoeIdFromC = c.shoeId || this.dialogStore.addColorForm.shoeId || shoeId
                            // skip duplicates
                            const exists = this.newOrderForm.orderShoeTypes.some((r) => String(r.colorId || r.color_id) === String(c.colorId) && String(r.shoeRid) === String(shoeRid))
                            if (exists) return
                            // try to find master shoe type metadata
                            const refreshedMaster = this.shoeTableData.find((s) => String(s.shoeId) === String(shoeIdFromC) || String(s.shoeRid) === String(shoeRid))
                            let foundType = null
                            if (refreshedMaster && Array.isArray(refreshedMaster.shoeTypeData)) {
                                foundType = refreshedMaster.shoeTypeData.find((t) => String(t.colorId || t.color_id || t.value) === String(c.colorId))
                            }
                            const newRow = {}
                            if (foundType) {
                                Object.assign(newRow, foundType)
                                newRow.shoeRid = refreshedMaster.shoeRid
                                newRow.shoeId = refreshedMaster.shoeId
                                newRow.shoeTypeId = foundType.shoeTypeId || foundType.id || c.shoeTypeId || null
                                newRow.colorId = foundType.colorId || foundType.color_id || c.colorId
                                newRow.colorName = foundType.colorName || foundType.label || ''
                            } else {
                                newRow.shoeRid = shoeRid
                                newRow.shoeId = shoeIdFromC
                                newRow.shoeTypeId = c.shoeTypeId || null
                                newRow.colorId = c.colorId
                                newRow.colorName = ''
                            }
                            newRow.customerShoeName = ''
                            newRow.customerColorName = ''
                            newRow.quantityMapping = {}
                            newRow.amountMapping = {}
                            newRow.orderShoeTypeBatchInfo = []
                            this.newOrderForm.orderShoeTypes.push(newRow)
                        })
                        // reconcile any optimistic rows with server-created ids
                        created.forEach((c) => {
                            const idx = this.newOrderForm.orderShoeTypes.findIndex(
                                (r) =>
                                    String(r.__pendingCreateColorId) === String(c.colorId) &&
                                    (String(r.shoeId) === String(c.shoeId || shoeId) ||
                                        String(r.shoeRid) === String(c.shoeRid || this.dialogStore.addColorForm.shoeRid))
                            )
                            if (idx !== -1) {
                                const row = this.newOrderForm.orderShoeTypes[idx]
                                const foundGlobal = (this.colorOptions || []).find(
                                    (co) => String(co.value) === String(c.colorId) || String(co.label) === String(c.colorId)
                                )
                                this.newOrderForm.orderShoeTypes.splice(
                                    idx,
                                    1,
                                    Object.assign({}, row, {
                                        shoeTypeId: c.shoeTypeId || row.shoeTypeId,
                                        colorId: c.colorId || row.colorId,
                                        colorName: row.colorName || (foundGlobal ? foundGlobal.label : '')
                                    })
                                )
                            }
                        })
                        // remap any remaining nulls
                        await this.remapOrderShoeTypesShoeTypeIds()
                        // If some created entries still lack shoeTypeId, try a targeted refresh+match
                        const missing = created.filter((c) => !c.shoeTypeId)
                        if (missing.length) {
                            console.debug('created entries missing shoeTypeId, refreshing master list to find IDs', missing)
                            try {
                                await this.getAllShoes()
                                // for each missing created entry, try to find the corresponding shoeType in master data
                                missing.forEach((c) => {
                                    const shoeRid = c.shoeRid || this.dialogStore.addColorForm.shoeRid || ''
                                    const shoeIdFromC = c.shoeId || this.dialogStore.addColorForm.shoeId || shoeId
                                    const master = this.shoeTableData.find((s) => String(s.shoeId) === String(shoeIdFromC) || String(s.shoeRid) === String(shoeRid))
                                    if (!master || !Array.isArray(master.shoeTypeData)) return
                                    const match = master.shoeTypeData.find((t) => String(t.colorId || t.color_id || t.value) === String(c.colorId) || String(t.colorName || t.label) === String(c.colorId))
                                    if (match) {
                                        // assign found id into any newOrderForm rows matching this shoe and color
                                        this.newOrderForm.orderShoeTypes.forEach((row) => {
                                            if ((String(row.colorId) === String(c.colorId) || String(row.colorName) === String(c.colorId) || String(row.colorName) === String(match.colorName)) && (String(row.shoeId) === String(master.shoeId) || String(row.shoeRid) === String(master.shoeRid))) {
                                                row.shoeTypeId = match.shoeTypeId || match.id
                                            }
                                        })
                                    }
                                })
                                // force refresh
                                        this.newOrderForm.orderShoeTypes = [...this.newOrderForm.orderShoeTypes]
                                        await this.$nextTick()
                                        // don't call getshoetype during add; mapping will be attempted at submit time
                            } catch (e) {
                                console.warn('targeted remap after addshoetype failed', e)
                            }
                        }
                        this.newOrderForm.flag = true
                    } else {
                        // fallback: refresh master shoe list and remap
                        await this.getAllShoes()
                        await this.remapOrderShoeTypesShoeTypeIds()
                    }
                    this.dialogStore.closeAddColorDialog()
                    this.dialogStore.resetAddColorForm()
                } else {
                    // rollback optimistic rows if server failed
                    try {
                        if (typeof pendingRows !== 'undefined' && pendingRows.length) {
                            this.newOrderForm.orderShoeTypes = (this.newOrderForm.orderShoeTypes || []).filter((r) => !r.__pendingCreateColorId)
                            this.newOrderForm.orderShoeTypes = [...this.newOrderForm.orderShoeTypes]
                        }
                    } catch (rollbackErr) {
                        console.warn('rollback pending rows failed', rollbackErr)
                    }
                    ElMessage.error('添加颜色失败')
                }
            } catch (e) {
                console.error('handleAddColorDialogSubmit failed', e)
                // rollback optimistic rows if request threw
                try {
                    if (typeof pendingRows !== 'undefined' && pendingRows.length) {
                        this.newOrderForm.orderShoeTypes = (this.newOrderForm.orderShoeTypes || []).filter((r) => !r.__pendingCreateColorId)
                        this.newOrderForm.orderShoeTypes = [...this.newOrderForm.orderShoeTypes]
                    }
                } catch (rollbackErr) {
                    console.warn('rollback pending rows failed', rollbackErr)
                }
                ElMessage.error('添加颜色失败')
            }
        },

        // Ensure each entry in newOrderForm.orderShoeTypes has a numeric shoeTypeId when possible
        async remapOrderShoeTypesShoeTypeIds() {
            try {
                if (!Array.isArray(this.newOrderForm.orderShoeTypes) || !Array.isArray(this.shoeTableData)) return
                // ensure we have fresh shoeTableData
                try {
                    await this.getAllShoes()
                } catch (e) {
                    console.warn('remapOrderShoeTypesShoeTypeIds: getAllShoes failed', e)
                }
                this.newOrderForm.orderShoeTypes.forEach((item) => {
                    const needsRemap = !item.shoeTypeId || (typeof item.shoeTypeId === 'string' && item.shoeTypeId.includes('_'))
                    if (!needsRemap) return
                    const master = this.shoeTableData.find((s) => String(s.shoeRid) === String(item.shoeRid) || String(s.shoeId) === String(item.shoeId))
                    if (!master || !Array.isArray(master.shoeTypeData)) return
                    const match = master.shoeTypeData.find((t) => {
                        const tVals = [t.colorId, t.color_id, t.value, t.colorName, t.label].map((v) => String(v))
                        const itemVals = [item.colorId, item.color_id, item.color, item.colorName, item.customerColorName].map((v) => String(v))
                        return tVals.some((tv) => itemVals.includes(tv)) || String(t.colorName || t.label) === String(item.colorName || item.customerColorName)
                    })
                    if (match) {
                        item.shoeTypeId = match.shoeTypeId || match.id
                    }
                })
                // force refresh
                this.newOrderForm.orderShoeTypes = [...this.newOrderForm.orderShoeTypes]
                await this.$nextTick()
            } catch (e) {
                console.warn('remapOrderShoeTypesShoeTypeIds failed', e)
            }
        },
        addNewShoe() {
            this.$confirm('确认添加新鞋型？', '提示', {
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                type: 'warning'
            }).then(async () => {
                const response = await axios.post(`${this.$apiBaseUrl}/shoemanage/addshoe`, this.dialogStore.shoeForm)
                if (response.status === 200) {
                    this.$message({
                        type: 'success',
                        message: '添加成功'
                    })
                    this.dialogStore.closeAddShoeDialog()
                    this.dialogStore.resetShoeForm()
                    this.shoeRidFilter = ''
                    await this.getAllShoes()
                }
            })
        },
        addShoeTypes() {
            this.dialogStore.shoeColorForm['colorId'] = this.dialogStore.shoeColorForm['shoeTypeColors']
            this.$confirm('确认添加颜色？', '提示', {
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                type: 'warning'
            }).then(async () => {
                // Prevent adding duplicate colors for the same shoe type: filter out colors that already exist
                const chosen = Array.isArray(this.dialogStore.shoeColorForm.shoeTypeColors) ? this.dialogStore.shoeColorForm.shoeTypeColors : []
                const shoeId = this.dialogStore.shoeColorForm.shoeId
                let existing = []
                try {
                    const shoe = this.shoeTableData.find((s) => s.shoeId == shoeId)
                    if (shoe && Array.isArray(shoe.shoeTypeData)) {
                        existing = shoe.shoeTypeData.map((t) => t.colorId || t.color_id || t.colorId)
                    }
                } catch (e) {
                    console.warn('addShoeTypes: failed to compute existing colors', e)
                }
                const existingStr = existing.map((x) => String(x))
                const toAdd = chosen.filter((c) => !existingStr.includes(String(c)))
                if (toAdd.length === 0) {
                    ElMessage.info('选中颜色已存在，不会重复添加')
                    this.dialogStore.closeAddShoeTypeDialog()
                    return
                }
                const payload = Object.assign({}, this.dialogStore.shoeColorForm, { colorId: toAdd, shoeTypeColors: toAdd })
                const response = await axios.post(`${this.$apiBaseUrl}/shoemanage/addshoetype`, payload)
                if (response.status === 200) {
                    this.$message({
                        type: 'success',
                        message: '上传成功'
                    })
                    this.dialogStore.closeAddShoeTypeDialog()
                    this.dialogStore.resetShoeColorForm()
                    await this.getAllShoes()
                }
            })
        },
        removeShoeType(row) {
            this.$confirm(`确认删除鞋型 ${row.shoeRid || row.shoeTypeId} 吗？`, '提示', {
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                type: 'warning'
            }).then(() => {
                this.newOrderForm.orderShoeTypes = this.newOrderForm.orderShoeTypes.filter((r) => r !== row)
                // if no shoe types left, clear flag
                if (this.newOrderForm.orderShoeTypes.length === 0) this.newOrderForm.flag = false
            })
        },
        openAddCustomerBatchDialog() {
            this.batchForm.customerId = this.newOrderForm.customerId
            this.batchForm.batchInfoTypeId = this.newOrderForm.batchInfoTypeId
            this.batchForm.packagingInfoLocale = this.newOrderForm.batchInfoTypeName
            this.dialogStore.openCustomerBatchDialog()
        },
        submitAddCustomerBatchForm() {
            this.$confirm('确认添加客户配码信息？', '提示', {
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                type: 'warning'
            })
                .then(async () => {
                    const result = await axios.post(`${this.$apiBaseUrl}/customer/addcustomerbatchinfo`, this.batchForm)
                })
                .then(async () => {
                    this.getCustomerBatchInfo(this.newOrderForm.customerId)
                    this.resetBatchForm()
                })
            this.dialogStore.closeCustomerBatchDialog()
        },
        deleteOrder(row) {
            this.$confirm('确认删除订单?', '提示', {
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                type: 'warning'
            })
                .then(async () => {
                    const result = await axios.delete(`${this.$apiBaseUrl}/order/deleteorder`, {
                        params: { orderId: row.orderDbId }
                    })
                    if (result.status === 200) {
                        ElMessage.success('订单删除成功')
                    } else {
                        ElMessage.error('订单删除失败')
                    }
                })
                .then(async () => {
                    this.initialStatusFilter()
                })
        },
        backPreviousStep() {
            this.dialogStore.orderCreationSecondInfoVis = false
            this.dialogStore.orderCreationInfoVis = true
        },
        closeAddBatchInfoDialog() {
            this.dialogStore.closeAddBatchInfoDialog()
            this.$refs.batchInfoDialog.batchTable?.clearSelection()
        },
        async orderCreationSecondStep() {
            if (this.newOrderForm.orderRId === '') {
                ElMessage.error('未输入订单号，不允许创建订单')
                return
            }
            const ridValidation = await this.validateOrderRidField()
            if (!ridValidation.valid) {
                if (ridValidation.message) {
                    ElMessage.error(ridValidation.message)
                }
                return
            }
            if (this.orderRidDuplicated) {
                ElMessage.error('订单号已存在，不允许创建订单')
                return
            }
            if (this.newOrderForm.customerName === '') {
                ElMessage.error('未选择客户，不允许创建订单')
                return
            }
            if (this.newOrderForm.customerBrand === '') {
                ElMessage.error('未选择客户商标，不允许创建订单')
                return
            }
            if (this.newOrderForm.batchInfoTypeName === '') {
                ElMessage.error('未选择配码种类，不允许创建订单')
                return
            }
            if (this.newOrderForm.orderStartDate === '') {
                ElMessage.error('未选择订单开始日期，不允许创建订单')
                return
            }
            if (this.newOrderForm.orderEndDate === '') {
                ElMessage.error('未选择订单结束日期，不允许创建订单')
                return
            }
            // If user did not explicitly select a shoe type but there's exactly one available,
            // auto-select it to simplify single-shoe workflows.
            if (!this.newOrderForm.orderShoeTypes || this.newOrderForm.orderShoeTypes.length === 0) {
                try {
                    if (Array.isArray(this.shoeTableData) && this.shoeTableData.length === 1) {
                        const shoe = this.shoeTableData[0]
                        if (Array.isArray(shoe.shoeTypeData) && shoe.shoeTypeData.length === 1) {
                            this.newOrderForm.orderShoeTypes = [Object.assign({}, shoe.shoeTypeData[0], { shoeRid: shoe.shoeRid })]
                        }
                    }
                } catch (e) {
                    console.warn('auto-select single shoeType failed', e)
                }
            }

            if (!this.newOrderForm.orderShoeTypes || this.newOrderForm.orderShoeTypes.length === 0) {
                ElMessage.error('请至少选择一种鞋型号')
                return
            }
            if (this.newOrderForm.supervisorId === '') {
                ElMessage.error('未选择下发经理，不允许创建订单')
                return
            }
            this.dialogStore.closeOrderCreationDialog()
            this.dialogStore.openOrderDetailDialog()
            // If the form was populated from a template (`flag === true`), preserve existing
            // `orderShoeTypeBatchInfo`, `quantityMapping`, and `amountMapping` so template selections
            // are not overwritten when progressing to the second step. Otherwise clear them.
            if (!this.newOrderForm.flag) {
                this.newOrderForm.orderShoeTypes.forEach((item) => {
                    item.orderShoeTypeBatchInfo = []
                    item.quantityMapping = {}
                    item.amountMapping = {}
                    item.customerColorName = ''
                    this.newOrderForm.customerShoeName[item.shoeRid] = ''
                })
            } else {
                // ensure mappings exist for template-loaded rows
                this.newOrderForm.orderShoeTypes.forEach((item) => {
                    item.quantityMapping = item.quantityMapping || {}
                    item.amountMapping = item.amountMapping || {}
                    item.orderShoeTypeBatchInfo = item.orderShoeTypeBatchInfo || []
                    this.newOrderForm.customerShoeName[item.shoeRid] = item.customerShoeName || ''
                })
            }
            this.getCustomerBatchInfo(this.newOrderForm.customerId)
        },
        updateAmountMapping(out_row, inner_row) {
            out_row.amountMapping[inner_row.packagingInfoId] = out_row.quantityMapping[inner_row.packagingInfoId] * inner_row.totalQuantityRatio
        },
        handleSelectionShoeType(selection, shoeId) {
            // only allow one shoe to be selected
            this.selectedShoeList = [...selection.map((item) => ({ ...item, shoeId }))]
            this.newOrderForm.orderShoeTypes = [...selection.map((item) => ({ ...item, shoeId }))]
        },
        handleSelectionBatchData(selection) {
            this.currentBatch = selection
            // console.log(this.currentBatch)
        },
        async getCustomerBatchInfo(customerId) {
            const response = await axios.get(`${this.$apiBaseUrl}/customer/getcustomerbatchinfo`, {
                params: {
                    customerid: customerId
                }
            })
            this.customerBatchData = response.data.filter((batch) => batch.batchInfoTypeId == this.newOrderForm.batchInfoTypeId)[0].batchInfoList
            this.customerDisplayBatchData = response.data.filter((batch) => batch.batchInfoTypeId == this.newOrderForm.batchInfoTypeId)[0].batchInfoList
        },
        async getAllCutomers() {
            const response = await axios.get(`${this.$apiBaseUrl}/customer/getcustomerdetails`)
            this.customerDetails = response.data
            this.customerNameList = [...new Set(response.data.map((item) => item.customerName))]
        },
        async getAllBatchTypes() {
            const response = await axios.get(`${this.$apiBaseUrl}/batchtype/getallbatchtypesbusiness`)
            this.batchTypes = response.data.batchDataTypes
            this.batchTypeNameList = [...new Set(this.batchTypes.map((item) => item.batchInfoTypeName))]
        },
        updateCustomerBrand() {
            this.customerBrandList = [...new Set(this.customerDetails.filter((item) => item.customerName == this.newOrderForm.customerName).map((item) => item.customerBrand))]
        },
        updateCustomerId() {
            this.newOrderForm.customerId = this.customerDetails
                .filter((item) => item.customerName == this.newOrderForm.customerName)
                .filter((item) => item.customerBrand == this.newOrderForm.customerBrand)[0].customerId
        },
        updateBatchType() {
            this.curBatchType = this.batchTypes.filter((item) => item.batchInfoTypeName == this.newOrderForm.batchInfoTypeName)[0]
            this.newOrderForm.batchInfoTypeId = this.curBatchType.batchInfoTypeId
        },
        filterBatchData() {
            if (!this.batchNameFilter) {
                this.customerDisplayBatchData = this.customerBatchData
            } else {
                this.customerFilteredBatchData = this.customerBatchData.filter((task) => {
                    const filteredData = task.packagingInfoName.includes(this.batchNameFilter)
                    return filteredData
                })
                this.customerDisplayBatchData = this.customerFilteredBatchData
            }
        },
        filterBatchDataWithSelection() {
            const selectedBatch = this.currentBatch
            if (!this.batchNameFilter) {
                this.customerDisplayBatchData = Array.from(new Set([...selectedBatch.concat(this.customerBatchData)]))
            } else {
                this.customerFilteredBatchData = this.customerBatchData.filter((task) => {
                    const filteredData = task.packagingInfoName.includes(this.batchNameFilter)
                    return filteredData
                })
                this.customerDisplayBatchData = Array.from(new Set([...selectedBatch.concat(this.customerFilteredBatchData)]))
            }
            this.$nextTick(() => {
                selectedBatch.forEach((item) => {
                    this.$refs.batchInfoSelectionTable.toggleRowSelection(
                        this.customerDisplayBatchData.find((row) => {
                            return row.packagingInfoId == item.packagingInfoId
                        }),
                        true
                    )
                })
            })
        },
        addShoeTypeBatchInfo() {
            this.newOrderForm.orderShoeTypes.find((row) => {
                return row.shoeTypeId == this.curShoeTypeId
            }).orderShoeTypeBatchInfo = this.currentBatch

            const curQuantityMapping = this.newOrderForm.orderShoeTypes.find((row) => {
                return row.shoeTypeId == this.curShoeTypeId
            }).quantityMapping
            const curAmountMapping = this.newOrderForm.orderShoeTypes.find((row) => {
                return row.shoeTypeId == this.curShoeTypeId
            }).amountMapping

            this.currentBatch.forEach((batch) => {
                {
                    curQuantityMapping[batch.packagingInfoId] = 0
                    curAmountMapping[batch.packagingInfoId] = 0
                }
            })
            // this.newOrderForm.orderShoeTypes.find(row => {
            //     return row.shoeTypeId == this.curShoeTypeId
            // }).unitQuantityInPair = 0

            // this.newOrderForm.orderShoeTypes.find(row => {
            //     return row.shoeTypeId == this.curShoeTypeId
            // }).
            this.newOrderForm.flag = true
            this.dialogStore.closeAddBatchInfoDialog()
        },
        expandOpen(row, expand) {
            return
            // console.log(this.expandedRowKeys)
            // this.expandedRowKeys.push(row.shoeTypeId)
            // row.batchQuantityMapping = row.orderShoeTypeBatchInfo.map((batchInfo) => { return batchInfo.packagingInfoId:batchInfo.unitQuantityInPair})Id})
        },
        closeAddBatchInfodialog() {
            return
        },
        async getAllOrders() {
            // const response = await axios.get(`${this.$apiBaseUrl}/order/getallorders`)

            if (this.role == 21) {
                const response = await axios.get(`${this.$apiBaseUrl}/order/getbusinessdisplayorderbyuser`, {
                    currentStaffId: staffId
                })
                this.orderStore.setOrders(response.data)
            } else if (this.role == 4) {
                const response = await axios.get(`${this.$apiBaseUrl}/order/getallorders`)
                this.orderStore.setOrders(response.data)
            }
        },
        // async getAllOrderStatus() {
        //     const response = await axios.get(`${this.$apiBaseUrl}/order/getallorderstatus`)
        //     this.orderStatusList = response.data
        // },
        async getOrderOrderShoe(orderRid) {
            const response = await axios.get(`${this.$apiBaseUrl}/order/getordershoeinfo`, {
                params: {
                    orderrid: orderRid
                }
            })
            this.orderShoePreviewData = response.data
        },
        async getAllShoes() {
            let params = {
                page: this.currentOrderCreatePage,
                pageSize: this.orderCreatePageSize,
                shoerid: this.shoeRidFilter,
                customerName: this.customerNameFilter,
                available: 1
            }
            const response = await axios.get(`${this.$apiBaseUrl}/shoe/getallshoesnew`, { params })
            this.shoeTableData = response.data.shoeTable
            this.shoeTotalItems = response.data.total
        },
        async refreshColorOptions() {
            try {
                const resp = await axios.get(`${this.$apiBaseUrl}/general/allcolors`)
                this.colorOptions = resp.data
            } catch (e) {
                console.warn('refreshColorOptions failed', e)
            }
        },
        async fetchShoeByRid(shoeRid) {
            if (!shoeRid) return null
            const params = {
                page: 1,
                pageSize: 1,
                shoerid: shoeRid,
                available: 1
            }
            const response = await axios.get(`${this.$apiBaseUrl}/shoe/getallshoesnew`, { params })
            return Array.isArray(response.data?.shoeTable) ? response.data.shoeTable[0] : null
        },
        async getOrderDocInfo(orderRid) {
            const response = await axios.get(`${this.$apiBaseUrl}/order/getorderdocinfo`, {
                params: {
                    orderrid: orderRid
                }
            })
            this.orderDocData = response.data
        },
        async submitUpload() {
            try {
                const loadingInstance = this.$loading({
                    lock: true,
                    text: '等待中，请稍后...',
                    background: 'rgba(0, 0, 0, 0.7)'
                })
                // Manually submit the file without reopening the dialog
                await this.$refs.uploadDoc.submit().then(() => {
                    loadingInstance.close()
                })
            } catch (error) {
                console.error('Upload error:', error)
                ElMessage.error('上传失败')
            }
        },
        filterTemplateOptions() {
            if (this.templateFilter != '') {
                this.templateCustomerBrandMatch = this.templateData.filter((task) => {
                    const templateCustomerBrandMatch = task.customerBrand.toLowerCase().includes(this.templateFilter.toLowerCase())
                    return templateCustomerBrandMatch
                })
                this.templateCustomerNameMatch = this.templateData.filter((task) => {
                    const templateCustomerNameMatch = task.customerName.toLowerCase().includes(this.templateFilter.toLowerCase())
                    return templateCustomerNameMatch
                })
                this.templateDisplayData = this.templateCustomerBrandMatch.concat(this.templateCustomerNameMatch)
            } else {
                this.templateDisplayData = this.templateData
            }
        },
        handleUploadSuccess(response, file) {
            // Handle the successful response
            this.tempFileName = response.tempFileName
            this.uploadData = response.data
            console.log('Upload successful:', response)
        },
        async handleUploadError(error, file) {
            // Handle any errors that occurred during the upload
            console.error('Upload error:', error)
            ElMessage.error('上传失败')
        },
        handleUploadDocSuccess(response, file) {
            // Handle the successful response
            console.log('Upload successful:', response)
            ElMessage.success('上传成功')
            this.getOrderDocInfo(this.orderData.orderRid)
            this.isSubmitDocVis = false
        },
        handleUploadDocError(error, file) {
            // Handle any errors that occurred during the upload
            console.error('Upload error:', error)
            ElMessage.error('上传失败')
            this.fileList = []
            this.getOrderDocInfo(this.orderData.orderRid)
            this.isSubmitDocVis = false
        },
        downloadDoc(type) {
            window.open(`${this.$apiBaseUrl}/orderimport/downloadorderdoc?orderrid=${this.orderData.orderRid}&filetype=${type}`)
        },
        mergeCells({ row, column, rowIndex, columnIndex }) {
            const mergeColumns = ['inheritId', 'customerId', 'colorCN', 'colorEN']

            if (mergeColumns.includes(column.property)) {
                // Check if the previous row has the same value for the column
                if (rowIndex > 0 && row[column.property] === this.uploadData[rowIndex - 1][column.property]) {
                    return {
                        rowspan: 0, // Hide the current cell
                        colspan: 0
                    }
                } else {
                    // Count how many consecutive rows have the same value
                    let rowspan = 1
                    for (let i = rowIndex + 1; i < this.uploadData.length; i++) {
                        if (this.uploadData[i][column.property] === row[column.property]) {
                            rowspan++
                        } else {
                            break
                        }
                    }
                    return {
                        rowspan: rowspan, // Merge cells
                        colspan: 1
                    }
                }
            }
        },
        mergeCellsPreview({ row, column, rowIndex, columnIndex }) {
            const mergeColumns = ['inheritId', 'customerId', 'colorCN', 'colorEN', 'status']

            // Only merge 'status' when both 'status' and 'inheritId' are the same
            if (mergeColumns.includes(column.property)) {
                if (column.property === 'status') {
                    // For 'status', also check 'inheritId' to ensure they match before merging
                    if (
                        rowIndex > 0 &&
                        row[column.property] === this.orderShoePreviewData[rowIndex - 1][column.property] &&
                        row['inheritId'] === this.orderShoePreviewData[rowIndex - 1]['inheritId']
                    ) {
                        return {
                            rowspan: 0, // Hide the current cell
                            colspan: 0
                        }
                    } else {
                        let rowspan = 1
                        for (let i = rowIndex + 1; i < this.orderShoePreviewData.length; i++) {
                            if (this.orderShoePreviewData[i][column.property] === row[column.property] && this.orderShoePreviewData[i]['inheritId'] === row['inheritId']) {
                                rowspan++
                            } else {
                                break
                            }
                        }
                        return {
                            rowspan: rowspan, // Merge cells
                            colspan: 1
                        }
                    }
                } else {
                    // Default merging logic for other columns
                    if (rowIndex > 0 && row[column.property] === this.orderShoePreviewData[rowIndex - 1][column.property]) {
                        return {
                            rowspan: 0, // Hide the current cell
                            colspan: 0
                        }
                    } else {
                        let rowspan = 1
                        for (let i = rowIndex + 1; i < this.orderShoePreviewData.length; i++) {
                            if (this.orderShoePreviewData[i][column.property] === row[column.property]) {
                                rowspan++
                            } else {
                                break
                            }
                        }
                        return {
                            rowspan: rowspan, // Merge cells
                            colspan: 1
                        }
                    }
                }
            }
        },
        handleDialogClose() {
            console.log('TODO handle dialog close in OrderManagement.Vue')
        },
        async closeClearUploadData() {
            this.isImportVis = false
            this.$refs.upload.clearFiles()
            this.uploadData = []
            this.updatekey++
            await axios.delete(`${this.$apiBaseUrl}/orderimport/deleteuploadtempfile`, {
                params: {
                    fileName: this.tempFileName
                }
            })
        },
        confirmImportFile() {
            console.log('confirm import file')
            if (this.uploadData.length === 0) {
                this.$message({
                    type: 'error',
                    message: '请先上传文件'
                })
                return
            }
            this.orderInfoVis = true
        },
        confirmImportInfo() {
            console.log('confirm import info')

            this.$confirm('确认导入订单信息？', '提示', {
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
                    const response = await axios.post(`${this.$apiBaseUrl}/orderimport/confirmimportorder`, {
                        fileName: this.tempFileName,
                        orderInfo: this.orderForm
                    })
                    loadingInstance.close()
                    if (response.status === 200) {
                        this.$message({
                            type: 'success',
                            message: '导入成功'
                        })
                        this.orderInfoVis = false
                        this.orderForm = {
                            orderRId: '',
                            customerId: null,
                            orderStartDate: '',
                            orderEndDate: '',
                            status: '',
                            salesman: ''
                        }
                        this.closeClearUploadData()
                        this.getAllOrders()
                    } else {
                        this.$message({
                            type: 'error',
                            message: '导入失败'
                        })
                    }
                })
                .catch(() => {
                    this.$message({
                        type: 'info',
                        message: '已取消导入'
                    })
                })
        },
        async submitNewOrder() {
            if (this.newOrderForm.flag === false) {
                ElMessage.error('请添加鞋型配码')
                return
            }
            const ridValidation = await this.validateOrderRidField()
            if (!ridValidation.valid) {
                if (ridValidation.message) {
                    ElMessage.error(ridValidation.message)
                }
                return
            }
            if (this.orderRidDuplicated) {
                ElMessage.error('订单号已存在，不允许创建订单')
                return
            }

            ElMessageBox.alert('请检查配码单位数量是否已填写', '', {
                confirmButtonText: '已填写',
                showCancelButton: true,
                callback: (action) => {
                    if (action === 'confirm') {
                        this.$confirm('确认导入订单信息？', '提示', {
                            confirmButtonText: '确定',
                            cancelButtonText: '取消',
                            type: 'warning'
                        }).then(async () => {
                            try {
                                const loadingInstance = this.$loading({
                                    lock: true,
                                    text: '等待中，请稍后...',
                                    background: 'rgba(0, 0, 0, 0.7)'
                                })
                                loadingInstance.close()
                                // Ensure shoeTypeId values are valid before submit
                                try {
                                    await this.getAllShoes()
                                } catch (e) {
                                    console.warn('submitNewOrder: getAllShoes failed', e)
                                }
                                let missingMappings = []
                                if (Array.isArray(this.newOrderForm.orderShoeTypes)) {
                                    this.newOrderForm.orderShoeTypes.forEach((item) => {
                                        const needsRemap = !item.shoeTypeId || (typeof item.shoeTypeId === 'string' && item.shoeTypeId.includes('_'))
                                        if (needsRemap) missingMappings.push(item)
                                    })
                                }

                                // Try to resolve missing mappings by querying backend by shoeId+colorId
                                if (missingMappings.length) {
                                    await Promise.all(missingMappings.map(async (item) => {
                                        const qShoeId = item.shoeId || item.shoeRid || this.dialogStore.addColorForm.shoeId
                                        const qColorId = item.colorId || item.color_id || item.colorName || item.color || item.customerColorName
                                        if (!qShoeId || qColorId == null) return
                                        try {
                                            console.debug('submitNewOrder: calling getshoetype for', { qShoeId, qColorId })
                                            const resp = await axios.get(`${this.$apiBaseUrl}/shoemanage/getshoetype`, { params: { shoeId: qShoeId, colorId: qColorId } })
                                            console.debug('submitNewOrder: getshoetype resp', resp && resp.data)
                                            if (resp && resp.data && (resp.data.shoeTypeId || resp.data.shoeTypeId === 0)) {
                                                item.shoeTypeId = resp.data.shoeTypeId
                                            }
                                        } catch (e) {
                                            console.warn('submitNewOrder: getshoetype failed for', { qShoeId, qColorId }, e)
                                        }
                                    }))
                                    // recompute missingMappings after attempts
                                    missingMappings = []
                                    this.newOrderForm.orderShoeTypes.forEach((item) => {
                                        const needsRemap = !item.shoeTypeId || (typeof item.shoeTypeId === 'string' && item.shoeTypeId.includes('_'))
                                        if (needsRemap) missingMappings.push(item)
                                    })
                                }

                                if (missingMappings.length) {
                                    // Attempt to make missingMappings serializable for logging (strip proxies)
                                    let serializable = []
                                    try {
                                        serializable = missingMappings.map((m) => JSON.parse(JSON.stringify(m)))
                                    } catch (e) {
                                        serializable = missingMappings.map((m) => ({ shoeRid: m.shoeRid || m.shoeId || null, colorId: m.colorId || m.color_id || null, colorName: m.colorName || m.customerColorName || null }))
                                    }
                                    console.error('submitNewOrder: missing shoeTypeId mappings for items (serializable):', serializable)
                                    // show user-friendly list of failing rows
                                    const summary = serializable.map((s) => `${s.shoeRid || s.shoeId || ''} / ${s.colorName || s.colorId || ''}`).join(', ')
                                    ElMessage.error(`部分鞋型/颜色未映射：${summary}。请刷新鞋款列表并确认颜色已添加后重试`)
                                    return
                                }

                                const res = await axios.post(`${this.$apiBaseUrl}/ordercreate/createneworder`, {
                                    orderInfo: this.newOrderForm
                                })

                                ElMessage.success('创建订单成功')
                                loadingInstance.close()
                                this.dialogStore.closeOrderDetailDialog()
                                this.newOrderForm = {
                                    orderRId: '',
                                    orderCid: '',
                                    customerName: '',
                                    customerBrand: '',
                                    customerId: null,
                                    batchInfoTypeName: '',
                                    batchInfoTypeId: '',
                                    orderStartDate: '',
                                    orderEndDate: '',
                                    status: '',
                                    orderType: 'N',
                                    salesman: '',
                                    orderShoeTypes: [],
                                    batchInfoQuantity: [],
                                    customerShoeName: {},
                                    flag: false,
                                    salesmanId: '',
                                    sourceOrderRid: null,
                                    sourceOrderId: null
                                }
                                this.orderRidDuplicated = false
                                this.getAllOrders()
                                this.openOrderDetail(res.data.newOrderId)
                            } catch (error) {
                                console.error('Upload error:', error)
                                ElMessage.error(error.data.message)
                            }
                        })
                    }
                }
            })
        },
        openOrderDetail(orderId) {
            console.log(orderId)
            let url = ''
            if (this.userRole == 4) {
                url = `${window.location.origin}/business/businessorderdetail/orderid=${orderId}/admin`
            } else if (this.userRole == 21) {
                url = `${window.location.origin}/business/businessorderdetail/orderid=${orderId}/clerk`
            }
            window.open(url, '_blank')
        },
        switchRadio(value) {
            this.orderStore.switchRadio(value)
        },
        async switchSortLogic(value) {
            console.log(value)
            if (value === 'asc') {
                if (!this.buttonFlag) {
                    const response = await axios.get(`${this.$apiBaseUrl}/order/getbusinessdisplayorderbyuser`, {
                        currentStaffId: this.staffId
                    })
                    this.orderStore.setOrders(response.data)
                } else {
                    const response = await axios.get(`${this.$apiBaseUrl}/order/getallorders`)
                    this.orderStore.setOrders(response.data)
                }
            } else if (value === 'desc') {
                if (!this.buttonFlag) {
                    const response = await axios.get(`${this.$apiBaseUrl}/order/getbusinessdisplayorderbyuser`, {
                        currentStaffId: this.staffId
                    })
                    this.orderStore.setOrders(response.data)
                    console.log(this.orderStore.unfilteredData)
                } else {
                    const response = await axios.get(`${this.$apiBaseUrl}/order/getallorders?descSymbol=1`)
                    this.orderStore.setOrders(response.data)
                }
            }
        },
        async validateOrderRid(rule, value, callback) {
            if (!value) {
                this.orderRidDuplicated = false
                callback()
                return
            }
            try {
                const response = await axios.get(`${this.$apiBaseUrl}/order/checkorderridexists`, {
                    params: {
                        pendingRid: value
                    }
                })
                const exists = response.data.exists === true
                this.orderRidDuplicated = exists

                if (exists) {
                    callback(new Error(response.data.result || '订单号已存在'))
                } else {
                    callback()
                }
            } catch (error) {
                console.error('Error checking order rid:', error)
                callback(new Error('订单号校验失败，请稍后重试'))
            }
        },
        async validateOrderRidField() {
            if (!this.$refs.orderCreationForm) {
                return { valid: false, message: '' }
            }
            return new Promise((resolve) => {
                this.$refs.orderCreationForm.validateField('orderRId', (errorMessage) => {
                    const message = typeof errorMessage === 'string' ? errorMessage : errorMessage?.message || ''
                    const noError =
                        !errorMessage || (Array.isArray(errorMessage) && errorMessage.length === 0) || errorMessage === true
                    resolve({ valid: noError, message })
                })
            })
        },
        async checkOrderRidExists() {
            const result = await this.validateOrderRidField()
            return result.valid
        },
        async handleOrderStatusChange(value) {
            let response
            if (value === '全部订单') {
                response = await axios.get(`${this.$apiBaseUrl}/order/getallorders`)
            } else if (value === '我审批的订单') {
                response = await axios.get(`${this.$apiBaseUrl}/order/getbusinessdisplayorderbyuser`, {
                    params: {
                        currentStaffId: this.staffId,
                        filterStatus: 0
                    }
                })
            } else if (value === '我发起的订单') {
                response = await axios.get(`${this.$apiBaseUrl}/order/getbusinessdisplayorderbyuser`, {
                    params: {
                        currentStaffId: this.staffId,
                        filterStatus: 1
                    }
                })
            }

            if (response && response.data) {
                this.orderStore.setOrders(response.data)

                this.orderStore.radio = 'all'
                this.sortRadio = 'asc'
            }
        },
        openReUploadImageDialog(row) {
            this.dialogStore.openReUploadImageDialog()
            this.currentShoeImageId = row.shoeRid
            this.currentShoeColor = row.colorName
            this.currentShoeColorId = row.colorId
            this.currentImageRow = row
        },
        onFileChange(event) {
            const file = event.target.files[0]
            if (!file) return

            const reader = new FileReader()
            reader.onload = () => {
                this.imageUrl = reader.result
            }
            reader.readAsDataURL(file)
        },
        async uploadCroppedImage() {
            const dialogRef = this.$refs.reUploadImageDialog
            if (!dialogRef || typeof dialogRef.getResult !== 'function') {
                ElMessage.error('裁剪组件未就绪，请稍后重试')
                return
            }

            const result = dialogRef.getResult()
            if (!result || !result.canvas) {
                ElMessage.error('未获取到裁剪结果')
                return
            }

            const canvas = result.canvas

            await new Promise((resolve, reject) => {
                canvas.toBlob(async (blob) => {
                    if (!blob) {
                        reject(new Error('生成图片失败'))
                        return
                    }

                    const formData = new FormData()
                    formData.append('file', blob, 'cropped.jpg')
                    formData.append('shoeRid', this.currentShoeImageId)
                    formData.append('shoeColorId', this.currentShoeColorId)
                    formData.append('shoeColorName', this.currentShoeColor)

                    try {
                        await axios.post(`${this.$apiBaseUrl}/shoemanage/uploadshoeimage`, formData)
                        this.$message.success('上传成功')

                        this.dialogStore.closeReUploadImageDialog()
                        this.imageUrl = null

                        this.refreshRowImage(this.currentShoeImageId, this.currentShoeColorId)
                        resolve()
                    } catch (e) {
                        console.error(e)
                        this.$message.error('上传失败')
                        reject(e)
                    }
                }, 'image/jpeg')
            })
        },

        async refreshRowImage(shoeId, shoeTypeId) {
            console.log(shoeId, shoeTypeId)
            const shoe = this.shoeTableData.find((s) => s.shoeRid === shoeId)
            if (!shoe) return

            const shoeType = shoe.shoeTypeData.find((t) => t.shoeTypeId === shoeTypeId)
            if (!shoeType) return

            const baseUrl = shoeType.shoeImageUrl.split('?')[0]
            const newUrl = `${baseUrl}?t=${Date.now()}`
            shoeType.shoeImageUrl = newUrl
        },
        async getAllBatchTemplates() {
            try {
                const response = await axios.get(`${this.$apiBaseUrl}/ordercreate/getallbatchtemplates`, {
                    params: {
                        customerName: this.newOrderForm.customerName,
                        customerBrand: this.newOrderForm.customerBrand
                    }
                })
                this.batchTemplateData = response.data
                this.batchTemplateDisplayData = response.data
            } catch (error) {
                console.error('Error fetching batch templates:', error)
                ElMessage.error('加载模板失败')
            }
        },
        async openLoadBatchTemplateDialog(row) {
            await this.getAllBatchTemplates()
            this.curShoeTypeId = row.shoeTypeId
            this.dialogStore.openBatchTemplateDialog()
        },
        openSaveBatchTemplateDialog() {
            this.dialogStore.openBatchTemplateSaveDialog()
            this.batchTemplateName = ''
            this.batchTemplateForm = {
                templateName: this.batchTemplateName,
                customerName: this.newOrderForm.customerName,
                customerBrand: this.newOrderForm.customerBrand,
                templateDescription: '',
                templateDetail: this.currentBatch
            }
            console.log('Opening save batch template dialog with data:', this.batchTemplateForm)
        },
        async saveBatchTemplate() {
            if (this.batchTemplateForm.templateName === '') {
                ElMessage.error('请填写模板名称')
                return
            }
            const templateData = {
                templateName: this.batchTemplateForm.templateName,
                customerName: this.batchTemplateForm.customerName,
                customerBrand: this.batchTemplateForm.customerBrand,
                templateDescription: this.batchTemplateForm.templateDescription,
                templateDetail: this.batchTemplateForm.templateDetail
            }
            try {
                const response = await axios.post(`${this.$apiBaseUrl}/ordercreate/savebatchtemplate`, templateData)
                if (response.status === 200) {
                    ElMessage.success('模板保存成功')
                    this.dialogStore.closeBatchTemplateSaveDialog()
                    this.batchTemplateForm = {}
                    this.batchTemplateName = ''
                } else {
                    ElMessage.error('模板保存失败')
                }
            } catch (error) {
                console.error('Error saving batch template:', error)
                ElMessage.error('模板保存失败')
            }

            console.log('Saving batch template:', templateData)
        },
        handleSelectionBatchTemplate(selection) {
            const tableRef = this.$refs.batchTemplateSelectionTable

            if (selection.length > 1) {
                // 只保留最新选择的一项
                const latest = selection[selection.length - 1]

                // 清除所有选择
                tableRef.clearSelection()

                // 只选中最新的
                tableRef.toggleRowSelection(latest, true)

                this.selectedBatchTemplate = latest
            } else if (selection.length === 1) {
                this.selectedBatchTemplate = selection[0]
            } else {
                this.selectedBatchTemplate = {}
            }
        },
        confirmLoadBatchTemplate() {
            if (!this.selectedBatchTemplate) {
                ElMessage.error('请选择一个模板')
                return
            }
            this.newOrderForm.orderShoeTypes.find((row) => {
                return row.shoeTypeId == this.curShoeTypeId
            }).orderShoeTypeBatchInfo = this.selectedBatchTemplate.batchInfoData

            const curQuantityMapping = this.newOrderForm.orderShoeTypes.find((row) => {
                return row.shoeTypeId == this.curShoeTypeId
            }).quantityMapping
            const curAmountMapping = this.newOrderForm.orderShoeTypes.find((row) => {
                return row.shoeTypeId == this.curShoeTypeId
            }).amountMapping

            this.selectedBatchTemplate.batchInfoData.forEach((batch) => {
                {
                    curQuantityMapping[batch.packagingInfoId] = 0
                    curAmountMapping[batch.packagingInfoId] = 0
                }
            })
            this.currentBatch = this.selectedBatchTemplate.batchInfoData
            this.$nextTick(() => {
                const tableRef = this.$refs.batchInfoSelectionTable
                if (!tableRef) return

                tableRef.clearSelection()

                this.customerDisplayBatchData.forEach((row) => {
                    const match = this.currentBatch.find((batch) => batch.packagingInfoId === row.packagingInfoId)
                    if (match) {
                        tableRef.toggleRowSelection(row, true)
                    }
                })
            })
            this.newOrderForm.flag = true

            this.dialogStore.closeBatchTemplateDialog()
        },
        async deleteBatchTemplateDialog(row) {
            this.$confirm(`确认删除模板 "${row.templateName}"?`, '提示', {
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                type: 'warning'
            })
                .then(async () => {
                    try {
                        const response = await axios.post(`${this.$apiBaseUrl}/ordercreate/deletebatchtemplate`, {
                            batchInfoTemplateId: row.batchInfoTemplateId
                        })
                        if (response.status === 200) {
                            ElMessage.success('模板删除成功')
                            await this.getAllBatchTemplates()
                        }
                    } catch (error) {
                        console.error('Error deleting batch template:', error)
                        ElMessage.error('模板删除失败')
                    }
                })
                .catch(() => {
                    this.$message({
                        type: 'info',
                        message: '已取消删除'
                    })
                })
        },
        orderRowDbClick(row) {
            this.openOrderDetail(row.orderDbId)
        }
    },
    watch: {
        async 'dialogStore.orderCreationInfoVis'(newValue) {
            if (newValue) {
                const response = await axios.get(`${this.$apiBaseUrl}/general/getbusinessmanagers`)
                this.departmentNameList = response.data
            }
        }
    }
}
</script>

<style scoped>
/* Clean base style */
::v-deep(.persistent-shadow-row > td) {
    border-top: 5px solid #dcdfe6;
    border-bottom: 5px solid #dcdfe6;
    background-color: #fff;
    padding: 12px 16px;
}

/* Left rounded corners */
::v-deep(.persistent-shadow-row > td:first-child) {
    border-left: 5px solid #dcdfe6;
    border-top-left-radius: 8px;
    border-bottom-left-radius: 8px;
}

/* Right rounded corners */
::v-deep(.persistent-shadow-row > td:last-child) {
    border-right: 5px solid #dcdfe6;
    border-top-right-radius: 8px;
    border-bottom-right-radius: 8px;
}
</style>
