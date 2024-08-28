<template>
  <el-row :gutter="20">
    <el-col :span="24" :offset="0" style="font-size: xx-large; text-align: center"
      >一次采购订单生成</el-col
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
import FirstOrderList from './FirstPurchaseOrder/FirstOrderList.vue'
import FirstOrderPend from './FirstPurchaseOrder/FirstOrderListPend.vue'
import FirstOrderProgress from './FirstPurchaseOrder/FirstOrderListProgress.vue'
import axios from 'axios'

export default {
  components: {
    FirstOrderList,
    FirstOrderPend,
    FirstOrderProgress
  },
  data() {
    return {
      Grid,
      Memo,
      currentDash: 'FirstOrderList',
      textData: [],
      textData2: [],
      datafinished: false,
      refreshkey: 0
    }
  },
  mounted() {
    this.getAllData()
  },
  methods: {
    refreshComponent() {
      // Increment the refresh key to force the component to re-render
      this.refreshKey++;
    },
    async getAllData() {
      const res = await axios.get(
        'http://192.168.50.135:8000/logistics/task?taskstatus=0&shoestatus=6'
      )
      this.textData = res.data
      const res2 = await axios.get(
        'http://192.168.50.135:8000/logistics/task?taskstatus=1&shoestatus=6'
      )
      this.textData2 = res2.data
      this.datafinished = true
      this.refreshComponent();
    },
    changeToList() {
      this.currentDash = 'FirstOrderList'
    },
    changeToPend() {
      this.currentDash = 'FirstOrderPend'
    },
    changeToProgress() {
      console.log(this.currentDash)
      this.currentDash = 'FirstOrderProgress'
    }
  }
}
</script>
<style></style>
