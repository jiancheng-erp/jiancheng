<template>
  <el-container class="app-shell">
    <el-header class="app-header">
      <AllHeader />
    </el-header>

    <el-container class="app-body">
      <el-aside class="app-aside">
        <div class="aside-brand">
          <div class="aside-brand-badge"><el-icon><Menu /></el-icon></div>
          <div class="aside-brand-text">
            <span class="aside-brand-title">功能导航</span>
            <span class="aside-brand-sub">行政管理</span>
          </div>
        </div>

        <el-menu :default-active="defaultActive" class="app-menu" :unique-opened="true">
          <el-menu-item index="inbound" @click="handleMenuClick('inbound')">
            <el-icon><Box /></el-icon>
            <span>行政入库</span>
          </el-menu-item>
          <el-menu-item index="outbound" @click="handleMenuClick('outbound')">
            <el-icon><SoldOut /></el-icon>
            <span>行政出库</span>
          </el-menu-item>
          <el-menu-item index="profile" @click="handleMenuClick('profile')">
            <el-icon><User /></el-icon>
            <span>个人信息</span>
          </el-menu-item>
        </el-menu>
      </el-aside>

      <el-main class="app-main">
        <component :is="currentComponent" v-bind="currentProps" />
      </el-main>
    </el-container>
  </el-container>
</template>

<script>
import AllHeader from '@/components/AllHeader.vue'
import { UserFilled, Menu, Box, SoldOut, User } from '@element-plus/icons-vue'
import axios from 'axios'
import PersonalInfo from '@/components/PersonalInfo.vue'
import PurchaseInbound from '@/Pages/TotalWarehouse/HeadOfWarehouse/components/PurchaseInbound.vue'
import OutboundMaterial from '@/Pages/TotalWarehouse/HeadOfWarehouse/components/OutboundMaterial.vue'

export default {
  components: {
    AllHeader,
    PersonalInfo,
    PurchaseInbound,
    OutboundMaterial,
    Menu,
    Box,
    SoldOut,
    User
  },
  data() {
    return {
      UserFilled,
      currentComponent: 'PurchaseInbound',
      currentProps: {
        inboundTypeOptions: [{ label: '行政入库', value: 3 }],
        fixedInboundType: 3,
        lockInboundType: true,
        hideOrderFields: true,
        hideShoeSizes: true,
        hideOrderQuery: true,
        disableSizeMaterials: true
      },
      defaultActive: 'inbound',
      userName: ''
    }
  },
  mounted() {
    this.$setAxiosToken()
    this.getUserAndCharacter()
  },
  methods: {
    async getUserAndCharacter() {
      const response = await axios.get(`${this.$apiBaseUrl}/general/getcurrentstaffandcharacter`)
      this.userName = response.data.staffName + '-' + response.data.characterName
    },
    handleMenuClick(index) {
      if (index === 'inbound') {
        this.currentComponent = 'PurchaseInbound'
        this.currentProps = {
          inboundTypeOptions: [{ label: '行政入库', value: 3 }],
          fixedInboundType: 3,
          lockInboundType: true,
          hideOrderFields: true,
          hideShoeSizes: true,
          hideOrderQuery: true,
          disableSizeMaterials: true
        }
        this.defaultActive = 'inbound'
      } else if (index === 'outbound') {
        this.currentComponent = 'OutboundMaterial'
        this.currentProps = {
          fixedOutboundType: 6,
          lockOutboundType: true,
          adminOutboundOnly: true,
          hideOrderFields: true
        }
        this.defaultActive = 'outbound'
      } else if (index === 'profile') {
        this.currentComponent = 'PersonalInfo'
        this.currentProps = {}
        this.defaultActive = 'profile'
      }
    },
    async logout() {
      await axios.post(`${this.$apiBaseUrl}/logout`)
      localStorage.removeItem('token')
      localStorage.removeItem('role')
      this.$router.push('/login')
    }
  }
}
</script>
