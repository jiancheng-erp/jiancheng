<template>
  <el-container class="app-shell">
    <!-- 顶部栏 -->
    <el-header class="app-header">
      <AllHeader />
    </el-header>

    <el-container class="app-body">
      <!-- 侧栏 -->
      <el-aside class="app-aside">
        <div class="profile">
          <el-avatar :icon="UserFilled" :size="80" />
          <div class="profile-name">{{ userName }}</div>
        </div>

        <!-- 左侧菜单（替代 el-tabs） -->
        <el-menu :default-active="activeIndex" class="app-menu" :unique-opened="true">
          <!-- <el-menu-item index="1" @click="handleMenuClick('FinancialDetailsDisplay','1')">
            <span>明细展示</span>
          </el-menu-item> -->
          <el-menu-item index="2" @click="handleMenuClick('InOutboundRecords','2')">
            <span>入库待审核</span>
          </el-menu-item>
          <el-menu-item index="3" @click="handleMenuClick('InboundDetails','3')">
            <span>入库明细</span>
          </el-menu-item>
          <el-menu-item index="4" @click="handleMenuClick('FinancialRecievableDetail','4')">
            <span>应收记录</span>
          </el-menu-item>
          <el-menu-item index="99" @click="logout">
            <span>退出系统</span>
          </el-menu-item>
        </el-menu>
      </el-aside>

      <!-- 主体 -->
      <el-main class="app-main">
        <!-- 内容区：跟随菜单切换 -->
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

/* 4个页面组件（与原 tabs 的 pane 一一对应） */
import InOutboundRecords from '@/Pages/TotalWarehouse/HeadOfWarehouse/components/InOutboundRecords.vue'
import InboundDetails from '../components/FinancialWarehouseDetail.vue'
import FinancialRecievableDetail from '../components/FinancialRecievableDetail.vue'

const components = {
  InOutboundRecords,
  InboundDetails,
  FinancialRecievableDetail
}

const userName = ref('财务部-审核')
const activeIndex = ref('2')
const currentComponent = ref('InOutboundRecords')

const { setAxiosToken } = useSetAxiosToken()
const $api_baseUrl = getCurrentInstance().appContext.config.globalProperties.$apiBaseUrl
const router = useRouter()

onMounted(() => {
  setAxiosToken()
  getUserAndCharacter()
})

async function getUserAndCharacter() {
  const { data } = await axios.get(`${$api_baseUrl}/general/getcurrentstaffandcharacter`)
  userName.value = `${data.staffName}-${data.characterName}`
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
/* 这里沿用 main.css 的外观，仅保留你原来的用户栏微样式 */
.user-info {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
  padding: 8px 20px;
  background: #ffffff;
  border-radius: var(--radius-lg, 12px);
  box-shadow: var(--shadow-soft, 0 6px 16px rgba(0,0,0,.08));
  transition: box-shadow .2s ease;
}
.user-info:hover { box-shadow: 0 8px 20px rgba(0,0,0,.08); }

.logout {
  color: var(--brand, #2193b0);
  cursor: pointer;
  font-style: normal;
  font-weight: 500;
  transition: color .2s ease;
}
.logout:hover { color: color-mix(in srgb, var(--brand) 80%, black); }

.username { font-weight: 600; color: #1e293b; }
</style>
