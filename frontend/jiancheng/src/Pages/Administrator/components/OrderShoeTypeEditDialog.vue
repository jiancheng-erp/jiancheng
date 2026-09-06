<template>
    <el-dialog :model-value="modelValue" title="修改订单鞋型信息" width="1100px" top="5vh"
        :close-on-click-modal="false" @update:model-value="handleVisibleChange" @open="handleOpen">
        <div v-loading="loading">
            <el-descriptions :column="3" border size="small" style="margin-bottom: 16px">
                <el-descriptions-item label="订单号">{{ orderInfo.orderRid }}</el-descriptions-item>
                <el-descriptions-item label="客人名称">{{ orderInfo.customerName }}</el-descriptions-item>
            </el-descriptions>

            <el-alert type="info" :closable="false" show-icon style="margin-bottom: 16px"
                title="修改鞋型颜色只会影响当前订单，不会影响其他订单。" />

            <div class="packaging-block">
                <span class="packaging-label">包装资料：</span>
                <el-tag v-if="orderInfo.packagingDocExists" type="success" size="small">已上传</el-tag>
                <el-tag v-else type="info" size="small">未上传</el-tag>
                <el-button v-if="orderInfo.packagingDocExists" size="small" text type="primary"
                    @click="downloadPackaging">下载</el-button>
                <el-upload :show-file-list="false" :http-request="handlePackagingUpload" accept=".xlsx,.xls,.pdf"
                    style="display: inline-block; margin-left: 8px">
                    <el-button size="small" type="primary" :loading="uploadingPackaging">替换包装资料</el-button>
                </el-upload>
                <span class="packaging-tip">支持 xlsx、xls、pdf 格式</span>
            </div>

            <div v-for="shoe in orderInfo.orderShoes" :key="shoe.orderShoeId" class="shoe-block">
                <div class="shoe-header">
                    <span class="shoe-title">工厂型号：{{ shoe.shoeRid }}</span>
                    <div class="customer-product">
                        <span>客户型号：</span>
                        <el-input class="u-w-220" v-model="shoe.customerProductName" size="small" clearable />
                    </div>
                </div>

                <div v-for="st in shoe.shoeTypes" :key="st.orderShoeTypeId" class="shoe-type-block">
                    <el-row :gutter="16" align="middle" style="margin-bottom: 10px">
                        <el-col :span="6">
                            <div class="field-label">颜色</div>
                            <div style="display: flex; gap: 4px">
                                <el-select v-model="st.colorId" filterable placeholder="选择颜色" size="small"
                                    style="flex: 1">
                                    <el-option v-for="c in colorOptions" :key="c.value" :label="c.label"
                                        :value="c.value" />
                                </el-select>
                                <el-button size="small" @click="openNewColorDialog(st)">新建</el-button>
                            </div>
                        </el-col>
                        <el-col :span="6">
                            <div class="field-label">客户颜色名</div>
                            <el-input v-model="st.customerColorName" size="small" clearable />
                        </el-col>
                        <el-col :span="6">
                            <div class="field-label">单价</div>
                            <el-input-number v-model="st.unitPrice" :min="0" :precision="4" :step="0.1"
                                controls-position="right" size="small" style="width: 100%" />
                        </el-col>
                        <el-col :span="6">
                            <div class="field-label">币种</div>
                            <el-select v-model="st.currencyType" filterable allow-create default-first-option
                                placeholder="币种" size="small" style="width: 100%">
                                <el-option v-for="cur in currencyOptions" :key="cur" :label="cur" :value="cur" />
                            </el-select>
                        </el-col>
                    </el-row>

                    <el-table :data="st.batchInfoList" border size="small" style="width: 100%">
                        <el-table-column label="配码名称" prop="name" width="120" fixed />
                        <el-table-column v-for="size in sizeList" :key="size" :label="String(size)" width="72">
                            <template #default="scope">
                                <el-input-number v-model="scope.row[`size${size}Amount`]" :min="0" :controls="false"
                                    size="small" style="width: 100%"
                                    @change="recalcBatch(scope.row, st.unitPrice)" />
                            </template>
                        </el-table-column>
                        <el-table-column label="总数量" width="90">
                            <template #default="scope">{{ scope.row.totalAmount }}</template>
                        </el-table-column>
                        <el-table-column label="金额" width="120">
                            <template #default="scope">{{ formatMoney(scope.row.totalPrice) }}</template>
                        </el-table-column>
                    </el-table>
                </div>
            </div>
        </div>

        <template #footer>
            <el-button @click="handleVisibleChange(false)">取消</el-button>
            <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
        </template>
    </el-dialog>

    <el-dialog v-model="newColorDialogVisible" title="新建颜色" width="420px" append-to-body
        :close-on-click-modal="false">
        <el-form label-width="90px">
            <el-form-item label="颜色名称" required>
                <el-input v-model="newColorForm.colorName" placeholder="中文颜色名（必填）" clearable />
            </el-form-item>
            <el-form-item label="英文名">
                <el-input v-model="newColorForm.colorNameEN" placeholder="选填" clearable />
            </el-form-item>
            <el-form-item label="西班牙文名">
                <el-input v-model="newColorForm.colorNameSP" placeholder="选填" clearable />
            </el-form-item>
            <el-form-item label="意大利文名">
                <el-input v-model="newColorForm.colorNameIT" placeholder="选填" clearable />
            </el-form-item>
        </el-form>
        <template #footer>
            <el-button @click="newColorDialogVisible = false">取消</el-button>
            <el-button type="primary" :loading="creatingColor" @click="submitNewColor">确定</el-button>
        </template>
    </el-dialog>
</template>

<script>
import axios from 'axios'
import { ElMessage } from 'element-plus'

export default {
    name: 'OrderShoeTypeEditDialog',
    props: {
        modelValue: {
            type: Boolean,
            default: false,
        },
        orderId: {
            type: [Number, String],
            default: null,
        },
    },
    emits: ['update:modelValue', 'saved'],
    data() {
        return {
            loading: false,
            saving: false,
            uploadingPackaging: false,
            orderInfo: {
                orderRid: '',
                customerName: '',
                packagingDocExists: false,
                orderShoes: [],
            },
            colorOptions: [],
            currencyOptions: ['RMB', 'USD', 'EUR'],
            sizeList: Array.from({ length: 13 }, (_, i) => 34 + i),
            newColorDialogVisible: false,
            creatingColor: false,
            activeColorTarget: null,
            newColorForm: {
                colorName: '',
                colorNameEN: '',
                colorNameSP: '',
                colorNameIT: '',
            },
        }
    },
    methods: {
        async handleOpen() {
            if (!this.orderId) {
                return
            }
            this.loading = true
            try {
                await this.getColorOptions()
                await this.getDetail()
            } finally {
                this.loading = false
            }
        },
        async getColorOptions() {
            try {
                const response = await axios.get(`${this.$apiBaseUrl}/general/allcolors`)
                this.colorOptions = response.data || []
            } catch (error) {
                console.error('获取颜色列表失败:', error)
            }
        },
        async getDetail() {
            try {
                const response = await axios.get(`${this.$apiBaseUrl}/order/getordershoetypeeditinfo`, {
                    params: { orderId: this.orderId },
                })
                this.orderInfo = response.data
            } catch (error) {
                console.error('获取订单鞋型信息失败:', error)
                ElMessage.error('获取订单鞋型信息失败')
            }
        },
        openNewColorDialog(st) {
            this.activeColorTarget = st
            this.newColorForm = {
                colorName: '',
                colorNameEN: '',
                colorNameSP: '',
                colorNameIT: '',
            }
            this.newColorDialogVisible = true
        },
        async submitNewColor() {
            const colorName = (this.newColorForm.colorName || '').trim()
            if (!colorName) {
                ElMessage.warning('请填写颜色名称')
                return
            }
            this.creatingColor = true
            try {
                await axios.post(`${this.$apiBaseUrl}/general/addnewcolor`, {
                    colorName,
                    colorNameEN: this.newColorForm.colorNameEN,
                    colorNameSP: this.newColorForm.colorNameSP,
                    colorNameIT: this.newColorForm.colorNameIT,
                })
                ElMessage.success('颜色创建成功')
                await this.selectColorByName(colorName)
                this.newColorDialogVisible = false
            } catch (error) {
                // 后端对重复颜色返回 500，此时直接选中已存在的同名颜色
                const msg = error?.response?.data?.message
                if (msg === 'duplicate color') {
                    await this.selectColorByName(colorName)
                    if (this.activeColorTarget && this.activeColorTarget.colorId) {
                        ElMessage.info('该颜色已存在，已为您选中')
                        this.newColorDialogVisible = false
                        return
                    }
                }
                ElMessage.error('颜色创建失败')
            } finally {
                this.creatingColor = false
            }
        },
        async selectColorByName(colorName) {
            await this.getColorOptions()
            const found = this.colorOptions.find((c) => c.label === colorName)
            if (found && this.activeColorTarget) {
                this.activeColorTarget.colorId = found.value
            }
        },
        downloadPackaging() {
            window.open(`${this.$apiBaseUrl}/order/downloadpackagingdoc?orderId=${this.orderId}`)
        },
        async handlePackagingUpload({ file }) {
            const formData = new FormData()
            formData.append('file', file)
            formData.append('orderId', this.orderId)
            this.uploadingPackaging = true
            try {
                await axios.post(`${this.$apiBaseUrl}/order/uploadpackagingdoc`, formData, {
                    headers: { 'Content-Type': 'multipart/form-data' },
                })
                ElMessage.success('包装资料替换成功')
                this.orderInfo.packagingDocExists = true
            } catch (error) {
                const msg = error?.response?.data?.message || '包装资料替换失败'
                ElMessage.error(msg)
            } finally {
                this.uploadingPackaging = false
            }
        },
        recalcBatch(row, unitPrice) {
            let total = 0
            for (const size of this.sizeList) {
                total += Number(row[`size${size}Amount`]) || 0
            }
            row.totalAmount = total
            row.totalPrice = total * (Number(unitPrice) || 0)
        },
        formatMoney(value) {
            const num = Number(value) || 0
            return num.toFixed(2)
        },
        handleVisibleChange(value) {
            this.$emit('update:modelValue', value)
        },
        async handleSave() {
            const payload = {
                orderShoes: [],
                shoeTypes: [],
            }
            for (const shoe of this.orderInfo.orderShoes) {
                payload.orderShoes.push({
                    orderShoeId: shoe.orderShoeId,
                    customerProductName: shoe.customerProductName,
                })
                for (const st of shoe.shoeTypes) {
                    payload.shoeTypes.push({
                        orderShoeTypeId: st.orderShoeTypeId,
                        colorId: st.colorId,
                        customerColorName: st.customerColorName,
                        unitPrice: st.unitPrice,
                        currencyType: st.currencyType,
                        batchInfoList: st.batchInfoList.map((b) => {
                            const item = { orderShoeBatchInfoId: b.orderShoeBatchInfoId }
                            for (const size of this.sizeList) {
                                item[`size${size}Amount`] = Number(b[`size${size}Amount`]) || 0
                            }
                            return item
                        }),
                    })
                }
            }
            this.saving = true
            try {
                await axios.post(`${this.$apiBaseUrl}/order/updateordershoetypeeditinfo`, payload)
                ElMessage.success('修改成功')
                this.$emit('saved')
                this.handleVisibleChange(false)
            } catch (error) {
                const msg = error?.response?.data?.message || '修改失败'
                ElMessage.error(msg)
            } finally {
                this.saving = false
            }
        },
    },
}
</script>

<style scoped>
.packaging-block {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 16px;
}

.packaging-label {
    font-weight: 600;
    font-size: 14px;
}

.packaging-tip {
    font-size: 12px;
    color: var(--color-text-3);
    margin-left: 4px;
}

.shoe-block {
    border: 1px solid var(--el-border-color-lighter);
    border-radius: 6px;
    padding: 12px 16px;
    margin-bottom: 16px;
}

.shoe-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 12px;
}

.shoe-title {
    font-weight: 600;
    font-size: 15px;
}

.customer-product {
    display: flex;
    align-items: center;
    gap: 6px;
}

.shoe-type-block {
    border-top: 1px dashed var(--el-border-color-lighter);
    padding-top: 12px;
    margin-top: 12px;
}

.field-label {
    font-size: 12px;
    color: var(--color-text-3);
    margin-bottom: 4px;
}
</style>
