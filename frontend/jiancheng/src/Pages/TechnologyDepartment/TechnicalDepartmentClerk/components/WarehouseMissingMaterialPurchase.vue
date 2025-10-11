<template>
    <div class="page p-4">
        <!-- 顶部工具栏：筛选 + 刷新 + 补采中订单入口 -->
        <el-card shadow="never" class="mb-3">
            <el-form :inline="true" :model="query" @submit.prevent>
                <el-form-item label="订单搜索">
                    <el-input v-model.trim="query.keyword" placeholder="订单号/客户/鞋型…" style="width: 280px" clearable @keyup.enter.native="loadOrders" />
                </el-form-item>
                <el-form-item label="下发日期">
                    <el-date-picker v-model="query.dates" type="daterange" start-placeholder="开始日期" end-placeholder="结束日期" value-format="YYYY-MM-DD" />
                </el-form-item>
                <el-form-item>
                    <el-button type="primary" :loading="loading" @click="reload">查询</el-button>
                    <el-button @click="reset">清空</el-button>
                </el-form-item>
                <div class="toolbar-right">
                    <el-badge :value="inProgressCount" :type="inProgressCount > 0 ? 'danger' : 'info'" class="mr-2">
                        <el-button type="warning" plain @click="openInProgressDialog">补采流程中</el-button>
                    </el-badge>
                    <el-switch v-model="onlyPending" active-text="仅看有待处理补采" class="mr-2" />
                    <el-button :loading="loading" @click="loadOrders" icon="Refresh">刷新</el-button>
                </div>
            </el-form>
        </el-card>

        <!-- 主列表卡片：已下发到总仓（且非补采流程中的订单） -->
        <el-card shadow="never" class="card-fill">
            <template #header>
                <div class="flex items-center justify-between">
                    <span>已下发到总仓的订单（{{ total }}）</span>
                    <small class="muted">（列表已排除正在补采流程中的订单）</small>
                </div>
            </template>

            <el-table :data="tableData" border stripe v-loading="loading" size="small" @sort-change="onSortChange">
                <el-table-column type="index" label="#" width="60" />
                <el-table-column prop="orderRid" label="订单号" min-width="140" sortable="custom">
                    <template #default="{ row }">
                        <el-link type="primary" @click="viewOrder(row)">{{ row.orderRid }}</el-link>
                    </template>
                </el-table-column>
                <el-table-column prop="customerName" label="客户" min-width="140" />
                <el-table-column prop="customerProductName" label="客户鞋型" min-width="160" show-overflow-tooltip />
                <el-table-column prop="brand" label="品牌" width="120" />
                <el-table-column prop="issueDate" label="下发日期" width="140" sortable="custom" />
                <el-table-column prop="warehouseStatus" label="总仓状态" width="120">
                    <template #default="{ row }">
                        <el-tag :type="row.warehouseStatusTag">{{ row.warehouseStatusText }}</el-tag>
                    </template>
                </el-table-column>
                <el-table-column prop="pendingRequestCount" label="待处理补采" width="110" align="center">
                    <template #default="{ row }">
                        <span v-if="row.pendingRequestCount > 0" class="text-red-500 font-bold">{{ row.pendingRequestCount }}</span>
                        <span v-else class="text-gray-400">0</span>
                    </template>
                </el-table-column>
                <el-table-column fixed="right" label="操作" width="260">
                    <template #default="{ row }">
                        <el-button type="primary" size="small" @click="openRequestDialog(row)">补采请求</el-button>
                        <el-button size="small" @click="viewHistory(row)">历史</el-button>
                        <el-button size="small" type="success" plain @click="openEditMaterials(row)">材料修改</el-button>
                    </template>
                </el-table-column>
            </el-table>

            <div class="mt-3 flex items-center justify-end">
                <el-pagination
                    background
                    layout="total, sizes, prev, pager, next, jumper"
                    :total="total"
                    :current-page="pagination.page"
                    :page-size="pagination.pageSize"
                    :page-sizes="[10, 20, 50, 100]"
                    @size-change="onPageSizeChange"
                    @current-change="onPageChange"
                />
            </div>
        </el-card>

        <!-- 补采请求对话框（75% 宽度 + 颜色 Tab） -->
        <el-dialog v-model="requestDialog.visible" :title="'补采请求 - ' + (requestDialog.order?.orderRid || '')" width="75%" :close-on-click-modal="false">
            <el-form ref="requestFormRef" :model="requestForm" :rules="requestRules" label-width="92px">
                <el-row :gutter="12">
                    <el-col :span="12">
                        <el-form-item label="需求原因" prop="reason">
                            <el-select v-model="requestForm.reason" placeholder="选择原因" filterable>
                                <el-option label="原计划不足" value="不足" />
                                <el-option label="品质问题退换" value="退换" />
                                <el-option label="新增尺码/颜色" value="新增" />
                                <el-option label="其他" value="其他" />
                            </el-select>
                        </el-form-item>
                    </el-col>
                </el-row>

                <el-form-item label="备注">
                    <el-input v-model.trim="requestForm.remark" placeholder="补充说明(可选)" maxlength="200" show-word-limit />
                </el-form-item>

                <el-divider content-position="left">鞋型颜色</el-divider>
                <div class="flex items-center gap-2 mb-2">
                    <el-select
                        v-model="selectedColor"
                        value-key="id"
                        placeholder="选择鞋型颜色"
                        style="width: 240px"
                        :loading="shoeColorsLoading"
                        :disabled="shoeColorsLoading || !shoeColorOptions.length"
                    >
                        <el-option v-for="c in shoeColorOptions" :key="c.id ?? c.orderShoeTypeId ?? c.name" :label="c.name || c" :value="c" />
                    </el-select>
                    <el-button type="primary" :disabled="!selectedColor" @click="addColorTab">添加颜色</el-button>
                </div>

                <el-tabs v-model="activeColor" type="card" closable @tab-remove="removeColorTab">
                    <el-tab-pane v-for="tab in requestForm.colorTabs" :key="tab.key" :name="tab.key" :label="tab.color">
                        <el-divider content-position="left">材料明细 - {{ tab.color }}</el-divider>
                        <el-table :data="tab.items" border style="width: 100%">
                            <el-table-column type="index" width="48" />
                            <el-table-column prop="materialCategory" label="材料大类" width="120">
                                <template #default="{ row }">
                                    <el-select v-model="row.materialCategory" placeholder="选择" style="width: 100%">
                                        <el-option v-for="opt in materialCategoryOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
                                    </el-select>
                                </template>
                            </el-table-column>
                            <el-table-column prop="supplierName" label="厂家名称" min-width="180">
                                <template #default="{ row }">
                                    <el-select v-model="row.supplierName" filterable clearable placeholder="请选择厂家" style="width: 100%">
                                        <el-option v-for="item in supplierNameOptions" :key="item.supplierName" :value="item.supplierName" :label="item.supplierName" />
                                    </el-select>
                                </template>
                            </el-table-column>
                            <el-table-column prop="materialName" label="材料名称" min-width="220">
                                <template #default="{ row }">
                                    <el-select
                                        v-model="row.materialName"
                                        filterable
                                        placeholder="请选择或搜索材料名称"
                                        style="width: 100%"
                                        @change="(val) => handleMaterialNameSelect(row, val)"
                                        @blur="trimInput(row, 'materialName')"
                                    >
                                        <el-option v-for="opt in filterByTypes(materialNameOptions, getTypesByCategory(row.materialCategory))" :key="opt.value" :label="opt.label" :value="opt.value" />
                                    </el-select>
                                </template>
                            </el-table-column>
                            <el-table-column prop="materialModel" label="材料型号" min-width="160">
                                <template #default="{ row }">
                                    <el-autocomplete
                                        v-model="row.materialModel"
                                        :fetch-suggestions="(queryString, cb) => querySearchModel(0, row, queryString, cb)"
                                        @blur="trimInput(row, 'materialModel')"
                                        placeholder=""
                                        show-word-limit
                                    />
                                </template>
                            </el-table-column>
                            <el-table-column prop="materialSpecification" label="材料规格" min-width="200">
                                <template #default="{ row }">
                                    <el-autocomplete
                                        v-model="row.materialSpecification"
                                        :fetch-suggestions="(queryString, cb) => querySearchModel(1, row, queryString, cb)"
                                        type="textarea"
                                        autosize
                                        placeholder=""
                                        @blur="trimInput(row, 'materialSpecification')"
                                        show-word-limit
                                    />
                                </template>
                            </el-table-column>
                            <el-table-column prop="materialColor" label="材料颜色" width="120">
                                <template #default="{ row }">
                                    <el-input v-model="row.materialColor" @blur="validateColor(row)" />
                                </template>
                            </el-table-column>
                            <el-table-column label="操作" width="120" fixed="right">
                                <template #default="{ $index }">
                                    <el-button type="danger" size="small" @click="removeItem($index)">删除</el-button>
                                </template>
                            </el-table-column>
                        </el-table>

                        <div class="mt-2">
                            <el-button @click="addItem" icon="Plus">在“{{ tab.color }}”下新增一行</el-button>
                            <el-button @click="importFromBom" icon="Document">从二次BOM导入</el-button>
                            <el-button type="danger" link @click="removeColorTab(tab.key)">删除该颜色</el-button>
                        </div>
                    </el-tab-pane>
                </el-tabs>
            </el-form>

            <template #footer>
                <span class="dialog-footer">
                    <el-button @click="requestDialog.visible = false">取 消</el-button>
                    <el-button type="primary" :loading="requestDialog.submitting" @click="submitRequest">提 交</el-button>
                </span>
            </template>
        </el-dialog>

        <!-- 补采流程中订单对话框 -->
        <el-dialog v-model="inProgressDialog.visible" title="补采流程中订单" width="75%" :close-on-click-modal="false">
            <el-table :data="inProgressList" border stripe size="small" v-loading="inProgressDialog.loading">
                <el-table-column type="index" width="52" />
                <el-table-column prop="orderRid" label="订单号" min-width="140">
                    <template #default="{ row }">
                        <el-link type="primary" @click="viewOrder(row)">{{ row.orderRid }}</el-link>
                    </template>
                </el-table-column>
                <el-table-column prop="customerName" label="客户" min-width="140" />
                <el-table-column prop="stageText" label="流程阶段" width="140" />
                <el-table-column prop="requester" label="发起人" width="120" />
                <el-table-column prop="createdAt" label="发起时间" width="160" />
                <el-table-column prop="pendingNodeText" label="当前待办" width="160" />
                <el-table-column fixed="right" label="操作" width="160">
                    <template #default="{ row }">
                        <el-button size="small" @click="openSupplementDetail(row)">查看详情</el-button>
                    </template>
                </el-table-column>
            </el-table>

            <div class="mt-3 flex items-center justify-end">
                <el-pagination
                    background
                    layout="total, prev, pager, next"
                    :total="inProgressPager.total"
                    :current-page="inProgressPager.page"
                    :page-size="inProgressPager.pageSize"
                    @current-change="onInProgressPageChange"
                />
            </div>

            <template #footer>
                <el-button @click="inProgressDialog.visible = false">关 闭</el-button>
            </template>
        </el-dialog>

        <!-- 补采记录详情对话框 -->
        <el-dialog v-model="detailDialog.visible" title="补采记录详情" width="75%" :close-on-click-modal="false">
            <div v-loading="detailDialog.loading">
                <el-descriptions :column="3" border v-if="detailDialog.record">
                    <el-descriptions-item label="订单号">{{ detailDialog.record.orderRid }}</el-descriptions-item>
                    <el-descriptions-item label="客户">{{ detailDialog.record.customerName }}</el-descriptions-item>
                    <el-descriptions-item label="状态">{{ detailDialog.record.stageText }}</el-descriptions-item>
                    <el-descriptions-item label="创建时间">{{ detailDialog.record.createdAt }}</el-descriptions-item>
                    <el-descriptions-item label="原因">{{ detailDialog.record.reason || '-' }}</el-descriptions-item>
                    <el-descriptions-item label="备注" :span="3">{{ detailDialog.record.remark || '-' }}</el-descriptions-item>
                </el-descriptions>

                <el-divider>明细</el-divider>
                <el-table :data="detailDialog.items" border stripe size="small">
                    <el-table-column type="index" width="52" />
                    <el-table-column prop="shoeColorName" label="鞋型颜色" width="120" />
                    <el-table-column prop="materialTypeText" label="材料大类" width="120" />
                    <el-table-column prop="materialName" label="材料名称" width="120" />
                    <el-table-column prop="materialModel" label="型号" min-width="140" />
                    <el-table-column prop="materialSpecification" label="规格" min-width="180" />
                    <el-table-column prop="color" label="材料颜色" width="120" />
                    <el-table-column prop="unitUsage" label="申请用量" width="120" />
                    <el-table-column prop="approvalUsage" label="核定用量" width="120" />
                    <el-table-column prop="purchaseAmount" label="采购数量" width="120" />
                </el-table>
            </div>
            <template #footer>
                <el-button @click="detailDialog.visible = false">关 闭</el-button>
            </template>
        </el-dialog>
    </div>
</template>

<script setup lang="ts">
const API = {
    CENTRAL_ORDERS: '/missing_material_purchase/getwarehouseorders',
    SUPPLEMENT_INPROGRESS: '/missing_material_purchase/inprogress',
    SUPPLEMENT_INPROGRESS_SUMMARY: '/missing_material_purchase/inprogress/summary',
    MATERIAL_SEARCH: '/api/material/search',
    CREATE_REQUEST: '/missing_material_purchase/request',
    SHOE_COLORS: '/missing_material_purchase/shoe_colors'
}

import { onMounted, reactive, ref, getCurrentInstance } from 'vue'
import { ElMessage, FormInstance, FormRules } from 'element-plus'
import axios from 'axios'
import { useRouter } from 'vue-router'

const router = useRouter()
const apiBaseUrl = getCurrentInstance().appContext.config.globalProperties.$apiBaseUrl

// ===== 查询条件 & 列表状态（非补采中） =====
const query = reactive({
    keyword: '',
    dates: [] as [string, string] | [],
    sort: { prop: 'issueDate', order: 'desc' as 'asc' | 'desc' }
})
const pagination = reactive({ page: 1, pageSize: 10 })
const loading = ref(false)
const onlyPending = ref(false)
const total = ref(0)
const tableData = ref<any[]>([])

// ===== 补采流程中订单入口（计数 + 列表） =====
const inProgressCount = ref<number>(0)
const inProgressDialog = reactive({ visible: false, loading: false })
const inProgressList = ref<any[]>([])
const inProgressPager = reactive({ page: 1, pageSize: 10, total: 0 })

// ===== 补采记录详情对话框 =====
const detailDialog = reactive({ visible: false, loading: false, record: null as any, items: [] as any[] })

function openInProgressDialog() {
    inProgressDialog.visible = true
    inProgressPager.page = 1
    loadInProgressList()
}

async function loadInProgressSummary() {
    try {
        const { data } = await axios.get(`${apiBaseUrl}${API.SUPPLEMENT_INPROGRESS_SUMMARY}`)
        inProgressCount.value = data?.count || 0
    } catch {
        inProgressCount.value = 0
    }
}

async function loadInProgressList() {
    inProgressDialog.loading = true
    try {
        const params = { page: inProgressPager.page, pageSize: inProgressPager.pageSize }
        const { data } = await axios.get(`${apiBaseUrl}${API.SUPPLEMENT_INPROGRESS}`, { params })
        inProgressList.value = (data?.list || []).map((r: any) => ({
            id: r.id || r.record_id || r.recordId, // <== 详情需要
            orderRid: r.order_rid || r.orderRid,
            customerName: r.customer_name || r.customerName,
            stageText: r.stage_text || r.stageText,
            requester: r.requester || r.created_by_name,
            createdAt: r.created_at || r.createdAt,
            pendingNodeText: r.pending_node_text || r.pendingNodeText,
            orderId: r.order_id || r.orderId
        }))
        inProgressPager.total = data?.total || 0
    } catch (e: any) {
        ElMessage.error(e?.message || '加载补采流程中的订单失败')
    } finally {
        inProgressDialog.loading = false
    }
}

function onInProgressPageChange(p: number) {
    inProgressPager.page = p
    loadInProgressList()
}

// 加载补采记录详情
async function loadRecordDetail(recordId: number) {
    try {
        const { data } = await axios.get(`${apiBaseUrl}/missing_material_purchase/record_detail`, { params: { id: recordId } })
        detailDialog.record = data?.record || null
        detailDialog.items = data?.items || []
    } catch (e: any) {
        ElMessage.error(e?.message || '加载详情失败')
    }
}

// ===== 列表交互 =====
function reload() {
    pagination.page = 1
    loadOrders()
}
function reset() {
    query.keyword = ''
    query.dates = []
    onlyPending.value = false
    reload()
}
function onPageChange(p: number) {
    pagination.page = p
    loadOrders()
}
function onPageSizeChange(sz: number) {
    pagination.pageSize = sz
    reload()
}
function onSortChange({ prop, order }: any) {
    if (!prop) return
    query.sort.prop = prop
    query.sort.order = order === 'ascending' ? 'asc' : 'desc'
    reload()
}

async function loadOrders() {
    loading.value = true
    try {
        const params: any = {
            page: pagination.page,
            pageSize: pagination.pageSize,
            keyword: query.keyword || undefined,
            startDate: Array.isArray(query.dates) && query.dates[0] ? query.dates[0] : undefined,
            endDate: Array.isArray(query.dates) && query.dates[1] ? query.dates[1] : undefined,
            sortProp: query.sort.prop,
            sortOrder: query.sort.order,
            issuedToCentral: 1,
            onlyPending: onlyPending.value ? 1 : 0,
            excludeInProgress: 1
        }
        const { data } = await axios.get(`${apiBaseUrl}${API.CENTRAL_ORDERS}`, { params })
        tableData.value = (data?.list || []).map((r: any) => normalizeRow(r))
        total.value = data?.total || 0
    } catch (e: any) {
        console.error(e)
        ElMessage.error(e?.message || '加载失败')
    } finally {
        loading.value = false
    }
}

function normalizeRow(r: any) {
    return {
        orderRid: r.order_rid || r.orderRid,
        customerName: r.customer_name || r.customerName,
        customerProductName: r.customer_product_name || r.customerProductName,
        brand: r.customer_brand || r.brand,
        issueDate: r.issue_date || r.issueDate,
        warehouseStatusText: r.warehouse_status_text || r.warehouseStatusText || '已下发',
        warehouseStatusTag: r.warehouse_status_tag || r.warehouseStatusTag || 'success',
        pendingRequestCount: r.pending_request_count ?? 0,
        orderId: r.order_id || r.orderId,
        orderShoeId: r.order_shoe_id || r.orderShoeId,
        orderShoeTypeId: r.order_shoe_type_id || r.orderShoeTypeId
    }
}

// ===== 行操作 =====
function viewOrder(row: any) {
    /* 可跳转至订单详情页 */
}
function viewHistory(row: any) {
    /* 打开历史记录 */
}
function openSupplementDetail(row: any) {
    if (!row?.id) {
        ElMessage.warning('缺少记录ID')
        return
    }
    detailDialog.visible = true
    detailDialog.loading = true
    loadRecordDetail(row.id).finally(() => (detailDialog.loading = false))
}
function openEditMaterials(row: any) {
    try {
        router.push({ name: 'OrderMaterialEdit', params: { orderId: row.orderId } })
    } catch {
        router.push(`/orders/${row.orderId}/materials-edit`).catch(() => {})
    }
}

// ===== 补采请求（颜色 Tab 结构） =====
const requestDialog = reactive({ visible: false, submitting: false, order: null as any })
const unitOptions = ['米', '码', '张', '卷', '双', '个', '箱', '包', 'KG', 'G']
const materialCategoryOptions = [
    { label: '面料', value: 'surface' },
    { label: '里料', value: 'lining' },
    { label: '辅料', value: 'accessory' },
    { label: '大底', value: 'outsole' },
    { label: '中底', value: 'midsole' },
    { label: '烫底', value: 'hotmelt' }
]

interface RequestRow {
    materialCategory?: string
    materialName?: string
    supplierName?: string
    materialModel?: string
    materialSpecification?: string
    materialColor?: string
    comment?: string
    processingRemark?: string
    quantity?: number | null
    unit?: string
    materialId?: number
    spuMaterialId?: number
}

interface ColorTab {
    key: string
    color: string
    orderShoeTypeId: number | null
    items: RequestRow[]
}

const requestFormRef = ref<FormInstance>()
const requestForm = reactive({
    orderId: 0,
    orderShoeId: 0,
    orderShoeTypeId: 0,
    reason: '',
    expectDate: '',
    remark: '',
    colorTabs: [] as ColorTab[]
})
const activeColor = ref<string>('')

// 鞋型颜色
const selectedColor = ref<{ name: string; orderShoeTypeId: number; id?: number } | null>(null)
const shoeColorOptions = ref<any[]>([])
const shoeColorsLoading = ref(false)

async function loadShoeColors(orderId: number, orderShoeId: number) {
    shoeColorsLoading.value = true
    try {
        const { data } = await axios.get(`${apiBaseUrl}${API.SHOE_COLORS}`, { params: { orderId, orderShoeId } })
        const arr = Array.isArray(data) ? data : data?.list || data?.colors || []
        shoeColorOptions.value = arr
            .filter((x: any) => x && (x.name || typeof x === 'string'))
            .map((x: any) => {
                if (typeof x === 'string') return { name: x, orderShoeTypeId: null, id: null }
                return {
                    name: x.name || x.color_name || '',
                    orderShoeTypeId: Number(x.orderShoeTypeId ?? x.id ?? x.order_shoe_type_id ?? 0) || null,
                    id: Number(x.id ?? x.orderShoeTypeId ?? x.order_shoe_type_id ?? 0) || null
                }
            })
    } catch (e: any) {
        shoeColorOptions.value = []
        ElMessage.error(e?.message || '加载鞋型颜色失败')
    } finally {
        shoeColorsLoading.value = false
    }
}

// 供应商 & 材料名称全集
const supplierNameOptions = ref<any[]>([])
const materialNameOptions = ref<Array<{ label: string; value: string; type?: number; materialType?: number; categoryType?: number; category?: number }>>([])

const CATEGORY_TYPE_MAP: Record<string, number[]> = {
    surface: [1],
    lining: [2],
    accessory: [3, 5],
    outsole: [7],
    midsole: [7],
    hotmelt: [16]
}
function getTypesByCategory(category?: string): number[] {
    return CATEGORY_TYPE_MAP[category || ''] || []
}
function filterByTypes(list: any, types: number[] = []) {
    const arr = Array.isArray(list) ? list : list?.value || []
    if (!types || types.length === 0) return arr
    return arr.filter((it: any) => {
        const t = Number(it.type ?? it.materialType ?? it.categoryType ?? it.category)
        return Number.isFinite(t) ? types.includes(t) : false
    })
}
async function getAllMaterialName() {
    try {
        const { data } = await axios.get(`${apiBaseUrl}/logistics/getallmaterialname`, { params: { department: '0' } })
        materialNameOptions.value = Array.isArray(data) ? data : data?.list || []
    } catch (e: any) {
        console.error('getallmaterialname error', e)
        materialNameOptions.value = []
    }
}

function trimInput(row: any, key: string) {
    if (row[key]) row[key] = String(row[key]).trim()
}
function validateColor(_row: any) {}

function findTab(key: string) {
    return requestForm.colorTabs.find((t) => t.key === key)
}
function getActiveTab() {
    return findTab(activeColor.value)
}

function addColorTab() {
    const sel = selectedColor.value
    if (!sel?.name) {
        ElMessage.warning('请选择鞋型颜色')
        return
    }
    const existed = requestForm.colorTabs.find((t) => t.color === sel.name && t.orderShoeTypeId === sel.orderShoeTypeId)
    if (existed) {
        activeColor.value = existed.key
        return
    }
    const key = `${Date.now()}_${Math.random().toString(36).slice(2, 6)}`
    requestForm.colorTabs.push({ key, color: sel.name, orderShoeTypeId: sel.orderShoeTypeId ?? null, items: [] })
    activeColor.value = key
}
function removeColorTab(key: string) {
    const idx = requestForm.colorTabs.findIndex((t) => t.key === key)
    if (idx >= 0) {
        requestForm.colorTabs.splice(idx, 1)
        if (activeColor.value === key) {
            activeColor.value = requestForm.colorTabs[0]?.key || ''
        }
    }
}

function addItem() {
    const tab = getActiveTab()
    if (!tab) {
        ElMessage.warning('请先添加并选择鞋型颜色')
        return
    }
    tab.items.push({ quantity: null })
}
function removeItem(idx: number) {
    const tab = getActiveTab()
    if (!tab) return
    tab.items.splice(idx, 1)
}

const requestRules: FormRules = {
    reason: [{ required: true, message: '请选择需求原因', trigger: 'blur' }],
    expectDate: [{ required: true, message: '请选择期望到货日期', trigger: 'change' }]
}

async function openRequestDialog(row: any) {
    requestDialog.order = row
    requestForm.orderId = row.orderId
    requestForm.orderShoeId = row.orderShoeId
    requestForm.orderShoeTypeId = row.orderShoeTypeId
    requestForm.reason = ''
    requestForm.expectDate = ''
    requestForm.remark = ''
    requestForm.colorTabs = []
    activeColor.value = ''
    await loadShoeColors(row.orderId, row.orderShoeId)
    requestDialog.visible = true
}

async function submitRequest() {
    if (!requestFormRef.value) return
    await requestFormRef.value.validate(async (valid) => {
        if (!valid) return
        const allItems = requestForm.colorTabs.flatMap((tab) => tab.items.map((it) => ({ ...it, shoeColor: tab.color, _orderShoeTypeId: tab.orderShoeTypeId })))
        if (!allItems.length) {
            ElMessage.error('请至少在某个颜色下添加一行材料')
            return
        }
        const invalid = allItems.find((it) => !it.materialName)
        if (invalid) {
            ElMessage.error('材料名称为必填')
            return
        }
        try {
            requestDialog.submitting = true
            const payload = {
                orderId: requestForm.orderId,
                orderShoeId: requestForm.orderShoeId,
                orderShoeTypeId: requestForm.orderShoeTypeId,
                reason: requestForm.reason,
                expectDate: requestForm.expectDate,
                remark: requestForm.remark,
                items: allItems.map((it: any) => ({
                    spuMaterialId: it.spuMaterialId,
                    materialId: it.materialId,
                    name: it.materialName,
                    model: it.materialModel,
                    spec: it.materialSpecification,
                    supplierName: it.supplierName,
                    color: it.materialColor || null,
                    orderShoeTypeId: it._orderShoeTypeId ?? requestForm.orderShoeTypeId
                }))
            }
            const { data } = await axios.post(`${apiBaseUrl}${API.CREATE_REQUEST}`, payload)
            if (data?.success) {
                ElMessage.success('已提交补采请求')
                requestDialog.visible = false
                loadOrders()
                loadInProgressSummary()
            } else {
                throw new Error(data?.message || '提交失败')
            }
        } catch (e: any) {
            ElMessage.error(e?.message || '提交失败')
        } finally {
            requestDialog.submitting = false
        }
    })
}

// ===== 自动补全函数（对接 /devproductionorder/* 接口） =====
async function queryMaterialNames(queryString: string, callback: (items: any[]) => void) {
    if (queryString && queryString.trim()) {
        try {
            const resp = await axios.get(`${apiBaseUrl}/devproductionorder/getautofinishedmaterialname`, { params: { materialName: queryString } })
            const suggestions = (resp.data || []).map((item: any) => ({ value: item.name }))
            callback(suggestions)
        } catch (err) {
            console.error('Failed to fetch material names:', err)
            callback([])
        }
    } else {
        callback([])
    }
}
async function searchRecords(materialName: any, materialSupplier: any, materialModel: any, materialSpecification: any, searchType: number) {
    const params: any = { searchType, materialName, materialSupplier }
    if (searchType === 0) {
        params.materialModel = materialModel
    } else if (searchType === 1) {
        params.materialModel = materialModel
        params.materialSpecification = materialSpecification
    }
    const response = await axios.get(`${apiBaseUrl}/devproductionorder/getautocompeletedata`, { params })
    return response.data
}
function querySearchModel(searchType: number, row: any, queryString: string, callback: (res: any[]) => void) {
    if (!queryString || !queryString.trim()) {
        callback([])
        return
    }
    if (searchType === 0) {
        searchRecords(row.materialName, row.supplierName, queryString, null, 0)
            .then((results: any[]) => callback(results.map((item: any) => ({ value: item }))))
            .catch(() => callback([]))
    } else if (searchType === 1) {
        searchRecords(row.materialName, row.supplierName, row.materialModel, queryString, 1)
            .then((results: any[]) => callback(results.map((item: any) => ({ value: item }))))
            .catch(() => callback([]))
    }
}
function querySearchSupplier(queryString: string, cb: (items: any[]) => void) {
    if (queryString && queryString.trim()) {
        const results = supplierNameOptions.value.filter((s) => s.supplierName?.toLowerCase().includes(queryString.toLowerCase()))
        const supplierNameResults = results.map((item) => ({ value: item.supplierName }))
        cb(supplierNameResults)
    } else {
        cb([])
    }
}
async function handleMaterialNameSelect(row: any) {
    try {
        const resp = await axios.get(`${apiBaseUrl}/devproductionorder/getmaterialdetail`, { params: { materialName: row.materialName } })
        const d = resp.data || {}
        row.materialId = d.materialId
        row.unit = d.unit
        row.materialType = d.materialType
    } catch (e: any) {
        console.error('getmaterialdetail error', e)
    }
}
function handleSupplierNameSelect(row: any, selectedItem: any) {
    row.supplierName = selectedItem?.value
}
async function querySupplierNames() {
    const response = await axios.get(`${apiBaseUrl}/logistics/allsuppliers`)
    supplierNameOptions.value = response.data || []
}

onMounted(() => {
    loadOrders()
    loadInProgressSummary()
    getAllMaterialName()
    querySupplierNames()
})
</script>

<style scoped>
.page {
    display: flex;
    flex-direction: column;
    gap: 12px;
}
.mb-3 {
    margin-bottom: 12px;
}
.card-fill {
    min-height: 420px;
}
.flex {
    display: flex;
}
.items-center {
    align-items: center;
}
.justify-between {
    justify-content: space-between;
}
.justify-end {
    justify-content: flex-end;
}
.gap-2 {
    gap: 8px;
}
.mt-2 {
    margin-top: 8px;
}
.mt-3 {
    margin-top: 12px;
}
.text-gray-500 {
    color: #909399;
}
.muted {
    color: #999;
}
.toolbar-right {
    margin-left: auto;
    display: inline-flex;
    align-items: center;
}
.mr-2 {
    margin-right: 8px;
}
</style>
