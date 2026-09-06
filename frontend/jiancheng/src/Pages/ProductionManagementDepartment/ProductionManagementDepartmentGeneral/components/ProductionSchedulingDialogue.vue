<template>
  <el-row :gutter="20">
    <el-col :span="6" :offset="20"
      ><el-button-group>
        <el-button type="default" size="default" :icon="Memo" @click="changeToList">列表视图</el-button>
        <el-button type="default" size="default" :icon="Calendar" @click="changeToSchedule">日历视图</el-button>
      </el-button-group>
    </el-col>
  </el-row>
  <component class="u-mt-5" :is="currentComponent"></component>
</template>

<script>
import { Calendar, Memo } from '@element-plus/icons-vue'
import ListView from './ProductionInfo/TableView.vue'
import ScheduleView from './ProductionInfo/ScheduleView.vue'

export default {
  components: {
    ListView,
    ScheduleView
  },
  data() {
    return {
      Calendar,
      Memo,
      currentComponent: "ListView"
    }
  },
  methods: {
    changeToSchedule() {
      this.currentComponent = "ScheduleView"
    },
    changeToList() {
      this.currentComponent = "ListView"
    }
  }
}
</script>

<style scoped></style>
