<template>
    <div>
        <!-- 筛选 -->
        <el-card shadow="never" class="mb-2">
            <el-form :inline="true" @submit.native.prevent>
                <el-form-item label="筛选维度">
                    <el-radio-group v-model="filters.mode" @change="onModeChange">
                        <el-radio-button label="month">按月</el-radio-button>
                        <el-radio-button label="year">按年</el-radio-button>
                    </el-radio-group>
                </el-form-item>

                <!-- 月份选择器 -->
                <el-form-item v-if="filters.mode === 'month'" label="月份">
                    <el-date-picker v-model="filters.month" type="month" placeholder="选择月份" format="YYYY-MM" value-format="YYYY-MM" :editable="false" :clearable="false" @change="onMonthChange" />
                </el-form-item>

                <!-- 年份选择器 -->
                <el-form-item v-if="filters.mode === 'year'" label="年份">
                    <el-date-picker v-model="filters.year" type="year" placeholder="选择年份" format="YYYY" value-format="YYYY" :editable="false" :clearable="false" @change="onYearChange" />
                </el-form-item>

                <el-form-item label="方向">
                    <el-select v-model="filters.direction" clearable placeholder="全部" @change="refresh" style="width: 120px">
                        <el-option label="入库" :value="'IN'" />
                        <el-option label="出库" :value="'OUT'" />
                    </el-select>
                </el-form-item>

                <!-- 业务单号（rid） -->
                <el-form-item label="业务单号">
                    <el-input v-model="filters.keyword" placeholder="按业务单号查询（rid）" clearable style="width: 220px" @keyup.enter.native="refresh" />
                </el-form-item>

                <!-- 工厂型号 & 颜色 -->
                <el-form-item label="工厂型号">
                    <el-input v-model="filters.shoeRid" placeholder="型号（shoeRid）" clearable style="width: 180px" @keyup.enter.native="refresh" />
                </el-form-item>

                <el-form-item label="颜色">
                    <el-input v-model="filters.color" placeholder="颜色" clearable style="width: 140px" @keyup.enter.native="refresh" />
                </el-form-item>

                <el-form-item>
                    <el-button type="primary" @click="refresh">查询</el-button>
                    <el-button @click="reset">重置</el-button>
                </el-form-item>
            </el-form>
        </el-card>

        <!-- 顶部统计（分币种，强化对比） -->
        <el-row :gutter="12" class="mb-2">
            <!-- 入库 -->
            <el-col :xs="24" :sm="8">
                <el-card shadow="never" class="stats-card inbound">
                    <div class="stats-title">
                        <el-icon><circle-check /></el-icon>
                        入库
                    </div>
                    <div class="stats-line">
                        数量 <b>{{ fmtNumber(total.inQty) }}</b>
                    </div>
                    <div class="stats-line">
                        金额
                        <span class="tag-list">
                            <el-tag v-for="(val, cur) in total.inAmountByCurrency" :key="'in-' + cur" size="small" type="success" effect="dark"> {{ cur }} {{ fmtMoney(val) }} </el-tag>
                        </span>
                    </div>
                </el-card>
            </el-col>

            <!-- 出库 -->
            <el-col :xs="24" :sm="8">
                <el-card shadow="never" class="stats-card outbound">
                    <div class="stats-title">
                        <el-icon><circle-close /></el-icon>
                        出库
                    </div>
                    <div class="stats-line">
                        数量 <b>{{ fmtNumber(total.outQty) }}</b>
                    </div>
                    <div class="stats-line">
                        金额
                        <span class="tag-list">
                            <el-tag v-for="(val, cur) in total.outAmountByCurrency" :key="'out-' + cur" size="small" type="danger" effect="dark"> {{ cur }} {{ fmtMoney(val) }} </el-tag>
                        </span>
                    </div>
                </el-card>
            </el-col>

            <!-- 净值（按正负变色） -->
            <el-col :xs="24" :sm="8">
                <el-card shadow="never" class="stats-card net" :class="{ 'net-pos': total.netQty >= 0, 'net-neg': total.netQty < 0 }">
                    <div class="stats-title">
                        <el-icon v-if="total.netQty >= 0"><trend-charts /></el-icon>
                        <el-icon v-else><warning /></el-icon>
                        净值
                    </div>
                    <div class="stats-line">
                        数量
                        <b :class="{ pos: total.netQty >= 0, neg: total.netQty < 0 }">
                            {{ fmtNumber(total.netQty) }}
                        </b>
                    </div>
                    <div class="stats-line">
                        金额
                        <span class="tag-list">
                            <el-tag v-for="(val, cur) in total.netAmountByCurrency" :key="'net-' + cur" size="small" :type="tagTypeForDelta(val)" effect="dark"> {{ cur }} {{ fmtMoney(val) }} </el-tag>
                        </span>
                    </div>
                </el-card>
            </el-col>
        </el-row>

        <!-- 主表（按明细行展示） -->
        <el-table :data="rows" border stripe height="560" show-summary :summary-method="tableSummary" :row-key="rowKey" v-loading="loading" element-loading-text="加载中...">
            <el-table-column prop="rid" label="业务单号" width="220" show-overflow-tooltip />
            <el-table-column prop="direction" label="方向" width="90">
                <template #default="{ row }">
                    <el-tag :type="row.direction === 'IN' ? 'success' : 'danger'">
                        {{ row.direction === 'IN' ? '入库' : '出库' }}
                    </el-tag>
                </template>
            </el-table-column>
            <el-table-column prop="shoeRid" label="工厂型号" width="200" show-overflow-tooltip />
            <el-table-column prop="color" label="颜色" width="140" show-overflow-tooltip />
            <el-table-column prop="designer" label="设计师" width="120" show-overflow-tooltip />
            <el-table-column prop="adjuster" label="调版师" width="120" show-overflow-tooltip />
            <el-table-column prop="quantity" label="数量" width="120" />
            <el-table-column prop="unitPrice" label="单价" width="120">
                <template #default="{ row }">{{ fmtMoney(row.unitPrice) }}</template>
            </el-table-column>
            <el-table-column prop="amount" label="金额" width="140">
                <template #default="{ row }">{{ fmtMoney(row.amount) }}</template>
            </el-table-column>
            <el-table-column prop="occurTime" label="时间">
                <template #default="{ row }">{{ formatTime(row.occurTime) }}</template>
            </el-table-column>
            <el-table-column prop="currency" label="币种" />
        </el-table>

        <!-- 分页 -->
        <div class="mt-2">
            <el-pagination
                background
                layout="total, sizes, prev, pager, next, jumper"
                :total="page.total"
                :page-size="page.pageSize"
                :page-sizes="page.pageSizes"
                :current-page="page.currentPage"
                @size-change="onSizeChange"
                @current-change="onPageChange"
            />
        </div>
    </div>
</template>

<script>
import axios from 'axios'

const DEFAULT_PAGE_SIZES = [10, 20, 30, 50]
function getNowParts() {
    const now = new Date()
    const yyyy = now.getFullYear()
    const mm = String(now.getMonth() + 1).padStart(2, '0')
    return { yyyy, mm }
}

export default {
    name: 'FinishedStorageDetails',
    data() {
        const { yyyy, mm } = getNowParts()
        return {
            filters: {
                mode: 'month',
                month: `${yyyy}-${mm}`,
                year: String(yyyy),
                direction: '',
                keyword: '', // 仅匹配 rid
                shoeRid: '',
                color: ''
            },
            rows: [],
            total: {
                inQty: 0,
                outQty: 0,
                inAmountByCurrency: {}, // { CNY: 0, USD: 0, ... }
                outAmountByCurrency: {}, // { CNY: 0, USD: 0, ... }
                get netQty() {
                    return this.inQty - this.outQty
                },
                get netAmountByCurrency() {
                    const keys = new Set([...Object.keys(this.inAmountByCurrency || {}), ...Object.keys(this.outAmountByCurrency || {})])
                    const res = {}
                    keys.forEach((k) => {
                        const a = Number((this.inAmountByCurrency || {})[k] || 0)
                        const b = Number((this.outAmountByCurrency || {})[k] || 0)
                        res[k] = +(a - b).toFixed(3)
                    })
                    return res
                }
            },
            page: {
                total: 0,
                currentPage: 1,
                pageSize: 20,
                pageSizes: DEFAULT_PAGE_SIZES
            },
            loading: false
        }
    },
    mounted() {
        this.fetchData()
    },
    methods: {
        // ===== DatePicker 兼容处理 =====
        toYYYYMM(val) {
            if (!val) return ''
            if (typeof val === 'string') return val
            const d = new Date(val)
            const y = d.getFullYear()
            const m = String(d.getMonth() + 1).padStart(2, '0')
            return `${y}-${m}`
        },
        toYYYY(val) {
            if (!val) return ''
            if (typeof val === 'string') return val
            const d = new Date(val)
            return String(d.getFullYear())
        },
        onMonthPanelChange(val) {
            const next = this.toYYYYMM(val)
            if (next && next !== this.filters.month) this.filters.month = next
        },
        onMonthChange(val) {
            const next = this.toYYYYMM(val)
            if (next && next !== this.filters.month) this.filters.month = next
            this.refresh()
        },
        onYearPanelChange(val) {
            const next = this.toYYYY(val)
            if (next && next !== this.filters.year) this.filters.year = next
        },
        onYearChange(val) {
            const next = this.toYYYY(val)
            if (next && next !== this.filters.year) this.filters.year = next
            this.refresh()
        },

        // ===== 核心请求 =====
        async fetchData() {
            this.loading = true
            try {
                this.ensureTimeDefaults()

                if (this.filters.mode === 'month' && !this.filters.month) {
                    this.$message && this.$message.warning('请选择月份')
                    return
                }
                if (this.filters.mode === 'year' && !this.filters.year) {
                    this.$message && this.$message.warning('请选择年份')
                    return
                }

                const params = {
                    page: this.page.currentPage,
                    pageSize: this.page.pageSize,
                    mode: this.filters.mode,
                    ...(this.filters.mode === 'month' ? { month: this.filters.month } : {}),
                    ...(this.filters.mode === 'year' ? { year: this.filters.year } : {}),
                    ...(this.filters.direction ? { direction: this.filters.direction } : {}),
                    ...(this.filters.keyword?.trim() ? { keyword: this.filters.keyword.trim() } : {}),
                    ...(this.filters.shoeRid?.trim() ? { shoeRid: this.filters.shoeRid.trim() } : {}),
                    ...(this.filters.color?.trim() ? { color: this.filters.color.trim() } : {})
                }

                const resp = await axios.get(`${this.$apiBaseUrl}/warehouse/getshoeinoutbounddetail`, { params })
                const data = resp?.data || {}

                this.rows = Array.isArray(data.list) ? data.list : []
                this.page.total = Number(data.total || 0)

                const stat = data.stat || {}
                // 数量
                this.total.inQty = Number(stat.inQty || 0)
                this.total.outQty = Number(stat.outQty || 0)

                // 金额（分币种）
                // 若后端提供分币种字典，则使用；否则用本页兜底统计
                if (stat.inAmountByCurrency || stat.outAmountByCurrency) {
                    this.total.inAmountByCurrency = this.cloneCurrencyMap(stat.inAmountByCurrency || {})
                    this.total.outAmountByCurrency = this.cloneCurrencyMap(stat.outAmountByCurrency || {})
                } else {
                    const { inMap, outMap } = this.pageCurrencyAgg(this.rows)
                    this.total.inAmountByCurrency = inMap
                    this.total.outAmountByCurrency = outMap
                }
            } catch (e) {
                this.$message && this.$message.error('加载明细失败')
            } finally {
                this.loading = false
            }
        },

        refresh() {
            this.page.currentPage = 1
            this.fetchData()
        },

        reset() {
            const { yyyy, mm } = getNowParts()
            this.filters.mode = 'month'
            this.filters.month = `${yyyy}-${mm}`
            this.filters.year = String(yyyy)
            this.filters.direction = ''
            this.filters.keyword = ''
            this.filters.shoeRid = ''
            this.filters.color = ''
            this.page.currentPage = 1
            this.page.pageSize = 20
            this.fetchData()
        },

        onModeChange() {
            const { yyyy, mm } = getNowParts()
            if (this.filters.mode === 'month') this.filters.month = `${yyyy}-${mm}`
            else this.filters.year = String(yyyy)
            this.page.currentPage = 1
        },

        onSizeChange(v) {
            this.page.pageSize = v
            this.page.currentPage = 1
            this.fetchData()
        },

        onPageChange(v) {
            this.page.currentPage = v
            this.fetchData()
        },

        // 表格合计行（仅合计当前页金额/数量）
        tableSummary({ columns, data }) {
            const sums = []
            columns.forEach((col, index) => {
                if (index === 0) {
                    sums[index] = '本页小计'
                    return
                }
                if (['quantity', 'amount'].includes(col.property)) {
                    const values = data.map((item) => Number(item[col.property] || 0))
                    const total = values.reduce((a, b) => a + (isNaN(b) ? 0 : b), 0)
                    sums[index] = col.property === 'amount' ? this.fmtMoney(total) : this.fmtNumber(total)
                } else {
                    sums[index] = ''
                }
            })
            return sums
        },

        // ===== 工具 =====
        formatTime(v) {
            if (!v) return '-'
            const d = new Date(v)
            if (isNaN(d.getTime())) return v
            const y = d.getFullYear()
            const m = String(d.getMonth() + 1).padStart(2, '0')
            const day = String(d.getDate()).padStart(2, '0')
            const hh = String(d.getHours()).padStart(2, '0')
            const mm = String(d.getMinutes()).padStart(2, '0')
            const ss = String(d.getSeconds()).padStart(2, '0')
            return `${y}-${m}-${day} ${hh}:${mm}:${ss}`
        },
        fmtMoney(n) {
            const v = Number(n || 0)
            return v.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })
        },
        fmtNumber(n) {
            const v = Number(n || 0)
            return v.toLocaleString()
        },
        fmtCurrencyMap(obj) {
            const entries = Object.entries(obj || {})
            if (!entries.length) return '—'
            return entries
                .sort(([a], [b]) => a.localeCompare(b))
                .map(([k, v]) => `${k} ${this.fmtMoney(v)}`)
                .join(' | ')
        },
        cloneCurrencyMap(obj) {
            const res = {}
            Object.keys(obj || {}).forEach((k) => {
                res[k] = Number(obj[k] || 0)
            })
            return res
        },
        // 当前页兜底：按币种聚合入/出金额
        pageCurrencyAgg(rows) {
            const inMap = {},
                outMap = {}
            for (const r of rows || []) {
                const c = r.currency || 'CNY'
                const a = Number(r.amount || 0)
                if (r.direction === 'IN') inMap[c] = +(Number(inMap[c] || 0) + a).toFixed(3)
                if (r.direction === 'OUT') outMap[c] = +(Number(outMap[c] || 0) + a).toFixed(3)
            }
            return { inMap, outMap }
        },
        rowKey(row) {
            return `${row.rid}-${row.detailId}`
        },
        ensureTimeDefaults() {
            const { yyyy, mm } = getNowParts()
            if (this.filters.mode === 'month') {
                if (!this.filters.month || !/^\d{4}-\d{2}$/.test(this.filters.month)) this.filters.month = `${yyyy}-${mm}`
            } else {
                if (!this.filters.year || !/^\d{4}$/.test(this.filters.year)) this.filters.year = String(yyyy)
            }
        },
        tagTypeForDelta(v) {
            const n = Number(v || 0)
            if (n > 0) return 'success'
            if (n < 0) return 'danger'
            return 'info'
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
.stats {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
}
.stats .divider {
    opacity: 0.6;
}
.stats-card {
  border: none;
  border-radius: 12px;
}

.stats-card .stats-title {
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 6px;
}

.stats-line {
  margin-top: 4px;
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.tag-list {
  display: inline-flex;
  gap: 6px;
  flex-wrap: wrap;
}

/* 入库/出库卡片的柔和底色 */
.stats-card.inbound {
  background: #f0f9eb; /* 绿底 */
}
.stats-card.outbound {
  background: #fef0f0; /* 红底 */
}

/* 净值卡片：底色随正负动态变化（默认蓝，负值橙） */
.stats-card.net {
  background: #ecf5ff; /* 默认蓝底（正/零） */
  transition: background 0.2s ease;
}
.stats-card.net-neg {
  background: #fdf6ec; /* 负值橙底 */
}

/* 数量正负色 */
.pos { color: #67c23a; }  /* green-500 */
.neg { color: #f56c6c; }  /* red-500 */
</style>
