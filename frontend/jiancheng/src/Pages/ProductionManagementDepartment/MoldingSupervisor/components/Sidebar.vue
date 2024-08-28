<template>
    <el-aside>
        <div>
            <el-avatar :icon="UserFilled" :size="100" />
        </div>
        <div style="font-size: x-large;">
            成型主任-姓名
        </div>
        <div class="aside-menu" style="width: 100%; margin-top: 50px;">
            <el-menu default-active="2" class="el-menu-vertical-demo">
                <!-- <el-menu-item index="1" @click="handleMenuOption('Dashboard')">
                    <span>任务看板</span>
                </el-menu-item> -->
                <el-menu-item index="2" @click="handleMenuOption('LaborPriceReport')">
                    <span>工价填报</span>
                </el-menu-item>
                <el-menu-item index="3" @click="handleMenuOption('AmountProduced')">
                    <span>数量填写</span>
                </el-menu-item>
                <el-menu-item index="4" @click="handleMenuOption('History')">
                    <span>历史记录</span>
                </el-menu-item>
                <el-menu-item index="5" @click="handleMenuOption('Setting')">
                    <span>个人信息</span>
                </el-menu-item>
                <el-menu-item index="6" @click="handleMenuOption('LogOut')">
                    <span>退出系统</span>
                </el-menu-item>
            </el-menu>
        </div>
    </el-aside>
</template>

<script setup>
const props = defineProps(['onEvent'])
const handleMenuOption = (option) => {
    props.onEvent(option)
}
</script>
