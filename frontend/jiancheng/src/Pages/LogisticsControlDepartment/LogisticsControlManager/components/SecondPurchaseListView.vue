<template>
  <el-row :gutter="20">
    <el-col :span="24" :offset="0" style="font-size: xx-large; text-align: center"
      >二次采购订单生成</el-col
    >
  </el-row>
  <component
    :is="currentDash"
    :pendingTaskData="textData"
    :inProgressTaskData="textData2"
    :datafinished="!datafinished"
    @backToList="changeToList"
    @changeToPend="changeToPend"
    @changeToProgress="changeToProgress"
  >
  </component>
</template>
<script>
import { Grid, Memo } from '@element-plus/icons-vue'
import SecondOrderList from './SecondPurchaseOrder/SecondOrderList.vue'
import SecondOrderPend from './SecondPurchaseOrder/SecondOrderListPend.vue'
import SecondOrderProgress from './SecondPurchaseOrder/SecondOrderListProgress.vue'
import axios from 'axios'
export default {
  components: {
    SecondOrderList,
    SecondOrderPend,
    SecondOrderProgress
  },
  data() {
    return {
      Grid,
      Memo,
      currentDash: 'SecondOrderList',
      textData: [],
      textData2: [],
      datafinished: false,
    }
  },
  mounted() {
    this.getAllData()
  },
  methods: {
    async getAllData() {
      const res = await axios.get(
        'http://192.168.50.135:8000/logistics/task?taskstatus=0&shoestatus=13'
      )
      this.textData = res.data
      const res2 = await axios.get(
        'http://192.168.50.135:8000/logistics/task?taskstatus=1&shoestatus=13'
      )
      this.textData2 = res2.data
      this.datafinished = true
    },
    changeToList() {
      this.currentDash = 'SecondOrderList'
    },
    changeToPend() {
      this.currentDash = 'SecondOrderPend'
    },
    changeToProgress() {
      console.log(this.currentDash)
      this.currentDash = 'SecondOrderProgress'
    }
  }
}
</script>
<style></style>
