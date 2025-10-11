<template>
  <div class="page p-4">
    <!-- 顶部筛选 -->
    <el-card shadow="never" class="mb-3">
      <el-form :inline="true" :model="query" @submit.prevent>
        <el-form-item label="搜索">
          <el-input
            v-model.trim="query.keyword"
            placeholder="订单号/客户/记录ID…"
            clearable
            style="width: 280px"
            @keyup.enter.native="reload"
          >
            <template #prefix><el-icon><Search /></el-icon></template>
          </el-input>
        </el-form-item>
        <el-form-item>
          <el-switch v-model="query.onlyPending" active-text="仅显示待填写采购用量" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="list.loading" @click="reload">查询</el-button>
          <el-button @click="reset">清空</el-button>
          <el-button :loading="list.loading" :icon="Refresh" @click="reload">刷新</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 待填写采购用量记录列表 -->
    <el-card shadow="never" class="card-fill">
      <template #header>
        <div class="flex items-center justify-between">
          <span>采购用量记录（需填写）共 {{ list.total }} 条</span>
          <small class="muted">提示：点击“填写采购用量”打开对话框进行逐项录入。</small>
        </div>
      </template>

      <el-table
        :data="list.rows"
        border
        stripe
        size="small"
        v-loading="list.loading"
        @sort-change="onSortChange"
      >
        <el-table-column type="index" width="60" />
        <el-table-column prop="id" label="记录ID" width="110" sortable="custom" />
        <el-table-column prop="orderRid" label="订单号" min-width="140">
          <template #default="{ row }">
            <el-tag type="info" effect="plain">{{ row.orderRid }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="customerName" label="客户" min-width="140" />
        <el-table-column prop="createdAt" label="创建时间" width="160" sortable="custom" />
        <el-table-column prop="stageText" label="流程阶段" width="120" />
        <el-table-column prop="pendingNodeText" label="当前待办" width="160" />
        <el-table-column fixed="right" label="操作" width="160">
          <template #default="{ row }">
            <el-button size="small" type="primary" @click="openPurchase(row)">填写采购用量</el-button>
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

    <!-- 采购用量对话框 -->
    <el-dialog
      v-model="detailDialog.visible"
      title="采购用量填写"
      width="85%"
      :close-on-click-modal="false"
      :before-close="closeDialog"
      @closed="onDialogClose"
    >
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

        <!-- 订单数量（尺码分布） 仅展示，确保“尺码顺序”一致 -->
        <el-divider>订单数量（尺码分布）</el-divider>
        <div class="flex items-center gap-2 mb-2">
          <el-select
            v-model="qtyColor"
            placeholder="选择颜色后加载尺码分布"
            style="width: 240px"
            :disabled="!detailDialog.record || !colorOptions.length"
            :loading="qtyLoading"
            clearable
          >
            <el-option v-for="c in colorOptions" :key="c" :label="c" :value="c" />
          </el-select>
          <el-button type="primary" :loading="qtyLoading" :disabled="!qtyColor" @click="loadQtyTableByColor">加载</el-button>
          <span class="muted">提示：点击下方“明细”任意一行，也会自动切换到该行的颜色并加载。</span>
        </div>

        <el-table
          v-loading="qtyLoading"
          :data="orderProduceInfo"
          border
          style="width: 100%"
          :span-method="arraySpanMethod"
          empty-text="选择颜色后加载"
        >
          <el-table-column prop="color" label="颜色" width="120" />
          <el-table-column
            v-for="column in filteredColumns"
            :key="column.prop"
            :prop="column.prop"
            :label="column.label"
            min-width="80"
          />
          <el-table-column prop="total" label="合计" width="120" />
        </el-table>

        <!-- 明细：采购用量（手动） / 带尺码材料 -->
        <el-divider>明细（核定用量 / 采购用量 / 带尺码材料）</el-divider>
        <div class="dlg-toolbar">
          <div class="flex items-center gap-2">
            <el-input
              v-model="keyword"
              placeholder="搜索：颜色/材料名称/型号/规格/材料颜色"
              clearable
              style="width: 320px"
            >
              <template #prefix><el-icon><Search /></el-icon></template>
            </el-input>
          </div>
          <div class="flex gap-2 totals">
            <span class="muted">当前筛选合计采购量：</span>
            <el-tag type="success">{{ totalPurchase }}</el-tag>
          </div>
        </div>

        <el-table
          :data="filteredRows"
          border
          stripe
          size="small"
          @row-click="onDetailRowClick"
        >
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

          <el-table-column prop="approvalUsage" label="核定用量" width="140" align="right">
            <template #default="{ row }">{{ row.approvalUsage }}</template>
          </el-table-column>

          <!-- 采购用量：普通材料=可编辑；尺码材料=只读（来自尺码数组合计） -->
          <el-table-column label="采购用量" width="200">
            <template #default="{ row }">
              <el-input-number
                v-model="row.purchaseUsage"
                :precision="4"
                :step="0.0001"
                :min="0"
                controls-position="right"
                :disabled="isSizeBased(row)"
                @change="onPurchaseChange(row)"
              />
            </template>
          </el-table-column>

          <!-- 尺码采购量入口 -->
          <el-table-column label="尺码采购量" width="160">
            <template #default="{ row }">
              <el-button v-if="isSizeBased(row)" type="primary" link @click="openSizeEditor(row)">编辑尺码采购</el-button>
              <span v-else class="muted">-</span>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <template #footer>
        <el-button @click="detailDialog.visible = false">关 闭</el-button>
        <el-button :loading="detailDialog.saving" @click="savePurchase">保 存</el-button>
        <el-button type="warning" :loading="detailDialog.submitting" @click="openSubmitConfirm">提 交</el-button>
      </template>
    </el-dialog>

    <!-- 带尺码材料：采购尺码编辑对话框（按列顺序，一一对应） -->
    <el-dialog
      v-model="sizeEditor.visible"
      :title="`按尺码填写采购量（${sizeEditor.row?.materialName || ''} / ${sizeEditor.row?.shoeColorName || ''}）`"
      width="50%"
      append-to-body
      :close-on-click-modal="false"
    >
      <div v-if="sizeEditor.visible">
        <div class="sizes-toolbar">
          <el-button @click="fillFromApproval">按核定尺码填充</el-button>
          <el-button @click="clearAllSizes">清空</el-button>
          <span class="muted ml-2">合计：</span>
          <el-tag type="success">{{ sizeEditorTotal }}</el-tag>
        </div>

        <div class="sizes-grid">
          <div v-for="(col, idx) in sizeEditor.columns" :key="col.prop" class="size-cell">
            <div class="size-label">{{ col.label }}</div>
            <el-input-number
              v-model="sizeEditor.formArr[idx]"
              :min="0"
              :step="1"
              controls-position="right"
              @change="onSizeCellChange"
            />
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="sizeEditor.visible = false">取 消</el-button>
        <el-button type="primary" @click="applySizeEditor">确 定</el-button>
      </template>
    </el-dialog>

    <!-- 提交前确认对话框 -->
    <el-dialog
      v-model="submitConfirm.visible"
      title="确认提交采购用量"
      width="560px"
      append-to-body
      :close-on-click-modal="false"
    >
      <div class="mb-3">
        <el-alert
          v-if="submitConfirm.errors.length"
          type="error"
          show-icon
          :closable="false"
          :title="`存在 ${submitConfirm.errors.length} 处校验问题，无法提交`"
        />
        <el-alert
          v-else
          type="info"
          show-icon
          :closable="false"
          title="请确认以下汇总信息后提交"
          class="mb-2"
        />
      </div>

      <el-descriptions :column="2" border>
        <el-descriptions-item label="总行数">{{ submitConfirm.stats.totalRows }}</el-descriptions-item>
        <el-descriptions-item label="带尺码行">{{ submitConfirm.stats.sizeRows }}</el-descriptions-item>
        <el-descriptions-item label="普通行">{{ submitConfirm.stats.normalRows }}</el-descriptions-item>
        <el-descriptions-item label="合计采购量">{{ submitConfirm.stats.totalPurchase }}</el-descriptions-item>
      </el-descriptions>

      <div v-if="submitConfirm.errors.length" class="mt-3">
        <div class="muted mb-1">问题列表：</div>
        <ul class="err-list">
          <li v-for="(e, i) in submitConfirm.errors" :key="i">• {{ e }}</li>
        </ul>
      </div>

      <template #footer>
        <el-button @click="submitConfirm.visible=false">取 消</el-button>
        <el-button
          type="primary"
          :loading="detailDialog.submitting"
          :disabled="submitConfirm.errors.length>0"
          @click="confirmSubmit"
        >确 认 提 交</el-button>
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
  PURCHASE_TASKS: '/missing_material_purchase/purchase_amount_tasks',
  PURCHASE_FORM:  '/missing_material_purchase/purchase_form',
  PURCHASE_SAVE:  '/missing_material_purchase/purchase_save'   // 提交也走这个，加 submit:1 参数
}
const apiBaseUrl = getCurrentInstance()?.appContext.config.globalProperties.$apiBaseUrl || ''

/** ====== 列表区 ====== */
const query = reactive({ keyword: '', onlyPending: true, sortProp: 'createdAt', sortOrder: 'desc' as 'asc' | 'desc' })
const pager = reactive({ page: 1, pageSize: 20 })
const list  = reactive({ loading: false, total: 0, rows: [] as any[] })

function reset(){ query.keyword=''; query.onlyPending = true; pager.page=1; loadTasks() }
function reload(){ pager.page=1; loadTasks() }
function onPageChange(p:number){ pager.page=p; loadTasks() }
function onPageSizeChange(sz:number){ pager.pageSize=sz; reload() }
function onSortChange({prop,order}:any){ if(!prop)return; query.sortProp=prop; query.sortOrder=order==='ascending'?'asc':'desc'; reload() }
async function loadTasks(){
  list.loading=true
  try{
    const params:any={ page:pager.page, pageSize:pager.pageSize, keyword:query.keyword||undefined, onlyPending:query.onlyPending?1:0, sortProp:query.sortProp, sortOrder:query.sortOrder }
    const {data}=await axios.get(`${apiBaseUrl}${API.PURCHASE_TASKS}`,{params})
    list.total=data?.total||0
    list.rows=(data?.list||[]).map((r:any)=>({
      id:r.id||r.record_id||r.recordId,
      orderRid:r.order_rid||r.orderRid,
      customerName:r.customer_name||r.customerName,
      createdAt:r.created_at||r.createdAt,
      stageText:r.stage_text||r.stageText,
      pendingNodeText:r.pending_node_text||r.pendingNodeText
    }))
  }catch(e:any){ ElMessage.error(e?.message||'加载记录失败') }
  finally{ list.loading=false }
}

/** ====== 尺码分布（展示 & 用于确定尺码列顺序） ====== */
const orderProduceInfo = ref<any[]>([])
const shoeSizeColumns = ref<Array<{prop:string;label:string}>>([])
const qtyColor = ref<string>('')
const qtyLoading = ref(false)

const filteredColumns = computed(()=>{
  const data=orderProduceInfo.value||[]
  return (shoeSizeColumns.value||[]).filter(col =>
    data.some(row => row[col.prop] !== undefined && row[col.prop] !== null && Number(row[col.prop]) !== 0)
  )
})
function arraySpanMethod({row,column,rowIndex,columnIndex}:any){
  const data=orderProduceInfo.value||[]
  if(columnIndex===0){
    if(rowIndex>0 && row.color===data[rowIndex-1].color) return [0,0]
    let rowspan=1
    for(let i=rowIndex+1;i<data.length;i++){ if(data[i].color===row.color) rowspan++; else break }
    return [rowspan,1]
  }
  if((column as any).property==='total'){
    let firstIdx=rowIndex
    for(let i=rowIndex-1;i>=0;i--){ if(data[i].color===row.color) firstIdx=i; else break }
    if(rowIndex!==firstIdx) return [0,0]
    let rowspan=1
    for(let i=firstIdx+1;i<data.length;i++){ if(data[i].color===row.color) rowspan++; else break }
    return [rowspan,1]
  }
}
async function getOrderShoeBatchInfo(orderRid:string, shoeRid:string, color:string, orderId?:number){
  try{
    qtyLoading.value=true
    const resp=await axios.get(`${apiBaseUrl}/order/getordershoesizetotal`,{ params:{ orderid:orderRid, ordershoeid:shoeRid, color } })
    orderProduceInfo.value=Array.isArray(resp.data)?resp.data:(resp.data?.list||[])
    const cols = await getShoeSizesName(orderId)
    shoeSizeColumns.value = (Array.isArray(cols)?cols:[]).map((c:any)=>{
      if(typeof c==='string'||typeof c==='number'){ const s=String(c); return {prop:s,label:s} }
      const name=c?.prop??c?.name??c?.value??''
      const label=c?.label??name
      return {prop:String(name), label:String(label)}
    }).filter(col=>col.prop)
  }catch(e:any){
    orderProduceInfo.value=[]
    shoeSizeColumns.value=[]
    ElMessage.error(e?.message||'加载尺码分布失败')
  }finally{ qtyLoading.value=false }
}

/** ====== 采购对话框数据 ====== */
type DetailRecord = {
  id?:number
  orderId?:number
  orderShoeId?:number|null
  orderRid?:string
  shoeRid?:string|null
  customerName?:string
  createdAt?:string
  stageText?:string
  reason?:string
  remark?:string
}

type RowItem = {
  id:number
  orderShoeTypeId:number|null
  shoeColorName:string
  materialType:string
  materialName:string
  materialModel:string
  materialSpecification:string
  color?:string
  orderQty:number
  approvalUsage:number
  purchaseUsage:number
  sizeApprovalArr?: number[]
  sizePurchaseArr?: number[]
}

const detailDialog=reactive({ visible:false, loading:false, saving:false, submitting:false, dirty:false, record:null as DetailRecord|null })
const rows = ref<RowItem[]>([])
const keyword = ref('')
let currentRecordId:number|null = null

const filteredRows = computed(()=>{
  const k = keyword.value.trim().toLowerCase()
  if(!k) return rows.value
  return rows.value.filter(r => [r.shoeColorName,r.materialName,r.materialModel,r.materialSpecification,r.color]
    .filter(Boolean).some(t => String(t).toLowerCase().includes(k)))
})
const totalPurchase = computed(()=> fix4(filteredRows.value.reduce((s,r)=>s + Number(r.purchaseUsage||0), 0)))

function fix4(n:any){ const v=Number(n||0); return Math.round(v*10000)/10000 }
function sum(arr?:number[]){ return fix4((arr||[]).reduce((s,n)=>s+Number(n||0),0)) }
function isSizeBased(row:RowItem){ return ['大底','中底','烫底'].includes(String(row.materialType||'')) }

/** 打开对话框 */
async function openPurchase(listRow:any){
  currentRecordId = Number(listRow.id)
  detailDialog.visible = true
  await loadPurchaseForm()
}

/** 容错读取（兼容多字段名） */
function toNumArr(a:any){ return Array.isArray(a)?a.map((n:any)=>Number(n??0)):undefined }
function pickSizeApprovalArr(it:any){ return toNumArr(it.size_approval_amount_arr ?? it.sizeApprovalArr ?? it.size_approved_arr) }
function pickSizePurchaseArr(it:any){ return toNumArr(it.size_purchase_amount_arr ?? it.size_purcahse_amount_arr ?? it.purchase_amount_arr ?? it.sizePurchaseArr) }

/** 加载 purchase_form：表头 + 明细 */
async function loadPurchaseForm(){
  if(!currentRecordId) return
  detailDialog.loading = true
  try{
    const { data } = await axios.get(`${apiBaseUrl}${API.PURCHASE_FORM}`, { params:{ id: currentRecordId } })
    const head = data?.record || null
    detailDialog.record = head ? {
      id: head.id,
      orderId: head.orderId,
      orderShoeId: head.orderShoeId,
      orderRid: head.orderRid,
      shoeRid: head.shoeRid,
      customerName: head.customerName,
      createdAt: head.createdAt,
      stageText: head.stageText,
      reason: head.reason,
      remark: head.remark
    } : null

    // 明细
    const items = Array.isArray(data?.items) ? data.items : []
    rows.value = items.map((it:any) => {
      const row: RowItem = {
        id: Number(it.id),
        orderShoeTypeId: it.orderShoeTypeId ?? null,
        shoeColorName: it.shoeColorName || '',
        materialType: it.materialType || '',
        materialName: it.materialName || '',
        materialModel: it.materialModel || '',
        materialSpecification: it.materialSpecification || '',
        color: it.color || '',
        orderQty: Number(it.orderQty || 0),
        approvalUsage: fix4(it.approvalUsage || 0),
        purchaseUsage: fix4(it.purchaseUsage || 0),
        sizeApprovalArr: pickSizeApprovalArr(it),
        sizePurchaseArr: pickSizePurchaseArr(it)
      }
      // 带尺码：若采购数组不存在 => 用核定数组默认填充，并计算合计
      if(isSizeBased(row)){
        if(!row.sizePurchaseArr || row.sizePurchaseArr.length===0){
          row.sizePurchaseArr = (row.sizeApprovalArr || []).slice()
        }
        row.purchaseUsage = sum(row.sizePurchaseArr)
      }
      return row
    })

    // 颜色选项 & 预选
    const firstColor = colorOptions.value[0]
    qtyColor.value = firstColor || ''
    orderProduceInfo.value = []
    if(firstColor && detailDialog.record?.orderRid && detailDialog.record?.shoeRid){
      await getOrderShoeBatchInfo(detailDialog.record.orderRid, detailDialog.record.shoeRid, firstColor, detailDialog.record.orderId)
    }

    detailDialog.dirty = false
  }catch(e:any){
    ElMessage.error(e?.message || '加载采购详情失败')
  }finally{
    detailDialog.loading = false
  }
}

/** 明细里可选颜色（用于切换上面的“尺码分布”展示） */
const colorOptions = computed(()=>{
  const set = new Set<string>()
  for(const it of rows.value||[]){ if(it?.shoeColorName) set.add(it.shoeColorName) }
  return Array.from(set)
})

/** 切换颜色并加载尺码分布 */
async function loadQtyTableByColor(){
  if(!detailDialog?.record?.orderRid || !detailDialog?.record?.shoeRid){ ElMessage.warning('缺少订单标识'); return }
  if(!qtyColor.value){ ElMessage.warning('请选择颜色'); return }
  await getOrderShoeBatchInfo(detailDialog.record.orderRid, detailDialog.record.shoeRid, qtyColor.value, detailDialog.record.orderId)
}
function onDetailRowClick(row:RowItem){
  if(!row?.shoeColorName) return
  qtyColor.value = row.shoeColorName
  loadQtyTableByColor()
}

/** 普通材料：采购用量手动输入 */
function onPurchaseChange(row:RowItem){
  if(isSizeBased(row)) return
  row.purchaseUsage = fix4(row.purchaseUsage)
  detailDialog.dirty = true
}

/** ====== 带尺码材料：采购尺码编辑 ====== */
const sizeEditor = reactive({
  visible:false,
  row: null as RowItem|null,
  columns: [] as Array<{prop:string;label:string}>,
  formArr: [] as number[]   // 与 columns 同长度、同顺序
})

function alignArrayToColumns(src:number[]|undefined, cols:Array<{prop:string;label:string}>):number[]{
  const a = Array.isArray(src) ? src.slice(0, cols.length) : []
  while(a.length < cols.length) a.push(0)
  return a
}

function openSizeEditor(row:RowItem){
  sizeEditor.row = row
  const ensureColumns = async ()=>{
    if(!shoeSizeColumns.value.length && detailDialog.record?.orderId){
      const cols = await getShoeSizesName(detailDialog.record.orderId)
      shoeSizeColumns.value = (Array.isArray(cols)?cols:[]).map((c:any)=>{
        if(typeof c==='string'||typeof c==='number'){ const s=String(c); return {prop:s,label:s} }
        const name=c?.prop??c?.name??c?.value??''
        const label=c?.label??name
        return {prop:String(name), label:String(label)}
      }).filter(col=>col.prop)
    }
    sizeEditor.columns = [...shoeSizeColumns.value]
  }
  qtyColor.value = row.shoeColorName
  loadQtyTableByColor()
    .finally(ensureColumns)
    .then(()=>{
      const base = (row.sizePurchaseArr && row.sizePurchaseArr.length)
        ? row.sizePurchaseArr
        : (row.sizeApprovalArr || [])
      sizeEditor.formArr = alignArrayToColumns(base, sizeEditor.columns)
      sizeEditor.visible = true
    })
}

function fillFromApproval(){
  if(!sizeEditor.row) return
  sizeEditor.formArr = alignArrayToColumns(sizeEditor.row.sizeApprovalArr || [], sizeEditor.columns)
}
function clearAllSizes(){
  sizeEditor.formArr = alignArrayToColumns([], sizeEditor.columns)
}
const sizeEditorTotal = computed(()=> sum(sizeEditor.formArr) )
function onSizeCellChange(){ /* 合计由 computed 处理 */ }

function applySizeEditor(){
  if(!sizeEditor.row) return
  sizeEditor.row.sizePurchaseArr = (sizeEditor.formArr || []).map(n => Number(n||0))
  sizeEditor.row.purchaseUsage = sum(sizeEditor.row.sizePurchaseArr)
  detailDialog.dirty = true
  sizeEditor.visible = false
}

/** 兜底：带尺码材料仅同步合计显示 */
watch(rows,(arr)=>{
  if(!Array.isArray(arr)) return
  arr.forEach(r=>{
    if(isSizeBased(r)){
      r.purchaseUsage = sum(r.sizePurchaseArr)
    }
  })
},{deep:true})

/** ====== 保存 / 提交 ====== */
// 构建 payload，并对尺码材料做兜底（未填则用核定数组）
function buildPayload(isSubmit:boolean){
  return {
    recordId: currentRecordId,
    submit: isSubmit ? 1 : 0,
    items: rows.value.map(r=>{
      if(isSizeBased(r)){
        const arr = (r.sizePurchaseArr && r.sizePurchaseArr.length>0)
          ? r.sizePurchaseArr
          : (r.sizeApprovalArr || [])
        return {
          id: r.id,
          size_purchase_amount_arr: (arr || []).map(n => Number(n||0))
        }
      }else{
        return {
          id: r.id,
          purchaseUsage: Number(r.purchaseUsage || 0)
        }
      }
    })
  }
}
// 简单校验，用于提交前对话框提示
function validateForSubmit(){
  const errors:string[] = []
  rows.value.forEach((r, idx)=>{
    if(isSizeBased(r)){
      const arr = (r.sizePurchaseArr && r.sizePurchaseArr.length>0) ? r.sizePurchaseArr : (r.sizeApprovalArr || [])
      if(!arr || arr.length===0){
        errors.push(`第 ${idx+1} 行（${r.materialName}/${r.shoeColorName}）：尺码采购为空，且无核定尺码可兜底`)
      }
      if(arr && arr.some(n=>Number(n)<0)){
        errors.push(`第 ${idx+1} 行（${r.materialName}/${r.shoeColorName}）：尺码采购存在负数`)
      }
    }else{
      if(Number(r.purchaseUsage) < 0){
        errors.push(`第 ${idx+1} 行（${r.materialName}/${r.shoeColorName}）：采购用量为负`)
      }
    }
  })
  return errors
}

async function savePurchase(){
  if(!currentRecordId) return
  try{
    detailDialog.saving = true
    const payload = buildPayload(false)
    const { data } = await axios.post(`${apiBaseUrl}${API.PURCHASE_SAVE}`, payload)
    if(data?.success){
      ElMessage.success('保存成功')
      detailDialog.dirty = false
      loadTasks()
    }else{
      throw new Error(data?.message || '保存失败')
    }
  }catch(e:any){
    ElMessage.error(e?.message || '保存失败')
  }finally{
    detailDialog.saving = false
  }
}

/** —— 提交按钮 + 确认对话框 —— */
const submitConfirm = reactive({
  visible:false,
  errors: [] as string[],
  stats: {
    totalRows: 0,
    sizeRows: 0,
    normalRows: 0,
    totalPurchase: 0
  }
})

function openSubmitConfirm(){
  submitConfirm.errors = validateForSubmit()
  submitConfirm.stats.totalRows = rows.value.length
  submitConfirm.stats.sizeRows  = rows.value.filter(r=>isSizeBased(r)).length
  submitConfirm.stats.normalRows= submitConfirm.stats.totalRows - submitConfirm.stats.sizeRows
  submitConfirm.stats.totalPurchase = fix4(rows.value.reduce((s,r)=>s+Number(r.purchaseUsage||0),0))
  submitConfirm.visible = true
}

async function confirmSubmit(){
  if(!currentRecordId) return
  try{
    detailDialog.submitting = true
    const payload = buildPayload(true) // 带 submit:1
    const { data } = await axios.post(`${apiBaseUrl}${API.PURCHASE_SAVE}`, payload)
    if(data?.success){
      ElMessage.success('提交成功')
      submitConfirm.visible = false
      detailDialog.visible = false
      loadTasks()
    }else{
      throw new Error(data?.message || '提交失败')
    }
  }catch(e:any){
    ElMessage.error(e?.message || '提交失败')
  }finally{
    detailDialog.submitting = false
  }
}

/** 关闭对话框 */
function closeDialog(done:()=>void){
  if(!detailDialog.dirty){ done(); return }
  ElMessageBox.confirm('存在未保存的更改，确定关闭吗？','提示',{type:'warning'})
    .then(()=>done())
    .catch(()=>{})
}
function onDialogClose(){
  keyword.value = ''
}

/** 初始加载 */
onMounted(()=>loadTasks())
</script>

<style scoped>
.page { display:flex; flex-direction:column; gap:12px; }
.mb-3 { margin-bottom:12px; }
.card-fill { min-height:420px; }
.flex { display:flex; }
.items-center { align-items:center; }
.justify-between { justify-content:space-between; }
.justify-end { justify-content:flex-end; }
.mt-2 { margin-top:8px; }
.mt-3 { margin-top:12px; }
.gap-2 { gap:8px; }
.small { font-size:12px; }
.muted { color:#999; }
.dlg-toolbar { display:flex; align-items:center; justify-content:space-between; margin:8px 0 12px; }
.totals { align-items:center; }

.sizes-toolbar { display:flex; align-items:center; gap:8px; margin-bottom:12px; }
.sizes-grid {
  display:grid;
  grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
  gap:12px;
}
.size-cell { padding:8px; border:1px solid #eee; border-radius:8px; }
.size-label { font-size:12px; color:#666; margin-bottom:6px; }
.ml-1 { margin-left:4px; }
.ml-2 { margin-left:8px; }

/* 提交确认对话框 */
.err-list { margin:0; padding-left: 18px; color:#c45656; line-height: 1.6; }
.mb-2 { margin-bottom: 8px; }
.mb-3 { margin-bottom: 12px; }
</style>
