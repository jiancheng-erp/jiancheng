<template>
    <el-row :gutter="20">
        <el-col :span="6">
            <el-date-picker v-model="dateRange" type="daterange" range-separator="至" start-placeholder="开始日期"
                end-placeholder="结束日期" value-format="YYYY-MM-DD" @change="getInboundRecordsTable"
                @clear="getInboundRecordsTable" clearable>
            </el-date-picker>
        </el-col>
        <el-col :span="4" :offset="1">
            <el-input v-model="supplierNameSearch" placeholder="请输入厂家名称" @change="getInboundRecordsTable"
                @clear="getInboundRecordsTable" clearable>
            </el-input>
        </el-col>
        <el-col :span="4" :offset="0">
            <el-input v-model="inboundRIdSearch" placeholder="请输入入库单号" @change="getInboundRecordsTable"
                @clear="getInboundRecordsTable" clearable>
            </el-input>
        </el-col>
        <el-col :span="4" :offset="0">
            <el-select v-model="statusSearch" @change="getInboundRecordsTable" @clear="getInboundRecordsTable"
                clearable>
                <el-option label="全部" :value="-1"></el-option>
                <el-option label="待审核" :value="0"></el-option>
                <el-option label="已批准" :value="1"></el-option>
                <el-option label="已驳回" :value="2"></el-option>
            </el-select>
        </el-col>
    </el-row>
    <el-row :gutter="20">
        <el-col :span="24">
            <el-table :data="tableData" border>
                <el-table-column prop="inboundRId" label="入库单号"></el-table-column>
                <el-table-column prop="supplierName" label="供货单位"></el-table-column>
                <el-table-column label="入库类型">
                    <template #default="scope">
                        {{ determineInboundName(scope.row.inboundType) }}
                    </template>
                </el-table-column>
                <el-table-column prop="warehouseName" label="仓库名称">
                </el-table-column>
                <el-table-column prop="timestamp" label="操作时间"></el-table-column>
                <el-table-column prop="rejectReason" label="驳回原因"></el-table-column>
                <el-table-column label="查看">
                    <template #default="scope">
                        <el-button-group>
                            <el-button type="primary" @click="handleView(scope.row)">查看</el-button>
                            <el-button v-if="role == 24 && scope.row.approvalStatus === 0" type="success"
                                @click="handleApproval(scope.row)">批准</el-button>
                            <el-button v-if="role == 24 && scope.row.approvalStatus === 0" type="warning"
                                @click="openRejectDialog(scope.row)">驳回</el-button>
                            <el-button v-if="role == 23 && scope.row.approvalStatus === 2" type="warning"
                                @click="handleEdit(scope.row)">编辑</el-button>
                            <!-- <el-button type="danger" @click="handleDelete(scope.row)">删除</el-button> -->
                        </el-button-group>
                    </template>
                </el-table-column>
            </el-table>
        </el-col>
    </el-row>
    <el-row :gutter="20">
        <el-col :span="12" :offset="10">
            <el-pagination @size-change="handleSizeChange" @current-change="handlePageChange"
                :current-page="currentPage" :page-sizes="[10, 20, 30, 40]" :page-size="pageSize"
                layout="total, sizes, prev, pager, next, jumper" :total="total" />
        </el-col>
    </el-row>

    <el-dialog title="入库单详情" v-model="dialogVisible" width="90%">
        <div id="printView">
            <h2 style="text-align: center;">健诚鞋业入库单</h2>
            <div style="display: flex; justify-content: flex-end; padding: 5px;">
                <span style="font-weight: bolder;font-size: 16px;">
                    单据编号：{{ currentRow.inboundRId }}
                </span>
            </div>
            <table class="table" border="0pm" cellspacing="0" align="left" width="100%"
                style="font-size: 16px;margin-bottom: 10px; table-layout:fixed;word-wrap:break-word;word-break:break-all">
                <tr>
                    <td style="padding:5px; width: 150px;" align="left">供应商:{{ currentRow.supplierName }}</td>
                    <td style="padding:5px; width: 150px;" align="left">仓库名称:{{ currentRow.warehouseName }}</td>
                    <td style="padding:5px; width: 300px;" align="left">入库时间:{{ currentRow.timestamp }}</td>
                    <td style="padding:5px; width: 150px;" align="left">结算方式:{{ currentRow.payMethod }}</td>
                </tr>
            </table>
            <table class="yk-table" border="1pm" cellspacing="0" align="center" width="100%"
                style="font-size: 16px; table-layout:fixed;word-wrap:break-word;word-break:break-all">
                <tr>
                    <th width="80">材料名</th>
                    <th width="80">型号</th>
                    <th width="200">规格</th>
                    <th width="60">颜色</th>
                    <th width="40">单位</th>
                    <th width="100">订单号</th>
                    <th v-if="recordData.items.length > 0 && recordData.items[0].materialName === '大底'" width="40"
                        v-for="(column, index) in filteredShoeSizeColumns" :key="index">{{ column.label }}</th>
                    <th v-else width="90">数量</th>
                    <th v-if="currentRow.inboundType != 2" width="60">单价</th>
                    <th v-if="currentRow.inboundType == 2" width="60">复合单价</th>
                    <th width="80">总价</th>
                    <th width="100">备注</th>
                </tr>
                <tr v-for="(item, index) in recordData.items" :key="index" align="center">
                    <td>{{ item.materialName }}</td>
                    <td>{{ item.materialModel }}</td>
                    <td>{{ item.materialSpecification }}</td>
                    <td>{{ item.colorName }}</td>
                    <td>{{ item.actualInboundUnit }}</td>
                    <td>{{ item.orderRId }}</td>
                    <td v-if="recordData.items.length > 0 && recordData.items[0].materialName === '大底'"
                        v-for="(column, index) in filteredShoeSizeColumns" :key="index">{{ item[column.prop] }}
                    </td>
                    <td v-else>{{ item.inboundQuantity }}</td>
                    <td v-if="currentRow.inboundType != 2">{{ item.unitPrice }}</td>
                    <td v-if="currentRow.inboundType == 2">{{ item.compositeUnitCost }}</td>
                    <td>{{ item.itemTotalPrice }}</td>
                    <td>{{ item.remark }}</td>
                </tr>
            </table>
            <div style="margin-top: 20px; font-size: 16px; font-weight: bold;">
                <div style="display: flex;">
                    <span style="padding-right: 10px;">合计数量: <span style="text-decoration: underline;">{{
                        calculateInboundTotal() }}</span></span>
                    <span style="padding-right: 10px;">合计金额: <span style="text-decoration: underline;">{{
                        currentRow.totalPrice }}</span></span>
                    <span style="padding-right: 10px;">备注: <span style="text-decoration: underline;">{{
                        currentRow.remark
                            }}</span></span>
                </div>
            </div>
        </div>
        <template #footer>
            <el-button type="primary" @click="dialogVisible = false">返回</el-button>
            <el-button type="primary" v-print="'#printView'">打印</el-button>
            <el-button type="primary"
                @click="downloadPDF(`健诚鞋业入库单${currentRow.inboundRId}`, `printView`)">下载PDF</el-button>
        </template>
    </el-dialog>

    <el-dialog title="修改入库单" v-model="editDialogVisible" width="100%">
        <el-row>
            <el-col :span="6">
                <div style="display: flex; align-items: center;">
                    <span style="margin-right: 8px; width: 80px">供货单位:</span>
                    <el-autocomplete v-model="currentRow.newSupplierName" :fetch-suggestions="querySuppliers" clearable
                        @select="handleSupplierSelect" />
                </div>
            </el-col>
            <el-col :span="6" :offset="1">
                <div style="display: flex; align-items: center;">
                    <span style="margin-right: 8px; width: 80px">付款方式:</span>
                    <el-input v-model="currentRow.payMethod" disabled></el-input>
                </div>
            </el-col>
            <el-col :span="6" :offset="1">
                <div style="display: flex; align-items: center;">
                    <span style="margin-right: 8px; width: 80px">入库备注:</span>
                    <el-input v-model="currentRow.remark"></el-input>
                </div>
            </el-col>
        </el-row>
        <el-row>
            <el-col>
                <el-table :data="recordData.items" border stripe>
                    <el-table-column label="材料名">
                        <template #default="scope">
                            <el-select v-model="scope.row.materialName" filterable clearable>
                                <el-option v-for="(item, index) in materialNameOptions" :key="index" :label="item.label"
                                    :value="item.value"></el-option>
                            </el-select>
                        </template>
                    </el-table-column>
                    <el-table-column label="型号">
                        <template #default="scope">
                            <el-input v-model="scope.row.materialModel"></el-input>
                        </template>
                    </el-table-column>
                    <el-table-column label="规格">
                        <template #default="scope">
                            <el-input v-model="scope.row.materialSpecification"></el-input>
                        </template>
                    </el-table-column>
                    <el-table-column label="颜色">
                        <template #default="scope">
                            <el-input v-model="scope.row.colorName"></el-input>
                        </template>
                    </el-table-column>
                    <el-table-column label="单位">
                        <template #default="scope">
                            <el-select v-model="scope.row.actualInboundUnit" filterable clearable>
                                <el-option v-for="item in unitOptions" :key="item.value" :value="item.value"
                                    :label="item.label"></el-option>
                            </el-select>
                        </template>
                    </el-table-column>
                    <el-table-column label="订单号">
                        <template #default="scope">
                            <el-input v-model="scope.row.orderRId"></el-input>
                        </template>
                    </el-table-column>
                    <el-table-column label="数量">
                        <template #default="scope">
                            <el-input-number v-model="scope.row.inboundQuantity" :step="0.001" :min="0" :precision="3"
                                size="small" @change="updateTotalPrice(scope.row)"></el-input-number>
                        </template>
                    </el-table-column>
                    <el-table-column label="单价">
                        <template #default="scope">
                            <el-input-number v-model="scope.row.unitPrice" :step="0.001" :min="0" :precision="3"
                                size="small" @change="updateTotalPrice(scope.row)"></el-input-number>
                        </template>
                    </el-table-column>
                    <el-table-column label="总价">
                        <template #default="scope">
                            <el-input-number v-model="scope.row.itemTotalPrice" :step="0.001" :min="0" :precision="3"
                                size="small"></el-input-number>
                        </template>
                    </el-table-column>
                    <el-table-column label="备注">
                        <template #default="scope">
                            <el-input v-model="scope.row.remark"></el-input>
                        </template>
                    </el-table-column>
                    <el-table-column label="删除" width="80">
                        <template #default="scope">
                            <el-switch v-model="scope.row.toDelete" 
                            :active-value="1" :inactive-value="0"
                            @change="(value) => markDelete(scope.row, value)" />
                        </template>
                    </el-table-column>
                </el-table>
            </el-col>
        </el-row>
        <template #footer>
            <el-button type="primary" @click="editDialogVisible = false">返回</el-button>
            <el-button type="primary" @click="updateInboundRecord">提交</el-button>
        </template>
    </el-dialog>

    <el-dialog title="驳回确认" v-model="rejectDialogVisible" width="40%">
        <!-- Textarea with character limit -->
        <el-input type="textarea" v-model="rejectText" :maxlength="255" show-word-limit>
        </el-input>
        <template #footer>
            <el-button @click="rejectDialogVisible = false">返回</el-button>
            <el-button type="primary" @click="handleReject()">驳回</el-button>
        </template>
    </el-dialog>
</template>
<script>
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus';
import htmlToPdf from '@/Pages/utils/htmlToPdf';
import print from 'vue3-print-nb'
import { updateTotalPriceHelper } from '@/Pages/utils/warehouseFunctions';
export default {
    directives: {
        print
    },
    props: {
        materialSupplierOptions: {
            type: Array,
            required: true
        }
    },
    data() {
        return {
            role: localStorage.getItem('role'),
            printLoading: true,
            printObj: {
                id: 'printView', // 需要打印的区域id
                preview: true, // 打印预览
                previewTitle: '打印预览',
                popTitle: 'good print',
                extraHead: '<meta http-equiv="Content-Language"content="zh-cn"/>',
                beforeOpenCallback(vue) {
                    console.log('打开之前')
                },
                openCallback(vue) {
                    console.log('执行了打印')
                },
                closeCallback(vue) {
                    console.log('关闭了打印工具')
                }
            },
            currentPage: 1,
            pageSize: 10,
            tableData: [],
            total: 0,
            currentRow: {},
            recordData: {},
            dialogVisible: false,
            dateRange: [null, null],
            inboundRIdSearch: null,
            supplierNameSearch: null,
            editDialogVisible: false,
            materialNameOptions: [],
            unitOptions: [],
            rejectDialogVisible: false,
            rejectText: '',
            statusSearch: 0,
        }
    },
    mounted() {
        this.getInboundRecordsTable()
    },
    computed: {
        filteredShoeSizeColumns() {
            return this.recordData.shoeSizeColumns.filter(column =>
                this.recordData.items.some(row => row[column.prop] !== undefined && row[column.prop] !== null && row[column.prop] !== 0)
            )
        }
    },
    methods: {
        querySuppliers(queryString, callback) {
            const results = this.materialSupplierOptions
                .filter((item) => item.toLowerCase().includes(queryString.toLowerCase()))
                .map((item) => ({ value: item }));

            callback(results);
        },
        handleSupplierSelect(item) {
            this.currentRow.newSupplierName = item.value;
        },
        updateTotalPrice(row) {
            row.itemTotalPrice = updateTotalPriceHelper(row)
        },
        calculateInboundTotal() {
            // Calculate the total inbound quantity
            const number = this.recordData.items.reduce((total, item) => {
                return total + (Number(item.inboundQuantity) || 0);
            }, 0);
            return Number(number).toFixed(2);
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
            if (this.dateRange === null) {
                this.dateRange = [null, null]
            }
            try {
                let params = {
                    page: this.currentPage,
                    pageSize: this.pageSize,
                    startDate: this.dateRange[0],
                    endDate: this.dateRange[1],
                    inboundRId: this.inboundRIdSearch,
                    supplierName: this.supplierNameSearch,
                    status: this.statusSearch
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
            this.currentPage = val
            this.getInboundRecordsTable()
        },
        async getInboundRecordDetail(row) {
            try {
                let params = { "inboundBatchId": row.inboundBatchId, "isSizedMaterial": row.isSizedMaterial }
                let response = await axios.get(`${this.$apiBaseUrl}/warehouse/getinboundrecordbybatchid`, { params })
                this.recordData["items"] = response.data
                // convert decimal to number
                for (let i = 0; i < this.recordData["items"].length; i++) {
                    this.recordData["items"][i].inboundQuantity = Number(this.recordData["items"][i].inboundQuantity)
                    this.recordData["items"][i].unitPrice = Number(this.recordData["items"][i].unitPrice)
                    this.recordData["items"][i].itemTotalPrice = Number(this.recordData["items"][i].itemTotalPrice)
                }
                // if the purchase divide order type is S, then the inbound record is for shoe size
                if (row.isSizedMaterial == 1) {
                    let sizeColumns = []
                    let tempTable = []
                    let firstItem = this.recordData["items"][0]
                    sizeColumns = firstItem.shoeSizeColumns
                    for (let i = 0; i < sizeColumns.length; i++) {
                        let obj = { "label": sizeColumns[i], "prop": `amount${i}` }
                        tempTable.push(obj)
                    }
                    this.recordData["shoeSizeColumns"] = tempTable
                }
            }
            catch (error) {
                console.log(error)
                ElMessage.error('获取入库单详情失败')
            }
        },
        async handleView(row) {
            this.currentRow = row
            await this.getInboundRecordDetail(row)
            this.dialogVisible = true
        },
        async getMaterialNameOptions() {
            const response = await axios.get(`${this.$apiBaseUrl}/logistics/getallmaterialname`)
            this.materialNameOptions = response.data
        },
        async getUnitOptions() {
            const response = await axios.get(`${this.$apiBaseUrl}/logistics/getallunit`)
            this.unitOptions = response.data
        },
        async handleEdit(row) {
            if (row.inboundType != 0) {
                ElMessage.error('只能编辑采购入库单')
                return
            }
            this.currentRow = row
            this.currentRow.newSupplierName = row.supplierName
            this.getInboundRecordDetail(row)
            this.getMaterialNameOptions()
            this.getUnitOptions()
            this.editDialogVisible = true
        },
        async handleApproval() {
            this.$confirm('是否批准该入库单？', '提示', {
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                type: 'warning'
            }).then(async () => {
                try {
                    let params = { "inboundRecordId": this.currentRow.inboundRecordId }
                    await axios.patch(`${this.$apiBaseUrl}/accounting/approveinboundrecord`, params)
                    ElMessage.success('批准成功')
                    this.getInboundRecordsTable()
                } catch (error) {
                    if (error.response) {
                        // Flask returns error in JSON format
                        this.errorMessage = error.response.data.message || "An error occurred";
                    } else {
                        this.errorMessage = "服务器异常";
                    }
                    ElMessage.error(this.errorMessage)
                    console.error("API Error:", error);
                }
            }).catch(() => {
                ElMessage.info('已取消批准')
            })
        },
        async updateInboundRecord() {
            ElMessageBox.confirm('是否提交修改？', '提示', {
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                type: 'warning'
            }).then(async () => {
                try {
                    let params = {
                        "inboundRecordId": this.currentRow.inboundRecordId,
                        "supplierName": this.currentRow.newSupplierName,
                        "inboundType": this.currentRow.inboundType,
                        "remark": this.currentRow.remark,
                        "payMethod": this.currentRow.payMethod,
                        "isSizedMaterial": this.currentRow.isSizedMaterial,
                        "items": this.recordData.items
                    }
                    await axios.patch(`${this.$apiBaseUrl}/warehouse/updateinboundrecord`, params)
                    ElMessage.success('修改成功')
                    this.editDialogVisible = false
                    this.getInboundRecordsTable()
                } catch (error) {
                    if (error.response) {
                        // Flask returns error in JSON format
                        this.errorMessage = error.response.data.message || "An error occurred";
                    } else {
                        this.errorMessage = "服务器异常";
                    }
                    ElMessage.error(this.errorMessage)
                    console.error("API Error:", error);
                }
            }).catch(() => {
                ElMessage.info('已取消修改')
            })

        },
        openRejectDialog(row) {
            this.currentRow = row
            this.rejectDialogVisible = true
        },
        handleReject() {
            this.$confirm('是否驳回该入库单？', '提示', {
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                type: 'warning'
            }).then(async () => {
                try {
                    let params = { "inboundRecordId": this.currentRow.inboundRecordId, "rejectReason": this.rejectText }
                    await axios.patch(`${this.$apiBaseUrl}/accounting/rejectinboundrecord`, params)
                    ElMessage.success('驳回成功')
                    this.rejectDialogVisible = false
                    this.rejectText = ''
                    this.getInboundRecordsTable()
                } catch (error) {
                    if (error.response) {
                        // Flask returns error in JSON format
                        this.errorMessage = error.response.data.message || "An error occurred";
                    } else {
                        this.errorMessage = "服务器异常";
                    }
                    ElMessage.error(this.errorMessage)
                    console.error("API Error:", error);
                }
            }).catch(() => {
                ElMessage.info('已取消驳回')
            })
        },
        markDelete(row, newVal) {
            row.toDelete = newVal
        },
        handleDelete(row) {
            this.$confirm('是否删除该入库单？', '提示', {
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                type: 'warning'
            }).then(async () => {
                try {
                    let params = { "inboundRecordId": row.inboundRecordId }
                    await axios.delete(`${this.$apiBaseUrl}/warehouse/deleteinboundrecord`, { params })
                    ElMessage.success('删除成功')
                    this.getInboundRecordsTable()
                } catch (error) {
                    if (error.response) {
                        // Flask returns error in JSON format
                        this.errorMessage = error.response.data.message || "An error occurred";
                    } else {
                        this.errorMessage = "服务器异常";
                    }
                    ElMessage.error(this.errorMessage)
                    console.error("API Error:", error);
                }
            }).catch(() => {
                ElMessage.info('已取消删除')
            })
        }
    }
}
</script>
<style>
#printView {
    padding-left: 20px;
    padding-right: 20px;
    color: black;
    font-family: SimHei;
}
</style>