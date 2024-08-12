<template>
    <el-row :gutter="20">
        <el-col :span="24" :offset="0" style="font-size: xx-large; text-align: center"
            >入库/出库历史记录</el-col
        >
    </el-row>
    <el-row :gutter="20">
        <el-col :span="24" :offset="0">
            <el-tabs v-model="currentTab" type="border-card" tab-position="top" @tab-click="">
                <el-tab-pane
                    v-for="item in panes"
                    :key="item.key"
                    :label="item.label"
                    :name="item.key"
                >
                    <el-row :gutter="20">
                        <el-col :span="6" :offset="0">
                            <el-button-group>
                                <el-button
                                v-if="item.key === 1"
                                    type="primary"
                                    size="default"
                                    @click="isMaterialDialogVisible = true"
                                    >根据材料搜索</el-button
                                >
                            </el-button-group>
                        </el-col>
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
                            <div v-if="item.key === 1">
                                <el-table :data="tabInstockData" border stripe height="400">
                                    <el-table-column
                                        prop="materialType"
                                        label="材料类型"
                                    ></el-table-column>
                                    <el-table-column
                                        prop="materialName"
                                        label="材料名称"
                                    ></el-table-column>
                                    <el-table-column
                                        prop="materialSpecification"
                                        label="材料规格"
                                    ></el-table-column>
                                    <el-table-column
                                        prop="materialUnit"
                                        label="材料单位"
                                    ></el-table-column>

                                    <el-table-column
                                        prop="materialPredictNum"
                                        label="材料应入库数量"
                                        :formatter="formatDecimal"
                                    ></el-table-column>
                                    <el-table-column
                                        prop="materialActualNum"
                                        label="材料实入库数量"
                                        :formatter="formatDecimal"
                                    ></el-table-column>
                                    <el-table-column
                                        prop="materialCurrentNum"
                                        label="材料库存"
                                        :formatter="formatDecimal"
                                    ></el-table-column>
                                    <el-table-column
                                        prop="materialUnitPrice"
                                        label="材料单价"
                                        :formatter="formatDecimal"
                                    ></el-table-column>
                                    <el-table-column
                                        prop="materialTotalPrice"
                                        label="材料总价"
                                        :formatter="formatDecimal"
                                    ></el-table-column>
                                    <el-table-column
                                        prop="materialSupplier"
                                        label="材料供应商"
                                    ></el-table-column>
                                    <el-table-column
                                        prop="materialOrderId"
                                        label="材料订单号"
                                    ></el-table-column>
                                    <el-table-column
                                        prop="materialInheritShoeId"
                                        label="材料鞋型号"
                                    ></el-table-column>
                                    <el-table-column
                                        prop="materialStatus"
                                        label="入库状态"
                                    ></el-table-column>
                                    <el-table-column label="操作" width="200">
                                        <template #default="scope">
                                            <el-button
                                                type="primary"
                                                size="small"
                                                @click="editMaterial(scope.row)"
                                                >入/出库记录</el-button
                                            >
                                        </template>
                                    </el-table-column>
                                </el-table>
                            </div>
                            <div v-else>
                                <el-table :data="tabShoeRecord" border stripe height="400">
                                    <el-table-column
                                        prop="orderId"
                                        label="订单号"
                                    ></el-table-column>
                                    <el-table-column
                                        prop="orderShoeId"
                                        label="工厂型号"
                                    ></el-table-column>
                                    <el-table-column
                                        prop="customer"
                                        label="客人号"
                                    ></el-table-column>
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
                                    <el-table-column
                                        prop="materialStatus"
                                        label="入库状态"
                                    ></el-table-column>
                                    <el-table-column label="操作" width="200">
                                        <template #default="scope">
                                            <el-button
                                                type="primary"
                                                size="small"
                                                @click="editMaterial(scope.row)"
                                                >入/出库记录</el-button
                                            >
                                        </template>
                                    </el-table-column>
                                </el-table>
                            </div>
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
                                :total="tabInstockData.length"
                            />
                        </el-col>
                    </el-row>
                </el-tab-pane>
            </el-tabs>
        </el-col>
    </el-row>
    <el-dialog title="材料搜索" v-model="isMaterialDialogVisible" width="30%">
        请选择材料类型：
        <el-select
            v-model="materialTypeSearch"
            value-key=""
            placeholder=""
            clearable
            filterable
            @change=""
            remote
            :remote-method="getMaterialType"
        >
            <el-option
                v-for="item in materialTypeOptions"
                :key="item.value"
                :label="item.label"
                :value="item.value"
            >
            </el-option>
        </el-select>
        请选择材料名称：
        <el-select
            v-model="materialNameSearch"
            value-key=""
            placeholder=""
            clearable
            filterable
            @change=""
            remote
            :remote-method="getMaterialName"
        >
            <el-option
                v-for="item in materialNameOptions"
                :key="item.value"
                :label="item.label"
                :value="item.value"
            >
            </el-option>
        </el-select>
        请选择材料规格：
        <el-select
            v-model="materialSpecificationSearch"
            value-key=""
            placeholder=""
            clearable
            filterable
            @change=""
            remote
            :remote-method="getMaterialSpecification"
        >
            <el-option
                v-for="item in materialSpecificationOptions"
                :key="item.value"
                :label="item.label"
                :value="item.value"
            >
            </el-option>
        </el-select>
        请选择材料供应商：
        <el-select
            v-model="materialSupplierSearch"
            value-key=""
            placeholder=""
            clearable
            filterable
            @change=""
            remote
            :remote-method="getMaterialSupplier"
        >
            <el-option
                v-for="item in materialSupplierOptions"
                :key="item.value"
                :label="item.label"
                :value="item.value"
            >
            </el-option>
        </el-select>

        <template #footer>
            <span>
                <el-button @click="">Cancel</el-button>
                <el-button type="primary" @click="">筛选</el-button>
            </span>
        </template>
    </el-dialog>
    <el-dialog title="材料入库/出库记录" v-model="isRecordDialogVisible" width="60%">
        <el-table :data="recordData" border stripe>
            <el-table-column prop="type" label="操作类型"></el-table-column>
            <el-table-column prop="instockNum" label="操作数量"></el-table-column>
            <el-table-column prop="instockDate" label="操作时间"></el-table-column>
        </el-table>

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
            isRecordDialogVisible: false,
            isMaterialDialogVisible: false,
            pageSize: 10,
            currentPage: 1,
            currentTab: 1,
            tabShoeRecord: [
                {
                    orderId: '订单号',
                    orderShoeId: '工厂型号',
                    customer: '客人号',
                    shoePredictNum: 100,
                    shoeCurrentNum: 100,
                    materialStatus: '入库状态'
                }
            ],
            recordData: [
                {
                    type: '入库',
                    instockNum: 100,
                    instockDate: '2024-06-10 18:00:00',
                    instockSizeNum: [
                        {
                            size: '36',
                            internalSize: '7',
                            externalSize: '7',
                            num: 100
                        }
                    ]
                }
            ],
            tabInstockData: [
                {
                    materialType: '材料类型',
                    materialName: '材料名称',
                    materialSpecification: '材料规格',
                    materialUnit: '材料单位',
                    materialPredictNum: 100,
                    materialActualNum: 100,
                    materialCurrentNum: 100,
                    materialUnitPrice: 100,
                    materialTotalPrice: 100,
                    materialSupplier: '材料供应商',
                    materialOrderId: '材料订单号',
                    materialInheritShoeId: '材料鞋型号',
                    materialStatus: '入库状态'
                }
            ],
            panes: [
                {
                    label: '材料仓',
                    key: 1
                },
                {
                    label: '半成品仓',
                    key: 2
                },
                {
                    label: '成品仓',
                    key: 3
                }
            ]
        }
    },
    methods: {
        formatDecimal(row, column) {
            return row[column.property].toFixed(2)
        },
        handleSizeChange(val) {
            this.pageSize = val
        },
        handleCurrentChange(val) {
            this.currentPage = val
        },
        searchByOrderNumber() {
            console.log('search by order number')
        },
        searchByShoeNumber() {
            console.log('search by shoe number')
        },
        editMaterial(row) {
            console.log('edit material')
            this.isRecordDialogVisible = true
        },
        getMaterialType(query) {
            console.log('get material type')
        },
        getMaterialName(query) {
            console.log('get material name')
        },
        getMaterialSpecification(query) {
            console.log('get material specification')
        },
        getMaterialSupplier(query) {
            console.log('get material supplier')
        }
    }
}
</script>
