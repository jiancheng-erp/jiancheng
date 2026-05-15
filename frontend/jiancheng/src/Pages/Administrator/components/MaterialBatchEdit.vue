<template>
    <div class="material-batch-edit">
        <!-- ============= 顶部：搜索栏 ============= -->
        <div class="toolbar">
            <el-form inline @submit.prevent="searchOrderShoes" class="search-bar">
                <el-form-item label="订单号/鞋型号">
                    <el-input v-model="searchKeyword" placeholder="输入订单号或鞋型号搜索"
                        clearable style="width: 280px" @keyup.enter="searchOrderShoes" />
                </el-form-item>
                <el-form-item>
                    <el-button type="primary" @click="searchOrderShoes">搜索</el-button>
                </el-form-item>
                <el-form-item v-if="selectedOrderShoe">
                    <el-tag type="success" size="large" closable @close="clearSelection">
                        <strong>{{ selectedOrderShoe.orderRid }}</strong>
                        / <strong>{{ selectedOrderShoe.shoeRid }}</strong>
                        <span v-if="selectedOrderShoe.customerProductName">
                            ({{ selectedOrderShoe.customerProductName }})
                        </span>
                    </el-tag>
                </el-form-item>
                <el-form-item v-if="selectedOrderShoe">
                    <el-button @click="fetchMaterials" :loading="materialsLoading">刷新材料</el-button>
                </el-form-item>
            </el-form>
        </div>

        <!-- 订单选择对话框 -->
        <el-dialog v-model="orderSelectVisible" title="选择订单-鞋款" width="720px" destroy-on-close>
            <el-table :data="orderShoeList" border stripe v-loading="orderSearchLoading"
                highlight-current-row @row-click="selectOrderShoe" max-height="420px"
                style="cursor: pointer;">
                <el-table-column prop="orderRid" label="订单号" width="170" />
                <el-table-column prop="shoeRid" label="鞋型号" width="170" />
                <el-table-column prop="customerProductName" label="客户款号" />
            </el-table>
        </el-dialog>

        <!-- ============= 空态提示 ============= -->
        <el-empty v-if="!selectedOrderShoe" description="请先搜索并选择一个订单-鞋款">
            <template #image>
                <el-icon :size="64" color="#dcdfe6"><Search /></el-icon>
            </template>
        </el-empty>

        <!-- ============= 配色 Tabs + 材料表格 ============= -->
        <div v-else>
            <!-- 说明卡片 -->
            <el-alert type="info" :closable="false" show-icon style="margin-bottom: 12px;">
                <div>
                    <strong>同步修改说明：</strong>
                    本工具以「投产指令单 (PI)」为根，沿 PI → 工艺单 / BOM → 采购订单 的链路
                    <strong style="color:#e6a23c;">全量联动</strong>。无需勾选文档类型，
                    修改时所有相关记录会自动一起更新。
                    若新材料供应商变化，对应采购订单项会自动搬移到目标供应商的采购分单。
                </div>
            </el-alert>

            <!-- 配色 Tabs -->
            <el-tabs v-model="selectedColorTypeId" type="card" @tab-change="onColorTabChange"
                v-loading="colorTypesLoading" style="margin-bottom: 10px;">
                <el-tab-pane label="全部配色" :name="0" />
                <el-tab-pane v-for="ct in colorTypes" :key="ct.orderShoeTypeId"
                    :name="ct.orderShoeTypeId">
                    <template #label>
                        <span>{{ ct.colorName }}</span>
                        <span v-if="ct.customerColorName" class="custom-color-name">
                            ({{ ct.customerColorName }})
                        </span>
                    </template>
                </el-tab-pane>
            </el-tabs>

            <!-- 工具条：过滤 -->
            <div class="filter-bar">
                <el-input v-model="filterText" placeholder="按材料名 / 供应商 / 型号 / 规格 / 颜色 过滤"
                    clearable style="width: 360px" prefix-icon="Search" />
                <el-checkbox v-model="onlyInconsistent">仅显示不一致</el-checkbox>
                <span class="stats">共 {{ filteredGroups.length }} / {{ materialGroups.length }} 个材料</span>
            </div>

            <!-- 材料表格 -->
            <el-table :data="filteredGroups" border stripe v-loading="materialsLoading"
                row-key="materialId" height="62vh" class="mat-table">
                <el-table-column type="expand">
                    <template #default="{ row }">
                        <div class="expand-panel">
                            <div class="expand-header">
                                <strong>{{ row.materialName }}</strong>
                                <el-tag size="small">ID: {{ row.materialId }}</el-tag>
                                <el-tag size="small" type="info">供应商: {{ row.supplierName || '-' }}</el-tag>
                                <span style="color:#909399;">共 {{ row.items.length }} 条记录</span>
                            </div>
                            <el-table :data="row.items" border size="small" style="width: 100%">
                                <el-table-column label="文档" width="130">
                                    <template #default="{ row: it }">
                                        <el-tag :type="docTagType(it.docType)" size="small">
                                            {{ it.docLabel }}
                                        </el-tag>
                                    </template>
                                </el-table-column>
                                <el-table-column label="配色" width="110">
                                    <template #default="{ row: it }">
                                        {{ colorLabelOf(it.orderShoeTypeId) }}
                                    </template>
                                </el-table-column>
                                <el-table-column label="型号" prop="materialModel" min-width="120">
                                    <template #default="{ row: it }">{{ it.materialModel || '（空）' }}</template>
                                </el-table-column>
                                <el-table-column label="规格" prop="materialSpecification" min-width="150">
                                    <template #default="{ row: it }">{{ it.materialSpecification || '（空）' }}</template>
                                </el-table-column>
                                <el-table-column label="颜色" prop="color" min-width="100">
                                    <template #default="{ row: it }">{{ it.color || '（空）' }}</template>
                                </el-table-column>
                                <el-table-column label="链路根" width="130">
                                    <template #default="{ row: it }">
                                        <el-tooltip v-if="it.linkRootId"
                                            :content="it.docType === 'purchase_order_item' ?
                                                `BOM项 #${it.linkRootId}` : `PI项 #${it.linkRootId}`">
                                            <el-tag size="small" effect="plain">
                                                #{{ it.linkRootId }}
                                            </el-tag>
                                        </el-tooltip>
                                        <el-tag v-else size="small" type="danger" effect="plain">无链路</el-tag>
                                    </template>
                                </el-table-column>
                                <el-table-column label="所属 PO/PDO" min-width="160">
                                    <template #default="{ row: it }">
                                        <span v-if="it.docType === 'purchase_order_item'">
                                            {{ it.purchaseOrderRid }}
                                            <el-tag size="small" effect="plain" style="margin-left:4px;">
                                                {{ it.purchaseDivideOrderRid }}
                                            </el-tag>
                                        </span>
                                        <span v-else style="color:#c0c4cc">—</span>
                                    </template>
                                </el-table-column>
                            </el-table>
                        </div>
                    </template>
                </el-table-column>
                <el-table-column prop="materialId" label="ID" width="70" />
                <el-table-column prop="materialName" label="材料名称" min-width="160" show-overflow-tooltip />
                <el-table-column prop="supplierName" label="供应商" min-width="130" show-overflow-tooltip />
                <el-table-column label="型号/规格/颜色 组合" min-width="280">
                    <template #default="{ row }">
                        <div class="combo-list">
                            <el-tag v-for="(combo, idx) in getUniqueCombos(row)" :key="idx"
                                size="small" type="info" effect="plain" style="margin: 2px;">
                                {{ combo.model || '-' }} / {{ combo.spec || '-' }} / {{ combo.color || '-' }}
                            </el-tag>
                        </div>
                    </template>
                </el-table-column>
                <el-table-column label="文档分布" min-width="230">
                    <template #default="{ row }">
                        <el-tag v-for="dt in getDocCounts(row)" :key="dt.type"
                            :type="docTagType(dt.type)" size="small"
                            style="margin: 2px;">
                            {{ dt.label }} × {{ dt.count }}
                        </el-tag>
                    </template>
                </el-table-column>
                <el-table-column label="覆盖配色" width="120">
                    <template #default="{ row }">
                        <el-tag size="small" :type="row.colorPresence.length > 1 ? 'warning' : ''">
                            {{ row.colorPresence.length }} 个配色
                        </el-tag>
                    </template>
                </el-table-column>
                <el-table-column label="状态" width="80" align="center">
                    <template #default="{ row }">
                        <el-tooltip :content="hasInconsistency(row) ? '该材料在不同文档/配色中型号/规格/颜色不一致' : '一致'">
                            <el-icon v-if="hasInconsistency(row)" color="#e6a23c" :size="20">
                                <Warning />
                            </el-icon>
                            <el-icon v-else color="#67c23a" :size="20">
                                <CircleCheck />
                            </el-icon>
                        </el-tooltip>
                    </template>
                </el-table-column>
                <el-table-column label="操作" width="120" fixed="right">
                    <template #default="{ row }">
                        <el-button type="primary" link size="small" @click="openEditDialog(row)">
                            整体替换/修改
                        </el-button>
                    </template>
                </el-table-column>
            </el-table>
        </div>

        <!-- ================= 编辑对话框 ================= -->
        <el-dialog v-model="editDialogVisible" :title="editDialogTitle"
            width="900px" destroy-on-close top="6vh">
            <!-- Step 1. 修改范围 -->
            <el-divider content-position="left">① 修改范围</el-divider>
            <el-radio-group v-model="editForm.scope" @change="onScopeChange">
                <el-radio value="color" :disabled="selectedColorTypeId === 0">
                    仅当前配色
                    <span style="color:#909399; margin-left:4px;">
                        ({{ currentColorLabel || '未选择' }})
                    </span>
                </el-radio>
                <el-radio value="shoe">
                    整鞋款 (所有 {{ editTarget.colorPresence?.length || 0 }} 个含该材料的配色一起改)
                </el-radio>
            </el-radio-group>
            <el-alert v-if="selectedColorTypeId === 0 && editForm.scope === 'color'"
                type="warning" :closable="false" style="margin-top:8px;">
                "全部配色"视图下无法按配色编辑，已自动切换到整鞋款。
            </el-alert>

            <!-- Step 2. 新材料 -->
            <el-divider content-position="left">② 选择新材料（可选）</el-divider>
            <el-form label-width="100px" inline>
                <el-form-item>
                    <el-switch v-model="editForm.changeMaterial" active-text="更换材料(可换厂家)"
                        inactive-text="保持原材料" @change="onChangeMaterialToggle" />
                </el-form-item>
            </el-form>
            <div v-if="editForm.changeMaterial" class="mat-search-block">
                <el-input v-model="materialSearchKw" placeholder="按材料名称搜索（可包含其他供应商的同名材料）"
                    style="width: 380px" @keyup.enter="searchMaterials" clearable>
                    <template #append>
                        <el-button @click="searchMaterials" :loading="materialSearchLoading">
                            搜索
                        </el-button>
                    </template>
                </el-input>
                <el-select v-if="materialSearchResults.length" v-model="editForm.newMaterialId"
                    placeholder="选择新材料" style="width: 100%; margin-top: 8px;" filterable
                    @change="onNewMaterialSelected">
                    <el-option v-for="mat in materialSearchResults" :key="mat.materialId"
                        :label="`${mat.materialName} | ${mat.supplierName || '无供应商'} (ID:${mat.materialId})`"
                        :value="mat.materialId">
                        <span style="float: left">{{ mat.materialName }}</span>
                        <span style="float: right; color: #8492a6; font-size: 12px;">
                            {{ mat.supplierName || '无供应商' }} | ID:{{ mat.materialId }}
                        </span>
                    </el-option>
                </el-select>
            </div>

            <!-- Step 3. 新属性 -->
            <el-divider content-position="left">③ 新属性</el-divider>
            <el-form label-width="100px">
                <el-row :gutter="12">
                    <el-col :span="8">
                        <el-form-item label="型号">
                            <el-input v-model="editForm.newModel" placeholder="（不修改请清空）" clearable />
                        </el-form-item>
                    </el-col>
                    <el-col :span="8">
                        <el-form-item label="规格">
                            <el-input v-model="editForm.newSpecification" placeholder="（不修改请清空）" clearable />
                        </el-form-item>
                    </el-col>
                    <el-col :span="8">
                        <el-form-item label="颜色">
                            <el-input v-model="editForm.newColor" placeholder="（不修改请清空）" clearable />
                        </el-form-item>
                    </el-col>
                </el-row>
            </el-form>

            <!-- Step 4. 旧/新 对比 -->
            <el-divider content-position="left">④ 旧 / 新 对比</el-divider>
            <el-table :data="diffRows" border size="small" style="width: 100%">
                <el-table-column prop="label" label="字段" width="120" />
                <el-table-column label="旧值">
                    <template #default="{ row }">
                        <span :class="{ 'old-val': row.changed }">{{ row.oldVal || '（空）' }}</span>
                    </template>
                </el-table-column>
                <el-table-column label="新值">
                    <template #default="{ row }">
                        <span :class="{ 'new-val': row.changed }">
                            <strong>{{ row.newVal || '（空）' }}</strong>
                            <el-tag v-if="row.changed" type="warning" size="small" style="margin-left:6px;">
                                变更
                            </el-tag>
                        </span>
                    </template>
                </el-table-column>
            </el-table>

            <!-- Step 5. 影响预览 -->
            <el-divider content-position="left">⑤ 影响预览</el-divider>
            <div v-if="!previewData" style="text-align:center; padding: 12px 0;">
                <el-button @click="loadPreview" :loading="previewLoading" :disabled="!isFormReady">
                    生成影响预览
                </el-button>
                <div v-if="!isFormReady" style="color:#909399; font-size:12px; margin-top:6px;">
                    请至少填写一个要修改的字段
                </div>
            </div>
            <div v-else>
                <el-row :gutter="12">
                    <el-col :span="6">
                        <div class="preview-card success">
                            <div class="num">{{ previewData.counts.production_instruction_item }}</div>
                            <div class="lbl">投产指令单</div>
                        </div>
                    </el-col>
                    <el-col :span="6">
                        <div class="preview-card warning">
                            <div class="num">{{ previewData.counts.craft_sheet_item }}</div>
                            <div class="lbl">工艺单</div>
                        </div>
                    </el-col>
                    <el-col :span="6">
                        <div class="preview-card primary">
                            <div class="num">{{ previewData.counts.bom_item }}</div>
                            <div class="lbl">BOM 项</div>
                        </div>
                    </el-col>
                    <el-col :span="6">
                        <div class="preview-card danger">
                            <div class="num">{{ previewData.counts.purchase_order_item }}</div>
                            <div class="lbl">采购订单项</div>
                        </div>
                    </el-col>
                </el-row>
                <el-alert v-if="previewData.supplierChanged" type="warning" :closable="false"
                    show-icon style="margin-top:12px;">
                    <strong>检测到供应商变化：</strong>
                    旧供应商「{{ previewData.oldMaterial?.supplierName || '-' }}」→
                    新供应商「{{ previewData.newMaterial?.supplierName || '-' }}」。
                    将会把 <strong>{{ previewData.poSplitCount }}</strong> 条采购订单项
                    自动搬移到新供应商对应的采购分单 (purchase_divide_order)。
                </el-alert>
                <el-alert v-if="previewData.counts.production_instruction_item === 0 &&
                              (previewData.counts.bom_item > 0 || previewData.counts.purchase_order_item > 0)"
                    type="info" :closable="false" show-icon style="margin-top:8px;">
                    当前范围下未找到投产指令单匹配项，但仍会更新通过链路或材料 ID 兜底匹配到的工艺单/BOM/采购订单项。
                </el-alert>
                <div v-if="previewData.pdoBreakdown?.length" style="margin-top:10px;">
                    <el-collapse>
                        <el-collapse-item title="受影响采购分单明细">
                            <el-table :data="previewData.pdoBreakdown" size="small" border>
                                <el-table-column prop="purchaseOrderRid" label="采购订单号" />
                                <el-table-column prop="purchaseDivideOrderRid" label="采购分单号" />
                                <el-table-column prop="itemCount" label="受影响行数" width="120" />
                            </el-table>
                        </el-collapse-item>
                    </el-collapse>
                </div>
            </div>

            <template #footer>
                <el-button @click="editDialogVisible = false">取消</el-button>
                <el-button v-if="previewData" type="success" :loading="editLoading"
                    @click="submitEdit">
                    确认执行 (共 {{ previewTotal }} 条)
                </el-button>
            </template>
        </el-dialog>
    </div>
</template>

<script>
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Warning, CircleCheck, Search } from '@element-plus/icons-vue'

export default {
    name: 'MaterialBatchEdit',
    components: { Warning, CircleCheck, Search },
    data() {
        return {
            // 搜索
            searchKeyword: '',
            orderShoeList: [],
            orderSearchLoading: false,
            orderSelectVisible: false,
            selectedOrderShoe: null,

            // 配色
            colorTypes: [],
            colorTypesLoading: false,
            selectedColorTypeId: 0,

            // 材料列表
            materialGroups: [],
            materialsLoading: false,
            filterText: '',
            onlyInconsistent: false,

            // 编辑
            editDialogVisible: false,
            editTarget: { materialId: null, materialName: '', items: [], colorPresence: [] },
            editForm: {
                scope: 'color',
                changeMaterial: false,
                newMaterialId: null,
                newModel: '',
                newSpecification: '',
                newColor: '',
            },
            editLoading: false,

            // 材料搜索
            materialSearchKw: '',
            materialSearchResults: [],
            materialSearchLoading: false,

            // 预览
            previewData: null,
            previewLoading: false,
        }
    },
    computed: {
        currentColorLabel() {
            if (this.selectedColorTypeId === 0) return '全部配色'
            const ct = this.colorTypes.find(c => c.orderShoeTypeId === this.selectedColorTypeId)
            if (!ct) return ''
            return ct.customerColorName
                ? `${ct.colorName}(${ct.customerColorName})`
                : ct.colorName
        },
        editDialogTitle() {
            if (!this.editTarget?.materialId) return '编辑材料'
            return `同步修改材料：${this.editTarget.materialName} (ID: ${this.editTarget.materialId})`
        },
        filteredGroups() {
            const kw = this.filterText.trim().toLowerCase()
            return this.materialGroups.filter(g => {
                if (this.onlyInconsistent && !this.hasInconsistency(g)) return false
                if (!kw) return true
                const hay = [
                    g.materialName, g.supplierName,
                    ...g.items.map(i => `${i.materialModel} ${i.materialSpecification} ${i.color}`),
                ].join(' ').toLowerCase()
                return hay.includes(kw)
            })
        },
        diffRows() {
            const items = this.editTarget?.items || []
            const oldName = this.editTarget.materialName || ''
            const oldSupplier = this.editTarget.supplierName || ''
            const newMat = this.editForm.changeMaterial && this.editForm.newMaterialId
                ? this.materialSearchResults.find(m => m.materialId === this.editForm.newMaterialId)
                : null
            const newName = newMat ? newMat.materialName : oldName
            const newSupplier = newMat ? (newMat.supplierName || '') : oldSupplier

            // 取旧值：若同一字段有多个值，用逗号合并
            const collectVals = (key) => {
                const set = new Set(items.map(i => i[key] || '').filter(v => v !== ''))
                return [...set].join(' / ') || '（空）'
            }
            const oldModel = collectVals('materialModel')
            const oldSpec = collectVals('materialSpecification')
            const oldColor = collectVals('color')
            const newModel = this.editForm.newModel || oldModel
            const newSpec = this.editForm.newSpecification || oldSpec
            const newColor = this.editForm.newColor || oldColor

            return [
                { label: '材料名称', oldVal: oldName, newVal: newName, changed: newName !== oldName },
                { label: '供应商', oldVal: oldSupplier, newVal: newSupplier, changed: newSupplier !== oldSupplier },
                { label: '型号', oldVal: oldModel, newVal: newModel, changed: newModel !== oldModel },
                { label: '规格', oldVal: oldSpec, newVal: newSpec, changed: newSpec !== oldSpec },
                { label: '颜色', oldVal: oldColor, newVal: newColor, changed: newColor !== oldColor },
            ]
        },
        isFormReady() {
            const f = this.editForm
            const hasMat = f.changeMaterial && f.newMaterialId
            return !!(hasMat || f.newModel || f.newSpecification || f.newColor)
        },
        previewTotal() {
            if (!this.previewData) return 0
            const c = this.previewData.counts
            return (c.production_instruction_item || 0)
                + (c.craft_sheet_item || 0) + (c.bom_item || 0)
                + (c.purchase_order_item || 0)
        },
    },
    watch: {
        // 表单任何变动 → 让预览失效
        'editForm.newModel'() { this.previewData = null },
        'editForm.newSpecification'() { this.previewData = null },
        'editForm.newColor'() { this.previewData = null },
        'editForm.newMaterialId'() { this.previewData = null },
        'editForm.changeMaterial'(v) { if (!v) this.editForm.newMaterialId = null; this.previewData = null },
        'editForm.scope'() { this.previewData = null },
    },
    methods: {
        clearSelection() {
            this.selectedOrderShoe = null
            this.colorTypes = []
            this.materialGroups = []
            this.selectedColorTypeId = 0
        },
        async searchOrderShoes() {
            if (!this.searchKeyword.trim()) {
                ElMessage.warning('请输入订单号或鞋型号')
                return
            }
            this.orderSearchLoading = true
            try {
                const res = await axios.get(`${this.$apiBaseUrl}/material/search-order-shoes`, {
                    params: { keyword: this.searchKeyword.trim() },
                })
                this.orderShoeList = res.data.result || []
                if (this.orderShoeList.length === 1) this.selectOrderShoe(this.orderShoeList[0])
                else if (this.orderShoeList.length > 1) this.orderSelectVisible = true
                else ElMessage.info('未找到匹配的订单')
            } catch (e) {
                console.error(e); ElMessage.error('搜索订单失败')
            } finally { this.orderSearchLoading = false }
        },
        async selectOrderShoe(row) {
            this.selectedOrderShoe = row
            this.orderSelectVisible = false
            this.selectedColorTypeId = 0
            this.materialGroups = []
            await this.fetchColorTypes()
            this.fetchMaterials()
        },
        async fetchColorTypes() {
            if (!this.selectedOrderShoe) return
            this.colorTypesLoading = true
            try {
                const res = await axios.get(`${this.$apiBaseUrl}/material/ordershoe-color-types`, {
                    params: { orderShoeId: this.selectedOrderShoe.orderShoeId },
                })
                this.colorTypes = res.data.result || []
                if (this.colorTypes.length === 1) {
                    this.selectedColorTypeId = this.colorTypes[0].orderShoeTypeId
                }
            } catch (e) { console.error(e); ElMessage.error('获取配色失败') }
            finally { this.colorTypesLoading = false }
        },
        onColorTabChange() { this.fetchMaterials() },
        async fetchMaterials() {
            if (!this.selectedOrderShoe) return
            this.materialsLoading = true
            try {
                const params = { orderShoeId: this.selectedOrderShoe.orderShoeId }
                if (this.selectedColorTypeId) params.orderShoeTypeId = this.selectedColorTypeId
                const res = await axios.get(`${this.$apiBaseUrl}/material/ordershoe-materials`, { params })
                this.materialGroups = res.data.result || []
            } catch (e) { console.error(e); ElMessage.error('获取材料信息失败') }
            finally { this.materialsLoading = false }
        },

        // ===== 表格渲染辅助 =====
        getUniqueCombos(row) {
            const set = new Set(), out = []
            for (const it of row.items) {
                const k = `${it.materialModel}|${it.materialSpecification}|${it.color}`
                if (!set.has(k)) {
                    set.add(k)
                    out.push({ model: it.materialModel, spec: it.materialSpecification, color: it.color })
                }
            }
            return out
        },
        getDocCounts(row) {
            const counts = {}
            for (const it of row.items) {
                if (!counts[it.docType]) counts[it.docType] = { type: it.docType, label: it.docLabel, count: 0 }
                counts[it.docType].count++
            }
            return Object.values(counts)
        },
        hasInconsistency(row) { return this.getUniqueCombos(row).length > 1 },
        docTagType(docType) {
            return ({
                production_instruction_item: 'success',
                craft_sheet_item: 'warning',
                bom_item: '',
                purchase_order_item: 'danger',
            })[docType] || ''
        },
        colorLabelOf(ostId) {
            if (!ostId) return '-'
            const ct = this.colorTypes.find(c => c.orderShoeTypeId === ostId)
            if (!ct) return `#${ostId}`
            return ct.customerColorName ? `${ct.colorName}(${ct.customerColorName})` : ct.colorName
        },

        // ===== 编辑对话框 =====
        openEditDialog(row) {
            this.editTarget = { ...row }
            const first = this.getUniqueCombos(row)[0] || {}
            this.editForm = {
                scope: this.selectedColorTypeId === 0 ? 'shoe' : 'color',
                changeMaterial: false,
                newMaterialId: null,
                newModel: first.model || '',
                newSpecification: first.spec || '',
                newColor: first.color || '',
            }
            this.materialSearchKw = row.materialName
            this.materialSearchResults = []
            this.previewData = null
            this.editDialogVisible = true
        },
        onScopeChange() { this.previewData = null },
        onChangeMaterialToggle(val) {
            if (val && !this.materialSearchResults.length && this.materialSearchKw) {
                this.searchMaterials()
            }
        },
        onNewMaterialSelected(mid) {
            const mat = this.materialSearchResults.find(m => m.materialId === mid)
            if (!mat) return
            // 若新材料名 != 旧材料名 不强制；型号/规格/颜色保留用户已填值
        },
        async searchMaterials() {
            const kw = this.materialSearchKw.trim()
            if (!kw) { ElMessage.warning('请输入搜索关键字'); return }
            this.materialSearchLoading = true
            try {
                const res = await axios.get(`${this.$apiBaseUrl}/material/variants`, {
                    params: { materialName: kw, pageSize: 50, page: 1, showAll: 'true' },
                })
                this.materialSearchResults = (res.data.result || []).map(m => ({
                    materialId: m.materialId,
                    materialName: m.materialName,
                    supplierName: m.supplierName || '',
                }))
                if (!this.materialSearchResults.length) ElMessage.info('未找到匹配的材料')
            } catch (e) { console.error(e); ElMessage.error('搜索材料失败') }
            finally { this.materialSearchLoading = false }
        },
        buildPayload() {
            const f = this.editForm
            const body = {
                orderShoeId: this.selectedOrderShoe.orderShoeId,
                materialId: this.editTarget.materialId,
                scope: f.scope,
            }
            if (f.scope === 'color') body.orderShoeTypeId = this.selectedColorTypeId
            if (f.changeMaterial && f.newMaterialId) body.newMaterialId = f.newMaterialId
            // 空字符串 → 不修改；后端通过 null 判定。空串视为不修改更直观，
            // 但若用户明确想清空可改为发送 ""。这里采用：空串=不修改。
            if (f.newModel !== '' && f.newModel != null) body.newModel = f.newModel
            if (f.newSpecification !== '' && f.newSpecification != null) body.newSpecification = f.newSpecification
            if (f.newColor !== '' && f.newColor != null) body.newColor = f.newColor
            return body
        },
        async loadPreview() {
            if (!this.isFormReady) { ElMessage.warning('请至少填写一个要修改的字段'); return }
            if (this.editForm.scope === 'color' && !this.selectedColorTypeId) {
                ElMessage.warning('配色范围下需先选择具体配色'); return
            }
            this.previewLoading = true
            try {
                const res = await axios.post(
                    `${this.$apiBaseUrl}/material/batch-edit-materials/preview`,
                    this.buildPayload(),
                )
                this.previewData = res.data
            } catch (e) {
                console.error(e)
                ElMessage.error(e.response?.data?.error || '预览失败')
            } finally { this.previewLoading = false }
        },
        async submitEdit() {
            if (!this.previewData) { ElMessage.warning('请先生成影响预览'); return }
            const total = this.previewTotal
            if (total === 0) { ElMessage.warning('当前范围下没有可更新的记录'); return }

            const f = this.editForm
            const changes = []
            if (f.changeMaterial && f.newMaterialId) {
                const newMat = this.materialSearchResults.find(m => m.materialId === f.newMaterialId)
                changes.push(`材料 → ${newMat?.materialName || ''} (供应商: ${newMat?.supplierName || '-'})`)
            }
            if (f.newModel) changes.push(`型号 → "${f.newModel}"`)
            if (f.newSpecification) changes.push(`规格 → "${f.newSpecification}"`)
            if (f.newColor) changes.push(`颜色 → "${f.newColor}"`)
            const scopeText = f.scope === 'color'
                ? `当前配色「${this.currentColorLabel}」`
                : `整鞋款 (${this.editTarget.colorPresence?.length || 0} 个配色)`

            try {
                await ElMessageBox.confirm(
                    `范围: ${scopeText}\n` +
                    `${changes.join('\n')}\n` +
                    `共 ${total} 条记录将被更新` +
                    (this.previewData.supplierChanged
                        ? `\n⚠ 供应商变化：${this.previewData.poSplitCount} 条采购订单项将被搬移到新供应商分单`
                        : ''),
                    '确认同步修改',
                    { confirmButtonText: '确认执行', cancelButtonText: '取消', type: 'warning' }
                )
            } catch { return }

            this.editLoading = true
            try {
                const res = await axios.post(
                    `${this.$apiBaseUrl}/material/batch-edit-materials`,
                    this.buildPayload(),
                )
                ElMessage.success(res.data.message || '修改成功')
                this.editDialogVisible = false
                this.fetchMaterials()
            } catch (e) {
                console.error(e)
                ElMessage.error(e.response?.data?.error || '修改失败')
            } finally { this.editLoading = false }
        },
    },
}
</script>

<style scoped>
.material-batch-edit {
    padding: 16px;
}

.toolbar {
    margin-bottom: 4px;
}

.search-bar :deep(.el-form-item) {
    margin-bottom: 8px;
    margin-right: 12px;
}

.custom-color-name {
    color: #909399;
    font-size: 12px;
    margin-left: 2px;
}

.filter-bar {
    display: flex;
    gap: 12px;
    align-items: center;
    margin-bottom: 8px;
}

.filter-bar .stats {
    margin-left: auto;
    color: #909399;
    font-size: 13px;
}

.mat-table :deep(.el-table__expanded-cell) {
    background: #fafbfc;
}

.expand-panel {
    padding: 12px 20px;
}

.expand-header {
    display: flex;
    gap: 10px;
    align-items: center;
    margin-bottom: 8px;
}

.combo-list {
    display: flex;
    flex-wrap: wrap;
}

.mat-search-block {
    padding: 4px 0 8px 16px;
}

.old-val {
    color: #909399;
    text-decoration: line-through;
}

.new-val {
    color: #67c23a;
}

.preview-card {
    border-radius: 6px;
    padding: 16px 12px;
    text-align: center;
    color: #fff;
}

.preview-card .num {
    font-size: 28px;
    font-weight: 600;
    line-height: 1;
}

.preview-card .lbl {
    font-size: 13px;
    margin-top: 6px;
    opacity: 0.92;
}

.preview-card.success {
    background: linear-gradient(135deg, #67c23a, #95d475);
}

.preview-card.warning {
    background: linear-gradient(135deg, #e6a23c, #eebe77);
}

.preview-card.primary {
    background: linear-gradient(135deg, #409eff, #79bbff);
}

.preview-card.danger {
    background: linear-gradient(135deg, #f56c6c, #f89898);
}
</style>
