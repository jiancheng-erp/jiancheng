<template>
    <div>
        <el-card shadow="never" class="mb-2">
            <el-form :inline="true" @submit.prevent>
                <el-form-item label="数据模式">
                    <el-radio-group v-model="queryMode" @change="refreshAndFetch">
                        <el-radio-button label="realtime">实时库存</el-radio-button>
                        <el-radio-button label="history">历史库存</el-radio-button>
                    </el-radio-group>
                </el-form-item>

                <el-form-item v-if="queryMode === 'history'" label="时间区间">
                    <el-date-picker
                        v-model="filters.dateRange"
                        type="daterange"
                        range-separator="至"
                        start-placeholder="开始日期"
                        end-placeholder="结束日期"
                        value-format="YYYY-MM-DD"
                        :disabled-date="disableAfterToday"
                        @change="refresh"
                    />
                </el-form-item>

                <el-form-item label="工厂型号">
                    <el-input v-model="filters.shoeRId" placeholder="输入工厂型号" clearable style="width: 220px" />
                </el-form-item>

                <el-form-item label="仅显示有库存">
                    <el-switch v-model="filters.showOnlyInStock" @change="refresh" />
                </el-form-item>

                <el-form-item label="鞋类型">
                    <el-select v-model="filters.category" clearable placeholder="全部" @change="refresh" style="width: 140px">
                        <el-option label="男鞋" value="男鞋" />
                        <el-option label="女鞋" value="女鞋" />
                        <el-option label="童鞋" value="童鞋" />
                        <el-option label="其它" value="其它" />
                    </el-select>
                </el-form-item>

                <el-form-item>
                    <el-button type="primary" @click="refreshAndFetch">查询</el-button>
                    <el-button @click="reset">重置</el-button>
                    <el-dropdown @command="downloadExcel" :disabled="downloading">
                        <el-button :loading="downloading">
                            导出 Excel<el-icon class="el-icon--right"><arrow-down /></el-icon>
                        </el-button>
                        <template #dropdown>
                            <el-dropdown-menu>
                                <el-dropdown-item command="model">按型号汇总导出</el-dropdown-item>
                                <el-dropdown-item command="color">按颜色明细导出</el-dropdown-item>
                            </el-dropdown-menu>
                        </template>
                    </el-dropdown>
                </el-form-item>
            </el-form>
        </el-card>

        <el-alert :closable="false" type="info" :title="summaryTitle" show-icon class="mb-2" />

        <el-table :data="pagedModels" border stripe height="540">
            <el-table-column type="expand" width="50">
                <template #default="scope">
                    <el-table :data="scope.row.colors" border stripe size="small">
                        <el-table-column prop="colorName" label="颜色" />
                        <el-table-column v-if="queryMode === 'history'" prop="openingAmount" label="期初" />
                        <el-table-column v-if="queryMode === 'history'" prop="periodInbound" label="入库变化" />
                        <el-table-column v-if="queryMode === 'history'" prop="periodOutbound" label="出库变化" />
                        <el-table-column prop="currentAmount" :label="queryMode === 'history' ? '期末' : '当前库存'" />
                    </el-table>
                </template>
            </el-table-column>

            <el-table-column prop="shoeRId" label="工厂型号" />
            <el-table-column prop="batchType" label="类型" width="200" show-overflow-tooltip />
            <el-table-column prop="designersText" label="设计师" show-overflow-tooltip />

            <el-table-column v-if="queryMode === 'history'" prop="totalOpening" label="期初数" />
            <el-table-column v-if="queryMode === 'history'" prop="totalInbound" label="入库变化" />
            <el-table-column v-if="queryMode === 'history'" prop="totalOutbound" label="出库变化" />
            <el-table-column prop="totalCurrent" :label="queryMode === 'history' ? '期末数' : '当前库存总数'" />
        </el-table>

        <div class="mt-2">
            <el-pagination
                background
                layout="total, sizes, prev, pager, next, jumper"
                :total="filteredModels.length"
                :page-size="pageSize"
                :page-sizes="pageSizes"
                :current-page="currentPage"
                @size-change="onSizeChange"
                @current-change="onPageChange"
            />
        </div>
    </div>
</template>

<script>
import axios from 'axios'
import { ArrowDown } from '@element-plus/icons-vue'

const DEFAULT_PAGE_SIZES = [10, 20, 30, 50]

const normalizeCategoryByBatchType = (name) => {
  const s = (name || '').trim()
  if (s.includes('男')) return '男鞋'
  if (s.includes('女')) return '女鞋'
  if (s.includes('童')) return '童鞋'
  return '其它'
}

export default {
    name: 'FinishedFactoryModelView_ByModel_ExpandColors',
    components: { ArrowDown },
    data() {
        return {
            queryMode: 'realtime',
            rawRows: [],
            modelMetaMap: {},
            downloading: false,
            filters: {
                shoeRId: '',
                showOnlyInStock: false,
                category: '',
                dateRange: []
            },
            currentPage: 1,
            pageSize: 20,
            pageSizes: DEFAULT_PAGE_SIZES
        }
    },
    computed: {
        filteredRows() {
            const { shoeRId, category } = this.filters
            return this.rawRows.filter((r) => {
                const okShoe = shoeRId
                    ? String(r.shoeRId || '').toLowerCase().includes(shoeRId.toLowerCase())
                    : true
                const rowCat = normalizeCategoryByBatchType(r.batchType)
                const okCat = category ? rowCat === category : true
                return okShoe && okCat
            })
        },

        groupedByShoeRId() {
            const map = new Map()
            for (const r of this.filteredRows) {
                const key = r.shoeRId || '-'
                if (!map.has(key)) {
                    map.set(key, {
                        shoeRId: key,
                        batchType: r.batchType || '-',
                        totalOpening: 0,
                        totalInbound: 0,
                        totalOutbound: 0,
                        totalCurrent: 0,
                        designers: new Set(),
                        colorMap: new Map(),
                        _flags: { man: false, woman: false, kid: false }
                    })
                }
                const agg = map.get(key)
                const opening = Number(r.openingAmount || 0)
                const inbound = Number(r.periodInbound || 0)
                const outbound = Number(r.periodOutbound || 0)
                const current = Number(r.currentAmount || 0)

                agg.totalOpening += opening
                agg.totalInbound += inbound
                agg.totalOutbound += outbound
                agg.totalCurrent += current

                if (r.designer && String(r.designer).trim() !== '') {
                    agg.designers.add(r.designer)
                }

                const colorKey = r.colorName || '-'
                if (!agg.colorMap.has(colorKey)) {
                    agg.colorMap.set(colorKey, {
                        colorName: colorKey,
                        openingAmount: 0,
                        periodInbound: 0,
                        periodOutbound: 0,
                        currentAmount: 0
                    })
                }
                const colorAgg = agg.colorMap.get(colorKey)
                colorAgg.openingAmount += opening
                colorAgg.periodInbound += inbound
                colorAgg.periodOutbound += outbound
                colorAgg.currentAmount += current

                const cat = normalizeCategoryByBatchType(r.batchType)
                if (cat === '男鞋') agg._flags.man = true
                else if (cat === '女鞋') agg._flags.woman = true
                else if (cat === '童鞋') agg._flags.kid = true
            }

            const arr = []
            for (const [, v] of map) {
                let category = '其它'
                if (v._flags.man) category = '男鞋'
                else if (v._flags.woman) category = '女鞋'
                else if (v._flags.kid) category = '童鞋'

                arr.push({
                    shoeRId: v.shoeRId,
                    batchType: v.batchType,
                    category,
                    totalOpening: v.totalOpening,
                    totalInbound: v.totalInbound,
                    totalOutbound: v.totalOutbound,
                    totalCurrent: v.totalCurrent,
                    designersText: Array.from(v.designers).join('、') || '-',
                    colors: Array.from(v.colorMap.values())
                })
            }
            arr.sort((a, b) => String(a.shoeRId).localeCompare(String(b.shoeRId)))
            return arr
        },

        filteredModels() {
            const list = this.groupedByShoeRId
            if (!this.filters.showOnlyInStock) return list
            return list.filter((x) => Number(x.totalCurrent) > 0)
        },

        totals() {
            return this.filteredModels.reduce(
                (acc, row) => {
                    acc.opening += Number(row.totalOpening || 0)
                    acc.inbound += Number(row.totalInbound || 0)
                    acc.outbound += Number(row.totalOutbound || 0)
                    acc.current += Number(row.totalCurrent || 0)
                    return acc
                },
                { opening: 0, inbound: 0, outbound: 0, current: 0 }
            )
        },

        summaryTitle() {
            if (this.queryMode === 'history') {
                return `型号总数：${this.filteredModels.length} | 期初：${this.totals.opening} | 入库变化：+${this.totals.inbound} | 出库变化：-${this.totals.outbound} | 期末：${this.totals.current}`
            }
            return `型号总数：${this.filteredModels.length} | 当前库存合计：${this.totals.current}`
        },

        pagedModels() {
            const start = (this.currentPage - 1) * this.pageSize
            return this.filteredModels.slice(start, start + this.pageSize)
        },
    },
    async mounted() {
        this.initDefaultRange()
        await this.fetchModelMeta()
        await this.fetchRows()
    },

    methods: {
        initDefaultRange() {
            const end = new Date()
            end.setDate(end.getDate() - 1)
            const start = new Date(end)
            start.setMonth(start.getMonth() - 3)
            this.filters.dateRange = [this.formatDate(start), this.formatDate(end)]
        },

        formatDate(d) {
            const y = d.getFullYear()
            const m = String(d.getMonth() + 1).padStart(2, '0')
            const day = String(d.getDate()).padStart(2, '0')
            return `${y}-${m}-${day}`
        },

        disableAfterToday(date) {
            const endToday = new Date()
            endToday.setHours(23, 59, 59, 999)
            return date.getTime() > endToday.getTime()
        },

        async fetchModelMeta() {
            const params = {
                page: 1,
                pageSize: 100000,
                showAll: 0
            }
            const resp = await axios.get(`${this.$apiBaseUrl}/warehouse/getfinishedstorages`, { params })
            const rows = resp.data && resp.data.result ? resp.data.result : []
            const map = {}
            for (const r of rows) {
                const key = r.shoeRId || '-'
                if (!map[key]) {
                    map[key] = { batchTypes: new Set(), designers: new Set() }
                }
                if (r.batchType) map[key].batchTypes.add(r.batchType)
                if (r.designer) map[key].designers.add(r.designer)
            }
            this.modelMetaMap = map
        },

        async fetchRows() {
            if (this.queryMode === 'history') {
                const [startDate, endDate] = this.filters.dateRange || []
                if (!startDate || !endDate) {
                    this.rawRows = []
                    this.currentPage = 1
                    return
                }
                const params = {
                    page: 1,
                    pageSize: 100000,
                    startDate,
                    endDate,
                    orderRId: undefined,
                    shoeRId: this.filters.shoeRId || undefined,
                    customerName: undefined,
                    customerBrand: undefined,
                    colorName: undefined,
                    displayZeroInventory: this.filters.showOnlyInStock
                }
                const resp = await axios.get(`${this.$apiBaseUrl}/warehouse/getfinishedinventoryperiod`, { params })
                const rows = resp.data?.data?.items || []
                this.rawRows = rows.map((r) => {
                    const meta = this.modelMetaMap[r.shoeRId] || { batchTypes: new Set(), designers: new Set() }
                    return {
                        shoeRId: r.shoeRId,
                        colorName: r.colorName,
                        batchType: Array.from(meta.batchTypes).join('、') || '-',
                        designer: Array.from(meta.designers).join('、') || '-',
                        openingAmount: Number(r.openingAmount || 0),
                        periodInbound: Number(r.periodInbound || 0),
                        periodOutbound: Number(r.periodOutbound || 0),
                        currentAmount: Number(r.closingAmount || 0)
                    }
                })
            } else {
                const params = {
                    page: 1,
                    pageSize: 100000,
                    showAll: 0,
                    shoeRId: this.filters.shoeRId || undefined,
                    category: this.filters.category || undefined
                }
                const resp = await axios.get(`${this.$apiBaseUrl}/warehouse/getfinishedstorages`, { params })
                this.rawRows = (resp.data && resp.data.result ? resp.data.result : []).map((r) => ({
                    shoeRId: r.shoeRId,
                    colorName: r.colorName,
                    batchType: r.batchType,
                    designer: r.designer,
                    openingAmount: 0,
                    periodInbound: 0,
                    periodOutbound: 0,
                    currentAmount: Number(r.currentAmount || 0)
                }))
            }
            this.currentPage = 1
        },

        refresh() {
            this.currentPage = 1
        },

        async refreshAndFetch() {
            this.currentPage = 1
            await this.fetchRows()
        },

        async reset() {
            this.filters.shoeRId = ''
            this.filters.showOnlyInStock = false
            this.filters.category = ''
            this.initDefaultRange()
            this.currentPage = 1
            await this.fetchRows()
        },

        onSizeChange(v) {
            this.pageSize = v
            this.currentPage = 1
        },

        onPageChange(v) {
            this.currentPage = v
        },

        async downloadExcel(mode) {
            const groupByModel = mode === 'model'
            this.downloading = true
            try {
                let url, params
                if (this.queryMode === 'history') {
                    const [startDate, endDate] = this.filters.dateRange || []
                    if (!startDate || !endDate) {
                        this.$message.warning('请先选择时间区间')
                        this.downloading = false
                        return
                    }
                    url = `${this.$apiBaseUrl}/warehouse/export/finished-inventory-period`
                    params = {
                        startDate,
                        endDate,
                        shoeRId: this.filters.shoeRId || undefined,
                        displayZeroInventory: this.filters.showOnlyInStock,
                        groupByModel,
                    }
                } else {
                    url = `${this.$apiBaseUrl}/warehouse/export/finished-inventory-history`
                    params = {
                        snapshotDate: new Date().toISOString().split('T')[0],
                        shoeRId: this.filters.shoeRId || undefined,
                        displayZeroInventory: !this.filters.showOnlyInStock,
                        groupByModel,
                    }
                }
                const res = await axios.get(url, { params, responseType: 'blob' })
                const blob = new Blob([res.data], { type: res.headers['content-type'] })
                const disposition = res.headers['content-disposition']
                let filename = '成品仓库存.xlsx'
                if (disposition && disposition.includes('filename=')) {
                    const match = disposition.match(/filename="?(.+?)"?$/)
                    if (match && match[1]) filename = decodeURIComponent(match[1])
                }
                const link = document.createElement('a')
                link.href = URL.createObjectURL(blob)
                link.download = filename
                document.body.appendChild(link)
                link.click()
                document.body.removeChild(link)
                URL.revokeObjectURL(link.href)
            } catch (err) {
                const msg = err?.response?.data?.message || '导出失败'
                this.$message.error(msg)
            } finally {
                this.downloading = false
            }
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
