<template>
    <el-row :gutter="20">
        <el-col :span="24" :offset="0" style="font-size: xx-large; text-align: center">成品出/入库</el-col>
    </el-row>
    <el-row :gutter="20">
        <el-col :span="4" :offset="0" style="white-space: nowrap;">
            订单号筛选：
            <el-input v-model="orderNumberSearch" placeholder="请输入订单号" clearable @keypress.enter="getTableData()"
                @clear="getTableData" />
        </el-col>
        <el-col :span="4" :offset="2" style="white-space: nowrap;">
            鞋型号筛选：
            <el-input v-model="shoeNumberSearch" placeholder="请输入鞋型号" clearable @keypress.enter="getTableData()"
                @clear="getTableData" />
        </el-col>
    </el-row>
    <el-row :gutter="20">
        <el-col :span="24" :offset="0">
            <el-table :data="tableData" border stripe height="400">
                <el-table-column prop="orderRId" label="订单号"></el-table-column>
                <el-table-column prop="shoeRId" label="工厂型号"></el-table-column>
                <el-table-column prop="customerProductName" label="客户型号"></el-table-column>
                <el-table-column prop="colorName" label="颜色"></el-table-column>
                <el-table-column prop="inboundAmount" label="鞋型应入库数量"></el-table-column>
                <el-table-column prop="currentAmount" label="鞋型库存"></el-table-column>
                <el-table-column prop="statusName" label="状态"></el-table-column>
                <el-table-column label="操作" width="300">
                    <template #default="scope">
                        <el-button-group>
                            <el-button type="primary" size="small" @click="openInboundDialog(scope.row)">入库</el-button>
                            <el-button type="success" size="small" @click="openOutboundDialog(scope.row)">出库</el-button>
                            <el-button v-if="scope.row.statusName === '未完成入库'" type="warning" size="small"
                                @click="finishInbound(scope.row)">完成入库</el-button>
                            <el-button v-if="scope.row.statusName === '已完成入库'" type="warning" size="small"
                                @click="finishOutbound(scope.row)">完成出库</el-button>
                        </el-button-group>
                    </template>
                </el-table-column>
            </el-table>
        </el-col>
    </el-row>
    <el-row :gutter="20">
        <el-col :span="12" :offset="14">
            <el-pagination @size-change="handleSizeChange" @current-change="handlePageChange"
                :current-page="currentPage" :page-sizes="[10, 20, 30, 40]" :page-size="pageSize"
                layout="total, sizes, prev, pager, next, jumper" :total="totalRows" />
        </el-col>
    </el-row>
    <el-dialog title="成品入库" v-model="inboundDialogVisible" width="35%">
        <el-row :gutter="20">
            <el-col :span="24" :offset="0">
                <el-form :model="inboundForm" label-position="right" :rules="rules" ref="inboundForm"
                    label-width="100px">
                    <el-form-item prop="inboundDate" label="入库时间">
                        <el-date-picker v-model="inboundForm.inboundDate" type="datetime" placeholder="选择日期时间"
                            style="width: 100%" value-format="YYYY-MM-DD HH:mm:ss" />
                    </el-form-item>
                    <el-form-item prop="actualInboundAmount" label="入库数量">
                        <el-input-number v-model="inboundForm.actualInboundAmount" :min="0"></el-input-number>
                    </el-form-item>
                    <el-form-item prop="inboundType" label="入库类型">
                        <el-radio-group v-model="inboundForm.inboundType">
                            <el-radio :value="0">自产</el-radio>
                            <el-radio :value="1">外包</el-radio>
                        </el-radio-group>
                    </el-form-item>
                    <el-table v-if="inboundForm.inboundType == 1" :data="inboundForm.outsourceInfo" style="width: 100%">
                        <el-table-column width="55">
                            <template #default="scope">
                                <el-radio v-model="inboundForm.selectedOutsource" :value="scope.row.outsourceInfoId" />
                            </template>
                        </el-table-column>
                        <el-table-column prop="outsourceFactory.value" label="工厂名称" />
                        <el-table-column prop="outsourceAmount" label="外包数量" />
                        <el-table-column prop="outsourceType" label="外包类型" />
                        <el-table-column label="操作">
                            <template #default="scope">
                                <el-button :disabled="inboundForm.selectedOutsource !== scope.row.outsourceInfoId"
                                    type="warning" size="small" @click="finishOutsourceInbound(scope.row)">
                                    完成外包入库
                                </el-button>
                            </template>
                        </el-table-column>
                    </el-table>
                </el-form>
            </el-col>
        </el-row>
        <template #footer>
            <span>
                <el-button @click="inboundDialogVisible = false">返回</el-button>
                <el-button type="primary" @click="submitInboundForm">入库</el-button>
            </span>
        </template>
    </el-dialog>
    <el-dialog title="成品出库" v-model="outboundDialogVisible" width="30%">
        <el-row :gutter="20">
            <el-col :span="24" :offset="0">
                <el-form label-position="right" label-width="100px">
                    <el-form-item label="出库时间">
                        <el-date-picker v-model="outboundForm.outboundDate" type="datetime" placeholder="选择日期时间"
                            style="width: 100%" value-format="YYYY-MM-DD HH:mm:ss" />
                    </el-form-item>
                    <el-form-item label="" prop="">
                        <el-text>成品最迟发货日期：{{ currentRow.endDate }}</el-text>
                    </el-form-item>

                    <el-form-item label="发货地址">
                        <el-input v-model="outboundForm.address" placeholder="请输入发货地址"></el-input>
                    </el-form-item>
                    <el-form-item label="出货选项">
                        <el-checkbox v-model="outboundForm.isOutboundAll" label="出货该订单所有鞋型" size="large" />
                    </el-form-item>
                </el-form>
            </el-col>
        </el-row>
        <template #footer>
            <span>
                <el-button @click="outboundDialogVisible = false">返回</el-button>
                <el-button type="primary" @click="submitOutboundForm">出库</el-button>
            </span>
        </template>
    </el-dialog>
</template>
<script>
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus';
export default {
    data() {
        return {
            inboundForm: {
                inboundDate: '',
                actualInboundAmount: 0,
                outsourceInfo: [],
                selectedOutsource: null,
                inboundType: 0
            },
            currentPage: 1,
            pageSize: 10,
            outboundForm: {
                outboundDate: '',
                outboundType: '1',
                section: '',
                receiver: '',
                deadlineDate: '',
                address: '',
                isOutboundAll: false
            },
            inboundDialogVisible: false,
            outboundDialogVisible: false,
            tableData: [],
            totalRows: 0,
            currentRow: {},
            orderNumberSearch: '',
            shoeNumberSearch: '',
            rules: {
                inboundDate: [
                    { required: true, message: '此项为必填项', trigger: 'change' },
                ],
                actualInboundAmount: [
                    {
                        required: true,
                        validator: (rule, value, callback) => {
                            if (value === 0 || !value) {
                                callback(new Error('入库数量不能为0'));
                            } else {
                                callback();
                            }
                        },
                        trigger: 'change'
                    }
                ],
                inboundType: [
                    { required: true, message: '此项为必填项', trigger: 'change' },
                ],
            },
        }
    },
    mounted() {
        this.getTableData()
    },
    methods: {
        async getTableData() {
            const params = {
                "page": this.currentPage,
                "pageSize": this.pageSize,
                "orderRId": this.orderNumberSearch,
                "shoeRId": this.shoeNumberSearch,
                "opType": 1
            }
            const response = await axios.get(`${this.$apiBaseUrl}/warehouse/warehousemanager/getfinishedinoutoverview`, { params })
            this.tableData = response.data.result
            this.totalRows = response.data.total
        },
        async submitInboundForm() {
            this.$refs.inboundForm.validate(async (valid) => {
                if (valid) {
                    let data = {
                        "orderId": this.currentRow.orderId,
                        "orderShoeId": this.currentRow.orderShoeId,
                        "storageId": this.currentRow.storageId,
                        "inboundDate": this.inboundForm.inboundDate,
                        "amount": this.inboundForm.actualInboundAmount
                    }
                    await axios.patch(`${this.$apiBaseUrl}/warehouse/warehousemanager/inboundfinished`, data)
                    try {
                        ElMessage.success("入库成功")
                    }
                    catch (error) {
                        console.log(error)
                        ElMessage.error("入库失败")
                    }
                    this.inboundDialogVisible = false
                    this.getTableData()
                }
                else {
                    console.log("Form has validation errors.");
                }
            })

        },
        async submitOutboundForm() {
            let data = {
                "orderId": this.currentRow.orderId,
                "orderShoeId": this.currentRow.orderShoeId,
                "storageId": this.currentRow.storageId,
                "outboundDate": this.outboundForm.outboundDate,
                "outboundAddress": this.outboundForm.address,
                "isOutboundAll": this.outboundForm.isOutboundAll
            }
            const response = await axios.patch(`${this.$apiBaseUrl}/warehouse/warehousemanager/outboundfinished`, data)
            if (response.status == 200) {
                ElMessage.success("出库成功")
            }
            else {
                ElMessage.error("出库失败")
            }
            this.outboundDialogVisible = false
            this.getTableData()
        },
        handleSizeChange(val) {
            this.pageSize = val
            this.getTableData()
        },
        handlePageChange(val) {
            this.page = val
            this.getTableData()
        },
        async getOutsourceInfoForInbound() {
            let params = { "orderShoeId": this.currentRow.orderShoeId }
            let response = await axios.get(`${this.$apiBaseUrl}/production/productionmanager/getordershoeoutsourceinfo`, { params })
            this.inboundForm.outsourceInfo = []
            response.data.forEach(element => {
                let length = element.outsourceType.length
                if (element.outsourceStatus == 5 || element.outsourceStatus == 6) {
                    if (element.outsourceType[length - 1] === '成型') {
                        this.inboundForm.outsourceInfo.push(element)
                    }
                }
            });
            if (this.inboundForm.outsourceInfo.length > 0) {
                this.inboundForm.selectedOutsource = this.inboundForm.outsourceInfo[0].outsourceInfoId
            }
        },
        async openInboundDialog(row) {
            this.currentRow = row
            await this.getOutsourceInfoForInbound()
            this.inboundDialogVisible = true
        },
        async finishInbound(row) {
            ElMessageBox.alert('该操作完成对此鞋型成品入库，是否继续？', '警告', {
                confirmButtonText: '确认',
                showCancelButton: true,
                cancelButtonText: '取消'
            }).then(async () => {
                const data = { "storageId": row.storageId }
                await axios.patch(`${this.$apiBaseUrl}/warehouse/warehousemanager/completeinboundfinished`, data)
                try {
                    ElMessage.success("操作成功")
                }
                catch (error) {
                    console.log(error)
                    ElMessage.error("操作异常")
                }
                this.getTableData()
            })
        },
        async finishOutsourceInbound(row) {
            try {
                let data = { "outsourceInfoId": row.outsourceInfoId }
                await axios.patch(`${this.$apiBaseUrl}/warehouse/warehousemanager/finishoutsourceinbound`, data)
                ElMessage.success("外包入库成功")
                await this.getOutsourceInfoForInbound()
            }
            catch (error) {
                console.log(error)
                ElMessage.error("外包入库失败")
            }
        },
        async finishOutbound(row) {
            ElMessageBox.alert('该操作完成对此鞋型成品出库，是否继续？', '警告', {
                confirmButtonText: '确认',
                showCancelButton: true,
                cancelButtonText: '取消'
            }).then(async () => {
                const data = { "storageId": row.storageId }
                await axios.patch(`${this.$apiBaseUrl}/warehouse/warehousemanager/completeoutboundfinished`, data)
                try {
                    ElMessage.success("操作成功")
                }
                catch (error) {
                    console.log(error)
                    ElMessage.error("操作异常")
                }
                this.getTableData()
            })
        },
        openOutboundDialog(row) {
            this.outboundDialogVisible = true
            this.currentRow = row
        }
    }
}
</script>
