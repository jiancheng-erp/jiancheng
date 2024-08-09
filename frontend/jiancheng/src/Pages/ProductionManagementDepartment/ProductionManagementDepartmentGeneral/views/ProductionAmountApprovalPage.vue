<template>
  <el-container>
    <el-header height="">
      <AllHeader></AllHeader>
    </el-header>
    <el-main height="">
      <el-row :gutter="20" style="text-align: center">
        <el-col :span="24" :offset="0" style="font-size: xx-large; text-align: center"
          >订单鞋型数量审批页面</el-col
        >
      </el-row>
      <el-row :gutter="20">
        <el-col :span="24" :offset="0">
          <el-descriptions title="订单及鞋型信息" border column="2">
            <el-descriptions-item label="订单号"></el-descriptions-item>
            <el-descriptions-item label="鞋型号"></el-descriptions-item>
            <el-descriptions-item label="客户型号"></el-descriptions-item>
            <el-descriptions-item label="订单发货日期"></el-descriptions-item>
          </el-descriptions>
        </el-col>
      </el-row>
      <el-row :gutter="20">
        <el-col :span="12" :offset="0">
          日期范围限制：
          <el-date-picker
            v-model="datePeriod"
            type="daterange"
            size="normal"
            range-separator="-"
            start-placeholder=""
            end-placeholder=""
          >
          </el-date-picker>
        </el-col>
        <el-col :span="4" :offset="0" style="white-space: nowrap">
          工段选择：
          <el-select
            v-model="departSelect"
            value-key=""
            placeholder=""
            clearable
            filterable
            @change=""
          >
            <el-option
              v-for="item in ['全部', '裁断批皮', '针车预备', '针车', '成型']"
              :key="item"
              :label="item"
              :value="item"
            >
            </el-option>
          </el-select>
        </el-col>
      </el-row>

      <el-row :gutter="20">
        <el-col :span="24" :offset="0">
          <el-table :data="amountListData" border stripe>
            <el-table-column prop="date" label="日期"></el-table-column>
            <el-table-column prop="department" label="工段"></el-table-column>
            <el-table-column prop="period" label="生产预计周期"></el-table-column>
            <el-table-column label="数量填报单状态">
              <template #default="scope">
                <el-button type="primary" size="default" @click="openApprovalDialog"
                  >审批</el-button
                >
              </template>
            </el-table-column>
          </el-table>
        </el-col>
      </el-row>
    </el-main>
  </el-container>
  <el-dialog title="数量审批界面" v-model="isAmountApprovalVis" width="50%">
    <el-row :gutter="20">
      <el-col :span="24" :offset="0">
        <el-table :data="shoeSizeAmountData" border stripe>
          <el-table-column prop="sizeType" label="鞋码编号"></el-table-column>、
          <el-table-column prop="amount" label="生产数量"></el-table-column>
          <el-table-column prop="remainAmount" label="剩余数量"></el-table-column>
        </el-table>
      </el-col>
    </el-row>

    <template #footer>
      <span>
        <el-button @click="">取消</el-button>
        <el-button type="danger" @click="openRefuseApprovalDialog">驳回请求</el-button>
        <el-button type="primary" @click="">审批通过</el-button>
      </span>
    </template>
  </el-dialog>
  <el-dialog title="驳回审批请求" v-model="isRefuseApprovalVis" width="30%">
    <el-row :gutter="20">
        <el-col :span="24" :offset="0">
            请填写驳回原因（不超过20字）：
            <el-input v-model="refuseReason" type="textarea" placeholder="" size="normal" resize="none" clearable @change=""></el-input>
            
        </el-col>
    </el-row>
    
    <template #footer>
      <span>
        <el-button @click="">取消</el-button>
        <el-button type="success" @click="">确认</el-button>
      </span>
    </template>
  </el-dialog>
</template>
<script>
import AllHeader from '@/components/AllHeader.vue'

export default {
  components: {
    AllHeader
  },
  data() {
    return {
        isRefuseApprovalVis: false,
        isAmountApprovalVis: false,
        shoeSizeAmountData: [
            {
                sizeType: "S12A",
                amount: 300,
                remainAmount: 200
            }
        ],
        refuseReason:'',
        datePeriod: [],
        departSelect: '',
        amountListData: [
            {
            date: '2024-07-23',
            department: '裁断批皮',
            period: '2024-07-23-2024-07-25'
            }
        ],
        
    }
  },
  methods: {
    openApprovalDialog() {
      this.isAmountApprovalVis = true
    },
    openRefuseApprovalDialog() {
        this.isRefuseApprovalVis = true
    }
  }
}
</script>
