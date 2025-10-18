<template>
  <el-container class="app-shell">
    <!-- 头部（固定+阴影） -->
    <el-header class="app-header">
      <AllHeader />
    </el-header>

    <!-- 身体：侧栏（在 Sidebar 内） + 主区 -->
    <el-container class="app-body">
      <Sidebar :onEvent="optionFn" />
      <el-main class="app-main">
          <!-- 引用 main -->
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
import ProcedureManagement from '../components/ProcedureManagement.vue'
import Setting from '../components/Setting.vue'
import Dashboard from '../components/Dashboard.vue'
import OrderProgress from '../../ProductionSharedPages/OrderProgress.vue'
import PersonalInfo from '@/components/PersonalInfo.vue'
import { ref } from 'vue'
const components = {
    Dashboard,
    LaborPriceReport,
    Setting,
    AmountProduced,
    ProcedureManagement,
    OrderProgress,
    PersonalInfo
}
const currentTab = ref('LaborPriceReport')
const optionFn = (option) => {
    currentTab.value = option
}

</script>
