<template>
    <el-row :gutter="20">
        <el-col :span="24" :offset="0" style="font-size: xx-large; text-align: center"
            >批量采购订单生成及下发</el-col
        >
    </el-row>
    <el-row :gutter="20">
        <el-col :span="4" :offset="0" style="white-space: nowrap">
            采购订单号搜索：
            <el-input
                v-model="purchaseOrderSearch"
                placeholder=""
                size="normal"
                :suffix-icon="Search"
                clearable
                @change="tableFilter"
            ></el-input>
        </el-col>
        <el-col :span="4" :offset="2" style="white-space: nowrap">
            订单号搜索：
            <el-input
                v-model="OrderSearch"
                placeholder=""
                size="normal"
                :suffix-icon="Search"
                clearable
                @change="tableFilter"
            ></el-input>
        </el-col>
        <el-col :span="4" :offset="2" style="white-space: nowrap">
            厂家搜索：
            <el-input
                v-model="supplierSearch"
                placeholder=""
                size="normal"
                :suffix-icon="Search"
                clearable
                @change="tableFilter"
            ></el-input>
        </el-col>
    </el-row>
    <el-row :gutter="20">
        <el-col :span="24" :offset="0">
            <el-tabs v-model="currentTab" type="card" tab-position="top">
                <el-tab-pane label="已下发采购订单" name="1">
                    <el-table :data="finishedPurchaseOrderData" border stripe height="600">
                        <el-table-column type="expand">
                            <template #default="scope">
                                <el-text>采购子订单</el-text>
                                    <el-table :data="scope.row.purchaseDivideOrders" border stripe height="400">
                                        <el-table-column prop="purchaseDivideOrderId" label="采购子订单编号"></el-table-column>
                                        <el-table-column prop="orderId" label="订单号"></el-table-column>
                                        <el-table-column prop="shoeRid" label="工厂型号"></el-table-column>
                                        <el-table-column prop="customerName" label="客户名"></el-table-column>
                                    </el-table>
                            </template>

                        </el-table-column>
                        <el-table-column prop="totalPurchaseOrderId" label="总采购订单编号"></el-table-column>
                        <el-table-column prop="supplierName" label="供应厂商"></el-table-column>
                        <el-table-column label="操作">
                            <template #default="scope">
                                <el-button type="primary" @click="handlePurchaseOrderDetail(scope.row.totalPurchaseOrderId)">查看详情</el-button>
                            </template>
                        </el-table-column>
                    </el-table>
                    
                </el-tab-pane>
                <el-tab-pane label="未下发采购订单" name="0">
                    <el-row :gutter="20">
                        <el-col :span="12" :offset="0">
                            <el-button type="primary" @click="handlePurchaseOrderIssue">由选定下发总采购订单</el-button>
                        </el-col>
                        <el-col :span="12" :offset="0"></el-col>
                    </el-row>
                    
                    <el-row :gutter="20">
                        <el-col :span="24" :offset="0">
                            <el-table :data="unfinishedPurchaseOrderData" border stripe height="600">
                                <el-table-column type="selection"></el-table-column>
                                <el-table-column prop="purchasedivideOrderId" label="采购子订单编号"></el-table-column>
                                <el-table-column prop="supplierName" label="供应厂商"></el-table-column>
                                <el-table-column prop="orderId" label="订单号"></el-table-column>
                                <el-table-column prop="shoeRid" label="工厂型号"></el-table-column>
                                <el-table-column prop="customerName" label="客户名"></el-table-column>
                                <el-table-column label="操作">
                                    <template #default="scope">
                                        <el-button type="primary" @click="handlePurchaseOrderDetail(scope.row.totalPurchaseOrderId)">查看详情</el-button>
                                    </template>
                                </el-table-column>
                            </el-table>
                        </el-col>
                    </el-row>
                    

                    
                </el-tab-pane>
                
            </el-tabs>
            
        </el-col>
    </el-row>
    
    
</template>

<script>
import { Search } from '@element-plus/icons-vue'
import axios from 'axios'

export default {
    data() {
        return {
            unfinishedPurchaseOrderData: [],
            finishedPurchaseOrderData: [],
            currentTab: '1',
            purchaseOrderSearch: '',
            OrderSearch: '',
            supplierSearch: '',
            Search,
        }

    }
}
</script>