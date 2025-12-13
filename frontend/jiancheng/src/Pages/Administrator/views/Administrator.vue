<template>
    <el-container>
        <el-header class="app-header">
            <AllHeader></AllHeader>
        </el-header>
        <!--引用header-->
        <el-container class="app-body">
            <!-- 侧栏（头像区 + 内部滚动菜单） -->
            <el-aside class="app-aside">
                <div class="profile">
                    <el-avatar :icon="UserFilled" :size="80" />
                    <div class="profile-name">{{ userName }}</div>
                </div>

                <el-menu :default-active="defaultActive" class="app-menu" :unique-opened="true">
                    <el-menu-item index="order" @click="handleMenuClick('order')">
                        <span>订单查询</span>
                    </el-menu-item>
                    <el-menu-item index="profile" @click="handleMenuClick('profile')">
                        <span>个人信息</span>
                    </el-menu-item>
                    <el-menu-item index="wechat" @click="handleMenuClick('wechat')">
                        <span>微信推送模板</span>
                    </el-menu-item>
                    <el-menu-item index="logout" @click="logout">
                        <span>退出系统</span>
                    </el-menu-item>
                </el-menu>
            </el-aside>
            <el-main>
                <!--引用main-->
                <component :is="currentComponent" v-bind="currentProps"></component>
            </el-main>
        </el-container>
    </el-container>
</template>

<script>
import AllHeader from '@/components/AllHeader.vue'
import { UserFilled } from '@element-plus/icons-vue'
import axios from 'axios'
import OrderSearch from '../components/OrderSearch.vue'
import PersonalInfo from '@/components/PersonalInfo.vue'
import WechatTemplateManager from '@/Pages/System/WechatTemplateManager.vue'
export default {
    components: {
        AllHeader,
        OrderSearch,
        PersonalInfo,
        WechatTemplateManager
    },
    data() {
        return {
            UserFilled,
            currentComponent: 'OrderSearch',
            userName: '',
            currentProps: {}
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
            if (index === 'order') {
                this.currentComponent = 'OrderSearch'
            } else if (index === 'profile') {
                this.currentComponent = 'PersonalInfo'
            } else if (index === 'wechat') {
                this.currentComponent = 'WechatTemplateManager'
            }
        },
        async logout() {
            this.$router.push('/login')
            await this.$axios.post(`${this.$apiBaseUrl}/logout`)
            localStorage.removeItem('token')
            localStorage.removeItem('role')
        }
    }
}
</script>
