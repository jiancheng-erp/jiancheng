<template>
    <h3>订单状态</h3>
    <el-row :gutter="20">
        <el-col>
            <el-descriptions border>
                <el-descriptions-item label="订单号">{{ orderInfo.orderRId }}</el-descriptions-item>
                <el-descriptions-item label="鞋型号">{{ orderInfo.shoeRId }}</el-descriptions-item>
                <el-descriptions-item label="订单数量">{{ orderAmount }}</el-descriptions-item>
                <el-descriptions-item label="订单状态">{{ orderStatus }}</el-descriptions-item>
                <el-descriptions-item label="订单子状态">{{ orderShoeStatus }}</el-descriptions-item>
            </el-descriptions>
        </el-col>
    </el-row>
</template>
<script>
import axios from 'axios'
export default {
    props: {
        orderInfo: {
            type: Object,
            required: true,
        },
    },
    data(){
        return {
            orderStatus: '',
            orderShoeStatus: '',
            purchaseOrder1Status: '',
            purchaseOrder2Status: '',
            orderAmount: 0,
        }
    },
    async mounted() {
        this.getOrderStatus()
        this.getOrderAmount()
    },
    methods: {
        async getOrderStatus() {
            const params = {
                "orderSearch": this.orderInfo.orderRId,
                "shoeRIdSearch": this.orderInfo.shoeRId
            }
            const response = await axios.get(`${this.$apiBaseUrl}/order/getorderfullinfo`, { params })
            this.orderStatus = response.data.result[0].status
            this.orderShoeStatus = response.data.result[0].shoes[0].statuses
        },
        async getOrderAmount() {
            const params = {
                "orderRId": this.orderInfo.orderRId,
                "shoeRId": this.orderInfo.shoeRId
            }
            const response = await axios.get(`${this.$apiBaseUrl}/production/getallordershoeinfo`, { params })
            this.orderAmount = response.data.result[0].orderAmount
        },
    },
}
</script>