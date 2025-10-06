<template>
    <div class="page p-4">
        <!-- 顶部筛选 -->
        <el-card shadow="never" class="mb-3">
            <el-form :inline="true" :model="query" @submit.prevent>
                <el-form-item label="搜索">
                    <el-input v-model.trim="query.keyword" placeholder="订单号/客户/记录ID…" clearable style="width: 280px" @keyup.enter.native="reload">
                        <template #prefix
                            ><el-icon><Search /></el-icon
                        ></template>
                    </el-input>
                </el-form-item>
                <el-form-item>
                    <el-switch v-model="query.onlyPending" active-text="仅显示待填写用量" />
                </el-form-item>
                <el-form-item>
                    <el-button type="primary" :loading="list.loading" @click="reload">查询</el-button>
                    <el-button @click="reset">清空</el-button>
                    <el-button :loading="list.loading" :icon="Refresh" @click="reload">刷新</el-button>
                </el-form-item>
            </el-form>
        </el-card>

        <!-- 需要填写用量的补采记录列表 -->
        <el-card shadow="never" class="card-fill">
            <template #header>
                <div class="flex items-center justify-between">
                    <span>补采记录（需填写/核定用量）共 {{ list.total }} 条</span>
                    <small class="muted">提示：点击“填写用量”打开对话框进行逐项录入与核定。</small>
                </div>
            </template>

            <el-table :data="list.rows" border stripe size="small" v-loading="list.loading" @sort-change="onSortChange">
                <el-table-column type="index" width="60" />
                <el-table-column prop="orderRid" label="订单号" min-width="140">
                    <template #default="{ row }"
                        ><el-tag type="info" effect="plain">{{ row.orderRid }}</el-tag></template
                    >
                </el-table-column>
                <el-table-column prop="customerName" label="客户" min-width="140" />
                <el-table-column prop="createdAt" label="创建时间" width="160" sortable="custom" />
                <el-table-column prop="stageText" label="流程阶段" width="120" />
                <el-table-column prop="pendingNodeText" label="当前待办" width="160" />
                <el-table-column label="用量进度" width="160">
                    <template #default="{ row }">
                        <el-progress :text-inside="true" :stroke-width="16" :percentage="Math.min(100, Math.round((row.filledCount / Math.max(1, row.itemCount)) * 100))" />
                        <div class="muted small mt-2">{{ row.filledCount }} / {{ row.itemCount }}</div>
                    </template>
                </el-table-column>
                <el-table-column fixed="right" label="操作" width="150">
                    <template #default="{ row }">
                        <el-button size="small" type="primary" @click="openUsage(row)">填写用量</el-button>
                    </template>
                </el-table-column>
            </el-table>

            <div class="mt-3 flex items-center justify-end">
                <el-pagination
                    background
                    layout="total, sizes, prev, pager, next, jumper"
                    :total="list.total"
                    :current-page="pager.page"
                    :page-size="pager.pageSize"
                    :page-sizes="[10, 20, 50, 100]"
                    @current-change="onPageChange"
                    @size-change="onPageSizeChange"
                />
            </div>
        </el-card>

        <!-- 填写用量对话框 -->
        <el-dialog v-model="detailDialog.visible" title="补采记录详情" width="85%" :close-on-click-modal="false" :before-close="closeDialog" @closed="onDialogClose">
            <div v-loading="detailDialog.loading">
                <!-- 头部信息 -->
                <el-descriptions :column="3" border v-if="detailDialog.record">
                    <el-descriptions-item label="订单号">{{ detailDialog.record.orderRid }}</el-descriptions-item>
                    <el-descriptions-item label="客户">{{ detailDialog.record.customerName }}</el-descriptions-item>
                    <el-descriptions-item label="状态">{{ detailDialog.record.stageText }}</el-descriptions-item>
                    <el-descriptions-item label="创建时间">{{ detailDialog.record.createdAt }}</el-descriptions-item>
                    <el-descriptions-item label="原因">{{ detailDialog.record.reason || '-' }}</el-descriptions-item>
                    <el-descriptions-item label="备注" :span="3">{{ detailDialog.record.remark || '-' }}</el-descriptions-item>
                </el-descriptions>

                <!-- 订单数量（尺码分布） -->
                <el-divider>订单数量（尺码分布）</el-divider>
                <div class="flex items-center gap-2 mb-2">
                    <el-select
                        v-model="qtyColor"
                        placeholder="选择颜色后加载尺码分布"
                        style="width: 240px"
                        :disabled="!detailDialog.record || !shoeColorOptionsInDetail.length"
                        :loading="qtyLoading"
                        clearable
                    >
                        <el-option v-for="c in shoeColorOptionsInDetail" :key="c" :label="c" :value="c" />
                    </el-select>
                    <el-button type="primary" :loading="qtyLoading" :disabled="!qtyColor" @click="loadQtyTableByColor">加载</el-button>
                    <span class="muted">提示：点击下方“明细”任意一行，也会自动切换到该行的颜色并加载。</span>
                </div>

                <el-table v-loading="qtyLoading" :data="orderProduceInfo" border style="width: 100%" :span-method="arraySpanMethod" empty-text="选择颜色后加载">
                    <el-table-column prop="color" label="颜色" width="120" />
                    <el-table-column v-for="column in filteredColumns" :key="column.prop" :prop="column.prop" :label="column.label" min-width="80" />
                    <el-table-column prop="total" label="合计" width="120" />
                </el-table>

                <!-- 明细编辑工具条 -->
                <el-divider>明细（单位用量 / 核定用量 / 尺码材料）</el-divider>
                <div class="dlg-toolbar">
                    <div class="flex items-center gap-2">
                        <el-input v-model="usageKeyword" placeholder="搜索：颜色/材料名称/型号/规格/材料颜色" clearable style="width: 320px">
                            <template #prefix
                                ><el-icon><Search /></el-icon
                            ></template>
                        </el-input>
                        <el-button @click="recalcAllAutoRows">重算“自动核定”行</el-button>
                        <el-button @click="setAllMode(false)">全部设为自动核定</el-button>
                        <el-button @click="setAllMode(true)">全部设为手动核定</el-button>
                        <el-button @click="setSelectedMode(false)">所选行设自动</el-button>
                        <el-button @click="setSelectedMode(true)">所选行设手动</el-button>
                    </div>
                    <div class="flex gap-2 totals">
                        <span class="muted">当前筛选合计核定量：</span>
                        <el-tag type="success">{{ totalApproval }}</el-tag>
                    </div>
                </div>

                <!-- 明细表（可编辑） -->
                <el-table :data="usageFilteredRows" border stripe size="small" @row-click="onDetailRowClick" @selection-change="onSelectionChange">
                    <el-table-column type="selection" width="48" />
                    <el-table-column type="index" width="52" />
                    <el-table-column prop="shoeColorName" label="鞋型颜色" width="120" />
                    <el-table-column prop="materialType" label="材料大类" width="120">
                        <template #default="{ row }">
                            <span>{{ row.materialType }}</span>
                            <el-tag v-if="isSizeBased(row)" size="small" type="warning" class="ml-1">带尺码</el-tag>
                        </template>
                    </el-table-column>
                    <el-table-column prop="materialName" label="材料名称" width="160" />
                    <el-table-column prop="materialModel" label="型号" min-width="160" />
                    <el-table-column prop="materialSpecification" label="规格" min-width="200" />
                    <el-table-column prop="color" label="材料颜色" width="120" />

                    <el-table-column prop="orderQty" label="订单数量" width="110" align="right">
                        <template #default="{ row }">{{ row.orderQty }}</template>
                    </el-table-column>

                    <!-- 单位用量：带尺码材料禁用 -->
                    <el-table-column label="单位用量" width="160">
                        <template #default="{ row }">
                            <el-input-number
                                v-model="row.unitUsage"
                                :precision="4"
                                :step="0.0001"
                                :min="0"
                                controls-position="right"
                                :disabled="isSizeBased(row)"
                                @update:modelValue="(v: number) => onUnitUsageInput(row, v)"
                                @change="() => onUnitUsageChange(row)"
                            />
                        </template>
                    </el-table-column>

                    <!-- 手动核定：带尺码材料禁用 -->
                    <el-table-column label="手动核定" width="110" align="center">
                        <template #default="{ row }">
                            <el-switch v-model="row.manualApproval" :disabled="isSizeBased(row)" @change="onManualToggle(row)" />
                        </template>
                    </el-table-column>

                    <!-- 核定用量：带尺码材料=尺码之和（只读） -->
                    <el-table-column label="核定用量" width="180">
                        <template #default="{ row }">
                            <el-input-number
                                v-model="row.approvalUsage"
                                :precision="4"
                                :step="0.0001"
                                :min="0"
                                controls-position="right"
                                :disabled="isSizeBased(row) ? true : !row.manualApproval"
                                @change="onApprovalChange(row)"
                            />
                        </template>
                    </el-table-column>

                    <!-- 尺码数量入口 -->
                    <el-table-column label="尺码数量" width="140">
                        <template #default="{ row }">
                            <el-button v-if="isSizeBased(row)" type="primary" link @click="openSizeEditor(row)">编辑尺码</el-button>
                            <span v-else class="muted">-</span>
                        </template>
                    </el-table-column>
                </el-table>
            </div>

            <template #footer>
                <el-button @click="detailDialog.visible = false">关 闭</el-button>
                <el-button type="primary" :loading="detailDialog.saving" @click="saveUsage">保 存</el-button>
            </template>
        </el-dialog>

        <!-- ★ 带尺码材料：尺码数量编辑对话框 -->
        <el-dialog
            v-model="sizeEditor.visible"
            :title="`按尺码填写（${sizeEditor.row?.materialName || ''} / ${sizeEditor.row?.shoeColorName || ''}）`"
            width="50%"
            append-to-body
            :close-on-click-modal="false"
        >
            <div v-if="sizeEditor.visible">
                <div class="sizes-toolbar">
                    <el-button @click="fillFromOrderDistribution">用鞋型数量填充</el-button>
                    <el-button @click="clearAllSizes">清空</el-button>
                    <span class="muted ml-2">合计：</span>
                    <el-tag type="success">{{ sizeEditorTotal }}</el-tag>
                </div>

                <div class="sizes-grid">
                    <div v-for="col in sizeEditor.columns" :key="col.prop" class="size-cell">
                        <div class="size-label">{{ col.label }}</div>
                        <el-input-number v-model="sizeEditor.form[col.prop]" :min="0" :step="1" controls-position="right" @change="onSizeCellChange" />
                    </div>
                </div>
            </div>
            <template #footer>
                <el-button @click="sizeEditor.visible = false">取 消</el-button>
                <el-button type="primary" @click="applySizeEditor">确 定</el-button>
            </template>
        </el-dialog>
    </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref, computed, watch, nextTick, getCurrentInstance } from 'vue'
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Refresh } from '@element-plus/icons-vue'
import { getShoeSizesName } from '@/Pages/utils/getShoeSizesName'

/** ====== API ====== */
const API = {
    USAGE_TASKS: '/missing_material_purchase/usage_tasks',
    USAGE_FORM: '/missing_material_purchase/usage_form',
    USAGE_SAVE: '/missing_material_purchase/usage_save'
}
const apiBaseUrl = getCurrentInstance()?.appContext.config.globalProperties.$apiBaseUrl || ''

/** ====== 列表区 ====== */
const query = reactive({ keyword: '', onlyPending: true, sortProp: 'createdAt', sortOrder: 'desc' as 'asc' | 'desc' })
const pager = reactive({ page: 1, pageSize: 20 })
const list = reactive({ loading: false, total: 0, rows: [] as any[] })

function reset() {
    query.keyword = ''
    query.onlyPending = true
    pager.page = 1
    loadTasks()
}
function reload() {
    pager.page = 1
    loadTasks()
}
function onPageChange(p: number) {
    pager.page = p
    loadTasks()
}
function onPageSizeChange(sz: number) {
    pager.pageSize = sz
    reload()
}
function onSortChange({ prop, order }: any) {
    if (!prop) return
    query.sortProp = prop
    query.sortOrder = order === 'ascending' ? 'asc' : 'desc'
    reload()
}
async function loadTasks() {
    list.loading = true
    try {
        const params: any = {
            page: pager.page,
            pageSize: pager.pageSize,
            keyword: query.keyword || undefined,
            onlyPending: query.onlyPending ? 1 : 0,
            sortProp: query.sortProp,
            sortOrder: query.sortOrder
        }
        const { data } = await axios.get(`${apiBaseUrl}${API.USAGE_TASKS}`, { params })
        list.total = data?.total || 0
        list.rows = (data?.list || []).map((r: any) => ({
            id: r.id || r.record_id || r.recordId,
            orderRid: r.order_rid || r.orderRid,
            customerName: r.customer_name || r.customerName,
            createdAt: r.created_at || r.createdAt,
            stageText: r.stage_text || r.stageText,
            pendingNodeText: r.pending_node_text || r.pendingNodeText,
            itemCount: r.item_count ?? r.itemCount ?? 0,
            filledCount: r.filled_count ?? r.filledCount ?? 0
        }))
    } catch (e: any) {
        ElMessage.error(e?.message || '加载记录失败')
    } finally {
        list.loading = false
    }
}

/** ====== 尺码分布（订单数量） ====== */
const orderProduceInfo = ref<any[]>([])
const shoeSizeColumns = ref<Array<{ prop: string; label: string }>>([])
const qtyColor = ref<string>('')
const qtyLoading = ref(false)

const filteredColumns = computed(() => {
    const data = orderProduceInfo.value || []
    return (shoeSizeColumns.value || []).filter((col) => data.some((row) => row[col.prop] !== undefined && row[col.prop] !== null && Number(row[col.prop]) !== 0))
})
function arraySpanMethod({ row, column, rowIndex, columnIndex }: any) {
    const data = orderProduceInfo.value || []
    if (columnIndex === 0) {
        if (rowIndex > 0 && row.color === data[rowIndex - 1].color) return [0, 0]
        let rowspan = 1
        for (let i = rowIndex + 1; i < data.length; i++) {
            if (data[i].color === row.color) rowspan++
            else break
        }
        return [rowspan, 1]
    }
    if ((column as any).property === 'total') {
        let firstIdx = rowIndex
        for (let i = rowIndex - 1; i >= 0; i--) {
            if (data[i].color === row.color) firstIdx = i
            else break
        }
        if (rowIndex !== firstIdx) return [0, 0]
        let rowspan = 1
        for (let i = firstIdx + 1; i < data.length; i++) {
            if (data[i].color === row.color) rowspan++
            else break
        }
        return [rowspan, 1]
    }
}

/** ★ 当前颜色尺码总数（用于把“订单数量”同步到普通材料） */
function calcCurrentColorTotal(): number {
    const sizeProps = (shoeSizeColumns.value || []).map((c) => c.prop)
    let sum = 0
    for (const row of orderProduceInfo.value || []) {
        for (const p of sizeProps) {
            const v = Number(row?.[p] ?? 0)
            if (Number.isFinite(v)) sum += v
        }
    }
    return fix4(sum)
}
/** ★ 同步“订单数量”到该颜色所有普通材料（非尺码材料）的行 */
function applyOrderQtyFromSize(color: string) {
    if (!color) return
    const total = calcCurrentColorTotal()
    usageRows.value.forEach((r) => {
        if (r.shoeColorName === color && !isSizeBased(r)) {
            r.orderQty = total
            if (!r.manualApproval) {
                r.approvalUsage = fix4(r.unitUsage * r.orderQty)
            }
        }
    })
}

/** 拉尺码分布（并缓存列），随后同步普通材料的订单数量 */
async function getOrderShoeBatchInfo(orderRid: string, shoeRid: string, color: string, orderId?: number) {
    try {
        qtyLoading.value = true
        const resp = await axios.get(`${apiBaseUrl}/order/getordershoesizetotal`, { params: { orderid: orderRid, ordershoeid: shoeRid, color } })
        orderProduceInfo.value = Array.isArray(resp.data) ? resp.data : resp.data?.list || []
        const cols = await getShoeSizesName(orderId)
        shoeSizeColumns.value = (Array.isArray(cols) ? cols : [])
            .map((c: any) => {
                if (typeof c === 'string' || typeof c === 'number') {
                    const s = String(c)
                    return { prop: s, label: s }
                }
                const name = c?.prop ?? c?.name ?? c?.value ?? ''
                const label = c?.label ?? name
                return { prop: String(name), label: String(label) }
            })
            .filter((col) => col.prop)
        await nextTick()
        applyOrderQtyFromSize(color)
    } catch (e: any) {
        orderProduceInfo.value = []
        shoeSizeColumns.value = []
        ElMessage.error(e?.message || '加载尺码分布失败')
    } finally {
        qtyLoading.value = false
    }
}

/** ====== 用量对话框状态 & 行结构 ====== */
type DetailRecord = {
    id?: number
    orderId?: number
    orderShoeId?: number | null
    orderRid?: string
    shoeRid?: string | null
    customerName?: string
    createdAt?: string
    stageText?: string
    reason?: string
    remark?: string
}
const detailDialog = reactive({ visible: false, loading: false, saving: false, dirty: false, record: null as DetailRecord | null })

type SizeMap = Record<string, number> // key = 尺码列名（与 shoeSizeColumns 对齐）

type RowItem = {
    id: number
    orderShoeTypeId: number | null
    shoeColorName: string
    materialType?: string
    materialName: string
    materialModel: string
    materialSpecification: string
    color?: string
    orderQty: number
    unitUsage: number
    approvalUsage: number
    manualApproval: boolean
    /** ★ 带尺码材料专用 */
    sizeQuantities?: SizeMap
}

const usageHeader = ref<any>(null)
const usageRows = ref<RowItem[]>([])
const usageKeyword = ref('')
let currentRecordId: number | null = null
let selectedRows: RowItem[] = []

/** 识别带尺码材料 */
function isSizeBased(row: RowItem) {
    return ['大底', '中底', '烫底'].includes(String(row.materialType || ''))
}

/** 过滤 / 合计 */
const usageFilteredRows = computed(() => {
    const k = usageKeyword.value.trim().toLowerCase()
    if (!k) return usageRows.value
    return usageRows.value.filter((r) => [r.shoeColorName, r.materialName, r.materialModel, r.materialSpecification, r.color].filter(Boolean).some((t) => String(t).toLowerCase().includes(k)))
})
const totalApproval = computed(() => fix4(usageFilteredRows.value.reduce((s, r) => s + Number(r.approvalUsage || 0), 0)))

function fix4(n: any) {
    const v = Number(n || 0)
    return Math.round(v * 10000) / 10000
}
function approxEq(a: number, b: number, eps = 0.0001) {
    return Math.abs((a ?? 0) - (b ?? 0)) <= eps
}

/** 打开对话框并加载详情 */
async function openUsage(row: any) {
    currentRecordId = Number(row.id)
    detailDialog.visible = true
    await loadUsageForm()
}

async function loadUsageForm() {
  if (!currentRecordId) return
  detailDialog.loading = true
  try {
    const { data } = await axios.get(`${apiBaseUrl}${API.USAGE_FORM}`, { params: { id: currentRecordId } })
    usageHeader.value = data?.record || null

    // 表头
    detailDialog.record = usageHeader.value
      ? {
          id: usageHeader.value.id,
          orderId: usageHeader.value.orderId,
          orderShoeId: usageHeader.value.orderShoeId,
          orderRid: usageHeader.value.orderRid,
          shoeRid: usageHeader.value.shoeRid,
          customerName: usageHeader.value.customerName,
          createdAt: usageHeader.value.createdAt,
          stageText: usageHeader.value.stageText,
          reason: usageHeader.value.reason,
          remark: usageHeader.value.remark
        }
      : null

    const items = Array.isArray(data?.items) ? data.items : []

    // 如果有“带尺码”材料且还没有尺码列，则先把尺码列取回来（注意 await）
    const hasSizeBased = items.some((it: any) =>
      ['大底', '中底', '烫底'].includes(String(it.materialType || ''))
    )
    if (hasSizeBased && !shoeSizeColumns.value.length && detailDialog.record?.orderId) {
      const cols = await getShoeSizesName(detailDialog.record.orderId)
      shoeSizeColumns.value = (Array.isArray(cols) ? cols : []).map((c: any) => {
        if (typeof c === 'string' || typeof c === 'number') {
          const s = String(c)
          return { prop: s, label: s }
        }
        const prop = String(c?.prop ?? c?.name ?? c?.value ?? '')
        const label = String(c?.label ?? prop)
        return { prop, label }
      }).filter(col => col.prop)
    }

    // ===== 关键：一定要 return row =====
    usageRows.value = items.map((it: any) => {
      const orderQty = Number(it.orderQty || 0)
      const unit = Number(it.unitUsage ?? 0)
      const autoVal = fix4(unit * orderQty)
      const approve = Number(it.approvalUsage ?? 0)
      const manual = !approxEq(approve, autoVal)

      const row: RowItem = {
        id: Number(it.id),
        orderShoeTypeId: it.orderShoeTypeId ?? null,
        shoeColorName: it.shoeColorName || '',
        materialType: it.materialType || '',
        materialName: it.materialName || '',
        materialModel: it.materialModel || '',
        materialSpecification: it.materialSpecification || '',
        color: it.color || '',
        orderQty,
        unitUsage: fix4(unit),
        approvalUsage: manual ? fix4(approve) : autoVal,
        manualApproval: manual
      }

      // 带尺码材料：优先使用后端数组，再兼容旧 map
      if (isSizeBased(row)) {
        if (Array.isArray(it.sizeQuantitiesArr)) {
          // 现在已确保有 shoeSizeColumns，可安全还原为 Map
          row.sizeQuantities = arrayToMap(it.sizeQuantitiesArr, shoeSizeColumns.value)
          row.approvalUsage = Object.values(row.sizeQuantities).reduce((s, n) => s + Number(n || 0), 0)
          row.manualApproval = false
        } else if (it.sizeQuantities) {
          row.sizeQuantities = normalizeSizeMap(it.sizeQuantities)
          row.approvalUsage = Object.values(row.sizeQuantities).reduce((s, n) => s + Number(n || 0), 0)
          row.manualApproval = false
        }
      }

      return row                // ←←← 这行是你缺失的
    })

    // 预选颜色并加载尺码分布（用于“默认=鞋型数量”）
    const firstColor = shoeColorOptionsInDetail.value[0]
    qtyColor.value = firstColor || ''
    orderProduceInfo.value = []
    if (firstColor && detailDialog.record?.orderRid && detailDialog.record?.shoeRid) {
      await getOrderShoeBatchInfo(
        detailDialog.record.orderRid,
        detailDialog.record.shoeRid,
        firstColor,
        detailDialog.record.orderId
      )
    }

    detailDialog.dirty = false
  } catch (e: any) {
    ElMessage.error(e?.message || '加载用量详情失败')
  } finally {
    detailDialog.loading = false
  }
}


/** 可选颜色来源 */
const shoeColorOptionsInDetail = computed(() => {
    const set = new Set<string>()
    for (const it of usageRows.value || []) {
        if ((it as any)?.shoeColorName) set.add((it as any).shoeColorName)
    }
    return Array.from(set)
})

/** 切换颜色并加载尺码分布 */
async function loadQtyTableByColor() {
    if (!detailDialog?.record?.orderRid || !detailDialog?.record?.shoeRid) {
        ElMessage.warning('缺少订单标识')
        return
    }
    if (!qtyColor.value) {
        ElMessage.warning('请选择颜色')
        return
    }
    await getOrderShoeBatchInfo(detailDialog.record.orderRid, detailDialog.record.shoeRid, qtyColor.value, detailDialog.record.orderId)
}
function onDetailRowClick(row: RowItem) {
    if (!row?.shoeColorName) return
    qtyColor.value = row.shoeColorName
    loadQtyTableByColor()
}

/** —— 普通材料：自动计算 —— */
function onUnitUsageInput(row: RowItem, v: number) {
    if (isSizeBased(row)) return
    row.unitUsage = fix4(v)
    if (!row.manualApproval) {
        row.approvalUsage = fix4(row.unitUsage * row.orderQty)
    }
    detailDialog.dirty = true
}
function onUnitUsageChange(row: RowItem) {
    if (isSizeBased(row)) return
    row.unitUsage = fix4(row.unitUsage)
    if (!row.manualApproval) {
        row.approvalUsage = fix4(row.unitUsage * row.orderQty)
    }
    detailDialog.dirty = true
}
function onManualToggle(row: RowItem) {
    if (isSizeBased(row)) return
    if (!row.manualApproval) {
        row.approvalUsage = fix4(row.unitUsage * row.orderQty)
    }
    detailDialog.dirty = true
}
function onApprovalChange(row: RowItem) {
    if (isSizeBased(row)) return
    row.approvalUsage = fix4(row.approvalUsage)
    if (!row.manualApproval) row.manualApproval = true
    detailDialog.dirty = true
}
function recalcAllAutoRows() {
    usageRows.value.forEach((r) => {
        if (isSizeBased(r)) return
        if (!r.manualApproval) r.approvalUsage = fix4(r.unitUsage * r.orderQty)
    })
    detailDialog.dirty = true
}
function setAllMode(manual: boolean) {
    usageRows.value.forEach((r) => {
        if (isSizeBased(r)) return
        r.manualApproval = manual
        if (!manual) r.approvalUsage = fix4(r.unitUsage * r.orderQty)
    })
    detailDialog.dirty = true
}
function setSelectedMode(manual: boolean) {
    selectedRows.forEach((r) => {
        if (isSizeBased(r)) return
        r.manualApproval = manual
        if (!manual) r.approvalUsage = fix4(r.unitUsage * r.orderQty)
    })
    detailDialog.dirty = true
}
function onSelectionChange(rows: RowItem[]) {
    selectedRows = rows || []
}

/** 兜底监听：普通材料联动；尺码材料=尺码之和 */
watch(
    usageRows,
    (rows) => {
        if (!Array.isArray(rows)) return
        rows.forEach((r) => {
            if (isSizeBased(r)) {
                r.approvalUsage = sumSizeMap(r.sizeQuantities)
            } else {
                if (!r.manualApproval) r.approvalUsage = fix4((+r.unitUsage || 0) * (+r.orderQty || 0))
            }
        })
    },
    { deep: true }
)

/** ====== 带尺码材料：编辑对话框 ====== */
const sizeEditor = reactive({
    visible: false,
    row: null as RowItem | null,
    color: '', // 当前编辑行的颜色
    columns: [] as Array<{ prop: string; label: string }>, // 固定列快照，保持位置一致
    form: {} as SizeMap // 每个尺码的数量
})

function openSizeEditor(row: RowItem) {
    sizeEditor.row = row
    sizeEditor.color = row.shoeColorName
    // 切到该颜色并确保尺码分布与列加载完成
    qtyColor.value = row.shoeColorName
    loadQtyTableByColor().then(async () => {
        await nextTick()
        sizeEditor.columns = [...shoeSizeColumns.value] // 固定列顺序
        // 默认：若该行还没有填过尺码数量 => 用鞋型数量填充
        if (!row.sizeQuantities || Object.keys(row.sizeQuantities).length === 0) {
            sizeEditor.form = buildDefaultSizeMapFromOrderTable()
        } else {
            // 以现有数据为主，同时补全缺失尺码为0
            const map = normalizeSizeMap(row.sizeQuantities)
            for (const c of sizeEditor.columns) {
                if (map[c.prop] == null) map[c.prop] = 0
            }
            sizeEditor.form = map
        }
        sizeEditor.visible = true
    })
}

/** 尺码编辑：工具函数 */
function buildDefaultSizeMapFromOrderTable(): SizeMap {
    const map: SizeMap = {}
    for (const c of shoeSizeColumns.value || []) {
        map[c.prop] = 0
    }
    for (const row of orderProduceInfo.value || []) {
        for (const c of shoeSizeColumns.value || []) {
            const v = Number(row?.[c.prop] ?? 0)
            if (Number.isFinite(v)) map[c.prop] = (map[c.prop] || 0) + v
        }
    }
    return map
}
function normalizeSizeMap(src: any): SizeMap {
    const map: SizeMap = {}
    for (const c of shoeSizeColumns.value || []) {
        const key = c.prop
        const v = Number(src?.[key] ?? 0)
        map[key] = Number.isFinite(v) ? v : 0
    }
    return map
}
function sumSizeMap(map?: SizeMap): number {
    if (!map) return 0
    return fix4(Object.values(map).reduce((s, n) => s + Number(n || 0), 0))
}
const sizeEditorTotal = computed(() => sumSizeMap(sizeEditor.form))

function fillFromOrderDistribution() {
    sizeEditor.form = buildDefaultSizeMapFromOrderTable()
}
function clearAllSizes() {
    const obj: SizeMap = {}
    for (const c of sizeEditor.columns) {
        obj[c.prop] = 0
    }
    sizeEditor.form = obj
}
function onSizeCellChange() {
    /* 联动合计即刻生效，computed 已处理 */
}

function applySizeEditor() {
    if (!sizeEditor.row) return
    // 落到行
    sizeEditor.row.sizeQuantities = { ...sizeEditor.form }
    sizeEditor.row.approvalUsage = sumSizeMap(sizeEditor.form) // 核定=尺码和
    sizeEditor.row.manualApproval = false
    detailDialog.dirty = true
    sizeEditor.visible = false
}

/** 保存（★ 尺码材料会额外带上 sizeQuantities） */
async function saveUsage() {
    if (!currentRecordId) return
    try {
        detailDialog.saving = true
        const payload = {
            recordId: currentRecordId,
            items: usageRows.value.map((r) => {
                if (isSizeBased(r)) {
                    return {
                        id: r.id,
                        approvalUsage: r.approvalUsage, // 后端会用数组合计覆盖，可保留
                        sizeQuantitiesArr: mapToArray(r.sizeQuantities || {}, shoeSizeColumns.value)
                    }
                } else {
                    return {
                        id: r.id,
                        unitUsage: r.unitUsage,
                        approvalUsage: r.approvalUsage
                    }
                }
            })
        }
        const { data } = await axios.post(`${apiBaseUrl}${API.USAGE_SAVE}`, payload)
        if (data?.success) {
            ElMessage.success('保存成功')
            detailDialog.dirty = false
            loadTasks()
        } else {
            throw new Error(data?.message || '保存失败')
        }
    } catch (e: any) {
        ElMessage.error(e?.message || '保存失败')
    } finally {
        detailDialog.saving = false
    }
}

/** 关闭对话框 */
function closeDialog(done: () => void) {
    if (!detailDialog.dirty) {
        done()
        return
    }
    ElMessageBox.confirm('存在未保存的更改，确定关闭吗？', '提示', { type: 'warning' })
        .then(() => done())
        .catch(() => {})
}
function onDialogClose() {
    selectedRows = []
    usageKeyword.value = ''
}
function mapToArray(map: Record<string, number>, cols: Array<{prop:string;label:string}>): number[] {
  return (cols||[]).map(c => Number(map?.[c.prop] ?? 0))
}
function arrayToMap(arr: number[], cols: Array<{prop:string;label:string}>): Record<string, number> {
  const m: Record<string, number> = {}
  cols.forEach((c, i) => { m[c.prop] = Number(arr?.[i] ?? 0) })
  return m
}

/** 初始加载 */
onMounted(() => loadTasks())
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
.mt-2 {
    margin-top: 8px;
}
.mt-3 {
    margin-top: 12px;
}
.gap-2 {
    gap: 8px;
}
.small {
    font-size: 12px;
}
.muted {
    color: #999;
}
.dlg-toolbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin: 8px 0 12px;
}
.totals {
    align-items: center;
}

/* ★ 尺码编辑弹窗样式 */
.sizes-toolbar {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 12px;
}
.sizes-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
    gap: 12px;
}
.size-cell {
    padding: 8px;
    border: 1px solid #eee;
    border-radius: 8px;
}
.size-label {
    font-size: 12px;
    color: #666;
    margin-bottom: 6px;
}
.ml-1 {
    margin-left: 4px;
}
.ml-2 {
    margin-left: 8px;
}
</style>
