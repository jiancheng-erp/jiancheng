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

                <el-form-item v-if="filters.mode === 'month'" label="月份">
                    <el-date-picker v-model="filters.month" type="month" format="YYYY-MM" value-format="YYYY-MM" :editable="false" :clearable="false" @change="refresh" />
                </el-form-item>
                <el-form-item v-else label="年份">
                    <el-date-picker v-model="filters.year" type="year" format="YYYY" value-format="YYYY" :editable="false" :clearable="false" @change="refresh" />
                </el-form-item>

                <el-form-item label="方向">
                    <el-select v-model="filters.direction" clearable placeholder="全部" @change="refresh" style="width: 120px">
                        <el-option label="入库" :value="'IN'" />
                        <el-option label="出库" :value="'OUT'" />
                    </el-select>
                </el-form-item>

                <el-form-item label="业务单号">
                    <el-input v-model="filters.keyword" placeholder="rid 模糊" clearable style="width: 200px" @keyup.enter.native="refresh" />
                </el-form-item>

                <el-form-item label="工厂型号">
                    <el-input v-model="filters.shoeRid" placeholder="型号" clearable style="width: 180px" @keyup.enter.native="refresh" />
                </el-form-item>

                <el-form-item label="颜色">
                    <el-input v-model="filters.color" placeholder="颜色" clearable style="width: 140px" @keyup.enter.native="refresh" />
                </el-form-item>
                <el-form-item label="鞋类型">
                    <el-select v-model="filters.category" clearable placeholder="全部" @change="refresh" style="width: 140px">
                        <el-option label="全部" value="" />
                        <el-option label="男鞋" value="男鞋" />
                        <el-option label="女鞋" value="女鞋" />
                        <el-option label="童鞋" value="童鞋" />
                        <el-option label="其它" value="其它" />
                    </el-select>
                </el-form-item>
                <el-form-item label="分组">
                    <el-select v-model="filters.groupBy" style="width: 160px" @change="refresh">
                        <el-option label="按型号" value="model" />
                        <el-option label="按型号+颜色" value="model_color" />
                    </el-select>
                </el-form-item>

                <el-form-item>
                    <el-button type="primary" @click="refresh">查询</el-button>
                    <el-button @click="reset">重置</el-button>
                    <el-button type="success" :loading="exportLoading" @click="exportExcel">导出Excel</el-button>
                </el-form-item>
            </el-form>
        </el-card>

        <!-- 顶部统计（沿用三卡片样式） -->
        <el-row :gutter="12" class="mb-2">
            <el-col :xs="24" :sm="8">
                <el-card shadow="never" class="stats-card inbound">
                    <div class="stats-title">入库</div>
                    <div class="stats-line">
                        数量 <b>{{ fmtNumber(stat.inQty) }}</b>
                    </div>
                    <div class="stats-line">
                        金额
                        <span class="tag-list">
                            <el-tag v-for="(val, cur) in stat.inAmountByCurrency" :key="'in-' + cur" size="small" type="success" effect="dark"> {{ cur }} {{ fmtMoney(val) }} </el-tag>
                        </span>
                    </div>
                </el-card>
            </el-col>
            <el-col :xs="24" :sm="8">
                <el-card shadow="never" class="stats-card outbound">
                    <div class="stats-title">出库</div>
                    <div class="stats-line">
                        数量 <b>{{ fmtNumber(stat.outQty) }}</b>
                    </div>
                    <div class="stats-line">
                        金额
                        <span class="tag-list">
                            <el-tag v-for="(val, cur) in stat.outAmountByCurrency" :key="'out-' + cur" size="small" type="danger" effect="dark"> {{ cur }} {{ fmtMoney(val) }} </el-tag>
                        </span>
                    </div>
                </el-card>
            </el-col>
            <el-col :xs="24" :sm="8">
                <el-card shadow="never" class="stats-card net" :class="{ 'net-neg': stat.netQty < 0 }">
                    <div class="stats-title">库存</div>
                    <div class="stats-line">
                        期初 <b>{{ fmtNumber(stat.openingQty) }}</b>
                    </div>
                    <div class="stats-line">
                        结存 <b>{{ fmtNumber(stat.closingQty) }}</b>
                    </div>
                    <div class="stats-line">
                        净变动 <b :class="{ pos: stat.netQty >= 0, neg: stat.netQty < 0 }">{{ fmtNumber(stat.netQty) }}</b>
                    </div>
                    <div class="stats-line">
                        净金额
                        <span class="tag-list">
                            <el-tag v-for="(val, cur) in stat.netAmountByCurrency" :key="'net-' + cur" size="small" :type="val > 0 ? 'success' : val < 0 ? 'danger' : 'info'" effect="dark">
                                {{ cur }} {{ fmtMoney(val) }}
                            </el-tag>
                        </span>
                    </div>
                </el-card>
            </el-col>
        </el-row>

        <!-- 表格：每行一个型号（或 型号+颜色） -->
        <el-table :data="rows" border stripe height="560" v-loading="loading">
            <el-table-column prop="shoeRid" label="工厂型号" width="220" show-overflow-tooltip />
            <el-table-column prop="category" label="类型" width="100" show-overflow-tooltip />
            <el-table-column v-if="filters.groupBy === 'model_color'" prop="color" label="颜色" width="160" show-overflow-tooltip />
            <el-table-column prop="designer" label="设计师" show-overflow-tooltip />
            <el-table-column prop="adjuster" label="调版师" show-overflow-tooltip />
            <el-table-column prop="openingQty" label="期初数量" width="120">
                <template #default="{ row }">
                    {{ fmtNumber(row.openingQty) }}
                </template>
            </el-table-column>
            <el-table-column prop="inQty" label="入库数量" width="120" />
            <el-table-column prop="outQty" label="出库数量" width="120" />
            <el-table-column prop="netQty" label="净变动" width="120">
                <template #default="{ row }">
                    <span :class="{ pos: row.netQty >= 0, neg: row.netQty < 0 }">{{ fmtNumber(row.netQty) }}</span>
                </template>
            </el-table-column>
            <el-table-column prop="closingQty" label="结存数量" width="120">
                <template #default="{ row }">
                    {{ fmtNumber(row.closingQty) }}
                </template>
            </el-table-column>
            <el-table-column prop="unitPrice" label="单价" width="120">
                <template #default="{ row }">
                    {{ fmtMoney(row.unitPrice) }}
                </template>
            </el-table-column>
            <el-table-column label="入库金额（分币种）" min-width="220">
                <template #default="{ row }">
                    <el-tag v-for="(v, k) in row.inAmountByCurrency" :key="'ri-' + row.shoeRid + '-' + k" size="small" type="success" effect="plain"> {{ k }} {{ fmtMoney(v) }} </el-tag>
                </template>
            </el-table-column>
            <el-table-column label="出库金额（分币种）" min-width="220">
                <template #default="{ row }">
                    <el-tag v-for="(v, k) in row.outAmountByCurrency" :key="'ro-' + row.shoeRid + '-' + k" size="small" type="danger" effect="plain"> {{ k }} {{ fmtMoney(v) }} </el-tag>
                </template>
            </el-table-column>
            <el-table-column label="净额（分币种）" min-width="220">
                <template #default="{ row }">
                    <el-tag v-for="(v, k) in row.netAmountByCurrency" :key="'rn-' + row.shoeRid + '-' + k" size="small" :type="v > 0 ? 'success' : v < 0 ? 'danger' : 'info'" effect="plain">
                        {{ k }} {{ fmtMoney(v) }}
                    </el-tag>
                </template>
            </el-table-column>
        </el-table>

        <div class="mt-2">
            <el-pagination
                background
                layout="total, sizes, prev, pager, next, jumper"
                :total="page.total"
                :page-size="page.pageSize"
                :page-sizes="[10, 20, 30, 50]"
                :current-page="page.currentPage"
                @size-change="onSizeChange"
                @current-change="onPageChange"
            />
        </div>
    </div>
</template>

<script>
import axios from 'axios'
import { ElMessage } from 'element-plus'

const createEmptyStat = () => ({
    openingQty: 0,
    closingQty: 0,
    inQty: 0,
    outQty: 0,
    netQty: 0,
    inAmountByCurrency: {},
    outAmountByCurrency: {},
    netAmountByCurrency: {},
    openingAmountByCurrency: {},
    closingAmountByCurrency: {}
})

export default {
    name: 'FinishedStorageSummaryByModel',
    data() {
        const now = new Date()
        const yyyy = String(now.getFullYear())
        const mm = String(now.getMonth() + 1).padStart(2, '0')
        return {
            filters: {
                mode: 'month',
                month: `${yyyy}-${mm}`,
                year: yyyy,
                direction: '',
                keyword: '',
                shoeRid: '',
                color: '',
                groupBy: 'model',
                category: '' // ← 新增：男鞋/女鞋/童鞋/其它（空=全部）
            },
            rows: [],
            stat: createEmptyStat(),
            page: { total: 0, currentPage: 1, pageSize: 20 },
            loading: false,
            exportLoading: false
        }
    },
    mounted() {
        this.fetchData()
    },
    methods: {
        buildQueryParams(includePaging = true) {
            const params = {
                mode: this.filters.mode,
                groupBy: this.filters.groupBy
            }
            if (this.filters.mode === 'month') {
                params.month = this.filters.month
            } else {
                params.year = this.filters.year
            }
            if (includePaging) {
                params.page = this.page.currentPage
                params.pageSize = this.page.pageSize
            }
            if (this.filters.direction) {
                params.direction = this.filters.direction
            }
            if (this.filters.keyword?.trim()) {
                params.keyword = this.filters.keyword.trim()
            }
            if (this.filters.shoeRid?.trim()) {
                params.shoeRid = this.filters.shoeRid.trim()
            }
            if (this.filters.color?.trim()) {
                params.color = this.filters.color.trim()
            }
            if (this.filters.category) {
                params.category = this.filters.category
            }
            return params
        },
        async fetchData() {
            this.loading = true
            try {
                const p = this.buildQueryParams(true)
                const resp = await axios.get(`${this.$apiBaseUrl}/warehouse/getshoeinoutboundsummarybymodel`, { params: p })
                const data = resp?.data || {}
                this.rows = Array.isArray(data.list) ? data.list : []
                this.page.total = Number(data.total || 0)
                this.stat = { ...createEmptyStat(), ...(data.stat || {}) }
            } finally {
                this.loading = false
            }
        },
        async exportExcel() {
            if (this.exportLoading) {
                return
            }
            this.exportLoading = true
            try {
                const params = this.buildQueryParams(false)
                const res = await axios.get(
                    `${this.$apiBaseUrl}/warehouse/export/shoeinoutsummarybymodel`,
                    { params, responseType: 'blob' }
                )
                let filename = '成品仓库存出入库明细.xlsx'
                const disposition = res.headers['content-disposition'] || res.headers['Content-Disposition']
                if (disposition) {
                    const match = disposition.match(/filename\*=UTF-8''(.+)|filename="?([^";]+)"?/)
                    if (match) {
                        filename = decodeURIComponent(match[1] || match[2])
                    }
                }
                const blob = new Blob([res.data], {
                    type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                })
                const link = document.createElement('a')
                link.href = URL.createObjectURL(blob)
                link.download = filename
                document.body.appendChild(link)
                link.click()
                URL.revokeObjectURL(link.href)
                document.body.removeChild(link)
                ElMessage.success('导出成功')
            } catch (error) {
                console.error(error)
                const message = error?.response?.data?.message || '导出失败'
                ElMessage.error(message)
            } finally {
                this.exportLoading = false
            }
        },
        refresh() {
            this.page.currentPage = 1
            this.fetchData()
        },
        reset() {
            const now = new Date()
            const yyyy = String(now.getFullYear())
            const mm = String(now.getMonth() + 1).padStart(2, '0')
            this.filters = {
                mode: 'month',
                month: `${yyyy}-${mm}`,
                year: yyyy,
                direction: '',
                keyword: '',
                shoeRid: '',
                color: '',
                groupBy: 'model',
                category: '' // ← 新增
            }
            this.page.currentPage = 1
            this.page.pageSize = 20
            this.fetchData()
        },
        onModeChange() {
            const now = new Date()
            const yyyy = String(now.getFullYear())
            const mm = String(now.getMonth() + 1).padStart(2, '0')
            if (this.filters.mode === 'month') {
                this.filters.month = `${yyyy}-${mm}`
            } else {
                this.filters.year = yyyy
            }
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
        // utils
        fmtMoney(n) {
            const v = Number(n || 0)
            return v.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })
        },
        fmtNumber(n) {
            const v = Number(n || 0)
            return v.toLocaleString()
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
.stats-card {
    border: none;
    border-radius: 12px;
}
.stats-card.inbound {
    background: #f0f9eb;
}
.stats-card.outbound {
    background: #fef0f0;
}
.stats-card.net {
    background: #ecf5ff;
}
.stats-card.net.net-neg {
    background: #fdf6ec;
}
.pos {
    color: #67c23a;
}
.neg {
    color: #f56c6c;
}
.tag-list {
    display: inline-flex;
    gap: 6px;
    flex-wrap: wrap;
}
.stats-title {
    font-weight: 600;
    margin-bottom: 6px;
}
.stats-line {
    margin-top: 4px;
    display: flex;
    gap: 6px;
    align-items: center;
    flex-wrap: wrap;
}
</style>
