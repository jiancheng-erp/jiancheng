<template>
    <el-container style="height: 100vh;">
        <el-header class="custom-header">
            <AllHeader></AllHeader>
        </el-header> <!--引用header-->
        <el-main class="custom-main">
            <div class="userInfo"
                style="display: flex;justify-content: end;align-items: center;right: 50px;position: relative;">
                <em style="margin-right: 20px;color: dodgerblue;cursor: pointer;" @click="logout">退出登录</em>
                <span>{{ userName }}</span>
            </div>
            <el-tabs tab-position="left" style="height: 98%">
                <el-tab-pane label="材料入库">
                    <InboundView />
                </el-tab-pane>
                <el-tab-pane label="库存查看">
                    <InboundOutboundHistory />
                </el-tab-pane>
                <el-tab-pane label="历史记录">
                    <InOutboundRecords />
                </el-tab-pane>
                <el-tab-pane label="个人信息">
                    <PersonalInfo />
                </el-tab-pane>
            </el-tabs>
        </el-main>
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

export default {
    components: {
        AllHeader,
        InboundOutboundHistory,
        InboundView,
        OutboundView,
        InOutboundRecords,
        PersonalInfo
    },
    data() {
        return {
            UserFilled,
            currentComponent: 'InboundView',
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
    }
}
</script>
<style scoped>
.custom-header {
    height: 50px;
    margin-bottom: 0;
    margin-top: 0;
}

.custom-main {
    margin-top: 10;
}
</style>