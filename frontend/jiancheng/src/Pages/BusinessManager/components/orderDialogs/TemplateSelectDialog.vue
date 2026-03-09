<template>
    <el-dialog title="选择订单来源" v-model="dialogStore.newOrderTemplateVis" width="72%">
        <el-tabs v-model="activeTab">
            <el-tab-pane label="订单列表" name="history">
                <div class="toolbar-row">
                    <el-input v-model="historySearch" @keyup.enter="$emit('search-history')" placeholder="搜索订单号、客户、客户型号或工厂型号" clearable @clear="$emit('search-history')" />
                    <el-button type="primary" :loading="historyOrderLoading" @click="$emit('search-history')">搜索</el-button>
                    <el-button :loading="historyOrderLoading" @click="$emit('refresh-history')">刷新</el-button>
                </div>
                <el-table :data="historyOrderDisplayData" style="margin-top:8px" height="420" v-loading="historyOrderLoading">
                    <el-table-column prop="orderRid" label="订单号" min-width="150" />
                    <el-table-column prop="orderCid" label="客户订单号" min-width="150" />
                    <el-table-column prop="customerName" label="客户名称" min-width="120" />
                    <el-table-column prop="customerBrand" label="客户商标" min-width="120" />
                    <el-table-column prop="customerProductName" label="客户型号" min-width="150" show-overflow-tooltip />
                    <el-table-column prop="shoeRId" label="工厂型号" min-width="150" show-overflow-tooltip />
                    <el-table-column prop="orderEndDate" label="结束日期" width="120" />
                    <el-table-column label="操作" width="140">
                        <template #default="scope">
                            <el-button type="primary" @click="$emit('create-from-history', scope.row.orderDbId)">加载</el-button>
                        </template>
                    </el-table-column>
                </el-table>
                <el-pagination :current-page="historyOrderPage" :page-size="historyOrderPageSize" :total="historyOrderTotal"
                    layout="total, prev, pager, next" style="margin-top: 12px"
                    @current-change="$emit('history-page-change', $event)" />
            </el-tab-pane>

            <el-tab-pane label="已保存模板" name="template">
                <el-input v-model="templateSearch" @input="$emit('filter-template')" placeholder="搜索模板、客户或商标" clearable />
                <el-table :data="templateDisplayData" style="margin-top:8px" height="420">
                    <el-table-column prop="templateName" label="模板名称" min-width="180" />
                    <el-table-column prop="templateDescription" label="说明" min-width="180" show-overflow-tooltip />
                    <el-table-column prop="customerName" label="客户名称" min-width="120" />
                    <el-table-column prop="customerBrand" label="客户商标" min-width="120" />
                    <el-table-column label="类型" width="100">
                        <template #default="scope">
                            <span>{{ scope.row.orderTemplateId ? '整单模板' : (scope.row.batchInfoTemplateId ? '配码模板' : '未知') }}</span>
                        </template>
                    </el-table-column>
                    <el-table-column label="操作" width="260">
                        <template #default="scope">
                            <el-button type="primary" @click="$emit('create-from-template', scope.row)">模板创建订单</el-button>
                            <el-button type="warning" @click="$emit('edit-template', scope.row)" style="margin-left:8px">重命名</el-button>
                            <el-button type="danger" @click="$emit('delete-template', scope.row)" style="margin-left:8px">删除</el-button>
                        </template>
                    </el-table-column>
                </el-table>
            </el-tab-pane>
        </el-tabs>
    </el-dialog>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useOrderDialogStore } from '@/Pages/BusinessManager/stores/orderDialog'

const props = defineProps({
    templateDisplayData: {
        type: Array,
        default: () => []
    },
    templateFilter: {
        type: String,
        default: ''
    },
    historyOrderDisplayData: {
        type: Array,
        default: () => []
    },
    historyOrderFilter: {
        type: String,
        default: ''
    },
    historyOrderLoading: {
        type: Boolean,
        default: false
    },
    historyOrderTotal: {
        type: Number,
        default: 0
    },
    historyOrderPage: {
        type: Number,
        default: 1
    },
    historyOrderPageSize: {
        type: Number,
        default: 10
    },
    userRole: {
        type: [String, Number],
        default: ''
    }
})

const emit = defineEmits([
    'create-from-template',
    'create-from-history',
    'filter-template',
    'search-history',
    'refresh-history',
    'history-page-change',
    'edit-template',
    'delete-template',
    'update:templateFilter',
    'update:historyOrderFilter'
])

const dialogStore = useOrderDialogStore()
const activeTab = ref('history')

const templateSearch = computed({
    get: () => props.templateFilter,
    set: (val) => emit('update:templateFilter', val)
})

const historySearch = computed({
    get: () => props.historyOrderFilter,
    set: (val) => emit('update:historyOrderFilter', val)
})
</script>

<style scoped>
.toolbar-row {
    display: flex;
    gap: 8px;
    align-items: center;
}

.toolbar-row > :deep(.el-input) {
    flex: 1;
}

</style>
