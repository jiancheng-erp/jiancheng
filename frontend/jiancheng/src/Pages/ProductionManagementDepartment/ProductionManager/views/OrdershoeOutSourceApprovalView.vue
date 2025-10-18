<template>
  <el-container>
    <el-header class="app-header">
      <AllHeader></AllHeader>
    </el-header>
    <el-main height="">
      <el-row :gutter="20" style="text-align: center">
        <el-col :span="24" :offset="0" style="font-size: xx-large; text-align: center"
          >订单鞋型外包审批页面</el-col
        >
      </el-row>
      <el-row :gutter="20">
        <el-col :span="24" :offset="0"
          ><el-descriptions title="订单信息" border column="2">
            <el-descriptions-item label="订单号">K24-2111620</el-descriptions-item>
            <el-descriptions-item label="鞋型号">0E21922</el-descriptions-item>
            <el-descriptions-item label="客户号">37号客人</el-descriptions-item>
            <el-descriptions-item label="出货日期">2024-07-19</el-descriptions-item>
          </el-descriptions></el-col
        >
      </el-row>
      <el-row :gutter="20" style="margin-top: 20px">
        <el-col :span="24" :offset="0">
          鞋型配码信息
          <el-table :data="shoeInfo" border stripe :max-height="200">
            <el-table-column prop="color" label="颜色"></el-table-column>
            <el-table-column prop="shoeSize" label="配码编号"></el-table-column>
            <el-table-column prop="size35" label="35"></el-table-column>
            <el-table-column prop="size36" label="36"></el-table-column>
            <el-table-column prop="size37" label="37"></el-table-column>
            <el-table-column prop="size38" label="38"></el-table-column>
            <el-table-column prop="size39" label="39"></el-table-column>
            <el-table-column prop="size40" label="40"></el-table-column>
            <el-table-column prop="size41" label="41"></el-table-column>
            <el-table-column prop="pairAmount" label="双数"></el-table-column>
            <el-table-column prop="totalAmount" label="总数"></el-table-column>
          </el-table>
        </el-col>
      </el-row>
      <el-row :gutter="20">
        <el-col :span="24" :offset="0">
          现有外包流程
          <el-table :data="outSourceInfo" border stripe>
            <el-table-column prop="outSourceType" label="外包类型"></el-table-column>
            <el-table-column prop="outSourceFactory" label="外包厂家"></el-table-column>
            <el-table-column prop="outSourceAmount" label="外包数量"></el-table-column>
            <el-table-column prop="outSourcePeriod" label="外包周期"></el-table-column>
            <el-table-column prop="approvalStatus" label="审批状态"></el-table-column>
            <el-table-column label="仓库材料发货情况">
              <template #default="scope">
                <el-button type="primary" size="default" @click="isOutSourceLogistic = true"
                  >查看外包物料发货情况</el-button
                >
              </template>
            </el-table-column>
            <el-table-column prop="shipDate" label="最迟交货日期"></el-table-column>
            <el-table-column label="操作">
              <el-button type="primary" size="default" @click="isOutSourcePreviewVis = true"
                >查看并审核外包流程</el-button
              >
            </el-table-column>
          </el-table>
        </el-col>
      </el-row>
    </el-main>
  </el-container>
  <el-dialog title="预览外发信息" v-model="isOutSourcePreviewVis" width="80%">
    <el-row :gutter="20">
      <el-col :span="24" :offset="0">
        <el-descriptions title="外包信息一览">
          <el-descriptions-item label="外包类型">{{
            outSourceFinData.outSourceType
          }}</el-descriptions-item>
          <el-descriptions-item label="外包工厂">{{
            outSourceFinData.outSourceFactory
          }}</el-descriptions-item>
          <el-descriptions-item label="外包周期">{{
            outSourceFinData.outSourcePeriod
          }}</el-descriptions-item>
          <el-descriptions-item label="最迟交货日期">{{
            outSourceFinData.shipDate
          }}</el-descriptions-item>
          <el-descriptions-item label="半成品最迟发货日期">{{
            outSourceFinData.outSourceTransitShipDate
          }}</el-descriptions-item>
          <el-descriptions-item label="材料最迟发货日期">{{
            outSourceFinData.outSpirceMaterialShipDate
          }}</el-descriptions-item>
        </el-descriptions>
      </el-col>
    </el-row>
    <el-row :gutter="20">
      <el-col :span="24" :offset="0">
        <el-table :data="outSourceFinData.materialData" border stripe>
          <el-table-column prop="partName" label="部件名称" />
          <el-table-column prop="color" label="颜色" />
          <el-table-column prop="materialName" label="材料名称" />
          <el-table-column prop="unit" label="单位" />
          <el-table-column prop="shipAmount" label="应发货数量" />
          <el-table-column prop="status" label="状态" />
          <el-table-column prop="section" label="使用工段" />
          <el-table-column prop="date" label="到货日期" />
        </el-table>
      </el-col>
    </el-row>

    <template #footer>
      <span>
        <el-button @click="">Cancel</el-button>
        <el-button type="success" @click="">批准</el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script>
import AllHeader from '@/components/AllHeader.vue'
export default {
  components: {
    AllHeader
  },
  data() {
    return {
      isOutSourcePreviewVis: false,
      outSourceFinData: {
        outSourceType: '',
        outSourceFactory: '',
        outSourcePeriod: [],
        outSourceTransitShipDate: '',
        outSpirceMaterialShipDate: '',
        shipDate: '',

        materialData: [
          {
            partName: '鞋面',
            color: '红色',
            materialName: '牛皮',
            unit: '平方米',
            shipAmount: 10,
            status: '未到货',
            date: '2024-07-21'
          }
        ]
      },
      outSourceInfo: [
        {
          outSourceType: '裁断',
          outSourceFactory: 'XX鞋业',
          outSourceAmount: 500,
          outSourcePeriod: '2024-07-05-2024-07-18',
          shipDate: '2024-07-19',
          approvalStatus: '未审批'
        }
      ],
      shoeInfo: [
        {
          color: '黑色',
          shoeSize: 'S12A',
          size35: 0,
          size36: 64,
          size37: 128,
          size38: 192,
          size39: 192,
          size40: 128,
          size41: 64,
          pairAmount: 768,
          totalAmount: 1800
        },
        {
          color: '黑色',
          shoeSize: 'S12B',
          size35: 14,
          size36: 28,
          size37: 42,
          size38: 42,
          size39: 28,
          size40: 14,
          size41: 0,
          pairAmount: 168,
          totalAmount: 1800
        },
        {
          color: '黑色',
          shoeSize: 'S6A1',
          size35: 0,
          size36: 14,
          size37: 14,
          size38: 14,
          size39: 14,
          size40: 14,
          size41: 6,
          pairAmount: 84,
          totalAmount: 1800
        },
        {
          color: '黑色',
          shoeSize: 'S6A2',
          size35: 0,
          size36: 10,
          size37: 20,
          size38: 20,
          size39: 10,
          size40: 0,
          size41: 6,
          pairAmount: 60,
          totalAmount: 1800
        },
        {
          color: '黑色',
          shoeSize: 'S6B1',
          size35: 2,
          size36: 2,
          size37: 2,
          size38: 2,
          size39: 2,
          size40: 2,
          size41: 0,
          pairAmount: 12,
          totalAmount: 1800
        },
        {
          color: '黑色',
          shoeSize: 'S6B2',
          size35: 0,
          size36: 6,
          size37: 12,
          size38: 12,
          size39: 6,
          size40: 0,
          size41: 6,
          pairAmount: 36,
          totalAmount: 1800
        },
        {
          color: '黑色',
          shoeSize: 'S8A1',
          size35: 0,
          size36: 48,
          size37: 48,
          size38: 96,
          size39: 96,
          size40: 48,
          size41: 48,
          pairAmount: 384,
          totalAmount: 1800
        },
        {
          color: '黑色',
          shoeSize: 'S8A2',
          size35: 0,
          size36: 10,
          size37: 10,
          size38: 10,
          size39: 10,
          size40: 0,
          size41: 8,
          pairAmount: 40,
          totalAmount: 1800
        },
        {
          color: '黑色',
          shoeSize: 'S8A3',
          size35: 0,
          size36: 13,
          size37: 26,
          size38: 26,
          size39: 26,
          size40: 13,
          size41: 8,
          pairAmount: 104,
          totalAmount: 1800
        },
        {
          color: '黑色',
          shoeSize: 'S8B1',
          size35: 11,
          size36: 11,
          size37: 22,
          size38: 22,
          size39: 11,
          size40: 11,
          size41: 0,
          pairAmount: 88,
          totalAmount: 1800
        },
        {
          color: '黑色',
          shoeSize: 'S8B2',
          size35: 0,
          size36: 14,
          size37: 14,
          size38: 14,
          size39: 14,
          size40: 0,
          size41: 8,
          pairAmount: 56,
          totalAmount: 1800
        }
      ]
    }
  }
}
</script>
