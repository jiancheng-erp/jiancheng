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
                <el-form-item v-if="selectedOrderShoe">
                    <el-button type="success" @click="openAddDialog">+ 添加材料</el-button>
                </el-form-item>
                <el-form-item v-if="selectedOrderShoe">
                    <el-button @click="runCheck" :loading="checkLoading">检查匹配</el-button>
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
                <el-table-column label="材料名称 (型号/规格)" min-width="200" show-overflow-tooltip>
                    <template #default="{ row }">
                        <span>{{ row.materialName }}</span>
                        <span v-if="row.groupModel" style="color:#909399; margin-left:4px;">{{ row.groupModel }}</span>
                        <span v-if="row.groupSpec" style="color:#909399; margin-left:4px;">/ {{ row.groupSpec }}</span>
                    </template>
                </el-table-column>
                <el-table-column prop="supplierName" label="供应商" min-width="130" show-overflow-tooltip />
                <el-table-column label="颜色" min-width="180">
                    <template #default="{ row }">
                        <div class="combo-list">
                            <el-tag v-for="(color, idx) in getUniqueColors(row)" :key="idx"
                                size="small" type="info" effect="plain" style="margin: 2px;">
                                {{ color || '—' }}
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
                        <el-tooltip :content="inconsistencyTooltip(row)">
                            <el-icon v-if="hasInconsistency(row)" color="#e6a23c" :size="20">
                                <Warning />
                            </el-icon>
                            <el-icon v-else color="#67c23a" :size="20">
                                <CircleCheck />
                            </el-icon>
                        </el-tooltip>
                    </template>
                </el-table-column>
                <el-table-column label="操作" width="230" fixed="right">
                    <template #default="{ row }">
                        <el-button type="primary" link size="small" @click="openEditDialog(row)">
                            整体替换/修改
                        </el-button>
                        <el-button v-if="hasCraftSheetNotInPi(row)" type="warning" link size="small"
                            :loading="syncLoadingKey === rowGroupKey(row)"
                            @click="syncMaterial(row)">
                            同步
                        </el-button>
                        <el-button v-if="hasBom1Missing(row)" type="warning" link size="small"
                            @click="openBom1SyncDialog(row)">
                            补充BOM
                        </el-button>
                        <el-button v-if="hasPOMissing(row)" type="danger" link size="small"
                            @click="openPOSyncDialog(row)">
                            补充采购
                        </el-button>
                        <el-button v-if="isZipperMaterial(row)" type="info" link size="small"
                            @click="openZipperPairDialog(row)">
                            配对组
                        </el-button>
                        <el-button type="danger" link size="small" @click="openDeleteDialog(row)">
                            删除
                        </el-button>
                    </template>
                </el-table-column>
            </el-table>
        </div>

        <!-- ================= 补充一次BOM对话框 ================= -->
        <el-dialog v-model="bom1SyncDialogVisible"
            :title="`补充一次BOM：${bom1SyncTarget ? [bom1SyncTarget.materialName, bom1SyncTarget.groupModel, bom1SyncTarget.groupSpec].filter(Boolean).join(' / ') : ''}`"
            width="780px" destroy-on-close>
            <el-alert type="info" :closable="false" style="margin-bottom:12px;">
                以下配色在投产指令单/工艺单中存在，但一次BOM中缺失。请填写用量后提交。
            </el-alert>
            <div v-for="r in bom1SyncRows" :key="r.ostId"
                style="border:1px solid #e4e7ed; border-radius:4px; padding:12px; margin-bottom:12px;">
                <div style="font-weight:bold; margin-bottom:8px; color:#303133;">
                    配色：{{ r.colorLabel }}
                </div>
                <!-- 尺码数量表 -->
                <div v-loading="r.sizeInfoLoading" style="margin-bottom:10px;">
                    <template v-if="r.sizeInfo && r.sizeInfo.batches.length">
                        <div style="font-size:12px; color:#606266; margin-bottom:4px;">
                            尺码数量（合计 <strong>{{ r.sizeInfo.grandTotal }}</strong> 双）
                        </div>
                        <el-table :data="r.sizeInfo.batches" border size="small"
                            show-summary :summary-method="(args) => bom1SizeSummary(args, r)">
                            <el-table-column prop="name" label="批次" width="70" fixed />
                            <el-table-column v-for="s in bom1SizeColumns(r)" :key="s" :prop="s" :label="s"
                                width="52" align="center">
                                <template #default="{ row }">
                                    <span :style="row[s] ? '' : 'color:#c0c4cc'">{{ row[s] || 0 }}</span>
                                </template>
                            </el-table-column>
                            <el-table-column prop="total" label="小计" width="60" align="center">
                                <template #default="{ row }"><strong>{{ row.total }}</strong></template>
                            </el-table-column>
                        </el-table>
                    </template>
                    <el-empty v-else-if="r.sizeInfo && !r.sizeInfo.batches.length"
                        description="该配色暂无尺码数量" :image-size="36" />
                </div>
                <el-row :gutter="12">
                    <el-col :span="10">
                        <div style="font-size:12px; color:#606266; margin-bottom:4px;">单位用量</div>
                        <el-input-number v-model="r.unitUsage" :min="0" :precision="5" :step="0.01"
                            style="width:100%;" @change="calcBom1Approval(r)" />
                    </el-col>
                    <el-col :span="14">
                        <div style="font-size:12px; color:#606266; margin-bottom:4px;">
                            核定用量
                            <span v-if="r.sizeInfo" style="color:#909399;">
                                = {{ r.unitUsage }} × {{ r.sizeInfo.grandTotal }}双
                            </span>
                        </div>
                        <el-input-number v-model="r.totalUsage" :min="0" :precision="5" :step="0.1"
                            style="width:100%;" />
                        <el-button v-if="r.sizeInfo" link type="primary" size="small"
                            style="margin-top:2px;" @click="calcBom1Approval(r)">
                            重新计算
                        </el-button>
                    </el-col>
                </el-row>
            </div>
            <template #footer>
                <el-button @click="bom1SyncDialogVisible = false">取消</el-button>
                <el-button type="primary" :loading="bom1SyncLoading" @click="submitBom1Sync">
                    确认补充
                </el-button>
            </template>
        </el-dialog>

        <!-- ================= 补充采购订单对话框 ================= -->
        <el-dialog v-model="poSyncDialogVisible"
            :title="`补充采购订单：${poSyncTarget ? [poSyncTarget.materialName, poSyncTarget.groupModel, poSyncTarget.groupSpec].filter(Boolean).join(' / ') : ''}`"
            width="780px" destroy-on-close>
            <el-alert type="info" :closable="false" style="margin-bottom:12px;">
                以下配色存在一次BOM，但采购订单中缺失。请填写采购用量后提交。
            </el-alert>
            <div v-for="r in poSyncRows" :key="r.ostId"
                style="border:1px solid #e4e7ed; border-radius:4px; padding:12px; margin-bottom:12px;">
                <div style="font-weight:bold; margin-bottom:8px; color:#303133;">
                    配色：{{ r.colorLabel }}
                    <span v-if="r.bomTotalUsage" style="font-weight:normal; font-size:12px; color:#909399; margin-left:8px;">
                        （一次BOM核定用量：{{ r.bomTotalUsage }}）
                    </span>
                </div>
                <!-- 尺码数量表 -->
                <div v-loading="r.sizeInfoLoading" style="margin-bottom:10px;">
                    <template v-if="r.sizeInfo && r.sizeInfo.batches.length">
                        <div style="font-size:12px; color:#606266; margin-bottom:4px;">
                            尺码数量（合计 <strong>{{ r.sizeInfo.grandTotal }}</strong> 双）
                        </div>
                        <el-table :data="r.sizeInfo.batches" border size="small"
                            show-summary :summary-method="(args) => poSizeSummary(args, r)">
                            <el-table-column prop="name" label="批次" width="70" fixed />
                            <el-table-column v-for="s in poSizeColumns(r)" :key="s" :prop="s" :label="s"
                                width="52" align="center">
                                <template #default="{ row }">
                                    <span :style="row[s] ? '' : 'color:#c0c4cc'">{{ row[s] || 0 }}</span>
                                </template>
                            </el-table-column>
                            <el-table-column prop="total" label="小计" width="60" align="center">
                                <template #default="{ row }"><strong>{{ row.total }}</strong></template>
                            </el-table-column>
                        </el-table>
                    </template>
                    <el-empty v-else-if="r.sizeInfo && !r.sizeInfo.batches.length"
                        description="该配色暂无尺码数量" :image-size="36" />
                </div>
                <el-row :gutter="12">
                    <!-- 尺码材料：输入每双用量，自动计算各尺码数量 -->
                    <template v-if="poSyncTarget && poSyncTarget.materialCategory === 1 && r.sizeInfo && r.sizeInfo.grandTotal > 0">
                        <el-col :span="14">
                            <div style="font-size:12px; color:#606266; margin-bottom:4px;">每双用量</div>
                            <el-input-number v-model="r.unitUsage" :min="0" :precision="5" :step="0.001"
                                style="width:160px;" @change="calcPOSizeAmounts(r)" />
                            <el-button v-if="r.bomUnitUsage" link type="primary" size="small"
                                style="margin-left:8px;"
                                @click="r.unitUsage = r.bomUnitUsage; calcPOSizeAmounts(r)">
                                BOM用量
                            </el-button>
                        </el-col>
                        <el-col :span="10">
                            <div style="font-size:12px; color:#606266; margin-bottom:4px;">采购总量（自动计算）</div>
                            <span style="font-size:15px; font-weight:bold; color:#303133;">{{ r.purchaseAmount || 0 }}</span>
                        </el-col>
                    </template>
                    <!-- 非尺码材料：手动输入 -->
                    <template v-else>
                        <el-col :span="24">
                            <div style="font-size:12px; color:#606266; margin-bottom:4px;">采购用量</div>
                            <el-input-number v-model="r.purchaseAmount" :min="0" :precision="5" :step="0.1"
                                style="width:200px;" />
                            <el-button v-if="r.bomTotalUsage" link type="primary" size="small"
                                style="margin-left:8px;" @click="r.purchaseAmount = r.bomTotalUsage">
                                使用BOM核定用量
                            </el-button>
                        </el-col>
                    </template>
                </el-row>
                <!-- 各尺码计算结果 -->
                <div v-if="r.sizeInfo && r.sizeInfo.grandTotal > 0 && r.unitUsage > 0 && r.sizeAmounts && Object.keys(r.sizeAmounts).length"
                    style="margin-top:8px; font-size:12px; color:#606266; background:#f5f7fa; padding:6px 10px; border-radius:4px;">
                    <span v-for="s in poSizeColumns(r)" :key="s" style="margin-right:14px;">
                        {{ s }}码: <strong>{{ r.sizeAmounts[s] || 0 }}</strong>
                    </span>
                </div>
            </div>
            <template #footer>
                <el-button @click="poSyncDialogVisible = false">取消</el-button>
                <el-button type="primary" :loading="poSyncLoading" @click="submitPOSync">
                    确认补充
                </el-button>
            </template>
        </el-dialog>

        <!-- ================= 拉链配对组对话框 ================= -->
        <el-dialog v-model="zipperPairDialogVisible"
            title="拉链 / 拉链头 配对组设置"
            width="860px" destroy-on-close>
            <el-alert type="info" :closable="false" style="margin-bottom:12px">
                为每行拉链/拉头指定配对组编号（1-9）。同一配色下编号相同的拉链与拉头视为一对，每组需同时有拉链和拉链头。
            </el-alert>
            <el-table :data="zipperPairRows" border size="small">
                <el-table-column label="配色" prop="colorLabel" width="100" />
                <el-table-column label="材料名称" prop="materialName" width="110" />
                <el-table-column label="型号" prop="materialModel" width="90" show-overflow-tooltip />
                <el-table-column label="规格" prop="materialSpec" width="90" show-overflow-tooltip />
                <el-table-column label="颜色" prop="color" width="80" show-overflow-tooltip />
                <el-table-column label="配对组" width="130" align="center">
                    <template #default="{ row }">
                        <el-input-number v-model="row.pairId" :min="1" :max="9"
                            controls-position="right" style="width:90px" size="small"
                            :placeholder="row.isZipper ? '拉链' : '拉头'" />
                        <el-button v-if="row.pairId != null" link size="small"
                            style="color:#c0c4cc; margin-left:4px"
                            @click="row.pairId = null">✕</el-button>
                    </template>
                </el-table-column>
            </el-table>
            <!-- 配对平衡提示 -->
            <div v-if="zipperPairWarnings.length" style="margin-top:10px">
                <el-alert v-for="w in zipperPairWarnings" :key="w" :title="w"
                    type="warning" show-icon :closable="false" style="margin-bottom:4px" />
            </div>
            <template #footer>
                <el-button @click="zipperPairDialogVisible = false">取消</el-button>
                <el-button type="primary" :loading="zipperPairLoading" @click="submitZipperPairs">
                    保存
                </el-button>
            </template>
        </el-dialog>

        <!-- ================= 检查匹配对话框 ================= -->
        <el-dialog v-model="checkDialogVisible" title="材料链路匹配检查" width="960px" destroy-on-close>
            <div v-if="checkLoading" style="text-align:center; padding:40px;">
                <el-icon class="is-loading" :size="32"><Loading /></el-icon>
                <div style="margin-top:8px; color:#909399;">正在检查中...</div>
            </div>
            <template v-else-if="checkData">
                <!-- 概要卡片 -->
                <el-row :gutter="12" style="margin-bottom:16px;">
                    <el-col :span="8">
                        <div class="preview-card" :class="checkData.totalIssues === 0 ? 'success' : 'danger'">
                            <div class="num">{{ checkData.totalIssues }}</div>
                            <div class="lbl">发现问题</div>
                        </div>
                    </el-col>
                    <el-col :span="8">
                        <div class="preview-card warning">
                            <div class="num">{{ checkData.autoFixableCount }}</div>
                            <div class="lbl">可自动修复</div>
                        </div>
                    </el-col>
                    <el-col :span="8">
                        <div class="preview-card primary">
                            <div class="num">{{ checkData.totalIssues - checkData.autoFixableCount }}</div>
                            <div class="lbl">需手动处理</div>
                        </div>
                    </el-col>
                </el-row>

                <el-alert v-if="checkData.totalIssues === 0" type="success" :closable="false" show-icon>
                    所有材料链路均对齐，无需处理。
                </el-alert>
                <template v-else>
                    <div style="margin-bottom:8px; display:flex; gap:8px; align-items:center;">
                        <span style="font-size:13px; color:#606266;">共 {{ checkData.issues.length }} 个问题项</span>
                        <el-tag type="warning" size="small">{{ checkData.autoFixableCount }} 可自动修复</el-tag>
                        <el-tag type="danger" size="small">{{ checkData.totalIssues - checkData.autoFixableCount }} 需手动处理</el-tag>
                    </div>
                    <el-table :data="checkData.issues" border size="small" max-height="420px">
                        <el-table-column label="文档类型" width="100">
                            <template #default="{ row }">
                                <el-tag :type="docTagType(row.docType)" size="small">{{ row.docLabel }}</el-tag>
                            </template>
                        </el-table-column>
                        <el-table-column label="材料名称" prop="materialName" min-width="140" show-overflow-tooltip />
                        <el-table-column label="配色" width="130">
                            <template #default="{ row }">
                                {{ colorLabelOf(row.orderShoeTypeId) }}
                            </template>
                        </el-table-column>
                        <el-table-column label="问题描述" prop="description" min-width="240" show-overflow-tooltip>
                            <template #default="{ row }">
                                <el-tag size="small" :type="issueTypeTag(row.issueType)" style="margin-right:4px;">
                                    {{ issueTypeLabel(row.issueType) }}
                                </el-tag>
                                {{ row.description }}
                            </template>
                        </el-table-column>
                        <el-table-column label="修复状态" width="120" align="center">
                            <template #default="{ row }">
                                <el-tooltip v-if="!row.canAutoFix"
                                    :content="row.candidateCount === 0 ? '无匹配候选PI项，请手动处理' : `发现${row.candidateCount}个候选，无法唯一确定`">
                                    <el-tag type="danger" size="small">
                                        {{ row.candidateCount === 0 ? '无候选项' : '多个候选' }}
                                    </el-tag>
                                </el-tooltip>
                                <el-tag v-else type="warning" size="small">可自动修复</el-tag>
                            </template>
                        </el-table-column>
                    </el-table>
                </template>
            </template>
            <el-empty v-else description="点击『重新检查』开始" :image-size="60" />

            <template #footer>
                <el-button @click="runCheck" :loading="checkLoading">重新检查</el-button>
                <el-button v-if="checkData && checkData.autoFixableCount > 0"
                    type="warning" :loading="fixLoading" @click="applyAutoFix">
                    自动修复 ({{ checkData.autoFixableCount }} 项)
                </el-button>
                <el-button @click="checkDialogVisible = false">关闭</el-button>
            </template>
        </el-dialog>

        <!-- ================= 删除确认对话框 ================= -->
        <el-dialog v-model="deleteDialogVisible" title="删除材料" width="600px" destroy-on-close>
            <el-alert type="error" :closable="false" show-icon style="margin-bottom:14px;">
                将从所有相关文档（投产指令单、工艺单、BOM、采购订单）中删除该材料的记录，此操作不可恢复！
            </el-alert>
            <el-descriptions :column="2" border v-if="deleteTarget">
                <el-descriptions-item label="材料名称">{{ deleteTarget.materialName }}</el-descriptions-item>
                <el-descriptions-item label="材料ID">{{ deleteTarget.materialId }}</el-descriptions-item>
                <el-descriptions-item label="供应商">{{ deleteTarget.supplierName || '-' }}</el-descriptions-item>
                <el-descriptions-item label="覆盖配色">{{ deleteTarget.colorPresence?.length || 0 }} 个</el-descriptions-item>
                <el-descriptions-item label="文档记录数" :span="2">{{ deleteTarget.items?.length || 0 }} 条</el-descriptions-item>
            </el-descriptions>
            <div style="margin-top:14px;">
                <span style="font-size:13px; margin-right:8px;">删除范围：</span>
                <el-radio-group v-model="deleteForm.scope">
                    <el-radio value="shoe">整鞋款（全部配色）</el-radio>
                    <el-radio value="color" :disabled="selectedColorTypeId === 0">
                        仅当前配色 ({{ currentColorLabel }})
                    </el-radio>
                </el-radio-group>
            </div>
            <template #footer>
                <el-button @click="deleteDialogVisible = false">取消</el-button>
                <el-button type="danger" :loading="deleteLoading" @click="submitDelete">确认删除</el-button>
            </template>
        </el-dialog>

        <!-- ================= 添加材料对话框 ================= -->
        <el-dialog v-model="addDialogVisible" title="添加材料到鞋款文档" width="700px" destroy-on-close>
            <el-alert type="info" :closable="false" show-icon style="margin-bottom:12px;">
                将同时写入投产指令单 (PI)、一次BOM 和采购分单（若已存在对应供应商的分单）。
            </el-alert>
            <el-form :model="addForm" label-width="100px">
                <el-form-item label="配色" required>
                    <el-select v-model="addForm.orderShoeTypeId" placeholder="选择配色（必选）" style="width:240px;"
                        @change="(val) => fetchSizeInfo(val)">
                        <el-option v-for="ct in colorTypes" :key="ct.orderShoeTypeId"
                            :value="ct.orderShoeTypeId"
                            :label="ct.customerColorName ? ct.colorName + '(' + ct.customerColorName + ')' : ct.colorName" />
                    </el-select>
                </el-form-item>

                <!-- 尺码数量表 -->
                <div v-if="addForm.orderShoeTypeId" style="margin-bottom:16px;">
                    <div style="font-size:13px; color:#606266; margin-bottom:6px; font-weight:bold;">
                        该配色尺码数量
                        <span v-if="sizeInfo" style="color:#409eff; font-weight:normal; margin-left:8px;">
                            合计 {{ sizeInfo.grandTotal }} 双
                        </span>
                    </div>
                    <div v-loading="sizeInfoLoading">
                        <el-table v-if="sizeInfo && sizeInfo.batches.length" :data="sizeInfo.batches"
                            border size="small" show-summary :summary-method="sizeSummary">
                            <el-table-column prop="name" label="批次" width="80" fixed />
                            <el-table-column v-for="s in sizeColumns" :key="s" :prop="s" :label="s"
                                width="52" align="center">
                                <template #default="{ row }">
                                    <span :style="row[s] ? '' : 'color:#c0c4cc'">{{ row[s] || 0 }}</span>
                                </template>
                            </el-table-column>
                            <el-table-column prop="total" label="小计" width="62" align="center">
                                <template #default="{ row }">
                                    <strong>{{ row.total }}</strong>
                                </template>
                            </el-table-column>
                        </el-table>
                        <el-empty v-else-if="sizeInfo && !sizeInfo.batches.length"
                            description="该配色暂无尺码数量" :image-size="40" />
                    </div>
                </div>
                <el-form-item label="材料" required>
                    <el-input v-model="addMaterialSearchKw" placeholder="搜索材料名称" style="width:280px;"
                        @keyup.enter="searchAddMaterials" clearable>
                        <template #append>
                            <el-button @click="searchAddMaterials" :loading="addMaterialSearchLoading">搜索</el-button>
                        </template>
                    </el-input>
                    <el-select v-if="addMaterialResults.length" v-model="addForm.materialId"
                        placeholder="选择材料" style="width:100%; margin-top:8px;" filterable>
                        <el-option v-for="mat in addMaterialResults" :key="mat.materialId"
                            :label="`${mat.materialName} | ${mat.supplierName || '无供应商'} (ID:${mat.materialId})`"
                            :value="mat.materialId">
                            <span style="float:left">{{ mat.materialName }}</span>
                            <span style="float:right; color:#8492a6; font-size:12px;">
                                {{ mat.supplierName || '无供应商' }} | ID:{{ mat.materialId }}
                            </span>
                        </el-option>
                    </el-select>
                </el-form-item>
                <el-row :gutter="12">
                    <el-col :span="8">
                        <el-form-item label="型号">
                            <el-input v-model="addForm.materialModel" placeholder="（可选）" clearable />
                        </el-form-item>
                    </el-col>
                    <el-col :span="8">
                        <el-form-item label="规格">
                            <el-input v-model="addForm.materialSpecification" placeholder="（可选）" clearable />
                        </el-form-item>
                    </el-col>
                    <el-col :span="8">
                        <el-form-item label="颜色">
                            <el-input v-model="addForm.color" placeholder="（可选）" clearable />
                        </el-form-item>
                    </el-col>
                </el-row>
                <el-row :gutter="12">
                    <el-col :span="12">
                        <el-form-item label="单位用量" required>
                            <el-input-number v-model="addForm.unitUsage" :min="0" :precision="5"
                                style="width:100%;" placeholder="每双用量" />
                        </el-form-item>
                    </el-col>
                    <el-col :span="12">
                        <el-form-item label="核定用量" required>
                            <el-input-number v-model="addForm.approvalAmount" :min="0" :precision="5"
                                style="width:100%;" placeholder="采购核定数量" />
                            <div style="font-size:11px; color:#909399; margin-top:2px;">
                                <template v-if="sizeInfo">
                                    = {{ addForm.unitUsage }} × {{ sizeInfo.grandTotal }}双
                                    <el-button link size="small" type="primary" @click="calcApproval">重新计算</el-button>
                                </template>
                                <span v-else style="color:#c0c4cc">（先选配色后可自动计算）</span>
                            </div>
                        </el-form-item>
                    </el-col>
                </el-row>
                <el-form-item label="备注">
                    <el-input v-model="addForm.remark" placeholder="（可选）" clearable />
                </el-form-item>
            </el-form>
            <template #footer>
                <el-button @click="addDialogVisible = false">取消</el-button>
                <el-button type="primary" :loading="addLoading" :disabled="!addForm.materialId || !addForm.orderShoeTypeId"
                    @click="submitAdd">确认添加</el-button>
            </template>
        </el-dialog>

        <!-- ================= 编辑对话框 ================= -->
        <el-dialog v-model="editDialogVisible" :title="editDialogTitle"
            width="900px" destroy-on-close top="6vh">

            <!-- 原分布状况 -->
            <el-collapse style="margin-bottom:4px;">
                <el-collapse-item>
                    <template #title>
                        <span style="font-size:13px; color:#606266;">
                            查看原分布状况
                            <el-tag size="small" type="info" style="margin-left:6px;">
                                {{ editTarget.items?.length || 0 }} 条记录 /
                                {{ editTarget.colorPresence?.length || 0 }} 个配色
                            </el-tag>
                        </span>
                    </template>
                    <el-table :data="editTarget.items || []" border size="small"
                        max-height="280px" style="width:100%; margin-top:4px;">
                        <el-table-column label="文档" width="110">
                            <template #default="{ row }">
                                <el-tag :type="docTagType(row.docType)" size="small">
                                    {{ row.docLabel }}
                                </el-tag>
                            </template>
                        </el-table-column>
                        <el-table-column label="配色" width="130">
                            <template #default="{ row }">
                                {{ colorLabelOf(row.orderShoeTypeId) }}
                            </template>
                        </el-table-column>
                        <el-table-column label="型号" prop="materialModel" min-width="110">
                            <template #default="{ row }">
                                <span :style="row.materialModel ? '' : 'color:#c0c4cc'">
                                    {{ row.materialModel || '（空）' }}
                                </span>
                            </template>
                        </el-table-column>
                        <el-table-column label="规格" prop="materialSpecification" min-width="140">
                            <template #default="{ row }">
                                <span :style="row.materialSpecification ? '' : 'color:#c0c4cc'">
                                    {{ row.materialSpecification || '（空）' }}
                                </span>
                            </template>
                        </el-table-column>
                        <el-table-column label="颜色" prop="color" min-width="100">
                            <template #default="{ row }">
                                <span :style="row.color ? '' : 'color:#c0c4cc'">
                                    {{ row.color || '（空）' }}
                                </span>
                            </template>
                        </el-table-column>
                    </el-table>
                </el-collapse-item>
            </el-collapse>

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
import { Warning, CircleCheck, Search, Loading } from '@element-plus/icons-vue'

export default {
    name: 'MaterialBatchEdit',
    components: { Warning, CircleCheck, Search, Loading },
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

            // 删除
            deleteDialogVisible: false,
            deleteTarget: null,
            deleteForm: { scope: 'shoe' },
            deleteLoading: false,

            // 添加
            addDialogVisible: false,
            addForm: {
                orderShoeTypeId: null,
                materialId: null,
                materialModel: '',
                materialSpecification: '',
                color: '',
                unitUsage: 0,
                approvalAmount: 0,
                remark: '',
            },
            addLoading: false,
            addMaterialSearchKw: '',
            addMaterialResults: [],
            addMaterialSearchLoading: false,

            // 尺码数量表
            sizeInfo: null,
            sizeInfoLoading: false,

            // 检查匹配
            checkDialogVisible: false,
            checkLoading: false,
            checkData: null,
            fixLoading: false,

            // 同步不一致材料
            syncLoadingKey: null,

            // 补充一次BOM对话框
            bom1SyncDialogVisible: false,
            bom1SyncTarget: null,
            bom1SyncRows: [],   // [{ ostId, colorLabel, unitUsage, totalUsage, sizeInfo, sizeInfoLoading, grandTotal }]
            bom1SyncLoading: false,

            // 补充采购订单对话框
            poSyncDialogVisible: false,
            poSyncTarget: null,
            poSyncRows: [],     // [{ ostId, colorLabel, purchaseAmount, sizeInfo, sizeInfoLoading, grandTotal }]
            poSyncLoading: false,

            // 配对组对话框
            zipperPairDialogVisible: false,
            zipperPairTarget: null,   // row
            zipperPairRows: [],       // [{ docType, itemId, colorLabel, materialName, docLabel, pairId }]
            zipperPairLoading: false,
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
            const parts = [this.editTarget.materialName]
            if (this.editTarget.groupModel) parts.push(this.editTarget.groupModel)
            if (this.editTarget.groupSpec) parts.push(this.editTarget.groupSpec)
            return `同步修改材料：${parts.join(' / ')} (ID: ${this.editTarget.materialId})`
        },
        filteredGroups() {
            const kw = this.filterText.trim().toLowerCase()
            return this.materialGroups.filter(g => {
                if (this.onlyInconsistent && !this.hasInconsistency(g)) return false
                if (!kw) return true
                const hay = [
                    g.materialName, g.supplierName,
                    g.groupModel, g.groupSpec,
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

            // 取旧值：型号/规格 从 group key 取（确定唯一），颜色从 items 合并
            const collectVals = (key) => {
                const set = new Set(items.map(i => i[key] || '').filter(v => v !== ''))
                return [...set].join(' / ') || '（空）'
            }
            const oldModel = this.editTarget.groupModel || '（空）'
            const oldSpec = this.editTarget.groupSpec || '（空）'
            const oldColor = collectVals('color')
            const newModel = this.editForm.newModel !== '' ? this.editForm.newModel : oldModel
            const newSpec = this.editForm.newSpecification !== '' ? this.editForm.newSpecification : oldSpec
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
        sizeColumns() {
            if (!this.sizeInfo) return []
            return Object.keys(this.sizeInfo.totals).filter(s => this.sizeInfo.totals[s] > 0)
        },
        issueTypeLabel() {
            return (t) => ({
                missing_link: '缺少链接',
                broken_link: '链接失效',
                wrong_material: '材料不匹配',
                missing_bom: '缺少BOM项',
                attr_mismatch: '属性不一致',
                extra_craft_item: '工艺单多余项',
            })[t] || t
        },
        issueTypeTag() {
            return (t) => ({
                missing_link: 'warning',
                broken_link: 'danger',
                wrong_material: 'danger',
                missing_bom: 'danger',
                attr_mismatch: 'warning',
                extra_craft_item: 'warning',
            })[t] || ''
        },
        // 全局判断：该鸞款是否已有任意配色的一次/二次BOM/采购订单
        globalBom1Exists() {
            return this.materialGroups.some(g =>
                g.items.some(i => i.docType === 'bom_item' && i.bomType === 0)
            )
        },
        globalBom2Exists() {
            return this.materialGroups.some(g =>
                g.items.some(i => i.docType === 'bom_item' && i.bomType === 1)
            )
        },
        globalPoExists() {
            return this.materialGroups.some(g =>
                g.items.some(i => i.docType === 'purchase_order_item')
            )
        },
        // 配对组对话框：检测同配色内拉链/拉头是否成对（不按文件计数，只看类型）
        zipperPairWarnings() {
            const byGroup = {}
            for (const r of this.zipperPairRows) {
                if (r.pairId == null) continue
                const key = `${r._ostId}|${r.pairId}`
                if (!byGroup[key]) byGroup[key] = { hasZipper: false, hasPull: false, label: r.colorLabel, pid: r.pairId }
                const isHead = (r.materialName || '').includes('拉链头')
                if (isHead) byGroup[key].hasPull = true
                else byGroup[key].hasZipper = true
            }
            return Object.values(byGroup)
                .filter(v => !v.hasZipper || !v.hasPull)
                .map(v => {
                    const missing = !v.hasZipper ? '缺少拉链' : '缺少拉链头'
                    return `${v.label} 配对组${v.pid}：${missing}`
                })
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
        // 添加对话框：配色切换时加载尺码表
        'addForm.orderShoeTypeId'(val) {
            if (val && this.addDialogVisible) this.fetchSizeInfo(val)
        },
        // 单位用量变化时自动重算核定用量
        'addForm.unitUsage'() { this.calcApproval() },
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
        getUniqueColors(row) {
            const seen = new Set()
            for (const it of row.items) {
                seen.add(it.color || '')
            }
            return [...seen].sort()
        },
        getDocCounts(row) {
            const counts = {}
            for (const it of row.items) {
                if (!counts[it.docType]) counts[it.docType] = { type: it.docType, label: it.docLabel, count: 0 }
                counts[it.docType].count++
            }
            return Object.values(counts)
        },
        getInconsistencyReasons(row) {
            const reasons = []
            const piOstIds = new Set(
                row.items.filter(i => i.docType === 'production_instruction_item').map(i => i.orderShoeTypeId)
            )
            const csOstIds = new Set(
                row.items.filter(i => i.docType === 'craft_sheet_item').map(i => i.orderShoeTypeId)
            )
            // 工艺单/投产指令单合并作为「上游」来源
            const sourceOstIds = new Set([...piOstIds, ...csOstIds])

            // 1. 工艺单有配色但投产指令单缺失
            const csNotInPi = [...csOstIds].filter(id => !piOstIds.has(id))
            if (csNotInPi.length)
                reasons.push(`工艺单有但投产指令单缺失：${csNotInPi.map(id => this.colorLabelOf(id)).join('、')}`)

            // 1b. 投产指令单有配色但工艺单缺失
            const piNotInCs = [...piOstIds].filter(id => !csOstIds.has(id))
            if (piNotInCs.length)
                reasons.push(`投产指令单有但工艺单缺失：${piNotInCs.map(id => this.colorLabelOf(id)).join('、')}`)

            // 2. 投产指令单有但一次BOM缺失（仅当该鞋款已产生一次BOM时检查）
            const bom1OstIds = new Set(
                row.items.filter(i => i.docType === 'bom_item' && i.bomType === 0 && i.orderShoeTypeId)
                    .map(i => i.orderShoeTypeId)
            )
            if (this.globalBom1Exists) {
                const missing = [...sourceOstIds].filter(id => !bom1OstIds.has(id))
                if (missing.length)
                    reasons.push(`一次BOM缺失：${missing.map(id => this.colorLabelOf(id)).join('、')}`)
            }

            // 3. 投产指令单有但二次BOM缺失（仅当该鞋款已产生二次BOM时检查）
            const bom2OstIds = new Set(
                row.items.filter(i => i.docType === 'bom_item' && i.bomType === 1 && i.orderShoeTypeId)
                    .map(i => i.orderShoeTypeId)
            )
            if (this.globalBom2Exists) {
                const missing = [...sourceOstIds].filter(id => !bom2OstIds.has(id))
                if (missing.length)
                    reasons.push(`二次BOM缺失：${missing.map(id => this.colorLabelOf(id)).join('、')}`)
            }

            // 4. 投产指令单有但采购订单缺失（仅当该鞋款已产生采购订单时检查）
            const poOstIds = new Set(
                row.items.filter(i => i.docType === 'purchase_order_item' && i.orderShoeTypeId)
                    .map(i => i.orderShoeTypeId)
            )
            if (this.globalPoExists) {
                const missing = [...sourceOstIds].filter(id => !poOstIds.has(id))
                if (missing.length)
                    reasons.push(`采购订单缺失：${missing.map(id => this.colorLabelOf(id)).join('、')}`)
            }

            return reasons
        },
        hasInconsistency(row) {
            return this.getInconsistencyReasons(row).length > 0
        },
        // 检查「工艺单」与「投产指令单」之间任意方向的互相缺失 —— 用于控制同步按钮
        hasCraftSheetNotInPi(row) {
            const piOstIds = new Set(
                row.items.filter(i => i.docType === 'production_instruction_item').map(i => i.orderShoeTypeId)
            )
            const csOstIds = new Set(
                row.items.filter(i => i.docType === 'craft_sheet_item').map(i => i.orderShoeTypeId)
            )
            if (piOstIds.size > 0 && [...piOstIds].some(id => !csOstIds.has(id))) return true
            if (csOstIds.size > 0 && [...csOstIds].some(id => !piOstIds.has(id))) return true
            return false
        },
        // 检查「一次BOM缺失」—— 用于控制补充BOM按钮
        hasBom1Missing(row) {
            if (!this.globalBom1Exists) return false
            const piOstIds = new Set(
                row.items.filter(i => i.docType === 'production_instruction_item').map(i => i.orderShoeTypeId)
            )
            const csOstIds = new Set(
                row.items.filter(i => i.docType === 'craft_sheet_item').map(i => i.orderShoeTypeId)
            )
            const sourceOstIds = new Set([...piOstIds, ...csOstIds])
            const bom1OstIds = new Set(
                row.items.filter(i => i.docType === 'bom_item' && i.bomType === 0).map(i => i.orderShoeTypeId)
            )
            return [...sourceOstIds].some(id => !bom1OstIds.has(id))
        },
        // 检查「采购订单缺失」—— 用于控制补充采购按钮
        hasPOMissing(row) {
            if (!this.globalPoExists) return false
            const piOstIds = new Set(
                row.items.filter(i => i.docType === 'production_instruction_item').map(i => i.orderShoeTypeId)
            )
            const csOstIds = new Set(
                row.items.filter(i => i.docType === 'craft_sheet_item').map(i => i.orderShoeTypeId)
            )
            const sourceOstIds = new Set([...piOstIds, ...csOstIds])
            const poOstIds = new Set(
                row.items.filter(i => i.docType === 'purchase_order_item').map(i => i.orderShoeTypeId)
            )
            return [...sourceOstIds].some(id => !poOstIds.has(id))
        },
        inconsistencyTooltip(row) {
            const reasons = this.getInconsistencyReasons(row)
            return reasons.length ? reasons.join('；') : '一致'
        },
        docTagType(docType) {
            return ({
                production_instruction_item: 'success',
                craft_sheet_item: 'warning',
                bom_item: '',
                purchase_order_item: 'danger',
            })[docType] || ''
        },
        // 判断该材料组是否包含拉链或拉链头
        isZipperMaterial(row) {
            const name = row.materialName || ''
            return name.includes('拉链头') || (name.includes('拉链') && !name.includes('拉链头'))
        },

        // ===== 配对组 =====
        openZipperPairDialog(row) {
            // 收集所有拉链/拉链头材料行，按 (配色+材料名+型号+规格+颜色) 合并为一行
            const allZipperRows = this.materialGroups.filter(r => this.isZipperMaterial(r))
            const docTypes = new Set(['production_instruction_item', 'craft_sheet_item', 'bom_item'])
            const merged = {}
            for (const matRow of allZipperRows) {
                for (const it of matRow.items) {
                    if (!docTypes.has(it.docType)) continue
                    const name = it.materialName || matRow.materialName || ''
                    const key = `${it.orderShoeTypeId}|${name}|${it.materialModel || ''}|${it.materialSpecification || ''}|${it.color || ''}`
                    if (!merged[key]) {
                        merged[key] = {
                            colorLabel: this.colorLabelOf(it.orderShoeTypeId),
                            materialName: name,
                            materialModel: it.materialModel || '',
                            materialSpec: it.materialSpecification || '',
                            color: it.color || '',
                            isZipper: name.includes('拉链') && !name.includes('拉链头'),
                            pairId: it.zipperPairId != null ? Number(it.zipperPairId) : null,
                            _ostId: it.orderShoeTypeId,
                            _docItems: [],
                        }
                    }
                    merged[key]._docItems.push({ docType: it.docType, itemId: it.itemId })
                    // 若任意子项有配对编号则用它（优先非空）
                    if (merged[key].pairId == null && it.zipperPairId != null) {
                        merged[key].pairId = Number(it.zipperPairId)
                    }
                }
            }
            const rows = Object.values(merged)
                .sort((a, b) => (a._ostId - b._ostId) || a.materialName.localeCompare(b.materialName))
            this.zipperPairRows = rows
            this.zipperPairTarget = row
            this.zipperPairDialogVisible = true
        },
        async submitZipperPairs() {
            const items = this.zipperPairRows.flatMap(r =>
                r._docItems.map(d => ({
                    docType: d.docType,
                    itemId: d.itemId,
                    zipperPairId: r.pairId != null ? Number(r.pairId) : null,
                }))
            )
            this.zipperPairLoading = true
            try {
                const res = await axios.post(`${this.$apiBaseUrl}/material/set-zipper-pair-ids`, { items })
                ElMessage.success(res.data.message || '保存成功')
                this.zipperPairDialogVisible = false
                this.fetchMaterials()
            } catch (e) {
                ElMessage.error(e.response?.data?.error || '保存失败')
            } finally {
                this.zipperPairLoading = false
            }
        },

        colorLabelOf(ostId) {
            if (!ostId) return '-'
            const ct = this.colorTypes.find(c => c.orderShoeTypeId === ostId)
            if (!ct) return `#${ostId}`
            return ct.customerColorName ? `${ct.colorName}(${ct.customerColorName})` : ct.colorName
        },

        // ===== 检查匹配 =====
        async runCheck() {
            if (!this.selectedOrderShoe) { ElMessage.warning('请先选择订单-鞋款'); return }
            this.checkDialogVisible = true
            this.checkLoading = true
            this.checkData = null
            try {
                const res = await axios.get(`${this.$apiBaseUrl}/material/check-material-links`, {
                    params: { orderShoeId: this.selectedOrderShoe.orderShoeId },
                })
                this.checkData = res.data
            } catch (e) {
                console.error(e)
                ElMessage.error(e.response?.data?.error || '检查失败')
            } finally { this.checkLoading = false }
        },
        async applyAutoFix() {
            const fixes = (this.checkData?.issues || [])
                .filter(i => i.canAutoFix)
                .map(i => ({ docType: i.docType, itemId: i.itemId, newLinkId: i.suggestedLinkId }))
            if (!fixes.length) { ElMessage.info('无可自动修复的项'); return }
            this.fixLoading = true
            try {
                const res = await axios.post(`${this.$apiBaseUrl}/material/fix-material-links`, { fixes })
                ElMessage.success(res.data.message || '修复成功')
                await this.runCheck()
                this.fetchMaterials()
            } catch (e) {
                console.error(e)
                ElMessage.error(e.response?.data?.error || '修复失败')
            } finally { this.fixLoading = false }
        },

        // ===== 同步不一致材料 =====
        rowGroupKey(row) {
            return `${row.materialId}|${row.groupModel || ''}|${row.groupSpec || ''}`
        },
        async syncMaterial(row) {
            // 计算两个方向的缺失信息（供确认弹框展示）
            const piOstIds = new Set(
                row.items.filter(i => i.docType === 'production_instruction_item').map(i => i.orderShoeTypeId)
            )
            const csOstIds = new Set(
                row.items.filter(i => i.docType === 'craft_sheet_item').map(i => i.orderShoeTypeId)
            )
            const csNotInPi = [...csOstIds].filter(id => !piOstIds.has(id))
            const piNotInCs = [...piOstIds].filter(id => !csOstIds.has(id))
            const matLabel = [row.materialName, row.groupModel, row.groupSpec].filter(Boolean).join(' / ')

            let msgLines = []
            if (csNotInPi.length) {
                const names = csNotInPi.map(id => this.colorLabelOf(id)).join('、')
                msgLines.push(`工艺单有但投产指令单缺失：${names}（将自动创建 PI 项、关联工艺单项、关联或创建 BOM 项）`)
            }
            if (piNotInCs.length) {
                const names = piNotInCs.map(id => this.colorLabelOf(id)).join('、')
                msgLines.push(`投产指令单有但工艺单缺失：${names}（将自动创建工艺单项）`)
            }

            try {
                await ElMessageBox.confirm(
                    `材料「${matLabel}」存在以下不一致：\n${msgLines.join('\n')}\n\n点击同步将自动修复上述问题。`,
                    '同步不一致材料',
                    { confirmButtonText: '确认同步', cancelButtonText: '取消', type: 'warning' }
                )
            } catch { return }

            const key = this.rowGroupKey(row)
            this.syncLoadingKey = key
            try {
                const res = await axios.post(`${this.$apiBaseUrl}/material/sync-inconsistent-material`, {
                    orderShoeId: this.selectedOrderShoe.orderShoeId,
                    materialId: row.materialId,
                    groupModel: row.groupModel ?? null,
                    groupSpec: row.groupSpec ?? null,
                })
                ElMessage.success(res.data.message || '同步成功')
                this.fetchMaterials()
            } catch (e) {
                console.error(e)
                ElMessage.error(e.response?.data?.error || '同步失败')
            } finally {
                if (this.syncLoadingKey === key) this.syncLoadingKey = null
            }
        },

        // ===== 补充一次BOM =====
        openBom1SyncDialog(row) {
            const piOstIds = new Set(
                row.items.filter(i => i.docType === 'production_instruction_item').map(i => i.orderShoeTypeId)
            )
            const csOstIds = new Set(
                row.items.filter(i => i.docType === 'craft_sheet_item').map(i => i.orderShoeTypeId)
            )
            const sourceOstIds = new Set([...piOstIds, ...csOstIds])
            const bom1OstIds = new Set(
                row.items.filter(i => i.docType === 'bom_item' && i.bomType === 0).map(i => i.orderShoeTypeId)
            )
            const missingOstIds = [...sourceOstIds].filter(id => !bom1OstIds.has(id))

            this.bom1SyncRows = missingOstIds.map(ostId => {
                const csItem = row.items.find(i => i.docType === 'craft_sheet_item' && i.orderShoeTypeId === ostId)
                return {
                    ostId,
                    colorLabel: this.colorLabelOf(ostId),
                    unitUsage: csItem?.unitUsage ?? 0,
                    totalUsage: csItem?.totalUsage ?? 0,
                    sizeInfo: null,
                    sizeInfoLoading: false,
                }
            })
            this.bom1SyncTarget = { ...row }
            this.bom1SyncDialogVisible = true
            // 异步加载每个配色的尺码表
            this.bom1SyncRows.forEach(r => this.loadBom1SizeInfo(r))
        },
        async loadBom1SizeInfo(r) {
            r.sizeInfoLoading = true
            try {
                const res = await axios.get(`${this.$apiBaseUrl}/material/ordershoetype-batch-info`, {
                    params: { orderShoeTypeId: r.ostId },
                })
                r.sizeInfo = res.data
                this.calcBom1Approval(r)
            } catch (e) { console.error(e) }
            finally { r.sizeInfoLoading = false }
        },
        calcBom1Approval(r) {
            if (!r.sizeInfo) return
            const total = r.sizeInfo.grandTotal || 0
            r.totalUsage = parseFloat(((r.unitUsage || 0) * total).toFixed(5))
        },
        bom1SizeColumns(r) {
            if (!r.sizeInfo) return []
            return Object.keys(r.sizeInfo.totals).filter(s => r.sizeInfo.totals[s] > 0)
        },
        bom1SizeSummary({ columns }, r) {
            const t = r.sizeInfo?.totals || {}
            const grand = r.sizeInfo?.grandTotal || 0
            return columns.map((col, i) => {
                if (i === 0) return '合计'
                if (col.property === 'total') return grand
                return t[col.property] || ''
            })
        },
        async submitBom1Sync() {
            const invalid = this.bom1SyncRows.filter(r => r.unitUsage == null || r.unitUsage === '')
            if (invalid.length) { ElMessage.warning('请填写所有配色的单位用量'); return }
            this.bom1SyncLoading = true
            try {
                const res = await axios.post(`${this.$apiBaseUrl}/material/create-missing-bom-items`, {
                    orderShoeId: this.selectedOrderShoe.orderShoeId,
                    materialId: this.bom1SyncTarget.materialId,
                    groupModel: this.bom1SyncTarget.groupModel ?? null,
                    groupSpec: this.bom1SyncTarget.groupSpec ?? null,
                    items: this.bom1SyncRows.map(r => ({
                        ostId: r.ostId,
                        unitUsage: r.unitUsage,
                        totalUsage: r.totalUsage,
                    })),
                })
                ElMessage.success(res.data.message || '补充成功')
                this.bom1SyncDialogVisible = false
                this.fetchMaterials()
            } catch (e) {
                console.error(e)
                ElMessage.error(e.response?.data?.error || '补充失败')
            } finally { this.bom1SyncLoading = false }
        },

        // ===== 补充采购订单 =====
        openPOSyncDialog(row) {
            const piOstIds = new Set(
                row.items.filter(i => i.docType === 'production_instruction_item').map(i => i.orderShoeTypeId)
            )
            const csOstIds = new Set(
                row.items.filter(i => i.docType === 'craft_sheet_item').map(i => i.orderShoeTypeId)
            )
            const sourceOstIds = new Set([...piOstIds, ...csOstIds])
            const poOstIds = new Set(
                row.items.filter(i => i.docType === 'purchase_order_item').map(i => i.orderShoeTypeId)
            )
            const missingOstIds = [...sourceOstIds].filter(id => !poOstIds.has(id))

            this.poSyncRows = missingOstIds.map(ostId => {
                const bomItem = row.items.find(i => i.docType === 'bom_item' && i.bomType === 0 && i.orderShoeTypeId === ostId)
                return {
                    ostId,
                    colorLabel: this.colorLabelOf(ostId),
                    bomTotalUsage: bomItem?.totalUsage ?? null,
                    purchaseAmount: bomItem?.totalUsage ?? 0,
                    unitUsage: null,
                    bomUnitUsage: null,
                    sizeAmounts: {},
                    sizeInfo: null,
                    sizeInfoLoading: false,
                }
            })
            this.poSyncTarget = { ...row }
            this.poSyncDialogVisible = true
            this.poSyncRows.forEach(r => this.loadPOSizeInfo(r))
        },
        async loadPOSizeInfo(r) {
            r.sizeInfoLoading = true
            try {
                const res = await axios.get(`${this.$apiBaseUrl}/material/ordershoetype-batch-info`, {
                    params: { orderShoeTypeId: r.ostId },
                })
                r.sizeInfo = res.data
                // 仅分尺码材料（materialCategory === 1）才反推每双用量并自动计算
                if (this.poSyncTarget?.materialCategory === 1 && r.bomTotalUsage && r.sizeInfo.grandTotal > 0) {
                    r.bomUnitUsage = r.bomTotalUsage / r.sizeInfo.grandTotal
                    r.unitUsage = r.bomUnitUsage
                    this.calcPOSizeAmounts(r)
                }
            } catch (e) { console.error(e) }
            finally { r.sizeInfoLoading = false }
        },
        calcPOSizeAmounts(r) {
            if (!r.sizeInfo || !r.unitUsage) {
                r.sizeAmounts = {}
                r.purchaseAmount = 0
                return
            }
            const amounts = {}
            let total = 0
            for (const [s, cnt] of Object.entries(r.sizeInfo.totals)) {
                if (!cnt) continue
                const amt = Math.ceil(r.unitUsage * cnt)
                amounts[s] = amt
                total += amt
            }
            r.sizeAmounts = amounts
            r.purchaseAmount = total
        },
        poSizeColumns(r) {
            if (!r.sizeInfo) return []
            return Object.keys(r.sizeInfo.totals).filter(s => r.sizeInfo.totals[s] > 0)
        },
        poSizeSummary({ columns }, r) {
            const t = r.sizeInfo?.totals || {}
            const grand = r.sizeInfo?.grandTotal || 0
            return columns.map((col, i) => {
                if (i === 0) return '合计'
                if (col.property === 'total') return grand
                return t[col.property] || ''
            })
        },
        async submitPOSync() {
            this.poSyncLoading = true
            try {
                const res = await axios.post(`${this.$apiBaseUrl}/material/create-missing-po-items`, {
                    orderShoeId: this.selectedOrderShoe.orderShoeId,
                    materialId: this.poSyncTarget.materialId,
                    groupModel: this.poSyncTarget.groupModel ?? null,
                    groupSpec: this.poSyncTarget.groupSpec ?? null,
                    items: this.poSyncRows.map(r => ({
                        ostId: r.ostId,
                        purchaseAmount: r.purchaseAmount,
                        sizeAmounts: r.sizeAmounts || {},
                    })),
                })
                ElMessage.success(res.data.message || '补充成功')
                this.poSyncDialogVisible = false
                this.fetchMaterials()
            } catch (e) {
                console.error(e)
                ElMessage.error(e.response?.data?.error || '补充失败')
            } finally { this.poSyncLoading = false }
        },

        // ===== 删除对话框 =====
        openDeleteDialog(row) {
            this.deleteTarget = { ...row }
            this.deleteForm.scope = this.selectedColorTypeId === 0 ? 'shoe' : 'color'
            this.deleteDialogVisible = true
        },
        async submitDelete() {
            const target = this.deleteTarget
            const scopeText = this.deleteForm.scope === 'color'
                ? `当前配色「${this.currentColorLabel}」`
                : `整鞋款 (${target.colorPresence?.length || 0} 个配色)`
            try {
                await ElMessageBox.confirm(
                    `确定要从「${scopeText}」中删除材料「${target.materialName}」的所有记录（共 ${target.items?.length || 0} 条）？\n此操作不可恢复！`,
                    '确认删除材料',
                    { confirmButtonText: '确认删除', cancelButtonText: '取消', type: 'error' }
                )
            } catch { return }
            this.deleteLoading = true
            try {
                const body = {
                    orderShoeId: this.selectedOrderShoe.orderShoeId,
                    materialId: target.materialId,
                    groupModel: target.groupModel ?? null,
                    groupSpec: target.groupSpec ?? null,
                    scope: this.deleteForm.scope,
                }
                if (this.deleteForm.scope === 'color') body.orderShoeTypeId = this.selectedColorTypeId
                const res = await axios.post(`${this.$apiBaseUrl}/material/batch-delete-material`, body)
                ElMessage.success(res.data.message || '删除成功')
                this.deleteDialogVisible = false
                this.fetchMaterials()
            } catch (e) {
                console.error(e)
                ElMessage.error(e.response?.data?.error || '删除失败')
            } finally { this.deleteLoading = false }
        },

        // ===== 添加材料对话框 =====
        openAddDialog() {
            const ostId = this.selectedColorTypeId || (this.colorTypes[0]?.orderShoeTypeId || null)
            this.addForm = {
                orderShoeTypeId: ostId,
                materialId: null,
                materialModel: '',
                materialSpecification: '',
                color: '',
                unitUsage: 0,
                approvalAmount: 0,
                remark: '',
            }
            this.addMaterialSearchKw = ''
            this.addMaterialResults = []
            this.sizeInfo = null
            this.addDialogVisible = true
            if (ostId) this.fetchSizeInfo(ostId)
        },
        async fetchSizeInfo(ostId) {
            this.sizeInfoLoading = true
            try {
                const res = await axios.get(`${this.$apiBaseUrl}/material/ordershoetype-batch-info`, {
                    params: { orderShoeTypeId: ostId },
                })
                this.sizeInfo = res.data
                this.calcApproval()
            } catch (e) {
                console.error(e)
                this.sizeInfo = null
            } finally { this.sizeInfoLoading = false }
        },
        calcApproval() {
            if (!this.sizeInfo) return
            const total = this.sizeInfo.grandTotal || 0
            const u = parseFloat(this.addForm.unitUsage) || 0
            this.addForm.approvalAmount = parseFloat((u * total).toFixed(5))
        },
        sizeSummary({ columns }) {
            const t = this.sizeInfo?.totals || {}
            const grand = this.sizeInfo?.grandTotal || 0
            return columns.map((col, i) => {
                if (i === 0) return '合计'
                if (col.property === 'total') return grand
                return t[col.property] || ''
            })
        },
        async searchAddMaterials() {
            const kw = this.addMaterialSearchKw.trim()
            if (!kw) { ElMessage.warning('请输入搜索关键字'); return }
            this.addMaterialSearchLoading = true
            try {
                const res = await axios.get(`${this.$apiBaseUrl}/material/variants`, {
                    params: { materialName: kw, pageSize: 50, page: 1, showAll: 'true' },
                })
                this.addMaterialResults = (res.data.result || []).map(m => ({
                    materialId: m.materialId,
                    materialName: m.materialName,
                    supplierName: m.supplierName || '',
                }))
                if (!this.addMaterialResults.length) ElMessage.info('未找到匹配的材料')
            } catch (e) { console.error(e); ElMessage.error('搜索材料失败') }
            finally { this.addMaterialSearchLoading = false }
        },
        async submitAdd() {
            if (!this.addForm.materialId) { ElMessage.warning('请先选择材料'); return }
            if (!this.addForm.orderShoeTypeId) { ElMessage.warning('请选择配色'); return }
            this.addLoading = true
            try {
                const body = {
                    orderShoeId: this.selectedOrderShoe.orderShoeId,
                    orderShoeTypeId: this.addForm.orderShoeTypeId,
                    materialId: this.addForm.materialId,
                    materialModel: this.addForm.materialModel,
                    materialSpecification: this.addForm.materialSpecification,
                    color: this.addForm.color,
                    unitUsage: this.addForm.unitUsage,
                    approvalAmount: this.addForm.approvalAmount,
                    remark: this.addForm.remark,
                }
                const res = await axios.post(`${this.$apiBaseUrl}/material/batch-add-material`, body)
                ElMessage.success(res.data.message || '添加成功')
                this.addDialogVisible = false
                this.fetchMaterials()
            } catch (e) {
                console.error(e)
                ElMessage.error(e.response?.data?.error || '添加失败')
            } finally { this.addLoading = false }
        },

        // ===== 编辑对话框 =====
        openEditDialog(row) {
            this.editTarget = { ...row }
            this.editForm = {
                scope: this.selectedColorTypeId === 0 ? 'shoe' : 'color',
                changeMaterial: false,
                newMaterialId: null,
                newModel: row.groupModel || '',
                newSpecification: row.groupSpec || '',
                newColor: '',
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
                groupModel: this.editTarget.groupModel ?? null,
                groupSpec: this.editTarget.groupSpec ?? null,
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
