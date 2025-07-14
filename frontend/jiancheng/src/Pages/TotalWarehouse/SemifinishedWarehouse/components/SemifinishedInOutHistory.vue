<template>
    <el-row :gutter="20">
        <el-col>
            <el-input v-model="orderNumberSearch" placeholder="订单号筛选" clearable @change="getTableData()" style="width: 200px; margin-right: 10px;"
                @clear="getTableData" />
            <el-input v-model="shoeNumberSearch" placeholder="鞋型号筛选" clearable @change="getTableData()" style="width: 200px; margin-right: 10px;"
                @clear="getTableData" />
            <el-input v-model="customerNameSearch" placeholder="客户号筛选" clearable @change="getTableData()" style="width: 200px; margin-right: 10px;"
                @clear="getTableData" />
            <el-input v-model="customerProductNameSearch" placeholder="客户鞋型筛选" clearable @change="getTableData()" style="width: 200px; margin-right: 10px;"
                @clear="getTableData" />
            <span>半成品仓库存：{{ this.totalStock }}</span>
        </el-col>
    </el-row>
    <el-row :gutter="20">
        <el-col :span="6" v-if="role != 10" >
            <el-button v-if="isOutboundToggle == false" type="primary" @click="toggleOutbound">出库</el-button>
            <el-button v-if="isOutboundToggle == true" type="success" @click="outboundShoes">确认出库数量</el-button>
            <el-button v-if="isOutboundToggle == true" @click="toggleOutbound">取消</el-button>
        </el-col>
    </el-row>
    <div v-if="isOutboundToggle" class="transfer-tables">
        <!-- Top Table -->
        <el-table ref="topTableData" :data="topTableData" style="width: 100%; margin-bottom: 20px; height: 20vh"
            @selection-change="handleTopSelectionChange" border stripe>
            <el-table-column type="selection" width="55"></el-table-column>
            <el-table-column prop="orderRId" label="订单号"></el-table-column>
            <el-table-column prop="shoeRId" label="工厂型号"></el-table-column>
            <el-table-column prop="customerName" label="客户号"></el-table-column>
            <el-table-column prop="customerProductName" label="客户鞋型"></el-table-column>
            <el-table-column prop="colorName" label="颜色"></el-table-column>
            <el-table-column prop="currentAmount" label="鞋型库存"></el-table-column>
        </el-table>

        <!-- Control Buttons -->
        <div class="transfer-buttons" style="text-align: center; margin-bottom: 20px;">
            <el-button type="primary" @click="moveUp" :disabled="bottomSelected.length === 0">
                选择 <el-icon>
                    <Top />
                </el-icon>
            </el-button>
            <el-button type="primary" @click="moveDown" :disabled="topSelected.length === 0" style="margin-left: 20px;">
                <el-icon>
                    <Bottom />
                </el-icon> 移除
            </el-button>
        </div>
    </div>
    <el-table :data="bottomTableData" border stripe style="width: 100%; margin-bottom: 20px; height: 55vh"
        @selection-change="handleBottomSelectionChange">
        <el-table-column v-if="isOutboundToggle" type="selection" width="55"></el-table-column>
        <el-table-column prop="orderRId" label="订单号"></el-table-column>
        <el-table-column prop="shoeRId" label="工厂型号"></el-table-column>
        <el-table-column prop="customerName" label="客户号"></el-table-column>
        <el-table-column prop="customerProductName" label="客户鞋型"></el-table-column>
        <el-table-column prop="colorName" label="颜色"></el-table-column>
        <el-table-column prop="currentAmount" label="鞋型库存"></el-table-column>
        <el-table-column prop="storageStatus" label="状态"></el-table-column>
        <!-- <el-table-column label="操作" width="200">
            <template #default="scope">
                <el-button type="primary" size="small" @click="viewStock(scope.row)">查看库存</el-button>
                <el-button type="primary" size="small" @click="viewRecords(scope.row)">入/出库记录</el-button>
            </template>
        </el-table-column> -->
    </el-table>
    <el-row :gutter="20">
        <el-col>
            <el-pagination @size-change="handleSizeChange" @current-change="handlePageChange"
                :current-page="currentPage" :page-sizes="[30, 40, 50, 100]" :page-size="pageSize"
                layout="total, sizes, prev, pager, next, jumper" :total="totalRows" />
        </el-col>
    </el-row>
    <el-dialog title="半成品入库/出库记录" v-model="isRecordDialogVisible" width="80%">
        <el-descriptions title="入库记录"></el-descriptions>
        <el-table :data="recordData.inboundRecords" border stripe style="margin-bottom: 1ch;">
            <el-table-column label="自产/外包">
                <template #default="scope">
                    {{ mapping[scope.row.productionType] }}
                </template>
            </el-table-column>
            <el-table-column prop="shoeInboundRId" label="入库编号" width="170"></el-table-column>
            <el-table-column prop="timestamp" label="操作时间"></el-table-column>
            <el-table-column prop="amount" label="入库数量"></el-table-column>
            <el-table-column prop="subsequentStock" label="入库后库存"></el-table-column>
            <el-table-column prop="source" label="来自"></el-table-column>
            <el-table-column prop="remark" label="备注"></el-table-column>
        </el-table>

        <el-descriptions title="出库记录"></el-descriptions>
        <el-table :data="recordData.outboundRecords" border stripe>
            <el-table-column label="自产/外包">
                <template #default="scope">
                    {{ mapping[scope.row.productionType] }}
                </template>
            </el-table-column>
            <el-table-column prop="shoeOutboundRId" label="出库编号" width="170"></el-table-column>
            <el-table-column prop="timestamp" label="操作时间"></el-table-column>
            <el-table-column prop="amount" label="出库数量"></el-table-column>
            <el-table-column prop="subsequentStock" label="出库后库存"></el-table-column>
            <el-table-column label="出库至">
                <template #default="scope">
                    <span v-if="scope.row.productionType == 0">{{ scope.row.picker }}</span>
                    <span v-else>{{ scope.row.destination }}</span>
                </template>
            </el-table-column>
            <el-table-column prop="remark" label="备注"></el-table-column>
        </el-table>
    </el-dialog>

    <el-dialog :title="`订单${currentQuantityRow.orderRId}/鞋型${currentQuantityRow.shoeRId}库存`" v-model="isOpenQuantityDialogVisible"
        width="60%">
        <el-form>
            <el-form-item>
                <el-table :data="filteredData" border stripe>
                    <el-table-column prop="shoeSizeName" label="鞋码"></el-table-column>
                    <el-table-column prop="currentQuantity" label="库存"></el-table-column>
                    <el-table-column v-if="isOutbound" label="出库数量">
                        <template #default="scope">
                            <el-input-number v-model="scope.row.outboundQuantity" size="small" :min="0"
                                @change="updateSemiShoeTotal"></el-input-number>
                        </template>
                    </el-table-column>
                </el-table>
            </el-form-item>
        </el-form>
        <template #footer>
            <el-button type="primary" @click="isOpenQuantityDialogVisible = false">
                确认
            </el-button>
        </template>
    </el-dialog>

    <el-dialog title="半成品出库" v-model="isOutboundDialogVisible" width="60%">
        <el-form v-model="outboundForm" ref="outboundForm">
            <el-form-item prop="picker" label="领料工组">
                <el-select v-model="outboundForm.picker" placeholder="请选择领料工组" style="width: 50%" clearable>
                    <el-option v-for="item in pickerOptions" :key="item.productionLineName"
                        :label="item.productionLineName" :value="item.productionLineName" />
                </el-select>
            </el-form-item>
            <!-- <el-form-item label="备注">
                <el-input v-model="outboundForm.remark" type="textarea" show-word-limit
                    :maxlength="commentLength"></el-input>
            </el-form-item> -->
            <el-form-item label="表格">
                <el-table :data="topTableData" border stripe>
                    <el-table-column prop="orderRId" label="订单号"></el-table-column>
                    <el-table-column prop="shoeRId" label="工厂型号"></el-table-column>
                    <el-table-column prop="colorName" label="颜色"></el-table-column>
                    <el-table-column prop="remainQuantity" label="剩余数量"></el-table-column>
                    <el-table-column label="出库数量">
                        <template #default="scope">
                            <el-input-number v-model="scope.row.outboundQuantity" :min="0"></el-input-number>
                        </template>
                    </el-table-column>
                    <el-table-column label="备注">
                        <template #default="scope">
                            <el-input v-model="scope.row.remark" type="textarea" show-word-limit
                                :maxlength="commentLength"></el-input>
                        </template>
                    </el-table-column>
                </el-table>
            </el-form-item>
        </el-form>
        <template #footer>
            <el-button type="primary" @click="confirmOutbound">确认出库</el-button>
            <el-button @click="isOutboundDialogVisible = false">取消</el-button>
        </template>

    </el-dialog>

    <!-- <el-dialog title="数量输入框" v-model="isOpenQuantityDialogVisible" width="60%">
        <el-table :data="filteredData" border stripe>
            <el-table-column prop="shoeSizeName" label="鞋码"></el-table-column>
            <el-table-column prop="currentQuantity" label="库存"></el-table-column>
            <el-table-column label="出库数量">
                <template #default="scope">
                    <el-input-number v-model="scope.row.outboundQuantity" size="small" :min="0"
                        @change="updateSemiShoeTotal"></el-input-number>
                </template>
            </el-table-column>
        </el-table>
        <template #footer>
            <el-button type="primary" @click="isOpenQuantityDialogVisible = false">
                确认
            </el-button>
        </template>
    </el-dialog> -->
</template>
<script>
import axios from 'axios'
import * as constants from '@/Pages/utils/constants'
import { ElMessage } from 'element-plus';
export default {
    data() {
        return {
            role: localStorage.getItem('role'),
            isRecordDialogVisible: false,
            orderNumberSearch: '',
            shoeNumberSearch: '',
            customerNameSearch: '',
            customerProductNameSearch: '',
            pageSize: 30,
            currentPage: 1,
            tableData: [],
            totalRows: 0,
            mapping: {
                0: "自产",
                1: "外包"
            },
            isOpenQuantityDialogVisible: false,
            shoeStockTable: [],
            topTableData: [],
            bottomTableData: [],
            topSelected: [],
            bottomSelected: [],
            pickerOptions: [],
            isOutboundDialogVisible: false,
            outboundFormTemplate: {
                picker: null,
                remark: null,
                items: []
            },
            outboundForm: {},
            commentLength: constants.BOUND_RECORD_COMMENT_LENGTH,
            isOutbound: true, // 控制是否显示出库数量列
            currentQuantityRow: {},
            isOutboundToggle: false, // 控制是否显示出库表格,
            totalStock: 0, // 半成品仓库存
        }
    },
    computed: {
        filteredData() {
            return this.currentQuantityRow.shoeStockTable.filter((row) => {
                return (
                    row.predictQuantity > 0
                );
            });
        },
    },
    mounted() {
        this.getMoldingLines()
        this.getTableData()
    },
    methods: {
        toggleOutbound() {
            this.isOutboundToggle = !this.isOutboundToggle
            if (this.isOutboundToggle == false) {
                this.resetVaribles()
                this.getTableData()
            }
        },
        updateSemiShoeTotal() {
            this.currentQuantityRow.remainQuantity = this.currentQuantityRow.shoeStockTable.reduce((total, item) => {
                return total + (item.outboundQuantity || 0);
            }, 0);
        },
        buildShoeStockTable(data) {
            for (let item of data) {
                item.remainQuantity = item.currentAmount
                item.outboundQuantity = item.currentAmount
                item["remark"] = null
                let shoesOutboundTable = []
                for (let i = 0; i < item.shoeSizeColumns.length; i++) {
                    let column = item.shoeSizeColumns[i];
                    if (column === '') {
                        break
                    }
                    shoesOutboundTable.push({
                        "shoeSizeName": column,
                        "predictQuantity": item[`size${i + 34}EstimatedAmount`],
                        "actualQuantity": item[`size${i + 34}ActualAmount`],
                        "currentQuantity": item[`size${i + 34}Amount`],
                        "outboundQuantity": item[`size${i + 34}Amount`]
                    });
                }
                item["shoeStockTable"] = shoesOutboundTable
            }
        },
        outboundShoes() {
            if (this.topTableData.length === 0) {
                this.$message.warning("请至少选择一条记录进行出库")
                return
            }
            this.outboundForm = JSON.parse(JSON.stringify(this.outboundFormTemplate))
            this.buildShoeStockTable(this.topTableData)
            this.isOutboundDialogVisible = true
        },
        openQuantityDialog(row) {
            this.isOutbound = true
            this.currentQuantityRow = row

            this.isOpenQuantityDialogVisible = true
        },
        resetVaribles() {
            this.outboundForm = JSON.parse(JSON.stringify(this.outboundFormTemplate))
            this.topTableData = []
            this.bottomTableData = []
            this.topSelected = []
            this.bottomSelected = []
        },
        async confirmOutbound() {
            console.log(this.topTableData)
            this.outboundForm.items = this.topTableData.map(item => {
                let obj = {
                    storageId: item.storageId,
                    outboundQuantity: item.outboundQuantity || 0, // 确保有默认值
                    amountList: [],
                    remark: item.remark
                }
                for (let i = 0; i < item.shoeStockTable.length; i++) {
                    obj["amountList"].push(item.shoeStockTable[i].outboundQuantity)
                }
                return obj
            })
            try {
                await axios.post(`${this.$apiBaseUrl}/warehouse/outboundsemifinished`, this.outboundForm)
                ElMessage.success("出库成功")
                this.resetVaribles()
                this.isOutboundDialogVisible = false
                this.getTableData()
            }
            catch (error) {
                if (error.response && error.response.data) {
                    ElMessage.error(error.response.data.message)
                } else {
                    ElMessage.error("出库失败")
                }
            }
        },
        async getMoldingLines() {
            let response = await axios.get(`${this.$apiBaseUrl}/production/getmoldinglines`)
            this.pickerOptions = response.data
        },
        async viewStock(row) {
            this.currentQuantityRow = row
            this.isOutbound = false
            this.buildShoeStockTable([row])
            this.isOpenQuantityDialogVisible = true
        },
        handleSizeChange(val) {
            this.pageSize = val
            this.getTableData()
        },
        handlePageChange(val) {
            this.currentPage = val
            this.getTableData()
        },
        handleTopSelectionChange(selection) {
            this.topSelected = selection
        },
        handleBottomSelectionChange(selection) {
            this.bottomSelected = selection
        },
        moveUp() {
            if (this.bottomSelected.length === 0) return
            // remove duplicates from after merging by storageId
            const uniqueBottomSelected = this.bottomSelected.filter(item =>
                !this.topTableData.some(topItem => topItem.storageId === item.storageId)
            );
            this.topTableData.push(...uniqueBottomSelected)
            this.bottomTableData = this.bottomTableData.filter(item => !this.bottomSelected.includes(item))
            this.bottomSelected = []
        },
        moveDown() {
            if (this.topSelected.length === 0) return
            // remove duplicates from after merging by storageId
            const uniqueTopSelected = this.topSelected.filter(item =>
                !this.bottomTableData.some(bottomItem => bottomItem.storageId === item.storageId)
            );
            this.bottomTableData.push(...uniqueTopSelected)
            this.topTableData = this.topTableData.filter(item => !this.topSelected.includes(item))
            this.topSelected = []
        },
        async getTableData() {
            const params = {
                "page": this.currentPage,
                "pageSize": this.pageSize,
                "orderRId": this.orderNumberSearch,
                "shoeRId": this.shoeNumberSearch,
                "customerName": this.customerNameSearch,
                "customerProductName": this.customerProductNameSearch,
                "showAll": 1
            }
            const response = await axios.get(`${this.$apiBaseUrl}/warehouse/getsemifinishedstorages`, { params })
            this.tableData = response.data.result
            this.totalRows = response.data.total
            this.bottomTableData = this.tableData

            const response2 = await axios.get(`${this.$apiBaseUrl}/warehouse/gettotalstockofsemistorage`)
            this.totalStock = response2.data.totalStock
        },
        async viewRecords(row) {
            const params = { "storageId": row.storageId }
            const response = await axios.get(`${this.$apiBaseUrl}/warehouse/warehousemanager/getsemifinishedinoutboundrecords`, { params })
            this.recordData = response.data
            this.isRecordDialogVisible = true
        },
    }
}
</script>