<template>
    <!-- ===== 搜索区 ===== -->
    <el-row :gutter="20">
        <el-col :span="16">
            <el-input v-model="orderNumberSearch" placeholder="请输入订单号" clearable @keypress.enter="getTableData" @clear="getTableData" class="search-input" />
            <el-input v-model="customerNameSearch" placeholder="请输入客户名称" clearable @keypress.enter="getTableData" @clear="getTableData" class="search-input" />
            <el-input v-model="orderCIdSearch" placeholder="请输入客户订单号" clearable @keypress.enter="getTableData" @clear="getTableData" class="search-input" />
            <el-input v-model="customerBrandSearch" placeholder="请输入客户商标" clearable @keypress.enter="getTableData" @clear="getTableData" class="search-input" />
        </el-col>
    </el-row>

    <!-- ===== 状态筛选 ===== -->
    <el-row class="mt-2">
        <el-col :span="12">
            <span>审核状态筛选：</span>
            <el-radio-group v-model="auditStatusNum" @change="getTableData">
                <el-radio-button v-for="option in auditStatusOptions" :key="option.value" :label="option.value">
                    {{ option.label }}
                </el-radio-button>
            </el-radio-group>
        </el-col>
        <el-col :span="12">
            <span>仓库状态筛选：</span>
            <el-radio-group v-model="storageStatusNum" @change="handleStorageStatusChange">
                <el-radio-button v-for="option in storageStatusOptionsForRole" :key="option.value" :label="option.value">
                    {{ option.label }}
                </el-radio-button>
            </el-radio-group>
        </el-col>
    </el-row>

    <!-- ===== 操作按钮区（业务 + 仓库；总经理逻辑已移除） ===== -->
    <el-row :gutter="20" class="mt-3">
        <el-col :span="12">
            <!-- 仓库：role = 20 只做确认出库 -->
            <el-button-group v-if="role == 20">
                <el-button type="warning" v-if="isMultipleSelection" @click="openWarehouseOutboundDialog" :disabled="storageStatusNum === FINISHED_STORAGE_STATUS_ENUM.PRODUCT_OUTBOUND_FINISHED">
                    批量出库
                </el-button>
                <el-button type="primary" @click="toggleSelectionMode" :disabled="storageStatusNum === FINISHED_STORAGE_STATUS_ENUM.PRODUCT_OUTBOUND_FINISHED">
                    {{ isMultipleSelection ? '退出选择' : '选择成品出库' }}
                </el-button>
            </el-button-group>

            <!-- 业务：填写出库申请（支持多订单） -->
            <el-button-group v-else-if="role == 4 || role == 21">
                <el-button v-if="isMultipleSelection" type="primary" @click="openBusinessDialog"> 填写出库申请 </el-button>
                <el-button type="primary" @click="toggleSelectionMode">
                    {{ isMultipleSelection ? '退出选择' : '选择订单' }}
                </el-button>
            </el-button-group>

            <!-- 其他角色在这个页面只能查看，不做任何操作 -->
            <el-button-group v-else>
                <el-button type="primary" disabled>仅查看</el-button>
            </el-button-group>
        </el-col>

        <!-- 查看出库申请列表（所有角色都可以看，根据需要你也可以限制） -->
        <el-col :span="12" style="text-align: right">
            <el-button type="success" plain @click="openApplyListDialog"> 查看出库申请 </el-button>
        </el-col>
    </el-row>

    <!-- ===== 订单总览表（展开到颜色；不再展示配码细节） ===== -->
    <el-row :gutter="20" class="mt-3">
        <el-col :span="24">
            <el-table :data="tableData" border stripe height="50vh" @selection-change="handleSelectionChange">
                <!-- 多选 -->
                <el-table-column v-if="isMultipleSelection" type="selection" width="55" />

                <!-- 展开：订单下所有鞋型+颜色（精简版） -->
                <el-table-column type="expand">
                    <template #default="{ row }">
                        <el-table :data="row.orderShoeTable" border stripe size="small">
                            <el-table-column prop="shoeRId" label="工厂型号" />
                            <el-table-column prop="customerProductName" label="客户鞋号" />
                            <el-table-column prop="colorName" label="颜色" />
                            <el-table-column prop="orderAmountPerColor" label="订单数量" />
                            <el-table-column prop="currentStock" label="当前库存" />
                            <el-table-column prop="outboundedAmount" label="已出库数量" />
                        </el-table>
                    </template>
                </el-table-column>

                <el-table-column prop="orderRId" label="订单号" />
                <el-table-column prop="customerName" label="客户名称" />
                <el-table-column prop="orderCId" label="客户订单号" />
                <el-table-column prop="customerBrand" label="客户商标" />
                <el-table-column prop="orderAmount" label="订单数量" />
                <el-table-column prop="currentStock" label="成品库存" />
                <el-table-column prop="pendingOutboundAmount" label="审核中出库数量" />
                <el-table-column prop="outboundedAmount" label="已出库数量" />

                <el-table-column label="仓库状态">
                    <template #default="{ row }">
                        <el-tag v-if="row.storageStatusNum == FINISHED_STORAGE_STATUS_ENUM.PRODUCT_INBOUND_NOT_FINISHED" type="warning">
                            {{ row.storageStatusLabel }}
                        </el-tag>
                        <el-tag v-else-if="row.storageStatusNum == FINISHED_STORAGE_STATUS_ENUM.PRODUCT_INBOUND_FINISHED" type="success">
                            {{ row.storageStatusLabel }}
                        </el-tag>
                        <el-tag v-else-if="row.storageStatusNum == FINISHED_STORAGE_STATUS_ENUM.PRODUCT_OUTBOUND_FINISHED" type="success">
                            {{ row.storageStatusLabel }}
                        </el-tag>
                    </template>
                </el-table-column>

                <el-table-column label="审核状态">
                    <template #default="{ row }">
                        <el-tag
                            :type="row.auditStatusNum === PRODUCT_OUTBOUND_AUDIT_STATUS_ENUM.PRODUCT_OUTBOUND_AUDIT_ONGOING ? 'warning' : 'info'"
                            style="cursor: pointer"
                            @click="openOrderPendingApplyDialog(row)"
                        >
                            {{ row.auditStatusLabel }}
                            <template v-if="row.pendingOutboundAmount > 0"> （{{ row.pendingOutboundAmount }} 双审核中） </template>
                        </el-tag>
                    </template>
                </el-table-column>
            </el-table>
        </el-col>
    </el-row>

    <!-- ===== 分页 ===== -->
    <el-row :gutter="20" class="mt-2">
        <el-col>
            <el-pagination
                @size-change="handleSizeChange"
                @current-change="handlePageChange"
                :current-page="currentPage"
                :page-sizes="pageSizes"
                :page-size="pageSize"
                layout="total, sizes, prev, pager, next, jumper"
                :total="totalRows"
            />
        </el-col>
    </el-row>

    <!-- ========== 业务：填写 / 编辑 出库申请（配码 + 鞋码比例，多订单） ========== -->
    <el-dialog :title="businessForm.applyId ? '编辑出库申请（配码 + 鞋码比例）' : '业务填写出库申请（配码 + 鞋码比例）'" v-model="isBusinessDialogVisible" width="95%">
        <el-form :model="businessForm" label-width="120px" class="mb-2">
            <el-form-item label="预计出库时间">
                <el-date-picker v-model="businessForm.expectedOutboundTime" type="datetime" value-format="YYYY-MM-DD HH:mm:ss" placeholder="请选择预计出库时间" />
            </el-form-item>
            <el-form-item label="备注">
                <el-input v-model="businessForm.remark" type="textarea" :rows="2" placeholder="本批次出库申请备注（可选）" />
            </el-form-item>
        </el-form>

        <!-- 每行 = 订单 + 型号 + 颜色 + 配码 + 鞋码比例 + 配码库存 + 申请箱数/双数 -->
        <el-table :data="businessPagedItems" border stripe size="small" style="width: 100%">
            <el-table-column prop="orderRId" label="订单号" />
            <el-table-column prop="shoeRId" label="工厂型号" />
            <el-table-column prop="customerProductName" label="客户鞋号" />
            <el-table-column prop="colorName" label="颜色" />
            <el-table-column prop="batchName" label="配码名称" />
            <el-table-column prop="packagingInfoName" label="包装方案" />

            <!-- 动态鞋码比例列（编辑模式下一般为空，不影响使用） -->
            <el-table-column v-for="col in businessForm.sizeColumns" :key="col.key" :label="col.label" min-width="70">
                <template #default="{ row }">
                    {{ row.sizeRatiosMap[col.key] ?? '' }}
                </template>
            </el-table-column>

            <!-- 配码库存总双数 -->
            <el-table-column prop="batchStock" label="配码库存(双)">
                <template #default="{ row }">
                    {{ row.batchStock }}
                </template>
            </el-table-column>

            <!-- 每箱双数，申请箱数，申请双数 -->
            <el-table-column prop="pairsPerCarton" label="每箱双数" />
            <el-table-column label="申请箱数" min-width="160">
                <template #default="{ row }">
                    <el-input-number v-model="row.applyCartons" :min="0" :step="0.05" :precision="2" @change="updateBusinessPairs(row)" />
                </template>
            </el-table-column>
            <el-table-column label="申请双数">
                <template #default="{ row }">
                    {{ row.applyPairs }}
                </template>
            </el-table-column>

            <el-table-column label="备注" min-width="160">
                <template #default="{ row }">
                    <el-input v-model="row.remark" size="small" />
                </template>
            </el-table-column>
        </el-table>

        <!-- 业务出库申请明细的本地分页 -->
        <el-row class="mt-2" v-if="businessForm.items.length > 0">
            <el-col>
                <el-pagination
                    @size-change="handleBusinessSizeChange"
                    @current-change="handleBusinessPageChange"
                    :current-page="businessCurrentPage"
                    :page-sizes="businessPageSizes"
                    :page-size="businessPageSize"
                    layout="total, sizes, prev, pager, next, jumper"
                    :total="businessForm.items.length"
                />
            </el-col>
        </el-row>

        <template #footer>
            <span>
                <el-button @click="isBusinessDialogVisible = false">取消</el-button>
                <el-button type="primary" @click="submitBusinessForm">
                    {{ businessForm.applyId ? '保存修改并提交审核' : '提交出库申请' }}
                </el-button>
            </span>
        </template>
    </el-dialog>

    <!-- ========== 仓库：确认出库（按订单颜色聚合） ========== -->
    <el-dialog :title="operationLabels.dialogTitle[currentOperation]" v-model="isOutboundDialogVisible" width="70%">
        <el-form :model="outboundForm">
            <el-form-item prop="remark" label="备注">
                <el-input v-model="outboundForm.remark" :maxlength="40" show-word-limit />
            </el-form-item>
        </el-form>

        <el-table :data="outboundForm.items" style="width: 100%" border stripe>
            <el-table-column prop="orderRId" label="订单号" width="120" />
            <el-table-column prop="shoeRId" label="工厂型号" width="120" />
            <el-table-column prop="colorName" label="颜色" width="80" />
            <el-table-column prop="currentStock" label="库存数量" width="100" />
            <el-table-column :label="operationLabels.operationAmount[currentOperation]" width="160">
                <template #default="{ row }">
                    <el-input-number v-model="row.outboundQuantity" :min="0" />
                </template>
            </el-table-column>
            <el-table-column prop="remark" label="备注" min-width="160">
                <template #default="{ row }">
                    <el-input v-model="row.remark" :maxlength="40" show-word-limit size="small" />
                </template>
            </el-table-column>
        </el-table>

        <template #footer>
            <span>
                <el-button @click="isOutboundDialogVisible = false">返回</el-button>
                <el-button type="primary" @click="submitOperationForm"> 出库 </el-button>
            </span>
        </template>
    </el-dialog>

    <!-- ===== 原有尺码数量对话框（保留） ===== -->
    <el-dialog title="数量输入框" v-model="isOpenQuantityDialogVisible" width="60%">
        <el-form>
            <el-form-item>
                <el-table :data="filteredData" border stripe>
                    <el-table-column prop="shoeSizeName" label="鞋码" />
                    <el-table-column prop="predictQuantity" label="应出库数量" />
                    <el-table-column prop="outboundedQuantity" label="已出库数量" />
                    <el-table-column prop="currentQuantity" label="库存" />
                    <el-table-column :label="operationLabels.operationAmount[currentOperation]">
                        <template #default="{ row }">
                            <el-input-number v-model="row.operationQuantity" size="small" :min="0" :max="row.currentQuantity" @change="updateTotalShoes" />
                        </template>
                    </el-table-column>
                </el-table>
            </el-form-item>
        </el-form>
        <template #footer>
            <el-button type="primary" @click="isOpenQuantityDialogVisible = false"> 确认 </el-button>
        </template>
    </el-dialog>

    <!-- 尺码生产进度（保留） -->
    <el-dialog title="各鞋码生产进度" v-model="isOpenShoeSizeDialogVisible" width="80%">
        <el-tabs v-model="activeStockTab">
            <el-tab-pane v-for="row in currentRow.orderShoeTable" :key="row.orderShoeTypeId" :label="`${row.shoeRId}-${row.colorName}`" :name="row.orderShoeTypeId">
                <el-table :data="row.shoesOutboundTable" border stripe>
                    <el-table-column prop="shoeSizeName" label="鞋码" />
                    <el-table-column prop="predictQuantity" label="订单数量" />
                    <el-table-column prop="currentQuantity" label="库存" />
                    <el-table-column prop="outboundedQuantity" label="已出库数量" />
                </el-table>
            </el-tab-pane>
        </el-tabs>
        <template #footer>
            <el-button type="primary" @click="isOpenShoeSizeDialogVisible = false"> 确认 </el-button>
        </template>
    </el-dialog>

    <!-- ===== 出库申请列表（查看所有状态） ===== -->
    <el-dialog title="出库申请列表" v-model="isApplyListDialogVisible" width="80%">
        <el-form :inline="true" :model="applyFilters" class="mb-2" @keyup.enter="getApplyList">
            <el-form-item label="订单号">
                <el-input v-model="applyFilters.orderRId" placeholder="订单号" clearable />
            </el-form-item>
            <el-form-item label="申请单号">
                <el-input v-model="applyFilters.applyRId" placeholder="出库申请单号" clearable />
            </el-form-item>
            <el-form-item label="客户名称">
                <el-input v-model="applyFilters.customerName" placeholder="客户名称" clearable />
            </el-form-item>
            <el-form-item label="状态">
                <el-select v-model="applyFilters.status" clearable placeholder="全部" style="min-width: 140px">
                    <el-option v-for="opt in applyStatusOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
                </el-select>
            </el-form-item>
            <el-form-item>
                <el-button type="primary" @click="getApplyList">查询</el-button>
            </el-form-item>
        </el-form>

        <el-table :data="applyTableData" border stripe height="400">
            <el-table-column prop="applyRId" label="申请单号" width="180" />
            <el-table-column prop="orderRId" label="主订单号" width="140" />
            <el-table-column prop="orderCId" label="客户订单号" width="160" />
            <el-table-column prop="customerName" label="客户名称" />
            <el-table-column prop="customerBrand" label="客户商标" />
            <el-table-column prop="totalPairs" label="申请总双数" width="120" />
            <el-table-column prop="statusLabel" label="状态" width="140" />
            <el-table-column prop="remark" label="备注" min-width="200" />
            <el-table-column prop="expectedOutboundTime" label="预计出库时间" width="180" />
            <el-table-column prop="actualOutboundTime" label="实际出库时间" width="180" />
            <!-- 编辑入口 -->
            <el-table-column label="操作" width="120">
                <template #default="{ row }">
                    <el-button v-if="canEditApply(row)" type="primary" link size="small" @click="editApply(row)"> 编辑 </el-button>
                    <span v-else style="color: #bbb">不可编辑</span>
                </template>
            </el-table-column>
        </el-table>

        <el-row class="mt-2">
            <el-col>
                <el-pagination
                    @size-change="handleApplySizeChange"
                    @current-change="handleApplyPageChange"
                    :current-page="applyCurrentPage"
                    :page-sizes="applyPageSizes"
                    :page-size="applyPageSize"
                    layout="total, sizes, prev, pager, next, jumper"
                    :total="applyTotalRows"
                />
            </el-col>
        </el-row>
    </el-dialog>

    <!-- 某订单的“正在审核”的出库申请列表 -->
    <el-dialog :title="`订单 ${pendingApplyOrderRId} 正在审核的出库申请`" v-model="isOrderPendingApplyDialogVisible" width="70%">
        <el-table :data="orderPendingApplyList" border stripe height="400">
            <el-table-column prop="applyRId" label="申请单号" width="180" />
            <el-table-column prop="totalPairs" label="申请双数" width="120" />
            <el-table-column prop="statusLabel" label="状态" width="140" />
            <el-table-column prop="remark" label="备注" min-width="200" />
            <el-table-column prop="createTime" label="创建时间" width="180" />
            <el-table-column prop="updateTime" label="更新时间" width="180" />
        </el-table>
    </el-dialog>
</template>

<script>
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'
import { PAGESIZE, PAGESIZES } from '../../warehouseUtils'

export default {
    data() {
        return {
            // 仓库确认出库用
            formItemTemplate: {
                picker: null,
                remark: null,
                items: []
            },
            outboundForm: {},

            // 业务填写 / 编辑 出库申请用
            businessForm: {
                applyId: null,
                orderId: null, // 主订单（apply 表头用）
                remark: '',
                items: [],
                sizeColumns: [],
                expectedOutboundTime: ''
            },

            // 业务对话框内部分页
            businessCurrentPage: 1,
            businessPageSize: 20,
            businessPageSizes: [10, 20, 50, 100],

            currentPage: 1,
            pageSize: PAGESIZE,
            pageSizes: PAGESIZES,
            tableData: [],
            totalRows: 0,

            orderNumberSearch: '',
            orderCIdSearch: '',
            customerNameSearch: '',
            customerBrandSearch: '',

            currentRow: { orderShoeTable: [] },
            isMultipleSelection: false,
            selectedRows: [],

            isOutboundDialogVisible: false,
            currentOperation: 1, // 0: inbound, 1: outbound
            operationLabels: {
                dialogTitle: ['成品入库', '成品出库'],
                timestamp: ['入库日期', '出库日期'],
                operationAmount: ['入库数量', '出库数量']
            },

            currentQuantityRow: null,
            isOpenQuantityDialogVisible: false,

            role: localStorage.getItem('role'),

            auditStatusOptions: [],
            storageStatusOptions: [],
            auditStatusNum: null,
            storageStatusNum: null,

            isOpenShoeSizeDialogVisible: false,
            activeStockTab: null,

            FINISHED_STORAGE_STATUS_ENUM: {},
            PRODUCT_OUTBOUND_AUDIT_STATUS_ENUM: {},

            isBusinessDialogVisible: false,

            // 出库申请列表
            isApplyListDialogVisible: false,
            applyFilters: {
                orderRId: '',
                applyRId: '',
                customerName: '',
                status: null
            },
            applyStatusOptions: [
                { value: 0, label: '草稿' },
                { value: 1, label: '待总经理审核' },
                { value: 2, label: '总经理驳回' },
                { value: 3, label: '待仓库出库' },
                { value: 4, label: '已完成出库' },
                { value: 5, label: '已作废' }
            ],
            applyTableData: [],
            applyTotalRows: 0,
            applyCurrentPage: 1,
            applyPageSize: 20,
            applyPageSizes: [10, 20, 50, 100],

            // 某订单的“正在审核”的出库申请弹窗
            isOrderPendingApplyDialogVisible: false,
            pendingApplyOrderRId: '',
            orderPendingApplyList: []
        }
    },
    computed: {
        filteredData() {
            if (!this.currentQuantityRow || !this.currentQuantityRow.shoesOutboundTable) {
                return []
            }
            return this.currentQuantityRow.shoesOutboundTable.filter((row) => row.predictQuantity > 0)
        },
        isBusinessRole() {
            return this.role == 4 || this.role == 21
        },
        storageStatusOptionsForRole() {
            if (!Array.isArray(this.storageStatusOptions)) {
                return []
            }
            const outboundFinishedValue = this.FINISHED_STORAGE_STATUS_ENUM?.PRODUCT_OUTBOUND_FINISHED
            if (!this.isBusinessRole || outboundFinishedValue == null) {
                return this.storageStatusOptions
            }
            return this.storageStatusOptions.filter((opt) => opt.value !== outboundFinishedValue)
        },
        // 业务明细分页后的数据
        businessPagedItems() {
            const start = (this.businessCurrentPage - 1) * this.businessPageSize
            const end = start + this.businessPageSize
            return this.businessForm.items.slice(start, end)
        }
    },
    async mounted() {
        await this.getStorageStatusOptions()
        await this.getOutboundAuditStatusOptions()
        this.displayOrdersbyRole()
        this.getTableData()
    },
    methods: {
        // ====== 枚举 & 初始角色筛选 ======
        async getStorageStatusOptions() {
            const response = await axios.get(`${this.$apiBaseUrl}/product/getstoragestatusoptions`)
            this.storageStatusOptions = response.data.storageStatusOptions
            this.FINISHED_STORAGE_STATUS_ENUM = response.data.storageStatusEnum
        },
        async getOutboundAuditStatusOptions() {
            const response = await axios.get(`${this.$apiBaseUrl}/product/getoutboundauditstatusoptions`)
            this.auditStatusOptions = response.data.productOutboundAuditStatusOptions
            this.PRODUCT_OUTBOUND_AUDIT_STATUS_ENUM = response.data.productOutboundAuditStatusEnum
        },
        displayOrdersbyRole() {
            // 默认展示
            this.storageStatusNum = this.FINISHED_STORAGE_STATUS_ENUM.PRODUCT_INBOUND_FINISHED
            this.auditStatusNum = this.PRODUCT_OUTBOUND_AUDIT_STATUS_ENUM.ALL

            // 业务：默认只看“未发起审核”订单
            if (this.role == 4 || this.role == 21) {
                this.storageStatusNum = this.FINISHED_STORAGE_STATUS_ENUM.ALL
                this.auditStatusNum = this.PRODUCT_OUTBOUND_AUDIT_STATUS_ENUM.PRODUCT_OUTBOUND_AUDIT_NOT_INIT
            }
            // 仓库：默认看“入库完成 + 出库审核通过”订单
            else if (this.role == 20) {
                this.storageStatusNum = this.FINISHED_STORAGE_STATUS_ENUM.PRODUCT_INBOUND_FINISHED
                this.auditStatusNum = this.PRODUCT_OUTBOUND_AUDIT_STATUS_ENUM.PRODUCT_OUTBOUND_AUDIT_APPROVED
            }
        },

        // ====== 通用表格 / 分页 ======
        toggleSelectionMode() {
            this.isMultipleSelection = !this.isMultipleSelection
            this.selectedRows = []
        },
        handleSelectionChange(selection) {
            this.selectedRows = selection
        },
        handleSizeChange(val) {
            this.pageSize = val
            this.getTableData()
        },
        handlePageChange(val) {
            this.currentPage = val
            this.getTableData()
        },

        // 业务明细分页事件
        handleBusinessSizeChange(val) {
            this.businessPageSize = val
            this.businessCurrentPage = 1
        },
        handleBusinessPageChange(val) {
            this.businessCurrentPage = val
        },

        // ====== 后端查询 ======
        async getTableData() {
            const outboundFinishedStatus =
                this.FINISHED_STORAGE_STATUS_ENUM && this.FINISHED_STORAGE_STATUS_ENUM.PRODUCT_OUTBOUND_FINISHED
            const shouldIgnoreAuditFilter =
                outboundFinishedStatus != null && this.storageStatusNum === outboundFinishedStatus
            const auditStatusEnum = this.PRODUCT_OUTBOUND_AUDIT_STATUS_ENUM || {}
            const effectiveAuditStatusNum = shouldIgnoreAuditFilter ? auditStatusEnum.ALL : this.auditStatusNum
            const params = {
                page: this.currentPage,
                pageSize: this.pageSize,
                orderRId: this.orderNumberSearch,
                orderCId: this.orderCIdSearch,
                customerName: this.customerNameSearch,
                customerBrand: this.customerBrandSearch,
                auditStatusNum: effectiveAuditStatusNum,
                storageStatusNum: this.storageStatusNum
            }
            const response = await axios.get(`${this.$apiBaseUrl}/warehouse/getproductoverview`, { params })
            const outboundFinishedValue = outboundFinishedStatus
            let result = response.data.result || []
            if (this.isBusinessRole && outboundFinishedValue != null) {
                result = result.filter((row) => row.storageStatusNum !== outboundFinishedValue)
            }
            this.tableData = result
            this.totalRows = response.data.total || 0
        },

        handleStorageStatusChange() {
            const outboundFinishedStatus =
                this.FINISHED_STORAGE_STATUS_ENUM && this.FINISHED_STORAGE_STATUS_ENUM.PRODUCT_OUTBOUND_FINISHED
            const auditStatusEnum = this.PRODUCT_OUTBOUND_AUDIT_STATUS_ENUM || {}
            if (
                outboundFinishedStatus != null &&
                this.storageStatusNum === outboundFinishedStatus &&
                auditStatusEnum.ALL !== undefined
            ) {
                this.auditStatusNum = auditStatusEnum.ALL
            }
            this.getTableData()
        },

        // ====== 前置校验（目前仓库用） ======
        async checkOutboundPrequisite() {
            if (this.selectedRows.length === 0) {
                ElMessage.error('未选择订单')
                return false
            }
            const unfinishedOrders = this.selectedRows.filter((row) => row.currentStock + row.outboundedAmount < row.orderAmount).map((row) => row.orderRId)
            if (unfinishedOrders.length > 0) {
                try {
                    await ElMessageBox.alert(`以下订单未完成入库: ${unfinishedOrders.join(', ')}，是否继续`, '警告', {
                        confirmButtonText: '确认',
                        showCancelButton: true,
                        cancelButtonText: '取消'
                    })
                    return true
                } catch (e) {
                    ElMessage.info('操作已取消')
                    return false
                }
            }
            return true
        },

        // ====== 业务：打开配码+比例填写对话框（新建，多订单版） ======
        openBusinessDialog() {
            if (this.selectedRows.length === 0) {
                ElMessage.error('未选择订单')
                return
            }
            for (const row of this.selectedRows) {
                if (row.storageStatusNum === this.FINISHED_STORAGE_STATUS_ENUM.PRODUCT_OUTBOUND_FINISHED) {
                    ElMessage.error(`订单 ${row.orderRId} 已完成出库，无法再次申请`)
                    return
                }
            }
            if (!(this.role == 4 || this.role == 21)) {
                ElMessage.error('当前角色不可填写出库申请')
                return
            }

            // 多订单一起申请：取第一个订单作为“主订单”（apply 表头用）
            const orderIds = [...new Set(this.selectedRows.map((r) => r.orderId))]
            const mainOrderId = orderIds[0]

            this.businessForm.applyId = null
            this.businessForm.orderId = mainOrderId
            this.businessForm.remark = ''
            this.businessForm.items = []
            this.businessForm.sizeColumns = []
            this.businessCurrentPage = 1 // 打开时回到第一页

            const sizeLabelSet = new Set()

            // 遍历所有选中的订单，一起生成明细
            this.selectedRows.forEach((orderRow) => {
                const orderRId = orderRow.orderRId
                const orderId = orderRow.orderId

                ;(orderRow.orderShoeTable || []).forEach((colorRow) => {
                    const sizeColumns = colorRow.sizeColumns || []
                    const batchInfos = colorRow.batchInfos || []

                    batchInfos.forEach((bi) => {
                        const sizeRatiosMap = {}
                        const packagingQty = Number(bi.packagingInfoQuantity || 0)

                        // 算各鞋码的比例
                        sizeColumns.forEach((sc) => {
                            const label = sc.label
                            const prop = sc.prop
                            const sizeTotal = Number(bi[prop] || 0)

                            if (!label) return

                            let ratio = sizeTotal
                            if (packagingQty > 0) {
                                ratio = sizeTotal / packagingQty
                            }

                            if (ratio > 0) {
                                sizeRatiosMap[label] = Number(ratio)
                                sizeLabelSet.add(label)
                            }
                        })

                        let pairsPerCarton = Number(bi.pairsPerCarton || 0)
                        if (!pairsPerCarton) {
                            pairsPerCarton = Object.values(sizeRatiosMap).reduce((sum, v) => sum + Number(v || 0), 0)
                        }

                        const batchStock = Number(bi.batchAvailableAmount || 0)
                        const totalOrderPairs = Number(bi.totalAmount || 0)
                        let defaultCartons = 0
                        if (pairsPerCarton > 0 && totalOrderPairs > 0) {
                            defaultCartons = totalOrderPairs / pairsPerCarton
                        } else if (pairsPerCarton > 0 && batchStock > 0) {
                            defaultCartons = batchStock / pairsPerCarton
                        }
                        const defaultPairs = totalOrderPairs > 0 ? totalOrderPairs : defaultCartons * pairsPerCarton

                        this.businessForm.items.push({
                            // 关键：明细里带上自己对应的订单
                            orderId,
                            orderRId,

                            shoeRId: colorRow.shoeRId,
                            customerProductName: colorRow.customerProductName,
                            colorName: colorRow.colorName,

                            storageId: colorRow.storageId, // finished_shoe_storage_id
                            orderShoeTypeId: colorRow.orderShoeTypeId,
                            batchInfoId: bi.batchInfoId,
                            batchName: bi.batchName || bi.name,
                            packagingInfoId: bi.packagingInfoId,
                            packagingInfoName: bi.packagingInfoName,

                            sizeRatiosMap,
                            batchStock,
                            pairsPerCarton,
                            applyCartons: defaultCartons,
                            applyPairs: defaultPairs,

                            remark: ''
                        })
                    })
                })
            })

            if (this.businessForm.items.length === 0) {
                ElMessage.warning('所选订单暂无配码信息，无法填写出库申请')
                return
            }

            // 生成对话框的“动态鞋码列”
            this.businessForm.sizeColumns = Array.from(sizeLabelSet)
                .sort((a, b) => {
                    const na = parseInt(a, 10)
                    const nb = parseInt(b, 10)
                    if (!isNaN(na) && !isNaN(nb)) return na - nb
                    return String(a).localeCompare(String(b))
                })
                .map((label) => ({
                    key: label,
                    label
                }))

            this.isBusinessDialogVisible = true
        },

        updateBusinessPairs(row) {
            const cartons = Number(row.applyCartons || 0)
            const perCarton = Number(row.pairsPerCarton || 0)
            row.applyPairs = cartons * perCarton
        },

        // ====== 业务：提交出库申请（新建 / 编辑） => /warehouse/outbound-apply/save ======
        async submitBusinessForm() {
            const hasPositive = this.businessForm.items.some((it) => it.applyCartons > 0)
            if (!hasPositive) {
                ElMessage.error('请至少为一个配码填写申请箱数')
                return
            }

            const orderId = this.businessForm.orderId || (this.businessForm.items[0] && this.businessForm.items[0].orderId)
            if (!orderId) {
                ElMessage.error('缺少订单信息，无法提交')
                return
            }

            const payload = {
                applyId: this.businessForm.applyId, // 新建时为 null，编辑时有值
                orderId, // 主订单
                status: 1, // 直接提交审核（0=草稿，1=提交）
                remark: this.businessForm.remark,
                expectedOutboundTime: this.businessForm.expectedOutboundTime || null,
                details: this.businessForm.items
                    .filter((it) => it.applyCartons > 0 && it.applyPairs > 0)
                    .map((it) => ({
                        // 编辑时可选带入 applyDetailId
                        applyDetailId: it.applyDetailId,
                        // 这些字段后端仍按原逻辑用来确定库存/配码
                        finishedShoeStorageId: it.storageId,
                        orderShoeTypeId: it.orderShoeTypeId,
                        orderShoeBatchInfoId: it.batchInfoId,
                        packagingInfoId: it.packagingInfoId,
                        cartonCount: it.applyCartons,
                        pairsPerCarton: it.pairsPerCarton,
                        totalPairs: it.applyPairs,
                        remark: it.remark
                    }))
            }

            if (!payload.details.length) {
                ElMessage.error('请至少为一条明细填写有效的申请箱数')
                return
            }

            try {
                const res = await axios.post(`${this.$apiBaseUrl}/warehouse/outbound-apply/save`, payload)
                ElMessage.success(res.data.message || '出库申请已提交')
                this.isBusinessDialogVisible = false
                this.getTableData()
            } catch (e) {
                console.error(e)
                const msg = e.response?.data?.message || e.response?.data?.error || '提交出库申请失败'
                ElMessage.error(msg)
            }
        },

        // ====== 仓库：尺码明细对话框（保留旧逻辑） ======
        updateTotalShoes() {
            if (!this.currentQuantityRow || !this.currentQuantityRow.shoesOutboundTable) return
            this.currentQuantityRow.shoesOutboundTable.forEach((element, index) => {
                this.currentQuantityRow[`amount${index}`] = element.operationQuantity
            })
            this.currentQuantityRow.operationQuantity = this.filteredData.reduce((acc, row) => {
                return acc + (row.operationQuantity || 0)
            }, 0)
        },
        openQuantityDialog(row) {
            this.currentQuantityRow = row
            this.isOpenQuantityDialogVisible = true
        },
        async getShoeSizeColumnsForOrder(row) {
            const params = { orderId: row.orderId }
            const response = await axios.get(`${this.$apiBaseUrl}/warehouse/getmultipleshoesizecolumns`, { params })
            return response
        },
        async openShoeSizeDialog(row) {
            this.currentRow = row
            const response = await this.getShoeSizeColumnsForOrder(row)
            const targetedStorageStock = response.data
            for (let i = 0; i < row.orderShoeTable.length; i++) {
                row.orderShoeTable[i].shoesOutboundTable = targetedStorageStock[row.orderShoeTable[i].storageId]
            }
            this.activeStockTab = row.orderShoeTable[0].orderShoeTypeId
            this.isOpenShoeSizeDialogVisible = true
        },

        // ====== 仓库：确认出库 ======
        openWarehouseOutboundDialog() {
            if (this.selectedRows.length === 0) {
                ElMessage.error('未选择订单')
                return
            }
            for (const row of this.selectedRows) {
                if (row.auditStatusNum !== this.PRODUCT_OUTBOUND_AUDIT_STATUS_ENUM.PRODUCT_OUTBOUND_AUDIT_APPROVED) {
                    ElMessage.error('存在未审批通过的订单，无法出库')
                    return
                }
            }
            const unfinishedInbound = this.selectedRows.filter(
                (row) => row.storageStatusNum !== this.FINISHED_STORAGE_STATUS_ENUM.PRODUCT_INBOUND_FINISHED
            )
            if (unfinishedInbound.length > 0) {
                ElMessage.error('存在未完成入库的订单，成品仓需等入库完成后才能出库')
                return
            }
            this.currentOperation = 1
            this.groupSelectedRowsForWarehouse()
            this.isOutboundDialogVisible = true
        },
        async groupSelectedRowsForWarehouse() {
            const selectedRowsCopy = JSON.parse(JSON.stringify(this.selectedRows))
            this.outboundForm = JSON.parse(JSON.stringify(this.formItemTemplate))
            this.outboundForm.items = []
            for (let i = 0; i < selectedRowsCopy.length; i++) {
                for (let j = 0; j < selectedRowsCopy[i].orderShoeTable.length; j++) {
                    const orderShoe = selectedRowsCopy[i].orderShoeTable[j]
                    // 默认全部库存出库（最大可出库数量）
                    orderShoe.outboundQuantity = orderShoe.currentStock
                    orderShoe.remark = null
                    this.outboundForm.items.push({
                        ...orderShoe,
                        orderRId: selectedRowsCopy[i].orderRId,
                        orderId: selectedRowsCopy[i].orderId
                    })
                }
            }
        },
        async submitOperationForm() {
            try {
                await axios.patch(`${this.$apiBaseUrl}/warehouse/warehousemanager/outboundfinished`, this.outboundForm)
                ElMessage.success('出库成功')
            } catch (error) {
                console.error(error)
                const errorMessage = error.response ? error.response.data.message : '操作异常'
                ElMessage.error(errorMessage)
            }
            this.isOutboundDialogVisible = false
            this.getTableData()
        },

        // ====== 出库申请列表 ======
        openApplyListDialog() {
            this.isApplyListDialogVisible = true
            this.applyCurrentPage = 1
            this.getApplyList()
        },
        async getApplyList() {
            const params = {
                page: this.applyCurrentPage,
                pageSize: this.applyPageSize,
                orderRId: this.applyFilters.orderRId || undefined,
                applyRId: this.applyFilters.applyRId || undefined,
                customerName: this.applyFilters.customerName || undefined,
                status: this.applyFilters.status != null ? this.applyFilters.status : undefined
            }
            const res = await axios.get(`${this.$apiBaseUrl}/warehouse/outbound-apply/list`, { params })
            this.applyTableData = res.data.result || []
            this.applyTotalRows = res.data.total || 0
        },
        handleApplySizeChange(val) {
            this.applyPageSize = val
            this.applyCurrentPage = 1
            this.getApplyList()
        },
        handleApplyPageChange(val) {
            this.applyCurrentPage = val
            this.getApplyList()
        },

        // 是否可以编辑出库申请：仅业务角色 + 状态为草稿/驳回
        canEditApply(row) {
            if (!(this.role == 4 || this.role == 21)) return false
            return row.status === 0 || row.status === 2
        },

        // 从申请列表中编辑已有出库申请
        async editApply(row) {
            if (!this.canEditApply(row)) return
            try {
                const res = await axios.get(`${this.$apiBaseUrl}/warehouse/outbound-apply/detail`, { params: { applyId: row.applyId } })
                const { header, details } = res.data || {}

                if (!header) {
                    ElMessage.error('未获取到申请单头信息')
                    return
                }
                this.businessForm.expectedOutboundTime = header.expectedOutboundTime || ''
                this.businessForm.applyId = header.applyId
                this.businessForm.orderId = header.orderId
                this.businessForm.remark = header.remark || ''
                this.businessForm.items = []
                this.businessForm.sizeColumns = [] // 编辑模式不再关心配码比例列
                this.businessCurrentPage = 1
                ;(details || []).forEach((d) => {
                    this.businessForm.items.push({
                        applyDetailId: d.applyDetailId,
                        orderId: header.orderId, // 编辑时保留主订单
                        orderRId: header.orderRId,
                        shoeRId: d.shoeRId,
                        customerProductName: d.customerProductName,
                        colorName: d.colorName,

                        storageId: d.finishedShoeStorageId,
                        orderShoeTypeId: d.orderShoeTypeId,
                        batchInfoId: d.orderShoeBatchInfoId,
                        batchName: d.batchName,
                        packagingInfoId: d.packagingInfoId,
                        packagingInfoName: d.packagingInfoName,

                        // 编辑时不再展示鞋码比例
                        sizeRatiosMap: {},
                        batchStock: d.currentStock,
                        pairsPerCarton: d.pairsPerCarton || 0,
                        applyCartons: d.cartonCount || 0,
                        applyPairs: d.totalPairs || 0,

                        remark: d.remark || ''
                    })
                })

                if (!this.businessForm.items.length) {
                    ElMessage.warning('该申请单暂无明细，无法编辑')
                    return
                }

                this.isApplyListDialogVisible = false
                this.isBusinessDialogVisible = true
            } catch (e) {
                console.error(e)
                const msg = e.response?.data?.message || e.response?.data?.error || '加载申请单失败'
                ElMessage.error(msg)
            }
        },

        async openOrderPendingApplyDialog(row) {
            this.pendingApplyOrderRId = row.orderRId
            this.isOrderPendingApplyDialogVisible = true
            try {
                const params = {
                    page: 1,
                    pageSize: 100,
                    orderRId: row.orderRId
                }
                const res = await axios.get(`${this.$apiBaseUrl}/warehouse/outbound-apply/list`, { params })
                const all = res.data.result || []
                // 1 = 待总经理审核, 3 = 待仓库出库，都算“正在流转中的单”
                this.orderPendingApplyList = all.filter((it) => it.status === 1 || it.status === 3)
            } catch (e) {
                console.error(e)
                ElMessage.error('加载该订单的出库申请失败')
                this.orderPendingApplyList = []
            }
        }
    }
}
</script>

<style scoped>
.mt-2 {
    margin-top: 8px;
}
.mt-3 {
    margin-top: 12px;
}
.search-input + .search-input {
    margin-left: 8px;
}
</style>
