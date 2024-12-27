<template>
    <el-row :gutter="20">
        <el-col :span="24">
            <el-table :data="tableData" border>
                <el-table-column prop="purchaseDivideOrderRId" label="采购单号"></el-table-column>
                <el-table-column prop="inboundRId" label="单号"></el-table-column>
                <el-table-column prop="timestamp" label="操作时间"></el-table-column>
                <el-table-column prop="orderRId" label="订单号"></el-table-column>
                <el-table-column prop="shoeRId" label="工厂型号"></el-table-column>
                <el-table-column label="查看">
                    <template #default="scope">
                        <el-button type="primary" @click="handleView(scope.row)">查看</el-button>
                    </template>
                </el-table-column>
            </el-table>
        </el-col>
    </el-row>
    <el-row :gutter="20">
        <el-col :span="12" :offset="14">
            <el-pagination @size-change="handleSizeChange" @current-change="handlePageChange"
                :current-page="currentPage" :page-sizes="[10, 20, 30, 40]" :page-size="pageSize"
                layout="total, sizes, prev, pager, next, jumper" :total="total" />
        </el-col>
    </el-row>

    <el-dialog title="入库单详情" v-model="dialogVisible" width="80%">
        <div :id="`inboundRecipt`" style="padding:10px;background-color:#fff;">
            <el-card>
                <h2 style="text-align: center; margin-bottom: 10px">{{ `健诚鞋业入库单${currentRow.inboundRId}` }}</h2>
                <el-descriptions :column="4" border>
                    <el-descriptions-item label="采购订单号">{{ currentRow.purchaseDivideOrderRId }}</el-descriptions-item>
                    <el-descriptions-item label="供应商">{{ recordData.items[0].supplierName }}</el-descriptions-item>
                    <el-descriptions-item label="入库时间">{{ currentRow.timestamp }}</el-descriptions-item>
                    <el-descriptions-item label="入库方式">{{ determineInboundName(currentRow.inboundType)}}</el-descriptions-item>
                </el-descriptions>
                <el-table v-if="currentRow.purchaseDivideOrderType === 'S'" :data="recordData.items" border>
                    <el-table-column prop="materialName" label="材料名称"></el-table-column>
                    <el-table-column prop="materialModel" label="材料型号"></el-table-column>
                    <el-table-column prop="materialSpecification" label="材料规格"></el-table-column>
                    <el-table-column prop="colorName" label="颜色"></el-table-column>
                    <el-table-column prop="materialUnit" label="单位"></el-table-column>
                    <el-table-column prop="orderRId" label="订单号"></el-table-column>
                    <el-table-column :label="`分码数量`" header-align="center">
                        <el-table-column v-for="column in recordData.shoeSizeColumns" :key="column.prop"
                            :prop="column.prop" :label="column.label" width="55">
                        </el-table-column>
                    </el-table-column>
                    <el-table-column prop="unitPrice" label="单价">
                    </el-table-column>
                    <el-table-column label="总价" width="100">
                        <template #default="scope">
                            {{ scope.row.inboundQuantity * scope.row.unitPrice }}
                        </template>
                    </el-table-column>
                    <el-table-column prop="remark" label="备注">
                    </el-table-column>
                </el-table>
                <el-table v-else :data="recordData.items" border>
                    <el-table-column prop="materialName" label="材料名称"></el-table-column>
                    <el-table-column prop="materialModel" label="材料型号"></el-table-column>
                    <el-table-column prop="materialSpecification" label="材料规格"></el-table-column>
                    <el-table-column prop="colorName" label="颜色"></el-table-column>
                    <el-table-column prop="materialUnit" label="单位"></el-table-column>
                    <el-table-column prop="orderRId" label="订单号"></el-table-column>
                    <el-table-column prop="inboundQuantity" label="入库数量">
                    </el-table-column>
                    <el-table-column v-if="currentRow.inboundType != 2" prop="unitPrice" label="单价">
                    </el-table-column>
                    <el-table-column v-if="currentRow.inboundType == 2" prop="compositeUnitCost" label="复合单价">
                    </el-table-column>
                    <el-table-column label="总价" width="100">
                        <template #default="scope">
                            {{ calculateTotalPrice(scope.row) }}
                        </template>
                    </el-table-column>
                    <el-table-column prop="remark" label="备注">
                    </el-table-column>
                </el-table>
            </el-card>
        </div>
        <template #footer>
            <el-button type="primary" @click="dialogVisible = false">返回</el-button>
            <el-button type="primary"
                @click="downloadPDF(`健诚鞋业入库单${currentRow.inboundRId}`, `inboundRecipt`)">下载PDF</el-button>
        </template>
    </el-dialog>
</template>
<script>
import axios from 'axios'
import { ElMessage } from 'element-plus';
import htmlToPdf from '@/Pages/utils/htmlToPdf';
export default {
    data() {
        return {
            currentPage: 1,
            pageSize: 10,
            tableData: [],
            total: 0,
            currentRow: {},
            recordData: {},
            dialogVisible: false,
        }
    },
    mounted() {
        this.getInboundRecordsTable()
    },
    methods: {
        calculateTotalPrice(row) {
            let result = 0
            if (this.currentRow.inboundType != 2) {
                result = Number(row.inboundQuantity) * Number(row.unitPrice)
            } else {
                result = Number(row.inboundQuantity) * Number(row.compositeUnitCost)
            }
            return result.toFixed(2)
        },
        determineInboundName(type) {
            if (type == 0) {
                return '采购入库'
            } else if (type == 1) {
                return '生产剩余'
            } else if (type == 2) {
                return '复合入库'
            } else {
                return '未知'
            }
        },
        downloadPDF(title, domName) {
            htmlToPdf.getPdf(title, domName);
        },
        async getInboundRecordsTable() {
            try {
                let params = {
                    page: this.currentPage,
                    pageSize: this.pageSize
                }
                let response = await axios.get(`${this.$apiBaseUrl}/warehouse/getmaterialinboundrecords`, { params })
                this.tableData = response.data.result
                this.total = response.data.total
            }
            catch (error) {
                console.log(error)
            }
        },
        handleSizeChange(val) {
            this.pageSize = val
            this.getInboundRecordsTable()
        },
        handlePageChange(val) {
            this.page = val
            this.getInboundRecordsTable()
        },
        async handleView(row) {
            this.currentRow = row
            console.log(row)
            try {
                let params = { "inboundBatchId": row.inboundBatchId, "purchaseDivideOrderType": row.purchaseDivideOrderType }
                let response = await axios.get(`${this.$apiBaseUrl}/warehouse/getinboundrecordbybatchid`, { params })
                this.recordData["items"] = response.data

                console.log(this.recordData["items"])
                // if the purchase divide order type is S, then the inbound record is for shoe size
                if (row.purchaseDivideOrderType == 'S') {
                    params = { "sizeMaterialStorageId": this.recordData["items"][0].materialStorageId, "orderId": row.orderId, "purchaseDivideOrderId": row.purchaseDivideOrderId }
                    response = await axios.get(`${this.$apiBaseUrl}/warehouse/warehousemanager/getsizematerialbyid`, { params })
                    this.recordData["sizeMaterialInboundTable"] = response.data
                    this.recordData["shoeSizeColumns"] = []
                    // insert shoe size columns into current row
                    this.recordData["sizeMaterialInboundTable"].forEach((element, index) => {
                        // for display
                        if (element.predictQuantity > 0) {
                            this.recordData["shoeSizeColumns"].push({
                                "prop": `amount${index}`,
                                "label": element.shoeSizeName
                            })
                        }
                    })
                }
                console.log(this.recordData)
                this.dialogVisible = true
            }
            catch (error) {
                console.log(error)
                ElMessage.error('获取入库单详情失败')
            }
        }
    }
}
</script>