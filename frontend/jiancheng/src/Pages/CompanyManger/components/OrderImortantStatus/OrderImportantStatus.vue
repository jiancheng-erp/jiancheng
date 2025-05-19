<template>
    <div class="content">
        <el-row :gutter="16" style="margin-top: 20px; width: 100%">
            <el-col :span="4" :offset="0" style="white-space: nowrap">
                进行中订单号筛选：
                <el-input v-model="orderRIdSearch" placeholder="请输入订单号" clearable />
            </el-col>
            <el-col :span="4" :offset="2" style="white-space: nowrap">
                关键节点筛选:
                <el-select v-model="orderShoeStatus" placeholder="请选择" style="width: 100%">
                    <el-option v-for="item in orderStatusOptions" :key="item.value" :label="item.label"
                        :value="item.value"></el-option>
                </el-select>
            </el-col>
            <el-col :span="4" :offset="2" style="white-space: nowrap">
                工厂型号筛选:
                <el-input v-model="shoeRidSearch" placeholder="请输入工厂型号" size="normal" clearable/>
            </el-col>
            <el-col :span="4" :offset="2" style="white-space: nowrap">
                客户型号筛选:
                <el-input v-model="shoeNameSearch" placeholder="请输入客户型号" size="normal" clearable/>
            </el-col>
            

        </el-row>
        <el-table :data="pagedTableData" style="width: 100%; margin-bottom: 20px; height: 540px" border>
            <el-table-column>
                <el-table-column type="expand">
                    <template #default="props">
                        <el-table :data="props.row.orderShoes"
                            style="width: calc(100% - 48px); margin-bottom: 5px; margin-left: 48px">
                            
                            <el-table-column prop="isMaterialArrived" label="当前材料物流状态" sortable />
                            <el-table-column prop="orderShoeStatus" label="生产状态" sortable />
                            <el-table-column prop="outboundStatus" label="发货状态" sortable />
                        </el-table>
                    </template>
                </el-table-column>
                <el-table-column prop="orderRid" label="订单编号" sortable />
                <el-table-column prop="customerName" label="客户名称" />
                <el-table-column prop="shoeRId" label="工厂型号"/>
                <el-table-column prop="shoeName" label="客户型号"/>
                <el-table-column prop="orderStartDate" label="订单开始日期" />
                <el-table-column label="操作">
                    <template #default="scope">
                        <el-button link type="primary" size="small" @click="
                            edit('edit', scope.row.orderRid + '>' + scope.row.orderId, 'add')
                            ">
                            订单详情
                        </el-button>
                    </template>
                </el-table-column>
            </el-table-column>
        </el-table>
        <el-row :gutter="20" style="justify-content: end; width: 100%">
            <el-pagination @size-change="changeCurrentPageSize" @current-change="changeCurrentPage"
                :current-page="currentPage" :page-sizes="[10, 20, 30, 40]" :page-size="currentPageSize"
                layout="total, sizes, prev, pager, next, jumper" :total="currentTotalRows" />
        </el-row>
    </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import axios from 'axios'
export default {
    data() {
        return {
            orderRIdSearch: '',
            shoeRidSearch: '',
            shoeNameSearch:'',
            currentPage: 1,
            currentPageSize: 10,
            currentTotalRows: 0,
            currentTableData: [],
            currentSelectionRows: [],
            orderShoeStatus: '全部',
            orderStatusOptions: [
                { value: '全部', label: '全部'},
                { value: '投产指令单创建', label: '投产指令单创建' },
                { value: '面料单位用量计算', label: '面料用量填写' },
                { value: '技术部调版分配', label: '工艺单创建' },
                { value: '一次采购订单创建', label: '一次采购订单创建' },
                { value: '总仓采购订单创建', label: '总仓采购订单创建' },
            ],
            Download: 'el-icon-download',
        }
    },
    computed: {
        filteredTableData() {
            return this.currentTableData.filter(order => {
                const matchOrderRid = this.orderRIdSearch
                    ? order.orderRid?.toLowerCase().includes(this.orderRIdSearch.toLowerCase())
                    : true
                const matchOrderShoeStatus = this.orderShoeStatus !== '全部'
                    ? order.orderShoes?.some(shoe => shoe.orderShoeStatus?.includes(this.orderShoeStatus))
                    : true
                const matchShoeRid = this.shoeRidSearch
                    ? order.shoeRId?.toLowerCase().includes(this.shoeRidSearch.toLowerCase())
                    :true
                const matchShoeName = this.shoeNameSearch
                    ? order.shoeName?.toLowerCase().includes(this.shoeNameSearch.toLowerCase())
                    :true
                return matchOrderRid && matchOrderShoeStatus && matchShoeRid && matchShoeName
            })
        },
        pagedTableData() {
            const start = (this.currentPage - 1) * this.currentPageSize
            const end = start + this.currentPageSize
            return this.filteredTableData.slice(start, end)
        }
    },
    watch: {
        filteredTableData: {
            handler(val) {
                this.currentTotalRows = val.length
            },
            immediate: true
        }
    },
    mounted() {
        this.getTableData()
    },
    methods: {
        async getTableData() {
            const res = await axios.get(`${this.$apiBaseUrl}/headmanager/getorderstatusinfo`, {
                params: {
                    orderType: "0",
                }
            })
            this.currentTableData = res.data
            this.currentTotalRows = res.data.length
        },
        changeCurrentPage(val) {
            this.currentPage = val
        },
        changeCurrentPageSize(val) {
            this.currentPageSize = val
            this.currentPage = 1
        }
    }

}

</script>