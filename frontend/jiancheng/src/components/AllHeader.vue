<template>
    <div class="main-header">
        <span class="header-title">浙江健诚集团鞋业有限公司ERP系统</span>
        <div class="header-user">
            <el-avatar :icon="UserFilled" :size="34" class="header-avatar" />
            <span class="header-username">{{ userName }}</span>
            <el-tooltip content="退出系统" placement="bottom">
                <button class="header-logout" type="button" aria-label="退出系统" @click="onLogout">
                    <el-icon><SwitchButton /></el-icon>
                </button>
            </el-tooltip>
        </div>
    </div>
</template>


<script>
import axios from 'axios'
import { UserFilled, SwitchButton } from '@element-plus/icons-vue'
import { logout } from '@/Pages/utils/logOut'

export default {
    name: 'AllHeader',
    components: { SwitchButton },
    data() {
        return {
            UserFilled,
            userName: ''
        }
    },
    mounted() {
        if (typeof this.$setAxiosToken === 'function') {
            this.$setAxiosToken()
        }
        this.fetchUser()
    },
    methods: {
        async fetchUser() {
            try {
                const res = await axios.get(`${this.$apiBaseUrl}/general/getcurrentstaffandcharacter`)
                this.userName = res.data.staffName + '-' + res.data.characterName
            } catch (e) {
                // 未登录或接口异常时静默，不阻塞页面
            }
        },
        onLogout() {
            logout()
        }
    }
}
</script>


<style scoped>
.main-header {
    position: relative;
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: Arial, Helvetica, sans-serif;
}
.header-title {
    font-size: 28px;
}
.header-user {
    position: absolute;
    right: 12px;
    top: 50%;
    transform: translateY(-50%);
    display: flex;
    align-items: center;
    gap: 10px;
}
.header-avatar {
    background: #fff !important;
    color: var(--brand);
    border: 2px solid rgba(255, 255, 255, .6);
    box-shadow: 0 2px 8px rgba(0, 0, 0, .18);
    flex: 0 0 auto;
}
.header-avatar :deep(.el-icon),
.header-avatar :deep(svg) {
    color: var(--brand);
}
.header-username {
    color: #fff;
    font-size: 14px;
    font-weight: 600;
    letter-spacing: normal;
    white-space: nowrap;
    text-shadow: 0 1px 2px rgba(0, 0, 0, .2);
}
.header-logout {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 34px;
    height: 34px;
    padding: 0;
    border: 1px solid rgba(255, 255, 255, .45);
    border-radius: 8px;
    background: rgba(255, 255, 255, .12);
    color: #fff;
    font-size: 18px;
    cursor: pointer;
    transition: background-color .2s ease, transform .2s ease;
}
.header-logout:hover {
    background: rgba(255, 255, 255, .26);
    transform: translateY(-1px);
}
</style>
