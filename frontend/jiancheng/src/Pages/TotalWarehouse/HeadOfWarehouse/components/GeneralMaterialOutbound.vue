<template>
    <div class="general-outbound">
        <el-card shadow="never" class="header-card">
            <div class="flex items-center justify-between">
                <div class="title">
                    <span>通用材料出库</span>
                    <el-tag size="small" type="info" class="ml-2">无订单绑定</el-tag>
                </div>
                <div class="hint">仅展示无订单绑定的材料库存（如包材、办公消耗、生产工具等）。</div>
            </div>
        </el-card>

        <el-card v-if="categoryTabs.length > 1" shadow="never" class="mb-3">
            <el-tabs v-model="activeTab" type="card" @tab-change="onTabChange">
                <el-tab-pane v-for="t in categoryTabs" :key="t.key" :label="t.label" :name="t.key" />
            </el-tabs>
        </el-card>

        <el-card shadow="never" class="mb-3">
            <el-form :inline="true">
                <el-form-item label="材料名称">
                    <el-input v-model.trim="filters.materialName" clearable placeholder="材料名称" style="width: 180px"
                        @change="reload" @clear="reload" />
                </el-form-item>
                <el-form-item label="厂家">
                    <el-input v-model.trim="filters.supplierName" clearable placeholder="厂家" style="width: 180px"
                        @change="reload" @clear="reload" />
                </el-form-item>
                <el-form-item label="型号">
                    <el-input v-model.trim="filters.materialModel" clearable placeholder="型号" style="width: 140px"
                        @change="reload" @clear="reload" />
                </el-form-item>
                <el-form-item label="规格">
                    <el-input v-model.trim="filters.materialSpec" clearable placeholder="规格" style="width: 140px"
                        @change="reload" @clear="reload" />
                </el-form-item>
                <el-form-item>
                    <el-button type="primary" :loading="loading" @click="reload">查询</el-button>
                    <el-button @click="resetFilters">清空筛选</el-button>
                </el-form-item>
            </el-form>
        </el-card>

        <el-card shadow="never">
            <template #header>
                <div class="flex items-center justify-between">
                    <div>可出库材料（{{ total }}）</div>
                    <div class="text-sm opacity-80">已选 {{ selectedRows.length }} 条，合计出库：{{ totalOutbound }}</div>
                </div>
            </template>

            <el-table ref="tableRef" :data="rows" border stripe size="small" height="55vh"
                :row-key="(row) => row.materialStorageId" @selection-change="onSelectionChange">
                <el-table-column type="selection" width="40" />
                <el-table-column prop="materialName" label="材料" min-width="120" show-overflow-tooltip />
                <el-table-column prop="supplierName" label="厂家" min-width="120" show-overflow-tooltip />
                <el-table-column prop="materialType" label="材料类型" min-width="90" />
                <el-table-column prop="materialModel" label="型号" min-width="80" show-overflow-tooltip />
                <el-table-column prop="materialSpecification" label="规格" min-width="100" show-overflow-tooltip />
                <el-table-column prop="materialColor" label="颜色" min-width="60" />
                <el-table-column prop="actualInboundUnit" label="单位" width="60" />
                <el-table-column prop="allowedOutboundAmount" label="可出库库存" min-width="100" />
                <el-table-column label="出库数量" min-width="120">
                    <template #default="{ row }">
                        <el-input-number v-model="row._outboundQuantity" size="small" :min="0"
                            :max="Number(row.allowedOutboundAmount) || 0" :step="1" />
                    </template>
                </el-table-column>
                <el-table-column label="备注" min-width="140">
                    <template #default="{ row }">
                        <el-input v-model="row._remark" placeholder="可选" size="small" />
                    </template>
                </el-table-column>
            </el-table>

            <div class="flex items-center justify-between" style="margin-top: 8px;">
                <el-pagination background layout="total, prev, pager, next, jumper" :total="total"
                    :page-size="pageSize" :current-page="currentPage" @current-change="(p) => { currentPage = p; reload() }" />
                <div class="flex items-center gap-3 footer-actions">
                    <el-select size="small" v-model="form.outboundType" style="width: 130px">
                        <el-option label="行政出库" :value="6" />
                        <el-option label="废料处理" :value="1" />
                    </el-select>
                    <el-select size="small" v-model="form.departmentId" placeholder="出库至部门(可选)" style="width: 180px"
                        filterable clearable>
                        <el-option v-for="d in departments" :key="d.value" :label="d.label" :value="d.value" />
                    </el-select>
                    <el-input size="small" v-model.trim="form.picker" placeholder="领料人" style="width: 130px" />
                    <el-input size="small" v-model.trim="form.remark" placeholder="用途说明（建议必填）" style="width: 220px" />
                    <el-button size="small" type="primary" :loading="submitting"
                        :disabled="selectedRows.length === 0" @click="openConfirm">提交出库</el-button>
                </div>
            </div>
        </el-card>

        <el-dialog v-model="dialogVisible" title="确认出库" width="60%">
            <el-table :data="previewItems" border stripe size="small">
                <el-table-column prop="materialName" label="材料" min-width="140" show-overflow-tooltip />
                <el-table-column prop="supplierName" label="厂家" min-width="120" show-overflow-tooltip />
                <el-table-column prop="materialModel" label="型号" min-width="100" show-overflow-tooltip />
                <el-table-column prop="materialSpecification" label="规格" min-width="100" show-overflow-tooltip />
                <el-table-column prop="materialColor" label="颜色" min-width="60" />
                <el-table-column prop="actualInboundUnit" label="单位" width="60" />
                <el-table-column prop="outboundQuantity" label="出库数量" min-width="100" />
                <el-table-column prop="remark" label="备注" min-width="120" show-overflow-tooltip />
            </el-table>
            <div class="dialog-summary">
                出库类型：{{ form.outboundType === 1 ? '废料处理' : '行政出库' }}
                <span style="margin-left: 16px;">合计件数：{{ previewItems.length }}</span>
                <span style="margin-left: 16px;">合计数量：{{ previewTotal }}</span>
            </div>
            <template #footer>
                <el-button @click="dialogVisible = false">取消</el-button>
                <el-button type="primary" :loading="submitting" @click="submit">确认提交</el-button>
            </template>
        </el-dialog>
    </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, getCurrentInstance } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'

const apiBaseUrl = (getCurrentInstance() as any)?.appContext.config.globalProperties.$apiBaseUrl

interface CategoryTab { key: string; label: string; typeNames: string[] }
const ALL_CATEGORY_TABS: CategoryTab[] = [
    { key: 'all', label: '全部', typeNames: [] },
    { key: 'fabric', label: '面料/里料/复合仓', typeNames: ['面料', '里料', '复合'] },
    { key: 'sole', label: '底材仓', typeNames: ['底材'] },
    { key: 'package', label: '包材仓', typeNames: ['包材'] },
    { key: 'aux', label: '辅料及饰品仓', typeNames: ['辅料', '饰品'] },
    { key: 'chemical', label: '化工仓', typeNames: ['化工'] },
    { key: 'tools', label: '生产工具', typeNames: ['生产工具'] },
    { key: 'process', label: '加工', typeNames: ['加工'] },
    { key: 'knife', label: '刀模', typeNames: ['刀模'] },
    { key: 'last', label: '楦头', typeNames: ['楦头'] },
    { key: 'office', label: '办公后勤', typeNames: ['办公后勤'] },
    { key: 'dev', label: '开发样品', typeNames: ['开发样品'] },
    { key: 'asset', label: '固定资产', typeNames: ['固定资产'] }
]

// 通用材料出库 — 角色级类型白名单（与后端 ROLE_GENERAL_OUTBOUND_TYPENAMES 对齐）。
// 未列出的角色将被后端拒绝；这里同步前端 UI 表现。
const GENERAL_OUTBOUND_ROLE_TYPES: Record<number, string[] | null> = {
    8: null,                                       // 总仓经理 -> 不限
    20: ['包材'],                                   // 成品仓
    23: ['生产工具', '办公后勤', '开发样品']         // 总仓文员
}
// 专仓文员 staff_id -> 可出库类型（与按订单出库保持一致）。
// role=23 同时命中专仓 staff 时，优先使用这个映射；总仓文员不在里面，仍走角色映射。
const STAFF_GENERAL_OUTBOUND_TYPES: Record<number, string[]> = {
    40: ['面料', '里料', '复合'],
    41: ['底材'],
    42: ['包材'],
    11: ['辅料', '饰品']
}
const HEAD_OF_WAREHOUSE_ROLE = 8

const staffId = ref<number | null>(null)
const userRole = ref<number | null>(null)
function loadIdentity() {
    try {
        const v = localStorage.getItem('staffid')
        staffId.value = v != null && v !== '' ? Number(v) : null
        const r = localStorage.getItem('role')
        userRole.value = r != null && r !== '' ? Number(r) : null
    } catch {
        staffId.value = null
        userRole.value = null
    }
}

const allowedRoleTypes = computed<string[] | null>(() => {
    if (userRole.value == null) return []
    // role=23 下，专仓文员优先使用 staff 映射（与按订单出库保持一致）
    if (staffId.value != null && staffId.value in STAFF_GENERAL_OUTBOUND_TYPES) {
        return STAFF_GENERAL_OUTBOUND_TYPES[staffId.value]
    }
    if (!(userRole.value in GENERAL_OUTBOUND_ROLE_TYPES)) return []
    return GENERAL_OUTBOUND_ROLE_TYPES[userRole.value]
})
const isRoleRestricted = computed(() => allowedRoleTypes.value !== null)

const categoryTabs = computed<CategoryTab[]>(() => {
    const allowed = allowedRoleTypes.value
    if (allowed === null) return ALL_CATEGORY_TABS
    if (allowed.length === 0) return []
    // 仅保留与角色权限相交的 tab；如果只剩一个，则不显示 “全部”
    const filtered: CategoryTab[] = []
    for (const tab of ALL_CATEGORY_TABS) {
        if (tab.key === 'all') continue
        const inter = tab.typeNames.filter((n) => allowed.includes(n))
        if (inter.length > 0) {
            filtered.push({ ...tab, typeNames: inter })
        }
    }
    return filtered
})

const activeTab = ref<string>('all')
const activeTypeNames = computed<string[]>(() => {
    const t = categoryTabs.value.find((x) => x.key === activeTab.value)
    if (t) return t.typeNames
    // 回退：默认使用首个 tab
    return categoryTabs.value[0]?.typeNames ?? []
})

const filters = reactive({
    materialName: '',
    supplierName: '',
    materialModel: '',
    materialSpec: ''
})
const form = reactive({
    outboundType: 6 as 1 | 6,
    departmentId: undefined as number | undefined,
    picker: '',
    remark: ''
})
const rows = ref<any[]>([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(10)
const loading = ref(false)
const submitting = ref(false)
const selectedRows = ref<any[]>([])
const dialogVisible = ref(false)
const departments = ref<any[]>([])
const tableRef = ref<any>(null)

const totalOutbound = computed(() =>
    selectedRows.value.reduce((s, r) => s + (Number(r._outboundQuantity) || 0), 0)
)
const previewItems = computed(() =>
    selectedRows.value.map((r) => ({
        ...r,
        outboundQuantity: Number(r._outboundQuantity) || 0,
        remark: r._remark || ''
    }))
)
const previewTotal = computed(() =>
    previewItems.value.reduce((s, r) => s + (Number(r.outboundQuantity) || 0), 0)
)

function onSelectionChange(list: any[]) {
    selectedRows.value = list
}
function onTabChange() {
    currentPage.value = 1
    reload()
}
function resetFilters() {
    filters.materialName = ''
    filters.supplierName = ''
    filters.materialModel = ''
    filters.materialSpec = ''
    currentPage.value = 1
    reload()
}
async function reload() {
    loading.value = true
    try {
        const params: any = {
            page: currentPage.value,
            pageSize: pageSize.value,
            materialName: filters.materialName || undefined,
            supplierName: filters.supplierName || undefined,
            materialModel: filters.materialModel || undefined,
            materialSpec: filters.materialSpec || undefined,
            materialTypeNames: activeTypeNames.value.length
                ? activeTypeNames.value.join(',')
                : undefined,
            // 后端会优先以服务端 staff_id 判断专仓文员权限，前端不再需要传 staffId
            staffId: undefined
        }
        const { data } = await axios.get(
            `${apiBaseUrl}/warehouse/generaloutbound/materials`,
            { params }
        )
        const list = (data?.result || []).map((r: any) => ({
            ...r,
            _outboundQuantity: 0,
            _remark: ''
        }))
        rows.value = list
        total.value = data?.total || 0
    } catch (e) {
        console.error(e)
        ElMessage.error('加载材料失败')
    } finally {
        loading.value = false
    }
}
async function loadDepartments() {
    try {
        const { data } = await axios.get(`${apiBaseUrl}/general/getalldepartments`)
        departments.value = Array.isArray(data) ? data : []
    } catch (e) {
        console.error(e)
    }
}
function openConfirm() {
    if (selectedRows.value.length === 0) return ElMessage.warning('请选择要出库的材料')
    for (const r of selectedRows.value) {
        const q = Number(r._outboundQuantity) || 0
        if (q <= 0) {
            return ElMessage.error(`材料 [${r.materialName}] 的出库数量必须大于 0`)
        }
        if (q > Number(r.allowedOutboundAmount)) {
            return ElMessage.error(`材料 [${r.materialName}] 的出库数量超出可用库存`)
        }
    }
    if (!form.remark || !form.remark.trim()) {
        return ElMessage.warning('请填写用途说明（remark）')
    }
    dialogVisible.value = true
}
async function submit() {
    submitting.value = true
    try {
        const items = selectedRows.value.map((r) => ({
            materialStorageId: r.materialStorageId,
            outboundQuantity: Number(r._outboundQuantity) || 0,
            remark: r._remark || ''
        }))
        const payload = {
            outboundType: form.outboundType,
            departmentId: form.departmentId,
            picker: form.picker,
            remark: form.remark,
            items
        }
        const { data } = await axios.post(
            `${apiBaseUrl}/warehouse/generaloutbound/create`,
            payload
        )
        ElMessage.success(`出库成功，单号 ${data.outboundRId}`)
        dialogVisible.value = false
        selectedRows.value = []
        if (tableRef.value) tableRef.value.clearSelection()
        await reload()
    } catch (e: any) {
        const msg = e?.response?.data?.message || '提交失败'
        ElMessage.error(msg)
    } finally {
        submitting.value = false
    }
}

onMounted(() => {
    loadIdentity()
    // 角色受限时使用第一个允许的 tab；不受限则保持 'all'
    const tabs = categoryTabs.value
    if (tabs.length > 0 && !tabs.find((t) => t.key === activeTab.value)) {
        activeTab.value = tabs[0].key
    }
    loadDepartments()
    reload()
})
</script>

<style scoped>
.general-outbound {
    display: flex;
    flex-direction: column;
    gap: 12px;
}

.header-card .title {
    font-size: 16px;
    font-weight: 600;
}

.header-card .hint {
    color: #909399;
    font-size: 13px;
}

.ml-2 {
    margin-left: 8px;
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

.gap-3 {
    gap: 12px;
}

.text-sm {
    font-size: 13px;
}

.opacity-80 {
    opacity: 0.8;
}

.dialog-summary {
    margin-top: 12px;
    color: #606266;
    font-size: 13px;
}

.mb-3 {
    margin-bottom: 12px;
}
</style>
