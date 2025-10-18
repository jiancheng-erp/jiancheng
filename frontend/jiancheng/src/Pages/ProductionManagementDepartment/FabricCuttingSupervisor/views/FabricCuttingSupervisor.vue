<template>
  <el-container class="app-shell">
    <!-- 头部 -->
    <el-header class="app-header">
      <AllHeader />
    </el-header>

    <!-- 身体：侧栏（在 Sidebar 内） + 主区 -->
    <el-container class="app-body">
      <Sidebar :onEvent="optionFn" />
      <el-main class="app-main">
        <component :is="components[currentTab]" />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import AllHeader from '@/components/AllHeader.vue'
import Sidebar from '../components/Sidebar.vue'
import LaborPriceReport from '../components/LaborPriceReport.vue'
import AmountProduced from '../components/AmountProduced.vue'
import Setting from '../components/Setting.vue'
import History from '../components/History.vue'
import Dashboard from '../components/Dashboard.vue'
import ProcedureManagement from '../components/ProcedureManagement.vue'
import OrderProgress from '../../ProductionSharedPages/OrderProgress.vue'
import PersonalInfo from '@/components/PersonalInfo.vue'
import axios from 'axios'
import { getCurrentInstance, ref } from 'vue'
const components = {
    Dashboard,
    LaborPriceReport,
    Setting,
    AmountProduced,
    History,
    ProcedureManagement,
    OrderProgress,
    PersonalInfo
}
const currentTab = ref('LaborPriceReport')
const optionFn = (option) => {
    currentTab.value = option
}

</script>
