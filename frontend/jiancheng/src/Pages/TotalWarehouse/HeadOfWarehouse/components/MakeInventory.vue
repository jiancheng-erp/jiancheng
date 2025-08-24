<template>
    <div>
        <!-- 顶部操作 -->
        <div class="mb-2" style="display: flex; gap: 12px; align-items: center">
            <el-button type="primary" @click="openInventDialog">新建盘库</el-button>
            <el-button @click="fetchRecordList">刷新</el-button>
            <el-input v-model="recordFilters.keyword" placeholder="搜索盘库单号 / 原因" clearable style="width: 240px" @keyup.enter.native="onRecordSearch" />
            <el-date-picker
                v-model="recordFilters.dateRange"
                type="daterange"
                start-placeholder="开始日期"
                end-placeholder="结束日期"
                value-format="YYYY-MM-DD"
                format="YYYY-MM-DD"
                range-separator="至"
                style="width: 320px"
                @change="onRecordSearch"
            />
        </div>

        <!-- 盘库记录列表 -->
        <el-card shadow="never" class="mb-2">
            <el-table :data="recordRows" border stripe height="560" v-loading="recordLoading" element-loading-text="加载中...">
                <el-table-column prop="makeInventoryRid" label="盘库单号" width="200" fixed="left" />
                <el-table-column prop="recordDate" label="盘库日期" width="140">
                    <template #default="{ row }">{{ row.recordDate || '-' }}</template>
                </el-table-column>
                <el-table-column prop="reason" label="盘库原因" show-overflow-tooltip />
                <el-table-column prop="status" label="状态" width="180">
                    <template #default="{ row }">
                        <el-tag v-if="row.status === 0 || (row.excelReuploadStatus === 0 && row.status === 1)" type="info">未回传</el-tag>
                        <el-tag v-else-if="row.status === 1 && row.excelReuploadStatus === 1" type="warning"> 已回传 </el-tag>
                        <el-tag v-else type="success">盘库完成</el-tag>
                    </template>
                </el-table-column>

                <el-table-column label="操作" width="280" fixed="right">
                    <template #default="{ row }">
                        <el-button type="primary" link @click="openInventDialog(row)" :disabled="row.status == 2">编辑</el-button>
                        <el-popconfirm title="确认将该盘库标记为【等待确认】？此操作会将库存内容全部出库！" @confirm="confirmRecord(row)">
                            <template #reference>
                                <el-button type="success" link :disabled="row.status !== 1">确认盘库</el-button>
                            </template>
                        </el-popconfirm>
                    </template>
                </el-table-column>
            </el-table>

            <div class="mt-2">
                <el-pagination
                    background
                    layout="total, sizes, prev, pager, next, jumper"
                    :total="recordPage.total"
                    :current-page="recordPage.currentPage"
                    :page-size="recordPage.pageSize"
                    :page-sizes="[10, 20, 30, 50, 100]"
                    @current-change="onRecordPageChange"
                    @size-change="onRecordSizeChange"
                />
            </div>
        </el-card>

        <!-- 新建 / 查看 盘库（对话框） -->
        <el-dialog title="盘库" v-model="invent.visible" width="80%">
            <el-form label-width="96px" :model="invent.form" class="mb-2">
                <el-form-item label="盘库日期">
                    <el-date-picker v-model="invent.form.date" type="date" value-format="YYYY-MM-DD" format="YYYY-MM-DD" placeholder="选择日期" :clearable="false" style="width: 220px" />
                </el-form-item>
                <el-form-item label="盘库原因">
                    <el-input v-model="invent.form.reason" type="textarea" :rows="3" placeholder="例如：季度例行盘点 / 调整异常库存" maxlength="200" show-word-limit style="width: 360px" />
                </el-form-item>

                <el-divider content-position="left">导出 / 导入</el-divider>
                <el-form-item label="操作">
                    <el-button type="primary" :loading="invent.exportLoading" @click="startInventoryExport"> 生成盘库Excel </el-button>

                    <el-upload action="" :auto-upload="false" :show-file-list="false" accept=".xlsx,.xls" @change="onImportFileChange">
                        <el-button>导入盘库Excel</el-button>
                    </el-upload>
                    <span style="color: #909399; margin-left: 12px">支持 .xlsx / .xls，表头与导出一致</span>
                </el-form-item>
            </el-form>

            <!-- 材料统计（SPU汇总） -->
            <el-alert type="info" :closable="false" show-icon class="mb-2" :title="`共 ${invent.page.total} 条 SPU | 当前页总库存：${fmtNumber(inventPageTotal)}`" />

            <div class="mb-2" style="display: flex; gap: 12px; align-items: center">
                <el-input v-model="invent.filters.keyword" placeholder="型号 / 规格 / 颜色 / SPU编号" clearable style="width: 280px" @keyup.enter.native="fetchInventSummary" />
                <el-button type="primary" @click="fetchInventSummary">查询</el-button>
                <el-button @click="resetInventFilters">重置</el-button>

                <el-select v-model="invent.sort.by" style="width: 220px" @change="fetchInventSummary">
                    <el-option label="按 总库存" value="total_current_amount" />
                    <el-option label="按 总价格" value="total_value_amount" />
                    <el-option label="按 平均单价" value="avg_unit_price" />
                    <el-option label="按 SPU ID" value="spu_material_id" />
                    <el-option label="按 型号" value="material_model" />
                    <el-option label="按 规格" value="material_specification" />
                    <el-option label="按 颜色" value="color" />
                    <el-option v-for="sz in invent.sizeColumns" :key="'sort-size-' + sz" :label="'按 尺码 ' + sz" :value="'size_' + sz" />
                </el-select>
                <el-select v-model="invent.sort.order" style="width: 120px" @change="fetchInventSummary">
                    <el-option label="降序" value="desc" />
                    <el-option label="升序" value="asc" />
                </el-select>
            </div>

            <el-table :data="invent.rows" border stripe height="420" v-loading="invent.loading" element-loading-text="加载中..." show-summary :summary-method="inventTableSummary">
                <el-table-column prop="spuRid" label="SPU编号" width="160" fixed="left" show-overflow-tooltip />
                <el-table-column prop="type" label="材料类型" width="160" show-overflow-tooltip />
                <el-table-column prop="name" label="材料名称" width="160" show-overflow-tooltip />
                <el-table-column prop="model" label="材料型号" width="160" show-overflow-tooltip />
                <el-table-column prop="specification" label="材料规格" width="160" show-overflow-tooltip />
                <el-table-column prop="color" label="颜色" width="120" show-overflow-tooltip />
                <el-table-column prop="unit" label="单位" width="90" />
                <el-table-column prop="totalCurrentAmount" label="总库存" width="120">
                    <template #default="{ row }">{{ fmtQty(row.totalCurrentAmount) }}</template>
                </el-table-column>
                <el-table-column prop="totalValueAmount" label="总价格" width="140">
                    <template #default="{ row }">{{ fmtQty(row.totalValueAmount) }}</template>
                </el-table-column>
                <el-table-column prop="avgUnitPrice" label="平均单价" width="120">
                    <template #default="{ row }">{{ fmtQty(row.avgUnitPrice) }}</template>
                </el-table-column>
                <!-- 如需动态尺码列，可在此处按 sizeColumns 追加 -->
            </el-table>

            <div class="mt-2">
                <el-pagination
                    background
                    layout="total, sizes, prev, pager, next, jumper"
                    :total="invent.page.total"
                    :current-page="invent.page.currentPage"
                    :page-size="invent.page.pageSize"
                    :page-sizes="[10, 20, 30, 50, 100]"
                    @current-change="onInventPageChange"
                    @size-change="onInventSizeChange"
                />
            </div>

            <template #footer>
                <el-button type="primary" @click="saveRecord" :loading="invent.saveLoading">保存</el-button>
                <el-button @click="invent.visible = false">关闭</el-button>
            </template>
        </el-dialog>

        <!-- 导入结果 -->
        <el-dialog title="导入结果" v-model="importResult.visible" width="640px">
            <div v-if="importResult.data">
                <p>
                    更新成功：<b>{{ importResult.data.updated }}</b> 条
                </p>
                <p>
                    失败：<b>{{ importResult.data.failed }}</b> 条
                </p>
                <div v-if="importResult.data.errors?.length">
                    <el-alert type="warning" :closable="false" show-icon title="错误详情：" class="mb-2" />
                    <el-table :data="importResult.data.errors" size="small" border>
                        <el-table-column prop="row" label="行号" width="80" />
                        <el-table-column prop="reason" label="原因" />
                    </el-table>
                </div>
            </div>
            <template #footer>
                <el-button type="primary" @click="importResult.visible = false">好的</el-button>
            </template>
        </el-dialog>
    </div>
    <el-dialog title="盘库表差异" v-model="diffDialog.visible" width="90%" destroy-on-close>
        <template v-if="diffDialog.view && diffDialog.diffHeader">
            <el-alert
                type="info"
                :closable="false"
                show-icon
                class="mb-2"
                :title="`盘库单号：${diffDialog.diffHeader.rid} | 基线：${diffDialog.diffHeader.baselineFile || '（未找到导出文件，视为全新增）'} | 上传：${diffDialog.diffHeader.uploadedFile}`"
            />
            <el-alert
                type="success"
                :closable="false"
                show-icon
                class="mb-2"
                :title="`变更：${diffDialog.diffHeader.summary.changed} | 新增：${diffDialog.diffHeader.summary.added} | 减少：${diffDialog.diffHeader.summary.removed} | 数量净变：${fmtSigned(diffDialog.diffHeader.summary.totalDeltaQty)} | 金额净变：${fmtSigned(diffDialog.diffHeader.summary.totalDeltaValue)}`"
            />

            <el-tabs v-model="diffDialog.activeTab" lazy>
                <el-tab-pane v-for="t in diffDialog.tabs" :key="t.key" :label="`${t.label} (${getGroupCount(t.key)})`" :name="t.key">
                    <el-table
                        :data="getPagedGroup(t.key)"
                        border
                        stripe
                        height="520"
                        empty-text="无数据"
                        :row-key="(row) => row.spuRid || row.spuMaterialId || row.after?.spuRid || row.before?.spuRid"
                    >
                        <el-table-column prop="spuRid" label="SPU编号" width="160" show-overflow-tooltip>
                            <template #default="{ row }">{{ row.spuRid || row.after?.spuRid || row.before?.spuRid }}</template>
                        </el-table-column>
                        <el-table-column label="名称/型号/规格/颜色" min-width="240" show-overflow-tooltip>
                            <template #default="{ row }">
                                <span>
                                    {{
                                        (row.after?.name || row.before?.name || '-') +
                                        ' / ' +
                                        (row.after?.model || row.before?.model || '-') +
                                        ' / ' +
                                        (row.after?.specification || row.before?.specification || '-') +
                                        ' / ' +
                                        (row.after?.color || row.before?.color || '-')
                                    }}
                                </span>
                            </template>
                        </el-table-column>
                        <el-table-column label="单位" width="90">
                            <template #default="{ row }">{{ row.unit || row.after?.unit || row.before?.unit || '-' }}</template>
                        </el-table-column>

                        <!-- 总库存 -->
                        <el-table-column label="总库存(前)" width="120">
                            <template #default="{ row }">{{ fmtQty(row.before?.totalCurrentAmount) }}</template>
                        </el-table-column>
                        <el-table-column label="总库存(后)" width="120">
                            <template #default="{ row }">{{ fmtQty(row.after?.totalCurrentAmount) }}</template>
                        </el-table-column>
                        <el-table-column label="Δ总库存" width="120">
                            <template #default="{ row }"
                                ><b>{{ fmtSigned(row.delta?.totalCurrentAmount) }}</b></template
                            >
                        </el-table-column>

                        <!-- 总价格 -->
                        <el-table-column label="总价格(前)" width="140">
                            <template #default="{ row }">{{ fmtQty(row.before?.totalValueAmount) }}</template>
                        </el-table-column>
                        <el-table-column label="总价格(后)" width="140">
                            <template #default="{ row }">{{ fmtQty(row.after?.totalValueAmount) }}</template>
                        </el-table-column>
                        <el-table-column label="Δ总价格" width="140">
                            <template #default="{ row }"
                                ><b>{{ fmtSigned(row.delta?.totalValueAmount) }}</b></template
                            >
                        </el-table-column>
                        <el-table-column label="标记" width="120">
                            <template #default="{ row }">
                                <el-tag v-if="row.type === 'added' && row.isNewMaterial" type="warning">新材料</el-tag>
                            </template>
                        </el-table-column>

                        <!-- 原始字段提示（可选显示更多：名称/型号/规格/颜色） -->
                    </el-table>
                    <div class="mt-2" style="text-align: right">
                        <el-pagination
                            background
                            layout="total, sizes, prev, pager, next, jumper"
                            :total="getGroupCount(t.key)"
                            :current-page="diffDialog.pager[t.key].page"
                            :page-size="diffDialog.pager[t.key].pageSize"
                            :page-sizes="[20, 50, 100, 200]"
                            @current-change="(p) => (diffDialog.pager[t.key].page = p)"
                            @size-change="
                                (s) => {
                                    diffDialog.pager[t.key].pageSize = s
                                    diffDialog.pager[t.key].page = 1
                                }
                            "
                        />
                    </div>
                </el-tab-pane>
            </el-tabs>
        </template>

        <template #footer>
            <el-button @click="diffDialog.visible = false">关闭</el-button>
        </template>
    </el-dialog>
    <!-- 统一的后台任务进度对话框 -->
    <el-dialog v-model="taskProgress.visible" :title="taskProgress.title" width="560px" :close-on-click-modal="false" :show-close="false">
        <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px">
            <el-progress :percentage="taskProgress.percent" :status="taskProgress.status" style="flex: 1" />
            <span style="width: 72px; text-align: right; color: #909399">{{ taskProgress.percent }}%</span>
        </div>

        <el-alert v-if="taskProgress.subtitle" :title="taskProgress.subtitle" type="info" :closable="false" show-icon class="mb-2" />

        <div
            style="
                height: 220px;
                overflow: auto;
                background: #0b1020;
                color: #b5c6ff;
                border-radius: 6px;
                padding: 10px;
                font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace;
                font-size: 12px;
            "
        >
            <div v-for="(line, idx) in taskProgress.logs" :key="idx">[{{ line.time }}] {{ line.text }}</div>
        </div>

        <template #footer>
            <el-button v-if="taskProgress.done" type="primary" @click="closeTaskProgress">完成</el-button>
            <el-button v-else disabled>后台执行中...</el-button>
        </template>
    </el-dialog>
</template>

<script>
import axios from 'axios'
import { markRaw } from 'vue'

export default {
    name: 'MaterialInventoryPage',
    data() {
        return {
            // ===== 盘库记录列表（主页） =====
            recordLoading: false,
            recordRows: [],
            recordFilters: {
                keyword: '',
                dateRange: []
            },
            recordPage: {
                total: 0,
                currentPage: 1,
                pageSize: 20
            },

            // ===== 盘库对话框（材料统计表在这里） =====
            invent: {
                visible: false,
                exportLoading: false,
                loading: false,
                currentRecord: null, // 如果是从某条记录“查看/再次导入”进入，可放在这里
                form: {
                    date: '',
                    reason: ''
                },
                // 表格数据
                filters: { keyword: '' },
                sort: { by: 'total_current_amount', order: 'desc' },
                sizeColumns: [],
                rows: [],
                page: { total: 0, currentPage: 1, pageSize: 20 }
            },

            // 导入反馈
            importResult: { visible: false, data: null },
            diffDialog: {
                visible: false,
                loading: false,
                diffHeader: null, // 仅保存 header/summary（轻）
                view: null, // 仅保存分组和尺码列（轻）
                tabs: [
                    { key: 'changed', label: '变更' },
                    { key: 'added', label: '新增' },
                    { key: 'removed', label: '减少' },
                    { key: 'unchanged', label: '未变化' }
                ],
                activeTab: 'changed',
                // 针对每个分组做分页，避免一次性渲染全部
                pager: {
                    changed: { page: 1, pageSize: 50 },
                    added: { page: 1, pageSize: 50 },
                    removed: { page: 1, pageSize: 50 },
                    unchanged: { page: 1, pageSize: 50 }
                }
            },
            taskProgress: {
                visible: false,
                title: '',
                subtitle: '',
                percent: 0,
                status: null, // null | 'success' | 'exception'
                logs: [],
                timer: null,
                done: false
            }
        }
    },
    computed: {
        inventPageTotal() {
            return this.invent.rows.reduce((s, r) => s + Number(r.totalCurrentAmount || 0), 0)
        }
    },
    mounted() {
        this.fetchRecordList()
    },
    methods: {
        toDateStr(v) {
            if (!v) return ''
            if (typeof v === 'string') return v.slice(0, 10)
            const d = new Date(v)
            if (Number.isNaN(d.getTime())) return ''
            const y = d.getFullYear()
            const m = String(d.getMonth() + 1).padStart(2, '0')
            const dd = String(d.getDate()).padStart(2, '0')
            return `${y}-${m}-${dd}`
        },
        async confirmRecord(row) {
            try {
                // 弹出进度框并记录阶段
                this.openTaskProgress('确认盘库', `盘库单号：${row.makeInventoryRid}`)
                this.logTask('开始确认盘库...')
                this.logTask('阶段 1/3：清库出库（按供应商+仓库分组）')
                this.tickTaskProgress(40, 150, 95)

                const resp = await axios.post(
                    `${this.$apiBaseUrl}/warehouse/makeinventory/confirm`,
                    {
                        makeInventoryRecordId: row.makeInventoryRecordId
                    },
                    { timeout: 0 }
                )

                // 阶段推进显示
                this.taskProgress.percent = Math.max(this.taskProgress.percent, 40)
                this.logTask('阶段 2/3：回传表回填入库（按聚合分组）')
                this.tickTaskProgress(75, 150, 95)

                // 成功返回后，做收尾
                this.taskProgress.percent = Math.max(this.taskProgress.percent, 75)
                this.logTask('阶段 3/3：更新盘库记录状态与关联单号')
                this.tickTaskProgress(95, 150, 95)

                // 刷新
                await this.fetchRecordList()
                this.logTask('刷新盘库记录列表完成')
                this.finishTaskProgress(true)
                this.$message.success('已标记为盘库完成')
            } catch (e) {
                this.logTask(`确认失败：${e?.response?.data?.message || e?.message || e}`)
                this.finishTaskProgress(false)
                this.$message.error('操作失败')
            }
        },
        // ===== 盘库记录列表 =====
        async fetchRecordList() {
            this.recordLoading = true
            try {
                const dr = this.recordFilters.dateRange
                const params = {
                    page: this.recordPage.currentPage,
                    pageSize: this.recordPage.pageSize,
                    ...(this.recordFilters.keyword?.trim() ? { keyword: this.recordFilters.keyword.trim() } : {}),
                    ...(Array.isArray(dr) && dr.length === 2
                        ? {
                              dateFrom: this.toDateStr(dr[0]),
                              dateTo: this.toDateStr(dr[1])
                          }
                        : {})
                }
                const resp = await axios.get(`${this.$apiBaseUrl}/warehouse/makeinventory/list`, { params })
                const data = resp?.data || {}
                this.recordRows = Array.isArray(data.list) ? data.list : []
                this.recordPage.total = Number(data.total || 0)
            } catch (e) {
                this.$message.error('加载盘库记录失败')
            } finally {
                this.recordLoading = false
            }
        },
        onRecordSearch() {
            this.recordPage.currentPage = 1
            this.fetchRecordList()
        },
        onRecordPageChange(v) {
            this.recordPage.currentPage = v
            this.fetchRecordList()
        },
        onRecordSizeChange(v) {
            this.recordPage.pageSize = v
            this.recordPage.currentPage = 1
            this.fetchRecordList()
        },

        // ===== 打开盘库对话框 =====
        openInventDialog(record = null) {
            if (record) {
                this.invent.currentRecord = record
                this.invent.form.date = this.toDateStr(record.recordDate || this.today())
                this.invent.form.reason = record.reason || ''
            } else {
                this.invent.currentRecord = null
                this.invent.form.date = this.today() // 已是字符串
                this.invent.form.reason = ''
            }
            this.resetInventFilters(false)
            this.invent.visible = true
            this.fetchInventSummary()
        },
        today() {
            const d = new Date()
            const yyyy = d.getFullYear()
            const mm = String(d.getMonth() + 1).padStart(2, '0')
            const dd = String(d.getDate()).padStart(2, '0')
            return `${yyyy}-${mm}-${dd}`
        },

        // ===== 盘库导出 =====
        async startInventoryExport() {
            if (!this.invent.form.date) {
                this.$message.warning('请选择盘库日期')
                return
            }
            this.invent.exportLoading = true
            try {
                const dateStr = this.toDateStr(this.invent.form.date)
                // 1) 生成Excel（导出全部，不分页）
                const params = {
                    export: 1,
                    inventoryDate: dateStr,
                    inventoryReason: this.invent.form.reason,
                    ...(this.invent.filters.keyword?.trim() ? { keyword: this.invent.filters.keyword.trim() } : {}),
                    ...(this.invent.currentRecord?.makeInventoryRecordId ? { recordId: this.invent.currentRecord.makeInventoryRecordId } : {})
                }
                const resp = await axios.get(`${this.$apiBaseUrl}/warehouse/inventorysummary/export`, {
                    params,
                    responseType: 'blob'
                })
                const blob = new Blob([resp.data], {
                    type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                })
                const url = URL.createObjectURL(blob)
                const a = document.createElement('a')
                const reasonSafe = (this.invent.form.reason || '').replace(/[\\/:*?"<>|]/g, '')
                a.href = url
                a.download = `材料盘库_${this.invent.form.date}${reasonSafe ? '_' + reasonSafe : ''}.xlsx`
                a.click()
                URL.revokeObjectURL(url)
                this.$message.success('盘库Excel已生成')

                // // 2) 记录盘库（落表）
                // await axios.post(`${this.$apiBaseUrl}/warehouse/makeinventory/create`, {
                //     recordDate: dateStr,
                //     reason: this.invent.form.reason
                // })
                this.fetchRecordList()
            } catch (e) {
                this.$message.error('生成或记录盘库失败')
            } finally {
                this.invent.exportLoading = false
            }
        },

        // ===== 盘库导入 =====

        // ===== 对话框内：材料统计表格 =====
        async fetchInventSummary() {
            this.invent.loading = true
            try {
                const params = {
                    page: this.invent.page.currentPage,
                    pageSize: this.invent.page.pageSize,
                    sortBy: this.invent.sort.by,
                    sortOrder: this.invent.sort.order,
                    ...(this.invent.filters.keyword?.trim() ? { keyword: this.invent.filters.keyword.trim() } : {})
                }
                const resp = await axios.get(`${this.$apiBaseUrl}/warehouse/inventorysummary`, { params })
                const data = resp?.data || {}
                this.invent.rows = Array.isArray(data.list) ? data.list : []
                this.invent.page.total = Number(data.total || 0)
                this.invent.sizeColumns = Array.isArray(data.sizeColumns) ? data.sizeColumns : []
            } catch (e) {
                this.$message.error('加载材料汇总失败')
            } finally {
                this.invent.loading = false
            }
        },
        resetInventFilters(refetch = true) {
            this.invent.filters.keyword = ''
            this.invent.sort.by = 'total_current_amount'
            this.invent.sort.order = 'desc'
            this.invent.page.currentPage = 1
            this.invent.page.pageSize = 20
            if (refetch) this.fetchInventSummary()
        },
        onInventPageChange(v) {
            this.invent.page.currentPage = v
            this.fetchInventSummary()
        },
        onInventSizeChange(v) {
            this.invent.page.pageSize = v
            this.invent.page.currentPage = 1
            this.fetchInventSummary()
        },

        // 合计（对话框内）
        inventTableSummary({ columns, data }) {
            const sums = []
            columns.forEach((col, index) => {
                if (index === 0) {
                    sums[index] = '本页合计'
                    return
                }
                if (['totalCurrentAmount', 'totalValueAmount', 'avgUnitPrice'].includes(col.property)) {
                    const total = data.reduce((s, r) => s + Number(r[col.property] || 0), 0)
                    sums[index] = this.fmtQty(total)
                } else {
                    sums[index] = ''
                }
            })
            return sums
        },

        // 主页操作：按记录导出（如需）
        async downloadExportByRecord(row) {
            try {
                const params = {
                    export: 1,
                    inventoryDate: row.recordDate,
                    inventoryReason: row.reason || ''
                }
                const resp = await axios.get(`${this.$apiBaseUrl}/warehouse/inventorysummary/export`, {
                    params,
                    responseType: 'blob'
                })
                const blob = new Blob([resp.data], {
                    type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                })
                const url = URL.createObjectURL(blob)
                const a = document.createElement('a')
                const reasonSafe = (row.reason || '').replace(/[\\/:*?"<>|]/g, '')
                a.href = url
                a.download = `材料盘库_${row.recordDate || ''}${reasonSafe ? '_' + reasonSafe : ''}.xlsx`
                a.click()
                URL.revokeObjectURL(url)
            } catch (e) {
                this.$message.error('按记录导出失败')
            }
        },

        // 工具
        fmtQty(n) {
            return Number(n || 0).toLocaleString(undefined, { maximumFractionDigits: 4 })
        },
        fmtNumber(n) {
            return Number(n || 0).toLocaleString()
        },
        async saveRecord() {
            if (!this.invent.form.date) {
                this.$message.warning('请选择盘库日期')
                return
            }
            this.invent.saveLoading = true
            try {
                const dateStr = this.toDateStr(this.invent.form.date)

                if (this.invent.currentRecord?.makeInventoryRecordId) {
                    await axios.put(`${this.$apiBaseUrl}/warehouse/makeinventory/update`, {
                        makeInventoryRecordId: this.invent.currentRecord.makeInventoryRecordId,
                        recordDate: dateStr,
                        reason: this.invent.form.reason
                    })
                    this.$message.success('已保存')
                } else {
                    const resp = await axios.post(`${this.$apiBaseUrl}/warehouse/makeinventory/create`, {
                        recordDate: dateStr,
                        reason: this.invent.form.reason
                    })
                    const d = resp?.data || {}
                    // ⚠️ 使用后端的真实字段名
                    this.invent.currentRecord = {
                        makeInventoryRecordId: d.makeInventoryRecordId,
                        makeInventoryRid: d.makeInventoryRid,
                        recordDate: dateStr,
                        reason: this.invent.form.reason,
                        status: 0
                    }
                    this.$message.success('已新建盘库记录')
                }

                this.fetchRecordList()
            } catch (e) {
                this.$message.error('保存失败')
            } finally {
                this.invent.saveLoading = false
            }
        },
        groupDiffItems(diff) {
            const groups = { changed: [], added: [], removed: [], unchanged: [] }
            const allSizeKeys = new Set()

            ;(diff?.items || []).forEach((it) => {
                const k = it.type || 'changed'
                if (!groups[k]) groups[k] = []
                groups[k].push(it)
                // 汇总所有出现过的尺码列，便于动态列渲染
                const beforeSizes = (it.before && it.before.sizes) || {}
                const afterSizes = (it.after && it.after.sizes) || {}
                const deltaSizes = (it.delta && it.delta.sizes) || {}
                Object.keys(beforeSizes).forEach((s) => allSizeKeys.add(s))
                Object.keys(afterSizes).forEach((s) => allSizeKeys.add(s))
                Object.keys(deltaSizes).forEach((s) => allSizeKeys.add(s))
            })

            return { groups, sizeKeys: Array.from(allSizeKeys).sort((a, b) => Number(a) - Number(b)) }
        },
        fmtSigned(n) {
            const v = Number(n || 0)
            const s = v.toLocaleString(undefined, { maximumFractionDigits: 4 })
            if (v > 0) return `+${s}`
            if (v < 0) return s
            return '0'
        },
        // 打开差异弹窗
        openDiffDialog(diff) {
            const raw = markRaw(diff) // 不让 Vue 深度代理
            const { groups, sizeKeys } = this.groupDiffItems(raw)

            // 只把轻量信息放到响应式里
            this.diffDialog.diffHeader = {
                rid: raw.rid,
                baselineFile: raw.baselineFile,
                uploadedFile: raw.uploadedFile,
                summary: raw.summary
            }
            this.diffDialog.view = markRaw({ groups, sizeKeys })

            // 重置分页
            Object.keys(this.diffDialog.pager).forEach((k) => {
                this.diffDialog.pager[k].page = 1
            })

            // 默认切到第一个有数据的分组
            const firstNonEmpty = ['changed', 'added', 'removed', 'unchanged'].find((k) => (groups[k] || []).length)
            this.diffDialog.activeTab = firstNonEmpty || 'changed'
            this.diffDialog.visible = true
        },
        async onImportFileChange(file) {
            try {
                if (!this.invent.currentRecord?.makeInventoryRecordId) {
                    this.$message.warning('请先保存盘库记录后再导入（需要RecordId）')
                    return
                }
                const form = new FormData()
                form.append('file', file.raw || file)
                form.append('recordId', this.invent.currentRecord.makeInventoryRecordId)

                // 进度对话框
                this.openTaskProgress('导入盘库 Excel', '正在上传文件...')
                this.logTask('开始上传文件')
                this.tickTaskProgress(40, 100, 90) // 上传阶段推进到 40%

                const resp = await axios.post(`${this.$apiBaseUrl}/warehouse/inventorysummary/import`, form, {
                    headers: { 'Content-Type': 'multipart/form-data' },
                    onUploadProgress: (evt) => {
                        if (evt.total) {
                            const p = Math.floor((evt.loaded / evt.total) * 35) // 上传算 0~35%
                            this.taskProgress.percent = Math.max(this.taskProgress.percent, p)
                        }
                    },
                    timeout: 0 // 导入可能较久，不限时
                })

                this.logTask('上传完成，服务器解析中...')
                // 解析/比对阶段模拟推进到 95%
                this.tickTaskProgress(95, 200, 95)

                const data = resp?.data || {}
                // 展示导入结果
                this.importResult.data = {
                    updated: Number(data.updated || 0),
                    failed: Number(data.failed || 0),
                    errors: Array.isArray(data.errors) ? data.errors : []
                }

                // 差异弹窗
                if (data.diff) {
                    this.logTask('解析完成，生成差异视图')
                    this.openDiffDialog(data.diff)
                }

                // 刷新列表
                await this.fetchInventSummary()
                await this.fetchRecordList()

                this.logTask('导入流程完成')
                this.finishTaskProgress(true)
            } catch (e) {
                this.logTask(`导入失败：${e?.message || e}`)
                this.finishTaskProgress(false)
                this.$message.error('导入失败')
            }
        },
        getGroupCount(key) {
            return (this.diffDialog.view?.groups?.[key] || []).length
        },
        getPagedGroup(key) {
            const arr = this.diffDialog.view?.groups?.[key] || []
            const { page, pageSize } = this.diffDialog.pager[key]
            const start = (page - 1) * pageSize
            return arr.slice(start, start + pageSize)
        },
        getSizeKeysForGroup(key) {
            const group = this.diffDialog.view?.groups?.[key] || []
            const set = new Set()
            group.forEach((it) => {
                ;[it.before?.sizes, it.after?.sizes, it.delta?.sizes].forEach((map) => {
                    if (map) Object.keys(map).forEach((k) => set.add(k))
                })
            })
            return Array.from(set).sort((a, b) => Number(a) - Number(b))
        },
        openTaskProgress(title, subtitle = '') {
            if (this.taskProgress.timer) {
                clearInterval(this.taskProgress.timer)
                this.taskProgress.timer = null
            }
            this.taskProgress.visible = true
            this.taskProgress.title = title
            this.taskProgress.subtitle = subtitle
            this.taskProgress.percent = 0
            this.taskProgress.status = null
            this.taskProgress.logs = []
            this.taskProgress.done = false
        },
        logTask(text) {
            const ts = new Date()
            const hh = String(ts.getHours()).padStart(2, '0')
            const mm = String(ts.getMinutes()).padStart(2, '0')
            const ss = String(ts.getSeconds()).padStart(2, '0')
            this.taskProgress.logs.push({ time: `${hh}:${mm}:${ss}`, text })
            this.$nextTick(() => {
                const box = document.querySelector('.el-dialog__body div[style*="overflow:auto"]')
                if (box) box.scrollTop = box.scrollHeight
            })
        },
        tickTaskProgress(target, speed = 400, maxHold = 95) {
            // 以固定间隔缓慢推进到 target（不超过 maxHold）
            if (this.taskProgress.timer) clearInterval(this.taskProgress.timer)
            this.taskProgress.timer = setInterval(() => {
                if (this.taskProgress.percent < Math.min(target, maxHold)) {
                    this.taskProgress.percent += 1
                }
            }, speed)
        },
        finishTaskProgress(success = true) {
            if (this.taskProgress.timer) {
                clearInterval(this.taskProgress.timer)
                this.taskProgress.timer = null
            }
            this.taskProgress.percent = 100
            this.taskProgress.status = success ? 'success' : 'exception'
            this.taskProgress.done = true
        },
        closeTaskProgress() {
            if (this.taskProgress.timer) {
                clearInterval(this.taskProgress.timer)
                this.taskProgress.timer = null
            }
            this.taskProgress.visible = false
        }
    }
}
</script>

<style scoped>
.mb-2 {
    margin-bottom: 12px;
}
.mt-2 {
    margin-top: 12px;
}
</style>
