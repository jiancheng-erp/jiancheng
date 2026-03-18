<template>
  <el-tabs>
    <el-tab-pane label="实时库存">
      <FinishedInOutHistory />
    </el-tab-pane>
    <el-tab-pane label="历史库存">
      <FinishedStorageSnapshot />
    </el-tab-pane>
  </el-tabs>
</template>

<script>
import FinishedInOutHistory from './FinishedInOutHistory.vue'
import FinishedStorageSnapshot from '@/Pages/FinancialManager/components/FinishedStorageSnapshot.vue'

export default {
  name: 'FinishedInventoryPanel',
  components: {
    FinishedInOutHistory,
    FinishedStorageSnapshot
  }
}
</script>
