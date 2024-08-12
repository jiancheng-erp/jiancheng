<template>
    <el-row :gutter="20">
        <el-col :span="24" :offset="0" style="font-size: xx-large; text-align: center"
            >成品仓出/入库</el-col
        >
    </el-row>
    <el-row :gutter="20">
        <el-col :span="4" :offset="0" style="white-space: nowrap">
            订单号筛选：
            <el-input
                v-model="orderNumberSearch"
                placeholder="请输入订单号"
                clearable
                @change="searchByOrderNumber"
            />
        </el-col>
        <el-col :span="4" :offset="2" style="white-space: nowrap">
            鞋型号筛选：
            <el-input
                v-model="shoeNumberSearch"
                placeholder="请输入鞋型号"
                clearable
                @change="searchByShoeNumber"
            />
        </el-col>
    </el-row>
    <el-row :gutter="20">
        <el-col :span="24" :offset="0">
            <el-table :data="shoeFilterData" border stripe height="400">
                <el-table-column prop="orderId" label="订单号"></el-table-column>
                <el-table-column prop="orderShoeId" label="工厂型号"></el-table-column>
                <el-table-column prop="customer" label="客人号"></el-table-column>
                <el-table-column
                    prop="shoePredictNum"
                    label="鞋型应入库数量"
                    :formatter="formatDecimal"
                ></el-table-column>
                <el-table-column
                    prop="shoeCurrentNum"
                    label="鞋型库存"
                    :formatter="formatDecimal"
                ></el-table-column>
                <el-table-column prop="shoeStatus" label="入库状态"></el-table-column>
                <el-table-column label="操作" width="200">
                    <template #default="scope">
                        <el-button
                            v-if="scope.row.shoeStatus !== '已入库'"
                            type="primary"
                            size="mini"
                            @click="InstockDialogVisible = true"
                            >入库</el-button
                        >
                        <el-button
                            v-else
                            type="success"
                            size="mini"
                            @click="OutstockDialogVisible = true"
                            >出库</el-button
                        >
                    </template>
                </el-table-column>
            </el-table>
        </el-col>
    </el-row>
    <el-row :gutter="20">
        <el-col :span="12" :offset="14">
            <el-pagination
                @size-change="handleSizeChange"
                @current-change="handleCurrentChange"
                :current-page="currentPage"
                :page-sizes="[10, 20, 30, 40]"
                :page-size="pageSize"
                layout="total, sizes, prev, pager, next, jumper"
                :total="shoeFilterData.length"
            />
        </el-col>
    </el-row>
    <el-dialog title="成品入库" v-model="InstockDialogVisible" width="30%">
        <el-row :gutter="20">
            <el-col :span="24" :offset="0">
                <el-form label-position="right" label-width="100px">
                    <el-form-item label="入库时间">
                        <el-date-picker
                            v-model="instockDate"
                            type="datetime"
                            placeholder="选择日期时间"
                            style="width: 100%"
                        />
                    </el-form-item>
                    <el-form-item label="入库方式">
                        <el-radio-group v-model="instockType">
                            <el-radio label="1">自产入库</el-radio>
                            <el-radio label="2">外包入库</el-radio>
                        </el-radio-group>
                    </el-form-item>
                </el-form>
            </el-col>
        </el-row>
        <template #footer>
            <span>
                <el-button @click="">Cancel</el-button>
                <el-button type="primary" @click="">OK</el-button>
            </span>
        </template>
    </el-dialog>
    <el-dialog title="半成品出库" v-model="OutstockDialogVisible" width="30%">
        <el-row :gutter="20">
            <el-col :span="24" :offset="0">
                <el-form label-position="right" label-width="100px">
                    <el-form-item label="出库时间">
                        <el-date-picker
                            v-model="outstockForm.outstockDate"
                            type="datetime"
                            placeholder="选择日期时间"
                            style="width: 100%"
                        />
                    </el-form-item>
                    <el-form-item label="" prop="">
                        <el-text>成品最迟发货日期：{{ outstockForm.deadlineDate }}</el-text>
                    </el-form-item>

                    <el-form-item label="发货地址">
                        <el-input
                            v-model="outstockForm.address"
                            placeholder="请输入发货地址"
                        ></el-input>
                    </el-form-item>
                </el-form>
            </el-col>
        </el-row>
        <template #footer>
            <span>
                <el-button @click="">Cancel</el-button>
                <el-button type="primary" @click="">OK</el-button>
            </span>
        </template>
    </el-dialog>
</template>
<script>
export default {
    data() {
        return {
            instockType: '1',
            instockDate: '',
            currentPage: 1,
            pageSize: 10,
            outstockForm: {
                outstockDate: '',
                outstockType: '1',
                section: '',
                receiver: '',
                deadlineDate: '2024-06-10',
                address: ''
            },
            InstockDialogVisible: false,
            OutstockDialogVisible: false,
            shoeFilterData: [
                {
                    orderId: 'K24-024 2111620',
                    orderShoeId: 'K24-024',
                    customer: '2111620',
                    shoePredictNum: 100,
                    shoeCurrentNum: 100,
                    shoeStatus: '已入库'
                },
                {
                    orderId: 'K24-025 2111622',
                    orderShoeId: 'K24-025',
                    customer: '2111622',
                    shoePredictNum: 100,
                    shoeCurrentNum: 100,
                    shoeStatus: '未入库'
                },
                {
                    orderId: 'K24-021 2111620',
                    orderShoeId: 'K24-021',
                    customer: '2111620',
                    shoePredictNum: 100,
                    shoeCurrentNum: 100,
                    shoeStatus: '已入库'
                },
                {
                    orderId: 'K24-021 2111620',
                    orderShoeId: 'K24-021',
                    customer: '2111620',
                    shoePredictNum: 100,
                    shoeCurrentNum: 100,
                    shoeStatus: '已入库'
                },
                {
                    orderId: 'K24-021 2111620',
                    orderShoeId: 'K24-021',
                    customer: '2111620',
                    shoePredictNum: 100,
                    shoeCurrentNum: 100,
                    shoeStatus: '已入库'
                },
                {
                    orderId: 'K24-021 2111620',
                    orderShoeId: 'K24-021',
                    customer: '2111620',
                    shoePredictNum: 100,
                    shoeCurrentNum: 100,
                    shoeStatus: '已入库'
                },
                {
                    orderId: 'K24-021 2111620',
                    orderShoeId: 'K24-021',
                    customer: '2111620',
                    shoePredictNum: 100,
                    shoeCurrentNum: 100,
                    shoeStatus: '已入库'
                },
                {
                    orderId: 'K24-021 2111620',
                    orderShoeId: 'K24-021',
                    customer: '2111620',
                    shoePredictNum: 100,
                    shoeCurrentNum: 100,
                    shoeStatus: '已入库'
                },
                {
                    orderId: 'K24-021 2111620',
                    orderShoeId: 'K24-021',
                    customer: '2111620',
                    shoePredictNum: 100,
                    shoeCurrentNum: 100,
                    shoeStatus: '已入库'
                }
            ],
            orderNumberSearch: '',
            shoeNumberSearch: ''
        }
    },
    methods: {
        searchByOrderNumber() {
            console.log(this.orderNumberSearch)
        },
        searchByShoeNumber() {
            console.log(this.shoeNumberSearch)
        }
    }
}
</script>
