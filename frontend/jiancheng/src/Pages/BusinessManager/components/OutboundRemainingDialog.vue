<template>
  <el-dialog :model-value="modelValue" :title="`订单 ${detail?.orderRid || ''} 出库剩余明细`" width="90%" top="5vh"
    @update:model-value="(v) => $emit('update:modelValue', v)" @open="load">
    <div v-loading="loading">
      <div v-if="detail" class="summary-bar">
        订单总双数 <strong>{{ detail.totalAmount }}</strong>，
        已出库 <strong>{{ detail.outboundedAmount }}</strong>，
        剩余 <strong class="remaining">{{ detail.remainingAmount }}</strong> 双
      </div>
      <div v-if="detail && !detail.items.length" class="empty-tip">该订单暂无颜色明细</div>
      <div v-for="item in detail?.items || []" :key="item.orderShoeTypeId" class="color-block">
        <div class="color-title">
          <span>{{ item.shoeRId }}<template v-if="item.customerProductName">（{{ item.customerProductName }}）</template> - {{ item.colorName }}</span>
          <span class="color-title-stat">
            订单 {{ item.totalAmount }} / 已出 {{ item.outboundedAmount }} / 剩余
            <strong class="remaining">{{ item.remainingAmount }}</strong> 双
          </span>
        </div>
        <el-alert v-if="item.batchDetailMismatch" type="warning" :closable="false" show-icon
          title="该颜色部分出库未记录配码，下方按配码折算的尺码剩余可能偏多，仅供参考" />
        <el-table :data="blockRows(item)" border size="small" :row-class-name="({ row }) => (row.isTotal ? 'total-row' : '')">
          <el-table-column prop="batchName" label="配码" width="140" />
          <el-table-column prop="totalAmount" label="订单数" width="90" />
          <el-table-column prop="outboundedAmount" label="已出库" width="90" />
          <el-table-column prop="remainingAmount" label="剩余" width="90" />
          <el-table-column v-for="col in detail.sizeColumns" :key="col.size" :label="col.label" min-width="60">
            <template #default="scope">
              <span :class="{ 'zero-cell': !scope.row.sizeRemaining[col.size] }">{{ scope.row.sizeRemaining[col.size] || 0 }}</span>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>
  </el-dialog>
</template>

<script>
import axios from 'axios'
import { ElMessage } from 'element-plus'

export default {
  name: 'OutboundRemainingDialog',
  props: {
    modelValue: { type: Boolean, default: false },
    orderId: { type: [Number, String], default: null }
  },
  emits: ['update:modelValue'],
  data() {
    return { loading: false, detail: null }
  },
  methods: {
    async load() {
      this.detail = null
      if (!this.orderId) return
      this.loading = true
      try {
        const res = await axios.get(`${this.$apiBaseUrl}/order/getoutboundremaining`, {
          params: { orderId: this.orderId }
        })
        this.detail = res.data
      } catch (e) {
        console.error(e)
        ElMessage.error('获取出库剩余明细失败')
        this.$emit('update:modelValue', false)
      } finally {
        this.loading = false
      }
    },
    blockRows(item) {
      return [
        ...item.batches,
        {
          batchName: '合计',
          totalAmount: item.totalAmount,
          outboundedAmount: item.outboundedAmount,
          remainingAmount: item.remainingAmount,
          sizeRemaining: item.sizeRemaining,
          isTotal: true
        }
      ]
    }
  }
}
</script>

<style scoped>
.summary-bar {
  margin-bottom: 12px;
  padding: 10px 16px;
  border-radius: 6px;
  background-color: var(--el-color-primary-light-9);
  border: 1px solid #b3d8ff;
  font-size: 15px;
}

.summary-bar strong {
  margin: 0 2px;
}

.remaining {
  color: var(--el-color-danger);
}

.color-block {
  margin-bottom: 18px;
}

.color-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
  font-weight: 600;
}

.color-title-stat {
  font-weight: normal;
}

.empty-tip {
  color: var(--el-text-color-secondary);
}

.zero-cell {
  color: var(--el-text-color-placeholder);
}

:deep(.total-row) {
  font-weight: 600;
  background-color: var(--el-fill-color-light);
}
</style>
