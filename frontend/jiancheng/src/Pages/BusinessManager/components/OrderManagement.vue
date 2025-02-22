<template>
    <el-row :gutter="20">
        <el-col :span="24" :offset="0" style="font-size: xx-large; text-align: center"
            >订单管理</el-col
        >
    </el-row>
    <el-row :gutter="10" style="margin-top: 20px">
        <el-col :span="4" :offset="0">
            <el-button size="default" type="primary" @click="openCreateOrderDialog"
                >创建订单</el-button
            >
            <el-button
                size="default"
                type="primary"
                @click="displayContent"
                v-if="this.userRole == 21 ? false : true"
                >{{ buttonText }}</el-button
            >
        </el-col>
        <el-col :span="4" :offset="1"
            ><el-input
                v-model="orderRidFilter"
                placeholder="订单号筛选"
                size="default"
                :suffix-icon="'el-icon-search'"
                clearable
                @input="filterDisplayOrder(1)"
                style="width: 300px;"
            ></el-input>
        </el-col>

        <el-col :span="4" :offset="2"
            ><el-input
                v-model="orderCidFilter"
                placeholder="客户订单号筛选"
                size="default"
                :suffix-icon="'el-icon-search'"
                clearable
                @input="filterDisplayOrder(2)"
                style="width: 300px"
            ></el-input>
        </el-col>
        <el-col :span="4" :offset="2"
            ><el-input
                v-model="orderCustomerNameFilter"
                placeholder="客户名称筛选"
                size="default"
                :suffix-icon="'el-icon-search'"
                clearable
                @input="filterDisplayOrder(3)"
                style="width: 300px"
            ></el-input>
        </el-col>
    </el-row>
    <el-row :gutter="10" style="margin-top: 20px">
        <el-col :span="4" :offset="0">
            <el-radio-group v-model="radio" size="small" @change="switchRadio(radio)">
                <el-radio-button label="全部订单" value="all" />
                <el-radio-button label="已下发订单" value="已下发" />
                <el-radio-button label="未下发订单" value="未下发" />
            </el-radio-group>
        </el-col>
        <el-col :span="4" :offset="1"
            ><el-input
                v-model="orderCustomerBrandFilter"
                placeholder="客户商标筛选"
                size="default"
                :suffix-icon="'el-icon-search'"
                clearable
                @input="filterDisplayOrder(4)"
                style="width: 300px"
            ></el-input>
        </el-col>
        <el-col :span="4" :offset="2">
            <div class="demo-date-picker">
                <div class="block">
                    <span class=""></span>
                    <el-date-picker
                        v-model="orderStartDateFilter"
                        type="daterange"
                        unlink-panels
                        range-separator="至"
                        start-placeholder="订单开始日期起"
                        end-placeholder="订单开始日期终"
                        :shortcuts="shortcuts"
                        size="default"
                        @change="filterDisplayOrder(5)"
                        style="width: 300px"
                    />
                </div>
            </div>
        </el-col>

        <el-col :span="4" :offset="2">
            <div class="demo-date-picker">
                <div class="block">
                    <span class=""></span>
                    <el-date-picker
                        v-model="orderEndDateFilter"
                        type="daterange"
                        unlink-panels
                        range-separator="至"
                        start-placeholder="订单结束日期起"
                        end-placeholder="订单结束日期终"
                        :shortcuts="shortcuts"
                        size="default"
                        @change="filterDisplayOrder(6)"
                        style="width: 300px"
                    />
                </div>
            </div>
        </el-col>
    </el-row>
    <el-row :gutter="20">
        <el-col :span="4">
            <el-radio-group v-model="sortRadio" size="small" @change="switchSortLogic(sortRadio)">
                <el-radio-button label="升序排列" value="asc" />
                <el-radio-button label="降序排列" value="desc" />
            </el-radio-group>
        </el-col>
    </el-row>
    <el-row :gutter="20">
        <el-table :data="paginatedDisplayData" border stripe height="500">
            <el-table-column prop="orderRid" label="订单号" sortable/>
            <el-table-column prop="orderCid" label="客户订单号" />
            <el-table-column prop="customerName" label="客户名" />
            <el-table-column prop="customerBrand" label="客户商标" />
            <el-table-column prop="orderStartDate" label="订单开始日期" sortable />
            <el-table-column prop="orderEndDate" label="订单结束日期" sortable />
            <el-table-column prop="orderStatus" label="订单状态" />
            <el-table-column label="操作" width="300">
                <template #default="scope">
                    <el-button
                        type="primary"
                        size="default"
                        @click="openOrderDetail(scope.row.orderDbId)"
                        >查看订单详情</el-button
                    >
                    <el-button
                        v-if="scope.row.orderStatusVal < 9 && this.userRole == 4"
                        type="danger"
                        size="default"
                        @click="deleteOrder(scope.row)"
                        >删除订单</el-button
                    >
                </template>
            </el-table-column>
        </el-table>
        <el-pagination
            :current-page="currentPage"
            :page-size="pageSize"
            :total="totalItems"
            @current-change="handlePageChange"
            layout="total,prev,pager,next,jumper"
            style="margin-top: 20px"
        ></el-pagination>
    </el-row>

    <el-dialog title="创建订单鞋型填写" v-model="orderCreationInfoVis" width="80%">
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
                <el-input v-model="newOrderForm.orderRId"></el-input>
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
                <el-select
                    v-model="newOrderForm.customerName"
                    filterable
                    placeholder="请选择客户"
                    @change="updateCustomerBrand"
                >
                    <el-option
                        v-for="item in this.customerNameList"
                        :key="item"
                        :label="item"
                        :value="item"
                    ></el-option>
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
                <el-select
                    v-model="newOrderForm.customerBrand"
                    filterable
                    placeholder="请选择商标"
                    @change="updateCustomerId"
                >
                    <el-option
                        v-for="item in this.customerBrandList"
                        :key="item"
                        :label="item"
                        :value="item"
                    ></el-option>
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
                <el-select
                    v-model="newOrderForm.batchInfoTypeName"
                    filterable
                    placeholder="请选择种类"
                    @change="updateBatchType"
                >
                    <el-option
                        v-for="item in this.batchTypes"
                        :key="item.batchInfoTypeId"
                        :label="item.batchInfoTypeName"
                        :value="item.batchInfoTypeName"
                    >
                    </el-option>
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
                <el-date-picker
                    v-model="newOrderForm.orderStartDate"
                    type="date"
                    placeholder="选择日期"
                    value-format="YYYY-MM-DD"
                ></el-date-picker>
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
                <el-date-picker
                    v-model="newOrderForm.orderEndDate"
                    type="date"
                    placeholder="选择日期"
                    value-format="YYYY-MM-DD"
                ></el-date-picker>
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
                <el-select
                    v-model="newOrderForm.supervisorId"
                    filterable
                    placeholder="请选择下发经理"
                >
                    <el-option
                        v-for="item in this.departmentNameList"
                        :key="item.staffId"
                        :label="item.staffName"
                        :value="item.staffId"
                    ></el-option>
                </el-select>
            </el-form-item>

            <el-row :gutter="20">
                <el-col :span="4" :offset="0" style="white-space: nowrap">
                    请选择鞋型号：
                    <el-input
                        v-model="shoeRidFilter"
                        placeholder="鞋型号搜索"
                        size="default"
                        :suffix-icon="'el-icon-search'"
                        :input="filterByShoeRid()"
                        clearable
                    >
                    </el-input>
                </el-col>
            </el-row>
            <el-table
                title=""
                :data="shoeTableDisplayData"
                style="width: 100%"
                stripe
                border
                height="500"
            >
                <el-table-column type="expand">
                    <template #default="props">
                        <el-table
                            :data="props.row.shoeTypeData"
                            border
                            row-key="shoeTypeId"
                            @selection-change="handleSelectionShoeType"
                            ref="shoeSelectionTable"
                        >
                            <el-table-column size="small" type="selection" align="center">
                            </el-table-column>
                            <el-table-column prop="colorName" label="鞋型颜色" width="100px" />
                            <el-table-column prop="shoeImageUrl" label="鞋型图片" align="center">
                                <template #default="scope">
                                    <el-image
                                        :src="scope.row.shoeImageUrl"
                                        style="width: 150px; height: 100px"
                                    />
                                </template>
                            </el-table-column>
                        </el-table>
                    </template>
                </el-table-column>
                <el-table-column prop="shoeRid" label="鞋型编号"></el-table-column>
            </el-table>
        </el-form>

        <template #footer>
            <span>
                <el-button @click="orderCreationInfoVis = false">取消</el-button>
                <el-button type="primary" @click="orderCreationSecondStep">确认</el-button>
            </span>
        </template>
    </el-dialog>

    <el-dialog title="创建订单详情填写" v-model="orderCreationSecondInfoVis" width="90%">
        <el-row :gutter="20">
            <el-col :span="24" :offset="0">
                <el-descriptions title="" :column="2" border>
                    <el-descriptions-item label="订单号" align="center">{{
                        this.newOrderForm.orderRId
                    }}</el-descriptions-item>
                    <el-descriptions-item label="客户订单号" align="center">{{
                        this.newOrderForm.orderCid
                    }}</el-descriptions-item>
                </el-descriptions>
                <el-descriptions title="" :column="2" border>
                    <el-descriptions-item label="客户名称" align="center">{{
                        this.newOrderForm.customerName
                    }}</el-descriptions-item>
                    <el-descriptions-item label="客户商标" align="center">{{
                        this.newOrderForm.customerBrand
                    }}</el-descriptions-item>
                </el-descriptions>
            </el-col>
        </el-row>
        <el-table
            :data="this.newOrderForm.orderShoeTypes"
            border
            stripe
            height="900"
            :row-key="
                (row) => {
                    return row.shoeTypeId
                }
            "
            :default-expand-all="true"
        >
            <el-table-column type="expand">
                <template #default="props">
                    <el-table :data="props.row.orderShoeTypeBatchInfo" border>
                        <el-table-column prop="packagingInfoName" label="配码名称" sortable />
                        <el-table-column prop="packagingInfoLocale" label="配码地区" sortable />
                        <el-table-column
                            v-for="col in Object.keys(this.attrMapping).filter(
                                (key) => this.curBatchType[key] != null
                            )"
                            :label="this.curBatchType[col]"
                            :prop="this.attrMapping[col]"
                        ></el-table-column>
                        <!-- <el-table-column prop="size34Ratio" label="34" />
                        <el-table-column prop="size35Ratio" label="35" />
                        <el-table-column prop="size36Ratio" label="36" />
                        <el-table-column prop="size37Ratio" label="37" />
                        <el-table-column prop="size38Ratio" label="38" />
                        <el-table-column prop="size39Ratio" label="39" />
                        <el-table-column prop="size40Ratio" label="40" />
                        <el-table-column prop="size41Ratio" label="41" />
                        <el-table-column prop="size42Ratio" label="42" />
                        <el-table-column prop="size43Ratio" label="43" />
                        <el-table-column prop="size44Ratio" label="44" />
                        <el-table-column prop="size45Ratio" label="45" />
                        <el-table-column prop="size46Ratio" label="46" /> -->
                        <el-table-column prop="totalQuantityRatio" label="比例和" />
                        <el-table-column label="单位数量">
                            <template #default="scope">
                                <el-input
                                    size="small"
                                    v-model="props.row.quantityMapping[scope.row.packagingInfoId]"
                                    @change="updateAmountMapping(props.row, scope.row)"
                                    controls-position="right"
                                >
                                </el-input>
                            </template>
                        </el-table-column>
                        <el-table-column label="总数量">
                            <template #default="scope">
                                <el-input
                                    size="small"
                                    v-model="props.row.amountMapping[scope.row.packagingInfoId]"
                                    controls-position="right"
                                    :disabled="true"
                                >
                                </el-input>
                            </template>
                        </el-table-column>
                    </el-table>
                </template>
            </el-table-column>
            <el-table-column prop="shoeRid" label="鞋型编号" sortable />
            <el-table-column prop="colorName" label="鞋型颜色" />
            <el-table-column label="鞋型图片">
                <template #default="scope">
                    <el-image
                        :src="scope.row.shoeImageUrl"
                        style="width: 150px; height: 100px"
                    ></el-image>
                </template>
            </el-table-column>
            <el-table-column>
                <template #default="scope">
                    <el-button
                        type="primary"
                        size="default"
                        @click="openAddBatchInfoDialog(scope.row)"
                        >编辑鞋型配码</el-button
                    >
                </template>
            </el-table-column>
            <el-table-column label="添加客户鞋型编号">
                <template #default="scope">
                    <el-input
                        size="default"
                        v-model="this.newOrderForm.customerShoeName[scope.row.shoeRid]"
                    ></el-input>
                </template>
            </el-table-column>

            <el-table-column label="添加客户鞋型颜色名称">
                <template #default="scope">
                    <el-input size="default" v-model="scope.row.customerColorName"></el-input>
                </template>
            </el-table-column>
        </el-table>
        <!-- <el-row :gutter="20">
            <el-table :data="customerDisplayBatchData" border stripe height="500">

                

                <el-table-column label="操作">
                    <template #default="scope">
                        <el-button type="primary" size="default" @click="openPreviewDialog(scope.row)"
                            >查看详情</el-button
                        >
                    </template>
                </el-table-column>
            </el-table>
        </el-row> -->
        <template #footer>
            <span>
                <el-button @click="backPreviousStep"> 上一步 </el-button>

                <el-button @click="orderCreationSecondInfoVis = false">取消</el-button>
                <el-button @click="submitNewOrder"> 添加订单 </el-button>
            </span>
        </template>
    </el-dialog>

    <el-dialog
        title="配码添加"
        v-model="addBatchInfoDialogVis"
        width="90%"
        @close="closeAddBatchInfoDialog()"
    >
        <el-col :span="4" :offset="15"
            ><el-input
                v-model="batchNameFilter"
                placeholder="请输入配码名称"
                size="default"
                :suffix-icon="'el-icon-search'"
                clearable
                @input="filterBatchDataWithSelection"
            ></el-input>
        </el-col>
        <el-row :gutter="20">
            <el-col :span="24" :offset="0">
                <el-descriptions title="" :column="2" border>
                    <el-descriptions-item label="客户名称" align="center">{{
                        this.newOrderForm.customerName
                    }}</el-descriptions-item>
                    <el-descriptions-item label="客户商标" align="center">{{
                        this.newOrderForm.customerBrand
                    }}</el-descriptions-item>
                </el-descriptions>
            </el-col>
        </el-row>
        <el-row :gutter="20">
            <el-table
                :data="customerDisplayBatchData"
                border
                stripe
                height="500"
                @selection-change="handleSelectionBatchData"
                ref="batchInfoSelectionTable"
            >
                <el-table-column size="small" type="selection" align="center"> </el-table-column>
                <el-table-column prop="packagingInfoName" label="配码名称" sortable />
                <el-table-column prop="packagingInfoLocale" label="配码地区" sortable />
                <el-table-column
                    v-for="col in Object.keys(this.attrMapping).filter(
                        (key) => this.curBatchType[key] != null
                    )"
                    :label="this.curBatchType[col]"
                    :prop="this.attrMapping[col]"
                ></el-table-column>
                <!-- <el-table-column prop="size34Ratio" label="34" sortable/>
                <el-table-column prop="size35Ratio" label="35" sortable/>
                <el-table-column prop="size36Ratio" label="36" sortable/>
                <el-table-column prop="size37Ratio" label="37" sortable/>
                <el-table-column prop="size38Ratio" label="38" sortable/>
                <el-table-column prop="size39Ratio" label="39" sortable/>
                <el-table-column prop="size40Ratio" label="40" sortable/>
                <el-table-column prop="size41Ratio" label="41" sortable/>
                <el-table-column prop="size42Ratio" label="42" sortable/>
                <el-table-column prop="size43Ratio" label="43" sortable/>
                <el-table-column prop="size44Ratio" label="44" sortable/>
                <el-table-column prop="size45Ratio" label="45" sortable/>
                <el-table-column prop="size46Ratio" label="46" sortable/> -->
                <el-table-column prop="totalQuantityRatio" label="比例和" sortable />
                <!-- <el-table-column label="操作">
                    <template #default="scope">
                        <el-button type="primary" size="default" @click="openPreviewDialog(scope.row)"
                            >查看详情</el-button
                        >
                    </template>
                </el-table-column>
 -->
            </el-table>
        </el-row>

        <template #footer>
            <el-button @click="closeAddBatchInfoDialog()">取消</el-button>
            <el-button @click="openAddCustomerBatchDialog()"> 添加新配码</el-button>
            <el-button type="primary" @click="addShoeTypeBatchInfo()"> 保存配码</el-button>
        </template>
    </el-dialog>

    <el-dialog title="添加配码" v-model="addCustomerBatchDialogVisible" width="30%">
        <el-form :model="batchForm" label-width="120px" :inline="false" size="default">
            <el-form-item label="配码名称">
                <el-input v-model="batchForm.packagingInfoName"></el-input>
            </el-form-item>
            <el-form-item label="配码地区">
                <el-input v-model="batchForm.packagingInfoLocale" disabled="true"></el-input>
            </el-form-item>
            <el-form-item
                v-for="col in Object.keys(this.attrMapping).filter(
                    (key) => this.curBatchType[key] != null
                )"
                :label="this.curBatchType[col]"
            >
                <el-input v-model="batchForm[attrMapping[col]]"></el-input>
            </el-form-item>
            <!-- <el-form-item label="34">
                <el-input v-model="batchForm.size34Ratio"></el-input>
            </el-form-item>
            <el-form-item label="35">
                <el-input v-model="batchForm.size35Ratio"></el-input>
            </el-form-item>
            <el-form-item label="36">
                <el-input v-model="batchForm.size36Ratio"></el-input>
            </el-form-item>
            <el-form-item label="37">
                <el-input v-model="batchForm.size37Ratio"></el-input>
            </el-form-item>
            <el-form-item label="38">
                <el-input v-model="batchForm.size38Ratio"></el-input>
            </el-form-item>
            <el-form-item label="39">
                <el-input v-model="batchForm.size39Ratio"></el-input>
            </el-form-item>
            <el-form-item label="40">
                <el-input v-model="batchForm.size40Ratio"></el-input>
            </el-form-item>
            <el-form-item label="41">
                <el-input v-model="batchForm.size41Ratio"></el-input>
            </el-form-item>
            <el-form-item label="42">
                <el-input v-model="batchForm.size42Ratio"></el-input>
            </el-form-item>
            <el-form-item label="43">
                <el-input v-model="batchForm.size43Ratio"></el-input>
            </el-form-item>
            <el-form-item label="44">
                <el-input v-model="batchForm.size44Ratio"></el-input>
            </el-form-item>
            <el-form-item label="45">
                <el-input v-model="batchForm.size45Ratio"></el-input>
            </el-form-item>
            <el-form-item label="46">
                <el-input v-model="batchForm.size46Ratio"></el-input>
            </el-form-item> -->
        </el-form>

        <template #footer>
            <span>
                <el-button @click="addCustomerDialogVisible = false">取消</el-button>
                <el-button type="primary" @click="submitAddCustomerBatchForm">确认提交</el-button>
            </span>
        </template>
    </el-dialog>
</template>

<script>
import { Download, Upload } from '@element-plus/icons-vue'
import axios from 'axios'
import { ElMessage, ElPagination, ElMessageBox } from 'element-plus'
import { toggleRowStatus } from 'element-plus/es/components/table/src/util'

export default {
    data() {
        return {
            token: localStorage.getItem('token'),
            staffId: localStorage.getItem('staffid'),
            orderNotInCurStatus: '',
            orderInCurStatus: '',
            currentPage: 1,
            pageSize: 8,
            totalItems: 200,
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
            addCustomerBatchDialogVisible: false,
            previewOrderVis: false,
            orderInfoVis: false,
            fileList: [],
            isImportVis: false,
            isSubmitDocVis: false,
            orderCreationInfoVis: false,
            orderCreationSecondInfoVis: false,
            parentBoarder: false,
            childBoarder: false,
            addBatchInfoDialogVis: false,
            Upload,
            batchNameFilter: '',
            orderRidFilter: '',
            orderCidFilter: '',
            orderStartDateFilter: '',
            orderEndDateFilter: '',
            orderCustomerNameFilter: '',
            orderCustomerBrandFilter: '',
            displayData: [],
            prevDisplayData: [],
            filterData: [],
            unfilteredData: [],
            uploadData: [],
            updatekey: 0,
            tempFileName: '',
            shoeTableData: [],
            shoeTableDisplayData: [],
            shoeTableTemp: [],
            shoeRidFilter: '',
            checkgroup: [],
            curShoeTypeId: '',
            batchTypes: [],
            batchTypeNameList: [],
            curBatchType: {},
            userRole: '',
            userName: '',
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
            radio: 'all',
            sortRadio: 'asc',
            buttonText: '查看所有订单',
            buttonFlag: true
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
        },
        paginatedDisplayData() {
            const start = (this.currentPage - 1) * this.pageSize
            const end = this.currentPage * this.pageSize
            return this.displayData.slice(start, end)
        }
    },
    mounted() {
        this.$setAxiosToken()
        this.userInfo()
        this.getAllOrders()
        this.getAllCutomers()
        // this.getAllOrderStatus()
        this.getAllShoes()
        this.getAllBatchTypes()
    },
    methods: {
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
            this.currentPage = newPage
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
        openCreateOrderDialog() {
            this.newOrderForm.orderStartDate = this.formatDateToYYYYMMDD(new Date())
            this.newOrderForm.salesman = this.userName
            this.newOrderForm.salesmanId = this.staffId
            this.orderCreationInfoVis = true
            this.shoeTableDisplayData = this.shoeTableData
            console.log(this.shoeTableDisplayData)
        },
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
            console.log(row)
            this.curShoeTypeId = row.shoeTypeId
            this.addBatchInfoDialogVis = true
            const idField = 'packagingInfoId'
            this.reselectSelected(
                this.$refs.batchInfoSelectionTable,
                row.orderShoeTypeBatchInfo,
                this.customerDisplayBatchData,
                idField
            )
        },
        openAddCustomerBatchDialog() {
            this.batchForm.customerId = this.newOrderForm.customerId
            this.batchForm.batchInfoTypeId = this.newOrderForm.batchInfoTypeId
            this.batchForm.packagingInfoLocale = this.newOrderForm.batchInfoTypeName
            this.addCustomerBatchDialogVisible = true
        },
        submitAddCustomerBatchForm() {
            console.log(this.batchForm)
            this.$confirm('确认添加客户配码信息？', '提示', {
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                type: 'warning'
            })
                .then(async () => {
                    const result = await axios.post(
                        `${this.$apiBaseUrl}/customer/addcustomerbatchinfo`,
                        this.batchForm
                    )
                })
                .then(async () => {
                    this.getCustomerBatchInfo(this.newOrderForm.customerId)
                    this.resetBatchForm()
                })
            this.addCustomerBatchDialogVisible = false
        },
        deleteOrder(row) {
            console.log(row)
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
                    this.getAllOrders()
                })
        },
        backPreviousStep() {
            this.orderCreationSecondInfoVis = false
            this.orderCreationInfoVis = true
        },
        closeAddBatchInfoDialog() {
            this.addBatchInfoDialogVis = false
            this.$refs.batchInfoSelectionTable.clearSelection()
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
            this.orderCreationInfoVis = false
            this.orderCreationSecondInfoVis = true
            this.newOrderForm.orderShoeTypes.forEach((item) => {
                item.orderShoeTypeBatchInfo = []
                item.quantityMapping = {}
                item.amountMapping = {}
                item.customerColorName = ''
                this.newOrderForm.customerShoeName[item.shoeRid] = ''
            })
            this.getCustomerBatchInfo(this.newOrderForm.customerId)
            // console.log(this.newOrderForm)
        },
        updateAmountMapping(out_row, inner_row) {
            out_row.amountMapping[inner_row.packagingInfoId] =
                out_row.quantityMapping[inner_row.packagingInfoId] * inner_row.totalQuantityRatio
        },
        handleSelectionShoeType(selection) {
            this.selectedShoeList = selection
            this.newOrderForm.orderShoeTypes = selection
            console.log(this.selectedShoeList)
            console.log(this.newOrderForm)
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
            this.customerBatchData = response.data.filter(
                (batch) => batch.batchInfoTypeId == this.newOrderForm.batchInfoTypeId
            )[0].batchInfoList
            this.customerDisplayBatchData = response.data.filter(
                (batch) => batch.batchInfoTypeId == this.newOrderForm.batchInfoTypeId
            )[0].batchInfoList
        },
        async getAllCutomers() {
            const response = await axios.get(`${this.$apiBaseUrl}/customer/getcustomerdetails`)
            this.customerDetails = response.data
            this.customerNameList = [...new Set(response.data.map((item) => item.customerName))]
        },
        async getAllBatchTypes() {
            const response = await axios.get(
                `${this.$apiBaseUrl}/batchtype/getallbatchtypesbusiness`
            )
            this.batchTypes = response.data.batchDataTypes
            this.batchTypeNameList = [
                ...new Set(this.batchTypes.map((item) => item.batchInfoTypeName))
            ]
        },
        updateCustomerBrand() {
            this.customerBrandList = [
                ...new Set(
                    this.customerDetails
                        .filter((item) => item.customerName == this.newOrderForm.customerName)
                        .map((item) => item.customerBrand)
                )
            ]
        },
        updateCustomerId() {
            this.newOrderForm.customerId = this.customerDetails
                .filter((item) => item.customerName == this.newOrderForm.customerName)
                .filter(
                    (item) => item.customerBrand == this.newOrderForm.customerBrand
                )[0].customerId
        },
        updateBatchType() {
            this.curBatchType = this.batchTypes.filter(
                (item) => item.batchInfoTypeName == this.newOrderForm.batchInfoTypeName
            )[0]
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
                this.customerDisplayBatchData = Array.from(
                    new Set([...selectedBatch.concat(this.customerBatchData)])
                )
            } else {
                this.customerFilteredBatchData = this.customerBatchData.filter((task) => {
                    const filteredData = task.packagingInfoName.includes(this.batchNameFilter)
                    return filteredData
                })
                this.customerDisplayBatchData = Array.from(
                    new Set([...selectedBatch.concat(this.customerFilteredBatchData)])
                )
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
            this.addBatchInfoDialogVis = false
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
            const response = await axios.get(
                `${this.$apiBaseUrl}/order/getbusinessdisplayorderbyuser`,
                {
                    currentStaffId: this.staffId
                }
            )
            this.unfilteredData = response.data
            this.displayData = this.unfilteredData
            this.totalItems = this.unfilteredData.length
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
            const response = await axios.get(`${this.$apiBaseUrl}/shoe/getallshoesnew`)
            this.shoeTableData = response.data
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
        filterOrderByFilterType(filterType) {
            switch (filterType) {
                case 1:
                    //console.log(this.orderRidFilter)
                    this.filterByRid()
                    break
                case 2:
                    //console.log(this.orderCidFilter)
                    this.filterByCid()
                    break
                case 3:
                    //console.log(this.orderCustomerNameFilter)
                    this.filterByCustomerName()
                    break
                case 4:
                    //console.log(this.orderCustomerBrandFilter)
                    this.filterByCustomerBrand()
                    break
                case 5:
                    //console.log(this.orderStartDateFilter)
                    this.filterOrderByStartDate()
                    break
                case 6:
                    //console.log(this.orderEndDateFilter)
                    this.filterOrderByEndDate()
                    break
            }
            return
        },

        filterDisplayOrder() {
            this.filterList = [
                this.orderRidFilter,
                this.orderCidFilter,
                this.orderCustomerNameFilter,
                this.orderCustomerBrandFilter,
                this.orderStartDateFilter,
                this.orderEndDateFilter
            ]
            this.indexToFilter = this.filterList
                .filter((filter) => filter)
                .map((filter) => this.filterList.indexOf(filter))
            this.displayData = this.unfilteredData
            this.indexToFilter.forEach((index) => this.filterOrderByFilterType(index + 1))
            this.filterOrderByStatus()
            this.totalItems = this.displayData.length
            return
        },
        filterOrderByStatus() {
            console.log(this.displayData)
            if (this.orderInCurStatus && this.orderNotInCurStatus) {
                return
            } else {
                if (this.orderInCurStatus) {
                    this.filterData = this.displayData.filter((task) => {
                        const filterMatch = task.orderStatusVal == 6
                        return filterMatch
                    })
                    this.displayData = this.filterData
                } else if (this.orderNotInCurStatus) {
                    this.filterData = this.displayData.filter((task) => {
                        const filterMatch = task.orderStatusVal != 6
                        return filterMatch
                    })
                    this.displayData = this.filterData
                }
            }
        },
        filterOrderByStartDate() {
            this.filterData = this.displayData.filter((task) => {
                const filterMatch =
                    new Date(task.orderStartDate) >= this.orderStartDateFilter[0] &&
                    new Date(task.orderStartDate) <= this.orderStartDateFilter[1]
                return filterMatch
            })
            this.displayData = this.filterData
        },
        filterOrderByEndDate() {
            this.filterData = this.displayData.filter((task) => {
                const filterMatch =
                    new Date(task.orderEndDate) >= this.orderEndDateFilter[0] &&
                    new Date(task.orderEndDate) <= this.orderEndDateFilter[1]
                return filterMatch
            })
            this.displayData = this.filterData
        },
        filterByCustomerName() {
            this.filterData = this.displayData.filter((task) => {
                const filterMatch = task.customerName
                    .toLowerCase()
                    .includes(this.orderCustomerNameFilter.toLowerCase())
                return filterMatch
            })
            this.displayData = this.filterData
        },
        filterByCustomerBrand() {
            this.filterData = this.displayData.filter((task) => {
                const filterMatch = task.customerBrand
                    .toLowerCase()
                    .includes(this.orderCustomerBrandFilter.toLowerCase())
                return filterMatch
            })
            this.displayData = this.filterData
        },
        filterByCid() {
            this.filterData = this.displayData.filter((task) => {
                const filterMatch = task.orderCid
                    .toLowerCase()
                    .includes(this.orderCidFilter.toLowerCase())
                return filterMatch
            })
            this.displayData = this.filterData
        },
        filterByRid() {
            this.filterData = this.displayData.filter((task) => {
                const filterMatch = task.orderRid
                    .toLowerCase()
                    .includes(this.orderRidFilter.toLowerCase())
                return filterMatch
            })
            this.displayData = this.filterData
        },
        filterByShoeRid() {
            if (!this.shoeRidFilter) {
                this.shoeTableDisplayData = this.shoeTableData
            } else {
                this.shoeTableTemp = this.shoeTableData.filter((task) => {
                    const filterMatch = task.shoeRid
                        .toLowerCase()
                        .includes(this.shoeRidFilter.toLowerCase())
                    return filterMatch
                })

                this.shoeTableDisplayData = this.shoeTableTemp
            }
        },
        filterByShoeRidWithSelection() {
            console.log(this.shoeRidFilter)
            const selectedShoeTypeIds = this.selectedShoeList.map((row) => row.shoeTypeId)
            if (!this.shoeRidFilter) {
                this.shoeTableDisplayData = Array.from(
                    new Set([...this.selectedShoeList.concat(this.shoeTableData)])
                )
            } else {
                this.shoeTableTemp = this.shoeTableData.filter((task) => {
                    const filterMatch = task.shoeRid.includes(this.shoeRidFilter)
                    return filterMatch
                })
                this.shoeTableDisplayData = Array.from(
                    new Set([...this.selectedShoeList.concat(this.shoeTableTemp)])
                )
            }
            const rowsToToggle = this.shoeTableDisplayData.filter((row) =>
                selectedShoeTypeIds.includes(row.shoeTypeId)
            )

            const fieldName = 'shoeTypeId'
            this.reselectSelected(
                this.$refs.shoeSelectionTable,
                rowsToToggle,
                this.shoeTableDisplayData,
                fieldName
            )
            // this.$nextTick(()=>{
            //         selectedShoeTypeIds.forEach(item =>
            //         {
            //         this.$refs.shoeSelectionTable.toggleRowSelection(this.shoeTableDisplayData.find(row => {
            //             return row.shoeTypeId == item
            //         }),true)
            //         })
            //     })
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
            window.open(
                `${this.$apiBaseUrl}/orderimport/downloadorderdoc?orderrid=${this.orderData.orderRid}&filetype=${type}`
            )
        },
        mergeCells({ row, column, rowIndex, columnIndex }) {
            const mergeColumns = ['inheritId', 'customerId', 'colorCN', 'colorEN']

            if (mergeColumns.includes(column.property)) {
                // Check if the previous row has the same value for the column
                if (
                    rowIndex > 0 &&
                    row[column.property] === this.uploadData[rowIndex - 1][column.property]
                ) {
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
                        row[column.property] ===
                            this.orderShoePreviewData[rowIndex - 1][column.property] &&
                        row['inheritId'] === this.orderShoePreviewData[rowIndex - 1]['inheritId']
                    ) {
                        return {
                            rowspan: 0, // Hide the current cell
                            colspan: 0
                        }
                    } else {
                        let rowspan = 1
                        for (let i = rowIndex + 1; i < this.orderShoePreviewData.length; i++) {
                            if (
                                this.orderShoePreviewData[i][column.property] ===
                                    row[column.property] &&
                                this.orderShoePreviewData[i]['inheritId'] === row['inheritId']
                            ) {
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
                    if (
                        rowIndex > 0 &&
                        row[column.property] ===
                            this.orderShoePreviewData[rowIndex - 1][column.property]
                    ) {
                        return {
                            rowspan: 0, // Hide the current cell
                            colspan: 0
                        }
                    } else {
                        let rowspan = 1
                        for (let i = rowIndex + 1; i < this.orderShoePreviewData.length; i++) {
                            if (
                                this.orderShoePreviewData[i][column.property] ===
                                row[column.property]
                            ) {
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
                    const response = await axios.post(
                        `${this.$apiBaseUrl}/orderimport/confirmimportorder`,
                        {
                            fileName: this.tempFileName,
                            orderInfo: this.orderForm
                        }
                    )
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
                            await axios.post(
                                `${this.$apiBaseUrl}/ordercreate/createneworder`,
                                {
                                    orderInfo: this.newOrderForm
                                }
                            )
                                ElMessage.success('创建订单成功')
                                loadingInstance.close()
                                this.orderCreationSecondInfoVis = false
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
                            }
                            catch (error) {
                                console.error('Upload error:', error)
                                ElMessage.error(error.data.message)
                            }
                        })
                    }
                }
            })
        },
        openOrderDetail(orderId) {
            let url = ''
            if (this.userRole == 4) {
                url = `${window.location.origin}/business/businessorderdetail/orderid=${orderId}/admin`
            } else if (this.userRole == 21) {
                url = `${window.location.origin}/business/businessorderdetail/orderid=${orderId}/clerk`
            }
            window.open(url, '_blank')
        },
        switchRadio(value) {
            if (value === 'all') {
                this.orderInCurStatus = '已下发'
                this.orderNotInCurStatus = '未下发'
            } else if (value === '已下发') {
                this.orderInCurStatus = ''
                this.orderNotInCurStatus = 'all'
            } else {
                this.orderInCurStatus = 'all'
                this.orderNotInCurStatus = ''
            }
            this.filterDisplayOrder()
        },
        async switchSortLogic(value) {
            console.log(value)
            if (value === 'asc') {
                if (!this.buttonFlag) {
                    const response = await axios.get(`${this.$apiBaseUrl}/order/getbusinessdisplayorderbyuser`,
                        {
                            currentStaffId: this.staffId
                        }
                    )
                    this.unfilteredData = response.data
                    this.displayData = this.unfilteredData
                    this.totalItems = this.unfilteredData.length
                }
                else {
                    const response = await axios.get(`${this.$apiBaseUrl}/order/getallorders`)
                    this.unfilteredData = response.data
                    this.displayData = this.unfilteredData
                    this.totalItems = this.unfilteredData.length
                }

            }
            else if (value === 'desc') {
                if (!this.buttonFlag) {
                    const response = await axios.get(`${this.$apiBaseUrl}/order/getbusinessdisplayorderbyuser`,
                        {
                            currentStaffId: this.staffId
                        }
                    )
                    this.unfilteredData = response.data
                    console.log(this.unfilteredData)
                    this.displayData = this.unfilteredData
                    this.totalItems = this.unfilteredData.length
                }
                else {
                    const response = await axios.get(`${this.$apiBaseUrl}/order/getallorders?descSymbol=1`,
                    )
                    this.unfilteredData = response.data
                    this.displayData = this.unfilteredData
                    this.totalItems = this.unfilteredData.length
                }
            }
        },
        async displayContent() {
            if (this.buttonFlag) {
                this.buttonText = '需我审批订单'
                const response = await axios.get(`${this.$apiBaseUrl}/order/getallorders`)
                this.unfilteredData = response.data
                this.displayData = this.unfilteredData
                this.totalItems = this.unfilteredData.length
                this.radio = 'all'
                this.sortRadio = 'asc'
            } else {
                this.buttonText = '查看所有订单'
                const response = await axios.get(
                    `${this.$apiBaseUrl}/order/getbusinessdisplayorderbyuser`,
                    {
                        currentStaffId: this.staffId
                    }
                )
                this.unfilteredData = response.data
                console.log(this.unfilteredData)
                this.displayData = this.unfilteredData
                this.totalItems = this.unfilteredData.length
                this.radio = 'all'
                this.sortRadio = 'asc'
            }
            this.buttonFlag = !this.buttonFlag
        }
    },
    watch: {
        async orderCreationInfoVis(newValue, oldValue) {
            if (newValue) {
                const response = await axios.get(`${this.$apiBaseUrl}/general/getbusinessmanagers`)
                this.departmentNameList = response.data
            }
        }
    }
}
</script>
