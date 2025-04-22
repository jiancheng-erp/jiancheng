<template>
    <el-container>
        <el-header>
            <AllHeader></AllHeader>
        </el-header>
        <el-container>
            <Sidebar :onEvent="optionFn" />
            <el-main> <!--引用main-->
                <component :is="components[currentTab]"></component>
            </el-main>
        </el-container>
    </el-container>

</template>

<script setup>
import AllHeader from '@/components/AllHeader.vue'
import Sidebar from '../components/Sidebar.vue'
import LaborPriceReport from '../components/LaborPriceReport.vue'
import ProcedureManagement from '../components/ProcedureManagement.vue'
import OrderProgress from '../../ProductionSharedPages/OrderProgress.vue'
import PersonalInfo from '@/components/PersonalInfo.vue'
import { ref } from 'vue'
const components = {
    LaborPriceReport,
    ProcedureManagement,
    OrderProgress,
    PersonalInfo
}
const currentTab = ref('LaborPriceReport')
const optionFn = (option) => {
    currentTab.value = option
}

</script>
