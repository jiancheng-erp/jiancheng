<template>
    <div class="material-batch-edit">
        <!-- 搜索栏 -->
        <el-form inline @submit.prevent="searchOrderShoes" class="search-bar">
            <el-form-item label="订单号/鞋型号">
                <el-input v-model="searchKeyword" placeholder="输入订单号或鞋型号搜索" clearable
                    style="width: 260px" @keyup.enter="searchOrderShoes" />
            </el-form-item>
            <el-form-item>
                <el-button type="primary" @click="searchOrderShoes">搜索</el-button>
            </el-form-item>
            <el-form-item v-if="selectedOrderShoe">
                <el-tag type="success" size="large">
                    当前: {{ selectedOrderShoe.orderRid }} - {{ selectedOrderShoe.shoeRid }}
                    <span v-if="selectedOrderShoe.customerProductName">
                        ({{ selectedOrderShoe.customerProductName }})
                    </span>
                </el-tag>
            </el-form-item>
        </el-form>

        <!-- 订单选择对话框 -->
        <el-dialog v-model="orderSelectVisible" title="选择订单-鞋款" width="700px" destroy-on-close>
            <el-table :data="orderShoeList" border stripe v-loading="orderSearchLoading"
                highlight-current-row @row-click="selectOrderShoe" max-height="400px"
                style="cursor: pointer;">
                <el-table-column prop="orderRid" label="订单号" width="160" />
                <el-table-column prop="shoeRid" label="鞋型号" width="160" />
                <el-table-column prop="customerProductName" label="客户款号" />
            </el-table>
        </el-dialog>

        <!-- 提示 -->
        <el-alert v-if="!selectedOrderShoe" type="info" :closable="false" style="margin-bottom: 16px">
            请先搜索并选择一个订单-鞋款，然后查看和编辑其所有文档中的材料信息。
        </el-alert>

        <!-- 配色选择 + 材料信息展示 -->
        <div v-if="selectedOrderShoe">
            <el-alert type="warning" :closable="false" style="margin-bottom: 16px">
                <strong>同步修改说明：</strong>不同配色的材料独立管理。请先选择配色，再修改该配色下的材料。修改时会同时更新勾选的文档（投产指令单、工艺单、BOM、采购订单）中对应的材料记录。
            </el-alert>

            <!-- 配色选择 Tabs -->
            <el-tabs v-model="selectedColorTypeId" type="card" @tab-change="onColorTabChange"
                v-loading="colorTypesLoading" style="margin-bottom: 12px;">
                <el-tab-pane label="全部配色" :name="0" />
                <el-tab-pane v-for="ct in colorTypes" :key="ct.orderShoeTypeId"
                    :name="ct.orderShoeTypeId">
                    <template #label>
                        {{ ct.colorName }}
                        <span v-if="ct.customerColorName" style="color: #909399; font-size: 12px;">
                            ({{ ct.customerColorName }})
                        </span>
                    </template>
                </el-tab-pane>
            </el-tabs>

            <!-- 材料表格 -->
            <el-table :data="materialGroups" border stripe v-loading="materialsLoading"
                row-key="materialId" height="60vh">
                <el-table-column type="expand">
                    <template #default="{ row }">
                        <div style="padding: 12px 24px;">
                            <div style="margin-bottom: 12px;">
                                <strong>材料在各文档中的记录 ({{ row.items.length }} 条)</strong>
                            </div>
                            <el-table :data="row.items" border size="small" style="width: 100%">
                                <el-table-column prop="docLabel" label="文档类型" width="130">
                                    <template #default="{ row: item }">
                                        <el-tag :type="docTagType(item.docType)" size="small">
                                            {{ item.docLabel }}
                                        </el-tag>
                                    </template>
                                </el-table-column>
                                <el-table-column prop="materialModel" label="型号" min-width="120">
                                    <template #default="{ row: item }">
                                        {{ item.materialModel || '（空）' }}
                                    </template>
                                </el-table-column>
                                <el-table-column prop="materialSpecification" label="规格" min-width="150">
                                    <template #default="{ row: item }">
                                        {{ item.materialSpecification || '（空）' }}
                                    </template>
                                </el-table-column>
                                <el-table-column prop="color" label="颜色" min-width="100">
                                    <template #default="{ row: item }">
                                        {{ item.color || '（空）' }}
                                    </template>
                                </el-table-column>
                                <el-table-column prop="materialSecondType" label="二级类别" width="100" />
                                <el-table-column label="备注" min-width="120">
                                    <template #default="{ row: item }">
                                        {{ item.remark || item.craftName || '' }}
                                    </template>
                                </el-table-column>
                            </el-table>
                        </div>
                    </template>
                </el-table-column>
                <el-table-column prop="materialId" label="材料ID" width="80" />
                <el-table-column prop="materialName" label="材料名称" min-width="140" />
                <el-table-column prop="supplierName" label="供应商" min-width="130" />
                <el-table-column label="型号/规格/颜色" min-width="240">
                    <template #default="{ row }">
                        <div class="material-summary">
                            <span v-for="(combo, idx) in getUniqueCombos(row)" :key="idx" class="combo-tag">
                                <el-tag size="small" type="info">
                                    {{ combo.model || '-' }} / {{ combo.spec || '-' }} / {{ combo.color || '-' }}
                                </el-tag>
                            </span>
                        </div>
                    </template>
                </el-table-column>
                <el-table-column label="出现文档" min-width="200">
                    <template #default="{ row }">
                        <el-tag v-for="dt in getDocTypes(row)" :key="dt.type"
                            :type="docTagType(dt.type)" size="small"
                            style="margin-right: 4px; margin-bottom: 2px;">
                            {{ dt.label }}: {{ dt.count }}条
                        </el-tag>
                    </template>
                </el-table-column>
                <el-table-column label="不一致" width="70">
                    <template #default="{ row }">
                        <el-icon v-if="hasInconsistency(row)" color="#e6a23c" :size="18">
                            <Warning />
                        </el-icon>
                        <el-icon v-else color="#67c23a" :size="18">
                            <CircleCheck />
                        </el-icon>
                    </template>
                </el-table-column>
                <el-table-column label="操作" width="100" fixed="right">
                    <template #default="{ row }">
                        <el-button type="primary" link size="small" @click="openEditDialog(row)"
                            :disabled="selectedColorTypeId === 0">
                            编辑
                        </el-button>
                    </template>
                </el-table-column>
            </el-table>
            <el-alert v-if="selectedColorTypeId === 0" type="info" :closable="false"
                style="margin-top: 8px;">
                "全部配色"模式下仅供查看，编辑材料请先选择具体配色。
            </el-alert>
        </div>

        <!-- 编辑对话框 -->
        <el-dialog v-model="editDialogVisible"
            :title="`编辑材料 - ${editTarget.materialName} (ID: ${editTarget.materialId})`"
            width="750px" destroy-on-close>
            <el-alert type="warning" :closable="false" style="margin-bottom: 16px">
                修改将同步更新当前配色「{{ currentColorLabel }}」下方勾选的所有文档类型中包含此材料的记录。
            </el-alert>

            <!-- 当前值展示 -->
            <div style="margin-bottom: 16px;">
                <strong>当前值（各文档中的记录）：</strong>
                <el-table :data="editTarget.items" border size="small" style="margin-top: 8px;" max-height="200px">
                    <el-table-column prop="docLabel" label="文档类型" width="130">
                        <template #default="{ row }">
                            <el-tag :type="docTagType(row.docType)" size="small">{{ row.docLabel }}</el-tag>
                        </template>
                    </el-table-column>
                    <el-table-column prop="materialModel" label="型号" min-width="120">
                        <template #default="{ row }">{{ row.materialModel || '（空）' }}</template>
                    </el-table-column>
                    <el-table-column prop="materialSpecification" label="规格" min-width="150">
                        <template #default="{ row }">{{ row.materialSpecification || '（空）' }}</template>
                    </el-table-column>
                    <el-table-column prop="color" label="颜色" min-width="100">
                        <template #default="{ row }">{{ row.color || '（空）' }}</template>
                    </el-table-column>
                </el-table>
            </div>

            <!-- 新值输入 -->
            <el-form label-width="120px" style="margin-bottom: 16px;">
                <el-form-item label="替换材料">
                    <el-switch v-model="editForm.changeMaterial" active-text="更换材料" inactive-text="仅修改属性" />
                </el-form-item>
                <el-form-item v-if="editForm.changeMaterial" label="新材料搜索">
                    <el-input v-model="materialSearchKw" placeholder="搜索材料名称" style="width: 260px"
                        @keyup.enter="searchMaterials" />
                    <el-button type="primary" @click="searchMaterials" style="margin-left: 8px">搜索</el-button>
                    <div v-if="materialSearchResults.length" style="margin-top: 8px;">
                        <el-select v-model="editForm.newMaterialId" placeholder="选择材料" style="width: 100%"
                            filterable>
                            <el-option v-for="mat in materialSearchResults" :key="mat.materialId"
                                :label="`${mat.materialName} (${mat.supplierName}) [ID:${mat.materialId}]`"
                                :value="mat.materialId" />
                        </el-select>
                    </div>
                </el-form-item>
                <el-form-item label="新型号">
                    <el-input v-model="editForm.newModel" placeholder="留空表示不修改"
                        style="width: 320px" clearable />
                </el-form-item>
                <el-form-item label="新规格">
                    <el-input v-model="editForm.newSpecification" placeholder="留空表示不修改"
                        style="width: 320px" clearable />
                </el-form-item>
                <el-form-item label="新颜色">
                    <el-input v-model="editForm.newColor" placeholder="留空表示不修改"
                        style="width: 320px" clearable />
                </el-form-item>
            </el-form>

            <!-- 选择影响的文档类型 -->
            <div style="margin-bottom: 12px;">
                <strong>同步修改的文档类型：</strong>
                <el-checkbox-group v-model="editForm.docTypes" style="margin-top: 8px;">
                    <el-checkbox value="production_instruction_item"
                        :disabled="!editTargetHasDoc('production_instruction_item')">
                        投产指令单
                        <el-tag v-if="editTargetHasDoc('production_instruction_item')" size="small" type="success">
                            {{ editTargetDocCount('production_instruction_item') }}条
                        </el-tag>
                    </el-checkbox>
                    <el-checkbox value="craft_sheet_item"
                        :disabled="!editTargetHasDoc('craft_sheet_item')">
                        工艺单
                        <el-tag v-if="editTargetHasDoc('craft_sheet_item')" size="small" type="warning">
                            {{ editTargetDocCount('craft_sheet_item') }}条
                        </el-tag>
                    </el-checkbox>
                    <el-checkbox value="bom_item"
                        :disabled="!editTargetHasDoc('bom_item')">
                        BOM
                        <el-tag v-if="editTargetHasDoc('bom_item')" size="small">
                            {{ editTargetDocCount('bom_item') }}条
                        </el-tag>
                    </el-checkbox>
                    <el-checkbox value="purchase_order_item"
                        :disabled="!editTargetHasDoc('purchase_order_item')">
                        采购订单
                        <el-tag v-if="editTargetHasDoc('purchase_order_item')" size="small" type="danger">
                            {{ editTargetDocCount('purchase_order_item') }}条
                        </el-tag>
                    </el-checkbox>
                </el-checkbox-group>
            </div>

            <template #footer>
                <el-button @click="editDialogVisible = false">取消</el-button>
                <el-button type="primary" :loading="editLoading" @click="submitEdit">
                    确认同步修改
                </el-button>
            </template>
        </el-dialog>
    </div>
</template>

<script>
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Warning, CircleCheck } from '@element-plus/icons-vue'

export default {
    name: 'MaterialBatchEdit',
    components: { Warning, CircleCheck },
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
            selectedColorTypeId: 0, // 0 = 全部配色

            // 材料列表
            materialGroups: [],
            materialsLoading: false,

            // 编辑
            editDialogVisible: false,
            editTarget: { materialId: null, materialName: '', items: [] },
            editForm: {
                changeMaterial: false,
                newMaterialId: null,
                newModel: null,
                newSpecification: null,
                newColor: null,
                docTypes: [],
            },
            editLoading: false,

            // 材料搜索
            materialSearchKw: '',
            materialSearchResults: [],
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
    },
    methods: {
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
                if (this.orderShoeList.length === 1) {
                    this.selectOrderShoe(this.orderShoeList[0])
                } else if (this.orderShoeList.length > 1) {
                    this.orderSelectVisible = true
                } else {
                    ElMessage.info('未找到匹配的订单')
                }
            } catch (e) {
                console.error(e)
                ElMessage.error('搜索订单失败')
            } finally {
                this.orderSearchLoading = false
            }
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
                // 如果只有一种配色，自动选中
                if (this.colorTypes.length === 1) {
                    this.selectedColorTypeId = this.colorTypes[0].orderShoeTypeId
                }
            } catch (e) {
                console.error(e)
                ElMessage.error('获取配色信息失败')
            } finally {
                this.colorTypesLoading = false
            }
        },

        onColorTabChange() {
            this.fetchMaterials()
        },

        async fetchMaterials() {
            if (!this.selectedOrderShoe) return
            this.materialsLoading = true
            try {
                const params = { orderShoeId: this.selectedOrderShoe.orderShoeId }
                if (this.selectedColorTypeId) {
                    params.orderShoeTypeId = this.selectedColorTypeId
                }
                const res = await axios.get(`${this.$apiBaseUrl}/material/ordershoe-materials`, {
                    params,
                })
                this.materialGroups = res.data.result || []
            } catch (e) {
                console.error(e)
                ElMessage.error('获取材料信息失败')
            } finally {
                this.materialsLoading = false
            }
        },

        getUniqueCombos(row) {
            const set = new Set()
            const combos = []
            for (const item of row.items) {
                const key = `${item.materialModel}|||${item.materialSpecification}|||${item.color}`
                if (!set.has(key)) {
                    set.add(key)
                    combos.push({
                        model: item.materialModel,
                        spec: item.materialSpecification,
                        color: item.color,
                    })
                }
            }
            return combos
        },

        getDocTypes(row) {
            const counts = {}
            for (const item of row.items) {
                if (!counts[item.docType]) {
                    counts[item.docType] = { type: item.docType, label: item.docLabel, count: 0 }
                }
                counts[item.docType].count++
            }
            return Object.values(counts)
        },

        hasInconsistency(row) {
            const combos = this.getUniqueCombos(row)
            return combos.length > 1
        },

        docTagType(docType) {
            const map = {
                production_instruction_item: 'success',
                craft_sheet_item: 'warning',
                bom_item: '',
                purchase_order_item: 'danger',
            }
            return map[docType] || ''
        },

        openEditDialog(row) {
            this.editTarget = { ...row }
            const combos = this.getUniqueCombos(row)
            const first = combos[0] || {}
            this.editForm = {
                changeMaterial: false,
                newMaterialId: null,
                newModel: first.model || '',
                newSpecification: first.spec || '',
                newColor: first.color || '',
                docTypes: [...new Set(row.items.map(i => i.docType))],
            }
            this.materialSearchKw = ''
            this.materialSearchResults = []
            this.editDialogVisible = true
        },

        editTargetHasDoc(docType) {
            return this.editTarget.items?.some(i => i.docType === docType)
        },

        editTargetDocCount(docType) {
            return (this.editTarget.items || []).filter(i => i.docType === docType).length
        },

        async searchMaterials() {
            if (!this.materialSearchKw.trim()) return
            try {
                const matRes = await axios.get(`${this.$apiBaseUrl}/material/variants`, {
                    params: {
                        materialName: this.materialSearchKw.trim(),
                        pageSize: 20,
                        page: 1,
                        showAll: 'true',
                    },
                })
                this.materialSearchResults = (matRes.data.result || []).map(m => ({
                    materialId: m.materialId,
                    materialName: m.materialName,
                    supplierName: m.supplierName,
                }))
            } catch (e) {
                console.error(e)
                ElMessage.error('搜索材料失败')
            }
        },

        async submitEdit() {
            const form = this.editForm
            const hasChange = form.newModel || form.newSpecification || form.newColor || form.newMaterialId
            if (!hasChange) {
                ElMessage.warning('请至少填写一个需要修改的字段')
                return
            }
            if (form.docTypes.length === 0) {
                ElMessage.warning('请至少勾选一个文档类型')
                return
            }

            const docLabels = form.docTypes.map(dt => {
                const map = {
                    production_instruction_item: '投产指令单',
                    craft_sheet_item: '工艺单',
                    bom_item: 'BOM',
                    purchase_order_item: '采购订单',
                }
                return map[dt] || dt
            })

            try {
                await ElMessageBox.confirm(
                    `确认同步修改配色「${this.currentColorLabel}」下的材料 "${this.editTarget.materialName}" ？\n` +
                    `文档类型：${docLabels.join('、')}\n` +
                    (form.newModel ? `型号 → "${form.newModel}"\n` : '') +
                    (form.newSpecification ? `规格 → "${form.newSpecification}"\n` : '') +
                    (form.newColor ? `颜色 → "${form.newColor}"\n` : '') +
                    (form.newMaterialId ? `替换材料ID → ${form.newMaterialId}\n` : '') +
                    '此操作将修改数据库中的多条记录，请确认无误。',
                    '确认同步修改',
                    { confirmButtonText: '确认修改', cancelButtonText: '取消', type: 'warning' }
                )
            } catch {
                return
            }

            this.editLoading = true
            try {
                const body = {
                    orderShoeId: this.selectedOrderShoe.orderShoeId,
                    orderShoeTypeId: this.selectedColorTypeId,
                    materialId: this.editTarget.materialId,
                    docTypes: form.docTypes,
                }
                if (form.newModel) body.newModel = form.newModel
                if (form.newSpecification) body.newSpecification = form.newSpecification
                if (form.newColor) body.newColor = form.newColor
                if (form.changeMaterial && form.newMaterialId) {
                    body.newMaterialId = form.newMaterialId
                }

                const res = await axios.post(
                    `${this.$apiBaseUrl}/material/batch-edit-materials`,
                    body
                )
                ElMessage.success(res.data.message || '修改成功')
                this.editDialogVisible = false
                this.fetchMaterials()
            } catch (e) {
                console.error(e)
                const msg = e.response?.data?.error || '修改失败'
                ElMessage.error(msg)
            } finally {
                this.editLoading = false
            }
        },
    },
}
</script>

<style scoped>
.material-batch-edit {
    padding: 16px;
}

.search-bar {
    margin-bottom: 12px;
    display: flex;
    flex-wrap: wrap;
    align-items: flex-end;
    gap: 0;
}

.search-bar :deep(.el-form-item) {
    margin-bottom: 8px;
    margin-right: 12px;
}

.search-bar :deep(.el-form-item__label) {
    padding-right: 4px;
}

.material-summary {
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
}

.combo-tag {
    margin-bottom: 2px;
}
</style>
