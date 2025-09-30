<template>
    <div class="page p-4">
        <!-- ========== 场景 1：订单选择（初始） ========== -->
        <template v-if="mode === 'order'">
            <el-card shadow="never" class="mb-3">
                <el-form :inline="true">
                    <el-form-item label="订单搜索">
                        <el-input v-model.trim="orderQuery.keyword" placeholder="输入订单号/客户信息/鞋型等关键词" clearable style="width: 280px" @keyup.enter="loadOrders" />
                    </el-form-item>
                    <el-form-item>
                        <el-button type="primary" :loading="orderLoading" @click="loadOrders">查询订单</el-button>
                        <el-button @click="resetOrderSearch">清空</el-button>
                    </el-form-item>
                </el-form>
            </el-card>

            <!-- 填充剩余高度的卡片 -->
            <el-card shadow="never" class="card-fill">
                <template #header>
                    有材料可出库的订单（{{ orderTotal }}）
                    <template v-if="isRoleRestricted">
                        <el-tag class="ml-2" size="small" type="info">
                            {{ allowedTypeNames.join(' / ') }}
                        </el-tag>
                    </template>
                </template>

                <div class="panel-grid">
                    <!-- 表格占满第一行 -->
                    <el-table :data="orderRows" border stripe height="100%">
                        <el-table-column prop="orderRId" label="订单号" />
                        <el-table-column prop="shoeRId" label="工厂型号" />
                        <el-table-column prop="customerName" label="客户" show-overflow-tooltip />
                        <el-table-column prop="brand" label="商标" width="120" />
                        <el-table-column prop="productName" label="客户型号" show-overflow-tooltip />
                        <el-table-column prop="period" label="订单周期" show-overflow-tooltip />
                        <el-table-column label="操作" width="120" fixed="right">
                            <template #default="{ row }">
                                <el-button type="primary" link @click="selectOrder(row.orderRId)">选择</el-button>
                            </template>
                        </el-table-column>
                    </el-table>

                    <!-- 分页固定在卡片底部第二行 -->
                    <div class="panel-footer">
                        <el-pagination
                            background
                            layout="total, prev, pager, next, jumper"
                            :total="orderTotal"
                            :page-size="orderQuery.pageSize"
                            :current-page="orderQuery.page"
                            @current-change="
                                (p) => {
                                    orderQuery.page = p
                                    loadOrders()
                                }
                            "
                        />
                    </div>
                </div>
            </el-card>
        </template>

        <!-- ========== 场景 2：材料出库（选中订单后） ========== -->
        <template v-else>
            <el-card shadow="never" class="mb-3">
                <div class="flex items-center justify-between">
                    <div>
                        <span class="text-sm opacity-80">当前订单：</span>
                        <el-tag type="success">{{ query.orderRId }}</el-tag>
                    </div>
                    <div class="flex items-center gap-3">
                        <el-button @click="backToOrderSelection">返回订单选择</el-button>
                        <el-button @click="resetMaterialsTable">重置材料表</el-button>
                        <el-button type="primary" link @click="recordsDrawer = true">查看订单出库记录</el-button>
                    </div>
                </div>
            </el-card>

            <el-card shadow="never" class="mb-3">
                <el-form :inline="true">
                    <el-form-item label="材料类型">
                        <el-select v-model="query.materialTypeId" clearable placeholder="全部" style="width: 220px">
                            <el-option v-for="t in materialTypes" :key="t.id" :label="t.name" :value="t.id" />
                        </el-select>
                    </el-form-item>
                    <el-form-item label="含非订单库存">
                        <el-switch v-model="includeGeneral" :active-value="1" :inactive-value="0" />
                    </el-form-item>
                    <el-form-item>
                        <el-button type="primary" :loading="loading" @click="reload">查询材料</el-button>
                        <el-button @click="resetFiltersOnly">清空筛选</el-button>
                    </el-form-item>
                </el-form>
            </el-card>

            <!-- 填充剩余高度的卡片：表格 + 操作条 -->
            <el-card shadow="never" class="card-fill">
                <template #header>
                    <div class="flex items-center justify-between">
                        <div>可出库材料（{{ total }}）</div>
                        <div class="text-sm opacity-80">已选 {{ selectedIdSet.size }} 条，合计出库：{{ totalOutboundGlobal }}</div>
                    </div>
                </template>

                <div class="panel-grid">
                    <div class="x-scroll">
                        <!-- 表格占满 -->
                        <el-table
                            ref="tableRef"
                            :data="rows"
                            border
                            stripe
                            height="100%"
                            :row-key="(row) => row.materialStorageId"
                            :reserve-selection="true"
                            @select="onRowSelect"
                            @select-all="onSelectAll"
                            @selection-change="onSelectionChange"
                        >
                            <el-table-column type="selection" width="44" />
                            <el-table-column prop="materialName" label="材料" />
                            <el-table-column prop="materialModel" label="型号" show-overflow-tooltip />
                            <el-table-column prop="materialSpecification" label="规格" show-overflow-tooltip />
                            <el-table-column prop="materialColor" label="颜色" />
                            <el-table-column prop="supplierName" label="供应商" show-overflow-tooltip />
                            <el-table-column prop="actualInboundUnit" label="单位" />
                            <el-table-column prop="currentAmount" label="库存" />

                            <el-table-column label="按尺码分配" min-width="160">
                                <template #default="{ row }">
                                    <div class="flex items-center gap-3">
                                        <span class="text-sm opacity-80"> 合计 {{ row._outboundQuantity || 0 }} / 库存 {{ row.currentAmount || 0 }} </span>
                                        <el-button type="primary" link @click="openSizeEditor(row)">编辑尺码</el-button>
                                    </div>
                                </template>
                            </el-table-column>

                            <el-table-column label="出库总数" min-width="120">
                                <template #default="{ row }">
                                    <el-input-number v-model="row._outboundQuantity" size="small" :min="0" :max="row.currentAmount" :step="1" @change="syncRowByTotal(row)" />
                                </template>
                            </el-table-column>

                            <el-table-column label="备注">
                                <template #default="{ row }">
                                    <el-input v-model="row._remark" placeholder="可选" />
                                </template>
                            </el-table-column>
                        </el-table>
                    </div>

                    <!-- 操作区固定在底部 -->
                    <div class="panel-footer sticky-footer" ref="footerRef">
                        <el-pagination
                            background
                            layout="total, prev, pager, next, jumper"
                            :total="total"
                            :page-size="query.pageSize"
                            :current-page="query.page"
                            @current-change="
                                (p) => {
                                    query.page = p
                                    reload()
                                }
                            "
                        />
                        <div class="footer-actions-scroll" ref="actionsScrollRef">
                            <!-- >= 收纳阈值：完整横排（但尺寸更紧凑） -->
                            <div class="flex items-center gap-3 footer-actions" v-if="!isNarrow">
                                <el-select size="small" v-model="form.departmentId" placeholder="出库至部门" style="width: 180px" filterable clearable>
                                    <el-option v-for="d in departments" :key="d.value" :label="d.label" :value="d.value" />
                                </el-select>
                                <el-input size="small" v-model.trim="form.picker" placeholder="领料人" style="width: 140px" />
                                <el-input size="small" v-model.trim="form.remark" placeholder="整单备注（可选）" style="width: 200px" />
                                <el-button size="small" type="primary" :loading="submitting" @click="openConfirm">提交出库</el-button>
                            </div>

                            <!-- 收纳：控件进 Popover，只留“提交出库”常驻 -->
                            <div class="flex items-center gap-3 footer-actions" v-else>
                                <el-popover placement="top" width="360" trigger="click">
                                    <template #reference>
                                        <el-button size="small">出库设置</el-button>
                                    </template>
                                    <div class="flex flex-col gap-2" style="padding: 4px 2px">
                                        <el-select size="small" v-model="form.departmentId" placeholder="出库至部门" filterable clearable>
                                            <el-option v-for="d in departments" :key="d.value" :label="d.label" :value="d.value" />
                                        </el-select>
                                        <el-input size="small" v-model.trim="form.picker" placeholder="领料人" />
                                        <el-input size="small" v-model.trim="form.remark" placeholder="整单备注（可选）" />
                                    </div>
                                </el-popover>
                                <el-button size="small" type="primary" :loading="submitting" @click="openConfirm">提交出库</el-button>
                            </div>
                        </div>
                    </div>
                </div>
            </el-card>

            <!-- 出库记录：抽屉，避免页面加长 -->
            <el-drawer v-model="recordsDrawer" title="订单出库记录" size="60%">
                <el-table :data="records" border stripe height="100%">
                    <el-table-column prop="timestamp" label="时间" width="180" />
                    <el-table-column prop="outboundRId" label="出库单号" width="200" />
                    <el-table-column prop="picker" label="领料人" width="120" />
                    <el-table-column prop="outboundType" label="类型" width="120" />
                    <el-table-column prop="outboundAmount" label="数量(明细)" width="120" />
                    <el-table-column prop="remark" label="备注" />
                    <el-table-column label="操作">
                        <template #default="{ row }">
                            <el-button type="primary" @click="viewOutboundRecord(row)">查看详情</el-button>
                        </template>
                    </el-table-column>
                </el-table>
            </el-drawer>
        </template>
    </div>
    <el-dialog v-model="sizeEditorVisible" title="尺码分配" width="720px" @open="onEditorOpen">
        <div class="mb-2 text-sm opacity-80">
            订单：<el-tag type="success" size="small">{{ query.orderRId }}</el-tag>
        </div>

        <el-scrollbar height="340px">
            <div class="size-grid">
                <div class="size-box" v-for="(name, i) in editingRow?.shoeSizeColumns || []" :key="i">
                    <div class="sb-head">
                        <div class="sb-name">{{ name }}</div>
                        <div class="sb-stock">库存：{{ editingRow?.[`currentAmount${i}`] || 0 }}</div>
                    </div>
                    <el-input-number v-model="editingTempAmounts[i]" :min="0" :max="editingRow?.[`currentAmount${i}`] || 0" :step="1" controls-position="right" @change="recalcEditingSum" />
                </div>
            </div>
        </el-scrollbar>

        <template #footer>
            <div class="flex items-center justify-between w-full">
                <div class="flex items-center gap-2">
                    <el-button @click="fillByStock">按库存填满</el-button>
                    <el-button @click="clearAllSize">清空</el-button>
                    <el-button @click="fillByRatio">按比例分配</el-button>
                </div>
                <div class="flex items-center gap-3">
                    <span class="text-sm opacity-80">合计：{{ editingSum }} / 库存：{{ editingTotalStock }}</span>
                    <el-button @click="sizeEditorVisible = false">取消</el-button>
                    <el-button type="primary" @click="confirmSizeEditor">确定</el-button>
                </div>
            </div>
        </template>
    </el-dialog>
    <el-dialog title="出库单详情" v-model="dialogVisible" width="80%">
        <div id="printView" v-show="true">
            <table style="width: 100%; border-collapse: collapse">
                <!-- Header repeated on each page -->
                <thead>
                    <tr>
                        <td>
                            <div style="position: relative; padding: 5px">
                                <h1 style="margin: 0; text-align: center">健诚鞋业出库单</h1>
                                <span style="position: absolute; right: 0; top: 50%; transform: translateY(-50%); font-weight: bolder; font-size: 16px"> 单据编号: {{ currentRow.outboundRId }} </span>
                            </div>
                            <table
                                class="table"
                                border="0"
                                cellspacing="0"
                                align="left"
                                width="100%"
                                style="font-size: 16px; margin-bottom: 10px; table-layout: fixed; word-wrap: break-word; word-break: break-all"
                            >
                                <tr>
                                    <td style="padding: 5px; width: 150px" align="left">出库至: {{ currentRow.destination }}</td>
                                    <td style="padding: 5px; width: 300px" align="left">出库时间: {{ currentRow.timestamp }}</td>
                                    <td style="padding: 5px; width: 150px" align="left">出库类型: {{ currentRow.outboundType }}</td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                </thead>

                <!-- Main body content -->
                <tbody>
                    <tr>
                        <td>
                            <table class="yk-table" border="1" cellspacing="0" align="center" width="100%" style="max-height: 360px; table-layout: fixed; word-wrap: break-word; word-break: break-all">
                                <thead>
                                    <tr>
                                        <th width="100">材料名</th>
                                        <th width="100">型号</th>
                                        <th width="180">规格</th>
                                        <th width="80">颜色</th>
                                        <th width="55">单位</th>
                                        <th width="100">订单号</th>
                                        <th width="100">工厂鞋型</th>
                                        <th width="100">数量</th>
                                        <th width="100">单价</th>
                                        <th width="100">金额</th>
                                        <th>备注</th>
                                    </tr>
                                </thead>

                                <tr v-for="(item, index) in recordData" :key="index" align="center">
                                    <td>{{ item.materialName }}</td>
                                    <td>{{ item.materialModel }}</td>
                                    <td>{{ item.materialSpecification }}</td>
                                    <td>{{ item.materialColor }}</td>
                                    <td>{{ item.actualInboundUnit }}</td>
                                    <td>{{ item.orderRId }}</td>
                                    <td>{{ item.shoeRId }}</td>
                                    <td>{{ item.outboundQuantity }}</td>
                                    <td>{{ item.unitPrice }}</td>
                                    <td>{{ item.itemTotalPrice }}</td>
                                    <td>{{ item.remark }}</td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                </tbody>

                <!-- Footer repeated on each page -->
                <tfoot>
                    <tr>
                        <td>
                            <div style="margin-top: 20px; font-size: 16px; font-weight: bold; display: flex">
                                <span style="padding-right: 10px"
                                    >合计数量: <span style="text-decoration: underline">{{ calculateOutboundTotal() }}</span></span
                                >
                                <span style="padding-right: 10px"
                                    >合计金额: <span style="text-decoration: underline">{{ currentRow.totalPrice }}</span></span
                                >
                                <span style="padding-right: 10px; width: 150px"
                                    >领料人: <span style="text-decoration: underline">{{ currentRow.picker }}</span></span
                                >
                                <span style="padding-right: 10px"
                                    >备注: <span style="text-decoration: underline">{{ currentRow.remark }}</span></span
                                >
                            </div>
                        </td>
                    </tr>
                </tfoot>
            </table>
        </div>
        <template #footer>
            <el-button type="primary" @click="dialogVisible = false">返回</el-button>
            <el-button type="primary" v-print="'#printView'">打印</el-button>
            <template v-if="isPreviewConfirm">
                <el-button @click="dialogVisible = false">返回修改</el-button>
                <el-button type="primary" :loading="submitting" @click="doSubmitInDialog">确认提交</el-button>
            </template>
            <template v-else>
                <el-button type="primary" @click="dialogVisible = false">返回</el-button>
                <el-button type="primary" v-print="'#printView'">打印</el-button>
            </template>
        </template>
    </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, getCurrentInstance, nextTick, watch } from 'vue'
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'
import { onUnmounted } from 'vue'

const isNarrow = ref(false)
function updateNarrow() {
    // 1280x720 宽度场景走紧凑模式
    isNarrow.value = window.innerWidth <= 1280
}
onMounted(() => {
    updateNarrow()
    window.addEventListener('resize', updateNarrow)
})
onUnmounted(() => {
    window.removeEventListener('resize', updateNarrow)
})

const apiBaseUrl = getCurrentInstance().appContext.config.globalProperties.$apiBaseUrl

/** 页面模式 */
const mode = ref<'order' | 'materials'>('order')

/** 订单区 */
const dialogVisible = ref(false)
const currentRow = ref<any>({})
const recordData = ref([])
const orderLoading = ref(false)
const orderQuery = reactive({ keyword: '', page: 1, pageSize: 10 })
const orderRows = ref([])
const orderTotal = ref(0)
const departments = ref<Array<{ value: number; label: string }>>([])
const editCache = reactive(new Map<string, { total: number; amounts: number[]; remark: string }>())
const tableRef = ref()
/** 跨页全局选择的 id 集合 */
const selectedIdSet = ref<Set<string>>(new Set())
const getRowId = (row: any) => String(row?.materialStorageId ?? '')
/** 计算全局合计出库 */
const totalOutboundGlobal = computed(() => {
    let sum = 0
    selectedIdSet.value.forEach((id) => {
        const cached = editCache.get(id)
        if (cached) sum += Number(cached.total || 0)
    })
    return sum
})
type DisplayRow = {
    materialName: string
    materialModel: string
    materialSpecification: string
    materialColor: string
    actualInboundUnit: string
    orderRId: string
    shoeRId?: string
    unitPrice?: number | string
}
const displayCache = reactive(new Map<string, DisplayRow>())
const confirmVisible = ref(false)
const previewItems = ref<any[]>([])
const previewTotalQty = computed(() => previewItems.value.reduce((s, it) => s + (Number(it.outboundQuantity) || 0), 0))

// 身份识别
const ROLE_TYPE_MAP: Record<number, string[]> = {
    40: ['面料','里料','复合'], // 面料仓
    41: ['底材'], // 底材仓
    42: ['包材'], // 包材仓
    11: ['辅料', '饰品'] // 辅料及饰品
}

const staffId = ref<number | null>(null)
const allowedTypeNames = computed<string[]>(() => {
    if (staffId.value == null) return []
    return ROLE_TYPE_MAP[staffId.value] ?? []
})
const isRoleRestricted = computed(() => allowedTypeNames.value.length > 0)

function loadStaffIdFromLocalStorage() {
    try {
        const v = localStorage.getItem('staffid')
        staffId.value = v != null && v !== '' ? Number(v) : null
    } catch {
        staffId.value = null
    }
}
// ===== 新增：预览/确认模式标记 =====
const isPreviewConfirm = ref(false)

// ===== 新增：构建预览明细（使用全局选择 + 缓存）=====
function buildPreviewItems() {
    const list: any[] = []
    selectedIdSet.value.forEach((id) => {
        const r = rows.value.find((x) => String(x.materialStorageId) === id) // 还在当前页的话也可用
        const d = displayCache.get(id) // 关键：跨页展示靠它
        const c = editCache.get(id)
        const outboundQuantity = Number((c?.total ?? r?._outboundQuantity) || 0)
        const remark = (c?.remark ?? r?._remark ?? '').toString()
        const unitPriceNum = Number(d?.unitPrice ?? r?.unitPrice ?? 0)
        const itemTotal = unitPriceNum * outboundQuantity
        list.push({
            materialName: d?.materialName ?? r?.materialName ?? '—',
            materialModel: d?.materialModel ?? r?.materialModel ?? '—',
            materialSpecification: d?.materialSpecification ?? r?.materialSpecification ?? '—',
            materialColor: d?.materialColor ?? r?.materialColor ?? '—',
            actualInboundUnit: d?.actualInboundUnit ?? r?.actualInboundUnit ?? '—',
            orderRId: d?.orderRId ?? query.orderRId,
            shoeRId: d?.shoeRId ?? r?.shoeRId ?? '—',
            outboundQuantity,
            unitPrice: Number.isFinite(unitPriceNum) ? unitPriceNum.toFixed(2) : '',
            itemTotalPrice: Number.isFinite(itemTotal) ? itemTotal.toFixed(2) : '0.00',
            remark
        })
    })
    return list
}

// ===== 新增：打开预览确认（复用现有 dialogVisible）=====
function openConfirm() {
    if (!query.orderRId) return ElMessage.warning('缺少订单号')
    if (selectedIdSet.value.size === 0) return ElMessage.warning('请选择要出库的材料')
    if (form.departmentId == null) return ElMessage.warning('请选择出库至部门')

    // 用于对话框抬头信息（预览阶段还没有出库单号/时间）
    currentRow.value = {
        outboundRId: '（提交后生成）',
        destination: selectedDepartmentName.value || '—',
        timestamp: '（提交后生成）',
        outboundType: '订单出库',
        picker: form.picker || '—',
        remark: form.remark || '—',
        totalPrice: '' // 如果需要也可先留空
    }
    recordData.value = buildPreviewItems()
    isPreviewConfirm.value = true
    dialogVisible.value = true
}

// ===== 新增：提交载荷（沿用你现有 submit 构造逻辑）=====
function buildSubmitPayloadItems() {
    const items: any[] = []
    selectedIdSet.value.forEach((id) => {
        const r = rows.value.find((x) => String(x.materialStorageId) === id)
        const cache = editCache.get(id)
        const total = cache?.total ?? r?._outboundQuantity ?? 0
        const amounts = cache?.amounts ?? r?._amounts ?? []
        const remark = (cache?.remark ?? r?._remark ?? '').toString()
        const payload: any = { materialStorageId: id, outboundQuantity: Number(total || 0), remark }
        amounts.forEach((val: number, i: number) => (payload[`amount${i}`] = Number(val || 0)))
        items.push(payload)
    })
    return items
}

// ===== 新增：在对话框中点“确认提交” =====
async function doSubmitInDialog() {
    const items = buildSubmitPayloadItems()
    if (items.length === 0) return ElMessage.warning('请选择要出库的材料')
    for (const it of items) {
        if (!it.outboundQuantity || it.outboundQuantity <= 0) {
            return ElMessage.error('出库总数必须大于 0')
        }
    }
    try {
        submitting.value = true
        const { data } = await axios.post(`${apiBaseUrl}/warehouse/orderoutbound/create`, {
            orderRId: query.orderRId,
            picker: form.picker,
            remark: form.remark,
            items,
            departmentId: form.departmentId,
            destinationDepartmentName: selectedDepartmentName.value
        })
        // 提交成功后，切换为“已生成出库单”的展示（保留同一个对话框用于打印）
        isPreviewConfirm.value = false
        // 更新抬头为真实单据信息
        currentRow.value = {
            ...currentRow.value,
            outboundRId: data.outboundRId,
            timestamp: data.outboundTime
        }
        // 如果你能拿到详情接口（含单价/金额），这里也可再调一次刷新 recordData：
        // await viewOutboundRecord(data.outboundRecordId)

        ElMessage.success('出库成功，已生成出库单！可直接打印')
        // 清空全局选择，重新加载列表
        selectedIdSet.value.clear()
        displayCache.clear()
        selectedItems.value = []
        await reload(false)
    } finally {
        submitting.value = false
    }
}

async function loadDepartments() {
    try {
        const { data } = await axios.get(`${apiBaseUrl}/general/getalldepartments`)
        departments.value = Array.isArray(data) ? data : []
    } catch (e) {
        console.error(e)
        ElMessage.error('加载部门列表失败')
    }
}

// 选中部门名（可选，用于提交时一并传递名称，后端也可仅用ID自己查）
const selectedDepartmentName = computed(() => {
    const d = departments.value.find((x) => x.value === form.departmentId)
    return d ? d.label : ''
})
async function loadOrders() {
    orderLoading.value = true
    try {
        const { data } = await axios.get(`${apiBaseUrl}/warehouse/orderoutbound/orders`, {
            params: {
                keyword: orderQuery.keyword,
                page: orderQuery.page,
                pageSize: orderQuery.pageSize,
                staffId: staffId.value ?? undefined // ← 新增
            }
        })
        orderRows.value = data?.result || []
        orderTotal.value = data?.total || 0
    } finally {
        orderLoading.value = false
    }
}
function resetOrderSearch() {
    orderQuery.keyword = ''
    orderQuery.page = 1
    loadOrders()
}
function selectOrder(orderRId: string) {
    query.orderRId = orderRId
    query.page = 1
    mode.value = 'materials'
    reload(false)
}
interface MaterialType {
    id: number
    name: string
}

/** 材料区 */
const loading = ref(false)
const submitting = ref(false)
const includeGeneral = ref(0)
const materialTypes = ref<MaterialType[]>([])

const loadMaterialTypes = async () => {
    try {
        const res = await axios.get(`${apiBaseUrl}/logistics/getallmaterialtypes`)
        const all = Array.isArray(res.data) ? res.data : []

        const names = allowedTypeNames.value
        const filtered = names.length ? all.filter((x: any) => names.includes(x.materialTypeName)) : all

        materialTypes.value = filtered.map((item: any) => ({
            id: item.materialTypeId,
            name: item.materialTypeName
        }))

        // 如果身份只有一个类型，默认选中它，减少误操作
        if (materialTypes.value.length === 1) {
            query.materialTypeId = materialTypes.value[0].id
        }
    } catch (err) {
        console.error('获取物料类型失败', err)
    }
}

const query = reactive({ orderRId: '', materialTypeId: undefined as number | undefined, page: 1, pageSize: 10 })
const rows = ref<any[]>([])
const originalRows = ref<any[]>([])
const total = ref(0)
const records = ref<any[]>([])
const recordsDrawer = ref(false)

const form = reactive({ picker: '', remark: '', departmentId: undefined as number | undefined })
const selectedItems = ref<any[]>([])
const totalOutbound = computed(() => selectedItems.value.reduce((s, r) => s + (Number(r._outboundQuantity) || 0), 0))

function normalizeRow(r: any) {
    const count = Array.isArray(r.shoeSizeColumns) ? r.shoeSizeColumns.length : 0
    r._amounts = []
    let sum = 0
    for (let i = 0; i < count; i++) {
        const stock = Number(r[`currentAmount${i}`] || 0)
        r._amounts.push(stock)
        sum += stock
    }
    // 如果没有尺码列，就用总体库存
    const totalStock = Number(r.currentAmount || 0)
    r._outboundQuantity = count > 0 ? sum : totalStock
    r._remark = ''
    return r
}
function deepClone<T>(obj: T): T {
    return JSON.parse(JSON.stringify(obj))
}

function resetFiltersOnly() {
    query.materialTypeId = undefined
    includeGeneral.value = 0
    query.page = 1
    reload(true)
}
function resetMaterialsTable() {
    rows.value = (originalRows.value || []).map((r: any) => normalizeRow(deepClone(r)))
    selectedItems.value = []
    selectedIdSet.value.clear()
    displayCache.clear()
}
function backToOrderSelection() {
    form.departmentId = undefined
    query.orderRId = ''
    rows.value = []
    originalRows.value = []
    total.value = 0
    records.value = []
    selectedItems.value = []
    form.picker = ''
    form.remark = ''
    mode.value = 'order'
    loadOrders()
    selectedIdSet.value.clear()
    displayCache.clear()
}

function onSelect(list: any[]) {
    selectedItems.value = list
}
function syncRowTotal(row: any) {
    row._outboundQuantity = (row._amounts || []).reduce((s: number, v: number) => s + (Number(v) || 0), 0)
    persistRowEdit(row) // ← 新增
}
function syncRowByTotal(row: any) {
    let remaining = Number(row._outboundQuantity || 0)
    for (let i = 0; i < (row._amounts || []).length; i++) {
        const cap = Number(row[`currentAmount${i}`] || 0)
        const take = Math.min(cap, remaining)
        row._amounts[i] = take
        remaining -= take
    }
    persistRowEdit(row) // ← 新增
}
watch(
    () => rows.value,
    () => {
        // 每次行渲染后，把 remark 的双向绑定也持久化
        rows.value.forEach((r) => persistRowEdit(r))
    },
    { deep: true }
)

async function loadRecords() {
    const { data } = await axios.get(`${apiBaseUrl}/warehouse/orderoutbound/records`, { params: { orderRId: query.orderRId, page: 1, pageSize: 50 } })
    records.value = data?.result || []
}
// ======= 弹窗状态 =======
const sizeEditorVisible = ref(false)
const editingRow = ref<any | null>(null)
const editingTempAmounts = ref<number[]>([])
const editingSum = ref(0)
const editingTotalStock = ref(0)

function openSizeEditor(row: any) {
    editingRow.value = row
    // 用当前行的 _amounts 作为初始（不覆盖用户改动）
    editingTempAmounts.value = (row._amounts || []).map((v: number) => Number(v) || 0)
    editingTotalStock.value = (row.shoeSizeColumns || []).reduce((s: number, _x: any, i: number) => s + (Number(row[`currentAmount${i}`]) || 0), 0)
    editingSum.value = editingTempAmounts.value.reduce((a, b) => a + Number(b || 0), 0)
    sizeEditorVisible.value = true
}

function onEditorOpen() {
    /* 需要的话在打开时做额外准备 */
}

function recalcEditingSum() {
    editingSum.value = editingTempAmounts.value.reduce((a, b) => a + Number(b || 0), 0)
}

function fillByStock() {
    const row = editingRow.value
    if (!row) return
    editingTempAmounts.value = (row.shoeSizeColumns || []).map((_: any, i: number) => Number(row[`currentAmount${i}`] || 0))
    recalcEditingSum()
}

function clearAllSize() {
    const row = editingRow.value
    if (!row) return
    editingTempAmounts.value = (row.shoeSizeColumns || []).map(() => 0)
    recalcEditingSum()
}

// 按当前“出库总数”在各尺码间按库存占比分配（不超库存）
function fillByRatio() {
    const row = editingRow.value
    if (!row) return
    const total = Number(row._outboundQuantity || 0)
    const stocks = (row.shoeSizeColumns || []).map((_: any, i: number) => Number(row[`currentAmount${i}`] || 0))
    const sumStock = stocks.reduce((a, b) => a + b, 0)
    if (sumStock <= 0 || total <= 0) {
        clearAllSize()
        return
    }
    // 先按比例下取整
    const tentative = stocks.map((s) => Math.floor(total * (s / sumStock)))
    let used = tentative.reduce((a, b) => a + b, 0)
    // 余数按剩余可用库存逐个补齐
    for (let i = 0; i < tentative.length && used < total; i++) {
        const canAdd = Math.min(stocks[i] - tentative[i], total - used)
        const add = Math.min(canAdd, 1)
        tentative[i] += add
        used += add
    }
    // 兜底不超过库存
    for (let i = 0; i < tentative.length; i++) {
        tentative[i] = Math.min(tentative[i], stocks[i])
    }
    editingTempAmounts.value = tentative
    recalcEditingSum()
}

function confirmSizeEditor() {
    if (!editingRow.value) return
    // 回填到行并同步合计
    editingRow.value._amounts = editingTempAmounts.value.slice()
    syncRowTotal(editingRow.value) // 你已有：把合计写回 _outboundQuantity
    sizeEditorVisible.value = false
}
async function viewOutboundRecord(arg: any) {
    // 兼容三种传法：整行对象 / 仅 id 字符串 / { outboundRecordId }
    const outboundRecordId = typeof arg === 'string' ? arg : arg?.outboundRecordId ?? arg?.outbound_record_id

    if (!outboundRecordId) {
        ElMessage.error('缺少出库记录ID')
        return
    }

    currentRow.value = arg || {} // 用来渲染打印头部（若只传了 id 也不会报错）

    try {
        const params = { outboundRecordId }
        const { data } = await axios.get(`${apiBaseUrl}/warehouse/getoutboundrecordbyrecordid`, { params })

        const list = Array.isArray(data) ? data : data ? [data] : []
        recordData.value = list.map((item: any) => {
            const cols: any[] = item?.shoeSizeColumns ?? []
            const displayShoeSizes = cols.map((name: any, j: number) => ({
                outboundAmount: item?.[`amount${j}`] ?? 0,
                shoeSizeColumns: name
            }))
            return { ...item, displayShoeSizes }
        })

        dialogVisible.value = true
    } catch (e) {
        console.error(e)
        ElMessage.error('获取出库单详情失败')
    }
}

function calculateOutboundTotal() {
    const number = (recordData.value || []).reduce((total: number, item: any) => {
        return total + (Number(item.outboundQuantity) || 0)
    }, 0)
    return Number(number).toFixed(2)
}

onMounted(async () => {
    loadStaffIdFromLocalStorage()
    console.log('当前 staffId=', staffId.value, '，允许的材料类型=', allowedTypeNames.value)
    await Promise.all([loadDepartments(), loadMaterialTypes()])
    await loadOrders() // 注意：现在会带上 staffId 过滤
})

/** 勾/取消单行时，同步到 selectedIdSet */
function onRowSelect(selection: any[], row: any) {
    const id = getRowId(row)
    if (!id) return
    if (selection.some((s) => String(s.materialStorageId) === id)) {
        selectedIdSet.value.add(id)
    } else {
        selectedIdSet.value.delete(id)
    }
}

/** 全选/全不选当前页 */
function onSelectAll(selection: any[]) {
    const pageIds = rows.value.map((r) => getRowId(r))
    if (selection.length === 0) {
        pageIds.forEach((id) => selectedIdSet.value.delete(id))
    } else {
        pageIds.forEach((id) => selectedIdSet.value.add(id))
    }
}

/** Element Plus 仍然会发这个事件，但它只包含“当前页”的选择。
 * 我们用它来纠正 selectedIdSet 与当前页的勾选一致性（防抖/幂等即可）。*/
function onSelectionChange(currentPageSelection: any[]) {
    const pageIdSet = new Set(rows.value.map((r) => getRowId(r)))
    const currentSelectedIds = new Set(currentPageSelection.map((r) => String(r.materialStorageId)))
    // 去掉当前页取消的
    rows.value.forEach((r) => {
        if (pageIdSet.has(r.materialStorageId) && !currentSelectedIds.has(r.materialStorageId)) {
            selectedIdSet.value.delete(r.materialStorageId)
        }
        const id = getRowId(r)
        if (pageIdSet.has(id) && !currentSelectedIds.has(id)) {
            selectedIdSet.value.delete(id)
        }
    })
    // 加上当前页新增的
    currentPageSelection.forEach((r) => selectedIdSet.value.add(String(r.materialStorageId)))
}
async function reload(preserveOriginal = true) {
    if (!query.orderRId) {
        ElMessage.warning('请先选择订单')
        return
    }
    loading.value = true
    try {
        const { data } = await axios.get(`${apiBaseUrl}/warehouse/orderoutbound/materials`, {
            params: {
                orderRId: query.orderRId,
                materialTypeId: query.materialTypeId,
                includeGeneral: includeGeneral.value,
                page: query.page,
                pageSize: query.pageSize,
                staffId: staffId.value ?? undefined // ← 新增
            }
        })
        const processed = (data?.result || []).map(normalizeRow)
        rows.value = processed
        rows.value.forEach((r) => {
            const id = getRowId(r)
            displayCache.set(id, {
                materialName: r?.materialName ?? '—',
                materialModel: r?.materialModel ?? '—',
                materialSpecification: r?.materialSpecification ?? '—',
                materialColor: r?.materialColor ?? '—',
                actualInboundUnit: r?.actualInboundUnit ?? '—',
                orderRId: query.orderRId,
                shoeRId: r?.shoeRId ?? '—',
                unitPrice: r?.unitPrice
            })
            const c = editCache.get(getRowId(r))
            if (c) {
                r._outboundQuantity = c.total
                // 如果有尺码列，回填 amounts
                if (Array.isArray(r._amounts) && Array.isArray(c.amounts) && r._amounts.length === c.amounts.length) {
                    r._amounts = c.amounts.slice()
                }
                r._remark = c.remark || ''
            }
        })
        total.value = data?.total || 0
        if (!preserveOriginal) originalRows.value = deepClone(processed)
        await loadRecords()
    } finally {
        loading.value = false
        // —— 关键：回勾当前页已选 —— //
        await nextTick()
        if (tableRef.value) {
            tableRef.value.clearSelection()
            rows.value.forEach((r) => {
                if (selectedIdSet.value.has(getRowId(r))) {
                    tableRef.value.toggleRowSelection(r, true)
                }
            })
        }
    }
}
function persistRowEdit(row: any) {
    const id = getRowId(row)
    if (!id) return
    editCache.set(id, {
        total: Number(row._outboundQuantity || 0),
        amounts: (row._amounts || []).map((x: number) => Number(x || 0)),
        remark: row._remark || ''
    })
}
</script>

<style scoped>
/* 视口高度：如果你的外层有固定头部高度（比如 56px），设置 --app-header=56px 即可 */
.page {
    height: calc(100vh - var(--app-header, 0px));
    display: flex;
    flex-direction: column;
}

/* 占满剩余空间的卡片 */
.card-fill {
    flex: 1 1 auto;
    display: flex;
    flex-direction: column;
    min-height: 0;
}
.card-fill :deep(.el-card__body) {
    display: flex;
    flex-direction: column;
    min-height: 0;
}

/* 卡片内部：上表格/下工具条 两行布局 */
.panel-grid {
    display: grid;
    grid-template-rows: 1fr auto;
    gap: 0.75rem;
    min-height: 0;
    height: 100%;
}
.panel-footer {
    display: flex;
    align-items: center;
    justify-content: space-between;
}

/* 简易工具类（沿用你之前的） */
.flex {
    display: flex;
}
.items-center {
    align-items: center;
}
.justify-between {
    justify-content: space-between;
}
.gap-2 {
    gap: 0.5rem;
}
.gap-3 {
    gap: 0.75rem;
}
.mb-3 {
    margin-bottom: 0.75rem;
}
.mt-3 {
    margin-top: 0.75rem;
}
.p-4 {
    padding: 1rem;
}
.opacity-80 {
    opacity: 0.8;
}
.text-sm {
    font-size: 0.875rem;
}

/* 尺码小组件 */
.size-cell {
    display: flex;
    align-items: center;
    gap: 0.25rem;
    margin: 0 0.25rem 0.25rem 0;
}
.size-name {
    font-size: 12px;
    opacity: 0.8;
    margin-right: 0.25rem;
}
.size-cap {
    font-size: 12px;
    opacity: 0.6;
    margin-left: 0.25rem;
}
/* 弹窗内尺码编辑面板：自动换行 + 卡片化 */
.size-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
    gap: 0.75rem;
    padding-right: 0.5rem; /* 避免滚动条盖住右侧 */
}
.size-box {
    border: 1px solid var(--el-border-color);
    border-radius: 8px;
    padding: 0.5rem;
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
}
.sb-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
}
.sb-name {
    font-size: 12px;
    font-weight: 600;
}
.sb-stock {
    font-size: 12px;
    opacity: 0.7;
}
/* 表格横向滚动容器 */
.x-scroll {
    overflow-x: auto;
    overflow-y: hidden;
    -webkit-overflow-scrolling: touch;
}

/* 表格内部最小宽度，避免被压扁（按你的列总宽度调整） */
:deep(.el-table__header),
:deep(.el-table__body) {
    min-width: 1100px;
}

/* 置底、粘滞的操作条，也能横向滚动 */
.sticky-footer {
    position: sticky;
    bottom: 0;
    z-index: 5;
    background: var(--el-bg-color);
    border-top: 1px solid var(--el-border-color);
    box-shadow: 0 -1px 6px rgba(0, 0, 0, 0.06);
}

/* 操作区允许横向滚动，按钮不再被截断 */
.footer-actions-scroll {
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
}

/* 让横向滚动生效：内部内容使用 inline-flex */
.footer-actions {
    display: inline-flex;
    align-items: center;
    gap: 0.75rem;
    padding-bottom: max(0.25rem, env(safe-area-inset-bottom));
}

/* 文本不换行，避免把行高挤高 */
.nowrap {
    white-space: nowrap;
}

/* 小屏下允许换行以进一步容错（可保留/删除） */
@media (max-width: 1200px) {
    .footer-actions {
        flex-wrap: wrap;
    }
}
</style>
