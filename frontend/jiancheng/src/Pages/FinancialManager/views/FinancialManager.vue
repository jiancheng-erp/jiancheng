<template>
  <el-container class="app-shell">
    <el-header class="app-header">
      <AllHeader />
    </el-header>

    <el-container class="app-body">
      <el-aside class="app-aside">
        <div class="profile">
          <el-avatar :icon="UserFilled" :size="80" />
          <div class="profile-name">{{ userName }}</div>
        </div>

        <el-menu :default-active="activeIndex" class="app-menu" :unique-opened="true">
          <el-menu-item index="1" @click="handleMenuClick('FinancialWarehouseDetail','1')">
            <span>总仓出入库记录</span>
          </el-menu-item>
          <el-menu-item index="2" @click="handleMenuClick('FinancialWarehouseInventory','2')">
            <span>库存</span>
          </el-menu-item>
          <el-menu-item index="9" @click="handleMenuClick('InOutboundRecords','9')">
            <span>成品仓出入库记录</span>
          </el-menu-item>          
          <el-menu-item index="3" @click="handleMenuClick('FinancialRecievableDetail','3')">
            <span>应收记录</span>
          </el-menu-item>
          <el-menu-item index="4" @click="handleMenuClick('GeneralOrderSearchForWarehouse','4')">
            <span>订单查询</span>
          </el-menu-item>
          <el-menu-item index="5" @click="handleMenuClick('SupplierManagementView','5')">
            <span>供应商管理</span>
          </el-menu-item>
          <el-menu-item index="6" @click="handleMenuClick('MaterialManagementView','6')">
            <span>物料管理</span>
          </el-menu-item>
          <el-menu-item index="7" @click="handleMenuClick('DevelopmentPerformanceManagement','7')">
            <span>开发绩效管理</span>
          </el-menu-item>
          <el-menu-item index="8" @click="handleMenuClick('OrderSearch','8')">
            <span>BOM查询</span>
          </el-menu-item>
          <el-menu-item index="10" @click="handleMenuClick('FinancialExchangeManagement','10')">
            <span>汇率管理</span>
          </el-menu-item>
          <el-menu-item index="99" @click="logout">
            <span>退出系统</span>
          </el-menu-item>
        </el-menu>
      </el-aside>

      <el-main class="app-main">
        <component :is="components[currentComponent]" />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="js">
import AllHeader from '@/components/AllHeader.vue'
import { UserFilled } from '@element-plus/icons-vue'
import axios from 'axios'
import { ref, onMounted, getCurrentInstance } from 'vue'
import { useRouter } from 'vue-router'
import useSetAxiosToken from '../hooks/useSetAxiosToken'

import FinancialPayableDetail from '../components/FinancialPayableDetail.vue'
import FinancialHistoryRecord from '../components/FinancialHistoryRecord.vue'
import FinancialItemEntry from '../components/FinancialItemEntry.vue'
import InventoryView from '../components/InventoryView.vue'
import OrderStatusConfirm from '../components/OrderStatusConfirm.vue'
import FinancialAccountDetail from '../components/FinancialAccountDetail.vue'
import FinancialAccountManagement from '../components/FinancialAccountManagement.vue'
import FinancialRecievableDetail from '../components/FinancialRecievableDetail.vue'
import FinancialWarehouseDetail from '../components/FinancialWarehouseDetail.vue'
import FinancialWarehouseInventory from '../components/FinancialWarehouseInventory.vue'
import InboundRecords from '@/Pages/TotalWarehouse/HeadOfWarehouse/components/InboundRecords.vue'
import GeneralOrderSearchForWarehouse from '@/components/GeneralOrderSearchForWarehouse.vue'
import SupplierManagementView from '@/Pages/LogisticsControlDepartment/LogisticsControlManager/components/SupplierManagementView.vue'
import MaterialManagementView from '@/Pages/LogisticsControlDepartment/LogisticsControlManager/components/MaterialManagementView.vue'
import DevelopmentPerformanceManagement from '@/Pages/DevelopmentManager/components/DevelopmentPerformanceManagement.vue'
import OrderSearch from '@/Pages/UsageCalculation/components/OrderSearch.vue'
import InOutboundRecords from '@/Pages/TotalWarehouse/FinishedWarehouse/components/InOutboundRecords.vue'
import FinancialExchangeManagement from '../components/FinancialExchangeManagement.vue'

const components = {
  FinancialPayableDetail,
  FinancialHistoryRecord,
  FinancialItemEntry,
  InventoryView,
  OrderStatusConfirm,
  FinancialAccountDetail,
  FinancialAccountManagement,
  FinancialRecievableDetail,
  FinancialWarehouseDetail,
  FinancialWarehouseInventory,
  InboundRecords,
  GeneralOrderSearchForWarehouse,
  SupplierManagementView,
  MaterialManagementView,
  DevelopmentPerformanceManagement,
  OrderSearch,
  InOutboundRecords,
  FinancialExchangeManagement
}

const userName = ref('财务部-主管')
const activeIndex = ref('1')
const currentComponent = ref('FinancialWarehouseDetail')

const { setAxiosToken } = useSetAxiosToken()
const $api_baseUrl = getCurrentInstance().appContext.config.globalProperties.$apiBaseUrl
const router = useRouter()

onMounted(() => {
  setAxiosToken()
  getUserAndCharacter()
})

async function getUserAndCharacter() {
  const response = await axios.get(`${$api_baseUrl}/general/getcurrentstaffandcharacter`)
  userName.value = response.data.staffName + '-' + response.data.characterName
}

function handleMenuClick(name, index) {
  currentComponent.value = name
  activeIndex.value = index
}

async function logout() {
  await axios.post(`${$api_baseUrl}/logout`)
  localStorage.removeItem('token')
  localStorage.removeItem('role')
  router.push('/login')
}
</script>

<style scoped>
:root {
  --header-grad-a: #6dd5ed;
  --header-grad-b: #2193b0;
  --brand: #2193b0;
  --border-color: #e5e7eb;
  --shadow-soft: 0 6px 16px rgba(0,0,0,.08);
  --shadow: 0 10px 30px rgba(0,0,0,.12);
  --radius-lg: 12px;
  --radius-xl: 16px;
}

.el-main {
  padding: 16px;
  background: #f5f7fa;
  border-radius: var(--radius-xl);
}

.userInfo {
  position: static !important;
  right: auto !important;
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 12px;
  margin: 0 0 16px;
  padding: 8px 16px;
  background: #fff;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-soft);
  transition: box-shadow .2s ease, transform .12s ease;
}
.userInfo:hover {
  box-shadow: 0 8px 20px rgba(0,0,0,.08);
  transform: translateY(-1px);
}
.userInfo em {
  margin-right: 8px !important;
  color: var(--brand) !important;
  cursor: pointer;
  font-style: normal;
  font-weight: 600;
}
.userInfo em:hover {
  color: color-mix(in srgb, var(--brand) 85%, black) !important;
}
</style>
