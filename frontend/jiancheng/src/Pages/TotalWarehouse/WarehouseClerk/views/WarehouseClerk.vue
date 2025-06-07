<template>
    <el-container>
        <el-header>
            <AllHeader></AllHeader>
        </el-header> <!--引用header-->
        <el-container>
            <el-aside width="280px"><!--引用aside-->
                <div>
                    <el-avatar :icon="UserFilled" :size="100" />
                </div>
                <div style="font-size: x-large;">
                    {{ userName }}
                </div>
                <div class="aside-menu" style="width: 100%; margin-top: 50px;">
                    <el-menu default-active="1" class="el-menu-vertical-demo">
                        <el-menu-item index="1" @click="handleMenuClick(1)">
                            <span>材料入库</span>
                        </el-menu-item>
                        <el-menu-item index="2" @click="handleMenuClick(2)">
                            <span>材料出库</span>
                        </el-menu-item>
                        <el-menu-item index="9" @click="handleMenuClick(9)">
                            <span>出入库记录</span>
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
                        <el-menu-item index="8" @click="logout">
                            <span>退出系统</span>
                        </el-menu-item>
                    </el-menu>
                </div>
            </el-aside>
            <el-main> <!--引用main-->
                <component :is="currentComponent"></component>
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
import InboundView from '../../HeadOfWarehouse/components/InboundView.vue'
import OutboundView from '../../HeadOfWarehouse/components/OutboundView.vue'
import InOutboundRecords from '../../HeadOfWarehouse/components/InOutboundRecords.vue'
import PersonalInfo from '@/components/PersonalInfo.vue'
import GeneralOrderSearch from '@/components/GeneralOrderSearch.vue'
import OutboundMaterial from '../../HeadOfWarehouse/components/OutboundMaterial.vue'

export default {
    components: {
        AllHeader,
        InboundOutboundHistory,
        InboundView,
        OutboundView,
        InOutboundRecords,
        PersonalInfo,
        GeneralOrderSearch,
        OutboundMaterial
    },
    data() {
        return {
            UserFilled,
            currentComponent:'InboundView',
            userName: '',
            logout
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
        handleMenuClick(index){
            switch(index) {
                case 1:
                    this.currentComponent = 'InboundView'
                    break
                case 2:
                    this.currentComponent = 'OutboundMaterial'
                    break
                case 5:
                    this.currentComponent = 'InboundOutboundHistory'
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
            }
        }
    }
}
</script>