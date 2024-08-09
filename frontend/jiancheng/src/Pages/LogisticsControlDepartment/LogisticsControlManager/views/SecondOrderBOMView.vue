<template>
  <el-container :direction="vertical">
    <el-header height="">
      <AllHeader></AllHeader>
    </el-header>
    <el-main height="">
      <el-row :gutter="20" style="text-align: center">
        <el-col :span="24" :offset="0" style="font-size: xx-large; text-align: center"
          >二次采购订单生成</el-col
        >
      </el-row>
      <el-row :gutter="20">
        <el-col :span="24" :offset="0">
          <span style="font-weight: bold; font-size: larger">订单信息：</span>
          <Arrow :status="11"></Arrow>
          <el-descriptions title="" :column="2">
            <el-descriptions-item label="订单编号">{{ orderId }}</el-descriptions-item>
            <el-descriptions-item label="订单创建时间">{{
              testOrderData.createTime
            }}</el-descriptions-item>
            <el-descriptions-item label="前序流程下发时间">{{
              testOrderData.prevTime
            }}</el-descriptions-item>
            <el-descriptions-item label="前序处理部门">{{
              testOrderData.prevDepart
            }}</el-descriptions-item>
            <el-descriptions-item label="前序处理人">{{
              testOrderData.prevUser
            }}</el-descriptions-item>
            <el-descriptions-item label="订单状态">{{
              testOrderData.orderrStatus
            }}</el-descriptions-item>
          </el-descriptions></el-col
        >
      </el-row>
      <el-row :gutter="20" style="margin-top: 20px">
        <el-col :span="24" :offset="0">
          <el-table :data="testTableData" border style="height: 400px">
            <el-table-column prop="bomId" label="BOM单编号"></el-table-column>
            <el-table-column prop="bomType" label="BOM类型"></el-table-column>
            <el-table-column prop="bomType" label="BOM类型"></el-table-column>
            <el-table-column prop="Status" label="状态"></el-table-column>
            <el-table-column label="操作">
              <template #default="scope">
                <el-button
                  v-if="scope.row.Status === '未生成材料统计表'"
                  type="primary"
                  @click="handleGenerate(scope.row)"
                  >生成</el-button
                >

                <div v-else-if="scope.row.Status === '已生成材料统计表'">
                  <el-button type="primary" @click="openPreviewDialog(scope.row)">查看</el-button>
                  <el-button type="warning" @click="isPurchaseOrderVis = true"
                    >生成采购订单</el-button
                  >
                </div>

                <div v-else-if="scope.row.Status === '已保存材料统计表'">
                  <el-button type="primary" @click="handleGenerate(scope.row)">编辑</el-button>
                  <el-button type="success" @click="openPreviewDialog(scope.row)">预览</el-button>
                </div>
              </template></el-table-column
            >
          </el-table></el-col
        >
      </el-row>
      <el-dialog
        title="二次采购订单 K2402121116202024061101F"
        v-model="createVis"
        width="90%"
        @close="handleGenerateClose"
      >
        <el-descriptions title="订单信息" :column="2">
          <el-descriptions-item label="订单编号">{{ orderId }}</el-descriptions-item>
          <el-descriptions-item label="订单创建时间">{{
            testOrderData.createTime
          }}</el-descriptions-item>
          <el-descriptions-item label="前序流程下发时间">{{
            testOrderData.prevTime
          }}</el-descriptions-item>
          <el-descriptions-item label="前序处理部门">{{
            testOrderData.prevDepart
          }}</el-descriptions-item>
          <el-descriptions-item label="前序处理人">{{
            testOrderData.prevUser
          }}</el-descriptions-item>
          <el-descriptions-item label="订单状态">{{
            testOrderData.orderrStatus
          }}</el-descriptions-item>
          <el-descriptions-item label="BOM编号">{{
            testOrderData.orderrStatus
          }}</el-descriptions-item>
        </el-descriptions>
        <el-table :data="bomTestData" border style="height: 400px">
          <el-table-column prop="partName" label="部件名称" />
          <el-table-column prop="color" label="颜色" />
          <el-table-column prop="materialType" label="材料类型" />
          <el-table-column prop="materialName" label="材料名称" />
          <el-table-column prop="materialSpecification" label="材料规格" />
          <el-table-column prop="unit" label="单位" width="75" />
          <el-table-column prop="unitUsage" label="单位用量" />
          <el-table-column prop="approvedUsage" label="核定用量" />
          <el-table-column label="采购数量">
            <template #default="scope">
              <el-input-number
                v-model="scope.row.purchaseAmount"
                :min="0"
                size="small"
                :disabled="sizeDisabled(scope.row, 0)"
              />
            </template>
          </el-table-column>
          <el-table-column label="工厂名称">
            <template #default="scope">
              <el-select v-model="scope.row.factoryName" placeholder="选择工厂">
                <el-option
                  v-for="factory in getFilteredFactoryOptions(scope.row.materialName)"
                  :key="factory.factoryName"
                  :label="factory.factoryName"
                  :value="factory.factoryName"
                />
              </el-select>
            </template>
          </el-table-column>
          <el-table-column prop="department" label="使用工段" />
          <el-table-column label="尺码信息" width="200">
            <template #default="scope">
              {{ scope.row.sizeStatus }}
              <el-button
                type="primary"
                size="default"
                @click="openSizeDialog(scope.row)"
                :disabled="sizeDisabled(scope.row, 1)"
                >尺码信息</el-button
              >
            </template>
          </el-table-column>
        </el-table>

        <template #footer>
          <span>
            <el-button @click="handleGenerateClose">取消</el-button>
            <el-button type="primary" @click="">保存</el-button>
          </span>
        </template>
      </el-dialog>

      <el-dialog
        title="预览采购订单 K2402121116202024061101F"
        v-model="isPreviewDialogVisible"
        width="90%"
      >
        <el-descriptions title="订单信息" :column="2">
          <el-descriptions-item label="订单编号">{{ orderId }}</el-descriptions-item>
        </el-descriptions>
        <div style="height: 500px; overflow-y: scroll; overflow-x: hidden">
          <el-row
            v-for="factory in purchaseTestData"
            :key="factory.factoryName"
            :gutter="20"
            style="margin-bottom: 20px"
          >
            <el-col :span="23">
              <h3>{{ factory.factoryName }}</h3>
              <div v-if="factoryFieldJudge(factory.factoryField)">
                <el-table :data="factory.data" border style="width: 100%">
                  <el-table-column type="index" label="编号" />
                  <el-table-column prop="materialType" label="材料类型"></el-table-column>
                  <el-table-column prop="materialName" label="材料名称" />
                  <el-table-column prop="materialSpecification" label="材料规格"></el-table-column>
                  <el-table-column prop="unit" label="单位" />

                  <el-table-column prop="amount" label="采购数量" />
                  <el-table-column label="分码数量（中国/美标内码/美标外显）">
                    <el-table-column label="35" width="50">
                      <el-table-column label="7" width="50">
                        <el-table-column prop="size35" label="7" width="50"></el-table-column>
                      </el-table-column>
                    </el-table-column>
                    <el-table-column label="36" width="50">
                      <el-table-column label="7" width="50">
                        <el-table-column prop="size36" label="7.5" width="50"></el-table-column>
                      </el-table-column>
                    </el-table-column>
                    <el-table-column label="37" width="50">
                      <el-table-column label="8" width="50">
                        <el-table-column prop="size37" label="8" width="50"></el-table-column>
                      </el-table-column>
                    </el-table-column>
                    <el-table-column label="38" width="50">
                      <el-table-column label="8" width="50">
                        <el-table-column prop="size38" label="8.5" width="50"></el-table-column>
                      </el-table-column>
                    </el-table-column>
                    <el-table-column label="39" width="50">
                      <el-table-column label="9" width="50">
                        <el-table-column prop="size39" label="9" width="50"></el-table-column>
                      </el-table-column>
                    </el-table-column>
                    <el-table-column label="40" width="50">
                      <el-table-column label="9" width="50">
                        <el-table-column prop="size40" label="9.5" width="50"></el-table-column>
                      </el-table-column>
                    </el-table-column>
                    <el-table-column label="41" width="50">
                      <el-table-column label="10" width="50">
                        <el-table-column prop="size41" label="10" width="50"></el-table-column>
                      </el-table-column>
                    </el-table-column>
                    <el-table-column label="42" width="50">
                      <el-table-column label="10" width="50">
                        <el-table-column prop="size42" label="10.5" width="50"></el-table-column>
                      </el-table-column>
                    </el-table-column>
                    <el-table-column label="43" width="50">
                      <el-table-column label="11" width="50">
                        <el-table-column prop="size43" label="11" width="50"></el-table-column>
                      </el-table-column>
                    </el-table-column>
                    <el-table-column label="44" width="50">
                      <el-table-column label="12" width="50">
                        <el-table-column prop="size44" label="12" width="50"></el-table-column>
                      </el-table-column>
                    </el-table-column>
                    <el-table-column label="45" width="50">
                      <el-table-column label="13" width="50">
                        <el-table-column prop="size45" label="13" width="50"></el-table-column>
                      </el-table-column>
                    </el-table-column>
                  </el-table-column>
                  <el-table-column prop="comment" label="备注" />
                </el-table>
              </div>
              <div v-else>
                <el-table :data="factory.data" border style="width: 100%">
                  <el-table-column type="index" label="编号" />
                  <el-table-column prop="materialType" label="材料类型"></el-table-column>
                  <el-table-column prop="materialName" label="材料名称" />
                  <el-table-column prop="materialSpecification" label="材料规格"></el-table-column>
                  <el-table-column prop="unit" label="单位" />
                  <el-table-column prop="unitUsage" label="单位用量" />
                  <el-table-column prop="approvedUsage" label="核定用量" />
                  <el-table-column prop="amount" label="采购数量" />
                  <el-table-column prop="comment" label="备注" />
                </el-table>
              </div>
            </el-col>
          </el-row>
        </div>
        <template #footer>
          <span>
            <el-button type="primary" @click="closePreviewDialog">确认</el-button>
          </span>
        </template>
      </el-dialog>
      <el-dialog title="采购订单创建页面" v-model="isPurchaseOrderVis" width="80%">
        <el-tabs v-model="activeTab" type="card" tab-position="top" @tab-click="">
          <el-tab-pane
            v-for="item in tabPlaneData"
            :key="item.purchaseOrderId"
            :label="item.purchaseOrderId + '    ' + item.factoryName"
            :name="item.purchaseOrderId"
            style="min-height: 500px"
          >
            <el-row :gutter="20">
              <el-col :span="12" :offset="0"
                ><span
                  >订单备注：
                  <el-input
                    v-model="item.unifiedRemark"
                    placeholder=""
                    type="textarea"
                    resize="none"
                    size="normal"
                    clearable
                    @change=""
                  ></el-input> </span
              ></el-col>
              <el-col :span="12" :offset="0">
                <span
                  >环境要求：
                  <el-input
                    v-model="item.environmentalRequirements"
                    placeholder=""
                    type="textarea"
                    resize="none"
                    size="normal"
                    clearable
                    @change=""
                  ></el-input>
                </span>
              </el-col>
            </el-row>
            <el-row :gutter="20">
              <el-col :span="12" :offset="0">
                <span
                  >发货地址：
                  <el-input
                    v-model="item.shippingAddress"
                    placeholder=""
                    type="textarea"
                    resize="none"
                    size="normal"
                    clearable
                    @change=""
                  ></el-input>
                </span>
              </el-col>
              <el-col :span="12" :offset="0">
                <span
                  >交货周期：
                  <el-input
                    v-model="item.leadTime"
                    placeholder=""
                    type="textarea"
                    resize="none"
                    size="normal"
                    clearable
                    @change=""
                  ></el-input>
                </span>
              </el-col>
            </el-row>
            <el-row :gutter="20" style="margin-top: 20px">
              <el-col :span="24" :offset="0">
                <div v-if="factoryFieldJudge(item.factoryField)">
                  <el-table :data="item.materialTableData" border style="width: 100%" height="500">
                  <el-table-column type="index" label="编号" />
                  <el-table-column prop="materialType" label="材料类型"></el-table-column>
                  <el-table-column prop="materialName" label="材料名称" />
                  <el-table-column prop="materialSpecification" label="材料规格"></el-table-column>
                  <el-table-column prop="unit" label="单位" />

                  <el-table-column prop="amount" label="采购数量" />
                  <el-table-column label="分码数量（中国/美标内码/美标外显）">
                    <el-table-column label="35" width="50">
                      <el-table-column label="7" width="50">
                        <el-table-column prop="size35" label="7" width="50"></el-table-column>
                      </el-table-column>
                    </el-table-column>
                    <el-table-column label="36" width="50">
                      <el-table-column label="7" width="50">
                        <el-table-column prop="size36" label="7.5" width="50"></el-table-column>
                      </el-table-column>
                    </el-table-column>
                    <el-table-column label="37" width="50">
                      <el-table-column label="8" width="50">
                        <el-table-column prop="size37" label="8" width="50"></el-table-column>
                      </el-table-column>
                    </el-table-column>
                    <el-table-column label="38" width="50">
                      <el-table-column label="8" width="50">
                        <el-table-column prop="size38" label="8.5" width="50"></el-table-column>
                      </el-table-column>
                    </el-table-column>
                    <el-table-column label="39" width="50">
                      <el-table-column label="9" width="50">
                        <el-table-column prop="size39" label="9" width="50"></el-table-column>
                      </el-table-column>
                    </el-table-column>
                    <el-table-column label="40" width="50">
                      <el-table-column label="9" width="50">
                        <el-table-column prop="size40" label="9.5" width="50"></el-table-column>
                      </el-table-column>
                    </el-table-column>
                    <el-table-column label="41" width="50">
                      <el-table-column label="10" width="50">
                        <el-table-column prop="size41" label="10" width="50"></el-table-column>
                      </el-table-column>
                    </el-table-column>
                    <el-table-column label="42" width="50">
                      <el-table-column label="10" width="50">
                        <el-table-column prop="size42" label="10.5" width="50"></el-table-column>
                      </el-table-column>
                    </el-table-column>
                    <el-table-column label="43" width="50">
                      <el-table-column label="11" width="50">
                        <el-table-column prop="size43" label="11" width="50"></el-table-column>
                      </el-table-column>
                    </el-table-column>
                    <el-table-column label="44" width="50">
                      <el-table-column label="12" width="50">
                        <el-table-column prop="size44" label="12" width="50"></el-table-column>
                      </el-table-column>
                    </el-table-column>
                    <el-table-column label="45" width="50">
                      <el-table-column label="13" width="50">
                        <el-table-column prop="size45" label="13" width="50"></el-table-column>
                      </el-table-column>
                    </el-table-column>
                  </el-table-column>
                  <el-table-column prop="comment" label="备注" />
                </el-table>
                </div>
                <div v-else>
                  <el-table :data="item.materialTableData" border stripe height="500">
                  <el-table-column type="index"></el-table-column>
                  <el-table-column prop="materialType" label="材料类型"></el-table-column>
                  <el-table-column prop="materialName" label="材料名称" />
                  <el-table-column prop="materialSpecification" label="材料规格"></el-table-column>
                  <el-table-column prop="unit" label="单位" />
                  <el-table-column prop="amount" label="数量" />
                  <el-table-column prop="comment" label="备注" />
                </el-table>
                </div>

              </el-col>
            </el-row>
          </el-tab-pane>
        </el-tabs>

        <template #footer>
          <span>
            <el-button @click="">取消</el-button>
            <el-button type="primary" @click="">保存</el-button>
            <el-button type="success" @click="">提交</el-button>
          </span>
        </template>
      </el-dialog>

      <!-- Main content -->
    </el-main>
  </el-container>
  <el-dialog title="尺码数量填写" v-model="isSizeDialogVisible" width="60%">
    <el-table :data="sizeData" border stripe>
      <el-table-column prop="size" label="尺码"></el-table-column>
      <el-table-column prop="USinnersize" label="内码美标尺码"></el-table-column>
      <el-table-column prop="USoutersize" label="外显美标尺码"></el-table-column>
      <el-table-column prop="usageAmount" label="BOM用量"></el-table-column>
      <el-table-column label="采购数量">
        <template #default="scope">
          <el-input-number v-model="scope.row.purchaseAmount" :min="0" size="small" />
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
</template>

<script>
import AllHeader from '@/components/AllHeader.vue'
import Arrow from '@/components/OrderArrowView.vue'
export default {
  props: ['orderId'],
  components: {
    AllHeader,
    Arrow
  },
  data() {
    return {
      activeTab: '',
      isPurchaseOrderVis: false,
      createVis: false,
      isSizeDialogVisible: false,
      sizeData: [],
      tabPlaneData: [
        {
          purchaseOrderId: '20240718155400PR1',
          factoryName: '一一鞋材',
          factoryField: '鞋面',
          unifiedRemark: '',
          shippingAddress: '',
          leadTime: '',
          environmentalRequirements: '',
          materialTableData: []
        },
        {
          purchaseOrderId: '20240718155400PR12',
          factoryName: '深博中底',
          factoryField: '中底',
          unifiedRemark: '',
          shippingAddress: '',
          leadTime: '',
          environmentalRequirements: '',
          materialTableData: []
        }
      ],
      testOrderData: {
        orderId: '123456',
        createTime: '2024-06-11',
        prevTime: '2024-06-11 12:00:00',
        prevDepart: '技术部',
        prevUser: 'XXX',
        orderrStatus: '未完成'
      },
      testTableData: [
        {
          bomId: 'K24021211162020240611180001',
          bomType: '二次采购BOM',
          bomLink: '0E20620,0E20621',
          Status: '未生成材料统计表'
        },
        {
          bomId: 'K24021211162020240611180002',
          bomType: '二次采购BOM',
          bomLink: '0E20620,0E20621',
          Status: '已生成材料统计表'
        },
        {
          bomId: 'K24021211162020240611180001',
          bomType: '二次采购BOM',
          bomLink: '0E20620,0E20621',
          Status: '已保存材料统计表'
        }
      ],
      bomTestData: [
        {
          partName: '鞋面',
          color: '黑色',
          materialType: '鞋面',
          materialName: '黑色超软镜面PU',
          unit: '米',
          unitUsage: 10.35,
          approvedUsage: 186,
          purchaseAmount: 0,
          factoryName: '',
          internalModel: '0E202620',
          customerModel: 'VRA-1020',
          comment: '',
          sizeStatus: '无尺码'
        },
        {
          partName: '中底',
          color: '白色',
          materialType: '中底',
          materialName: '蓝色底',
          unit: '米',
          unitUsage: null,
          approvedUsage: null,
          purchaseAmount: null,
          factoryName: '',
          internalModel: '0E202620',
          customerModel: 'VRA-1020',
          comment: '',
          department: '成型',
          sizeStatus: '已填写',
          sizeInfo: [
            {
              size: '35',
              usageAmount: 20,
              USinnersize: '7',
              USoutersize: '7',
              purchaseAmount: 0
            },
            {
              size: '36',
              usageAmount: 20,
              USinnersize: '7',
              USoutersize: '7.5',
              purchaseAmount: 0
            },
            {
              size: '37',
              usageAmount: 20,
              USinnersize: '8',
              USoutersize: '8',
              purchaseAmount: 0
            },
            {
              size: '38',
              usageAmount: 20,
              USinnersize: '8',
              USoutersize: '8.5',
              purchaseAmount: 0
            },
            {
              size: '39',
              usageAmount: 20,
              USinnersize: '9',
              USoutersize: '9',
              purchaseAmount: 0
            },
            {
              size: '40',
              usageAmount: 20,
              USinnersize: '9',
              USoutersize: '9.5',
              purchaseAmount: 0
            },
            {
              size: '41',
              usageAmount: 20,
              USinnersize: '10',
              USoutersize: '10',
              purchaseAmount: 0
            },
            {
              size: '42',
              usageAmount: 20,
              USinnersize: '10',
              USoutersize: '10.5',
              purchaseAmount: 0
            },
            {
              size: '43',
              usageAmount: 20,
              USinnersize: '11',
              USoutersize: '11',
              purchaseAmount: 0
            },
            {
              size: '44',
              usageAmount: 20,
              USinnersize: '12',
              USoutersize: '12',
              purchaseAmount: 0
            },
            {
              size: '45',
              usageAmount: 20,
              USinnersize: '13',
              USoutersize: '13',
              purchaseAmount: 0
            }
          ]
        },
        {
          partName: '鞋面',
          color: '蓝色',
          materialType: '鞋面',
          materialName: '蓝色超软镜面PU',
          unit: '米',
          unitUsage: 10.35,
          approvedUsage: 186,
          purchaseAmount: 0,
          factoryName: '',
          internalModel: '0E202620',
          customerModel: 'VRA-1020',
          comment: '',
          sizeStatus: '无尺码'
        }
      ],
      originalBomTestData: [],
      factoryOptions: [
        { materialName: '黑色超软镜面PU', factoryName: '一一鞋材' },
        { materialName: '黑色超软镜面PU', factoryName: '深源皮革' },
        { materialName: '黑色超软镜面PU', factoryName: '嘉泰皮革' }
        // Add more options here
      ],
      purchaseTestData: [
        {
          factoryName: '一一鞋材',
          factoryField: '鞋面',
          data: [
            {
              num: 1,
              materialName: '黑色超软镜面PU',
              unit: '米',
              unitUsage: 10.35,
              approvedUsage: 186,
              amount: '200',
              customerId: 'K24',
              internalModel: '0E202620',
              customerModel: 'VRA-1020',
              comment: ''
            },
            {
              num: 1,
              materialName: '白色超软镜面PU',
              unit: '米',
              amount: '250',
              customerId: 'K24',
              internalModel: '0E202620',
              customerModel: 'VRA-1020',
              comment: ''
            },
            {
              num: 1,
              materialName: '蓝色超软镜面PU',
              unit: '米',
              amount: '140',
              customerId: 'K24',
              internalModel: '0E202620',
              customerModel: 'VRA-1020',
              comment: ''
            }
          ]
        },
        {
          factoryName: '深博中底',
          factoryField: '中底',
          data: [
            {
              num: 1,
              materialName: '黑色超软镜面PU',
              unit: '米',
              amount: '200',
              customerId: 'K24',
              internalModel: '0E202620',
              customerModel: 'VRA-1020',
              comment: ''
            },
            {
              num: 1,
              materialName: '白色超软镜面PU',
              unit: '米',
              amount: '250',
              customerId: 'K24',
              internalModel: '0E202620',
              customerModel: 'VRA-1020',
              comment: ''
            },
            {
              num: 1,
              materialName: '蓝色超软镜面PU',
              unit: '米',
              amount: '140',
              customerId: 'K24',
              internalModel: '0E202620',
              customerModel: 'VRA-1020',
              comment: ''
            }
          ]
        },
        {
          factoryName: '嘉泰皮革',
          factoryField: '鞋面',
          data: [
            {
              num: 1,
              materialName: '黑色超软镜面PU',
              unit: '米',
              amount: '200',
              customerId: 'K24',
              internalModel: '0E202620',
              customerModel: 'VRA-1020',
              comment: ''
            },
            {
              num: 1,
              materialName: '白色超软镜面PU',
              unit: '米',
              amount: '250',
              customerId: 'K24',
              internalModel: '0E202620',
              customerModel: 'VRA-1020',
              comment: ''
            },
            {
              num: 1,
              materialName: '蓝色超软镜面PU',
              unit: '米',
              amount: '140',
              customerId: 'K24',
              internalModel: '0E202620',
              customerModel: 'VRA-1020',
              comment: ''
            }
          ]
        },
        {
          factoryName: '一一皮革',
          factoryField: '鞋面',
          data: [
            {
              num: 1,
              materialName: '黑色超软镜面PU',
              unit: '米',
              amount: '200',
              customerId: 'K24',
              internalModel: '0E202620',
              customerModel: 'VRA-1020',
              comment: ''
            },
            {
              num: 1,
              materialName: '白色超软镜面PU',
              unit: '米',
              amount: '250',
              customerId: 'K24',
              internalModel: '0E202620',
              customerModel: 'VRA-1020',
              comment: ''
            },
            {
              num: 1,
              materialName: '蓝色超软镜面PU',
              unit: '米',
              amount: '140',
              customerId: 'K24',
              internalModel: '0E202620',
              customerModel: 'VRA-1020',
              comment: ''
            }
          ]
        }
      ],
      isPreviewDialogVisible: false,
      selectedFile: null
    }
  },
  mounted() {
    this.activeTab = this.tabPlaneData[0].purchaseOrderId
  },
  methods: {
    factoryFieldJudge(field) {
      if (field.includes('中底') || field.includes('大底') || field.includes('鞋楦')) {
        return true
      }
      return false
    },
    openSizeDialog(row) {
      this.sizeData = row.sizeInfo
      this.isSizeDialogVisible = true
    },
    sizeDisabled(row, column) {
      if (column === 1) {
        return (
          row.materialType !== '大底' && row.materialType !== '中底' && row.materialType !== '楦头'
        )
      }
      return (
        row.materialType === '大底' || row.materialType === '中底' || row.materialType === '楦头'
      )
    },
    handleGenerate(row) {
      this.originalBomTestData = JSON.parse(JSON.stringify(this.bomTestData))
      this.createVis = true
    },
    handleGenerateClose() {
      this.bomTestData = JSON.parse(JSON.stringify(this.originalBomTestData)) // Restore original data
      this.createVis = false
    },
    getFilteredFactoryOptions(materialName) {
      const filteredOptions = this.factoryOptions.filter(
        (option) => option.materialName === materialName
      )
      return [{ factoryName: '询价' }, ...filteredOptions]
    },
    openPreviewDialog() {
      // Replace this with the actual logic to get the file
      this.isPreviewDialogVisible = true
    },
    closePreviewDialog() {
      this.isPreviewDialogVisible = false
    }
  }
}
</script>

<style scoped>
/* Add your styles here */
</style>
