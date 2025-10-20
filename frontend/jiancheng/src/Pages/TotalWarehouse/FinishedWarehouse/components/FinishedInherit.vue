<template>
    <div>
        <!-- 筛选 -->
        <el-card shadow="never" class="mb-2">
            <el-form :inline="true" @submit.native.prevent>
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
                    <el-button type="primary" @click="refresh">查询</el-button>
                    <el-button @click="reset">重置</el-button>
                </el-form-item>
            </el-form>
        </el-card>

        <!-- 顶部统计 -->
        <el-alert :closable="false" type="info" :title="`型号总数：${filteredModels.length} | 当前库存合计：${sumCurrent}`" show-icon class="mb-2" />

        <!-- 主表 -->
        <el-table :data="pagedModels" border stripe height="540">
            <!-- 展开：颜色与库存 -->
            <el-table-column type="expand" width="50">
                <template #default="scope">
                    <el-table :data="scope.row.colors" border stripe size="small">
                        <el-table-column prop="colorName" label="颜色" />
                        <el-table-column prop="currentAmount" label="当前库存" />
                    </el-table>
                </template>
            </el-table-column>

            <el-table-column prop="shoeRId" label="工厂型号" />
            <el-table-column prop="batchType" label="类型" width="200" show-overflow-tooltip />
            <el-table-column prop="designersText" label="设计师" show-overflow-tooltip />
            <el-table-column prop="totalCurrent" label="当前库存总数" />
        </el-table>

        <!-- 分页 -->
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
    data() {
        return {
            rawRows: [], // /warehouse/getfinishedstorages 明细
            filters: {
                shoeRId: '',
                showOnlyInStock: false,
                category: '' // ← 新增：男鞋/女鞋/童鞋/其它（空=全部）
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
                    ? String(r.shoeRId || '')
                          .toLowerCase()
                          .includes(shoeRId.toLowerCase())
                    : true

                // 按类别筛选（来源 r.batchType）
                const rowCat = normalizeCategoryByBatchType(r.batchType)
                const okCat = category ? rowCat === category : true

                return okShoe && okCat
            })
        },

        // 聚合：型号维度；保留设计师；颜色放到 expand
        groupedByShoeRId() {
            const map = new Map()
            for (const r of this.filteredRows) {
                const key = r.shoeRId || '-'
                if (!map.has(key)) {
                    map.set(key, {
                        shoeRId: key,
                        batchType: r.batchType || '-', // 原始文本仍保留（如需显示）
                        totalCurrent: 0,
                        designers: new Set(),
                        colorMap: new Map(), // color -> { colorName, currentAmount }
                        _flags: { man: false, woman: false, kid: false } // 类别标志
                    })
                }
                const agg = map.get(key)

                // 累加库存
                const current = Number(r.currentAmount || 0)
                agg.totalCurrent += current

                // 设计师
                if (r.designer && String(r.designer).trim() !== '') {
                    agg.designers.add(r.designer)
                }

                // 颜色 -> 当前库存
                const colorKey = r.colorName || '-'
                if (!agg.colorMap.has(colorKey)) {
                    agg.colorMap.set(colorKey, { colorName: colorKey, currentAmount: 0 })
                }
                agg.colorMap.get(colorKey).currentAmount += current

                // 类别标志（基于 batchType）
                const cat = normalizeCategoryByBatchType(r.batchType)
                if (cat === '男鞋') agg._flags.man = true
                else if (cat === '女鞋') agg._flags.woman = true
                else if (cat === '童鞋') agg._flags.kid = true
            }

            const arr = []
            for (const [, v] of map) {
                // 统一类别：若型号下多种类别，按男>女>童>其它 优先
                let category = '其它'
                if (v._flags.man) category = '男鞋'
                else if (v._flags.woman) category = '女鞋'
                else if (v._flags.kid) category = '童鞋'

                arr.push({
                    shoeRId: v.shoeRId,
                    batchType: v.batchType,
                    category, // ← 新增：展示用
                    totalCurrent: v.totalCurrent,
                    designersText: Array.from(v.designers).join('、') || '-',
                    colors: Array.from(v.colorMap.values())
                })
            }
            // 默认按型号排序
            arr.sort((a, b) => String(a.shoeRId).localeCompare(String(b.shoeRId)))
            return arr
        },

        // 应用“仅显示有库存”开关
        filteredModels() {
            const list = this.groupedByShoeRId
            if (this.filters.showOnlyInStock) {
                return list.filter((x) => Number(x.totalCurrent) > 0)
            }
            return list
        },

        // 顶部合计（对聚合后的行再合计）
        sumCurrent() {
            return this.filteredModels.reduce((sum, row) => sum + Number(row.totalCurrent || 0), 0)
        },

        // 分页
        pagedModels() {
            const start = (this.currentPage - 1) * this.pageSize
            return this.filteredModels.slice(start, start + this.pageSize)
        },
    },
    async mounted() {
        await this.fetchRows()
    },
    
    methods: {
        async fetchRows() {
            // 拉全量明细，前端聚合；如数据量过大可改为后端按型号聚合接口
            const params = {
                page: 1,
                pageSize: 100000,
                showAll: 0 // 包含未完成
            }
            const resp = await axios.get(`${this.$apiBaseUrl}/warehouse/getfinishedstorages`, { params })
            this.rawRows = resp.data && resp.data.result ? resp.data.result : []
            this.currentPage = 1
        },

        refresh() {
            this.currentPage = 1
        },

        reset() {
            this.filters.shoeRId = ''
            this.filters.showOnlyInStock = false
            this.filters.category = '' // ← 新增
            this.currentPage = 1
        },
        onSizeChange(v) {
            this.pageSize = v
            this.currentPage = 1
        },

        onPageChange(v) {
            this.currentPage = v
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
