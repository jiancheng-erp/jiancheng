<template>
  <el-row :gutter="20">
    <el-col :span="24" :offset="0" style="font-size: xx-large; text-align: center">任务看板</el-col>
  </el-row>

  <el-row :gutter="0">
    <el-col :span="4" :offset="20">
      <el-button-group>
        <el-button size="default" @click="changeToGrid" :icon="Grid">卡片显示</el-button>
        <el-button size="default" @click="changeToList" :icon="Memo">列表显示</el-button>
      </el-button-group>
    </el-col>
  </el-row>
  <component
    :is="currentDash"
    :pendingTaskData="textData"
    :inProgressTaskData="textData2"
    :datafinished="!datafinished"
    @backGrid="changeToGrid"
    @changeToPend="changeToPend"
    @changeToProgress="changeToProgress"

  >
  </component>
</template>
<script>
import { Grid, Memo } from '@element-plus/icons-vue'
import DashboardGrid from './Dashboard/DashboardGrid.vue'
import DashboardList from './Dashboard/DashboardList.vue'
import DashboardPend from './Dashboard/DashboardListPend.vue'
import DashboardProgress from './Dashboard/DashboardListProgress.vue'
import axios from 'axios'

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
    async getAllData() {
      const res = await axios.get(
        'http://192.168.50.135:8000/logistics/task?taskstatus=0&shoestatus=all'
      )
      this.textData = res.data
      const res2 = await axios.get(
        'http://192.168.50.135:8000/logistics/task?taskstatus=1&shoestatus=all'
      )
      this.textData2 = res2.data
      this.datafinished = true
    },
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
    }
  }
}
</script>
<style></style>
