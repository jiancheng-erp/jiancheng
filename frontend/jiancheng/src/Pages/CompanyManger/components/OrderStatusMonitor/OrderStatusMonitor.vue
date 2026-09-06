<template>
    <el-tabs v-model="editableTabsValue" type="card" class="demo-tabs" @edit="handleTabsEdit">
        <!-- <el-tab-pane label="已完成订单" name="1" :closable="false">
            <component :is="CompletedOrders" @edit="handleTabsEdit"></component>
        </el-tab-pane> -->
        <el-tab-pane label="进行中订单" name="2" :closable="false">
            <UnfinishedOrders  @edit="handleTabsEdit"/>
        </el-tab-pane>
        <el-tab-pane
            v-for="item in editableTabs"
            :key="item.name"
            :label="item.title"
            :name="item.name"
            :closable="item.closable"
        >
            <component
                :is="item.content"
                :orderId="item.orderId"
            ></component>
        </el-tab-pane>
    </el-tabs>
</template>

<script lang="js" setup>
// import CompletedOrders from '../OrderStatusMonitor/CompletedOrders.vue';
import UnfinishedOrders from '../OrderStatusMonitor/UnfinishedOrders.vue';
import OrderTimeLine from '../OrderStatusMonitor/OrderTimeLine.vue';
import { ref } from 'vue';

const editableTabsValue = ref('2');
const editableTabs = ref([]);

const handleTabsEdit = (targetName, action) => {
    const tabName = targetName.split('>')[0];
    const orderId = targetName.split('>')[1];
    if (action === 'add') {
        editableTabs.value.push({
            title: '订单：' + tabName,
            name: tabName,
            content: OrderTimeLine,
            closable: true,
            needQuery: true,
            orderId: orderId
        });
        editableTabsValue.value = tabName;
    } else if (action === 'remove') {
        const tabs = editableTabs.value;
        let activeName = editableTabsValue.value;
        if (activeName === tabName) {
            tabs.forEach((tab, index) => {
                if (tab.name === tabName) {
                    const nextTab = tabs[index + 1] || tabs[index - 1];
                    if (nextTab) {
                        activeName = nextTab.name;
                    } else {
                        activeName = '2';
                    }
                }
            })
        }
        editableTabsValue.value = activeName;
        editableTabs.value = tabs.filter((tab) => tab.name !== tabName);
    }
}
</script>

<style scoped>
.demo-tabs > :deep(.el-tabs__content) {
    color: #6b778c;
}
.demo-tabs {
    height: calc(100% - 40px);
    width: calc(100% - 40px);
}
:deep(.el-tab-pane) {
    height: 100%;
    overflow: auto;
}
</style>
