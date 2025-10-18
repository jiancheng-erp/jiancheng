<template>
    <el-container>
        <el-header>
            <AllHeader></AllHeader>
        </el-header>
        <!--引用header-->
        <el-main>
            <div class="userInfo" style="display: flex;justify-content: end;align-items: center;right: 50px;position: relative;">
                <em style="margin-right: 20px;color: dodgerblue;cursor: pointer ;" @click="logout">退出登录</em>
                <span>{{ userName }}</span>
                <el-avatar :icon="UserFilled" :size="30" />
            </div>
            <el-tabs tab-position="left" style="height: 780px" class="demo-tabs" type="border-card">
                <!-- <el-tab-pane label="明细展示"><FinancialDetailsDisplay /></el-tab-pane> -->
                <!-- <el-tab-pane label="项目录入"><FinancialItemEntry /></el-tab-pane> -->
                <!-- <el-tab-pane label="历史记录"><FinancialHistoryRecord /></el-tab-pane> -->
                <!-- <el-tab-pane label="应付信息"><FinancialPayableDetail /></el-tab-pane>
                <el-tab-pane label="财务科目信息"><FinancialAccountDetail /></el-tab-pane> -->
                <!-- <el-tab-pane label="财务科目分类管理"><FinancialAccountManagement /></el-tab-pane> -->
                <!-- <el-tab-pane label="订单状态确认"><OrderStatusConfirm /></el-tab-pane> -->
                <el-tab-pane label="总仓出入库记录"><FinancialWarehouseDetail/></el-tab-pane>
                <el-tab-pane label="库存"><FinancialWarehouseInventory/></el-tab-pane>
                <el-tab-pane label="应收记录"><FinancialRecievableDetail/></el-tab-pane>
                <el-tab-pane label="订单查询"><GeneralOrderSearchForWarehouse/></el-tab-pane>
                <el-tab-pane label="供应商管理"><SupplierManagementView/></el-tab-pane>
                <el-tab-pane label="物料管理"><MaterialManagementView/></el-tab-pane>
                <el-tab-pane label="开发绩效管理"><DevelopmentPerformanceManagement/></el-tab-pane>
                <el-tab-pane label="BOM查询"><OrderSearch/></el-tab-pane>
                <!-- <el-tab-pane label="库存查看"><InventoryView /></el-tab-pane>
                <el-tab-pane label="入库记录"><InboundRecords /></el-tab-pane> -->
            </el-tabs>
        </el-main>
    </el-container>
</template>

<script setup lang="js">
import AllHeader from '@/components/AllHeader.vue'
import { UserFilled } from '@element-plus/icons-vue'
import axios from 'axios'
import { ref, onMounted, getCurrentInstance } from 'vue'
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
import useSetAxiosToken from '../hooks/useSetAxiosToken'
import { useRouter } from 'vue-router'
import InboundRecords from '@/Pages/TotalWarehouse/HeadOfWarehouse/components/InboundRecords.vue'
import GeneralOrderSearchForWarehouse from '@/components/GeneralOrderSearchForWarehouse.vue'
import SupplierManagementView from '@/Pages/LogisticsControlDepartment/LogisticsControlManager/components/SupplierManagementView.vue'
import MaterialManagementView from '@/Pages/LogisticsControlDepartment/LogisticsControlManager/components/MaterialManagementView.vue'
import DevelopmentPerformanceManagement from '@/Pages/DevelopmentManager/components/DevelopmentPerformanceManagement.vue'
import OrderSearch from '@/Pages/UsageCalculation/components/OrderSearch.vue'

let userName = ref('财务部-主管')
const { setAxiosToken } = useSetAxiosToken()
const $api_baseUrl = getCurrentInstance().appContext.config.globalProperties.$apiBaseUrl
const router = useRouter()

onMounted(() => {
    setAxiosToken()
    getUserAndCharacter()
    handleMenuClick('CostCalcAndProfitAnalysis')
})

// 接口预留，请求后台获取当前登录用户信息
async function getUserAndCharacter() {
    const response = await axios.get(`${$api_baseUrl}/general/getcurrentstaffandcharacter`)
    userName.value = response.data.staffName + '-' + response.data.characterName
}

// 菜单选项切换函数
function handleMenuClick(value) {
    // currentComponent.value = value
}

// 退出登录
async function logout() {
    await axios.post(`${$api_baseUrl}/logout`)
    localStorage.removeItem('token')
    localStorage.removeItem('role')
    router.push('/login')
}
</script>
<style scoped>
/* 兜底主题变量（若全局 main.css 已有，会被覆盖为全局） */
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

/* 顶部 Header 统一风格（渐变+圆角+阴影） */
.el-header {
  --header-h: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  height: var(--header-h);
  margin: 16px;
  padding: .75rem 1rem;
  color: #fff;
  background: linear-gradient(145deg, var(--header-grad-a), var(--header-grad-b));
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow);
}

/* 主体区域留白与背景 */
.el-main {
  padding: 16px;
  background: #f5f7fa;
  border-radius: var(--radius-xl);
}

/* 右上角用户信息条：卡片化 + 去掉内联定位影响 */
.userInfo {
  position: static !important;   /* 覆盖内联 position: relative */
  right: auto !important;        /* 覆盖内联 right: 50px */
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
  margin-right: 8px !important;  /* 比原来的 20px 更紧凑 */
  color: var(--brand) !important;
  cursor: pointer;
  font-style: normal;
  font-weight: 600;
}
.userInfo em:hover {
  color: color-mix(in srgb, var(--brand) 85%, black) !important;
}

/* Tabs 外层卡片化（不改 Tab 结构与行为） */
.demo-tabs {
  background: #fff;
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-soft);
  padding: 6px;
  height: 780px; /* 与模板 inline 保持一致；可在模板里去掉 inline，仅保留这里 */
  border: 1px solid var(--border-color);
}

/* Tab 内容区：更合理的字号与留白（覆盖你之前的大字号） */
.demo-tabs > .el-tabs__content {
  padding: 18px;
  color: #0f172a;
  font-size: 14px;   /* 原来是 32px，过大 */
  font-weight: 500;  /* 原来是 600，略重 */
  background: #f8fafc;
  border-radius: 12px;
}

/* 保持左右布局下内容区始终充满高度，内部可滚动 */
.el-tabs--right .el-tabs__content,
.el-tabs--left .el-tabs__content {
  height: 100%;
  overflow: auto;
}

/* （可选）Tab 左侧标题区域的一点点留白优化，不改变交互 */
.demo-tabs :deep(.el-tabs__header.is-left) {
  padding: 8px 6px;
  border-right-color: var(--border-color);
}

/* 适度缩小左侧每个 Tab 项的间距（不改变视觉风格） */
.demo-tabs :deep(.el-tabs__item) {
  margin: 4px 6px;
}

/* 主体视口高度（让内容在视口内滚动，而不是整页） */
:deep(.el-main) {
  height: calc(100vh - 96px); /* 头部+外边距预留 */
  overflow: hidden;            /* 交给内部滚动 */
}
</style>

