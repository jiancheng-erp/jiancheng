<template>
    <el-row :gutter="20">
        <el-col>
            <FinishedSearchBar :search-filters="searchFilters" @confirm="confirmSearchFilters" />
        </el-col>
    </el-row>
    <el-row :gutter="20" class="mb-2">
        <el-col>
            <el-button type="primary" :loading="exportLoadingOutbound" @click="exportOutboundExcel"> 导出出库Excel </el-button>
            <el-button type="success" :loading="exportLoadingInout" @click="exportInoutExcel"> 导出出入库合并Excel </el-button>
        </el-col>
    </el-row>
    <el-row :gutter="20">
        <el-col :span="24">
            <el-table :data="tableData" border stripe height="500" show-summary :summary-method="getSummaries">
                <el-table-column prop="outboundRId" label="出库单号"></el-table-column>
                <el-table-column prop="timestamp" label="操作时间"></el-table-column>
                <el-table-column prop="orderRId" label="订单号"></el-table-column>
                <el-table-column prop="shoeRId" label="工厂鞋型"></el-table-column>
                <el-table-column prop="customerName" label="客户名称"></el-table-column>
                <el-table-column prop="orderCId" label="客户订单号"></el-table-column>
                <el-table-column prop="customerProductName" label="客户鞋型"></el-table-column>
                <el-table-column prop="customerBrand" label="客户商标"></el-table-column>
                <el-table-column prop="colorName" label="颜色"></el-table-column>
                <el-table-column prop="detailAmount" label="数量"></el-table-column>
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
                :total="total"
            />
        </el-col>
    </el-row>

</template>
<script>
import axios from 'axios'
import { ElMessage } from 'element-plus'
import htmlToPdf from '@/Pages/utils/htmlToPdf'
import print from 'vue3-print-nb'
import { PAGESIZE, PAGESIZES, getSummaries } from '../../warehouseUtils'
import FinishedSearchBar from './FinishedSearchBar.vue'
export default {
    components: {
        FinishedSearchBar
    },
    directives: {
        print
    },
    data() {
        return {
            currentPage: 1,
            pageSize: PAGESIZE,
            pageSizes: PAGESIZES,
            tableData: [],
            total: 0,
            currentRow: {},
            recordData: {},
            dialogVisible: false,
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
            getSummaries: getSummaries,
            exportLoadingOutbound: false,
            exportLoadingInout: false
        }
    },
    mounted() {
        this.getOutboundRecordsTable()
    },
    computed: {
        filteredShoeSizeColumns() {
            return this.recordData.shoeSizeColumns.filter((column) => this.recordData.items.some((row) => row[column.prop] !== undefined && row[column.prop] !== null && row[column.prop] !== 0))
        }
    },
    methods: {
        confirmSearchFilters(filters) {
            this.searchFilters = { ...filters }
            this.getOutboundRecordsTable()
        },
        calculateOutboundTotal() {
            // Calculate the total outbound quantity
            const number = this.recordData.items.reduce((total, item) => {
                return total + (Number(item.totalAmount) || 0)
            }, 0)
            return Number(number)
        },
        downloadPDF(title, domName) {
            htmlToPdf.getPdf(title, domName)
        },
        async getOutboundRecordsTable() {
            if (this.searchFilters.dateRange === null) {
                this.searchFilters.dateRange = [null, null]
            }
            try {
                let params = {
                    page: this.currentPage,
                    pageSize: this.pageSize,
                    startDate: this.searchFilters.dateRange[0],
                    endDate: this.searchFilters.dateRange[1],
                    outboundRId: this.searchFilters.boundRIdSearch,
                    orderRId: this.searchFilters.orderRIdSearch,
                    shoeRId: this.searchFilters.shoeRIdSearch,
                    customerName: this.searchFilters.customerNameSearch,
                    customerProductName: this.searchFilters.customerProductNameSearch,
                    orderCId: this.searchFilters.orderCIdSearch,
                    customerBrand: this.searchFilters.customerBrandSearch
                }
                let response = await axios.get(`${this.$apiBaseUrl}/warehouse/getfinishedoutboundrecords`, { params })
                this.tableData = response.data.result
                this.total = response.data.total
            } catch (error) {
                console.log(error)
            }
        },
        handleSizeChange(val) {
            this.pageSize = val
            this.getOutboundRecordsTable()
        },
        handlePageChange(val) {
            this.currentPage = val
            this.getOutboundRecordsTable()
        },
        async handleView(row) {
            this.currentRow = row
            console.log(row)
            try {
                let params = { orderId: this.currentRow.orderId, outboundBatchId: row.outboundBatchId }
                let response = await axios.get(`${this.$apiBaseUrl}/warehouse/getfinishedoutboundrecordbybatchid`, { params })
                this.recordData = response.data

                console.log(response.data)
                this.dialogVisible = true
            } catch (error) {
                console.log(error)
                ElMessage.error('获取出库单详情失败')
            }
        },
        _buildExportParams() {
            const [start, end] = this.searchFilters?.dateRange || [null, null]
            return {
                startDate: start,
                endDate: end,
                outboundRId: this.searchFilters.boundRIdSearch, // 出库单号
                orderRId: this.searchFilters.orderRIdSearch,
                shoeRId: this.searchFilters.shoeRIdSearch,
                customerName: this.searchFilters.customerNameSearch,
                customerProductName: this.searchFilters.customerProductNameSearch,
                orderCId: this.searchFilters.orderCIdSearch,
                customerBrand: this.searchFilters.customerBrandSearch
            }
        },

        // 通用下载器：GET -> blob -> 保存
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

        // 导出：出库记录
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

        // 导出：出入库合并
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
    }
}
</script>
<style media="print">
@page {
    size: auto;
    margin: 3mm;
}

html {
    background-color: #ffffff;
    margin: 0px;
}

body {
    border: solid 1px #ffffff;
}
</style>

<style lang="scss" scoped>
@media print {
    #printView {
        display: block;
        width: 100%;
        overflow: hidden;
    }
}
</style>
