<template>
    <div>
      <el-table
        :data="inproductiontableData"
        style="width: 100%; margin-bottom: 20px"
        row-key="id"
        border
        default-expand-all
      >
      <el-table-column label="生产中订单">
        <el-table-column prop="customerId" label="客人编号" sortable />
        <el-table-column prop="productionstartDate" label="生产开始日期" sortable />
        <el-table-column prop="totalQuantity" label="订单总数量" sortable/> 
        <el-table-column prop="prodStatus" label="生产状态" sortable />
        <el-table-column prop="remainingQuantity" label="剩余数量" sortable/> 
        <el-table-column prop="estimatedproductionDate" label="预计完成时间" sortable/>
        <el-table-column prop="deliverDate" label="截止日期" sortable />
        <el-table-column label="操作">
            <template #default="scope">
            <el-button link type="primary" size="small" @click="openNewWindow(scope.row)">
            订单详情
            </el-button>
            </template>
      <!-- <el-table-column prop="cuttingStatus" label="裁断" sortable/>
        <el-table-column prop="sewingStatus" label="针车" sortable/>
        <el-table-column prop="moldingStatus" label="成型" sortable/> -->
      </el-table-column>
    </el-table-column>
      </el-table>


      <el-table
        :data="preproductiontableData"
        style="width: 100%; margin-bottom: 20px"
        row-key="id"
        border
        default-expand-all
      >
      <el-table-column label="待排产订单">
        <el-table-column prop="customerId" label="客人编号" sortable />
        <el-table-column prop="productionstartDate" label="开始日期" sortable />
        <el-table-column prop="totalQuantity" label="订单总数量" sortable/>
        <el-table-column prop="materialStatus" label="物料状态" sortable />
        <el-table-column prop="deliverDate" label="截止日期" sortable />
        <el-table-column label="操作" sortable >
            <template #default>
            <el-button link type="primary" size="small" @click="openNewWindow(current-row-key)">
            排产
            </el-button>
            </template>
        </el-table-column>
        <!-- <el-table-column prop="cuttingStatus" label="裁断" sortable/>
        <el-table-column prop="sewingStatus" label="针车" sortable/>
        <el-table-column prop="moldingStatus" label="成型" sortable/> -->
      </el-table-column>
      </el-table>

    </div>
  </template>
  
<script>
import { Grid, Memo } from '@element-plus/icons-vue'
import DashboardGrid from './Dashboard/DashboardGrid.vue';
import DashboardList from './Dashboard/DashboardList.vue'
import DashboardPend from './Dashboard/DashboardListPend.vue'
import DashboardProgress from './Dashboard/DashboardListProgress.vue'

export default {
    components: {
        DashboardGrid,
        DashboardList,
        DashboardPend,
        DashboardProgress
    },
    data() {
        return {
            Grid,
            Memo,
            currentDash: 'DashboardGrid',
            inproductiontableData: [{
                customerId: "K24-014客人37 XTI 2111620",
                productionstartDate: "2024-02-27",
                prodStatus: "已排产",
                estimatedproductionDate:"2024-04-20",
                deliverDate: "2024-05-05",
                totalQuantity:720,
                remainingQuantity:"720"

            },
            {
                customerId: "K24-015 客人37XTI 2111622",
                productionstartDate: "2024-06-10",
                prodStatus: "已排产",
                estimatedproductionDate:"2024-04-20",
                deliverDate: "2024-04-20",
                totalQuantity:2340,
                remainingQuantity:"2340"
            },
            {
                customerId: "K24-016客人37 XTI 2111623",
                productionstartDate: "2024-06-10",
                prodStatus: "已排产",
                estimatedproductionDate:"2024-04-20",
                deliverDate: "2024-04-20",
                totalQuantity:3364,
                remainingQuantity:"3364"
            },
            {
                customerId: "K24-017客人37 XTI 2111620",
                productionstartDate: "2024-06-10",
                prodStatus: "已排产",
                estimatedproductionDate:"2024-04-20",
                deliverDate: "2024-07-10",
                totalQuantity:6900,
                remainingQuantity:"6900"
            },
            {
                customerId: "K24-020客人37 XTI 2111620",
                productionstartDate: "2024-06-10",
                prodStatus: "已排产",
                estimatedproductionDate:"2024-04-20",
                deliverDate: "2024-05-05",
                totalQuantity:26620,
                remainingQuantity:"26620"
            },
            {
                customerId: "K24-019客人37 XTI 2111620",
                productionstartDate: "2024-06-10",
                prodStatus: "生产中",
                estimatedproductionDate:"2024-04-20",
                deliverDate: "2024-05-05",
                totalQuantity:13296,
                remainingQuantity:"9042"
            },
            
            ],
            preproductiontableData: [{
                customerId: "K24-018客人37 XTI 2111620",
                productionstartDate: "2024-06-10",
                prodStatus: "针车中",
                deliverDate: "2024-07-10",
                totalQuantity:"10094",
                remainingQuantity:"500"
            },
            
            
            {
                customerId: "K24-021客人37 XTI 2111620",
                productionstartDate: "2024-06-10",
                prodStatus: "针车中",
                deliverDate: "2024-07-10",
                totalQuantity:"64600",
                remainingQuantity:"500"
            },
            {
                customerId: "K24-022客人37 XTI 2111620",
                productionstartDate: "2024-06-10",
                prodStatus: "针车中",
                deliverDate: "2024-07-10",
                totalQuantity:"3000",
                remainingQuantity:"500"
            },
            {
                customerId: "K24-023客人37 XTI 2111620",
                productionstartDate: "2024-06-10",
                prodStatus: "针车中",
                deliverDate: "2024-07-10",
                totalQuantity:"4320",
                remainingQuantity:"500"
            },
            {
                customerId: "K24-024客人37 XTI 2111620",
                productionstartDate: "2024-06-10",
                prodStatus: "针车中",
                deliverDate: "2024-07-10",
                totalQuantity:"4800",
                remainingQuantity:"500"
            },
            {
                customerId: "K24 客人37 2111620",
                productionstartDate: "2024-02-25",
                prodStatus: "针车中",
                deliverDate: "2024-04-20",
                totalQuantity:"2000",
                remainingQuantity:"500"
            }
            ],
        }
    },
    methods: {
        changeToGrid() {
            this.currentDash = 'DashboardGrid'
        },
        changeToList() {
            this.currentDash = 'DashboardList'
        },
        changeToPend() {
            this.currentDash = 'DashboardPend'
        },
        changeToProgress() {
            console.log(this.currentDash)
            this.currentDash = 'DashboardProgress'
        },
        openNewWindow(rowkey)
        {
            let url = ""
            const orderId = rowkey.customerId.replace(' ','-')
            url = `${window.location.origin}/productiongeneral/productiondetail/customerid=${orderId}`;
            window.open(url, '_blank');
        }

    }
}
</script>
<style scoped></style>