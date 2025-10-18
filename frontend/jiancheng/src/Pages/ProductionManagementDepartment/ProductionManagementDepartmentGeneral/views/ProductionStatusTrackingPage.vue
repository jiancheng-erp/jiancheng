<template>
    <el-container>
        <el-header class="app-header">
            <AllHeader></AllHeader>
        </el-header>
        <el-main height="">
            <el-row :gutter="20">
                <el-col :span="24" :offset="0" style="font-size: xx-large; text-align: center">生产节点管理</el-col>
            </el-row>
            <el-row :gutter="20">
                <Arrow v-if="productionStatus != -1" :status="productionStatus" :workflowType="1"></Arrow>
            </el-row>
            <el-collapse>
                <el-collapse-item title="鞋型配码信息" name="鞋型配码信息">
                    <el-table :data="shoeBatchInfo" :span-method="spanMethod" border stripe :max-height="500">
                        <el-table-column prop="colorName" label="颜色"></el-table-column>
                        <el-table-column prop="totalAmount" label="颜色总数"></el-table-column>
                        <el-table-column prop="batchName" label="配码编号"></el-table-column>
                        <el-table-column v-for="column in filteredColumns" :key="column.prop" :prop="column.prop"
                            :label="column.label"></el-table-column>
                        <el-table-column prop="pairAmount" label="双数"></el-table-column>
                    </el-table>
                </el-collapse-item>
                <el-collapse-item title="计划自产数量" name="计划自产数量">
                    <el-tabs v-model="currentProductionAmountTab" type="border-card" tab-position="top">
                        <el-tab-pane v-for="item in productionAmountPanes" :key="item.key" :label="item.label"
                            :name="item.key">
                            <el-table :data="shoeBatchProductionPlan[item.key]" border stripe :max-height="500">
                                <el-table-column prop="colorName" label="颜色"></el-table-column>
                                <el-table-column prop="totalAmount" label="颜色总数"></el-table-column>
                                <el-table-column v-for="column in filteredColumns" :key="column.prop"
                                    :prop="column.prop" :label="column.label">
                                </el-table-column>
                            </el-table>
                        </el-tab-pane>
                    </el-tabs>
                </el-collapse-item>
                <el-collapse-item title="工价单" name="工价单">
                    <el-tabs v-model="currentPriceReportTab" type="border-card" tab-position="top" @tab-click="">
                        <el-tab-pane v-for="item in panes" :key="item.key" :label="item.label" :name="item.key">
                            <el-row v-if="priceReportDict[item.key] === undefined">
                                尚未有工价单
                            </el-row>
                            <el-row v-else>
                                <el-table :data="priceReportDict[item.key]" border stripe max-height="500">
                                    <el-table-column prop="rowId" label="序号" />
                                    <el-table-column prop="procedure" label="工序"></el-table-column>
                                    <el-table-column prop="price" label="单位价格"></el-table-column>
                                    <el-table-column prop="note" label="备注"></el-table-column>
                                </el-table>
                            </el-row>
                        </el-tab-pane>
                    </el-tabs>
                </el-collapse-item>
                <el-collapse-item title="数量单" name="数量单">
                    <el-button type="primary" @click="openProductionAmountApprovalPage">
                        打开数量单审批页面
                    </el-button>
                </el-collapse-item>
                <el-collapse-item title="外包信息" name="外包信息">
                    <el-tabs v-model="currentOutsourceTab" type="border-card" tab-position="top">
                        <el-tab-pane v-for="(row, index) in outsourceInfo" :key="row.outsourceInfoId" :name="index"
                            :label="`外包${index + 1}`">
                            <el-descriptions title="" :column="3" border>
                                <el-descriptions-item label="外包工厂" align="center">{{
                                    row.outsourceFactory.value }}</el-descriptions-item>
                                <el-descriptions-item label="外包类型" align="center">{{
                                    row.outsourceType.toString()
                                    }}</el-descriptions-item>
                                <el-descriptions-item label="外包数量" align="center">{{
                                    row.outsourceAmount
                                    }}</el-descriptions-item>
                                <el-descriptions-item label="外包周期" align="center">
                                    {{ row.outsourceStartDate }} 至 {{ row.outsourceEndDate }}
                                </el-descriptions-item>
                                <el-descriptions-item label="最迟交货日期" align="center">{{
                                    row.deadlineDate
                                    }}</el-descriptions-item>
                                <el-descriptions-item label="状态" align="center">{{
                                    row.outsourceStatus
                                    }}</el-descriptions-item>
                            </el-descriptions>
                            <Arrow :status="row.outsourceNode" :workflowType="2"></Arrow>
                            <el-button v-if="row.outsourceStatus === '已审批'" type="primary"
                                @click="startOutsourceFlow(row)">开始外包</el-button>
                        </el-tab-pane>
                    </el-tabs>
                    <el-button type="primary" @click="openOutsourceSetting">
                        打开外包设置页面
                    </el-button>
                </el-collapse-item>
            </el-collapse>
            <el-row :gutter="20">
                <el-col :offset="22">
                    <el-button type="success" @click="confirmNode">确认推进流程</el-button>
                </el-col>
            </el-row>
        </el-main>
    </el-container>
</template>
<script>
import AllHeader from '@/components/AllHeader.vue'
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus';
import Arrow from '@/components/OrderShoeProductionArrorView.vue'
import { checkProductionStatus, checkOutsourceStatus, shoeBatchInfoTableSpanMethod, productionLines, getShoeSizesName } from '../../utils';
export default {
    props: ['orderId', "orderShoeId"],
    data() {
        return {
            getShoeSizesName,
            orderTableData: [],
            currentRow: {},
            currentPriceReportTab: -1,
            panes: [
                {
                    label: '裁断',
                    key: 0
                },
                {
                    label: '针车预备',
                    key: 1
                },
                {
                    label: '针车',
                    key: 2
                },
                {
                    label: '成型',
                    key: 3
                }
            ],
            productionAmountPanes: [
                {
                    label: '裁断',
                    key: 0
                },
                {
                    label: '针车预备+针车',
                    key: 1
                },
                {
                    label: '成型',
                    key: 2
                }
            ],
            currentPriceReportTable: [],
            cuttingPriceReportData: [],
            pewSewingPriceReportData: [],
            sewingPriceReportData: [],
            moldingPriceReportData: [],
            shoeBatchInfo: [],
            shoeBatchProductionPlan: [],
            outsourcePanes: [],
            currentOutsourceTab: 0,
            productionStatus: -1,
            outsourceNode: -1,
            outsourceStatus: '',
            outsourceInfo: [],
            currentProductionAmountTab: 0,
            priceReportDict: {},
            shoeSizeColumns: [],
        }
    },
    components: {
        AllHeader,
        Arrow
    },
    mounted() {
        this.getOrderShoeStatus()
        this.getOrderShoeBatchInfo()
        this.getPriceReportData()
        this.getOrderShoeProductionAmount()
        this.getOutsourceInfo()
    },
    computed: {
        filteredColumns() {
            return this.shoeSizeColumns.filter(column =>
                this.shoeBatchInfo.some(row => row[column.prop] !== undefined && row[column.prop] !== null && row[column.prop] !== 0)
            );
        }
    },
    methods: {
        async getOrderShoeStatus() {
            const params = { "orderShoeId": this.$props.orderShoeId }
            const response = await axios.get(`${this.$apiBaseUrl}/production/productionmanager/getordershoestatus`, { params })
            this.productionStatus = checkProductionStatus(response.data)
        },
        async getOrderShoeBatchInfo() {
            const params = { "orderShoeId": this.$props.orderShoeId }
            const response = await axios.get(`${this.$apiBaseUrl}/production/getordershoebatchinfo`, { params })
            this.shoeSizeColumns = await this.getShoeSizesName(this.$props.orderId)
            this.shoeBatchInfo = response.data
            this.spanMethod = shoeBatchInfoTableSpanMethod(this.shoeBatchInfo)
        },
        async getOrderShoeProductionAmount() {
            const params = { "orderShoeId": this.$props.orderShoeId }
            const response = await axios.get(`${this.$apiBaseUrl}/production/productionmanager/getordershoeproductionamount`, { params })
            this.shoeBatchProductionPlan = response.data
            this.currentProductionAmountTab = 0
        },
        async getOutsourceInfo() {
            const params = { "orderShoeId": this.$props.orderShoeId }
            const response = await axios.get(`${this.$apiBaseUrl}/production/productionmanager/getordershoeoutsourceinfo`, { params })
            this.outsourceInfo = [...response.data]
            if (this.outsourceInfo.length > 0) {
                this.outsourceInfo.forEach(row => {
                    row.outsourceNode = checkOutsourceStatus(row.outsourceStatus)
                })
            }
        },
        openProductionAmountApprovalPage() {
            const params = {
                "orderId": this.$props.orderId,
                "orderShoeId": this.$props.orderShoeId,
            }
            const queryString = new URLSearchParams(params).toString();
            const url = `${window.location.origin}/productiongeneral/productionamountapproval?${queryString}`
            window.open(url, '_blank')
        },
        async getPriceReportData() {
            try {
                let teams = ["裁断", "针车预备", "针车", "成型"]
                teams.forEach(async (team, index) => {
                    let params = { "orderShoeId": this.$props.orderShoeId, "team": team, "status": 2 }
                    let response = await axios.get(`${this.$apiBaseUrl}/production/getpricereportdetailbyordershoeid`, { params })
                    this.priceReportDict[index] = response.data.detail
                })
                this.currentPriceReportTab = 0
            }
            catch (error) {
                console.log(error)
            }
        },
        confirmNode() {
            ElMessageBox.alert('请再次确认推进流程，此操作不可撤回！', '警告', {
                confirmButtonText: '确认',
                showCancelButton: true,
                cancelButtonText: '取消'
            }).then(async () => {
                try {
                    const data = { "orderId": this.$props.orderId, "orderShoeId": this.$props.orderShoeId }
                    await axios.patch(`${this.$apiBaseUrl}/production/productionmanager/editordershoestatus`, data)
                    ElMessage.success("推进流程成功")
                    window.location.reload()
                }
                catch (error) {
                    console.log(error)
                    ElMessage.error(`推进流程失败, ${error.response.data.message}`)
                }
            })
        },
        async openOutsourceSetting() {
            const params = {
                "orderId": this.$props.orderId,
                "orderShoeId": this.$props.orderShoeId,
            }
            const queryString = new URLSearchParams(params).toString();
            const url = `${window.location.origin}/productiongeneral/productionoutsource?${queryString}`
            window.open(url, '_blank')
        },
        async startOutsourceFlow(rowData) {
            try {
                let data = { "outsourceInfoId": rowData.outsourceInfoId }
                await axios.patch(`${this.$apiBaseUrl}/production/productionmanager/editoutsourcestatus`, data)
                ElMessage.success("推进外包成功")
            }
            catch (error) {
                console.log(error)
                ElMessage.error("推进外包失败")
            }
            await this.getOutsourceInfo()
        },
        // spanMethod({ row, column, rowIndex, columnIndex }, tableData) {
        //     // Merging 'colorName' and 'totalAmount' columns
        //     if (columnIndex === 0 || columnIndex === 16) { // colorName and totalAmount columns
        //         const currentColor = tableData[rowIndex].colorName;

        //         // Skip rows already merged
        //         if (rowIndex > 0 && tableData[rowIndex - 1].colorName === currentColor) {
        //             return [0, 0]; // Skip this cell
        //         }

        //         // Calculate the rowspan for the current 'colorName'
        //         let rowspan = 1;
        //         for (let i = rowIndex + 1; i < tableData.length; i++) {
        //             if (tableData[i].colorName === currentColor) {
        //                 rowspan++;
        //             } else {
        //                 break;
        //             }
        //         }

        //         return [rowspan, 1]; // Set the rowspan for merging, and colspan = 1
        //     }
        // }
    },
}
</script>