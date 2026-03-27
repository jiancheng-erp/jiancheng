<template>
    <el-row :gutter="20">
        <el-col>
            <FinishedSearchBar :search-filters="searchFilters" @confirm="confirmSearchFilters" />
        </el-col>
    </el-row>

    <el-tabs v-model="activeTab" class="outbound-tabs">
        <el-tab-pane label="出库详情" name="detail">
            <el-row :gutter="20">
                <el-col :span="24">
                    <el-table
                        :data="pagedOutboundList"
                        border
                        stripe
                        style="height: 60vh;"
                    >
                        <el-table-column label="明细" width="80" fixed="left">
                            <template #default="{ row }">
                                <el-button type="primary" link size="small" @click="openOutboundDetailDialog(row)">查看</el-button>
                            </template>
                        </el-table-column>
                        <el-table-column prop="outboundRId" label="出库单号"/>
                        <el-table-column prop="timestamp" label="操作时间"/>
                        <el-table-column label="客户名称" min-width="160">
                            <template #default="{ row }">
                                <span>{{ row.customerName }}</span>
                                <el-tooltip v-if="row.allCustomerNames" placement="top" :teleported="false">
                                    <template #content>
                                        <div>涉及客户：{{ row.allCustomerNames }}</div>
                                        <div v-if="row.allOrderRIds">涉及订单：{{ row.allOrderRIds }}</div>
                                        <div v-if="row.allShoeRIds">涉及鞋型：{{ row.allShoeRIds }}</div>
                                    </template>
                                    <el-tag size="small" type="warning" style="margin-left:4px">多客户</el-tag>
                                </el-tooltip>
                            </template>
                        </el-table-column>
                        <el-table-column
                            prop="ordersCount"
                            label="订单数量"
                            width="100"
                        />
                        <el-table-column
                            prop="shoesCount"
                            label="鞋型数量"
                            width="100"
                        />
                        <el-table-column
                            prop="totalAmount"
                            label="总数量（双）"
                            width="140"
                        />
                        <el-table-column label="操作" width="160">
                            <template #default="{ row }">
                                <el-button type="primary" size="small" @click="downloadOutboundList(row)">
                                    下载出库清单
                                </el-button>
                            </template>
                        </el-table-column>
                    </el-table>
                </el-col>
            </el-row>

            <el-row :gutter="20">
                <el-col>
                    <el-pagination
                        @size-change="handleSizeChange"
                        @current-change="handlePageChange"
                        :current-page="currentPage"
                        :page-sizes="pageSizes"
                        :page-size="pageSize"
                        layout="total, sizes, prev, pager, next, jumper"
                        :total="groupedTotal"
                    />
                </el-col>
            </el-row>
        </el-tab-pane>

        <el-tab-pane label="出库申请下载" name="apply">
            <div class="apply-search-bar">
                <el-form inline @submit.prevent>
                    <el-form-item label="申请单号">
                        <el-input
                            v-model="applySearch.applyRId"
                            placeholder="请输入申请单号"
                            style="width: 240px;"
                            clearable
                            @keyup.enter="getApplyList"
                        />
                    </el-form-item>
                    <el-form-item label="订单号">
                        <el-input
                            v-model="applySearch.orderRId"
                            placeholder="请输入订单号"
                            style="width: 200px;"
                            clearable
                            @keyup.enter="getApplyList"
                        />
                    </el-form-item>
                    <el-form-item label="客户名称">
                        <el-input
                            v-model="applySearch.customerName"
                            placeholder="请输入客户名称"
                            style="width: 200px;"
                            clearable
                            @keyup.enter="getApplyList"
                        />
                    </el-form-item>
                    <el-form-item label="状态">
                        <el-select
                            v-model="applySearch.status"
                            placeholder="全部"
                            style="width: 160px;"
                            clearable
                            @change="getApplyList"
                        >
                            <el-option label="全部" :value="null" />
                            <el-option
                                v-for="item in applyStatusOptions"
                                :key="item.value"
                                :label="item.label"
                                :value="item.value"
                            />
                        </el-select>
                    </el-form-item>
                    <el-form-item>
                        <el-button type="primary" @click="getApplyList">查询</el-button>
                        <el-button @click="resetApplySearch">重置</el-button>
                    </el-form-item>
                </el-form>
            </div>

            <el-row :gutter="20">
                <el-col :span="24">
                    <el-table
                        :data="pagedApplyList"
                        border
                        stripe
                        height="60vh"
                        :loading="applyLoading"
                        :empty-text="applyDownloadList.length ? '本页暂无申请单' : '暂无申请单'"
                    >
                        <el-table-column label="明细" width="80" fixed="left">
                            <template #default="{ row }">
                                <el-button type="primary" link size="small" @click="openApplyDetailDialog(row)">查看</el-button>
                            </template>
                        </el-table-column>
                        <el-table-column prop="applyRId" label="申请单号" width="180"/>
                        <el-table-column prop="orderRId" label="订单号" width="180"/>
                        <el-table-column prop="orderCId" label="客户订单号" width="180"/>
                        <el-table-column label="客户名称" min-width="160">
                            <template #default="{ row }">
                                <span>{{ row.customerName }}</span>
                                <el-tooltip v-if="row.allCustomerNames && row.allCustomerNames !== row.customerName" placement="top" :teleported="false">
                                    <template #content>
                                        <div>涉及客户：{{ row.allCustomerNames }}</div>
                                        <div v-if="row.allOrderRIds">涉及订单：{{ row.allOrderRIds }}</div>
                                    </template>
                                    <el-tag size="small" type="warning" style="margin-left:4px">多客户</el-tag>
                                </el-tooltip>
                            </template>
                        </el-table-column>
                        <el-table-column prop="statusLabel" label="状态" width="140"/>
                        <el-table-column prop="totalPairs" label="总数量（双）" width="140"/>
                        <el-table-column prop="timestamp" label="建单时间" width="190"/>
                        <el-table-column label="操作" width="160">
                            <template #default="{ row }">
                                <el-button
                                    type="success"
                                    size="small"
                                    plain
                                    @click="downloadOutboundApply({ applyIds: [row.applyId] })"
                                >
                                    下载出库申请
                                </el-button>
                            </template>
                        </el-table-column>
                    </el-table>
                </el-col>
            </el-row>

            <el-row :gutter="20">
                <el-col>
                    <el-pagination
                        @size-change="handleApplySizeChange"
                        @current-change="handleApplyPageChange"
                        :current-page="applyCurrentPage"
                        :page-sizes="applyPageSizes"
                        :page-size="applyPageSize"
                        layout="total, sizes, prev, pager, next, jumper"
                        :total="applyTotal"
                    />
                </el-col>
            </el-row>
        </el-tab-pane>
    </el-tabs>

    <!-- ===== PACKING LIST 明细对话框 ===== -->
    <el-dialog
        v-model="isDetailDialogVisible"
        :title="`出库明细 - ${detailDialogTitle}`"
        width="92%"
    >
        <el-descriptions :column="4" border size="small" style="margin-bottom: 12px">
            <el-descriptions-item label="订单号">{{ detailRow?.allOrderRIds || detailRow?.orderRId || '' }}</el-descriptions-item>
            <el-descriptions-item label="客户订单号">{{ detailRow?.allOrderCIds || detailRow?.orderCId || '' }}</el-descriptions-item>
            <el-descriptions-item label="客户名称">{{ detailRow?.allCustomerNames || detailRow?.customerName || '' }}</el-descriptions-item>
            <el-descriptions-item label="客户商标">{{ detailRow?.customerBrand || '' }}</el-descriptions-item>
        </el-descriptions>

        <!-- 无关联申请的旧出库单：显示简易明细表 -->
        <template v-if="isLegacyDetail">
            <el-table :data="detailRow?.details || []" border stripe size="small">
                <el-table-column prop="orderRId" label="订单号" />
                <el-table-column prop="orderCId" label="客户订单号" />
                <el-table-column prop="shoeRId" label="工厂鞋型" />
                <el-table-column prop="customerProductName" label="客户鞋型" />
                <el-table-column prop="customerBrand" label="客户商标" />
                <el-table-column prop="colorName" label="颜色" />
                <el-table-column prop="detailAmount" label="数量（双）" />
            </el-table>
        </template>

        <!-- 有关联申请的出库单：显示 PACKING LIST -->
        <template v-else>

        <el-table
            v-loading="detailLoading"
            :data="detailPageData"
            border
            stripe
            size="small"
            show-summary
            :summary-method="getDetailSummary"
        >
            <el-table-column label="起始箱号" prop="cNoStart" width="90" align="center" />
            <el-table-column label="截止箱号" prop="cNoEnd" width="90" align="center" />
            <el-table-column label="PO.NO. (工厂型号)" prop="shoeRId" min-width="130" />
            <el-table-column label="STYLE# (客户型号)" prop="customerProductName" min-width="140" />
            <el-table-column label="COLOR" prop="colorName" width="100" />
            <el-table-column label="配码名称" prop="batchName" min-width="110" />
            <el-table-column label="SIZE" align="center" v-if="detailSizeColumns.length > 0">
                <el-table-column
                    v-for="col in detailSizeColumns"
                    :key="col.label"
                    :label="col.label"
                    width="55"
                    align="center"
                >
                    <template #default="{ row }">{{ row.sizeRatios?.[col.label] || '' }}</template>
                </el-table-column>
            </el-table-column>
            <el-table-column label="PRS/Ctn" prop="pairsPerCarton" width="90" align="center" />
            <el-table-column label="CTNS" prop="cartonCount" width="80" align="center" />
            <el-table-column label="Units(prs)" prop="totalPairs" width="100" align="center" />
        </el-table>

        <el-pagination
            style="margin-top: 10px"
            @size-change="(s) => { detailPageSize = s; detailCurrentPage = 1 }"
            @current-change="(p) => { detailCurrentPage = p }"
            :current-page="detailCurrentPage"
            :page-sizes="[10, 20, 30, 50, 100]"
            :page-size="detailPageSize"
            layout="total, sizes, prev, pager, next"
            :total="detailPackingList.length"
        />
        </template>

        <template #footer>
            <el-button type="primary" @click="exportDetailPackingList" v-if="!isLegacyDetail">导出Excel</el-button>
            <el-button @click="isDetailDialogVisible = false">关闭</el-button>
        </template>
    </el-dialog>
</template>

<script>
import axios from 'axios'
import { ElMessage } from 'element-plus'
import { PAGESIZE, PAGESIZES, getSummaries } from '../../warehouseUtils'
import FinishedSearchBar from './FinishedSearchBar.vue'
import * as XLSX from 'xlsx'

export default {
    name: 'FinishedOutboundExpandView',
    components: {
        FinishedSearchBar
    },
    data() {
        return {
            currentPage: 1,
            pageSize: PAGESIZE,
            pageSizes: PAGESIZES,
            activeTab: 'detail',
            applyCurrentPage: 1,
            applyPageSize: PAGESIZE,
            applyPageSizes: PAGESIZES,
            applyRawList: [],
            applySearch: {
                applyRId: '',
                orderRId: '',
                customerName: '',
                status: null
            },
            applyStatusOptions: [
                { value: 0, label: '草稿' },
                { value: 1, label: '待总经理审核' },
                { value: 2, label: '总经理驳回' },
                { value: 3, label: '待仓库出库' },
                { value: 4, label: '已完成出库' },
                { value: 5, label: '已作废/取消' }
            ],
            applyLoading: false,
            rawTableData: [],
            searchFilters: {
                dateRange: [null, null],
                boundRIdSearch: null,
                orderRIdSearch: null,
                shoeRIdSearch: null,
                customerNameSearch: null,
                customerProductNameSearch: null,
                orderCIdSearch: null,
                customerBrandSearch: null
            },
            exportLoadingOutbound: false,
            exportLoadingInout: false,
            getSummaries: getSummaries,

            // PACKING LIST 明细对话框
            isDetailDialogVisible: false,
            detailRow: null,
            detailDialogTitle: '',
            detailLoading: false,
            detailSizeColumns: [],
            detailCurrentPage: 1,
            detailPageSize: 20,
            detailDetails: [],
            isLegacyDetail: false
        }
    },
    computed: {
        groupedOutboundList() {
            const map = new Map()

            this.rawTableData.forEach((item) => {
                const key = item.outboundRId
                if (!key) return

                if (!map.has(key)) {
                    map.set(key, {
                        outboundRId: item.outboundRId,
                        outboundId: item.outboundId,
                        timestamp: item.timestamp,
                        customerName: item.customerName,
                        totalAmount: Number(item.detailAmount) || 0,
                        ordersSet: new Set(item.orderRId ? [item.orderRId] : []),
                        shoesSet: new Set(item.shoeRId ? [item.shoeRId] : []),
                        customersSet: new Set(item.customerName ? [item.customerName] : []),
                        applyIds: new Set(item.applyId ? [item.applyId] : []),
                        details: [
                            {
                                orderRId: item.orderRId,
                                orderCId: item.orderCId,
                                shoeRId: item.shoeRId,
                                customerProductName: item.customerProductName,
                                customerBrand: item.customerBrand,
                                colorName: item.colorName,
                                detailAmount: Number(item.detailAmount) || 0
                            }
                        ]
                    })
                } else {
                    const rec = map.get(key)
                    rec.totalAmount += Number(item.detailAmount) || 0
                    if (item.orderRId) rec.ordersSet.add(item.orderRId)
                    if (item.shoeRId) rec.shoesSet.add(item.shoeRId)
                    if (item.customerName) rec.customersSet.add(item.customerName)
                    if (item.applyId) rec.applyIds.add(item.applyId)

                    rec.details.push({
                        orderRId: item.orderRId,
                        orderCId: item.orderCId,
                        shoeRId: item.shoeRId,
                        customerProductName: item.customerProductName,
                        customerBrand: item.customerBrand,
                        colorName: item.colorName,
                        detailAmount: Number(item.detailAmount) || 0
                    })
                }
            })

            // 把 Set 转成数量，组装最终数组
            return Array.from(map.values()).map((rec) => {
                const applyIds = Array.from(rec.applyIds)
                const allCustomers = Array.from(rec.customersSet)
                return {
                    outboundRId: rec.outboundRId,
                    outboundId: rec.outboundId,
                    timestamp: rec.timestamp,
                    customerName: rec.customerName,
                    allCustomerNames: allCustomers.length > 1 ? allCustomers.join('、') : '',
                    allOrderRIds: Array.from(rec.ordersSet).join('、'),
                    allShoeRIds: Array.from(rec.shoesSet).join('、'),
                    totalAmount: rec.totalAmount,
                    ordersCount: rec.ordersSet.size,
                    shoesCount: rec.shoesSet.size,
                    details: rec.details,
                    applyIds,
                    applyId: applyIds.length === 1 ? applyIds[0] : null
                }
            })
        },
        // 聚合后的总条数（出库单数量）
        groupedTotal() {
            return this.groupedOutboundList.length
        },
        // 针对“出库单”做前端分页
        pagedOutboundList() {
            const start = (this.currentPage - 1) * this.pageSize
            const end = start + this.pageSize
            return this.groupedOutboundList.slice(start, end)
        },
        applyDownloadList() {
            return this.applyRawList.map((item) => ({
                applyId: item.applyId,
                applyRId: item.applyRId,
                orderRId: item.orderRId,
                orderCId: item.orderCId,
                customerName: item.customerName,
                customerBrand: item.customerBrand,
                totalPairs: item.totalPairs,
                statusLabel: item.statusLabel,
                timestamp: item.createTime || item.updateTime,
                allCustomerNames: item.allCustomerNames,
                allOrderRIds: item.allOrderRIds,
                allShoeRIds: item.allShoeRIds
            }))
        },
        applyTotal() {
            return this.applyDownloadList.length
        },
        pagedApplyList() {
            const start = (this.applyCurrentPage - 1) * this.applyPageSize
            const end = start + this.applyPageSize
            return this.applyDownloadList.slice(start, end)
        },
        // PACKING LIST 明细（带起止箱号）
        detailPackingList() {
            const details = this.detailDetails
            if (!details.length) return []
            let cumulative = 0
            let prevStyle = null
            return details.map((d) => {
                const style = d.customerProductName || ''
                if (style !== prevStyle) {
                    cumulative = 0
                    prevStyle = style
                }
                const cartons = Math.ceil(Number(d.cartonCount || 0))
                const cNoStart = cumulative + 1
                cumulative += cartons
                return { ...d, cNoStart, cNoEnd: cumulative, cartonCount: cartons }
            })
        },
        detailPageData() {
            const start = (this.detailCurrentPage - 1) * this.detailPageSize
            return this.detailPackingList.slice(start, start + this.detailPageSize)
        }
    },
    mounted() {
        this.getOutboundRecords()
        this.getApplyList()
    },
    methods: {
        confirmSearchFilters(filters) {
            this.searchFilters = { ...filters }
            this.currentPage = 1
            this.getOutboundRecords()
        },

        async getOutboundRecords() {
            if (!this.searchFilters.dateRange) {
                this.searchFilters.dateRange = [null, null]
            }
            const [start, end] = this.searchFilters.dateRange

            try {
                // 不依赖后端分页，一次性取完当前筛选条件下的出库明细
                const params = {
                    page: 1,
                    pageSize: 100000, // 给一个足够大的值，避免漏数据
                    startDate: start,
                    endDate: end,
                    outboundRId: this.searchFilters.boundRIdSearch,
                    orderRId: this.searchFilters.orderRIdSearch,
                    shoeRId: this.searchFilters.shoeRIdSearch,
                    customerName: this.searchFilters.customerNameSearch,
                    customerProductName: this.searchFilters.customerProductNameSearch,
                    orderCId: this.searchFilters.orderCIdSearch,
                    customerBrand: this.searchFilters.customerBrandSearch
                }
                const res = await axios.get(`${this.$apiBaseUrl}/warehouse/getfinishedoutboundrecords`, {
                    params
                })
                this.rawTableData = res.data.result || []
                this.currentPage = 1
                this.applyCurrentPage = 1
            } catch (err) {
                console.error(err)
                ElMessage.error('获取出库记录失败')
            }
        },

        handleSizeChange(val) {
            this.pageSize = val
            this.currentPage = 1
        },
        handlePageChange(val) {
            this.currentPage = val
        },
        handleApplySizeChange(val) {
            this.applyPageSize = val
            this.applyCurrentPage = 1
        },
        handleApplyPageChange(val) {
            this.applyCurrentPage = val
        },
        async getApplyList() {
            this.applyLoading = true
            try {
                const params = {
                    page: 1,
                    pageSize: 100000
                }
                if (this.applySearch.applyRId) {
                    params.applyRId = this.applySearch.applyRId
                }
                if (this.applySearch.orderRId) {
                    params.orderRId = this.applySearch.orderRId
                }
                if (this.applySearch.customerName) {
                    params.customerName = this.applySearch.customerName
                }
                if (this.applySearch.status !== null && this.applySearch.status !== undefined && this.applySearch.status !== '') {
                    params.status = this.applySearch.status
                }
                const res = await axios.get(`${this.$apiBaseUrl}/warehouse/outbound-apply/list`, {
                    params
                })
                this.applyRawList = res.data.result || []
                this.applyCurrentPage = 1
            } catch (err) {
                console.error(err)
                ElMessage.error('获取出库申请失败')
            } finally {
                this.applyLoading = false
            }
        },
        resetApplySearch() {
            this.applySearch.applyRId = ''
            this.applySearch.orderRId = ''
            this.applySearch.customerName = ''
            this.applySearch.status = null
            this.applyCurrentPage = 1
            this.getApplyList()
        },

        _buildExportParams() {
            const [start, end] = this.searchFilters?.dateRange || [null, null]
            return {
                startDate: start,
                endDate: end,
                outboundRId: this.searchFilters.boundRIdSearch,
                orderRId: this.searchFilters.orderRIdSearch,
                shoeRId: this.searchFilters.shoeRIdSearch,
                customerName: this.searchFilters.customerNameSearch,
                customerProductName: this.searchFilters.customerProductNameSearch,
                orderCId: this.searchFilters.orderCIdSearch,
                customerBrand: this.searchFilters.customerBrandSearch
            }
        },

        // 通用导出
        async _downloadExcel(url, params, fallbackName = 'export.xlsx') {
            const res = await axios.get(`${this.$apiBaseUrl}${url}`, {
                params,
                responseType: 'blob'
            })

            let filename = fallbackName
            const dispo = res.headers['content-disposition'] || res.headers['Content-Disposition']
            if (dispo) {
                const utf8Match = /filename\*=UTF-8''([^;]+)/i.exec(dispo)
                const asciiMatch = /filename="?([^"]+)"?/i.exec(dispo)
                if (utf8Match) filename = decodeURIComponent(utf8Match[1])
                else if (asciiMatch) filename = asciiMatch[1]
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
        },

        async exportOutboundExcel() {
            this.exportLoadingOutbound = true
            try {
                const params = this._buildExportParams()
                await this._downloadExcel('/warehouse/export/finished-outbound', params, '成品出库记录.xlsx')
                ElMessage.success('出库记录导出成功')
            } catch (e) {
                console.error(e)
                ElMessage.error('出库记录导出失败')
            } finally {
                this.exportLoadingOutbound = false
            }
        },

        async exportInoutExcel() {
            this.exportLoadingInout = true
            try {
                const params = this._buildExportParams()
                await this._downloadExcel('/warehouse/export/finished-inout', params, '成品出入库合并.xlsx')
                ElMessage.success('合并记录导出成功')
            } catch (e) {
                console.error(e)
                ElMessage.error('合并记录导出失败')
            } finally {
                this.exportLoadingInout = false
            }
        },
        // ====== PACKING LIST 明细对话框 ======
        async openOutboundDetailDialog(row) {
            if (!row) return
            const applyIds = row.applyIds || []
            this.detailRow = row
            this.detailDialogTitle = row.outboundRId || ''
            this.isDetailDialogVisible = true
            this.detailCurrentPage = 1
            this.detailDetails = []
            this.detailSizeColumns = []

            // 旧出库单无关联申请，显示简易明细
            if (!applyIds.length) {
                this.isLegacyDetail = true
                return
            }
            this.isLegacyDetail = false
            this.detailLoading = true
            try {
                // 加载第一个关联的 apply 的明细（多 apply 合并）
                let allDetails = []
                let sizeColumns = []
                let headerInfo = {}
                for (const applyId of applyIds) {
                    const res = await axios.get(`${this.$apiBaseUrl}/warehouse/outbound-apply/detail`, {
                        params: { applyId }
                    })
                    allDetails = allDetails.concat(res.data.details || [])
                    if (!sizeColumns.length && res.data.sizeColumns) {
                        sizeColumns = res.data.sizeColumns
                    }
                    if (res.data.header) {
                        headerInfo = res.data.header
                    }
                }
                this.detailDetails = allDetails
                this.detailSizeColumns = sizeColumns
                // 补充 header 信息
                if (headerInfo.allOrderRIds) row.allOrderRIds = headerInfo.allOrderRIds
                if (headerInfo.allOrderCIds) row.allOrderCIds = headerInfo.allOrderCIds
                if (headerInfo.allCustomerNames) row.allCustomerNames = headerInfo.allCustomerNames
                if (headerInfo.customerBrand) row.customerBrand = headerInfo.customerBrand
            } catch (e) {
                console.error(e)
                ElMessage.error(e.response?.data?.message || '加载明细失败')
            } finally {
                this.detailLoading = false
            }
        },

        async openApplyDetailDialog(row) {
            if (!row || !row.applyId) return
            this.detailRow = row
            this.detailDialogTitle = row.applyRId || ''
            this.isDetailDialogVisible = true
            this.detailCurrentPage = 1
            this.detailLoading = true
            try {
                const res = await axios.get(`${this.$apiBaseUrl}/warehouse/outbound-apply/detail`, {
                    params: { applyId: row.applyId }
                })
                this.detailDetails = res.data.details || []
                this.detailSizeColumns = res.data.sizeColumns || []
                const h = res.data.header || {}
                if (h.allOrderRIds) row.allOrderRIds = h.allOrderRIds
                if (h.allOrderCIds) row.allOrderCIds = h.allOrderCIds
                if (h.allCustomerNames) row.allCustomerNames = h.allCustomerNames
                if (h.customerBrand) row.customerBrand = h.customerBrand
            } catch (e) {
                console.error(e)
                ElMessage.error(e.response?.data?.message || '加载明细失败')
            } finally {
                this.detailLoading = false
            }
        },

        getDetailSummary({ columns }) {
            const allData = this.detailPackingList
            const sums = []
            columns.forEach((col, index) => {
                if (index === 0) {
                    sums[index] = '合计'
                    return
                }
                if (col.property === 'cartonCount' || col.property === 'totalPairs') {
                    sums[index] = allData.reduce((sum, row) => sum + (Number(row[col.property]) || 0), 0)
                } else {
                    sums[index] = ''
                }
            })
            return sums
        },        exportDetailPackingList() {
            const row = this.detailRow
            if (!row) return
            const allData = this.detailPackingList
            const sizeCols = this.detailSizeColumns
            const title = this.detailDialogTitle || '出库明细'
            const headerRows = [
                [`出库明细 - ${title}`],
                ['订单号', row.allOrderRIds || row.orderRId || '', '', '客户订单号', row.allOrderCIds || row.orderCId || ''],
                ['客户名称', row.allCustomerNames || row.customerName || '', '', '客户商标', row.customerBrand || ''],
                []
            ]
            const colHeaders = ['起始箱号', '截止箱号', 'PO.NO. (工厂型号)', 'STYLE# (客户型号)', 'COLOR', '配码名称']
            sizeCols.forEach(c => colHeaders.push(c.label))
            colHeaders.push('PRS/Ctn', 'CTNS', 'Units(prs)')
            headerRows.push(colHeaders)
            const dataRows = allData.map(d => {
                const r = [d.cNoStart, d.cNoEnd, d.shoeRId || '', d.customerProductName || '', d.colorName || '', d.batchName || '']
                sizeCols.forEach(c => r.push(d.sizeRatios?.[c.label] || ''))
                r.push(d.pairsPerCarton || '', d.cartonCount || '', d.totalPairs || '')
                return r
            })
            const sumCartons = allData.reduce((s, d) => s + (Number(d.cartonCount) || 0), 0)
            const sumPairs = allData.reduce((s, d) => s + (Number(d.totalPairs) || 0), 0)
            const sumRow = ['合计', '', '', '', '', '']
            sizeCols.forEach(() => sumRow.push(''))
            sumRow.push('', sumCartons, sumPairs)
            const wsData = [...headerRows, ...dataRows, sumRow]
            const ws = XLSX.utils.aoa_to_sheet(wsData)
            const wb = XLSX.utils.book_new()
            XLSX.utils.book_append_sheet(wb, ws, 'PACKING LIST')
            XLSX.writeFile(wb, `${title}.xlsx`)
        },        // 按“出库单”下载出库清单
        async downloadOutboundList(row) {
            try {
                const params = {
                    outboundRecordIds: [row.outboundId],
                    outboundRIds: [row.outboundRId]
                    // 或 outbound_rids，看你服务端参数名
                }

                const res = await axios.post(
                    `${this.$apiBaseUrl}/warehouse/downloadfinishedoutboundrecordbybatchid`,
                    params,
                    { responseType: 'blob' }
                )

                let filename = '出货清单.xlsx'
                const dispo = res.headers['content-disposition'] || res.headers['Content-Disposition']
                if (dispo) {
                    const match = dispo.match(/filename="?(.+)"?/)
                    if (match && match[1]) filename = decodeURIComponent(match[1])
                }

                const blob = new Blob([res.data], {
                    type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                })
                const url = URL.createObjectURL(blob)
                const a = document.createElement('a')
                a.href = url
                a.download = filename
                a.click()
                URL.revokeObjectURL(url)
            } catch (err) {
                console.error(err)
                ElMessage.error('下载出库单失败')
            }
        },

        async downloadOutboundApply(row) {
            const applyIds = row.applyIds && row.applyIds.length ? row.applyIds : (row.applyId ? [row.applyId] : [])
            if (!applyIds.length) {
                ElMessage.error('该出库单未关联出库申请，无法下载')
                return
            }
            try {
                const res = await axios.post(
                    `${this.$apiBaseUrl}/warehouse/downloadfinishedoutboundapply`,
                    { applyIds },
                    { responseType: 'blob' }
                )

                let filename = '出库申请单.xlsx'
                const dispo = res.headers['content-disposition'] || res.headers['Content-Disposition']
                if (dispo) {
                    const match = dispo.match(/filename="?(.+)"?/)
                    if (match && match[1]) filename = decodeURIComponent(match[1])
                }

                const blob = new Blob([res.data], {
                    type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                })
                const url = URL.createObjectURL(blob)
                const a = document.createElement('a')
                a.href = url
                a.download = filename
                a.click()
                URL.revokeObjectURL(url)
            } catch (err) {
                console.error(err)
                ElMessage.error('下载出库申请单失败')
            }
        }
    }
}
</script>

<style scoped>
.mb-2 {
    margin-bottom: 8px;
}
.apply-search-bar {
    margin: 16px 0 12px;
}
</style>
