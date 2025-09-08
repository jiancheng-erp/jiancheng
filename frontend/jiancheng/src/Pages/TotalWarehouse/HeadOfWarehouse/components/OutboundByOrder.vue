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
                <template #header>有材料可出库的订单（{{ orderTotal }}）</template>

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
                        <div class="text-sm opacity-80">已选 {{ selectedItems.length }} 条，合计出库：{{ totalOutbound }}</div>
                    </div>
                </template>

                <div class="panel-grid">
                    <!-- 表格占满 -->
                    <el-table :data="rows" border stripe height="100%" @selection-change="onSelect">
                        <el-table-column type="selection" width="44" />
                        <el-table-column prop="materialName" label="材料" width="140" />
                        <el-table-column prop="materialModel" label="型号" width="160" show-overflow-tooltip />
                        <el-table-column prop="materialSpecification" label="规格" width="160" show-overflow-tooltip />
                        <el-table-column prop="materialColor" label="颜色" width="100" />
                        <el-table-column prop="supplierName" label="供应商" width="160" show-overflow-tooltip />
                        <el-table-column prop="actualInboundUnit" label="单位" width="80" />
                        <el-table-column prop="currentAmount" label="库存" width="100" />

                        <el-table-column label="按尺码分配" min-width="220">
                            <template #default="{ row }">
                                <div class="flex items-center gap-3">
                                    <span class="text-sm opacity-80"> 合计 {{ row._outboundQuantity || 0 }} / 库存 {{ row.currentAmount || 0 }} </span>
                                    <el-button type="primary" link @click="openSizeEditor(row)">编辑尺码</el-button>
                                </div>
                            </template>
                        </el-table-column>

                        <el-table-column label="出库总数" width="160">
                            <template #default="{ row }">
                                <el-input-number v-model="row._outboundQuantity" :min="0" :max="row.currentAmount" :step="1" @change="syncRowByTotal(row)" />
                            </template>
                        </el-table-column>

                        <el-table-column label="备注" width="180">
                            <template #default="{ row }">
                                <el-input v-model="row._remark" placeholder="可选" />
                            </template>
                        </el-table-column>
                    </el-table>

                    <!-- 操作区固定在底部 -->
                    <div class="panel-footer flex items-center justify-between">
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
                        <div class="flex items-center gap-3">
                            <!-- 出库至部门 -->
                            <el-select v-model="form.departmentId" placeholder="出库至部门" style="width: 200px" filterable clearable>
                                <el-option v-for="d in departments" :key="d.value" :label="d.label" :value="d.value" />
                            </el-select>
                            <el-input v-model.trim="form.picker" placeholder="领料人" style="width: 160px" />
                            <el-input v-model.trim="form.remark" placeholder="整单备注（可选）" style="width: 220px" />
                            <el-button type="primary" :loading="submitting" @click="submit">提交出库</el-button>
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
        </template>
    </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, getCurrentInstance } from 'vue'
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'

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
            params: { keyword: orderQuery.keyword, page: orderQuery.page, pageSize: orderQuery.pageSize }
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
  id: number;
  name: string;
}

/** 材料区 */
const loading = ref(false)
const submitting = ref(false)
const includeGeneral = ref(0)
const materialTypes = ref<MaterialType[]>([]);

const loadMaterialTypes = async () => {
  try {
    const res = await axios.get(`${apiBaseUrl}/logistics/getallmaterialtypes`);
    // 后端返回的每一项包含 materialTypeId 和 materialTypeName
    materialTypes.value = res.data.map((item: any) => ({
      id: item.materialTypeId,
      name: item.materialTypeName,
    }));
  } catch (err) {
    console.error("获取物料类型失败", err);
  }
};
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

async function reload(preserveOriginal = true) {
    if (!query.orderRId) {
        ElMessage.warning('请先选择订单')
        return
    }
    loading.value = true
    try {
        const { data } = await axios.get(`${apiBaseUrl}/warehouse/orderoutbound/materials`, {
            params: { orderRId: query.orderRId, materialTypeId: query.materialTypeId, includeGeneral: includeGeneral.value, page: query.page, pageSize: query.pageSize }
        })
        const processed = (data?.result || []).map(normalizeRow)
        rows.value = processed
        total.value = data?.total || 0
        if (!preserveOriginal) originalRows.value = deepClone(processed)
        await loadRecords()
    } finally {
        loading.value = false
    }
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
}

function onSelect(list: any[]) {
    selectedItems.value = list
}
function syncRowTotal(row: any) {
    row._outboundQuantity = (row._amounts || []).reduce((s: number, v: number) => s + (Number(v) || 0), 0)
}
function syncRowByTotal(row: any) {
    let remaining = Number(row._outboundQuantity || 0)
    for (let i = 0; i < (row._amounts || []).length; i++) {
        const cap = Number(row[`currentAmount${i}`] || 0)
        const take = Math.min(cap, remaining)
        row._amounts[i] = take
        remaining -= take
    }
}

async function submit() {
    if (!query.orderRId) {
        ElMessage.warning('缺少订单号')
        return
    }
    if (selectedItems.value.length === 0) {
        ElMessage.warning('请选择要出库的材料')
        return
    }
    if (form.departmentId == null) {
        ElMessage.warning('请选择出库至部门')
        return
    } // ← 新增校验

    const items = selectedItems.value.map((r: any) => {
        const payload: any = { materialStorageId: r.materialStorageId, outboundQuantity: Number(r._outboundQuantity || 0), remark: r._remark || '' }
        ;(r._amounts || []).forEach((val: number, i: number) => (payload[`amount${i}`] = Number(val || 0)))
        return payload
    })
    for (const it of items) {
        if (!it.outboundQuantity || it.outboundQuantity <= 0) {
            ElMessage.error('出库总数必须大于 0')
            return
        }
    }

    try {
        submitting.value = true
        const { data } = await axios.post(`${apiBaseUrl}/warehouse/orderoutbound/create`, {
            orderRId: query.orderRId,
            picker: form.picker,
            remark: form.remark,
            items,
            // ======= 新增字段，传给后端 =======
            departmentId: form.departmentId,
            destinationDepartmentName: selectedDepartmentName.value // 可选
        })
        ElMessageBox.alert(`出库成功！单号：${data.outboundRId}\n时间：${data.outboundTime}`, '提示', { type: 'success' })
        selectedItems.value = []
        await reload(false)
    } finally {
        submitting.value = false
    }
}

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
  await Promise.all([loadOrders(), loadDepartments()])
  loadMaterialTypes();
  // 如果你不想并行，也可先 loadDepartments 再 loadOrders
})
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
</style>
