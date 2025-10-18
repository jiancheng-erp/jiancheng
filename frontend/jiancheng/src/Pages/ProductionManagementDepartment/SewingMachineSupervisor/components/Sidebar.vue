<template>
  <el-aside class="app-aside">
    <!-- 头像与用户名 -->
    <div class="profile">
      <el-avatar :icon="UserFilled" :size="80" />
      <div class="profile-name">{{ userName }}</div>
    </div>
            <el-menu default-active="3" class="app-menu menu-normal">
                <!-- <el-menu-item index="1" @click="handleMenuOption('Dashboard')">
                    <span>任务看板</span>
                </el-menu-item> -->
                <el-menu-item index="3" @click="handleMenuOption('LaborPriceReport')">
                    <span>工序填报</span>
                </el-menu-item>
                <el-menu-item index="2" @click="handleMenuOption('OrderProgress')">
                    <span>生产动态明细</span>
                </el-menu-item>
                <el-menu-item index="5" @click="handleMenuOption('ProcedureManagement')">
                    <span>工序管理</span>
                </el-menu-item>
                <el-menu-item index="6" @click="handleMenuOption('PersonalInfo')">
                    <span>个人信息</span>
                </el-menu-item>
                <el-menu-item index="8" @click="logout">
                    <span>退出系统</span>
                </el-menu-item>
            </el-menu>
    </el-aside>
</template>

<script setup>
import { ref, getCurrentInstance, onMounted } from 'vue'
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
