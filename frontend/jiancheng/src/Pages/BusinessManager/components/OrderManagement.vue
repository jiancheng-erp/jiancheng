<template>
    <el-row :gutter="20">
        <el-col :span="24" :offset="0" style="font-size: xx-large; text-align: center">订单管理</el-col>
    </el-row>
    <el-row :gutter="10" style="margin-top: 20px">
        <el-col :span="4" :offset="0">
            <el-button size="default" type="primary" @click="openCreateOrderDialog">创建订单</el-button>
            <el-button size="default" type="primary" @click="showTemplate"> 模板 </el-button>
            <el-select
                v-model="orderStore.selectedOrderStatus"
                placeholder="请选择订单类型"
                size="default"
                :disabled="role === '21'"
                @change="handleOrderStatusChange"
                style="width: 200px; width: 150px"
            >
                <el-option v-for="item in orderStore.orderStatusOption" :key="item" :label="item" :value="item" />
            </el-select>
        </el-col>
        <el-col :span="4" :offset="1"
            ><el-input v-model="orderStore.orderRidFilter" placeholder="订单号筛选" size="default" :suffix-icon="'el-icon-search'" clearable @input="orderStore.filterDisplayOrder"></el-input>
        </el-col>

        <el-col :span="4"
            ><el-input v-model="orderStore.orderCidFilter" placeholder="客户订单号筛选" size="default" :suffix-icon="'el-icon-search'" clearable @input="orderStore.filterDisplayOrder"></el-input>
        </el-col>
        <el-col :span="4"
            ><el-input
                v-model="orderStore.orderCustomerNameFilter"
                placeholder="客户名称筛选"
                size="default"
                :suffix-icon="'el-icon-search'"
                clearable
                @input="orderStore.filterDisplayOrder"
            ></el-input>
        </el-col>
        <el-col :span="4">
            <el-date-picker
                v-model="orderStore.orderStartDateFilter"
                type="daterange"
                unlink-panels
                range-separator="至"
                start-placeholder="订单开始日期起"
                end-placeholder="订单开始日期终"
                :shortcuts="shortcuts"
                size="default"
                @change="orderStore.filterDisplayOrder"
            />
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
            <el-input
                v-model="orderStore.customerProductNameFilter"
                placeholder="客户型号筛选"
                size="default"
                :suffix-icon="'el-icon-search'"
                clearable
                @input="orderStore.filterDisplayOrder"
            ></el-input>
        </el-col>
        <el-col :span="4">
            <el-input v-model="orderStore.shoeRIdSearch" placeholder="工厂型号筛选" size="default" :suffix-icon="'el-icon-search'" clearable @input="orderStore.filterDisplayOrder"></el-input>
        </el-col>
        <el-col :span="4"
            ><el-input
                v-model="orderStore.orderCustomerBrandFilter"
                placeholder="客户商标筛选"
                size="default"
                :suffix-icon="'el-icon-search'"
                clearable
                @input="orderStore.filterDisplayOrder"
            ></el-input>
        </el-col>

        <el-col :span="4">
            <el-date-picker
                v-model="orderStore.orderEndDateFilter"
                type="daterange"
                unlink-panels
                range-separator="至"
                start-placeholder="订单结束日期起"
                end-placeholder="订单结束日期终"
                :shortcuts="shortcuts"
                size="default"
                @change="orderStore.filterDisplayOrder"
            />
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
        <el-table :data="orderStore.paginatedDisplayData" border stripe @row-dblclick="orderRowDbClick" style="height: 60vh">
            <el-table-column prop="orderRid" label="订单号" sortable />
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
                        <el-button type="primary" size="default" @click="openOrderDetail(scope.row.orderDbId)">查看订单详情</el-button>
                        <el-button v-if="scope.row.orderStatusVal < 9 && this.userRole == 4" type="danger" size="default" @click="deleteOrder(scope.row)">删除订单</el-button>
                    </el-button-group>
                </template>
            </el-table-column>
        </el-table>
        <el-pagination
            :current-page="orderStore.currentPage"
            :page-size="orderStore.pageSize"
            :total="orderStore.totalItems"
            @current-change="orderStore.handlePageChange"
            layout="total,prev,pager,next,jumper"
            style="margin-top: 20px"
        ></el-pagination>
    </el-row>

    <el-dialog title="创建订单鞋型填写" v-model="dialogStore.orderCreationInfoVis" width="100%" fullscreen :close-on-click-modal="false">
        <el-form :model="newOrderForm" label-width="120px" :inline="false" size="default">
            <el-form-item
                label="请输入订单号"
                prop="orderRId"
                :rules="[
                    {
                        required: true,
                        message: '订单号不能为空',
                        trigger: ['blur']
                    }
                ]"
            >
                <el-input @change="checkOrderRidExists" v-model="newOrderForm.orderRId"></el-input>
            </el-form-item>
            <el-form-item label="客户订单号">
                <el-input v-model="newOrderForm.orderCid"></el-input>
            </el-form-item>
            <el-form-item
                label="请选择客户"
                prop="customerName"
                :rules="[
                    {
                        required: true,
                        message: '客户不能为空',
                        trigger: ['blur']
                    }
                ]"
            >
                <el-select v-model="newOrderForm.customerName" filterable placeholder="请选择客户" @change="updateCustomerBrand">
                    <el-option v-for="item in this.customerNameList" :key="item" :label="item" :value="item"></el-option>
                </el-select>
            </el-form-item>
            <el-form-item
                label="请选择客户商标"
                prop="customerBrand"
                :rules="[
                    {
                        required: true,
                        message: '客户商标不能为空',
                        trigger: ['blur']
                    }
                ]"
            >
                <el-select v-model="newOrderForm.customerBrand" filterable placeholder="请选择商标" @change="updateCustomerId">
                    <el-option v-for="item in this.customerBrandList" :key="item" :label="item" :value="item"></el-option>
                </el-select>
            </el-form-item>
            <el-form-item
                label="请选择配码种类"
                prop="batchInfoTypeName"
                :rules="[
                    {
                        required: true,
                        message: '请选择配码种类',
                        trigger: ['blur']
                    }
                ]"
            >
                <el-select v-model="newOrderForm.batchInfoTypeName" filterable placeholder="请选择种类" @change="updateBatchType">
                    <el-option v-for="item in this.batchTypes" :key="item.batchInfoTypeId" :label="item.batchInfoTypeName" :value="item.batchInfoTypeName"> </el-option>
                </el-select>
            </el-form-item>
            <el-form-item
                label="订单开始日期"
                ref="startdatepicker"
                prop="orderStartDate"
                :rules="[
                    {
                        required: true,
                        message: '请选择订单开始日期',
                        trigger: ['blur']
                    }
                ]"
            >
                <el-date-picker v-model="newOrderForm.orderStartDate" type="date" placeholder="选择日期" value-format="YYYY-MM-DD"></el-date-picker>
            </el-form-item>
            <el-form-item
                label="订单结束日期"
                prop="orderEndDate"
                :rules="[
                    {
                        required: true,
                        message: '请选择订单结束日期',
                        trigger: ['blur']
                    }
                ]"
            >
                <el-date-picker v-model="newOrderForm.orderEndDate" type="date" placeholder="选择日期" value-format="YYYY-MM-DD"></el-date-picker>
            </el-form-item>
            <el-form-item
                label="业务员"
                prop="salesman"
                :rules="[
                    {
                        required: true,
                        message: '请选择业务员',
                        trigger: ['blur']
                    }
                ]"
            >
                <el-input v-model="newOrderForm.salesman" disabled></el-input>
            </el-form-item>

            <el-form-item
                label="选择审批经理"
                prop="supervisorId"
                :rules="[
                    {
                        required: true,
                        message: '内容不能为空',
                        trigger: ['blur']
                    }
                ]"
            >
                <el-select v-model="newOrderForm.supervisorId" filterable placeholder="请选择下发经理">
                    <el-option v-for="item in this.departmentNameList" :key="item.staffId" :label="item.staffName" :value="item.staffId"></el-option>
                </el-select>
            </el-form-item>

            <el-row :gutter="20">
                <el-col :span="4" :offset="0" style="white-space: nowrap">
                    请选择鞋型号：
                    <el-input v-model="shoeRidFilter" placeholder="鞋型号搜索" size="default" :suffix-icon="'el-icon-search'" @change="getAllShoes()" @clear="getAllShoes()" clearable> </el-input>
                </el-col>
                <el-col :span="4" :offset="2">
                    <el-input v-model="customerNameFilter" placeholder="客户型号搜索" size="default" :suffix-icon="'el-icon-search'" @change="getAllShoes()" @clear="getAllShoes()" clearable>
                    </el-input>
                </el-col>
                <el-col :span="2" :offset="2">
                    <el-button type="primary" size="default" @click="openAddShoeDialog"> 添加新鞋型 </el-button>
                </el-col>
            </el-row>
            <el-table :data="shoeTableData" style="width: 100%" stripe border height="500" row-key="shoeId">
                <el-table-column type="expand">
                    <template #default="props">
                        <el-table
                            :data="props.row.shoeTypeData"
                            border
                            row-key="shoeTypeId"
                            @selection-change="(selection) => handleSelectionShoeType(selection, props.row.shoeId)"
                            ref="shoeSelectionTable"
                        >
                            <el-table-column size="small" type="selection" align="center"> </el-table-column>
                            <el-table-column prop="colorName" label="鞋型颜色" width="100px" />
                            <el-table-column prop="shoeImageUrl" label="鞋型图片" align="center">
                                <template #default="scope">
                                    <el-image :src="scope.row.shoeImageUrl" style="width: 150px; height: 100px" :key="scope.row.shoeImageUrl" />
                                </template>
                            </el-table-column>
                            <el-table-column label="操作">
                                <template #default="scope">
                                    <el-button type="primary" @click="openReUploadImageDialog(scope.row)">重新上传鞋图</el-button>
                                </template>
                            </el-table-column>
                        </el-table>
                    </template>
                </el-table-column>
                <el-table-column prop="shoeRid" label="鞋型编号"></el-table-column>
                <el-table-column>
                    <template #default="scope">
                        <el-button type="primary" size="default" @click="openAddShoeTypeDialog(scope.row)">添加鞋款</el-button>
                    </template>
                </el-table-column>
            </el-table>
            <el-pagination
                :current-page="currentOrderCreatePage"
                :page-size="orderCreatePageSize"
                :total="shoeTotalItems"
                @current-change="handleOrderCreatePageChange"
                layout="total, prev, pager, next, jumper"
                style="margin-top: 20px"
            ></el-pagination>
        </el-form>

        <template #footer>
            <span>
                <el-button type="primary" @click="orderCreationSecondStep">下一步</el-button>
            </span>
        </template>
    </el-dialog>

    <AddShoeDialog :color-options="colorOptions" @submit="addNewShoe" />
    <AddShoeTypeDialog :color-options="colorOptions" @submit="addShoeTypes" />
    <el-dialog title="创建订单详情填写" v-model="dialogStore.orderCreationSecondInfoVis" width="100%" fullscreen :close-on-click-modal="false">
        <el-row :gutter="20">
            <el-col :span="24" :offset="0">
                <el-descriptions title="" :column="2" border>
                    <el-descriptions-item label="订单号" align="center">{{ this.newOrderForm.orderRId }}</el-descriptions-item>
                    <el-descriptions-item label="客户订单号" align="center">{{ this.newOrderForm.orderCid }}</el-descriptions-item>
                </el-descriptions>
                <el-descriptions title="" :column="2" border>
                    <el-descriptions-item label="客户名称" align="center">{{ this.newOrderForm.customerName }}</el-descriptions-item>
                    <el-descriptions-item label="客户商标" align="center">{{ this.newOrderForm.customerBrand }}</el-descriptions-item>
                </el-descriptions>
            </el-col>
        </el-row>
        <el-table
            class="order-shoe-create-table"
            :data="this.newOrderForm.orderShoeTypes"
            border
            stripe
            height="900"
            :row-key="
                (row) => {
                    return row.shoeTypeId
                }
            "
            :row-class-name="'persistent-shadow-row'"
            :default-expand-all="true"
        >
            <el-table-column type="expand">
                <template #default="props">
                    <el-table :data="props.row.orderShoeTypeBatchInfo" border>
                        <el-table-column prop="packagingInfoName" label="配码名称" sortable />
                        <el-table-column prop="packagingInfoLocale" label="配码地区" sortable />
                        <el-table-column
                            v-for="col in Object.keys(this.attrMapping).filter((key) => this.curBatchType[key] != null)"
                            :label="this.curBatchType[col]"
                            :prop="this.attrMapping[col]"
                        ></el-table-column>
                        <el-table-column prop="totalQuantityRatio" label="比例和" />
                        <el-table-column label="单位数量">
                            <template #default="scope">
                                <el-input size="small" v-model="props.row.quantityMapping[scope.row.packagingInfoId]" @change="updateAmountMapping(props.row, scope.row)" controls-position="right">
                                </el-input>
                            </template>
                        </el-table-column>
                        <el-table-column label="总数量">
                            <template #default="scope">
                                <el-input size="small" v-model="props.row.amountMapping[scope.row.packagingInfoId]" controls-position="right" :disabled="true"> </el-input>
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
                    <el-button type="primary" size="default" @click="openAddBatchInfoDialog(scope.row)">编辑鞋型配码</el-button>
                    <el-button type="primary" size="default" @click="openLoadBatchTemplateDialog(scope.row)">加载配码模板</el-button>
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

    <AddBatchInfoDialog
        ref="batchInfoDialog"
        v-model:batchNameFilter="batchNameFilter"
        :new-order-form="newOrderForm"
        :customer-display-batch-data="customerDisplayBatchData"
        :attr-mapping="attrMapping"
        :cur-batch-type="curBatchType"
        @selection-change="handleSelectionBatchData"
        @close="closeAddBatchInfoDialog"
        @open-add-customer-batch="openAddCustomerBatchDialog"
        @open-save-template="openSaveBatchTemplateDialog"
        @save-batch="addShoeTypeBatchInfo"
        @filter-with-selection="filterBatchDataWithSelection"
    />
    <TemplateSelectDialog
        v-model:templateFilter="templateFilter"
        :template-display-data="templateDisplayData"
        @filter="filterTemplateOptions"
        @create-from-template="openCreateOrderDialogFromTemplate"
    />
    <AddCustomerBatchDialog
        v-model:batchForm="batchForm"
        :attr-mapping="attrMapping"
        :cur-batch-type="curBatchType"
        @close="dialogStore.closeCustomerBatchDialog()"
        @submit="submitAddCustomerBatchForm"
    />
    <ReUploadImageDialog ref="reUploadImageDialog" :image-url="imageUrl" @file-change="onFileChange" @close="dialogStore.closeReUploadImageDialog()" @upload="uploadCroppedImage" />
    <CustomerBatchTemplateDialog
        :batch-template-display-data="batchTemplateDisplayData"
        :attr-mapping="attrMapping"
        :cur-batch-type="curBatchType"
        @selection-change="handleSelectionBatchTemplate"
        @delete-template="deleteBatchTemplateDialog"
        @confirm-load="confirmLoadBatchTemplate"
        @close="dialogStore.closeBatchTemplateDialog()"
    />
    <CustomerBatchTemplateSaveDialog
        v-model:batchTemplateForm="batchTemplateForm"
        :attr-mapping="attrMapping"
        :cur-batch-type="curBatchType"
        @close="dialogStore.closeBatchTemplateSaveDialog()"
        @save="saveBatchTemplate"
    />
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
import TemplateSelectDialog from './orderDialogs/TemplateSelectDialog.vue'
import AddCustomerBatchDialog from './orderDialogs/AddCustomerBatchDialog.vue'
import ReUploadImageDialog from './orderDialogs/ReUploadImageDialog.vue'
import CustomerBatchTemplateDialog from './orderDialogs/CustomerBatchTemplateDialog.vue'
import CustomerBatchTemplateSaveDialog from './orderDialogs/CustomerBatchTemplateSaveDialog.vue'

export default {
    components: {
        AddShoeTypeDialog,
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
            this.$nextTick(() => {
                selected.forEach((item) => {
                    ref.toggleRowSelection(
                        displaydataentity.find((row) => {
                            return row[id] == item[id]
                        }),
                        true
                    )
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
        openCreateOrderDialog() {
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
        openAddBatchInfoDialog(row) {
            this.curShoeTypeId = row.shoeTypeId
            this.dialogStore.openAddBatchInfoDialog()
            const idField = 'packagingInfoId'
            this.reselectSelected(this.$refs.batchInfoDialog.batchTable, row.orderShoeTypeBatchInfo, this.customerDisplayBatchData, idField)
        },
        openAddShoeDialog() {
            this.dialogStore.openAddShoeDialog()
        },
        openAddShoeTypeDialog(row) {
            this.shoeIdToAdd = row.shoeRid
            this.dialogStore.openAddShoeTypeDialog({
                shoeRid: row.shoeRid,
                shoeId: row.shoeId,
                shoeTypeColors: row.shoeTypeColors.map((color) => color.value)
            })
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
                const response = await axios.post(`${this.$apiBaseUrl}/shoemanage/addshoetype`, this.dialogStore.shoeColorForm)
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
        orderCreationSecondStep() {
            if (this.newOrderForm.orderRId === '') {
                ElMessage.error('未输入订单号，不允许创建订单')
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
            if (this.newOrderForm.orderShoeTypes.length === 0) {
                ElMessage.error('请至少选择一种鞋型号')
                return
            }
            if (this.newOrderForm.supervisorId === '') {
                ElMessage.error('未选择下发经理，不允许创建订单')
                return
            }
            this.dialogStore.closeOrderCreationDialog()
            this.dialogStore.openOrderDetailDialog()
            this.newOrderForm.orderShoeTypes.forEach((item) => {
                item.orderShoeTypeBatchInfo = []
                item.quantityMapping = {}
                item.amountMapping = {}
                item.customerColorName = ''
                this.newOrderForm.customerShoeName[item.shoeRid] = ''
            })
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
                                    salesman: '',
                                    orderShoeTypes: [],
                                    batchInfoQuantity: [],
                                    customerShoeName: {},
                                    flag: false,
                                    salesmanId: ''
                                }
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
        async checkOrderRidExists() {
            const queryRid = this.newOrderForm.orderRId
            const response = await axios.get(`${this.$apiBaseUrl}/order/checkorderridexists`, {
                params: {
                    pendingRid: queryRid
                }
            })
            const message = response.data.result
            const exists = response.data.exists
            if (exists == true) {
                this.$message.warning(message)
            } else {
                this.$message.success(message)
            }
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
