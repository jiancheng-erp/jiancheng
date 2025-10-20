<template>
  <el-row :gutter="20">
    <el-col>
      <FinishedSearchBar :searchFilters="searchFilters" @confirm="confirmTableData" />
      <span style="color: red">成品总欠数: {{ this.totalRemainingAmount }}</span>
    </el-col>
  </el-row>

  <el-row :gutter="20">
    <el-col :span="8" :offset="0">
      <el-button-group>
        <el-button v-if="isMultipleSelection" @click="openOperationDialog">入库</el-button>
        <el-button type="primary" @click="toggleSelectionMode">
          {{ isMultipleSelection ? '退出' : '选择成品入库' }}
        </el-button>
      </el-button-group>
    </el-col>
  </el-row>

  <el-row :gutter="20">
    <el-col :span="24" :offset="0">
      <el-table
        ref="tableRef"
        :data="tableData"
        border
        stripe
        height="500"
        :cell-style="getCellStyle"
        :row-key="row => row.storageId"
        :reserve-selection="true"
        @selection-change="handleSelectionChange"
      >
        <!-- 仅允许“实际入库数量 < 计划入库数量”的条目可被选择 -->
        <el-table-column
          v-if="isMultipleSelection"
          type="selection"
          width="55"
          :selectable="isRowSelectable"
        />
        <el-table-column prop="orderRId" label="订单号" />
        <el-table-column prop="shoeRId" label="工厂型号" />
        <el-table-column prop="customerName" label="客户名称" />
        <el-table-column prop="orderCId" label="客户订单号" />
        <el-table-column prop="customerProductName" label="客户鞋型" />
        <el-table-column prop="customerBrand" label="客户商标" />
        <el-table-column prop="colorName" label="颜色" />
        <el-table-column prop="estimatedInboundAmount" label="计划入库数量" />
        <el-table-column prop="actualInboundAmount" label="实际入库数量" />
        <el-table-column prop="currentAmount" label="成品库存" />
        <el-table-column prop="remainingAmount" label="欠数" />
      </el-table>
    </el-col>
  </el-row>

  <el-row :gutter="20">
    <el-col>
      <el-pagination
        @size-change="handleSizeChange"
        @current-change="handlePageChange"
        :current-page="currentPage"
        :page-size="pageSize"
        layout="total, sizes, prev, pager, next, jumper"
        :total="totalRows"
        :page-sizes="pageSizes"
      />
    </el-col>
  </el-row>

  <!-- 批量入库对话框 -->
  <el-dialog :title="operationLabels.dialogTitle" v-model="isMultiInboundDialogVisible" width="70%" destroy-on-close>
    <el-form>
      <el-form-item prop="remark" label="备注">
        <el-input v-model="inboundForm.remark" type="textarea" show-word-limit :maxlength="commentLength" />
      </el-form-item>
    </el-form>

    <el-tabs v-model="activeTab">
      <el-tab-pane
        v-for="(group, index) in inboundForm.orderShoeItems"
        :key="group.orderShoeId"
        :label="`订单鞋型 ${group.items[0].orderRId} - ${group.items[0].shoeRId}`"
        :name="group.orderShoeId"
      >
        <el-table :data="group.items" style="width: 100%" border stripe>
          <el-table-column prop="colorName" label="颜色" />
          <el-table-column prop="operationQuantity" label="待入库数量" />
          <el-table-column :label="operationLabels.operationAmount">
            <template #default="scope">
              <el-input-number v-model="scope.row.inboundQuantity" :min="0" />
            </template>
          </el-table-column>
          <el-table-column prop="remark" label="备注">
            <template #default="scope">
              <el-input v-model="scope.row.remark" :maxlength="commentLength" show-word-limit />
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
    </el-tabs>

    <template #footer>
      <span>
        <el-button @click="isMultiInboundDialogVisible = false">返回</el-button>
        <el-button type="primary" @click="submitOperationForm">入库</el-button>
      </span>
    </template>
  </el-dialog>

  <!-- 尺码数量输入对话框 -->
  <el-dialog title="数量输入框" v-model="isOpenQuantityDialogVisible" width="60%">
    <el-form>
      <el-form-item>
        <el-table :data="filteredData" border stripe>
          <el-table-column prop="shoeSizeName" label="鞋码" />
          <el-table-column prop="predictQuantity" label="应入库数量" />
          <el-table-column prop="actualQuantity" label="实入库数量" />
          <el-table-column prop="currentQuantity" label="库存" />
          <el-table-column :label="operationLabels.operationAmount">
            <template #default="scope">
              <el-input-number
                v-model="scope.row.operationQuantity"
                size="small"
                :min="0"
                @change="updateSemiShoeTotal"
              />
            </template>
          </el-table-column>
        </el-table>
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button type="primary" @click="isOpenQuantityDialogVisible = false">确认</el-button>
    </template>
  </el-dialog>
</template>

<script>
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'
import * as constants from '@/Pages/utils/constants'
import { PAGESIZE, PAGESIZES } from '../../warehouseUtils'
import FinishedSearchBar from './FinishedSearchBar.vue'

export default {
  components: {
    FinishedSearchBar
  },
  data() {
    return {
      formItemTemplate: {
        inboundAmount: 0,
        outsourceInfo: [],
        orderShoeItems: [],
        remark: null
      },
      inboundForm: {},
      currentPage: 1,
      pageSize: PAGESIZE,
      pageSizes: PAGESIZES,
      tableData: [],
      totalRows: 0,
      searchFilters: {
        orderRIdSearch: '',
        shoeRIdSearch: '',
        customerNameSearch: '',
        customerProductNameSearch: '',
        orderCIdSearch: '',
        customerBrandSearch: ''
      },
      currentRow: {},
      isMultipleSelection: false,
      selectedRows: [],
      selectedIds: [],           // ✅ 记录已选主键（storageId 数组）
      isMultiInboundDialogVisible: false,
      activeTab: null,
      currentQuantityRow: null,
      isOpenQuantityDialogVisible: false,
      operationLabels: {
        dialogTitle: '成品入库',
        timestamp: '入库日期',
        operationAmount: '入库数量'
      },
      commentLength: constants.BOUND_RECORD_COMMENT_LENGTH,
      totalRemainingAmount: 0
    }
  },
  computed: {
    filteredData() {
      return (this.currentQuantityRow?.shoesInboundTable || []).filter((row) => {
        return row.predictQuantity > 0
      })
    }
  },
  mounted() {
    this.getTableData()
  },
  methods: {
    // —— 选择持久化 & 恢复 —— //
    persistSelections() {
      this.selectedIds = this.selectedRows.map(r => r.storageId).filter(v => v != null)
    },
    async restoreSelections() {
      // 等待表格渲染完成再恢复
      await this.$nextTick()
      const table = this.$refs.tableRef
      if (!table || !this.selectedIds?.length) return
      const map = new Set(this.selectedIds)
      for (const row of this.tableData) {
        if (map.has(row.storageId) && this.isRowSelectable(row)) {
          table.toggleRowSelection(row, true)
        }
      }
    },

    // 仅允许“实际入库数量 < 计划入库数量”的条目可被选择
    isRowSelectable(row) {
      const est = Number(row.estimatedInboundAmount) || 0
      const act = Number(row.actualInboundAmount) || 0
      return act < est
      // 如果更喜欢用欠数判断：return (Number(row.remainingAmount) || 0) > 0
    },

    confirmTableData(filters) {
      this.searchFilters = { ...filters }
      this.getTableData()
    },
    getCellStyle({ column }) {
      if (column.property === 'remainingAmount') {
        return { color: 'red' }
      }
      return {}
    },
    updateSemiShoeTotal() {
      this.currentQuantityRow.shoesInboundTable.forEach((element, index) => {
        this.currentQuantityRow[`amount${index}`] = element.operationQuantity
      })
      this.currentQuantityRow.operationQuantity = this.filteredData.reduce((acc, row) => {
        return acc + (Number(row.operationQuantity) || 0)
      }, 0)
    },
    openQuantityDialog(row) {
      this.currentQuantityRow = row
      this.isOpenQuantityDialogVisible = true
    },
    async toggleSelectionMode() {
      this.isMultipleSelection = !this.isMultipleSelection
      if (!this.isMultipleSelection) {
        // 退出选择模式清空
        this.selectedRows = []
        this.selectedIds = []
      }
      // 进入/退出选择模式都刷新一遍（进入时带上 inboundableOnly=1）
      await this.getTableData()
      // 进入模式时可能已有勾选（如分页返回回来），恢复
      if (this.isMultipleSelection) await this.restoreSelections()
    },
    handleSelectionChange(selection) {
      this.selectedRows = selection
      this.persistSelections() // ✅ 每次变更同步 selectedIds
    },

    // —— 入库前：强制以“仅可入库”刷新，并恢复+校验选择 —— //

    // 入库：刷新仅可入库数据 -> 恢复并校验选择 -> 打开弹窗
    async openOperationDialog() {

      if (this.selectedRows.length === 0) {
        ElMessage.error('未选择条目或无可入库条目')
        return
      }
      // 兜底防并发
      const valid = this.selectedRows.filter((r) => {
        const est = Number(r.estimatedInboundAmount) || 0
        const act = Number(r.actualInboundAmount) || 0
        return act < est
      })
      if (valid.length === 0) {
        ElMessage.error('所选条目均已完成入库')
        return
      }
      if (valid.length < this.selectedRows.length) {
        ElMessage.warning(`已排除 ${this.selectedRows.length - valid.length} 条已完成入库的条目`)
      }
      this.selectedRows = valid
      this.persistSelections()

      this.groupSelectedRows()
      this.isMultiInboundDialogVisible = true
    },

    async groupSelectedRows() {
      let groupedData = []
      this.inboundForm = JSON.parse(JSON.stringify(this.formItemTemplate))
      for (let item of this.selectedRows) {
        let newItem = { ...item, operationQuantity: 0, remark: '', shoesInboundTable: [] }
        // 按鞋码展开尺码入库表
        for (let i = 0; i < item.shoeSizeColumns.length; i++) {
          const column = item.shoeSizeColumns[i]
          if (column === '') break
          newItem.shoesInboundTable.push({
            shoeSizeName: column,
            predictQuantity: item[`size${i + 34}EstimatedAmount`],
            actualQuantity: item[`size${i + 34}ActualAmount`],
            currentQuantity: item[`size${i + 34}Amount`],
            operationQuantity:
              (item[`size${i + 34}EstimatedAmount`] || 0) - (item[`size${i + 34}ActualAmount`] || 0)
          })
        }
        newItem.shoesInboundTable.forEach((element, index) => {
          newItem[`amount${index}`] = element.operationQuantity
          newItem.operationQuantity += Number(element.operationQuantity) || 0
        })
        // 行总操作数与默认入库数
        newItem.operationQuantity = (item.estimatedInboundAmount || 0) - (item.actualInboundAmount || 0)
        newItem.inboundQuantity = newItem.operationQuantity

        const group = groupedData.find((g) => g.orderShoeId === item.orderShoeId)
        if (group) {
          group.items.push(newItem)
        } else {
          groupedData.push({
            orderShoeId: item.orderShoeId,
            items: [newItem]
          })
        }
      }
      this.inboundForm.orderShoeItems = groupedData
      this.activeTab = groupedData[0]?.orderShoeId ?? null
    },

    // 加了可选参数：forceInboundableOnly=true 时，强制以“仅可入库”刷新
    async getTableData({ forceInboundableOnly = false } = {}) {
      const params = {
        page: this.currentPage,
        pageSize: this.pageSize,
        orderRId: this.searchFilters.orderRIdSearch,
        shoeRId: this.searchFilters.shoeRIdSearch,
        customerName: this.searchFilters.customerNameSearch,
        customerProductName: this.searchFilters.customerProductNameSearch,
        orderCId: this.searchFilters.orderCIdSearch,
        customerBrand: this.searchFilters.customerBrandSearch,
        showAll: 0,
        // 进入选择模式或强制刷新时，只取“可入库”
        inboundableOnly: this.isMultipleSelection || forceInboundableOnly ? 1 : 0
      }
      // 刷新前保存一次选择主键，避免瞬间清空
      this.persistSelections()

      const { data } = await axios.get(`${this.$apiBaseUrl}/warehouse/getfinishedstorages`, { params })
      this.tableData = data.result
      this.totalRows = data.total

      // 恢复选择（可多次调用，Element Plus 会去重）
      await this.restoreSelections()

      // 同步顶部欠数
      const resp2 = await axios.get(`${this.$apiBaseUrl}/warehouse/getremainingamountoffinishedstorage`, { params })
      this.totalRemainingAmount = resp2.data.remainingAmount
    },

    async submitOperationForm() {
      let data = {
        remark: this.inboundForm.remark,
        items: []
      }
      for (let orderShoeItem of this.inboundForm.orderShoeItems) {
        for (let item of orderShoeItem.items) {
          const obj = {
            storageId: item.storageId,
            inboundQuantity: item.inboundQuantity,
            remark: item.remark
          }
          const amountList = []
          for (let i = 0; i < item.shoesInboundTable.length; i++) {
            amountList.push(item[`amount${i}`])
          }
          obj.amountList = amountList
          data.items.push(obj)
        }
      }
      try {
        await axios.patch(`${this.$apiBaseUrl}/warehouse/inboundfinished`, data)
        ElMessage.success('入库成功')
      } catch (error) {
        console.log(error)
        ElMessage.error('操作异常')
      }
      this.isMultiInboundDialogVisible = false
      this.getTableData()
    },

    handleSizeChange(val) {
      this.pageSize = val
      this.getTableData()
    },
    handlePageChange(val) {
      this.currentPage = val
      this.getTableData()
    },

    finishInbound(row) {
      ElMessageBox.alert('提前完成半成品入库，是否继续？', '警告', {
        confirmButtonText: '确认',
        showCancelButton: true,
        cancelButtonText: '取消'
      }).then(async () => {
        const data = { storageId: row.storageId }
        try {
          await axios.patch(`${this.$apiBaseUrl}/warehouse/warehousemanager/finishinboundfinished`, data)
          ElMessage.success('操作成功')
        } catch (error) {
          console.log(error)
          ElMessage.error('操作异常')
        }
        this.getTableData()
      })
    }
  }
}
</script>
