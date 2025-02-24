<template>
  <el-row :gutter="20" style="margin-top: 20px">
    <el-col :span="8" :offset="0">
      <el-radio-group v-model="lineType" size="large">
        <el-radio-button label="裁断" value="0" />
        <el-radio-button label="针车预备" value="1" />
        <el-radio-button label="针车" value="2" />
        <el-radio-button label="成型" value="3" />
      </el-radio-group>
    </el-col>
    <el-col :span="4" :offset="0" style="white-space: nowrap">
      选择生产线：
      <el-select
        v-model="linenum"
        value-key=""
        placeholder=""
        clearable
        filterable
        @change=""
        :disabled="lineType !== '3'"
      >
        <el-option
          v-for="item in options"
          :key="item.value"
          :label="item.label"
          :value="item.value"
        >
        </el-option>
      </el-select>
    </el-col>
    <el-col :span="4" :offset="8"
      ><el-button type="primary" size="default" @click="isScheduleVis = true">编辑排期</el-button>
    </el-col>
  </el-row>
  <vue-cal
    :disable-views="['years', 'year']"
    locale="zh-cn"
    :time="false"
    :events="events"
    style="height: 550px"
  >
    <template #event="{ event, view }">
      <!-- <el-image :src="event.image" fit="fill" :lazy="true"></el-image> -->

      <div class="vuecal__event-title">订单号： {{ event.title }}</div>
      <div class="vuecal__event-cotent">鞋型号： {{ event.content }}</div>
      <div>数量：{{ event.number }}</div>
      <div>已使用生产线数量： {{ event.lineUsage }}</div>
    </template>
    <template #cell-content="{ cell, view, events, goNarrower }">
      <span class="vuecal__no-event" v-if="['week', 'day'].includes(view.id) && !events.length"
        >没有任务</span
      >
    </template>
  </vue-cal>
  <el-dialog title="排期编辑页面" v-model="isScheduleVis" width="90%">
    <span>
      <el-text>未排产订单</el-text>
      <el-input
        v-model="dialogOrderSearch"
        placeholder=""
        size=""
        clearable
        @change=""
      ></el-input>
      <el-table :data="unprocessedOrder" border stripe style="height: 350px">
        <el-table-column prop="orderId" label="订单编号"> </el-table-column>
        <el-table-column prop="createDate" label="订单创建日期"> </el-table-column>
        <el-table-column label="物流状态">
          <template #default="scope">
            <el-button type="primary" size="default" @click="isShoeLogisticVis = true"
              >查看详细状态</el-button
            >
          </template>
        </el-table-column>
        <el-table-column prop="shipDate" label="订单出货日期"> </el-table-column>
        <el-table-column label="操作">
          <template #default="scope">
            <el-button type="primary" size="default" @click="isShoeScheduleVis = true"
              >排产</el-button
            >
          </template>
        </el-table-column>
      </el-table>
      <el-text>已排产订单</el-text>
      <el-input
        v-model="dialogOrderSearch"
        placeholder=""
        size=""
        clearable
        @change=""
      ></el-input>
      <el-table :data="processedOrder" border stripe style="height: 350px">
        <el-table-column prop="orderId" label="订单编号"> </el-table-column>
        <el-table-column prop="createDate" label="订单创建日期"> </el-table-column>
        <el-table-column label="物流状态">
          <template #default="scope">
            <el-button type="primary" size="default" @click="isShoeLogisticVis = true"
              >查看详细状态</el-button
            >
          </template>
        </el-table-column>
        <el-table-column prop="remainAmount" label="成型剩余数量"> </el-table-column>
        <el-table-column prop="orderStatus" label="订单状态"> </el-table-column>
        <el-table-column prop="shipDate" label="订单出货日期"> </el-table-column>
        <el-table-column label="操作">
          <template #default="scope">
            <el-button type="primary" size="default" @click="isShoeScheduleVis = true"
              >修改排产</el-button
            >
          </template>
        </el-table-column>
      </el-table>
    </span>
    <template #footer>
      <span>
        <el-button @click="">取消</el-button>
        <el-button type="primary" @click="">确认</el-button>
      </span>
    </template>
  </el-dialog>
  <el-dialog title="订单号 K24-2111620 鞋型排产详情" v-model="isShoeScheduleVis" width="90%">
    <span>
      <el-table :data="shoeProcess" border stripe>
        <el-table-column type="expand">
          <template #default="scope">
            <el-descriptions title="" column="2">
              <el-descriptions-item label="裁断完成情况">{{
                scope.row.details.cutStatus
              }}</el-descriptions-item>
              <el-descriptions-item label="裁断完成数量">{{
                scope.row.details.cutAmount
              }}</el-descriptions-item>
              <el-descriptions-item label="针车预备完成情况">{{
                scope.row.details.sewPreStatus
              }}</el-descriptions-item>
              <el-descriptions-item label="针车预备完成数量">{{
                scope.row.details.sewPreAmount
              }}</el-descriptions-item>
              <el-descriptions-item label="针车完成情况">{{
                scope.row.details.sewStatus
              }}</el-descriptions-item>
              <el-descriptions-item label="针车完成数量">{{
                scope.row.details.sewAmount
              }}</el-descriptions-item>
              <el-descriptions-item label="成型完成情况">{{
                scope.row.details.moldStatus
              }}</el-descriptions-item>
              <el-descriptions-item label="成型完成数量">{{
                scope.row.details.moldAmount
              }}</el-descriptions-item>
            </el-descriptions>
          </template>
        </el-table-column>
        <el-table-column prop="inheritId" label="工厂型号"> </el-table-column>
        <el-table-column prop="customerTypeId" label="客户型号"> </el-table-column>
        <el-table-column prop="remainAmount" label="数量"> </el-table-column>
        <el-table-column prop="cutLine" label="裁断线号"> </el-table-column>
        <el-table-column prop="cutDatePeriod" label="裁断周期"> </el-table-column>
        <el-table-column prop="sewPreLine" label="针车预备线号"> </el-table-column>
        <el-table-column prop="sewPreDatePeriod" label="针车预备周期"> </el-table-column>
        <el-table-column prop="sewLine" label="针车线号"> </el-table-column>
        <el-table-column prop="sewDatePeriod" label="针车周期"> </el-table-column>
        <el-table-column prop="moldLine" label="成型线号"> </el-table-column>
        <el-table-column prop="moldDatePeriod" label="成型周期"> </el-table-column>
        <el-table-column label="操作">
          <template #default="scope">
            <el-button type="primary" size="default" @click="isScheduleModify = true"
              >修改排期</el-button
            >
          </template>
        </el-table-column>
      </el-table>
    </span>
    <template #footer>
      <span>
        <el-button @click="">取消</el-button>
        <el-button type="primary" @click="">确认</el-button>
      </span>
    </template>
  </el-dialog>

  <el-dialog title="修改排产信息" v-model="isScheduleModify" width="60%">
    <el-tabs v-model="activeTab" type="card" tab-position="top" @tab-click="">
      <el-tab-pane v-for="tab in tabs" :key="tab.name" :label="tab.label" :name="tab.name">
        <el-row :gutter="20">
          <el-col :span="10" :offset="0">
            <span style="white-space: nowrap">
              {{ tab.lineLabel }}：
              <el-select v-model="tab.lineValue" placeholder="" @change="" multiple>
                <el-option
                  v-for="item in cuttingLineOption"
                  :key="item"
                  :label="item"
                  :value="item"
                >
                </el-option>
              </el-select>
            </span>
          </el-col>
          <el-col :span="8" :offset="6"
            ><el-descriptions title="" border>
              <el-descriptions-item label="外包状态"
                >未外包
                <el-button
                  v-if="tab.isOutSource === 0"
                  type="primary"
                  size="default"
                  @click="startOutSourceFlow()"
                  style="margin-left: 5px"
                  >启动外包流程</el-button
                >
                <el-button
                  v-else-if="tab.isOutSource === 1"
                  type="primary"
                  size="default"
                  @click=""
                  style="margin-left: 5px"
                  >查看外包流程</el-button
                >
                <el-button
                  v-else-if="tab.isOutSource === 2"
                  type="primary"
                  size="default"
                  @click=""
                  style="margin-left: 5px"
                  >查看外包流程</el-button
                >
                <el-button
                  v-else-if="tab.isOutSource === 3"
                  type="primary"
                  size="default"
                  @click=""
                  style="margin-left: 5px"
                  >查看外包流程</el-button
                >
              </el-descriptions-item>
            </el-descriptions></el-col
          >
        </el-row>
        <el-row :gutter="20">
          <el-col :span="10" :offset="0">
            <span>
              {{ tab.dateLabel }}：
              <el-date-picker
                v-model="tab.dateValue"
                type="daterange"
                size=""
                range-separator="-"
                start-placeholder=""
                end-placeholder=""
              >
              </el-date-picker>
            </span>
          </el-col>
          <el-col :span="12" :offset="0"
            >预计每天生产数量：{{ calculateDailyProduction(tab.dateValue) }}</el-col
          >
        </el-row>
        <el-row :gutter="20">
          <el-col :span="24" :offset="0">
            <el-table :data="dateStatusTable" border stripe>
              <el-table-column type="expand">
                <template #default="props">
                  <el-table :data="props.row.shoeList" :border="childBorder">
                    <el-table-column type="index" />
                    <el-table-column label="订单号" prop="orderId" />
                    <el-table-column label="工厂型号" prop="shoeId" />
                    <el-table-column label="鞋型总数量" prop="amount" />
                    <el-table-column label="生产周期" prop="datePeriod" />
                    <el-table-column label="平均每天数量" prop="averageAmount" />
                  </el-table>
                </template>
              </el-table-column>

              <el-table-column prop="date" label="日期"> </el-table-column>
              <el-table-column prop="productAmount" label="已排产鞋型数"> </el-table-column>
              <el-table-column prop="predictAmount" label="预计当日现有生产量"> </el-table-column>
            </el-table>
          </el-col>
        </el-row>
      </el-tab-pane>
    </el-tabs>

    <span> </span>
    <template #footer>
      <span>
        <el-button @click="">取消</el-button>
        <el-button type="primary" @click="">确认</el-button>
      </span>
    </template>
  </el-dialog>

  <el-dialog title="订单 K24-2111620 鞋型物流信息一览" v-model="isShoeLogisticVis" width="90%">
    <el-table :data="logisticsShoeData" border stripe>
      <el-table-column prop="inheritId" label="工厂型号"></el-table-column>
      <el-table-column prop="customerTypeId" label="客户型号"></el-table-column>
      <el-table-column
        prop="fabricStatus"
        label="面料辅料状态"
        :formatter="statusFormatter"
      ></el-table-column>
      <el-table-column
        prop="smallPartsStatus"
        label="扣件拉链鞋带等小件状态"
        :formatter="statusFormatter"
      ></el-table-column>
      <el-table-column
        prop="soleStatus"
        label="鞋底状态"
        :formatter="statusFormatter"
      ></el-table-column>
      <el-table-column
        prop="insoleStatus"
        label="中底状态"
        :formatter="statusFormatter"
      ></el-table-column>
      <el-table-column
        prop="lastStatus"
        label="楦型状态"
        :formatter="statusFormatter"
      ></el-table-column>
      <el-table-column
        prop="packingStatus"
        label="包材状态"
        :formatter="statusFormatter"
      ></el-table-column>
      <el-table-column label="详细信息">
        <template #default="scope">
          <el-button type="primary" size="default" @click="isMaterialLogisticVis = true"
            >查看所有材料信息</el-button
          >
        </template>
      </el-table-column>
    </el-table>

    <template #footer>
      <span>
        <el-button @click="">Cancel</el-button>
        <el-button type="primary" @click="">OK</el-button>
      </span>
    </template>
  </el-dialog>
  <el-dialog title="鞋型所有材料物流信息" v-model="isMaterialLogisticVis" width="80%">
    <el-row :gutter="20">
      <el-col :span="24" :offset="0">
        <el-table :data="logisticsMaterialData" border stripe>
          <el-table-column prop="partName" label="部件名称"></el-table-column>
          <el-table-column prop="materialName" label="材料名称"></el-table-column>
          <el-table-column prop="color" label="颜色"></el-table-column>
          <el-table-column prop="approvedUsage" label="核定用量"></el-table-column>
          <el-table-column prop="purchaseAmount" label="采购数量"></el-table-column>
          <el-table-column prop="factoryName" label="供应商名称"></el-table-column>
          <el-table-column prop="materialType" label="材料类型"></el-table-column>
          <el-table-column prop="materialStatus" label="材料状态"></el-table-column>
        </el-table>
      </el-col>
    </el-row>

    <template #footer>
      <span>
        <el-button @click="">Cancel</el-button>
        <el-button type="primary" @click="">OK</el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script>
import VueCal from 'vue-cal'
import 'vue-cal/dist/vuecal.css'

export default {
  components: {
    VueCal
  },
  data() {
    return {
      activeTab: '裁断排产',
      cuttingLine: 1,
      cuttingDatePicker: '',
      sewPreLine: 1,
      sewPreDatePicker: '',
      dialogOrderSearch: '',
      isMaterialLogisticVis: false,
      isShoeLogisticVis: false,
      isShoeScheduleVis: false,
      isScheduleVis: false,
      isScheduleModify: false,
      lineType: '0',
      linenum: '',
      unprocessedOrder: [
        {
          orderId: 'K24-2111620',
          createDate: '2024-07-08',
          logisticsStatus: 0,
          orderStatus: '已逾期',
          shipDate: '2024-09-10'
        }
      ],
      processedOrder: [
        {
          orderId: 'K24-2111620',
          createDate: '2024-07-08',
          logisticsStatus: 0,
          remainAmount: 5000,
          orderStatus: '已逾期',
          cutDatePeriod: '2024-07-09 至 2024-08-16',
          sewPreDatePeriod: '2024-07-09 至 2024-08-16',
          sewDatePeriod: '2024-07-09 至 2024-08-16',
          moldDatePeriod: '2024-07-09 至 2024-08-16',
          shipDate: '2024-09-10'
        }
      ],
      shoeProcess: [
        {
          inheritId: '0E26210',
          customerTypeId: 'VRA-015',
          logisticsStatus: 0,
          remainAmount: 5000,
          cutLine: 1,
          cutDatePeriod: '2024-07-09 至 2024-08-16',
          sewPreLine: 1,
          sewPreDatePeriod: '2024-07-09 至 2024-08-16',
          sewLine: 2,
          sewDatePeriod: '2024-07-09 至 2024-08-16',
          moldLine: 4,
          moldDatePeriod: '2024-07-09 至 2024-08-16',
          details: {
            cutStatus: '未完成',
            cutAmount: '1000/5000',
            sewPreStatus: '未完成',
            sewPreAmount: '1000/5000',
            sewStatus: '未完成',
            sewAmount: '1000/5000',
            moldStatus: '未完成',
            moldAmount: '1000/5000'
          }
        }
      ],
      events: [
        {
          start: '2024-07-04',
          end: '2024-07-06',
          title: 'K24-0111620',
          content: '0E21922',
          class: 'leisure',
          number: 500,
          lineUsage: 5,
          image: 'https://via.placeholder.com/50'
        },
        {
          start: '2024-07-06',
          end: '2024-07-07',
          title: 'K24-0111621',
          content: '0E21922',
          class: 'sport',
          image: 'https://via.placeholder.com/50'
        }
      ],
      cuttingLineOption: [1, 2, 3, 4],
      tabs: [
        {
          name: '裁断排产',
          label: '裁断排产',
          lineLabel: '裁断线号选择',
          dateLabel: '裁断工期选择',
          lineValue: [],
          dateValue: null,
          isOutSource: 0
        },
        {
          name: '针车预备排产',
          label: '针车预备排产',
          lineLabel: '针车线号选择',
          dateLabel: '针车工期选择',
          lineValue: [],
          dateValue: null,
          isOutSource: 1
        },
        {
          name: '针车排产',
          label: '针车排产',
          lineLabel: '针车线号选择',
          dateLabel: '针车工期选择',
          lineValue: [],
          dateValue: null,
          isOutSource: 0
        },
        {
          name: '成型排产',
          label: '成型排产',
          lineLabel: '成型线号选择',
          dateLabel: '成型工期选择',
          lineValue: [],
          dateValue: null,
          isOutSource: 0
        }
      ],
      dateStatusTable: [
        {
          date: '2024-07-16',
          productAmount: 10,
          predictAmount: 2000,
          shoeList: [
            {
              orderId: 'K24-2111620',
              shoeId: '0E11150',
              amount: 300,
              datePeriod: '2024-07-16 至 2024-07-20',
              averageAmount: 75
            }
          ]
        }
      ],
      logisticsMaterialData: [
        {
          partName: '鞋面',
          materialName: '黑色PU',
          color: '黑色',
          approvedUsage: 500,
          purchaseAmount: 550,
          factoryName: '一一鞋材',
          materialStatus: '未到货',
          materialType: '面料辅料'
        }
      ],
      logisticsShoeData: [
        {
          inheritId: '0E229940',
          customerTypeId: 'VRA-0015',
          fabricStatus: 0,
          smallPartsStatus: 0,
          soleStatus: 0,
          insoleStatus: 0,
          lastStatus: 0,
          packingStatus: 0,
          isCutOutsource: 0,
          isSewPreOutsource: 0,
          isSewOutsouce: 0,
          isMoldOutSouce: 0
        }
      ]
    }
  },
  methods: {
    calculateDailyProduction(dateRange) {
      if (dateRange && dateRange.length === 2) {
        const startDate = new Date(dateRange[0])
        const endDate = new Date(dateRange[1])
        const timeDiff = Math.abs(endDate - startDate)
        const diffDays = Math.ceil(timeDiff / (1000 * 60 * 60 * 24)) + 1
        return (5000 / diffDays).toFixed(2)
      }
      return 0
    },
    statusFormatter(row, column, cellValue, index) {
      let returnValue = ''
      switch (cellValue) {
        case 0:
          returnValue = '未订购'
          break
        case 1:
          returnValue = '已订购'
          break
        case 2:
          returnValue = '已到货'
          break
      }
      console.log(returnValue)
      return returnValue
    },
    startOutSourceFlow() {
      const orderId = "K24-2111620"
      const orderShoeId = "0E255530"
      const url = `${window.location.origin}/productiongeneral/productionoutsource/orderid=${orderId}&ordershoeid=${orderShoeId}`
      window.open(url, '_blank')

    }
  }
}
</script>
