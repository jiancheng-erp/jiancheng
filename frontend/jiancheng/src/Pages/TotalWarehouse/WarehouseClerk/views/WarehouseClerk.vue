<template>
  <el-container class="app-shell">
    <!-- 头部 -->
    <el-header class="app-header">
      <AllHeader />
    </el-header>

    <!-- 身体：侧栏 + 主区 -->
    <el-container class="app-body">
      <!-- 侧栏 -->
      <el-aside class="app-aside">
        <div class="profile">
          <el-avatar :icon="UserFilled" :size="100" />
          <div class="profile-name">{{ userName }}</div>
        </div>

        <!-- 菜单（内部滚动） -->
        <el-menu
          :default-active="defaultActive"
          class="app-menu"
          :unique-opened="true"
        >
          <el-menu-item
            v-if="['35', '39'].includes(staffId)"
            index="1"
            @click="handleMenuClick(1)"
          >
            <span>材料入库</span>
          </el-menu-item>

          <el-menu-item index="2" @click="handleMenuClick(2)">
            <span>材料出库</span>
          </el-menu-item>

          <el-menu-item index="6" @click="handleMenuClick(6)">
            <span>按订单出库</span>
          </el-menu-item>

          <el-menu-item index="9" @click="handleMenuClick(9)">
            <span>出入库审核</span>
          </el-menu-item>

          <el-menu-item index="13" @click="handleMenuClick(13)">
            <span>出入库明细</span>
          </el-menu-item>

          <el-menu-item index="5" @click="handleMenuClick(5)">
            <span>库存</span>
          </el-menu-item>

          <el-menu-item index="7" @click="handleMenuClick(7)">
            <span>订单查询</span>
          </el-menu-item>

          <el-menu-item index="12" @click="handleMenuClick(12)">
            <span>个人信息</span>
          </el-menu-item>

          <el-menu-item index="99" @click="logout()">
            <span>退出系统</span>
          </el-menu-item>
        </el-menu>
      </el-aside>

      <!-- 主内容（内部滚动） -->
      <el-main class="app-main">
        <component :is="currentComponent" />
      </el-main>
    </el-container>
  </el-container>
</template>

<script>
import AllHeader from '@/components/AllHeader.vue'
import InboundOutboundHistory from '../../HeadOfWarehouse/components/InboundOutboundHistory.vue'
import { UserFilled } from '@element-plus/icons-vue'
import axios from 'axios'
import { logout } from '@/Pages/utils/logOut'
import PurchaseInbound from '../../HeadOfWarehouse/components/PurchaseInbound.vue'
import InOutboundRecords from '../../HeadOfWarehouse/components/InOutboundRecords.vue'
import PersonalInfo from '@/components/PersonalInfo.vue'
import GeneralOrderSearch from '@/components/GeneralOrderSearch.vue'
import OutboundMaterial from '../../HeadOfWarehouse/components/OutboundMaterial.vue'
import FinancialWarehouseDetail from '@/Pages/FinancialManager/components/FinancialWarehouseDetail.vue'
import OutboundByOrder from '../../HeadOfWarehouse/components/OutboundByOrder.vue'

export default {
    components: {
        AllHeader,
        InboundOutboundHistory,
        PurchaseInbound,
        InOutboundRecords,
        PersonalInfo,
        GeneralOrderSearch,
        OutboundMaterial,
        FinancialWarehouseDetail,
        OutboundByOrder
    },
    data() {
        return {
            UserFilled,
            currentComponent: null,
            userName: '',
            logout,
            staffId: localStorage.getItem('staffid'),
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
            this.currentComponent = ['35', '39'].includes(this.staffId) ? 'PurchaseInbound' : 'OutboundMaterial'
        },
        defaultPage() {
            if (['35', '39'].includes(this.staffId)) {
                return '1'
            } else {
                return '2'
            }
        },
        handleMenuClick(index){
            switch(index) {
                case 1:
                    this.currentComponent = 'PurchaseInbound'
                    break
                case 2:
                    this.currentComponent = 'OutboundMaterial'
                    break
                case 5:
                    this.currentComponent = 'InboundOutboundHistory'
                    break
                case 6:
                    this.currentComponent = 'OutboundByOrder'
                    break
                case 9:
                    this.currentComponent = 'InOutboundRecords'
                    break
                case 7:
                    this.currentComponent = 'GeneralOrderSearch'
                    break
                case 12:
                    this.currentComponent = 'PersonalInfo'
                    break
                case 13:
                    this.currentComponent = 'FinancialWarehouseDetail'
            }
        }
    }
}
</script>