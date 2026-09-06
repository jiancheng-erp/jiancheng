<template>
  <el-aside class="app-aside">
    <div class="aside-brand">
      <div class="aside-brand-badge"><el-icon><Menu /></el-icon></div>
      <div class="aside-brand-text">
        <span class="aside-brand-title">功能导航</span>
        <span class="aside-brand-sub">针车管理</span>
      </div>
    </div>
            <el-menu default-active="3" class="app-menu menu-normal">
                <!-- <el-menu-item index="1" @click="handleMenuOption('Dashboard')">
                    <span>任务看板</span>
                </el-menu-item> -->
                <el-menu-item index="3" @click="handleMenuOption('LaborPriceReport')">
                    <el-icon><Tickets /></el-icon>
                    <span>工序填报</span>
                </el-menu-item>
                <el-menu-item index="2" @click="handleMenuOption('OrderProgress')">
                    <el-icon><TrendCharts /></el-icon>
                    <span>生产动态明细</span>
                </el-menu-item>
                <el-menu-item index="5" @click="handleMenuOption('ProcedureManagement')">
                    <el-icon><Management /></el-icon>
                    <span>工序管理</span>
                </el-menu-item>
                <el-menu-item index="6" @click="handleMenuOption('PersonalInfo')">
                    <el-icon><User /></el-icon>
                    <span>个人信息</span>
                </el-menu-item>
            </el-menu>
    </el-aside>
</template>

<script setup>
import { ref, getCurrentInstance, onMounted } from 'vue'
import { Menu, Tickets, TrendCharts, Management, User } from '@element-plus/icons-vue'
import axios from 'axios'
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
