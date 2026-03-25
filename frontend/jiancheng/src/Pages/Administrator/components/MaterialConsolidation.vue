<template>
    <div class="material-consolidation">
        <!-- 搜索栏 -->
        <el-form inline @submit.prevent="fetchVariants" class="search-bar">
            <el-form-item label="材料名称">
                <el-input v-model="search.materialName" placeholder="模糊搜索" clearable style="width:180px" @keyup.enter="fetchVariants" />
            </el-form-item>
            <el-form-item label="供应商">
                <el-input v-model="search.supplierName" placeholder="模糊搜索" clearable style="width:180px" @keyup.enter="fetchVariants" />
            </el-form-item>
            <el-form-item label="材料类型">
                <el-input v-model="search.materialType" placeholder="模糊搜索" clearable style="width:150px" @keyup.enter="fetchVariants" />
            </el-form-item>
            <el-form-item>
                <el-checkbox v-model="search.showAll">显示所有（含无重复）</el-checkbox>
            </el-form-item>
            <el-form-item>
                <el-button type="primary" @click="fetchVariants">查询</el-button>
            </el-form-item>
        </el-form>

        <!-- 材料列表 -->
        <el-table :data="materialList" border stripe style="width:100%" v-loading="loading" height="70vh" row-key="materialId">
            <el-table-column type="expand">
                <template #default="{ row }">
                    <div style="padding: 12px 24px;">
                        <div style="margin-bottom:12px; display:flex; align-items:center; gap:12px;">
                            <strong>变体列表（{{ row.variantCount }} 个组合）</strong>
                            <el-button v-if="row.variantCount >= 2" type="warning" size="small" @click="openMergeDialog(row)">
                                合并变体
                            </el-button>
                            <el-tag v-if="row.similarPairs && row.similarPairs.length" type="warning" size="small">
                                发现 {{ row.similarPairs.length }} 对相似变体
                            </el-tag>
                        </div>
                        <el-table :data="row.variants" border size="small" style="width:100%"
                            :row-class-name="(scope) => getVariantRowClass(row, scope.$index)">
                            <el-table-column prop="materialModel" label="型号" min-width="180">
                                <template #default="{ row: v }">
                                    <span>{{ v.materialModel || '（空）' }}</span>
                                </template>
                            </el-table-column>
                            <el-table-column prop="materialSpecification" label="规格" min-width="200">
                                <template #default="{ row: v }">
                                    <span>{{ v.materialSpecification || '（空）' }}</span>
                                </template>
                            </el-table-column>
                            <el-table-column prop="color" label="颜色" min-width="120">
                                <template #default="{ row: v }">
                                    <span>{{ v.color || '（空）' }}</span>
                                </template>
                            </el-table-column>
                            <el-table-column label="引用次数" width="100">
                                <template #default="{ row: v }">
                                    <el-tag>{{ v.totalRefs }}</el-tag>
                                </template>
                            </el-table-column>
                            <el-table-column label="引用来源" min-width="320">
                                <template #default="{ row: v }">
                                    <el-tag
                                        v-for="(count, table) in v.sources"
                                        :key="table"
                                        size="small"
                                        :type="sourceTagType(table)"
                                        style="margin-right:4px; margin-bottom:2px;"
                                    >
                                        {{ sourceLabel(table) }}: {{ count }}
                                    </el-tag>
                                </template>
                            </el-table-column>
                            <el-table-column label="相似" width="90">
                                <template #default="{ $index }">
                                    <el-tooltip v-if="getSimilarInfo(row, $index)" :content="getSimilarInfo(row, $index)" placement="top">
                                        <el-icon color="#e6a23c" :size="18"><Warning /></el-icon>
                                    </el-tooltip>
                                </template>
                            </el-table-column>
                        </el-table>
                    </div>
                </template>
            </el-table-column>
            <el-table-column prop="materialId" label="材料ID" width="90" />
            <el-table-column label="材料名称" min-width="160">
                <template #default="{ row }">
                    <span>{{ row.materialName }}</span>
                    <el-button type="primary" link size="small" style="margin-left:6px" @click="openRenameDialog(row)">
                        改名
                    </el-button>
                </template>
            </el-table-column>
            <el-table-column prop="supplierName" label="供应商" min-width="140" />
            <el-table-column prop="materialType" label="材料类型" width="120" />
            <el-table-column label="变体数" width="90" sortable :sort-method="(a,b) => a.variantCount - b.variantCount">
                <template #default="{ row }">
                    <el-tag :type="row.variantCount >= 2 ? 'danger' : 'success'">
                        {{ row.variantCount }}
                    </el-tag>
                </template>
            </el-table-column>
            <el-table-column label="相似" width="70">
                <template #default="{ row }">
                    <el-icon v-if="row.similarPairs && row.similarPairs.length" color="#e6a23c" :size="18"><Warning /></el-icon>
                </template>
            </el-table-column>
        </el-table>

        <!-- 分页 -->
        <el-pagination
            class="mt-2"
            @size-change="handleSizeChange"
            @current-change="handlePageChange"
            :current-page="currentPage"
            :page-sizes="[20, 50, 100]"
            :page-size="pageSize"
            layout="total, sizes, prev, pager, next"
            :total="total"
        />

        <!-- 合并变体对话框 -->
        <el-dialog v-model="mergeDialogVisible" :title="`合并变体 - ${mergeTarget.materialName} (${mergeTarget.variantCount} 个变体)`" width="900px" destroy-on-close>
            <el-alert type="warning" :closable="false" style="margin-bottom:16px">
                将勾选的旧变体统一替换为下方填写的标准值。此操作将同时更新 BOM、采购单、投产指示、工艺单等所有相关表。
            </el-alert>

            <el-form label-width="120px" style="margin-bottom:12px">
                <el-form-item label="标准型号">
                    <el-input v-model="mergeForm.newModel" placeholder="合并后的型号值" style="width:320px" />
                </el-form-item>
                <el-form-item label="标准规格">
                    <el-input v-model="mergeForm.newSpec" placeholder="合并后的规格值" style="width:320px" />
                </el-form-item>
                <el-form-item label="标准颜色">
                    <el-input v-model="mergeForm.newColor" placeholder="合并后的颜色值" style="width:320px" />
                </el-form-item>
            </el-form>

            <!-- 搜索与匹配栏 -->
            <div style="display:flex; align-items:center; gap:8px; margin-bottom:10px; flex-wrap:wrap;">
                <el-input v-model="mergeSearch.keyword" placeholder="搜索型号/规格/颜色" clearable style="width:220px" @keyup.enter="fetchMergeVariants(1)" />
                <el-button type="primary" size="small" @click="fetchMergeVariants(1)">搜索</el-button>
                <el-button type="warning" size="small" @click="autoMatchSimilar">
                    <el-icon style="margin-right:4px"><Warning /></el-icon>自动匹配相似
                </el-button>
                <span v-if="mergeSelectedVariants.length" style="color:#409eff; font-size:13px; margin-left:auto;">
                    已选 {{ mergeSelectedVariants.length }} 个变体
                </span>
            </div>

            <el-table :data="mergeVariantList" border size="small" v-loading="mergeVariantLoading"
                @selection-change="handleMergeSelectionChange" ref="mergeTable" row-key="variantKey"
                max-height="360px">
                <el-table-column type="selection" width="55" :reserve-selection="true" />
                <el-table-column prop="materialModel" label="型号" min-width="140">
                    <template #default="{ row }">
                        {{ row.materialModel || '（空）' }}
                    </template>
                </el-table-column>
                <el-table-column prop="materialSpecification" label="规格" min-width="160">
                    <template #default="{ row }">
                        {{ row.materialSpecification || '（空）' }}
                    </template>
                </el-table-column>
                <el-table-column prop="color" label="颜色" min-width="100">
                    <template #default="{ row }">
                        {{ row.color || '（空）' }}
                    </template>
                </el-table-column>
                <el-table-column prop="totalRefs" label="引用数" width="80" />
                <el-table-column label="相似度" width="80" v-if="mergeShowSimilar">
                    <template #default="{ row }">
                        <el-tag v-if="row.similarScore >= 60" type="danger" size="small">{{ row.similarScore }}分</el-tag>
                        <el-tag v-else-if="row.similarScore >= 20" type="warning" size="small">{{ row.similarScore }}分</el-tag>
                    </template>
                </el-table-column>
                <el-table-column label="快捷" width="100">
                    <template #default="{ row }">
                        <el-button type="success" link size="small" @click="setAsStandard(row)">
                            设为标准
                        </el-button>
                    </template>
                </el-table-column>
            </el-table>

            <!-- 合并列表分页 -->
            <el-pagination
                style="margin-top:8px"
                small
                @current-change="handleMergePageChange"
                @size-change="handleMergePageSizeChange"
                :current-page="mergePage.current"
                :page-sizes="[20, 50, 100]"
                :page-size="mergePage.size"
                layout="total, sizes, prev, pager, next"
                :total="mergePage.total"
            />

            <template #footer>
                <el-button @click="mergeDialogVisible = false">取消</el-button>
                <el-button type="primary" :loading="mergeLoading" :disabled="mergeSelectedVariants.length === 0" @click="submitMerge">
                    确认合并 ({{ mergeSelectedVariants.length }} 个变体)
                </el-button>
            </template>
        </el-dialog>

        <!-- 改名对话框 -->
        <el-dialog v-model="renameDialogVisible" title="修改材料名称" width="460px" destroy-on-close>
            <el-form label-width="90px">
                <el-form-item label="当前名称">
                    <span style="font-weight:500">{{ renameTarget.materialName }}</span>
                </el-form-item>
                <el-form-item label="新名称">
                    <el-input v-model="renameForm.newName" placeholder="输入新名称" autofocus />
                </el-form-item>
            </el-form>
            <template #footer>
                <el-button @click="renameDialogVisible = false">取消</el-button>
                <el-button type="primary" :loading="renameLoading" @click="submitRename">确认修改</el-button>
            </template>
        </el-dialog>
    </div>
</template>

<script>
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Warning } from '@element-plus/icons-vue'

const SOURCE_LABELS = {
    bom_item: 'BOM用料',
    production_instruction_item: '投产指示',
    craft_sheet_item: '工艺单',
    purchase_order_item: '采购订单',
    assets_purchase_order_item: '资产采购',
    spu_material: 'SPU材料',
    warehouse_missing_purchase_record_item: '缺料采购',
}

const SOURCE_TAG_TYPES = {
    bom_item: '',
    production_instruction_item: 'success',
    craft_sheet_item: 'warning',
    purchase_order_item: 'danger',
    assets_purchase_order_item: 'info',
    spu_material: '',
    warehouse_missing_purchase_record_item: 'info',
}

// 相似度行的背景色
const SIMILAR_COLORS = [
    'rgba(230, 162, 60, 0.12)',
    'rgba(64, 158, 255, 0.12)',
    'rgba(103, 194, 58, 0.12)',
    'rgba(245, 108, 108, 0.12)',
    'rgba(144, 147, 153, 0.12)',
]

export default {
    name: 'MaterialConsolidation',
    components: { Warning },
    data() {
        return {
            loading: false,
            materialList: [],
            total: 0,
            currentPage: 1,
            pageSize: 50,
            search: {
                materialName: '',
                supplierName: '',
                materialType: '',
                showAll: false,
            },
            // 合并
            mergeDialogVisible: false,
            mergeTarget: { materialId: null, materialName: '', variantCount: 0 },
            mergeForm: { newModel: '', newSpec: '', newColor: '' },
            mergeSelectedVariants: [],
            mergeLoading: false,
            mergeVariantList: [],
            mergeVariantLoading: false,
            mergeShowSimilar: false,
            mergeSearch: { keyword: '' },
            mergePage: { current: 1, size: 50, total: 0 },
            // 改名
            renameDialogVisible: false,
            renameTarget: { materialId: null, materialName: '' },
            renameForm: { newName: '' },
            renameLoading: false,
        }
    },
    mounted() {
        this.fetchVariants()
    },
    methods: {
        async fetchVariants() {
            this.loading = true
            try {
                const res = await axios.get(`${this.$apiBaseUrl}/material/variants`, {
                    params: {
                        page: this.currentPage,
                        pageSize: this.pageSize,
                        materialName: this.search.materialName || undefined,
                        supplierName: this.search.supplierName || undefined,
                        materialType: this.search.materialType || undefined,
                        showAll: this.search.showAll ? 'true' : 'false',
                    },
                })
                this.materialList = res.data.result || []
                this.total = res.data.total || 0
            } catch (e) {
                console.error(e)
                ElMessage.error('查询材料变体失败')
            } finally {
                this.loading = false
            }
        },
        handleSizeChange(val) {
            this.pageSize = val
            this.currentPage = 1
            this.fetchVariants()
        },
        handlePageChange(val) {
            this.currentPage = val
            this.fetchVariants()
        },
        sourceLabel(table) {
            return SOURCE_LABELS[table] || table
        },
        sourceTagType(table) {
            return SOURCE_TAG_TYPES[table] || ''
        },

        // ── 相似度相关 ──
        /** 为变体行返回相似度高亮 class */
        getVariantRowClass(material, index) {
            if (!material.similarPairs || !material.similarPairs.length) return ''
            for (let g = 0; g < material.similarPairs.length; g++) {
                const p = material.similarPairs[g]
                if (p.indexA === index || p.indexB === index) {
                    return `similar-row-${g % SIMILAR_COLORS.length}`
                }
            }
            return ''
        },
        /** 获取该行的相似度提示文本 */
        getSimilarInfo(material, index) {
            if (!material.similarPairs) return ''
            const matches = material.similarPairs.filter(p => p.indexA === index || p.indexB === index)
            if (!matches.length) return ''
            return matches.map(p => {
                const other = p.indexA === index ? p.indexB : p.indexA
                return `与第${other + 1}行相似 (${Math.round(p.similarity * 100)}%)`
            }).join('; ')
        },

        // ── 合并相关 ──
        openMergeDialog(row) {
            this.mergeTarget = {
                materialId: row.materialId,
                materialName: row.materialName,
                variantCount: row.variantCount,
            }
            // 默认用引用最多的作为标准值
            const top = row.variants[0] || {}
            this.mergeForm.newModel = top.materialModel || ''
            this.mergeForm.newSpec = top.materialSpecification || ''
            this.mergeForm.newColor = top.color || ''
            this.mergeSelectedVariants = []
            this.mergeSearch.keyword = ''
            this.mergeShowSimilar = false
            this.mergePage.current = 1
            this.mergeDialogVisible = true
            this.fetchMergeVariants(1)
        },
        async fetchMergeVariants(page) {
            if (page) this.mergePage.current = page
            this.mergeVariantLoading = true
            try {
                const params = {
                    page: this.mergePage.current,
                    pageSize: this.mergePage.size,
                }
                if (this.mergeSearch.keyword) {
                    params.keyword = this.mergeSearch.keyword
                }
                if (this.mergeShowSimilar) {
                    params.matchModel = this.mergeForm.newModel || ''
                    params.matchSpec = this.mergeForm.newSpec || ''
                    params.matchColor = this.mergeForm.newColor || ''
                }
                const res = await axios.get(
                    `${this.$apiBaseUrl}/material/variants/${this.mergeTarget.materialId}`,
                    { params }
                )
                this.mergeVariantList = (res.data.variants || []).map(v => ({
                    ...v,
                    variantKey: `${v.materialModel}|||${v.materialSpecification}|||${v.color}`,
                }))
                this.mergePage.total = res.data.total || 0
            } catch (e) {
                console.error(e)
                ElMessage.error('获取变体列表失败')
            } finally {
                this.mergeVariantLoading = false
            }
        },
        handleMergePageChange(page) {
            this.fetchMergeVariants(page)
        },
        handleMergePageSizeChange(size) {
            this.mergePage.size = size
            this.fetchMergeVariants(1)
        },
        autoMatchSimilar() {
            if (!this.mergeForm.newModel && !this.mergeForm.newSpec && !this.mergeForm.newColor) {
                ElMessage.warning('请先填写标准型号/规格/颜色')
                return
            }
            this.mergeShowSimilar = true
            this.mergePage.current = 1
            this.fetchMergeVariants(1)
        },
        handleMergeSelectionChange(selection) {
            this.mergeSelectedVariants = selection
        },
        setAsStandard(row) {
            this.mergeForm.newModel = row.materialModel || ''
            this.mergeForm.newSpec = row.materialSpecification || ''
            this.mergeForm.newColor = row.color || ''
        },
        async submitMerge() {
            if (this.mergeSelectedVariants.length === 0) {
                ElMessage.warning('请勾选要合并的变体')
                return
            }
            try {
                await ElMessageBox.confirm(
                    `确认将 ${this.mergeSelectedVariants.length} 个变体合并为：\n型号="${this.mergeForm.newModel || '（空）'}"\n规格="${this.mergeForm.newSpec || '（空）'}"\n颜色="${this.mergeForm.newColor || '（空）'}"？\n此操作将修改数据库中的多条记录，请确认无误。`,
                    '确认合并',
                    { confirmButtonText: '确认合并', cancelButtonText: '取消', type: 'warning' }
                )
            } catch {
                return
            }
            this.mergeLoading = true
            try {
                const res = await axios.post(`${this.$apiBaseUrl}/material/merge-variants`, {
                    materialId: this.mergeTarget.materialId,
                    newModel: this.mergeForm.newModel,
                    newSpecification: this.mergeForm.newSpec,
                    newColor: this.mergeForm.newColor,
                    oldVariants: this.mergeSelectedVariants.map((v) => ({
                        materialModel: v.materialModel,
                        materialSpecification: v.materialSpecification,
                        color: v.color,
                    })),
                })
                ElMessage.success(res.data.message || '合并成功')
                this.mergeDialogVisible = false
                this.fetchVariants()
            } catch (e) {
                console.error(e)
                const msg = e.response?.data?.error || '合并失败'
                ElMessage.error(msg)
            } finally {
                this.mergeLoading = false
            }
        },

        // ── 改名相关 ──
        openRenameDialog(row) {
            this.renameTarget = { materialId: row.materialId, materialName: row.materialName }
            this.renameForm.newName = row.materialName
            this.renameDialogVisible = true
        },
        async submitRename() {
            const newName = this.renameForm.newName.trim()
            if (!newName) {
                ElMessage.warning('名称不能为空')
                return
            }
            if (newName === this.renameTarget.materialName) {
                ElMessage.info('名称未变更')
                return
            }
            this.renameLoading = true
            try {
                const res = await axios.post(`${this.$apiBaseUrl}/material/rename`, {
                    materialId: this.renameTarget.materialId,
                    newName,
                })
                ElMessage.success(res.data.message || '修改成功')
                this.renameDialogVisible = false
                this.fetchVariants()
            } catch (e) {
                console.error(e)
                const msg = e.response?.data?.error || '修改失败'
                ElMessage.error(msg)
            } finally {
                this.renameLoading = false
            }
        },
    },
}
</script>

<style scoped>
.material-consolidation {
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
.mt-2 {
    margin-top: 12px;
}
</style>
<style>
/* 相似度行高亮（不能 scoped，因为 el-table 内部渲染） */
.similar-row-0 { background-color: rgba(230, 162, 60, 0.12) !important; }
.similar-row-1 { background-color: rgba(64, 158, 255, 0.12) !important; }
.similar-row-2 { background-color: rgba(103, 194, 58, 0.12) !important; }
.similar-row-3 { background-color: rgba(245, 108, 108, 0.12) !important; }
.similar-row-4 { background-color: rgba(144, 147, 153, 0.12) !important; }
</style>
