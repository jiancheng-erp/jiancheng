<template>
  <div class="instruction-download">
    <section class="filters-panel">
      <div class="panel-header">
        <div>
          <h2>生产指令下载</h2>
        </div>
        <el-button link type="primary" @click="refreshData">刷新数据</el-button>
      </div>
      <el-form class="filters-form" label-position="top">
        <el-form-item label="订单号">
          <el-input
            v-model="filters.orderNumber"
            placeholder="输入订单号"
            clearable
            @keyup.enter="handleSearch"
          />
        </el-form-item>
        <el-form-item label="下单日期">
          <el-date-picker
            v-model="filters.dateRange"
            type="daterange"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
            range-separator="至"
            clearable
          />
        </el-form-item>
        <div class="filters-actions">
          <el-button type="primary" @click="handleSearch">查询</el-button>
          <el-button @click="resetFilters">重置</el-button>
        </div>
      </el-form>
    </section>

    <section class="table-panel">
      <el-table
        :data="pagedData"
        border
        stripe
        :loading="loading"
        empty-text="暂无满足条件的订单"
        style="height: 60vh;"
      >
        <el-table-column type="expand">
          <template #default="scope">
            <el-table :data="scope.row.colors" size="small" border class="color-expand-table">
              <el-table-column prop="colorName" label="颜色" min-width="180">
                <template #default="colorScope">
                  <div class="color-cell">
                    <span class="product-name">{{ colorScope.row.customerProductName }}</span>
                    <span class="color-name">{{ colorScope.row.colorName }}</span>
                  </div>
                </template>
              </el-table-column>
              <el-table-column label="阶段状态" min-width="320">
                <template #default="colorScope">
                  <div class="stage-tag-row">
                    <el-tag
                      v-for="stage in stageTabs"
                      :key="stage.key"
                      :type="stageTagType(colorScope.row.stages?.[stage.key])"
                      size="small"
                      class="stage-tag"
                    >
                      {{ stage.label }} · {{ stageTagLabel(colorScope.row.stages?.[stage.key]) }}
                    </el-tag>
                  </div>
                </template>
              </el-table-column>
              <el-table-column label="操作" width="220">
                <template #default="colorScope">
                  <el-button type="primary" text @click="openDrawer(scope.row, colorScope.row)">
                    查看指令单
                  </el-button>
                  <el-button
                    type="success"
                    text
                    :disabled="!colorScope.row.hasSchedule"
                    @click="handleDownload(scope.row, colorScope.row)"
                  >
                    下载
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
          </template>
        </el-table-column>
        <el-table-column type="index" label="#" width="60" :index="tableIndex" />
        <el-table-column prop="orderRid" label="订单号" min-width="160" />
        <el-table-column label="客户" min-width="220">
          <template #default="scope">
            <div class="customer-cell">
              <span class="customer-name">{{ scope.row.customerName }}</span>
              <span class="customer-brand">{{ scope.row.customerBrand }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="订单周期" min-width="220">
          <template #default="scope">
            <div class="date-range">
              <span>{{ scope.row.orderStartDate }}</span>
              <span class="divider">→</span>
              <span>{{ scope.row.orderEndDate }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="colorCount" label="颜色数" min-width="100" />
        <el-table-column prop="totalScheduledPairs" label="累计排产" min-width="120" />
        <el-table-column label="排产状态" min-width="140">
          <template #default="scope">
            <el-tag :type="orderStatusTag(scope.row)">{{ orderStatusText(scope.row) }}</el-tag>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-row">
        <el-pagination
          background
          layout="total, sizes, prev, pager, next"
          :total="totalRows"
          :current-page="pagination.currentPage"
          :page-size="pagination.pageSize"
          :page-sizes="[10, 20, 30, 50]"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </section>

    <el-drawer
      v-model="drawerVisible"
      size="60%"
      custom-class="instruction-drawer"
      :with-header="false"
      :close-on-click-modal="true"
      :close-on-press-escape="true"
      @close="clearDrawer"
    >
      <div v-if="activeOrder && activeColor" class="drawer-content">
        <div class="drawer-header">
          <div class="drawer-header-text">
            <h3>{{ activeOrder.orderRid }}</h3>
            <p class="drawer-subtitle">
              {{ activeColor.colorName }} · {{ activeColor.customerProductName }}
            </p>
            <p class="drawer-meta-line">
              客户：{{ activeOrder.customerName }} · 品牌：{{ activeOrder.customerBrand }}
            </p>
          </div>
          <div class="drawer-header-right">
            <div v-if="drawerShoeImage" class="drawer-image">
              <img :src="drawerShoeImage" alt="鞋图" />
            </div>
            <div v-else class="drawer-image placeholder">
              <span>鞋图未上传或路径缺失</span>
            </div>
            <button class="drawer-close" type="button" @click="closeDrawer">×</button>
          </div>
        </div>

        <el-tabs v-model="activeStageKey" class="drawer-tabs">
          <el-tab-pane
            v-for="stage in stageTabs"
            :key="stage.key"
            :label="stage.label"
            :name="stage.key"
          >
            <template v-if="activeColor.stages?.[stage.key]">
              <div class="drawer-meta">
                <div>
                  <span>阶段状态</span>
                  <strong>
                    {{ stageTagLabel(activeColor.stages[stage.key]) }} ·
                    {{ activeColor.stages[stage.key].stageLabel }}
                  </strong>
                </div>
                <div>
                  <span>线别/组别</span>
                  <strong>{{ activeColor.stages[stage.key].lineGroup || '未分配' }}</strong>
                </div>
                <div>
                  <span>计划周期</span>
                  <strong>
                    {{ activeColor.stages[stage.key].startDate || '--' }} 至
                    {{ activeColor.stages[stage.key].endDate || '--' }}
                  </strong>
                </div>
                <div>
                  <span>排产对数</span>
                  <strong>
                    {{ activeColor.stages[stage.key].scheduled
                      ? activeColor.stages[stage.key].scheduledPairs
                      : '未排产' }}
                  </strong>
                </div>
              </div>

              <el-alert
                v-if="!activeColor.stages[stage.key].scheduled"
                type="warning"
                show-icon
                title="该阶段尚未排产，无法导出指令单"
                :closable="false"
              />

              <section class="drawer-section">
                <div class="section-heading">
                  <h4>尺码排产明细</h4>
                </div>
                <el-table :data="buildSizeRows(activeColor, stage.key)" border size="small">
                  <el-table-column prop="label" label="码段" min-width="120" />
                  <el-table-column prop="value" label="数量" min-width="120">
                    <template #default="scope">
                      <span>{{ scope.row.value || 0 }}</span>
                    </template>
                  </el-table-column>
                </el-table>
              </section>

              <section class="drawer-section">
                <div class="section-heading">
                  <h4>材料详情</h4>
                  <small>楦型 / 大底 / 中底 / 烫底</small>
                </div>
                <div v-if="drawerMaterialEntries.length" class="material-grid">
                  <div
                    v-for="entry in drawerMaterialEntries"
                    :key="entry.key"
                    class="material-card"
                  >
                    <span class="material-label">{{ entry.label }}:</span>
                    <strong>{{ entry.value || '—' }}</strong>
                    <small v-if="entry.caption">{{ entry.caption }}</small>
                  </div>
                </div>
                <el-empty v-else description="暂无材料信息" />
              </section>

              <section class="drawer-section">
                <div class="section-heading">
                  <h4>工艺要求</h4>
                  <small>生产 / 后处理 / 裁断 / 针车 / 成型</small>
                </div>
                <div v-if="drawerCraftEntries.length" class="material-grid">
                  <div v-for="entry in drawerCraftEntries" :key="entry.key" class="material-card">
                    <span class="material-label">{{ entry.label }}:</span>
                    <strong>{{ entry.value || '—' }}</strong>
                  </div>
                </div>
                <el-empty v-else description="暂无工艺要求" />
              </section>
            </template>
            <el-empty v-else description="该阶段尚未创建" />
          </el-tab-pane>
        </el-tabs>
      </div>
      <el-empty v-else description="请选择需要查看的订单颜色" />
    </el-drawer>

    <el-dialog
      v-model="downloadDialogVisible"
      title="下载生产指令单"
      width="440px"
      :close-on-click-modal="false"
      :close-on-press-escape="false"
      @closed="resetDownloadDialog"
    >
      <div class="download-context" v-if="downloadContext.order && downloadContext.color && downloadContext.stage">
        <span>订单：{{ downloadContext.order.orderRid }}</span>
        <span>颜色：{{ downloadContext.color.colorName }}</span>
        <span>阶段：{{ downloadContext.stage.stageLabel }}</span>
      </div>
      <el-form :model="downloadForm" label-width="96px" size="small">
        <el-form-item label="指令日期">
          <el-date-picker
            v-model="downloadForm.instructionDate"
            type="date"
            placeholder="请选择指令日期"
            value-format="YYYY-MM-DD"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="鞋盒规格">
          <el-input v-model="downloadForm.shoeBoxSpecification" placeholder="可选" clearable />
        </el-form-item>
        <el-form-item label="外箱规格">
          <el-input v-model="downloadForm.outerCartonSpecification" placeholder="可选" clearable />
        </el-form-item>
        <el-form-item label="烫印丝印">
          <el-input v-model="downloadForm.printingProcess" placeholder="可选" clearable />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="downloadDialogVisible = false" :disabled="downloadLoading">取消</el-button>
          <el-button type="primary" :loading="downloadLoading" @click="confirmDownloadInstruction">下载</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { reactive, ref, computed, onMounted, getCurrentInstance } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'

const stageTabs = Object.freeze([
  { key: 'cutting', label: '裁断' },
  { key: 'preSewing', label: '针车预备' },
  { key: 'sewing', label: '针车' },
  { key: 'molding', label: '成型' }
])
const stagePriority = ['molding', 'sewing', 'preSewing', 'cutting']

const apiBaseUrl = getCurrentInstance().appContext.config.globalProperties.$apiBaseUrl

const filters = reactive({
  orderNumber: '',
  dateRange: []
})

const pagination = reactive({
  currentPage: 1,
  pageSize: 10
})

const loading = ref(false)
const tableData = ref([])
const drawerVisible = ref(false)
const activeOrder = ref(null)
const activeColor = ref(null)
const activeStageKey = ref(stageTabs[0].key)
const downloadDialogVisible = ref(false)
const downloadLoading = ref(false)
const downloadContext = reactive({ order: null, color: null, stage: null })
const downloadForm = reactive({
  instructionDate: getDefaultInstructionDate(),
  shoeBoxSpecification: '',
  outerCartonSpecification: '',
  printingProcess: ''
})

const pagedData = computed(() => {
  const start = (pagination.currentPage - 1) * pagination.pageSize
  const end = start + pagination.pageSize
  return tableData.value.slice(start, end)
})

const totalRows = computed(() => tableData.value.length)
const drawerStageData = computed(
  () => activeColor.value?.stages?.[activeStageKey.value] || null
)
const drawerMaterialEntries = computed(() => {
  const materials = drawerStageData.value?.materials || activeColor.value?.materials
  return buildMaterialEntries(materials)
})
const drawerCraftEntries = computed(() => {
  const craft = drawerStageData.value?.craftRequirements || activeColor.value?.craftRequirements
  return buildCraftEntries(craft)
})
const drawerShoeImage = computed(() => {
  const materials = drawerStageData.value?.materials || activeColor.value?.materials
  return materials?.shoeImage?.public || null
})

onMounted(() => {
  fetchInstructionOrders()
})

function buildQueryParams() {
  const params = {}
  const cleanedOrder = filters.orderNumber.trim()
  if (cleanedOrder) {
    params.orderRid = cleanedOrder
  }
  if (Array.isArray(filters.dateRange) && filters.dateRange.length === 2) {
    params.startDate = filters.dateRange[0]
    params.endDate = filters.dateRange[1]
  }
  return params
}

async function fetchInstructionOrders() {
  loading.value = true
  try {
    const { data } = await axios.get(`${apiBaseUrl}/production/instruction/orders`, {
      params: buildQueryParams()
    })
    const records = Array.isArray(data) ? data : []
    tableData.value = normalizeOrders(records)
    pagination.currentPage = 1
  } catch (error) {
    ElMessage.error('获取生产指令单列表失败')
    tableData.value = []
  } finally {
    loading.value = false
  }
}

function normalizeOrders(records) {
  const orderMap = new Map()
  records.forEach((record) => {
    if (!record?.orderId) return
    const orderId = record.orderId
    if (!orderMap.has(orderId)) {
      orderMap.set(orderId, {
        orderId,
        orderRid: record.orderRid,
        customerName: record.customerName,
        customerBrand: record.customerBrand,
        orderStartDate: record.orderStartDate,
        orderEndDate: record.orderEndDate,
        orderStatus: record.orderStatus,
        orderStatusVal: record.orderStatusVal,
        colors: new Map()
      })
    }
    const orderEntry = orderMap.get(orderId)
    const colorKey = record.orderShoeTypeId || record.orderShoeId || `${orderId}-${record.colorName}`
    if (!orderEntry.colors.has(colorKey)) {
      orderEntry.colors.set(colorKey, {
        orderShoeTypeId: record.orderShoeTypeId,
        orderShoeId: record.orderShoeId,
        colorName: record.colorName,
        customerProductName: record.customerProductName,
        shoeRid: record.shoeRid,
        stages: {},
        sizeLabelMap: record.sizeLabelMap || {},
        materials: record.materials || null,
        craftRequirements: record.craftRequirements || null
      })
    }
    const colorEntry = orderEntry.colors.get(colorKey)
    colorEntry.stages[record.stageKey] = { ...record }
    if (!Object.keys(colorEntry.sizeLabelMap || {}).length && record.sizeLabelMap) {
      colorEntry.sizeLabelMap = record.sizeLabelMap
    }
    if (record.materials) {
      colorEntry.materials = record.materials
    }
    if (record.craftRequirements) {
      colorEntry.craftRequirements = record.craftRequirements
    }
  })

  return Array.from(orderMap.values()).map((orderEntry) => {
    const colors = Array.from(orderEntry.colors.values()).map((color) => {
      const hasSchedule = stageTabs.some((stage) => color.stages?.[stage.key]?.scheduled)
      return {
        ...color,
        hasSchedule
      }
    })
    return {
      ...orderEntry,
      colors,
      colorCount: colors.length,
      totalScheduledPairs: colors.reduce((sum, color) => sum + resolveColorPairs(color), 0),
      scheduled: colors.some((color) => color.hasSchedule)
    }
  })
}

function resolveColorPairs(color) {
  for (const key of stagePriority) {
    const stage = color.stages?.[key]
    if (stage?.scheduledPairs) {
      return stage.scheduledPairs
    }
  }
  return 0
}

function handleSearch() {
  pagination.currentPage = 1
  fetchInstructionOrders()
}

function resetFilters() {
  filters.orderNumber = ''
  filters.dateRange = []
  handleSearch()
}

function refreshData() {
  fetchInstructionOrders()
}

function handleSizeChange(size) {
  if (pagination.pageSize !== size) {
    pagination.pageSize = size
    pagination.currentPage = 1
  }
}

function handlePageChange(page) {
  pagination.currentPage = page
}

function tableIndex(index) {
  return (pagination.currentPage - 1) * pagination.pageSize + index + 1
}

function openDrawer(order, color) {
  activeOrder.value = order
  activeColor.value = color
  const firstStage = stageTabs.find((stage) => color?.stages?.[stage.key])
  activeStageKey.value = firstStage?.key || stageTabs[0].key
  drawerVisible.value = true
}

function closeDrawer() {
  drawerVisible.value = false
  clearDrawer()
}

function clearDrawer() {
  activeOrder.value = null
  activeColor.value = null
  activeStageKey.value = stageTabs[0].key
}

function handleDownload(order, color) {
  if (!color?.hasSchedule) {
    ElMessage.warning('该颜色尚未排产，无法下载指令单')
    return
  }
  const scheduledStage =
    stagePriority
      .map((key) => color.stages?.[key])
      .find((stage) => stage?.scheduled) ||
    stageTabs
      .map((tab) => color.stages?.[tab.key])
      .find((stage) => stage?.scheduled)
  if (!scheduledStage) {
    ElMessage.warning('该颜色尚未排产，无法下载指令单')
    return
  }
  downloadContext.order = order
  downloadContext.color = color
  downloadContext.stage = scheduledStage
  if (!downloadForm.instructionDate) {
    downloadForm.instructionDate = getDefaultInstructionDate()
  }
  downloadDialogVisible.value = true
}

function stageTagType(stage) {
  if (!stage) return 'info'
  return stage.scheduled ? 'success' : 'warning'
}

function stageTagLabel(stage) {
  if (!stage) return '未创建'
  return stage.scheduled ? '已排产' : '待排产'
}

function orderStatusTag(order) {
  return order.scheduled ? 'success' : 'info'
}

function orderStatusText(order) {
  return order.scheduled ? '部分/已排产' : '未排产'
}

async function confirmDownloadInstruction() {
  if (downloadLoading.value) return
  if (!downloadContext.order || !downloadContext.color || !downloadContext.stage) {
    ElMessage.warning('请先选择需要下载的订单颜色')
    return
  }
  if (!downloadForm.instructionDate) {
    ElMessage.warning('请选择指令日期')
    return
  }
  downloadLoading.value = true
  try {
    const payload = {
      orderId: downloadContext.order.orderId,
      orderRid: downloadContext.order.orderRid,
      orderShoeId: downloadContext.color.orderShoeId,
      orderShoeTypeId: downloadContext.color.orderShoeTypeId,
      stageKey: downloadContext.stage.stageKey,
      instructionDate: downloadForm.instructionDate,
      shoeBoxSpecification: (downloadForm.shoeBoxSpecification || '').trim(),
      outerCartonSpecification: (downloadForm.outerCartonSpecification || '').trim(),
      printingProcess: (downloadForm.printingProcess || '').trim()
    }
    const response = await axios.post(
      `${apiBaseUrl}/production/instruction/orders/download`,
      payload,
      { responseType: 'blob' }
    )
    const disposition = response.headers?.['content-disposition']
    const fileName =
      extractFilenameFromDisposition(disposition) ||
      `${downloadContext.order.orderRid}_${downloadContext.stage.stageLabel}.xlsx`
    saveBlobFile(response.data, fileName)
    downloadDialogVisible.value = false
    resetDownloadDialog()
    ElMessage.success('生产指令单已开始下载')
  } catch (error) {
    const message = await unwrapDownloadError(error)
    ElMessage.error(message || '下载失败')
  } finally {
    downloadLoading.value = false
  }
}

function resetDownloadDialog() {
  downloadContext.order = null
  downloadContext.color = null
  downloadContext.stage = null
  downloadForm.instructionDate = getDefaultInstructionDate()
  downloadForm.shoeBoxSpecification = ''
  downloadForm.outerCartonSpecification = ''
  downloadForm.printingProcess = ''
}

function buildMaterialEntries(materials) {
  if (!materials) {
    return []
  }
  const entries = []
  if (materials.lastType) {
    entries.push({ key: 'lastType', label: '楦型', value: materials.lastType })
  }
  if (materials.outsole) {
    const outsoleValue =
      materials.outsole.displayText ||
      formatSupplierModel(
        materials.outsole.supplierName,
        materials.outsole.materialModel,
        materials.outsole.materialSpecification
      )
    entries.push({ key: 'outsole', label: '大底', value: outsoleValue || '—' })
  }
  if (materials.midsole) {
    const midsoleValue =
      materials.midsole.displayText ||
      formatSupplierModel(
        materials.midsole.supplierName,
        materials.midsole.materialModel,
        materials.midsole.materialSpecification
      )
    entries.push({ key: 'midsole', label: '中底', value: midsoleValue || '—' })
  }
  if (materials.hotsole) {
    const supplierModel = formatSupplierModel(
      materials.hotsole.supplierName,
      materials.hotsole.materialModel
    )
    const displayValue =
      materials.hotsole.displayText || supplierModel || materials.hotsole.preCraftName || '—'
    const caption =
      !materials.hotsole.displayText && supplierModel && materials.hotsole.preCraftName
        ? materials.hotsole.preCraftName
        : null
    entries.push({
      key: 'hotsole',
      label: '烫底',
      value: displayValue,
      caption
    })
  }
  return entries
}

function buildCraftEntries(craft) {
  if (!craft) {
    return []
  }
  return [
    { key: 'productionRequirement', label: '生产要求', value: craft.productionRequirement },
    { key: 'postProcessing', label: '后处理', value: craft.postProcessing },
    { key: 'cuttingRequirement', label: '裁断要求', value: craft.cuttingRequirement },
    { key: 'sewingRequirement', label: '针车要求', value: craft.sewingRequirement },
    { key: 'moldingRequirement', label: '成型要求', value: craft.moldingRequirement }
  ]
}

function formatSupplierModel(supplier, model, specification) {
  const parts = [supplier, model, specification].filter(Boolean)
  return parts.length ? parts.join(' ').trim() : ''
}

function buildSizeRows(color, stageKey) {
  if (!color?.stages?.[stageKey]) {
    return []
  }
  const stage = color.stages[stageKey]
  const amounts = stage.sizeAmounts || {}
  const labels = Object.keys(stage.sizeLabelMap || {}).length
    ? stage.sizeLabelMap
    : color.sizeLabelMap || {}
  return Object.entries(amounts)
    .map(([code, value]) => ({
      code,
      label: labels[code] || code,
      value: value || 0
    }))
    .filter((row) => row.value > 0)
    .sort((a, b) => Number(a.code) - Number(b.code))
}

function getDefaultInstructionDate() {
  return new Date().toISOString().slice(0, 10)
}

function extractFilenameFromDisposition(disposition) {
  if (!disposition) return null
  const utfMatch = disposition.match(/filename\*=UTF-8''([^;]+)/i)
  if (utfMatch && utfMatch[1]) {
    try {
      return decodeURIComponent(utfMatch[1])
    } catch (error) {
      return utfMatch[1]
    }
  }
  const asciiMatch = disposition.match(/filename="?([^";]+)"?/i)
  return asciiMatch ? asciiMatch[1] : null
}

function saveBlobFile(data, filename) {
  const blob = new Blob([data])
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  window.URL.revokeObjectURL(url)
}

async function unwrapDownloadError(error) {
  if (error?.response?.data instanceof Blob) {
    try {
      const text = await error.response.data.text()
      const parsed = JSON.parse(text)
      return parsed.message || parsed.error || null
    } catch (parseError) {
      return '下载失败'
    }
  }
  return error?.response?.data?.message || error?.message || '下载失败'
}
</script>

<style scoped>
.instruction-download {
  width: 100%;
  min-height: 100%;
  padding: 18px 22px 32px;
  background: linear-gradient(135deg, #f7f9fb 0%, #f0f6ff 55%, #fdf7ff 100%);
  font-family: 'Space Grotesk', 'Noto Sans SC', 'Microsoft YaHei', sans-serif;
}

.filters-panel {
  background: rgba(255, 255, 255, 0.9);
  border-radius: 18px;
  padding: 18px 20px;
  box-shadow: 0 12px 45px rgba(82, 98, 255, 0.12);
  margin-bottom: 22px;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.panel-header h2 {
  margin: 0;
  font-size: 22px;
  color: #1f2a44;
}

.panel-header p {
  margin: 4px 0 12px;
  color: #6b778c;
  font-size: 14px;
}

.filters-form {
  display: flex;
  flex-wrap: wrap;
  gap: 14px;
}

.filters-form .el-form-item {
  flex: 1;
  min-width: 200px;
}

.filters-actions {
  display: flex;
  align-items: flex-end;
  gap: 12px;
  min-width: 200px;
  flex: 0 0 auto;
}

.table-panel {
  background: rgba(255, 255, 255, 0.92);
  border-radius: 18px;
  padding: 12px 16px;
  box-shadow: 0 12px 45px rgba(37, 56, 128, 0.12);
}

.color-expand-table {
  margin-top: 8px;
}

.color-cell {
  display: flex;
  flex-direction: column;
}

.product-name {
  font-weight: 600;
  color: #111c3a;
}

.color-name {
  font-size: 12px;
  color: #6b7280;
}

.customer-cell {
  display: flex;
  flex-direction: column;
}

.customer-name {
  font-weight: 600;
  color: #111c3a;
}

.customer-brand {
  font-size: 12px;
  color: #6b7280;
}

.stage-tag-row {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.stage-tag {
  margin: 2px 0;
}

.date-range {
  display: flex;
  align-items: center;
  gap: 6px;
}

.date-range .divider {
  color: #9ca3af;
}

.pagination-row {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}

.instruction-drawer {
  background: linear-gradient(160deg, #0f172a 0%, #1e2a3a 45%, #101632 100%);
}

.drawer-content {
  padding: 26px 24px 40px;
}

.drawer-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 26px;
}

.drawer-header h3 {
  margin: 0;
  font-size: 24px;
}

.drawer-header-text {
  flex: 1;
  padding-right: 16px;
}

.drawer-header-right {
  display: flex;
  align-items: flex-start;
  gap: 16px;
}

.drawer-image {
  width: 180px;
  height: 180px;
  border-radius: 16px;
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.18);
  box-shadow: 0 16px 40px rgba(0, 0, 0, 0.35);
}

.drawer-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.drawer-image.placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(15, 23, 42, 0.7);
  border-style: dashed;
  border-color: rgba(255, 255, 255, 0.35);
  box-shadow: none;
  padding: 12px;
  text-align: center;
}

.drawer-image.placeholder span {
  font-size: 14px;
  line-height: 1.4;
}

.drawer-close {
  border: none;
  background: transparent;
  font-size: 28px;
  cursor: pointer;
  line-height: 1;
}

.material-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 12px;
}

.material-card {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 14px;
  padding: 12px;
  min-height: 120px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.material-label {
  font-size: 12px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  margin-bottom: 6px;
}

.material-card strong {
  font-size: 16px;
}

.material-card small {
  color: rgba(125, 211, 252, 0.9);
  margin-top: 4px;
}

.drawer-meta {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 14px;
  margin-bottom: 18px;
}

.drawer-meta span {
  display: block;
  font-size: 12px;
}

.drawer-meta strong {
  display: block;
  font-size: 16px;
  margin-top: 2px;
}

.drawer-section {
  background: rgba(255, 255, 255, 0.04);
  border-radius: 16px;
  padding: 18px;
  margin-bottom: 22px;
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.06);
}

.instruction-drawer :deep(.el-table) {
  background: rgba(15, 23, 42, 0.6);
  --el-table-border-color: rgba(255, 255, 255, 0.12);
}

.instruction-drawer :deep(.el-table th),
.instruction-drawer :deep(.el-table td) {
  background-color: transparent;
}

.instruction-drawer :deep(.el-table__body tr:hover > td) {
  background-color: rgba(125, 211, 252, 0.08);
}



.section-heading {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  margin-bottom: 10px;
}

.section-heading h4 {
  margin: 0;
  font-size: 18px;
}


.drawer-tabs {
  --el-color-primary: #7dd3fc;
}

.drawer-tabs :deep(.el-tabs__header) {
  background: transparent;
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
  margin-bottom: 18px;
}

.drawer-tabs :deep(.el-tabs__nav-wrap::after) {
  background-color: transparent;
}



.drawer-tabs :deep(.el-tabs__active-bar) {
  background-color: #7dd3fc;
}

.download-context {
  margin-bottom: 12px;
  font-size: 14px;
  color: #1f2a44;
  line-height: 1.4;
}

.download-context span + span {
  margin-top: 4px;
}

@media (max-width: 1200px) {
  .filters-form {
    flex-direction: column;
  }

  .drawer-meta {
    grid-template-columns: 1fr;
  }
}
</style>
