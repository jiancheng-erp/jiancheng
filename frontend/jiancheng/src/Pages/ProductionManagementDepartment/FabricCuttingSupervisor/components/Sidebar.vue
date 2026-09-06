<template>
  <el-aside class="app-aside">
    <div class="aside-brand">
      <div class="aside-brand-badge"><el-icon><Menu /></el-icon></div>
      <div class="aside-brand-text">
        <span class="aside-brand-title">功能导航</span>
        <span class="aside-brand-sub">裁断管理</span>
      </div>
    </div>

    <!-- 菜单区 -->
    <el-menu
      :default-active="activeIndex"
      class="app-menu menu-normal"
      :unique-opened="true"
    >
      <!-- 如需任务看板，可取消注释 -->
      <!-- <el-menu-item index="1" @click="handleMenuOption('Dashboard', '1')">
        <span>任务看板</span>
      </el-menu-item> -->

      <el-menu-item index="3" @click="handleMenuOption('LaborPriceReport', '3')">
        <el-icon><Tickets /></el-icon>
        <span>工序填报</span>
      </el-menu-item>

      <el-menu-item index="2" @click="handleMenuOption('OrderProgress', '2')">
        <el-icon><TrendCharts /></el-icon>
        <span>生产动态明细</span>
      </el-menu-item>

      <el-menu-item index="5" @click="handleMenuOption('ProcedureManagement', '5')">
        <el-icon><Management /></el-icon>
        <span>工序管理</span>
      </el-menu-item>

      <el-menu-item index="7" @click="handleMenuOption('PersonalInfo', '7')">
        <el-icon><User /></el-icon>
        <span>个人信息</span>
      </el-menu-item>
    </el-menu>
  </el-aside>
</template>

<script setup>
import { ref, getCurrentInstance, onMounted } from 'vue'
import axios from 'axios'
import { Menu, Tickets, TrendCharts, Management, User } from '@element-plus/icons-vue'
import { logout } from '@/Pages/utils/logOut';
const userName = ref('')
const proxy = getCurrentInstance()
const apiBaseUrl = proxy.appContext.config.globalProperties.$apiBaseUrl
const setAxiosToken = proxy.appContext.config.globalProperties.$setAxiosToken
const getUserAndCharacter = async () => {
    const response = await axios.get(`${apiBaseUrl}/general/getcurrentstaffandcharacter`)
    userName.value = response.data.staffName + '-' + response.data.characterName
}
onMounted(() => {
    getUserAndCharacter()
})
const props = defineProps(['onEvent'])
const handleMenuOption = (option) => {
    props.onEvent(option)
}
</script>
