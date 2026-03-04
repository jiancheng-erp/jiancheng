<template>
  <el-row :gutter="20">
    <el-col :span="24" style="font-size: xx-large; text-align: center">预报单管理</el-col>
  </el-row>

  <el-row :gutter="12" style="margin-top: 16px">
    <el-col :span="24">
      <el-button type="primary" @click="openCreateDialog">创建预报单</el-button>
      <el-button style="margin-left: 8px" @click="loadForecastSheets">刷新</el-button>
    </el-col>
  </el-row>

  <el-row :gutter="12" style="margin-top: 12px">
    <el-col :span="5">
      <el-input v-model="sheetFilters.forecastRid" clearable placeholder="预报单号筛选" />
    </el-col>
    <el-col :span="5">
      <el-input v-model="sheetFilters.forecastCid" clearable placeholder="客户预报号筛选" />
    </el-col>
    <el-col :span="4">
      <el-input v-model="sheetFilters.customerName" clearable placeholder="客户筛选" />
    </el-col>
    <el-col :span="4">
      <el-input v-model="sheetFilters.customerBrand" clearable placeholder="商标筛选" />
    </el-col>
    <el-col :span="3">
      <el-select v-model="sheetFilters.status" clearable placeholder="状态">
        <el-option label="草稿" :value="0" />
        <el-option label="已下发" :value="1" />
      </el-select>
    </el-col>
    <el-col :span="3" style="text-align: right">
      <el-button @click="resetSheetFilters">重置</el-button>
    </el-col>
  </el-row>

  <el-row :gutter="20" style="margin-top: 16px">
    <el-col :span="24">
      <el-table :data="paginatedForecastSheets" border stripe style="height: 56vh" row-key="forecastSheetId">
        <el-table-column prop="forecastRid" label="预报单号" min-width="180" />
        <el-table-column prop="forecastCid" label="客户预报号" min-width="140" />
        <el-table-column prop="customerName" label="客户" min-width="120" />
        <el-table-column prop="customerBrand" label="商标" min-width="120" />
        <el-table-column label="包装资料" width="110">
          <template #default="scope">
            <el-tag :type="scope.row.packagingUploaded ? 'success' : 'danger'">
              {{ scope.row.packagingUploaded ? '已上传' : '未上传' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="statusText" label="状态" width="100" />
        <el-table-column label="操作" width="700">
          <template #default="scope">
            <div class="forecast-op-wrap">
              <el-button size="small" type="primary" @click="openPreviewDialog(scope.row)">预览</el-button>
              <!-- <el-button size="small" @click="showItems(scope.row)">查看鞋型</el-button> -->
              <el-button
                size="small"
                :disabled="Number(scope.row.status) !== 0"
                @click="openEditDialog(scope.row)"
              >编辑预报单</el-button>
              <el-button
                size="small"
                :disabled="Number(scope.row.status) !== 0"
                @click="openSheetPackagingDialog(scope.row)"
              >编辑配码</el-button>
              <el-dropdown @command="(command) => downloadForecastExcel(scope.row, command)">
                <el-button size="small">下载Excel</el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item :command="0">配码预报单</el-dropdown-item>
                    <el-dropdown-item :command="1">数量预报单</el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
              <el-button
                size="small"
                type="primary"
                :disabled="Number(scope.row.status) !== 0"
                @click="openPackagingUploadDialog(scope.row)"
              >上传包装资料</el-button>
              <el-button
                size="small"
                type="warning"
                :disabled="Number(scope.row.status) !== 0"
                @click="openDispatchDialog(scope.row)"
              >下发拆单</el-button>
              <el-button
                size="small"
                type="danger"
                :disabled="Number(scope.row.status) !== 0"
                @click="deleteForecastSheet(scope.row)"
              >删除预报单</el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
      <el-pagination
        style="margin-top: 10px; justify-content: flex-end"
        layout="total, prev, pager, next"
        :current-page="forecastSheetPage"
        :page-size="forecastSheetPageSize"
        :total="filteredForecastSheets.length"
        @current-change="handleForecastSheetPageChange"
      />
    </el-col>
  </el-row>

  <el-dialog v-model="createDialogVisible" :title="isEditMode ? '编辑预报单' : '创建预报单'" width="88%" :close-on-click-modal="false">
    <el-form :model="createForm" label-width="130px">
      <el-row :gutter="12">
        <el-col :span="8">
          <el-form-item label="预报单号">
            <el-input v-model="createForm.forecastRid" placeholder="可空，后台自动生成" />
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="客户预报号">
            <el-input v-model="createForm.forecastCid" />
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="业务员">
            <el-input v-model="createForm.salesmanName" disabled />
          </el-form-item>
        </el-col>
      </el-row>

      <el-row :gutter="12">
        <el-col :span="8">
          <el-form-item label="客户" required>
            <el-select v-model="createForm.customerId" filterable placeholder="请选择" @change="handleCustomerChange">
              <el-option
                v-for="item in customerOptions"
                :key="item.customerId"
                :label="`${item.customerName} - ${item.customerBrand}`"
                :value="item.customerId"
              />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="配码种类" required>
            <el-select v-model="createForm.batchInfoTypeId" filterable placeholder="请选择" @change="handleBatchTypeChange">
              <el-option
                v-for="item in batchTypeOptions"
                :key="item.batchInfoTypeId"
                :label="item.batchInfoTypeName"
                :value="item.batchInfoTypeId"
              />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="审批经理" required>
            <el-select v-model="createForm.supervisorId" filterable placeholder="请选择">
              <el-option
                v-for="item in managerOptions"
                :key="item.staffId"
                :label="item.staffName"
                :value="item.staffId"
              />
            </el-select>
          </el-form-item>
        </el-col>
      </el-row>

      <el-row :gutter="12">
        <el-col :span="8">
          <el-form-item label="货币类型" required>
            <el-select v-model="createForm.currencyType" placeholder="请选择货币类型">
              <el-option
                v-for="item in currencyTypeOptions"
                :key="item"
                :label="item"
                :value="item"
              />
            </el-select>
          </el-form-item>
        </el-col>
      </el-row>

      <el-divider content-position="left">鞋型明细</el-divider>
      <el-row :gutter="10" style="margin-bottom: 10px">
        <el-col :span="24">
          <el-button type="primary" plain @click="openShoeSelectorDialog">批量选择鞋型</el-button>
          <el-button style="margin-left: 8px" @click="addItemRow">手动新增一行</el-button>
        </el-col>
      </el-row>

      <el-table :data="paginatedCreateItems" border style="margin-top: 12px" row-key="uid" height="42vh">
        <el-table-column label="鞋图" width="120">
          <template #default="scope">
            <el-image
              v-if="scope.row.shoeImageUrl"
              :src="scope.row.shoeImageUrl"
              style="width: 96px; height: 64px"
              fit="cover"
            />
          </template>
        </el-table-column>
        <el-table-column label="鞋型" min-width="240">
          <template #default="scope">
            <el-select
              v-model="scope.row.shoeTypeId"
              remote
              filterable
              clearable
              :remote-method="queryManualShoeType"
              :loading="manualShoeTypeLoading"
              placeholder="选择鞋型+颜色"
              style="width: 100%"
              @change="(val) => handleShoeTypeChange(scope.row, val)"
            >
              <el-option
                v-for="item in allShoeTypeOptions"
                :key="item.shoeTypeId"
                :label="`${item.shoeRid} - ${item.colorName}`"
                :value="item.shoeTypeId"
              />
            </el-select>
          </template>
        </el-table-column>
        <el-table-column label="客户型号" min-width="160">
          <template #default="scope">
            <el-input
              v-model="scope.row.customerShoeName"
              @input="(val) => handleCustomerShoeNameInput(scope.row, val)"
            />
          </template>
        </el-table-column>
        <el-table-column label="客户颜色" min-width="140">
          <template #default="scope">
            <el-input v-model="scope.row.customerColorName" />
          </template>
        </el-table-column>
        <el-table-column label="配码" min-width="220">
          <template #default="scope">
            <el-text>{{ scope.row.packagingInfoName || '创建后在主页面“编辑配码”设置' }}</el-text>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="90">
          <template #default="scope">
            <el-button type="danger" link @click="removeItemRowByUid(scope.row.uid)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-pagination
        style="margin-top: 10px; justify-content: flex-end"
        layout="total, prev, pager, next"
        :current-page="createItemPage"
        :page-size="createItemPageSize"
        :total="createItems.length"
        @current-change="handleCreateItemPageChange"
      />
    </el-form>

    <template #footer>
      <el-button @click="createDialogVisible = false">取消</el-button>
      <el-button type="primary" :loading="createSubmitting" @click="submitCreate">{{ isEditMode ? '保存修改' : '保存' }}</el-button>
    </template>
  </el-dialog>

  <el-dialog v-model="itemDialogVisible" title="预报单鞋型" width="72%">
    <el-table :data="paginatedCurrentItems" border style="max-height: 52vh">
      <el-table-column prop="shoeRid" label="鞋型" min-width="130" />
      <el-table-column prop="colorName" label="颜色" min-width="100" />
      <el-table-column prop="customerShoeName" label="客户型号" min-width="130" />
      <el-table-column prop="customerColorName" label="客户颜色" min-width="130" />
      <el-table-column prop="packagingInfoName" label="配码" min-width="140" />
      <el-table-column prop="unitPrice" label="单价" width="100" />
      <el-table-column prop="totalPairs" label="总双数" width="100" />
    </el-table>
    <el-pagination
      style="margin-top: 10px; justify-content: flex-end"
      layout="total, prev, pager, next"
      :current-page="itemDialogPage"
      :page-size="itemDialogPageSize"
      :total="currentItems.length"
      @current-change="handleItemDialogPageChange"
    />
  </el-dialog>

  <el-dialog v-model="sheetItemsDialogVisible" title="编辑预报单鞋型配码" width="90%" :close-on-click-modal="false">
    <el-table :data="paginatedSheetPackagingItems" border style="height: 50vh">
      <el-table-column prop="shoeRid" label="鞋型" min-width="120" />
      <el-table-column prop="colorName" label="颜色" min-width="80" />
      <el-table-column prop="packagingInfoName" label="配码" min-width="260" />
      <el-table-column label="单价" width="160">
        <template #default="scope">
          <el-input-number
            v-model="scope.row.unitPrice"
            :min="0"
            :step="0.01"
            :precision="4"
            size="small"
            style="width: 130px"
          />
        </template>
      </el-table-column>
      <el-table-column label="各配码总数量" min-width="300">
        <template #default="scope">
          <el-text>{{ formatRowPackagingTotals(scope.row) }}</el-text>
        </template>
      </el-table-column>
      <el-table-column label="各配码总金额" min-width="300">
        <template #default="scope">
          <el-text>{{ formatRowPackagingAmounts(scope.row) }}</el-text>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="240">
        <template #default="scope">
          <el-button type="success" size="small" @click="openRowQuantityDialog(scope.row)">修改单位数量</el-button>
          <el-button type="primary" size="small" @click="openForecastBatchInfoDialog(scope.row)">编辑配码</el-button>
          <el-button type="warning" size="small" style="margin-left: 8px" @click="openForecastLoadBatchTemplateDialog(scope.row)">加载模板</el-button>
        </template>
      </el-table-column>
      <el-table-column prop="computedTotalPairs" label="总数量" width="80" />
      <el-table-column label="总金额" width="130">
        <template #default="scope">
          <el-text>{{ formatCurrency(getRowTotalAmount(scope.row)) }}</el-text>
        </template>
      </el-table-column>
    </el-table>
    <el-pagination
      style="margin-top: 10px; justify-content: flex-end"
      layout="total, prev, pager, next"
      :current-page="sheetPackagingPage"
      :page-size="sheetPackagingPageSize"
      :total="sheetPackagingItems.length"
      @current-change="handleSheetPackagingPageChange"
    />
    <template #footer>
      <el-button @click="sheetItemsDialogVisible = false">取消</el-button>
      <el-button type="primary" :loading="sheetPackagingSubmitting" @click="saveSheetPackaging">保存配码</el-button>
    </template>
  </el-dialog>

  <el-dialog v-model="previewDialogVisible" title="预报单预览" width="80%">
    <el-descriptions :column="3" border>
      <el-descriptions-item label="预报单号">{{ previewTarget?.forecastRid || '-' }}</el-descriptions-item>
      <el-descriptions-item label="客户预报号">{{ previewTarget?.forecastCid || '-' }}</el-descriptions-item>
      <el-descriptions-item label="状态">{{ previewTarget?.statusText || '-' }}</el-descriptions-item>
      <el-descriptions-item label="客户">{{ previewTarget?.customerName || '-' }}</el-descriptions-item>
      <el-descriptions-item label="商标">{{ previewTarget?.customerBrand || '-' }}</el-descriptions-item>
      <el-descriptions-item label="日期">{{ `${previewTarget?.startDate || '-'} 至 ${previewTarget?.endDate || '-'}` }}</el-descriptions-item>
    </el-descriptions>
    <el-table :data="paginatedPreviewItems" border style="margin-top: 12px; max-height: 50vh">
      <el-table-column prop="shoeRid" label="鞋型" min-width="130" />
      <el-table-column prop="colorName" label="颜色" min-width="110" />
      <el-table-column prop="customerShoeName" label="客户型号" min-width="130" />
      <el-table-column prop="customerColorName" label="客户颜色" min-width="130" />
      <el-table-column prop="packagingInfoName" label="配码" min-width="150" />
      <el-table-column label="总数量" width="110">
        <template #default="scope">
          <el-text>{{ Number(scope.row?.computedTotalPairs ?? scope.row?.totalPairs ?? 0) }}</el-text>
        </template>
      </el-table-column>
      <el-table-column prop="unitPrice" label="单价" width="110" />
      <el-table-column label="总金额" width="120">
        <template #default="scope">
          <el-text>{{ formatCurrency(getRowTotalAmount(scope.row)) }}</el-text>
        </template>
      </el-table-column>
    </el-table>
    <el-pagination
      style="margin-top: 10px; justify-content: flex-end"
      layout="total, prev, pager, next"
      :current-page="previewPage"
      :page-size="previewPageSize"
      :total="previewItems.length"
      @current-change="handlePreviewPageChange"
    />
  </el-dialog>

  <el-dialog v-model="rowQuantityDialogVisible" title="修改单位数量" width="560px" :close-on-click-modal="false">
    <el-table :data="paginatedRowQuantityEditingRows" border style="max-height: 320px">
      <el-table-column prop="packagingInfoName" label="配码" min-width="220" />
      <el-table-column label="单位数量" min-width="180">
        <template #default="scope">
          <el-input-number
            v-model="rowQuantityForm[scope.row.key]"
            :min="1"
            :step="1"
            size="small"
            style="width:140px"
          />
        </template>
      </el-table-column>
    </el-table>
    <el-pagination
      style="margin-top: 10px; justify-content: flex-end"
      layout="total, prev, pager, next"
      :current-page="rowQuantityPage"
      :page-size="rowQuantityPageSize"
      :total="rowQuantityEditingRows.length"
      @current-change="handleRowQuantityPageChange"
    />
    <template #footer>
      <el-button @click="rowQuantityDialogVisible = false">取消</el-button>
      <el-button type="primary" @click="applyRowQuantityUpdate">保存</el-button>
    </template>
  </el-dialog>

  <AddBatchInfoDialog
    ref="forecastBatchInfoDialog"
    v-model:batchNameFilter="batchNameFilter"
    :new-order-form="sheetBatchDialogForm"
    :customer-display-batch-data="customerDisplayBatchData"
    :selected-batch-data="currentBatch"
    :attr-mapping="attrMapping"
    :cur-batch-type="curBatchType"
    @selection-change="handleSelectionBatchData"
    @close="closeForecastBatchInfoDialog"
    @open-add-customer-batch="openForecastAddCustomerBatchDialog"
    @open-add-color="openForecastAddColorDialog"
    @open-save-template="openForecastSaveTemplateDialog"
    @save-batch="applyForecastBatchToItem"
    @filter-with-selection="filterBatchDataWithSelection"
  />

  <AddCustomerBatchDialog
    v-model:batchForm="batchForm"
    :attr-mapping="attrMapping"
    :cur-batch-type="curBatchType"
    @close="dialogStore.closeCustomerBatchDialog()"
    @submit="submitForecastAddCustomerBatchForm"
  />

  <CustomerBatchTemplateDialog
    :batch-template-display-data="batchTemplateDisplayData"
    :attr-mapping="attrMapping"
    :cur-batch-type="curBatchType"
    @selection-change="handleSelectionBatchTemplate"
    @delete-template="deleteForecastBatchTemplateDialog"
    @confirm-load="confirmForecastLoadBatchTemplate"
    @close="dialogStore.closeBatchTemplateDialog()"
  />

  <el-dialog v-model="shoeSelectorDialogVisible" title="批量选择鞋型" width="90%" :close-on-click-modal="false">
    <el-row :gutter="12">
      <el-col :span="6">
        <el-input v-model="shoeSelectorFilters.shoeRid" clearable placeholder="工厂型号筛选" />
      </el-col>
      <el-col :span="6">
        <el-input v-model="shoeSelectorFilters.colorName" clearable placeholder="颜色筛选" />
      </el-col>
      <el-col :span="6"></el-col>
      <el-col :span="6"></el-col>
    </el-row>
    <el-row :gutter="12" style="margin-top: 8px">
      <el-col :span="24" style="text-align: right">
        <el-button type="primary" @click="searchShoeSelector">查询</el-button>
      </el-col>
    </el-row>

    <el-row style="margin-top: 8px">
      <el-col :span="24">
        <el-text>已选鞋型：{{ selectedShoeTypeCount }}</el-text>
      </el-col>
    </el-row>

    <el-table
      :data="filteredShoeSelectorShoes"
      border
      stripe
      row-key="shoeId"
      v-loading="shoeSelectorLoading"
      style="height: 60vh; margin-top: 12px"
    >
      <el-table-column type="expand" width="55">
        <template #default="props">
          <el-table
            :data="props.row.shoeTypeData"
            border
            stripe
            row-key="shoeTypeId"
            @selection-change="(selection) => handleShoeTypeSelectionChange(selection, props.row)"
          >
            <el-table-column type="selection" width="55" />
            <el-table-column prop="colorName" label="颜色" min-width="120" />
            <el-table-column label="鞋图" width="140">
              <template #default="scope">
                <el-image
                  v-if="scope.row.shoeImageUrl"
                  :src="scope.row.shoeImageUrl"
                  style="width: 110px; height: 72px"
                  fit="cover"
                />
              </template>
            </el-table-column>
          </el-table>
        </template>
      </el-table-column>
      <el-table-column prop="shoeRid" label="工厂型号" min-width="180" />
      <el-table-column prop="shoeTypeCount" label="颜色数" width="90" />
    </el-table>
    <el-pagination
      style="margin-top: 10px; justify-content: flex-end"
      layout="total, prev, pager, next"
      :current-page="shoeSelectorPage"
      :page-size="shoeSelectorPageSize"
      :total="shoeSelectorTotal"
      @current-change="handleShoeSelectorPageChange"
    />

    <template #footer>
      <el-button @click="shoeSelectorDialogVisible = false">取消</el-button>
      <el-button type="primary" @click="confirmBatchAddShoeTypes">加入明细</el-button>
    </template>
  </el-dialog>

  <el-dialog v-model="dispatchDialogVisible" title="下发拆单" width="760px" :close-on-click-modal="false">
    <el-form label-width="110px">
      <el-form-item label="订单开始日期" required>
        <el-date-picker v-model="dispatchForm.startDate" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
      </el-form-item>
      <el-form-item label="订单结束日期" required>
        <el-date-picker v-model="dispatchForm.endDate" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
      </el-form-item>
      <el-form-item label="订单号" required>
        <el-table :data="paginatedDispatchOrderRidRows" border style="width: 100%; max-height: 300px">
          <el-table-column prop="shoeRid" label="鞋型" min-width="160" />
          <el-table-column prop="colorSummary" label="颜色" min-width="180" />
          <el-table-column label="订单号" min-width="220">
            <template #default="scope">
              <el-input v-model="scope.row.orderRid" placeholder="请输入订单号" />
            </template>
          </el-table-column>
        </el-table>
        <el-pagination
          style="margin-top: 10px; justify-content: flex-end"
          layout="total, prev, pager, next"
          :current-page="dispatchPage"
          :page-size="dispatchPageSize"
          :total="dispatchOrderRidRows.length"
          @current-change="handleDispatchPageChange"
        />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="dispatchDialogVisible = false">取消</el-button>
      <el-button type="primary" @click="dispatchSheet">确认下发</el-button>
    </template>
  </el-dialog>

  <el-dialog v-model="packagingUploadDialogVisible" title="上传预报单包装资料" width="520px" :close-on-click-modal="false">
    <el-upload
      ref="forecastPackagingUpload"
      :auto-upload="false"
      :limit="1"
      :on-exceed="handlePackagingFileExceed"
      :on-change="handlePackagingFileChange"
      :on-remove="handlePackagingFileRemove"
      :before-upload="beforePackagingUpload"
      :http-request="uploadForecastPackagingFile"
      drag
    >
      <el-icon style="font-size: 28px"><Upload /></el-icon>
      <div style="margin-top: 8px">将文件拖到此处，或点击上传</div>
      <template #tip>
        <div>仅支持 .xls/.xlsx，上传后下发拆单会自动复制到所有下属订单目录</div>
      </template>
    </el-upload>
    <template #footer>
      <el-button @click="packagingUploadDialogVisible = false">取消</el-button>
      <el-button type="primary" :loading="packagingUploadSubmitting" @click="submitPackagingUpload">上传</el-button>
    </template>
  </el-dialog>
</template>

<script>
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Upload } from '@element-plus/icons-vue'
import { useOrderDialogStore } from '@/Pages/BusinessManager/stores/orderDialog'
import AddBatchInfoDialog from './orderDialogs/AddBatchInfoDialog.vue'
import AddCustomerBatchDialog from './orderDialogs/AddCustomerBatchDialog.vue'
import CustomerBatchTemplateDialog from './orderDialogs/CustomerBatchTemplateDialog.vue'

export default {
  components: {
    AddBatchInfoDialog,
    AddCustomerBatchDialog,
    CustomerBatchTemplateDialog,
    Upload
  },
  data() {
    return {
      dialogStore: useOrderDialogStore(),
      staffId: localStorage.getItem('staffid'),
      userStaffId: null,
      userName: '',
      forecastSheets: [],
      forecastSheetPage: 1,
      forecastSheetPageSize: 20,
      sheetFilters: {
        forecastRid: '',
        forecastCid: '',
        customerName: '',
        customerBrand: '',
        status: null
      },

      customerOptions: [],
      batchTypeOptions: [],
      managerOptions: [],
      currencyTypeOptions: ['RMB', 'USD', 'EUR'],
      shoeSelectorShoes: [],
      shoeTypeCatalog: [],
      shoeTypeOptions: [],
      shoeTypeOptionCache: {},
      manualShoeTypeOptions: [],
      manualShoeTypeLoading: false,
      packagingOptions: [],
      customerBatchData: [],
      customerDisplayBatchData: [],
      currentBatch: [],
      isSyncingBatchSelection: false,
      batchNameFilter: '',
      curBatchType: {},
      editingForecastGroupKey: '',
      attrMapping: {
        size34Name: 'size34Ratio',
        size35Name: 'size35Ratio',
        size36Name: 'size36Ratio',
        size37Name: 'size37Ratio',
        size38Name: 'size38Ratio',
        size39Name: 'size39Ratio',
        size40Name: 'size40Ratio',
        size41Name: 'size41Ratio',
        size42Name: 'size42Ratio',
        size43Name: 'size43Ratio',
        size44Name: 'size44Ratio',
        size45Name: 'size45Ratio',
        size46Name: 'size46Ratio'
      },
      editingForecastItemIds: [],
      sheetBatchDialogForm: {
        customerName: '',
        customerBrand: ''
      },
      batchForm: {
        customerId: '',
        packagingInfoName: '',
        packagingInfoLocale: '',
        batchInfoTypeId: '',
        size34Ratio: 0,
        size35Ratio: 0,
        size36Ratio: 0,
        size37Ratio: 0,
        size38Ratio: 0,
        size39Ratio: 0,
        size40Ratio: 0,
        size41Ratio: 0,
        size42Ratio: 0,
        size43Ratio: 0,
        size44Ratio: 0,
        size45Ratio: 0,
        size46Ratio: 0,
        totalQuantityRatio: 0
      },
      batchTemplateDisplayData: [],
      selectedBatchTemplate: {},
      sheetItemsDialogVisible: false,
      sheetPackagingSubmitting: false,
      sheetPackagingOptions: [],
      sheetPackagingItems: [],
      sheetPackagingPage: 1,
      sheetPackagingPageSize: 10,
      sheetPackagingTarget: null,
      rowQuantityDialogVisible: false,
      rowQuantityEditingGroupKey: '',
      rowQuantityEditingRows: [],
      rowQuantityPage: 1,
      rowQuantityPageSize: 8,
      rowQuantityForm: {},

      shoeSelectorDialogVisible: false,
      shoeSelectorSelection: [],
      selectedShoeTypeMap: {},
      shoeSelectorLoading: false,
      shoeSelectorPage: 1,
      shoeSelectorPageSize: 60,
      shoeSelectorTotal: 0,
      shoeSelectorFilters: {
        shoeRid: '',
        colorName: ''
      },
      shoeSelectorDefaults: {
        totalPairs: 1
      },

      dispatchDialogVisible: false,
      dispatchTargetRow: null,
      dispatchOrderRidRows: [],
      packagingUploadDialogVisible: false,
      packagingUploadTarget: null,
      packagingUploadSubmitting: false,
      selectedPackagingFile: null,
      dispatchForm: {
        startDate: '',
        endDate: ''
      },

      createDialogVisible: false,
      createSubmitting: false,
      isEditMode: false,
      editingForecastSheetId: null,
      createForm: {
        forecastRid: '',
        forecastCid: '',
        customerId: null,
        batchInfoTypeId: null,
        salesmanId: null,
        salesmanName: '',
        supervisorId: null,
        currencyType: 'RMB'
      },
      createItems: [],
      createItemPage: 1,
      createItemPageSize: 20,

      itemDialogVisible: false,
      currentItems: [],
      itemDialogPage: 1,
      itemDialogPageSize: 10,
      previewDialogVisible: false,
      previewTarget: null,
      previewItems: [],
      previewPage: 1,
      previewPageSize: 10,
      dispatchPage: 1,
      dispatchPageSize: 8
    }
  },
  computed: {
    allShoeTypeOptions() {
      const cacheValues = Object.values(this.shoeTypeOptionCache || {})
      if (cacheValues.length) return cacheValues
      return this.manualShoeTypeOptions || []
    },
    selectedShoeTypeCount() {
      return Object.keys(this.selectedShoeTypeMap || {}).length
    },
    filteredShoeSelectorShoes() {
      const ridKeyword = String(this.shoeSelectorFilters.shoeRid || '').trim().toLowerCase()
      const colorKeyword = String(this.shoeSelectorFilters.colorName || '').trim().toLowerCase()
      return (this.shoeSelectorShoes || [])
        .map((shoe) => {
          const types = Array.isArray(shoe.shoeTypeData) ? shoe.shoeTypeData : []
          const filteredTypes = types.filter((type) => {
            if (!colorKeyword) return true
            return String(type.colorName || '').toLowerCase().includes(colorKeyword)
          })
          return {
            ...shoe,
            shoeTypeData: filteredTypes,
            shoeTypeCount: filteredTypes.length
          }
        })
        .filter((shoe) => {
          const ridMatch = !ridKeyword || String(shoe.shoeRid || '').toLowerCase().includes(ridKeyword)
          return ridMatch && shoe.shoeTypeData.length > 0
        })
    },
    paginatedCreateItems() {
      const start = (this.createItemPage - 1) * this.createItemPageSize
      const end = start + this.createItemPageSize
      return (this.createItems || []).slice(start, end)
    },
    filteredForecastSheets() {
      const filters = this.sheetFilters || {}
      const keyword = (value) => String(value || '').trim().toLowerCase()
      const ridKeyword = keyword(filters.forecastRid)
      const cidKeyword = keyword(filters.forecastCid)
      const customerKeyword = keyword(filters.customerName)
      const brandKeyword = keyword(filters.customerBrand)
      const hasStatusFilter = filters.status === 0 || filters.status === 1 || String(filters.status || '').trim() !== ''
      return (this.forecastSheets || []).filter((row) => {
        if (ridKeyword && !String(row?.forecastRid || '').toLowerCase().includes(ridKeyword)) return false
        if (cidKeyword && !String(row?.forecastCid || '').toLowerCase().includes(cidKeyword)) return false
        if (customerKeyword && !String(row?.customerName || '').toLowerCase().includes(customerKeyword)) return false
        if (brandKeyword && !String(row?.customerBrand || '').toLowerCase().includes(brandKeyword)) return false
        if (hasStatusFilter && Number(row?.status) !== Number(filters.status)) return false
        return true
      })
    },
    filteredShoeTypeCatalog() {
      return this.shoeTypeCatalog || []
    },
    paginatedForecastSheets() {
      const start = (this.forecastSheetPage - 1) * this.forecastSheetPageSize
      const end = start + this.forecastSheetPageSize
      return (this.filteredForecastSheets || []).slice(start, end)
    },
    paginatedCurrentItems() {
      const start = (this.itemDialogPage - 1) * this.itemDialogPageSize
      const end = start + this.itemDialogPageSize
      return (this.currentItems || []).slice(start, end)
    },
    paginatedSheetPackagingItems() {
      const start = (this.sheetPackagingPage - 1) * this.sheetPackagingPageSize
      const end = start + this.sheetPackagingPageSize
      return (this.sheetPackagingItems || []).slice(start, end)
    },
    paginatedPreviewItems() {
      const start = (this.previewPage - 1) * this.previewPageSize
      const end = start + this.previewPageSize
      return (this.previewItems || []).slice(start, end)
    },
    paginatedRowQuantityEditingRows() {
      const start = (this.rowQuantityPage - 1) * this.rowQuantityPageSize
      const end = start + this.rowQuantityPageSize
      return (this.rowQuantityEditingRows || []).slice(start, end)
    },
    paginatedDispatchOrderRidRows() {
      const start = (this.dispatchPage - 1) * this.dispatchPageSize
      const end = start + this.dispatchPageSize
      return (this.dispatchOrderRidRows || []).slice(start, end)
    }
  },
  watch: {
    sheetFilters: {
      handler() {
        this.forecastSheetPage = 1
      },
      deep: true
    }
  },
  mounted() {
    this.$setAxiosToken()
    this.initPage()
  },
  methods: {
    handleForecastSheetPageChange(page) {
      this.forecastSheetPage = page
    },
    handleItemDialogPageChange(page) {
      this.itemDialogPage = page
    },
    handleSheetPackagingPageChange(page) {
      this.sheetPackagingPage = page
    },
    handlePreviewPageChange(page) {
      this.previewPage = page
    },
    handleRowQuantityPageChange(page) {
      this.rowQuantityPage = page
    },
    handleDispatchPageChange(page) {
      this.dispatchPage = page
    },
    buildForecastItemGroupKey(item) {
      const sortIndex = item?.sortIndex ?? item?.sort_index
      if (sortIndex !== undefined && sortIndex !== null && String(sortIndex).trim() !== '') {
        return `sort_${String(sortIndex)}`
      }
      const shoeTypeId = item?.shoeTypeId == null ? '' : String(item.shoeTypeId)
      const shoeRid = String(item?.shoeRid || '')
      const colorName = String(item?.colorName || '')
      const customerShoeName = String(item?.customerShoeName || '')
      const customerColorName = String(item?.customerColorName || '')
      return `${shoeTypeId}__${shoeRid}__${colorName}__${customerShoeName}__${customerColorName}`
    },
    normalizeForecastItemPackagingIds(item) {
      if (Array.isArray(item?.packagingInfoIds) && item.packagingInfoIds.length) {
        return item.packagingInfoIds.map((id) => Number(id)).filter((id) => !Number.isNaN(id))
      }
      if (item?.packagingInfoId) {
        const id = Number(item.packagingInfoId)
        return Number.isNaN(id) ? [] : [id]
      }
      return []
    },
    normalizeForecastItemPackagingNames(item) {
      if (Array.isArray(item?.packagingInfoNames) && item.packagingInfoNames.length) {
        return item.packagingInfoNames.filter((name) => String(name || '').trim())
      }
      if (item?.packagingInfoName) {
        return [item.packagingInfoName]
      }
      return []
    },
    getPackagingRatio(packagingInfoId) {
      const target = (this.sheetPackagingOptions || []).find((item) => Number(item.packagingInfoId) === Number(packagingInfoId))
      return Number(target?.totalQuantityRatio || 0)
    },
    getRowPackagingRatio(row, packagingInfoId) {
      const key = String(packagingInfoId)
      const ratioMap = row?.packagingInfoRatioMap || {}
      const rowRatio = Number(ratioMap[key] || 0)
      if (rowRatio > 0) {
        return rowRatio
      }
      return this.getPackagingRatio(packagingInfoId)
    },
    getPackagingName(packagingInfoId) {
      const target = (this.sheetPackagingOptions || []).find((item) => Number(item.packagingInfoId) === Number(packagingInfoId))
      return target?.packagingInfoName || String(packagingInfoId || '')
    },
    getRowPackagingName(row, packagingInfoId) {
      const key = String(packagingInfoId)
      const rowNameMap = row?.packagingInfoNameMap || {}
      const mappedName = rowNameMap[key]
      if (String(mappedName || '').trim()) {
        return mappedName
      }
      const ids = Array.isArray(row?.packagingInfoIds) ? row.packagingInfoIds : []
      const names = Array.isArray(row?.packagingInfoNames) ? row.packagingInfoNames : []
      const idx = ids.findIndex((id) => String(id) === key)
      if (idx > -1 && String(names[idx] || '').trim()) {
        return names[idx]
      }
      const sourceItem = (row?.sourceItems || []).find((item) => String(item?.packagingInfoId || '') === key)
      if (String(sourceItem?.packagingInfoName || '').trim()) {
        return sourceItem.packagingInfoName
      }
      return this.getPackagingName(packagingInfoId)
    },
    getRowPackagingPersistedTotal(row, packagingInfoId) {
      const key = String(packagingInfoId)
      const rowTotalMap = row?.packagingInfoPersistedTotalMap || {}
      if (rowTotalMap[key] != null) {
        return Number(rowTotalMap[key] || 0)
      }
      const sourceItems = Array.isArray(row?.sourceItems) ? row.sourceItems : []
      let total = 0
      sourceItems.forEach((item) => {
        if (String(item?.packagingInfoId || '') !== key) return
        total += Number(item?.totalPairs || 0)
      })
      return Number(total || 0)
    },
    rebuildGroupedPackagingQuantities(row) {
      const sourceItems = Array.isArray(row?.sourceItems) ? row.sourceItems : []
      const map = {}
      sourceItems.forEach((item) => {
        const pid = Number(item?.packagingInfoId)
        if (!pid) return
        const ratio = this.getRowPackagingRatio(row, pid)
        const totalPairs = Number(item?.totalPairs || 0)
        const persistedQty = Number(item?.packagingInfoQuantity || 0)
        const qty = persistedQty > 0 ? persistedQty : (ratio > 0 ? Math.max(1, Math.round(totalPairs / ratio)) : 1)
        map[String(pid)] = qty
      })
      ;(row.packagingInfoIds || []).forEach((pid) => {
        if (!map[String(pid)]) map[String(pid)] = 1
      })
      row.packagingInfoQuantityMap = map
      this.recomputeRowTotalPairs(row)
    },
    syncGroupedRowToSourceItems(row) {
      const sourceItems = Array.isArray(row?.sourceItems) ? row.sourceItems : []
      if (!sourceItems.length) return
      sourceItems.forEach((sourceItem) => {
        const pid = Number(sourceItem?.packagingInfoId || 0)
        if (!pid) return
        const ratio = this.getRowPackagingRatio(row, pid)
        const quantity = Number(row?.packagingInfoQuantityMap?.[String(pid)] || 0)
        if (ratio > 0 && quantity > 0) {
          sourceItem.totalPairs = Number((ratio * quantity).toFixed(2))
          sourceItem.packagingInfoQuantity = quantity
        }
      })
    },
    recomputeRowTotalPairs(row) {
      const ids = Array.isArray(row?.packagingInfoIds) ? row.packagingInfoIds : []
      let total = 0
      ids.forEach((pid) => {
        const ratio = this.getRowPackagingRatio(row, pid)
        const qty = Number(row?.packagingInfoQuantityMap?.[String(pid)] || 0)
        if (ratio > 0 && qty > 0) {
          total += ratio * qty
          return
        }
        total += this.getRowPackagingPersistedTotal(row, pid)
      })
      row.computedTotalPairs = Number(total.toFixed(2))
      row.totalPairs = row.computedTotalPairs
      this.syncGroupedRowToSourceItems(row)
    },
    replaceSheetPackagingItem(row) {
      const groupKey = String(row?.groupKey || '')
      if (!groupKey) return
      const targetIndex = (this.sheetPackagingItems || []).findIndex((item) => String(item.groupKey) === groupKey)
      if (targetIndex < 0) return
      const replaced = {
        ...row,
        packagingInfoIds: [...(row.packagingInfoIds || [])],
        packagingInfoNames: [...(row.packagingInfoNames || [])],
        packagingInfoQuantityMap: { ...(row.packagingInfoQuantityMap || {}) },
        packagingInfoNameMap: { ...(row.packagingInfoNameMap || {}) },
        packagingInfoRatioMap: { ...(row.packagingInfoRatioMap || {}) },
        sourceItems: Array.isArray(row.sourceItems) ? row.sourceItems.map((source) => ({ ...source })) : []
      }
      this.sheetPackagingItems.splice(targetIndex, 1, replaced)
      this.sheetPackagingItems = [...(this.sheetPackagingItems || [])]
    },
    syncBatchSelectionToSourceItems(row, selectedBatchList) {
      const sourceItems = Array.isArray(row?.sourceItems) ? row.sourceItems : []
      if (!sourceItems.length) return
      const sourceByPid = {}
      sourceItems.forEach((sourceItem) => {
        const sourcePid = Number(sourceItem?.packagingInfoId || 0)
        if (sourcePid > 0) {
          sourceByPid[String(sourcePid)] = sourceItem
        }
      })
      const baseSource = sourceItems[0]
      const quantityMap = row?.packagingInfoQuantityMap || {}
      const nextSourceItems = selectedBatchList.map((batch) => {
        const pid = Number(batch?.packagingInfoId || 0)
        const key = String(pid)
        const existing = sourceByPid[key]
        const ratio = this.getRowPackagingRatio(row, pid)
        const qty = Number(quantityMap[key] || 0)
        const nextTotalPairs = ratio > 0 && qty > 0 ? Number((ratio * qty).toFixed(2)) : Number(existing?.totalPairs || 0)
        return {
          ...(existing || baseSource || {}),
          packagingInfoId: pid,
          packagingInfoName: batch?.packagingInfoName || existing?.packagingInfoName || '',
          totalQuantityRatio: Number(batch?.totalQuantityRatio || existing?.totalQuantityRatio || ratio || 0),
          packagingInfoQuantity: qty > 0 ? qty : Number(existing?.packagingInfoQuantity || 0),
          totalPairs: nextTotalPairs
        }
      })
      row.sourceItems = nextSourceItems
    },
    formatRowPackagingTotals(row) {
      const ids = Array.isArray(row?.packagingInfoIds) ? row.packagingInfoIds : []
      if (!ids.length) return '-'
      return ids
        .map((pid) => {
          const name = this.getRowPackagingName(row, pid)
          const unitQty = Number(row?.packagingInfoQuantityMap?.[String(pid)] || 0)
          const ratio = this.getRowPackagingRatio(row, pid)
          const totalQty = unitQty > 0 && ratio > 0
            ? Number((unitQty * ratio).toFixed(2))
            : this.getRowPackagingPersistedTotal(row, pid)
          return `${name}:${totalQty}`
        })
        .join('；')
    },
    formatRowPackagingAmounts(row) {
      const ids = Array.isArray(row?.packagingInfoIds) ? row.packagingInfoIds : []
      if (!ids.length) return '-'
      const unitPrice = Number(row?.unitPrice || 0)
      return ids
        .map((pid) => {
          const name = this.getRowPackagingName(row, pid)
          const unitQty = Number(row?.packagingInfoQuantityMap?.[String(pid)] || 0)
          const ratio = this.getRowPackagingRatio(row, pid)
          const totalQty = unitQty > 0 && ratio > 0
            ? Number((unitQty * ratio).toFixed(2))
            : this.getRowPackagingPersistedTotal(row, pid)
          const amount = totalQty * unitPrice
          return `${name}:${this.formatCurrency(amount)}`
        })
        .join('；')
    },
    getRowTotalAmount(row) {
      const totalPairs = Number(row?.computedTotalPairs ?? row?.totalPairs ?? 0)
      const unitPrice = Number(row?.unitPrice || 0)
      return Number((totalPairs * unitPrice).toFixed(2))
    },
    formatCurrency(value) {
      const amount = Number(value || 0)
      if (!Number.isFinite(amount)) return '0.00'
      return amount.toFixed(2)
    },
    openRowQuantityDialog(row) {
      if (!row?.groupKey) {
        ElMessage.error('未定位到当前鞋型')
        return
      }
      const ids = Array.isArray(row?.packagingInfoIds) ? row.packagingInfoIds : []
      if (!ids.length) {
        ElMessage.warning('请先编辑配码')
        return
      }
      const form = {}
      const rows = ids.map((pid) => {
        const key = String(pid)
        form[key] = Number(row?.packagingInfoQuantityMap?.[key] || 1)
        return {
          key,
          packagingInfoId: Number(pid),
          packagingInfoName: this.getRowPackagingName(row, pid)
        }
      })
      this.rowQuantityEditingGroupKey = row.groupKey
      this.rowQuantityForm = form
      this.rowQuantityEditingRows = rows
      this.rowQuantityPage = 1
      this.rowQuantityDialogVisible = true
    },
    applyRowQuantityUpdate() {
      if (!this.rowQuantityEditingGroupKey) {
        ElMessage.error('未定位到当前鞋型')
        return
      }
      const target = (this.sheetPackagingItems || []).find((row) => String(row.groupKey) === String(this.rowQuantityEditingGroupKey))
      if (!target) {
        ElMessage.error('目标鞋型不存在')
        return
      }
      const ids = Array.isArray(target?.packagingInfoIds) ? target.packagingInfoIds : []
      const map = { ...(target.packagingInfoQuantityMap || {}) }
      for (let i = 0; i < ids.length; i++) {
        const pid = ids[i]
        const key = String(pid)
        const qty = Number(this.rowQuantityForm[key] || 0)
        if (qty <= 0) {
          ElMessage.error('单位数量必须大于0')
          return
        }
        map[key] = qty
      }
      target.packagingInfoQuantityMap = map
      this.recomputeRowTotalPairs(target)
      const targetIndex = (this.sheetPackagingItems || []).findIndex((row) => String(row.groupKey) === String(this.rowQuantityEditingGroupKey))
      if (targetIndex > -1) {
        this.sheetPackagingItems.splice(targetIndex, 1, { ...target })
      }
      this.sheetPackagingItems = [...(this.sheetPackagingItems || [])]
      this.rowQuantityDialogVisible = false
      ElMessage.success('单位数量已更新')
    },
    groupForecastItems(items) {
      const groups = new Map()
      ;(items || []).forEach((rawItem) => {
        const item = { ...rawItem }
        const key = this.buildForecastItemGroupKey(item)
        const packagingInfoIds = this.normalizeForecastItemPackagingIds(item)
        const packagingInfoNames = this.normalizeForecastItemPackagingNames(item)
        const itemUnitPrice = Number(item?.unitPrice ?? item?.unit_price ?? 0)
        if (!groups.has(key)) {
          const packagingInfoNameMap = {}
          const packagingInfoRatioMap = {}
          const packagingInfoPersistedTotalMap = {}
          const sourcePid = Number(item?.packagingInfoId || 0)
          if (sourcePid > 0) {
            const sourceKey = String(sourcePid)
            if (String(item?.packagingInfoName || '').trim()) {
              packagingInfoNameMap[sourceKey] = item.packagingInfoName
            }
            const sourceRatio = Number(item?.totalQuantityRatio || 0)
            if (sourceRatio > 0) {
              packagingInfoRatioMap[sourceKey] = sourceRatio
            }
            packagingInfoPersistedTotalMap[sourceKey] = Number(item?.totalPairs || 0)
          }
          groups.set(key, {
            groupKey: key,
            forecastSheetItemId: item.forecastSheetItemId,
            forecastSheetItemIds: item.forecastSheetItemId != null ? [item.forecastSheetItemId] : [],
            sortIndex: item?.sortIndex ?? item?.sort_index ?? null,
            shoeTypeId: item.shoeTypeId,
            shoeRid: item.shoeRid,
            colorName: item.colorName,
            customerShoeName: item.customerShoeName,
            customerColorName: item.customerColorName,
            totalPairs: item.totalPairs,
            unitPrice: Number.isNaN(itemUnitPrice) ? 0 : itemUnitPrice,
            packagingInfoIds: [...new Set(packagingInfoIds)],
            packagingInfoNames: [...new Set(packagingInfoNames)],
            packagingInfoNameMap,
            packagingInfoRatioMap,
            packagingInfoPersistedTotalMap,
            sourceItems: [item]
          })
          return
        }
        const grouped = groups.get(key)
        if (item.forecastSheetItemId != null) {
          grouped.forecastSheetItemIds.push(item.forecastSheetItemId)
        }
        if (grouped.sortIndex == null && (item?.sortIndex ?? item?.sort_index) != null) {
          grouped.sortIndex = item?.sortIndex ?? item?.sort_index
        }
        grouped.sourceItems.push(item)
        grouped.packagingInfoIds = [...new Set([...(grouped.packagingInfoIds || []), ...packagingInfoIds])]
        grouped.packagingInfoNames = [...new Set([...(grouped.packagingInfoNames || []), ...packagingInfoNames])]
        const sourcePid = Number(item?.packagingInfoId || 0)
        if (sourcePid > 0) {
          const sourceKey = String(sourcePid)
          grouped.packagingInfoNameMap = grouped.packagingInfoNameMap || {}
          grouped.packagingInfoRatioMap = grouped.packagingInfoRatioMap || {}
          grouped.packagingInfoPersistedTotalMap = grouped.packagingInfoPersistedTotalMap || {}
          if (!String(grouped.packagingInfoNameMap[sourceKey] || '').trim() && String(item?.packagingInfoName || '').trim()) {
            grouped.packagingInfoNameMap[sourceKey] = item.packagingInfoName
          }
          const sourceRatio = Number(item?.totalQuantityRatio || 0)
          if (!Number(grouped.packagingInfoRatioMap[sourceKey]) && sourceRatio > 0) {
            grouped.packagingInfoRatioMap[sourceKey] = sourceRatio
          }
          const oldTotal = Number(grouped.packagingInfoPersistedTotalMap[sourceKey] || 0)
          grouped.packagingInfoPersistedTotalMap[sourceKey] = oldTotal + Number(item?.totalPairs || 0)
        }
        if ((!Number(grouped.unitPrice) || Number(grouped.unitPrice) === 0) && !Number.isNaN(itemUnitPrice) && itemUnitPrice > 0) {
          grouped.unitPrice = itemUnitPrice
        }
      })
      return Array.from(groups.values()).map((grouped) => ({
        ...grouped,
        forecastSheetItemIds: [...new Set(grouped.forecastSheetItemIds || [])],
        packagingInfoName: (grouped.packagingInfoNames || []).join(' / '),
        packagingInfoQuantityMap: {},
        packagingInfoNameMap: { ...(grouped.packagingInfoNameMap || {}) },
        packagingInfoRatioMap: { ...(grouped.packagingInfoRatioMap || {}) },
        packagingInfoPersistedTotalMap: { ...(grouped.packagingInfoPersistedTotalMap || {}) },
        computedTotalPairs: Number(grouped.totalPairs || 0)
      }))
    },
    async initPage() {
      await Promise.all([
        this.loadUser(),
        this.loadCustomers(),
        this.loadBatchTypes(),
        this.loadManagers(),
        this.loadForecastSheets()
      ])
    },
    async loadUser() {
      const response = await axios.get(`${this.$apiBaseUrl}/order/onmount`)
      this.userName = response.data.staffName || ''
      this.userStaffId = Number(response.data.staffId || this.staffId) || null
      this.createForm.salesmanName = this.userName
      this.createForm.salesmanId = this.userStaffId
    },
    async loadCustomers() {
      const response = await axios.get(`${this.$apiBaseUrl}/customer/getcustomerdetails`)
      this.customerOptions = response.data || []
    },
    async loadBatchTypes() {
      const response = await axios.get(`${this.$apiBaseUrl}/batchtype/getallbatchtypesbusiness`)
      this.batchTypeOptions = response.data?.batchDataTypes || response.data || []
    },
    async loadManagers() {
      const response = await axios.get(`${this.$apiBaseUrl}/general/getbusinessmanagers`)
      this.managerOptions = response.data || []
    },
    async loadShoeTypes(params = {}) {
      this.shoeSelectorLoading = true
      const response = await axios.get(`${this.$apiBaseUrl}/shoe/getallshoesnew`, {
        params: {
          page: params.page || 1,
          pageSize: params.pageSize || this.shoeSelectorPageSize,
          shoerid: params.shoeRid || '',
          available: 1
        }
      })
      const shoes = response.data?.shoeTable || []
      this.shoeSelectorTotal = Number(response.data?.total || 0)
      this.shoeSelectorShoes = shoes
      const options = []
      shoes.forEach((shoe) => {
        const shoeTypes = shoe.shoeTypeData || []
        shoeTypes.forEach((type) => {
          options.push({
            shoeTypeId: type.shoeTypeId,
            shoeRid: shoe.shoeRid,
            colorName: type.colorName,
            colorId: type.colorId,
            shoeImageUrl: type.shoeImageUrl || ''
          })
        })
      })
      this.shoeTypeCatalog = options
      options.forEach((item) => {
        this.shoeTypeOptionCache[item.shoeTypeId] = item
      })
      this.shoeSelectorLoading = false
    },
    findShoeTypeOptionById(shoeTypeId) {
      const cached = this.shoeTypeOptionCache[shoeTypeId]
      if (cached) return cached
      const merged = [
        ...(this.manualShoeTypeOptions || []),
        ...(this.shoeTypeCatalog || []),
        ...(this.shoeTypeOptions || [])
      ]
      return merged.find((item) => Number(item.shoeTypeId) === Number(shoeTypeId))
    },
    async queryManualShoeType(keyword) {
      const q = String(keyword || '').trim()
      if (!q) {
        this.manualShoeTypeOptions = []
        return
      }
      this.manualShoeTypeLoading = true
      await this.loadShoeTypes({ page: 1, pageSize: 120, shoeRid: q })
      this.manualShoeTypeOptions = [...this.shoeTypeCatalog]
      this.manualShoeTypeOptions.forEach((item) => {
        this.shoeTypeOptionCache[item.shoeTypeId] = item
      })
      this.manualShoeTypeLoading = false
    },
    async searchShoeSelector() {
      this.shoeSelectorPage = 1
      await this.loadShoeTypes({
        page: this.shoeSelectorPage,
        pageSize: this.shoeSelectorPageSize,
        shoeRid: this.shoeSelectorFilters.shoeRid
      })
    },
    async handleShoeSelectorPageChange(page) {
      this.shoeSelectorPage = page
      await this.loadShoeTypes({
        page: this.shoeSelectorPage,
        pageSize: this.shoeSelectorPageSize,
        shoeRid: this.shoeSelectorFilters.shoeRid
      })
    },
    async loadForecastSheets() {
      const response = await axios.get(`${this.$apiBaseUrl}/forecastsheet/list`)
      this.forecastSheets = response.data || []
      this.forecastSheetPage = 1
    },
    resetSheetFilters() {
      this.sheetFilters = {
        forecastRid: '',
        forecastCid: '',
        customerName: '',
        customerBrand: '',
        status: null
      }
      this.forecastSheetPage = 1
    },
    async openPreviewDialog(row) {
      if (!row?.forecastSheetId) return
      const response = await axios.get(`${this.$apiBaseUrl}/forecastsheet/items`, {
        params: { forecastSheetId: row.forecastSheetId }
      })
      this.previewTarget = { ...row }
      this.previewItems = this.groupForecastItems(response.data || [])
      this.previewPage = 1
      this.previewDialogVisible = true
    },
    downloadForecastExcel(row, outputType = 0) {
      if (!row?.forecastSheetId) {
        ElMessage.error('未选择预报单')
        return
      }
      window.open(`${this.$apiBaseUrl}/forecastsheet/downloadexcel?forecastSheetId=${row.forecastSheetId}&outputType=${outputType}`)
    },

    async handleCustomerChange(customerId) {
      if (!customerId) {
        return
      }
    },
    async handleBatchTypeChange(batchInfoTypeId) {
      if (!batchInfoTypeId) return
    },
    async loadPackagingOptions(customerId, batchInfoTypeId) {
      const response = await axios.get(`${this.$apiBaseUrl}/customer/getcustomerbatchinfo`, {
        params: { customerid: customerId }
      })
      const allTypes = Array.isArray(response.data) ? response.data : []
      const matched = allTypes.find((item) => Number(item.batchInfoTypeId) === Number(batchInfoTypeId))
      const options = matched?.batchInfoList || []
      this.packagingOptions = options
      return options
    },
    handleShoeTypeChange(row, shoeTypeId) {
      const target = this.findShoeTypeOptionById(shoeTypeId)
      if (!target) return
      row.shoeRid = target.shoeRid
      row.colorName = target.colorName
      row.shoeImageUrl = target.shoeImageUrl || ''
    },
    handleCustomerShoeNameInput(row, value) {
      const shoeRid = String(row?.shoeRid || '').trim()
      if (!shoeRid) return
      const text = value == null ? '' : String(value)
      ;(this.createItems || []).forEach((item) => {
        if (String(item?.shoeRid || '').trim() === shoeRid) {
          item.customerShoeName = text
        }
      })
    },
    handlePackagingChange(row, packagingInfoId) {
      const target = (this.sheetPackagingOptions || []).find((item) => Number(item.packagingInfoId) === Number(packagingInfoId))
      if (!target) {
        row.packagingInfoName = ''
        return
      }
      row.packagingInfoName = target.packagingInfoName
    },

    openCreateDialog() {
      this.isEditMode = false
      this.editingForecastSheetId = null
      this.createDialogVisible = true
      this.createForm = {
        forecastRid: '',
        forecastCid: '',
        customerId: null,
        batchInfoTypeId: null,
        salesmanId: this.userStaffId,
        salesmanName: this.userName,
        supervisorId: null,
        currencyType: 'RMB'
      }
      this.createItems = []
      this.createItemPage = 1
      this.addItemRow()
    },
    async openEditDialog(row) {
      if (!row?.forecastSheetId) return
      const response = await axios.get(`${this.$apiBaseUrl}/forecastsheet/items`, {
        params: { forecastSheetId: row.forecastSheetId }
      })
      const editItems = response.data || []
      const groupedEditItems = this.groupForecastItems(editItems.map((item) => ({ ...item })))
      this.isEditMode = true
      this.editingForecastSheetId = row.forecastSheetId
      this.createDialogVisible = true
      this.createForm = {
        forecastRid: row.forecastRid || '',
        forecastCid: row.forecastCid || '',
        customerId: row.customerId || null,
        batchInfoTypeId: row.batchInfoTypeId || null,
        salesmanId: row.salesmanId || this.userStaffId,
        salesmanName: this.userName,
        supervisorId: row.supervisorId || null,
        currencyType: row.currencyType || 'RMB'
      }
      this.createItems = groupedEditItems.map((item) => ({
        uid: `${Date.now()}-${Math.random()}-${item.forecastSheetItemId || item.groupKey}`,
        shoeTypeId: item.shoeTypeId,
        shoeRid: item.shoeRid,
        colorName: item.colorName,
        shoeImageUrl: '',
        customerShoeName: item.customerShoeName,
        customerColorName: item.customerColorName,
        packagingInfoId: Array.isArray(item.packagingInfoIds) && item.packagingInfoIds.length ? item.packagingInfoIds[0] : null,
        packagingInfoName: item.packagingInfoName,
        unitPrice: Number(item.unitPrice || 0),
        totalPairs: Number(item.computedTotalPairs ?? item.totalPairs ?? 0),
        sortIndex: item?.sortIndex ?? null,
        sourceItems: Array.isArray(item.sourceItems) ? item.sourceItems.map((source) => ({ ...source })) : []
      }))
      this.createItems.forEach((item) => {
        if (!item?.shoeTypeId) return
        this.shoeTypeOptionCache[item.shoeTypeId] = {
          shoeTypeId: item.shoeTypeId,
          shoeRid: item.shoeRid || '',
          colorName: item.colorName || '',
          shoeImageUrl: ''
        }
      })
      this.manualShoeTypeOptions = Array.from(
        new Map(
          [...(this.manualShoeTypeOptions || []), ...Object.values(this.shoeTypeOptionCache || {})]
            .filter((item) => item && item.shoeTypeId)
            .map((item) => [item.shoeTypeId, item])
        ).values()
      )
      this.createItemPage = 1
    },
    async deleteForecastSheet(row) {
      if (!row?.forecastSheetId) return
      try {
        await ElMessageBox.confirm(`确认删除预报单 ${row.forecastRid} 吗？`, '提示', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        })
        await axios.post(`${this.$apiBaseUrl}/forecastsheet/delete`, {
          forecastSheetId: row.forecastSheetId
        })
        ElMessage.success('删除成功')
        await this.loadForecastSheets()
      } catch (error) {
      }
    },
    addItemRow() {
      this.createItems.push({
        uid: `${Date.now()}-${Math.random()}`,
        shoeTypeId: null,
        shoeRid: '',
        colorName: '',
        shoeImageUrl: '',
        customerShoeName: '',
        customerColorName: '',
        packagingInfoId: null,
        packagingInfoName: '',
        unitPrice: 0,
        totalPairs: 1
      })
      this.createItemPage = Math.max(1, Math.ceil(this.createItems.length / this.createItemPageSize))
    },
    removeItemRowByUid(uid) {
      this.createItems = (this.createItems || []).filter((item) => item.uid !== uid)
      const maxPage = Math.max(1, Math.ceil(this.createItems.length / this.createItemPageSize))
      if (this.createItemPage > maxPage) {
        this.createItemPage = maxPage
      }
    },
    handleCreateItemPageChange(page) {
      this.createItemPage = page
    },

    openShoeSelectorDialog() {
      this.shoeSelectorDialogVisible = true
      this.shoeSelectorSelection = []
      this.selectedShoeTypeMap = {}
      this.shoeSelectorPage = 1
      this.shoeSelectorFilters = {
        shoeRid: '',
        colorName: ''
      }
      this.shoeSelectorDefaults = {
        totalPairs: 1
      }
      this.searchShoeSelector()
    },
    async openSheetPackagingDialog(row) {
      if (!row?.forecastSheetId) return
      if (!row.customerId || !row.batchInfoTypeId) {
        ElMessage.error('预报单缺少客户或配码种类，无法编辑配码')
        return
      }
      this.sheetPackagingTarget = row
      this.sheetBatchDialogForm = {
        customerName: row.customerName || '',
        customerBrand: row.customerBrand || ''
      }
      this.curBatchType = (this.batchTypeOptions || []).find((item) => Number(item.batchInfoTypeId) === Number(row.batchInfoTypeId)) || {}
      this.batchNameFilter = ''
      this.currentBatch = []
      this.editingForecastItemIds = []
      this.editingForecastGroupKey = ''
      const [itemResp, packagingResp] = await Promise.all([
        axios.get(`${this.$apiBaseUrl}/forecastsheet/items`, {
          params: { forecastSheetId: row.forecastSheetId }
        }),
        this.loadPackagingOptions(row.customerId, row.batchInfoTypeId)
      ])
      this.sheetPackagingItems = this.groupForecastItems((itemResp.data || []).map((item) => ({ ...item })))
      this.sheetPackagingOptions = packagingResp || []
      this.customerBatchData = [...this.sheetPackagingOptions]
      this.customerDisplayBatchData = [...this.sheetPackagingOptions]
      this.sheetPackagingItems.forEach((item) => this.rebuildGroupedPackagingQuantities(item))
      this.sheetPackagingPage = 1
      this.sheetItemsDialogVisible = true
    },
    handleSelectionBatchData(selection) {
      const incoming = Array.isArray(selection) ? selection : []
      const current = Array.isArray(this.currentBatch) ? this.currentBatch : []
      if (this.isSyncingBatchSelection && incoming.length === 0 && current.length > 0) {
        return
      }

      const visibleIdSet = new Set((this.customerDisplayBatchData || []).map((row) => String(row?.packagingInfoId)))
      const mergedMap = new Map()

      current.forEach((item) => {
        const id = item?.packagingInfoId
        if (id === undefined || id === null) return
        const key = String(id)
        if (!visibleIdSet.has(key)) {
          mergedMap.set(key, item)
        }
      })

      incoming.forEach((item) => {
        const id = item?.packagingInfoId
        if (id === undefined || id === null) return
        mergedMap.set(String(id), item)
      })

      this.currentBatch = Array.from(mergedMap.values())
    },
    reselectSelected(ref, selected, displayDataEntity, id) {
      this.$nextTick(() => {
        ;(selected || []).forEach((item) => {
          const foundRow = (displayDataEntity || []).find((row) => row[id] == item[id])
          if (foundRow) {
            ref.toggleRowSelection(foundRow, true)
          }
        })
      })
    },
    filterBatchDataWithSelection() {
      const selectedBatch = this.currentBatch || []
      this.isSyncingBatchSelection = true
      if (!this.batchNameFilter) {
        this.customerDisplayBatchData = [...(this.customerBatchData || [])]
      } else {
        const filtered = (this.customerBatchData || []).filter((task) => String(task.packagingInfoName || '').includes(this.batchNameFilter))
        this.customerDisplayBatchData = [...filtered]
      }
      this.$nextTick(() => {
        const batchTable = this.$refs.forecastBatchInfoDialog?.batchTable?.value || this.$refs.forecastBatchInfoDialog?.batchTable
        if (!batchTable || typeof batchTable.toggleRowSelection !== 'function') return
        selectedBatch.forEach((item) => {
          const found = this.customerDisplayBatchData.find((row) => row.packagingInfoId == item.packagingInfoId)
          if (found) {
            batchTable.toggleRowSelection(found, true)
          }
        })
        this.isSyncingBatchSelection = false
      })
    },
    openForecastBatchInfoDialog(item) {
      const editingIds = Array.isArray(item?.forecastSheetItemIds) && item.forecastSheetItemIds.length
        ? item.forecastSheetItemIds
        : (item?.forecastSheetItemId ? [item.forecastSheetItemId] : [])
      if (!editingIds.length) return
      this.editingForecastItemIds = editingIds
      this.editingForecastGroupKey = item.groupKey || this.buildForecastItemGroupKey(item)
      this.currentBatch = []
      this.customerDisplayBatchData = [...(this.customerBatchData || [])]
      this.dialogStore.openAddBatchInfoDialog()

      const selected = []
      const selectedIds = Array.isArray(item.packagingInfoIds) && item.packagingInfoIds.length
        ? item.packagingInfoIds
        : (item.packagingInfoId ? [item.packagingInfoId] : [])
      selectedIds.forEach((pid) => {
        const found = (this.customerDisplayBatchData || []).find((batch) => Number(batch.packagingInfoId) === Number(pid))
        if (found) {
          selected.push({ packagingInfoId: found.packagingInfoId })
        }
      })
      this.currentBatch = selected

      this.$nextTick(() => {
        const batchTable = this.$refs.forecastBatchInfoDialog?.batchTable?.value || this.$refs.forecastBatchInfoDialog?.batchTable
        if (!batchTable || typeof batchTable.clearSelection !== 'function') return
        batchTable.clearSelection()
        if (selected.length) {
          this.reselectSelected(batchTable, selected, this.customerDisplayBatchData, 'packagingInfoId')
        }
      })
    },
    closeForecastBatchInfoDialog() {
      this.dialogStore.closeAddBatchInfoDialog()
      const batchTable = this.$refs.forecastBatchInfoDialog?.batchTable?.value || this.$refs.forecastBatchInfoDialog?.batchTable
      if (batchTable && typeof batchTable.clearSelection === 'function') {
        batchTable.clearSelection()
      }
    },
    openForecastAddCustomerBatchDialog() {
      if (!this.sheetPackagingTarget?.customerId || !this.sheetPackagingTarget?.batchInfoTypeId) {
        ElMessage.error('缺少客户或配码种类信息，无法新增配码')
        return
      }
      this.batchForm.customerId = this.sheetPackagingTarget.customerId
      this.batchForm.batchInfoTypeId = this.sheetPackagingTarget.batchInfoTypeId
      this.batchForm.packagingInfoLocale = this.curBatchType?.batchInfoTypeName || ''
      this.dialogStore.openCustomerBatchDialog()
    },
    openForecastAddColorDialog() {
      ElMessage.info('预报单配码编辑不涉及颜色新增')
    },
    openForecastSaveTemplateDialog() {
      ElMessage.info('预报单配码编辑暂不支持保存配码模板')
    },
    async getForecastBatchTemplates() {
      if (!this.sheetPackagingTarget?.customerName || !this.sheetPackagingTarget?.customerBrand) {
        this.batchTemplateDisplayData = []
        return
      }
      try {
        const response = await axios.get(`${this.$apiBaseUrl}/ordercreate/getallbatchtemplates`, {
          params: {
            customerName: this.sheetPackagingTarget.customerName,
            customerBrand: this.sheetPackagingTarget.customerBrand
          }
        })
        this.batchTemplateDisplayData = response.data || []
      } catch (error) {
        this.batchTemplateDisplayData = []
        ElMessage.error('加载配码模板失败')
      }
    },
    async openForecastLoadBatchTemplateDialog(item) {
      if (!item?.groupKey) return
      this.editingForecastGroupKey = item.groupKey
      await this.getForecastBatchTemplates()
      this.selectedBatchTemplate = {}
      this.dialogStore.openBatchTemplateDialog()
    },
    handleSelectionBatchTemplate(selection) {
      if (Array.isArray(selection) && selection.length) {
        this.selectedBatchTemplate = selection[selection.length - 1]
      } else {
        this.selectedBatchTemplate = {}
      }
    },
    confirmForecastLoadBatchTemplate() {
      if (!this.selectedBatchTemplate || !Array.isArray(this.selectedBatchTemplate.batchInfoData) || !this.selectedBatchTemplate.batchInfoData.length) {
        ElMessage.error('请选择一个模板')
        return
      }
      if (!this.editingForecastGroupKey) {
        ElMessage.error('未定位到正在编辑的鞋型')
        return
      }
      const item = (this.sheetPackagingItems || []).find((row) => String(row.groupKey) === String(this.editingForecastGroupKey))
      if (!item) {
        ElMessage.error('目标鞋型不存在')
        return
      }
      const templateBatchList = this.selectedBatchTemplate.batchInfoData || []
      item.packagingInfoIds = templateBatchList.map((batch) => batch.packagingInfoId)
      item.packagingInfoNames = templateBatchList.map((batch) => batch.packagingInfoName)
      item.packagingInfoNameMap = templateBatchList.reduce((acc, batch) => {
        const key = String(batch?.packagingInfoId || '')
        if (key) acc[key] = batch?.packagingInfoName || ''
        return acc
      }, {})
      item.packagingInfoRatioMap = templateBatchList.reduce((acc, batch) => {
        const key = String(batch?.packagingInfoId || '')
        const ratio = Number(batch?.totalQuantityRatio || 0)
        if (key && ratio > 0) acc[key] = ratio
        return acc
      }, { ...(item.packagingInfoRatioMap || {}) })
      item.packagingInfoId = item.packagingInfoIds[0]
      item.packagingInfoName = item.packagingInfoNames.join(' / ')
      const quantityMap = { ...(item.packagingInfoQuantityMap || {}) }
      item.packagingInfoIds.forEach((pid) => {
        if (!quantityMap[String(pid)]) quantityMap[String(pid)] = 1
      })
      Object.keys(quantityMap).forEach((key) => {
        if (!item.packagingInfoIds.some((pid) => String(pid) === String(key))) {
          delete quantityMap[key]
        }
      })
      item.packagingInfoQuantityMap = quantityMap
      this.syncBatchSelectionToSourceItems(item, templateBatchList)
      this.recomputeRowTotalPairs(item)
      this.replaceSheetPackagingItem(item)
      this.dialogStore.closeBatchTemplateDialog()
      ElMessage.success('配码模板加载成功')
    },
    async deleteForecastBatchTemplateDialog(row) {
      this.$confirm(`确认删除模板 "${row.templateName}"?`, '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      })
        .then(async () => {
          await axios.post(`${this.$apiBaseUrl}/ordercreate/deletebatchtemplate`, {
            batchInfoTemplateId: row.batchInfoTemplateId
          })
          ElMessage.success('模板删除成功')
          await this.getForecastBatchTemplates()
        })
        .catch(() => {})
    },
    applyForecastBatchToItem() {
      if (!this.editingForecastGroupKey) {
        ElMessage.error('未定位到正在编辑的鞋型')
        return
      }
      if (!this.currentBatch.length) {
        ElMessage.error('请选择配码')
        return
      }
      const selectedBatchList = (this.currentBatch || []).map((batch) => ({ ...batch }))
      const item = (this.sheetPackagingItems || []).find((row) => String(row.groupKey) === String(this.editingForecastGroupKey))
      if (!item) {
        ElMessage.error('目标鞋型不存在')
        return
      }
      item.packagingInfoIds = selectedBatchList.map((batch) => batch.packagingInfoId)
      item.packagingInfoNames = selectedBatchList.map((batch) => batch.packagingInfoName)
      item.packagingInfoNameMap = selectedBatchList.reduce((acc, batch) => {
        const key = String(batch?.packagingInfoId || '')
        if (key) acc[key] = batch?.packagingInfoName || ''
        return acc
      }, {})
      item.packagingInfoRatioMap = selectedBatchList.reduce((acc, batch) => {
        const key = String(batch?.packagingInfoId || '')
        const ratio = Number(batch?.totalQuantityRatio || 0)
        if (key && ratio > 0) acc[key] = ratio
        return acc
      }, { ...(item.packagingInfoRatioMap || {}) })
      item.packagingInfoId = item.packagingInfoIds[0]
      item.packagingInfoName = item.packagingInfoNames.join(' / ')
      const quantityMap = { ...(item.packagingInfoQuantityMap || {}) }
      item.packagingInfoIds.forEach((pid) => {
        if (!quantityMap[String(pid)]) quantityMap[String(pid)] = 1
      })
      Object.keys(quantityMap).forEach((key) => {
        if (!item.packagingInfoIds.some((pid) => String(pid) === String(key))) {
          delete quantityMap[key]
        }
      })
      item.packagingInfoQuantityMap = quantityMap
      this.syncBatchSelectionToSourceItems(item, selectedBatchList)
      this.recomputeRowTotalPairs(item)
      this.replaceSheetPackagingItem(item)
      this.closeForecastBatchInfoDialog()
      ElMessage.success('鞋型配码已更新')
    },
    resetBatchForm() {
      this.batchForm = {
        customerId: '',
        packagingInfoName: '',
        packagingInfoLocale: '',
        batchInfoTypeId: '',
        size34Ratio: 0,
        size35Ratio: 0,
        size36Ratio: 0,
        size37Ratio: 0,
        size38Ratio: 0,
        size39Ratio: 0,
        size40Ratio: 0,
        size41Ratio: 0,
        size42Ratio: 0,
        size43Ratio: 0,
        size44Ratio: 0,
        size45Ratio: 0,
        size46Ratio: 0,
        totalQuantityRatio: 0
      }
    },
    async submitForecastAddCustomerBatchForm() {
      try {
        await axios.post(`${this.$apiBaseUrl}/customer/addcustomerbatchinfo`, this.batchForm)
        ElMessage.success('添加客户配码成功')
        this.dialogStore.closeCustomerBatchDialog()
        this.resetBatchForm()
        if (this.sheetPackagingTarget?.customerId && this.sheetPackagingTarget?.batchInfoTypeId) {
          const options = await this.loadPackagingOptions(this.sheetPackagingTarget.customerId, this.sheetPackagingTarget.batchInfoTypeId)
          this.sheetPackagingOptions = options || []
          this.customerBatchData = [...this.sheetPackagingOptions]
          this.customerDisplayBatchData = [...this.sheetPackagingOptions]
        }
      } catch (error) {
        const message = error?.response?.data?.error || error?.response?.data?.message || '新增客户配码失败'
        ElMessage.error(message)
      }
    },
    async saveSheetPackaging() {
      if (this.sheetPackagingSubmitting) return
      if (!this.sheetPackagingTarget?.forecastSheetId) return
      if (!(this.sheetPackagingItems || []).length) {
        ElMessage.warning('该预报单没有可编辑的鞋型')
        return
      }
      this.sheetPackagingSubmitting = true
      try {
        const requestItems = (this.sheetPackagingItems || []).map((item) => {
          const rawPackagingInfoIds = (Array.isArray(item.packagingInfoIds) && item.packagingInfoIds.length)
            ? item.packagingInfoIds
            : [item.packagingInfoId]
          const packagingInfoIds = (rawPackagingInfoIds || [])
            .map((id) => Number(id))
            .filter((id) => Number.isFinite(id) && id > 0)
          const quantityMap = item.packagingInfoQuantityMap || {}
          const packagingInfoQuantityMap = {}
          packagingInfoIds.forEach((packagingId) => {
            const key = String(packagingId)
            const qty = Number(quantityMap[key] ?? quantityMap[packagingId] ?? 0)
            if (qty > 0) {
              packagingInfoQuantityMap[key] = qty
            }
          })
          const fallbackSource = Array.isArray(item.sourceItems) && item.sourceItems.length ? item.sourceItems[0] : item
          return {
            forecastSheetItemId: item.forecastSheetItemId || fallbackSource.forecastSheetItemId,
            forecastSheetItemIds: item.forecastSheetItemIds || (Array.isArray(item.sourceItems) ? item.sourceItems.map((source) => source.forecastSheetItemId).filter(Boolean) : []),
            shoeTypeId: item.shoeTypeId,
            shoeRid: item.shoeRid,
            colorName: item.colorName,
            customerShoeName: item.customerShoeName,
            customerColorName: item.customerColorName,
            unitPrice: Number(item.unitPrice || 0),
            totalPairs: Number(item.computedTotalPairs ?? item.totalPairs ?? 0),
            packagingInfoIds,
            packagingInfoQuantityMap
          }
        })
        await axios.post(`${this.$apiBaseUrl}/forecastsheet/updatepackaging`, {
          forecastSheetId: this.sheetPackagingTarget.forecastSheetId,
          items: requestItems
        })
        ElMessage.success('配码保存成功')
        this.sheetItemsDialogVisible = false
        await this.loadForecastSheets()
      } catch (error) {
        const message = error?.response?.data?.error || error?.response?.data?.message || '保存配码失败'
        ElMessage.error(message)
      } finally {
        this.sheetPackagingSubmitting = false
      }
    },
    handleShoeTypeSelectionChange(selection, shoeRow) {
      const currentShoeTypeIds = (shoeRow?.shoeTypeData || []).map((item) => Number(item.shoeTypeId))
      currentShoeTypeIds.forEach((id) => {
        delete this.selectedShoeTypeMap[id]
      })
      ;(selection || []).forEach((item) => {
        this.selectedShoeTypeMap[Number(item.shoeTypeId)] = {
          ...item,
          shoeRid: shoeRow?.shoeRid || item.shoeRid || ''
        }
      })
    },
    confirmBatchAddShoeTypes() {
      const selectedShoeTypes = Object.values(this.selectedShoeTypeMap || {})
      if (!selectedShoeTypes.length) {
        ElMessage.warning('请先选择鞋型')
        return
      }
      const existsMap = new Set((this.createItems || []).map((item) => Number(item.shoeTypeId)))
      let appendCount = 0

      selectedShoeTypes.forEach((item) => {
        if (existsMap.has(Number(item.shoeTypeId))) {
          return
        }
        const normalizedOption = {
          shoeTypeId: item.shoeTypeId,
          shoeRid: item.shoeRid || '',
          colorName: item.colorName || '',
          colorId: item.colorId,
          shoeImageUrl: item.shoeImageUrl || ''
        }
        this.shoeTypeOptionCache[item.shoeTypeId] = normalizedOption
        this.createItems.push({
          uid: `${Date.now()}-${Math.random()}-${item.shoeTypeId}`,
          shoeTypeId: item.shoeTypeId,
          shoeRid: item.shoeRid,
          colorName: item.colorName,
          shoeImageUrl: item.shoeImageUrl || '',
          customerShoeName: '',
          customerColorName: '',
          packagingInfoId: null,
          packagingInfoName: '',
          unitPrice: 0,
          totalPairs: Number(this.shoeSelectorDefaults.totalPairs || 1)
        })
        appendCount += 1
      })

      this.createItemPage = Math.max(1, Math.ceil(this.createItems.length / this.createItemPageSize))

      this.shoeSelectorDialogVisible = false
      if (appendCount > 0) {
        ElMessage.success(`已加入 ${appendCount} 个鞋型`)
      } else {
        ElMessage.warning('所选鞋型都已在明细中')
      }
    },

    async submitCreate() {
      if (this.createSubmitting) return
      if (!this.createForm.customerId || !this.createForm.batchInfoTypeId || !this.createForm.supervisorId || !this.createForm.currencyType) {
        ElMessage.error('请填写客户/配码种类/审批经理/货币类型')
        return
      }
      if (!this.createItems.length) {
        ElMessage.error('请至少添加一个鞋型')
        return
      }
      for (let i = 0; i < this.createItems.length; i++) {
        const row = this.createItems[i]
        if (!row.shoeTypeId) {
          ElMessage.error(`第${i + 1}行数据不完整`)
          return
        }
      }

      const submitItems = []
      ;(this.createItems || []).forEach((row) => {
        const sourceItems = Array.isArray(row.sourceItems) ? row.sourceItems : []
        if (sourceItems.length) {
          sourceItems.forEach((source) => {
            submitItems.push({
              shoeTypeId: row.shoeTypeId,
              shoeRid: row.shoeRid,
              colorName: row.colorName,
              customerShoeName: row.customerShoeName,
              customerColorName: row.customerColorName,
              packagingInfoId: source.packagingInfoId || row.packagingInfoId || 0,
              packagingInfoName: source.packagingInfoName || row.packagingInfoName || '',
              unitPrice: Number(row.unitPrice || 0),
              totalPairs: Number(source.totalPairs || 0),
              sortIndex: source?.sortIndex ?? source?.sort_index ?? row?.sortIndex ?? null
            })
          })
          return
        }
        submitItems.push({
          shoeTypeId: row.shoeTypeId,
          shoeRid: row.shoeRid,
          colorName: row.colorName,
          customerShoeName: row.customerShoeName,
          customerColorName: row.customerColorName,
          packagingInfoId: row.packagingInfoId || 0,
          packagingInfoName: row.packagingInfoName || '',
          unitPrice: Number(row.unitPrice || 0),
          totalPairs: Number(row.totalPairs),
          sortIndex: row?.sortIndex ?? null
        })
      })

      const payload = {
        forecastSheetId: this.editingForecastSheetId,
        forecastInfo: {
          forecastRid: this.createForm.forecastRid,
          forecastCid: this.createForm.forecastCid,
          customerId: this.createForm.customerId,
          batchInfoTypeId: this.createForm.batchInfoTypeId,
          salesmanId: this.createForm.salesmanId,
          supervisorId: this.createForm.supervisorId,
          currencyType: this.createForm.currencyType
        },
        items: submitItems
      }
      this.createSubmitting = true
      try {
        const api = this.isEditMode ? 'update' : 'create'
        await axios.post(`${this.$apiBaseUrl}/forecastsheet/${api}`, payload)
        ElMessage.success(this.isEditMode ? '预报单修改成功' : '预报单创建成功')
        this.createDialogVisible = false
        this.isEditMode = false
        this.editingForecastSheetId = null
        await this.loadForecastSheets()
      } catch (error) {
        const message = error?.response?.data?.error || error?.response?.data?.message || '保存失败，请稍后重试'
        ElMessage.error(message)
      } finally {
        this.createSubmitting = false
      }
    },

    async showItems(row) {
      const response = await axios.get(`${this.$apiBaseUrl}/forecastsheet/items`, {
        params: { forecastSheetId: row.forecastSheetId }
      })
      this.currentItems = this.groupForecastItems(response.data || [])
      this.itemDialogPage = 1
      this.itemDialogVisible = true
    },

    async openDispatchDialog(row) {
      const today = new Date().toISOString().slice(0, 10)
      const itemResp = await axios.get(`${this.$apiBaseUrl}/forecastsheet/items`, {
        params: { forecastSheetId: row.forecastSheetId }
      })
      const grouped = {}
      ;(itemResp.data || []).forEach((item) => {
        const key = String(item?.shoeRid || item?.shoeTypeId || '')
        if (!key) return
        if (!grouped[key]) {
          grouped[key] = {
            groupKey: key,
            shoeRid: item?.shoeRid || '',
            colorSet: new Set(),
            orderRid: ''
          }
        }
        grouped[key].colorSet.add(String(item?.colorName || ''))
      })

      this.dispatchTargetRow = row
      this.dispatchForm = {
        startDate: today,
        endDate: today
      }
      this.dispatchOrderRidRows = Object.values(grouped).map((entry) => ({
        groupKey: entry.groupKey,
        shoeRid: entry.shoeRid,
        colorSummary: Array.from(entry.colorSet).filter((v) => v).join(' / '),
        orderRid: ''
      }))
      this.dispatchPage = 1
      this.dispatchDialogVisible = true
    },

    async dispatchSheet() {
      const row = this.dispatchTargetRow
      if (!row) return
      if (!this.dispatchForm.startDate || !this.dispatchForm.endDate) {
        ElMessage.error('请填写起止日期')
        return
      }
      if (!(this.dispatchOrderRidRows || []).length) {
        ElMessage.error('未找到可下发鞋型')
        return
      }
      const localRidSet = new Set()
      for (let i = 0; i < this.dispatchOrderRidRows.length; i++) {
        const rid = String(this.dispatchOrderRidRows[i]?.orderRid || '').trim()
        if (!rid) {
          ElMessage.error(`请填写鞋型 ${this.dispatchOrderRidRows[i]?.shoeRid || ''} 的订单号`)
          return
        }
        if (localRidSet.has(rid)) {
          ElMessage.error(`订单号重复：${rid}`)
          return
        }
        localRidSet.add(rid)
      }
      await ElMessageBox.confirm(
        `确认下发并拆分预报单 ${row.forecastRid} 吗？`,
        '提示',
        {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        }
      )
      const response = await axios.post(`${this.$apiBaseUrl}/forecastsheet/dispatch`, {
        forecastSheetId: row.forecastSheetId,
        staffId: Number(this.staffId),
        startDate: this.dispatchForm.startDate,
        endDate: this.dispatchForm.endDate,
        orderRidMappings: (this.dispatchOrderRidRows || []).map((item) => ({
          groupKey: item.groupKey,
          shoeRid: item.shoeRid,
          orderRid: String(item.orderRid || '').trim()
        }))
      })
      const createdIds = response.data?.createdOrderIds || []
      const createdRids = response.data?.createdOrderRids || []
      const createdCount = Array.isArray(createdIds)
        ? createdIds.length
        : (Array.isArray(createdRids) ? createdRids.length : 0)
      ElMessage.success(`下发成功，已拆分 ${createdCount} 个订单`)
      this.dispatchDialogVisible = false
      await this.loadForecastSheets()
    },

    openPackagingUploadDialog(row) {
      if (!row?.forecastSheetId) return
      this.packagingUploadTarget = row
      this.selectedPackagingFile = null
      this.packagingUploadDialogVisible = true
      this.$nextTick(() => {
        if (this.$refs.forecastPackagingUpload?.clearFiles) {
          this.$refs.forecastPackagingUpload.clearFiles()
        }
      })
    },
    handlePackagingFileExceed() {
      ElMessage.warning('一次仅允许上传一个文件')
    },
    handlePackagingFileChange(file) {
      this.selectedPackagingFile = file?.raw || null
    },
    handlePackagingFileRemove() {
      this.selectedPackagingFile = null
    },
    beforePackagingUpload(file) {
      const name = String(file?.name || '').toLowerCase()
      if (!(name.endsWith('.xlsx') || name.endsWith('.xls'))) {
        ElMessage.error('仅支持 .xls/.xlsx 文件')
        return false
      }
      return true
    },
    submitPackagingUpload() {
      if (!this.packagingUploadTarget?.forecastSheetId) {
        ElMessage.error('未选择预报单')
        return
      }
      if (!this.selectedPackagingFile) {
        ElMessage.warning('请先选择文件')
        return
      }
      const uploader = this.$refs.forecastPackagingUpload
      if (!uploader) return
      uploader.submit()
    },
    async uploadForecastPackagingFile(uploadRequest) {
      if (!this.packagingUploadTarget?.forecastSheetId) {
        uploadRequest.onError(new Error('未选择预报单'))
        return
      }
      this.packagingUploadSubmitting = true
      try {
        const formData = new FormData()
        formData.append('file', uploadRequest.file)
        formData.append('forecastSheetId', this.packagingUploadTarget.forecastSheetId)
        await axios.post(`${this.$apiBaseUrl}/forecastsheet/submitpackaging`, formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        })
        uploadRequest.onSuccess({ message: 'ok' })
        ElMessage.success('包装资料上传成功')
        this.packagingUploadDialogVisible = false
        await this.loadForecastSheets()
      } catch (error) {
        uploadRequest.onError(error)
        const message = error?.response?.data?.error || error?.response?.data?.message || '包装资料上传失败'
        ElMessage.error(message)
      } finally {
        this.packagingUploadSubmitting = false
      }
    }
  }
}
</script>

<style scoped>
.forecast-op-wrap {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: center;
}
</style>
