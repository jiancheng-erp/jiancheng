<template>
  <div class="production-board">
    <el-container>
      <el-header class="board-header">
        <span class="board-title">{{ boardTitle }}</span>
      </el-header>
      <el-main class="board-main">
        <el-table
          :data="tableData"
          border
          :cell-style="cellStyle"
          :header-cell-style="headerCellStyle"
          :default-sort="{ prop: 'onlineTime', order: 'ascending' }"
          class="production-table"
        >
          <el-table-column
            prop="idCustomers"
            label="客户"
            width="160"
            align="center"
            class-name="custom-font-size"
          />
          <el-table-column
            prop="idOrders"
            label="订单号"
            width="160"
            align="center"
            class-name="custom-font-size"
          />
          <el-table-column
            prop="idShoes"
            label="工厂鞋型"
            width="160"
            align="center"
            class-name="custom-font-size"
          />
          <el-table-column prop="Amount" label="双数" width="90" align="center" />
          <el-table-column prop="Color" label="颜色" width="120" align="center" />

          <!-- 动态尺码列：label 来自 size_xx_name -->
          <el-table-column label="码段" align="center">
            <el-table-column
              v-for="col in sizeColumns"
              :key="col.prop"
              :prop="col.prop"
              :label="col.label"
              width="90"
              align="center"
            />
          </el-table-column>

          <el-table-column prop="onlineTime" label="上线时间" width="140" align="center" />
          <el-table-column prop="predictTime" label="预计完成时间" width="160" align="center" />
          <el-table-column
            prop="processRequirements"
            label="生产工艺要求"
            align="center"
            min-width="200"
            :span-method="objectSpanMethod"
          />
        </el-table>
      </el-main>
      <el-footer class="board-footer">
        <el-button type="primary" @click="backToDashboard">返回管理主页面</el-button>
      </el-footer>
    </el-container>
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue';
import type { TableColumnCtx } from 'element-plus';
import axios from 'axios';

/** 前端表格结构（支持动态尺码字段） */
interface Order {
  idCustomers: string;
  idOrders: string;
  idShoes: string;
  Amount: number;
  Color: string;
  onlineTime: string;
  predictTime: string;
  processRequirements: string;
  // 动态挂载 size34 ~ size46
  [key: string]: any;
}

/** 后端 /production/dashboard/todaymoldingorders 返回的结构 */
interface SizeItem {
  name: string | null;
  amount: number | null;
}

interface RawMoldingOrder {
  orderId: number;
  orderRId: string;
  shoeTypeId: number;
  colorName: string | null;
  orderShoeId: number;
  customerProductName: string | null;
  customerName: string;
  shoeId: number;
  shoeRId: string;
  moldingLineGroup: string | null;
  moldingStartDate: string; // 已经 format_date 过
  moldingEndDate: string;
  totalAmount: number | null;
  sizeAmounts: {
    size34: SizeItem;
    size35: SizeItem;
    size36: SizeItem;
    size37: SizeItem;
    size38: SizeItem;
    size39: SizeItem;
    size40: SizeItem;
    size41: SizeItem;
    size42: SizeItem;
    size43: SizeItem;
    size44: SizeItem;
    size45: SizeItem;
    size46: SizeItem;
  };
}

interface SpanMethodProps {
  row: Order;
  column: TableColumnCtx<Order>;
  rowIndex: number;
  columnIndex: number;
}

interface SizeColumnDef {
  prop: string;  // 'size34' ~ 'size46'
  label: string; // 来自 size_xx_name，比如 '34' / '35' / '6.5'
}

export default defineComponent({
  name: 'ProductionBoard',
  data() {
    return {
      tableData: [] as Order[],
      allData: [] as Order[],
      currentPage: 1,
      pageSize: 6,
      timerId: null as ReturnType<typeof setInterval> | null,
      lineId: '1',
      sizeColumns: [] as SizeColumnDef[],
    };
  },
  computed: {
    boardTitle(): string {
      return '健诚集团生产检测可视化看板';
    },
  },
  watch: {
    '$route.query.line'(newVal: string | undefined) {
      this.lineId = newVal || '1';
      this.fetchOrders();
    },
  },
  mounted() {
    this.lineId = (this.$route.query.line as string) || '1';
    this.fetchOrders();
  },
  beforeUnmount() {
    this.clearTimer();
  },
  methods: {
    /** 表头样式 */
    headerCellStyle() {
      return {
        background:
          'linear-gradient(90deg, rgba(0, 180, 255, 0.45), rgba(0, 255, 210, 0.35))',
        color: '#E8F7FF',
        fontSize: '18px',
        fontWeight: 600,
        borderBottom: '1px solid rgba(0, 255, 255, 0.5)',
      };
    },
    /** 单元格样式 */
    cellStyle() {
      return {
        height: '45px',
        color: '#E4F3FF',
        fontSize: '16px',
      };
    },
    /** 合并“生产工艺要求”列（保留原逻辑） */
    objectSpanMethod({ row, column, rowIndex, columnIndex }: SpanMethodProps) {
      // 这里只示意保留原逻辑，如果你以后不需要合并可以直接 return
      // 假设工艺要求在最后一列，columnIndex 可以按需要调整
      const lastColumnIndex = 9 + this.sizeColumns.length; // 前 5 列 + 动态尺码列 + 2 列时间
      if (columnIndex === lastColumnIndex) {
        if (rowIndex < this.tableData.length - 1) {
          let rowspan = 1;
          let i = rowIndex + 1;
          while (
            i < this.tableData.length &&
            this.tableData[rowIndex][column.property as keyof Order] ===
              this.tableData[i][column.property as keyof Order]
          ) {
            rowspan++;
            i++;
          }
          if (
            rowIndex === 0 ||
            this.tableData[rowIndex][column.property as keyof Order] !==
              this.tableData[rowIndex - 1][column.property as keyof Order]
          ) {
            return { rowspan, colspan: 1 };
          }
        }
        return { rowspan: 0, colspan: 0 };
      }
      return undefined;
    },
    updateTableData() {
      const start = (this.currentPage - 1) * this.pageSize;
      this.tableData = this.allData.slice(start, start + this.pageSize);
    },
    startTimer() {
      this.clearTimer();
      this.timerId = setInterval(this.nextPage, 15000);
    },
    clearTimer() {
      if (this.timerId) {
        clearInterval(this.timerId);
        this.timerId = null;
      }
    },
    nextPage() {
      if (this.currentPage * this.pageSize < this.allData.length) {
        this.currentPage += 1;
      } else {
        this.currentPage = 1;
      }
      this.updateTableData();
    },

    /** 根据后端 size_xx_name 构造动态列：34/35/6.5... 按 34->46 顺序 */
    buildSizeColumns(rawList: RawMoldingOrder[]) {
      this.sizeColumns = [];
      if (!rawList.length) return;

      const first = rawList[0].sizeAmounts;
      const fields: Array<keyof RawMoldingOrder['sizeAmounts']> = [
        'size34',
        'size35',
        'size36',
        'size37',
        'size38',
        'size39',
        'size40',
        'size41',
        'size42',
        'size43',
        'size44',
        'size45',
        'size46',
      ];

      fields.forEach((key) => {
        const item = first[key];
        if (item && item.name) {
          this.sizeColumns.push({
            prop: key,        // 对应每一行上的字段
            label: item.name, // 列头显示这个 name，例如 34 / 35 / 6.5
          });
        }
      });
    },

    /** 把后端一条记录转换成前端 Order 结构，并填充所有启用的尺码列 */
    transformOrder(raw: RawMoldingOrder): Order {
      const order: Order = {
        idCustomers: raw.customerName,
        idOrders: raw.orderRId,
        idShoes: raw.shoeRId,
        Amount: raw.totalAmount ?? 0,
        Color: raw.colorName || '',
        onlineTime: raw.moldingStartDate,
        predictTime: raw.moldingEndDate,
        processRequirements: '', // 暂时没有工艺要求字段
      };

      // 给当前记录挂上各尺码数量（只对已启用的尺码列赋值）
      const sizeAmounts = raw.sizeAmounts;
      this.sizeColumns.forEach((col) => {
        const item = sizeAmounts[col.prop as keyof typeof sizeAmounts];
        order[col.prop] = item?.amount ?? 0;
      });

      return order;
    },

    /** 拉取后端数据并转换 */
    async fetchOrders() {
      try {
        const response = await axios.get<RawMoldingOrder[]>(
          `${this.$apiBaseUrl}/production/dashboard/todaymoldingorders`,
          { params: { line: this.lineId } },
        );

        const rawList = response.data || [];
        // 先根据第一条记录生成尺码列
        this.buildSizeColumns(rawList);
        // 再把所有记录映射成表格用的数据
        this.allData = rawList.map((item) => this.transformOrder(item));

        this.currentPage = 1;
        this.updateTableData();
        this.startTimer();
      } catch (error) {
        console.error('Failed to load production orders', error);
        this.allData = [];
        this.tableData = [];
      }
    },

    backToDashboard() {
      this.$router.push('/administrator');
    },
  },
});
</script>

<style scoped>
.production-board {
  background:
    radial-gradient(circle at top left, rgba(0, 140, 255, 0.28), transparent 45%),
    radial-gradient(circle at bottom right, rgba(0, 255, 210, 0.26), transparent 40%),
    #050d18;
  min-height: 100vh;
  color: #e8f7ff;
  padding: 12px;
  display: flex;
  flex-direction: column;
}
.el-main {
  background: transparent;
}

.board-header {
  text-align: center;
  height: 100px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.board-title {
  font-size: 48px;
  font-weight: 700;
  letter-spacing: 2px;
  background: linear-gradient(120deg, #00eaff, #7df9ff, #ffffff);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
  text-shadow: 0 0 12px rgba(0, 255, 255, 0.8);
}

.board-main {
  padding: 10px;
}

/* 表格整体主题 */
.production-table {
  --el-table-bg-color: transparent;
  --el-table-border-color: rgba(0, 255, 255, 0.45);
  --el-table-header-text-color: #e8f7ff;
  --el-table-row-hover-bg-color: rgba(0, 255, 255, 0.08);
  --el-table-tr-bg-color: transparent;
  --el-table-header-bg-color: rgba(3, 40, 70, 0.9);
  --el-table-text-color: #e4f3ff;
  --el-table-border: 2px solid rgba(0, 255, 255, 0.6);
  border: 2px solid rgba(0, 255, 255, 0.3);
  font-size: 16px;
  box-shadow: 0 0 25px rgba(0, 200, 255, 0.35);
  border-radius: 10px;
  overflow: hidden;
}

/* 修正 scoped 下 Element Plus 内部文字颜色 */
.production-table :deep(.el-table__cell) {
  color: #e4f3ff;
}

.production-table :deep(.el-table__header .el-table__cell) {
  font-weight: 600;
}

/* 行 hover 效果 */
.production-table :deep(.el-table__row) {
  transition: background-color 0.25s ease, transform 0.15s ease;
}

.production-table :deep(.el-table__row:hover) {
  background-color: rgba(0, 255, 255, 0.08) !important;
}

/* 斑马纹 */
.production-table :deep(.el-table__row--striped) {
  background-color: rgba(5, 25, 45, 0.8);
}

/* “客户 / 订单号 / 工厂鞋型”略小一点 */
.custom-font-size .cell {
  font-size: 14px;
}

/* 底部按钮区域 */
.board-footer {
  text-align: center;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 按钮轻微发光 */
.board-footer :deep(.el-button--primary) {
  box-shadow: 0 0 12px rgba(0, 200, 255, 0.7);
}
</style>
