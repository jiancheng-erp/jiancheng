<template>
    <el-row :gutter="20">
        <el-col :span="24" :offset="0" style="font-size: xx-large; text-align: center"
            >材料出库</el-col
        >
    </el-row>
    <el-row :gutter="20">
        <el-col :span="6" :offset="0">
            <el-button-group>
                <el-button type="primary" size="default" @click="isMaterialDialogVisible = true"
                    >根据材料出库</el-button
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
            <el-table :data="materialTableFilterData" border stripe height="500">
                <el-table-column prop="materialType" label="材料类型"></el-table-column>
                <el-table-column prop="materialName" label="材料名称"></el-table-column>
                <el-table-column prop="materialSpecification" label="材料规格"></el-table-column>
                <el-table-column prop="materialUnit" label="材料单位"></el-table-column>
                <el-table-column
                    prop="materialPredictNum"
                    label="材料应出库数量"
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
                <el-table-column prop="materialSupplier" label="材料供应商"></el-table-column>
                <el-table-column prop="materialOrderId" label="材料订单号"></el-table-column>
                <el-table-column prop="materialInheritShoeId" label="材料鞋型号"> </el-table-column>
                <el-table-column prop="materialStatus" label="材料订单状态"></el-table-column>
                <el-table-column fixed="right" label="操作" width="200">
                    <template #default="scope">
                        <el-button type="primary" size="mini" @click="editMaterial(scope.row)"
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
                :total="materialTableFilterData.length"
            />
        </el-col>
    </el-row>
    <el-dialog title="材料出库筛选" v-model="isMaterialDialogVisible" width="30%">
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
    <el-dialog title="出库对话框" v-model="isOutstockDialogVisible" width="30%">
            <el-form-item label="出库数量">
                <el-input v-model="outstockForm.quantity" placeholder="请输入出库数量"></el-input>
            </el-form-item>
            <el-form-item label="出库日期">
                <el-date-picker v-model="outstockForm.date" type="date" placeholder="选择日期"></el-date-picker>
            </el-form-item>
            <el-form-item label="出库类型">
                <el-radio-group v-model="outstockForm.outstockType">
                    <el-radio label="1">鞋型使用</el-radio>
                    <el-radio label="2">废料处理</el-radio>
                    <el-radio label="3">外包发货</el-radio>
                </el-radio-group>
            </el-form-item>
            <el-form-item label="出库工段">
                <el-input v-model="outstockForm.section" placeholder="请输入出库工段" :disabled="outstockForm.outstockType !== '1'"></el-input>
            </el-form-item>
            <el-form-item label="领料人">
                <el-input v-model="outstockForm.receiver" placeholder="请输入领料人" :disabled="outstockForm.outstockType !== '1'"></el-input>
            </el-form-item>
            <el-form-item label="外包信息">
            </el-form-item>
            <el-text>材料最迟发货日期：{{ outstockForm.deadlineDate }}</el-text>
            <el-form-item label="发货地址">
                <el-input v-model="outstockForm.address" placeholder="请输入发货地址" :disabled="outstockForm.outstockType !== '3'"></el-input>
            </el-form-item>
        <template #footer>
            <span>
                <el-button @click="cancelInstock">取消</el-button>
                <el-button type="primary" @click="submitInstock">确定</el-button>
            </span>
        </template>
    </el-dialog>
    <el-dialog title="多鞋码出库对话框" v-model="isMultiOutstockDialogVisible" width="50%">
            <el-table :data="multipleOutstockForm" border stripe>
                <el-table-column prop="shoeSize" label="鞋码"></el-table-column>
                <el-table-column prop="internalSize" label="内码"></el-table-column>
                <el-table-column prop="externalSize" label="外显"></el-table-column>
                <el-table-column prop="predictQuantity" label="预计数量"></el-table-column>
                <el-table-column prop="actualQuantity" label="实际数量"></el-table-column>
                <el-table-column prop="currentQuantity" label="材料库存"></el-table-column>
                <el-table-column label="出库数量">
                    <template #default="scope">
                        <el-input v-model="scope.row.outstockQuantity" placeholder="请输入出库数量"></el-input>
                    </template>
                </el-table-column>
            </el-table>
            
            <el-form-item label="出库日期">
                <el-date-picker v-model="outstockForm.date" type="date" placeholder="选择日期"></el-date-picker>
            </el-form-item>
            <el-form-item label="出库类型">
                <el-radio-group v-model="outstockForm.outstockType">
                    <el-radio label="1">内部使用</el-radio>
                    <el-radio label="2">废料处理</el-radio>
                    <el-radio label="3">外包发货</el-radio>
                </el-radio-group>
            </el-form-item>
            <el-form-item label="出库工段">
                <el-input v-model="outstockForm.section" placeholder="请输入出库工段" :disabled="outstockForm.outstockType !== '1'"></el-input>
            </el-form-item>
            <el-form-item label="领料人">
                <el-input v-model="outstockForm.receiver" placeholder="请输入领料人" :disabled="outstockForm.outstockType !== '1'"></el-input>
            </el-form-item>
            <el-form-item label="外包信息">
              
            </el-form-item>
            <el-text>材料最迟发货日期：{{ outstockForm.deadlineDate }}</el-text>
            <el-form-item label="发货地址">
                <el-input v-model="outstockForm.address" placeholder="请输入发货地址" :disabled="outstockForm.outstockType !== '3'"></el-input>
            </el-form-item>
        <template #footer>
            <span>
                <el-button @click="cancelOutstock">取消</el-button>
                <el-button type="primary" @click="submitOutstock">确定</el-button>
            </span>
        </template>
    </el-dialog>
</template>
<script>

export default {
    data() {
        return {
            isMultiOutstockDialogVisible: false,
            materialTypeSearch: '',
            materialNameSearch: '',
            materialSpecificationSearch: '',
            materialSupplierSearch: '',
            materialTypeOptions: [],

            outstockForm: {
                quantity: 0,
                date: '',
                outstockType: '1',
                section: '',
                receiver: '',
                address: '',
                deadlineDate: '',
            },
            isOutstockDialogVisible: false,
            currentPage: 1,
            pageSize: 10,
            orderNumberSearch: '',
            shoeNumberSearch: '',
            materialTableFilterData: [
                {
                    materialType: '材料类型',
                    materialName: '材料名称',
                    materialSpecification: '材料规格',
                    materialUnit: '材料单位',
                    materialPredictNum: 100.00,
                    materialActualNum: 100.00,
                    materialCurrentNum: 100.00,
                    materialUnitPrice: 10000.00,
                    materialTotalPrice: 10000.00,
                    materialSupplier: '材料供应商',
                    materialOrderId: '材料订单号',
                    materialInheritShoeId: '材料鞋型号',
                    materialStatus: '入库状态',
                },
                {
                    materialType: '大底',
                    materialName: '大底材料',
                    materialSpecification: '大底规格',
                    materialUnit: '个',
                    materialPredictNum: 100.00,
                    materialActualNum: 100.00,
                    materialCurrentNum: 100.00,
                    materialUnitPrice: 10000.00,
                    materialTotalPrice: 10000.00,
                    materialSupplier: '材料供应商',
                    materialOrderId: '材料订单号',
                    materialInheritShoeId: '材料鞋型号',
                    materialStatus: '入库状态',
                    materialSizeNum: [
                        {
                            shoeSize: '35',
                            internalSize: '7',
                            externalSize: '7',
                            predictQuantity: 10,
                            actualQuantity: 10,
                            currentQuantity: 10,
                            outstockQuantity: 0,
                        },
                        {
                            shoeSize: '36',
                            internalSize: '7',
                            externalSize: '7.5',
                            predictQuantity: 10,
                            actualQuantity: 10,
                            currentQuantity: 10,
                            outstockQuantity: 0,
                        },
                        {
                            shoeSize: '37',
                            internalSize: '8',
                            externalSize: '8',
                            predictQuantity: 10,
                            actualQuantity: 10,
                            currentQuantity: 10,
                            outstockQuantity: 0,
                        },
                        {
                            shoeSize: '38',
                            internalSize: '8',
                            externalSize: '8.5',
                            predictQuantity: 10,
                            actualQuantity: 10,
                            currentQuantity: 10,
                            outstockQuantity: 0,
                        },
                        {
                            shoeSize: '39',
                            internalSize: '9',
                            externalSize: '9',
                            predictQuantity: 10,
                            actualQuantity: 10,
                            currentQuantity: 10,
                            outstockQuantity: 0,
                        },
                        {
                            shoeSize: '40',
                            internalSize: '9',
                            externalSize: '9.5',
                            predictQuantity: 10,
                            actualQuantity: 10,
                            currentQuantity: 10,
                            outstockQuantity: 0,
                        },
                        {
                            shoeSize: '41',
                            internalSize: '10',
                            externalSize: '10',
                            predictQuantity: 10,
                            actualQuantity: 10,
                            currentQuantity: 10,
                            outstockQuantity: 0,
                        },
                        {
                            shoeSize: '42',
                            internalSize: '10',
                            externalSize: '10.5',
                            predictQuantity: 10,
                            actualQuantity: 10,
                            currentQuantity: 10,
                            outstockQuantity: 0,
                        },
                        {
                            shoeSize: '43',
                            internalSize: '11',
                            externalSize: '11',
                            predictQuantity: 10,
                            actualQuantity: 10,
                            currentQuantity: 10,
                            outstockQuantity: 0,
                        },
                        {
                            shoeSize: '44',
                            internalSize: '12',
                            externalSize: '12',
                            predictQuantity: 10,
                            actualQuantity: 10,
                            currentQuantity: 10,
                            outstockQuantity: 0,
                        }

                    ]
                }
            ],
            isMaterialDialogVisible: false,
            materialDialogData: {}
        }
    },
    methods: {
        handleSizeChange(val) {
            this.pageSize = val
        },
        handleCurrentChange(val) {
            this.currentPage = val
        },
        searchByOrderNumber() {
            this.materialTableFilterData = this.materialTableData.filter((item) => {
                return item.materialOrderNumber.includes(this.orderNumberSearch)
            })
        },
        searchByShoeNumber() {
            this.materialTableFilterData = this.materialTableData.filter((item) => {
                return item.materialInheritShoeId.includes(this.shoeNumberSearch)
            })
        },
        formatDecimal(row, column) {
            return row[column.property].toFixed(2)
        },
        editMaterial(row) {
            console.log(row)
            if (row.materialType === '大底' || row.materialType === '中底' || row.materialType === '鞋楦') {
                this.multipleOutstockForm = row.materialSizeNum
                this.isMultiOutstockDialogVisible = true
            } else {
                this.isOutstockDialogVisible = true
            }
        },
    }
}
</script>
