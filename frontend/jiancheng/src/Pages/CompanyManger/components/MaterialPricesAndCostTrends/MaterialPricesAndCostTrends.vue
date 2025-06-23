<template>
    <el-tabs v-model="editableTabsValue" type="card" class="demo-tabs" @edit="handleTabsEdit">
        <el-tab-pane label="材料价格与成本趋势" name="1" :closable="false">
            <MaterialData  @edit="handleTabsEdit"/>
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
                :materialStorageId="item.materialStorageId"
                :materialType="item.materialType"
                :materialName="item.needQuery ? item.name : undefined"
                :spuMaterialId="item.spuMaterialId"
            ></component>
        </el-tab-pane>
    </el-tabs>
</template>
<script setup lang="js">
import MaterialData from './MaterialData.vue';
import HistoryTrend from './HistoryTrend.vue';
import { ref } from 'vue';

const editableTabsValue = ref('1');
const editableTabs = ref([]);

const handleTabsEdit = (targetName, action) => {
    const tabName = targetName.split('>')[0];
    const materialStorageId = targetName.split('>')[1]
    const materialType = targetName.split('>')[2]
    const spuMaterialId = targetName.split('>')[3]
    if (action === 'add') {
        editableTabs.value.push({
            title: tabName + '历史价格数据曲线',
            name: tabName,
            content: HistoryTrend,
            closable: true,
            needQuery: true,
            materialStorageId: materialStorageId,
            materialType: materialType,
            spuMaterialId: spuMaterialId
            
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
                        activeName = '1';
                    }
                }
            })
        }
        editableTabsValue.value = activeName;
        editableTabs.value = tabs.filter((tab) => tab.name !== tabName);
    }
}
</script>

<style>
.demo-tabs > .el-tabs__content {
    color: #6b778c;
}
.demo-tabs {
    height: calc(100% - 40px);
    width: calc(100% - 40px);
}
.el-tab-pane {
    height: 100%;
    overflow: auto;
}
</style>
