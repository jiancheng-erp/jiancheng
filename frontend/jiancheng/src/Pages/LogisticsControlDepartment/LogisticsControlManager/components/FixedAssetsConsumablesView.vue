<template>
  <el-row :gutter="20">
    <el-col :span="24" :offset="0" style="font-size: xx-large; text-align: center"
      >固定资产/耗材采购订单生成</el-col
    >
  </el-row>
  <el-row :gutter="20" style="margin-top: 20px">
    <el-col :span="12" :offset="0"
      ><el-button-group>
        <el-button type="primary" size="default" @click="openCreateDialog"
          >新建耗材/固定资产采购订单</el-button
        >
        <el-button type="primary" size="default" @click="isLastPurchaseOrderDialogVisible = true"
          >创建楦头采购订单</el-button
        >
      </el-button-group>
    </el-col>
    <el-col :span="4" :offset="8"
      ><el-button type="warning" size="large" @click="openUnsubmitDialog"
        >待提交订单 {{ finishedNum }}</el-button
      >
    </el-col>
  </el-row>
  <el-row :gutter="20" style="margin-top: 20px">
    <el-col :span="6" :offset="0">
      <div style="display: flex; align-items: center; white-space: nowrap">
        订单编号查询：<el-input
          v-model="orderSearch"
          placeholder=""
          size="default"
          :suffix-icon="Search"
          clearable
          @input="tableWholeFilter"
        ></el-input>
      </div>
    </el-col>
    <el-col :span="6" :offset="0">
      <div style="display: flex; align-items: center; white-space: nowrap">
        耗材类型查询：<el-input
          v-model="assetsTypeSearch"
          placeholder=""
          size="default"
          :suffix-icon="Search"
          clearable
          @input="tableWholeFilter"
        ></el-input>
      </div>
    </el-col>
    <el-col :span="6" :offset="0">
      <div style="display: flex; align-items: center; white-space: nowrap">
        采购类型查询：
        <el-select
          v-model="isPurchaseOrderFilter"
          value-key=""
          placeholder=""
          clearable
          filterable
          @change="tableWholeFilter"
        >
          <el-option
            v-for="item in isPurchaseOrderOptions"
            :key="item.value"
            :label="item.label"
            :value="item.value"
          >
          </el-option>
        </el-select>
      </div>
    </el-col>
  </el-row>

  <el-row :gutter="20" style="margin-top: 20px">
    <el-col :span="24" :offset="0">
      <el-table
        :data="materialPurchaseFilterData"
        border
        style="height: 600px"
        ref="singleSelectTable"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="55"></el-table-column>
        <el-table-column prop="purchaseId" label="采购订单编号"></el-table-column>
        <el-table-column prop="purchaseCreateDate" label="采购下发日期"></el-table-column>
        <el-table-column prop="purchaseType" label="采购物品类型"></el-table-column>
        <el-table-column prop="isPurchaseOrder" label="随订单采购/独立采购"></el-table-column>
        <el-table-column prop="purchaseOrderId" label="订单编号"></el-table-column>
        <el-table-column label="操作">
          <template #default="scope">
            <el-button type="primary" @click="openPreviewDialog(scope.row)">查看</el-button>
          </template></el-table-column
        >
      </el-table>
    </el-col>
  </el-row>
  <!--未提交订单对话框-->
  <el-dialog title="未提交订单一览" v-model="unsubmitVis" width="90%">
    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="24" :offset="0">
        <el-table :data="materialPurchaseFilterData" border style="height: 600px">
          <el-table-column prop="purchaseId" label="采购订单编号"></el-table-column>
          <el-table-column
            prop="purchaseCreateDate"
            label="采购下发日期"
            width="120%"
          ></el-table-column>
          <el-table-column prop="purchaseType" label="采购物品类型"></el-table-column>
          <el-table-column prop="isPurchaseOrder" label="随订单采购/独立采购"></el-table-column>
          <el-table-column prop="purchaseOrderId" label="订单编号"></el-table-column>
          <el-table-column label="操作">
            <template #default="scope">
              <el-button type="primary" @click="openPreviewDialog(scope.row)">查看</el-button>
              <el-button type="primary" @click="openEditDialog(scope.row)">编辑</el-button>
              <el-button type="success" @click="isPurchaseOrderVis = true">下发</el-button>
              <el-button
                type="danger"
                @click="deleteCurrentRow(scope.$index, materialPurchaseFilterData)"
                >删除</el-button
              >
            </template></el-table-column
          >
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

  <!--创建新采购订单/过往订单创建-->
  <el-dialog
    title="耗材/固定资产采购订单 K2402121116202024061101F"
    v-model="createVis"
    width="95%"
    @close="handleGenerateClose"
  >
    <el-table :data="newAssetPurchaseData" border>
      <el-table-column prop="materialType" label="材料类型" />
      <el-table-column prop="materialName" label="材料名称" />
      <el-table-column label="材料规格">
        <template #default="scope">
          <el-input
            v-model="scope.row.materialSpecification"
            placeholder=""
            size="default"
            clearable
          ></el-input>
        </template>
      </el-table-column>
      <el-table-column prop="warehouseType" label="所属仓库" />
      <el-table-column prop="unit" label="单位" />
      <el-table-column label="采购数量">
        <template #default="scope">
          <el-input-number v-model="scope.row.purchaseAmount" :min="0" size="small" />
        </template>
      </el-table-column>
      <el-table-column prop="factoryName" label="工厂名称"> </el-table-column>
      <el-table-column label="随订单采购/独立采购">
        <template #default="scope">
          <el-select v-model="scope.row.isPurchaseOrder" placeholder="" filterable>
            <el-option
              v-for="item in isPurchaseOrderOptions"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            >
            </el-option>
          </el-select>
        </template>
      </el-table-column>
      <el-table-column label="订单编号">
        <template #default="scope">
          <el-input
            v-model="scope.row.purchaseOrderId"
            placeholder=""
            size="default"
            clearable
            :disabled="scope.row.isPurchaseOrder === '独立采购'"
          ></el-input>
        </template>
      </el-table-column>
      <el-table-column label="备注">
        <template #default="scope">
          <el-input v-model="scope.row.comment" placeholder="" size="default" clearable></el-input>
        </template>
      </el-table-column>
      <el-table-column label="操作">
        <template #default="scope">
          <el-button type="danger" @click="deleteCurrentRow(scope.$index, newAssetPurchaseData)"
            >删除</el-button
          >
        </template>
      </el-table-column>
    </el-table>
    <el-button type="primary" size="default" @click="openNewMaterialDialog">添加新材料</el-button>

    <template #footer>
      <span>
        <el-button @click="handleGenerateClose">取消</el-button>
        <el-button type="primary" @click="">保存</el-button>
      </span>
    </template>
  </el-dialog>
  <!--采购材料对话框-->
  <el-dialog title="添加新采购材料" v-model="newMaterialVis" width="60%">
    <el-row :gutter="20">
      <el-col :span="6" :offset="0">
        <div style="display: flex; align-items: center; white-space: nowrap">
          材料类型查询：<el-input
            v-model="materialTypeSearch"
            placeholder=""
            size="default"
            :suffix-icon="Search"
            clearable
            @input="materialTableWholeFilter"
          ></el-input>
        </div>
      </el-col>
      <el-col :span="6" :offset="0">
        <div style="display: flex; align-items: center; white-space: nowrap">
          材料名称查询：<el-input
            v-model="materialSearch"
            placeholder=""
            size="default"
            :suffix-icon="Search"
            clearable
            @input="materialTableWholeFilter"
          ></el-input>
        </div>
      </el-col>
      <el-col :span="6" :offset="0">
        <div style="display: flex; align-items: center; white-space: nowrap">
          工厂名查询：<el-input
            v-model="factorySearch"
            placeholder=""
            size="default"
            :suffix-icon="Search"
            clearable
            @input="materialTableWholeFilter"
          ></el-input>
        </div>
      </el-col>
    </el-row>
    <el-table
      :data="assetFilterTable"
      border
      ref="materialSelectTable"
      @selection-change="handleMaterialSelectionChange"
      style="max-height: 400px"
    >
      <el-table-column type="selection" width="55"></el-table-column>
      <el-table-column prop="materialType" label="材料类型" />
      <el-table-column prop="materialName" label="材料名称" />
      <el-table-column prop="warehouseName" label="所属仓库" />
      <el-table-column prop="unit" label="单位" />
      <el-table-column prop="factoryName" label="工厂名称" />
    </el-table>

    <template #footer>
      <span>
        <el-button @click="handleGenerateClose">取消</el-button>
        <el-button type="primary" @click="confirmNewMaterialAdd">保存</el-button>
      </span>
    </template>
  </el-dialog>
  <!--采购订单预览-->
  <el-dialog
    title="耗材/固定资产采购订单 K2402121116202024061101F 预览"
    v-model="purchaseOrderVis"
    width="90%"
  >
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
        <el-button @click="">Cancel</el-button>
        <el-button type="primary" @click="">OK</el-button>
      </span>
    </template>
  </el-dialog>
  <el-dialog
    title="创建楦头采购订单 K2402121116202024061101F"
    v-model="isLastPurchaseOrderDialogVisible"
    width="80%"
  >
    <el-table :data="lastData" border stripe>
      <el-table-column prop="materialType" label="材料类型" />
      <el-table-column prop="materialName" label="材料名称" />
      <el-table-column prop="materialSpecification" label="材料规格">
        <template #default="scope">
          <el-input
            v-model="scope.row.materialSpecification"
            placeholder=""
            size="default"
            clearable
          ></el-input>
        </template>
      </el-table-column>
      <el-table-column prop="warehouseType" label="所属仓库" />
      <el-table-column prop="unit" label="单位" />
      <el-table-column label="工厂名称">
        <template #default="scope">
          <el-select v-model="scope.row.factoryName" placeholder="" filterable>
            <el-option
              v-for="item in factoryOptions"
              :key="item.factoryName"
              :label="item.factoryName"
              :value="item.factoryName"
            >
            </el-option>
          </el-select>
        </template>
      </el-table-column>
      <el-table-column label="型号填写">
        <template #default="scope">
          {{ scope.row.sizeStatus }}
          <el-button type="primary" size="default" @click="openSizeDialog(scope.row)">尺码信息</el-button>
        </template>
      </el-table-column>
      <el-table-column label="备注">
        <template #default="scope">
          <el-input v-model="scope.row.comment" placeholder="" size="default" clearable></el-input>
        </template>
      </el-table-column>
      <el-table-column label="操作">
        <template #default="scope">
          <el-button type="danger" @click="deleteCurrentRow(scope.$index, newAssetPurchaseData)"
            >删除</el-button
          >
        </template>
      </el-table-column>
    </el-table>
    <el-button type="primary" size="default" @click="addLastMaterial">添加新材料</el-button>
    <template #footer>
      <span>
        <el-button @click="">Cancel</el-button>
        <el-button type="primary" @click="">OK</el-button>
      </span>
    </template>
  </el-dialog>
  <el-dialog title="尺码数量填写" v-model="isSizeDialogVisible" width="60%">
    <el-table :data="sizeData" border stripe>
      <el-table-column prop="size" label="尺码"></el-table-column>
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
</template>
<script>
import { Search } from '@element-plus/icons-vue'
import { markRaw } from 'vue'
import { ElMessageBox } from 'element-plus'
export default {
  data() {
    return {
        activeTab: '',
        isPurchaseOrderVis: false,
      isSizeDialogVisible: false,
      isLastPurchaseOrderDialogVisible: false,
      sizeData: [],
      lastData: [
        {
          materialType: '楦头',
          materialName: '楦头',
          materialSpecification: '',
          warehouseType: '楦头库',
          unit: '个',
          factoryName: '询价',
          sizeStatus: '未填写',
          comment: '',
          sizeInfo: [
            {
              size: '35',
              purchaseAmount: 0
            },
            {
              size: '36',
              purchaseAmount: 0
            },
            {
              size: '37',
              purchaseAmount: 0
            },
            {
              size: '38',
              purchaseAmount: 0
            },
            {
              size: '39',
              purchaseAmount: 0
            },
            {
              size: '40',
              purchaseAmount: 0
            },
            {
              size: '41',
              purchaseAmount: 0
            },
            {
              size: '42',
              purchaseAmount: 0
            },
            {
              size: '43',
              purchaseAmount: 0
            },
            {
              size: '44',
              purchaseAmount: 0
            },
            {
              size: '45',
              purchaseAmount: 0
            }
          ]
        }
      ],
      finishedNum: 1,
      materialSearch: '',
      materialTypeSearch: '',
      factorySearch: '',
      unsubmitVis: false,
      createVis: false,
      newMaterialVis: false,
      purchaseOrderVis: false,
      orderSearch: '',
      assetsTypeSearch: '',
      isPurchaseOrderFilter: '',
      addAssetName: '',
      isPurchaseOrderOptions: [
        { value: '随订单采购', label: '随订单采购' },
        { value: '独立采购', label: '独立采购' }
      ],
      assetTable: [
        { materialName: '胶水', warehouseName: '化工库', unit: '桶', factoryName: '询价' },
        { materialName: '染料', warehouseName: '化工库', unit: '桶', factoryName: '询价' },
        { materialName: '森达G8C307新', warehouseName: '楦头库', unit: '个', factoryName: '森达' },
        { materialName: '森达E69138', warehouseName: '楦头库', unit: '个', factoryName: '森达' }
      ],
      assetFilterTable: [],
      Search: markRaw(Search),
      materialPurchaseTestData: [
        {
          purchaseId: 'K2402121116202024061101A',
          purchaseCreateDate: '2024-06-12',
          purchaseType: '化工类, 工具类',
          isPurchaseOrder: '随订单采购',
          purchaseOrderId: 'W24-01-2111620'
        },
        {
          purchaseId: 'K2402121116202024061102A',
          purchaseCreateDate: '2024-06-12',
          purchaseType: '化工类, 工具类',
          isPurchaseOrder: '随订单采购',
          purchaseOrderId: 'W24-01-2111620'
        }
      ],
      materialPurchaseFilterData: [],
      selectedRow: null,
      materialSelectRow: null,
      newAssetPurchaseData: [],
      factoryOptions: [
        { materialName: '黑色超软镜面PU', factoryName: '一一鞋材' },
        { materialName: '黑色超软镜面PU', factoryName: '深源皮革' },
        { materialName: '黑色超软镜面PU', factoryName: '嘉泰皮革' }
        // Add more options here
      ],
      purchaseTestData: [
        {
          factoryName: '询价',
          factoryField: '',
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
          factoryName: '深源鞋楦',
          factoryField: '鞋楦',
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
          factoryField: '面料',
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
          factoryField: '面料',
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
    }
  },
  mounted() {
    this.materialPurchaseFilterData = this.materialPurchaseTestData
    this.activeTab = this.tabPlaneData[0].purchaseOrderId
  },
  methods: {
    factoryFieldJudge(field) {
      if (field.includes('中底') || field.includes('大底') || field.includes('鞋楦')) {
        return true
      }
      return false
    },
    addLastMaterial() {
        this.lastData.push({
            materialType: '楦头',
            materialName: '楦头',
            materialSpecification: '',
            warehouseType: '楦头库',
            unit: '个',
            factoryName: '询价',
            sizeStatus: '未填写',
            comment: '',
            sizeInfo: [
            {
                size: '35',
                purchaseAmount: 0
            },
            {
                size: '36',
                purchaseAmount: 0
            },
            {
                size: '37',
                purchaseAmount: 0
            },
            {
                size: '38',
                purchaseAmount: 0
            },
            {
                size: '39',
                purchaseAmount: 0
            },
            {
                size: '40',
                purchaseAmount: 0
            },
            {
                size: '41',
                purchaseAmount: 0
            },
            {
                size: '42',
                purchaseAmount: 0
            },
            {
                size: '43',
                purchaseAmount: 0
            },
            {
                size: '44',
                purchaseAmount: 0
            },
            {
                size: '45',
                purchaseAmount: 0
            }
            ]
        })
    },
    openSizeDialog(row) {
      this.sizeData = row.sizeInfo
      this.isSizeDialogVisible = true
    },
    handleSelectionChange(selection) {
      if (selection.length > 1) {
        // Ensure only one row is selected
        this.$refs.singleSelectTable.clearSelection()
        this.$refs.singleSelectTable.toggleRowSelection(selection[selection.length - 1], true)
      } else {
        this.selectedRow = selection[0]
      }
      console.log(this.selectedRow)
    },
    handleMaterialSelectionChange(selection) {
      if (selection.length > 1) {
        // Ensure only one row is selected
        this.$refs.materialSelectTable.clearSelection()
        this.$refs.materialSelectTable.toggleRowSelection(selection[selection.length - 1], true)
      } else {
        this.materialSelectRow = selection[0]
      }
      console.log(this.materialSelectRow)
    },
    tableWholeFilter() {
      if (!this.orderSearch && !this.assetsTypeSearch && !this.isPurchaseOrderFilter) {
        this.materialPurchaseFilterData = this.materialPurchaseTestData
        return
      }

      this.materialPurchaseFilterData = this.materialPurchaseTestData.filter((task) => {
        const orderMatch = task.purchaseOrderId.includes(this.orderSearch)
        const typeMatch = task.purchaseType.includes(this.assetsTypeSearch)
        const purchaseOrderMatch =
          this.isPurchaseOrderFilter === '' ||
          task.isPurchaseOrder.includes(this.isPurchaseOrderFilter)

        return orderMatch && typeMatch && purchaseOrderMatch
      })
    },
    openUnsubmitDialog() {
      this.unsubmitVis = true
    },
    openCreateDialog() {
      this.createVis = true
    },
    openNewMaterialDialog() {
      this.newMaterialVis = true
      this.assetFilterTable = this.assetTable
    },
    openPreviewDialog() {
      this.purchaseOrderVis = true
    },
    confirmNewMaterialAdd() {
      if (this.materialSelectRow === null) {
        ElMessageBox.alert('材料不能为空！', '警告', { confirmButtonText: '确认' })
        return
      }

      this.newAssetPurchaseData.push({
        materialName: this.materialSelectRow.materialName,
        warehouseType: this.materialSelectRow.warehouseName,
        unit: this.materialSelectRow.unit,
        purchaseAmount: 0,
        factoryName: this.materialSelectRow.factoryName,
        isPurchaseOrder: '独立采购',
        purchaseOrderId: '',
        comment: ''
      })
      this.addAssetName = ''
      this.newMaterialVis = false
    },
    getFilteredFactoryOptions(materialName) {
      const filteredOptions = this.factoryOptions.filter(
        (option) => option.materialName === materialName
      )
      return [{ factoryName: '询价' }, ...filteredOptions]
    },
    materialTableWholeFilter() {
      if (!this.materialSearch && !this.factorySearch) {
        this.assetFilterTable = this.assetTable
        return
      }

      this.assetFilterTable = this.assetTable.filter((task) => {
        const materialMatch = task.materialName.includes(this.materialSearch)
        const factoryMatch = task.factoryName.includes(this.factorySearch)
        const materialTypeMatch = task.materialType.includes(this.materialTypeSearch)
        return materialMatch && factoryMatch && materialTypeMatch
      })
    },
    deleteCurrentRow(index, datafield) {
      this.$confirm('确定删除此行吗？', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      })
        .then(() => {
          datafield.splice(index, 1)
          this.$message({
            type: 'success',
            message: '删除成功!'
          })
        })
        .catch(() => {
          this.$message({
            type: 'info',
            message: '已取消删除'
          })
        })
    }
  }
}
</script>
