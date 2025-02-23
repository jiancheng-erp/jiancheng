

<template>
    <el-container direction="vertical">
        <el-main style="height: 100vh;">
            <el-row :gutter="20" style="text-align: center;">
                <el-col :span="24" :offset="0" style="font-size: xx-large; text-align: center;">
                    {{ `包材采购` }}
                </el-col>
            </el-row>
            <el-row :gutter="20">
                <el-col :span="1" :offset="0">
                    <el-text style="white-space: nowrap;">订单筛选：</el-text>
                </el-col>
                <el-col :span="4" :offset="0">
                    <el-input v-model="orderSearch" placeholder="请输入订单号" size="normal" clearable @change=""></el-input>        
                </el-col>
                <el-col :span="4" :offset="0">
                    <el-input v-model="customerSearch" placeholder="请输入客户名" size="normal" clearable @change=""></el-input>
                </el-col>
                <el-col :span="4" :offset="0"></el-col>
            </el-row>
            <el-row :gutter="20">
                <el-col :span="24" :offset="0">
                    <el-table :data="orderList" border stripe height="500" style="width: 100%">
                        <el-table-column prop="orderRid" label="订单号"></el-table-column>
                        <el-table-column prop="orderCid" label="客户订单号"></el-table-column>
                        <el-table-column prop="customerName" label="客户名"></el-table-column>
                        <el-table-column prop="orderStartDate" label="下单日期"></el-table-column>
                        <el-table-column prop="orderStatus" label="包材采购状态"></el-table-column>
                        <el-table-column prop="orderRemark" label="备注"></el-table-column>
                        <el-table-column label="操作" width="180">
                            <template slot-scope="scope">
                                <el-button type="primary" size="mini" @click="handleEdit(scope.row)">编辑</el-button>
                                <el-button type="danger" size="mini" @click="handleDelete(scope.row)">删除</el-button>
                            </template>
                        </el-table-column>
                    </el-table>
                </el-col>
            </el-row>
            
        </el-main>
    </el-container>
</template>

<script>
import axios from 'axios'
export default {
    data() {
        return {
            orderSearch: '',
            customerSearch: '',
            orderList: []
        }
    },
    mounted() {
        this.getAllOrders()
    },
    methods: {
        async getAllOrders() {
            try {
                const response = await axios.get(`${this.$apiBaseUrl}/order/getallorders`)
                this.orderList = response.data
                console.log(this.orderList)
            } catch (error) {
                console.log(error)
            }
        },
        handleSearch() {
            console.log(this.OrderSearch)
        }
    }
}
</script>
        