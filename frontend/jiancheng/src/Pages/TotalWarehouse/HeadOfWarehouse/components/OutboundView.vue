<template>
    <el-tabs v-model="activeTab" tab-position="top" style="width: 100%;">
        <el-tab-pane label="原材料" name="原材料">
            <MaterialOutbound></MaterialOutbound>
        </el-tab-pane>
        <!-- <el-tab-pane label="复合材料" name="复合材料">
            <CompositeMaterialOutbound></CompositeMaterialOutbound>
        </el-tab-pane> -->
    </el-tabs>
    </template>
    <script>
    import axios from 'axios';
    import { ElMessage, ElMessageBox } from 'element-plus';
    import MaterialOutbound from './MaterialOutbound.vue';
    import CompositeMaterialOutbound from './CompositeMaterialOutbound.vue';
    export default {
        components: {
            MaterialOutbound,
            CompositeMaterialOutbound
        },
        data() {
            return {
                activeTab: '原材料',
                tabs: [
                    { label: "原材料", name: "原材料" },
                    { label: "复合材料", name: "复合材料" }
                ],
            }
        }
    }
    </script>