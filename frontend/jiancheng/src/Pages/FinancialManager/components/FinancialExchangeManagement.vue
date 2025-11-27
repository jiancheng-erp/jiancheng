<template>
    <div class="financial-exchange">
        <el-card shadow="hover">
            <div class="card-header">
                <div class="title">汇率管理</div>
                <div class="actions">
                    <span class="base-currency">基础货币：{{ baseCurrencyLabel }}</span>
                    <el-button size="small" :loading="loading" @click="refreshData">刷新</el-button>
                </div>
            </div>

            <el-table :data="displayRows" v-loading="loading">
                <el-table-column prop="unitName" label="目标货币"></el-table-column>
                <el-table-column prop="rate" label="人民币兑目标汇率">
                    <template #default="scope">
                        <span v-if="scope.row.rate !== null">{{ scope.row.rate }}</span>
                        <span v-else class="placeholder">--</span>
                    </template>
                </el-table-column>
                <el-table-column prop="rateDate" label="汇率日期">
                    <template #default="scope">
                        <span v-if="scope.row.rateDate">{{ scope.row.rateDate }}</span>
                        <span v-else class="placeholder">--</span>
                    </template>
                </el-table-column>
                <el-table-column prop="rateActive" label="启用">
                    <template #default="scope">
                        <el-tag :type="scope.row.rateActive ? 'success' : 'info'">
                            {{ scope.row.rateActive ? '启用' : '停用' }}
                        </el-tag>
                    </template>
                </el-table-column>
                <el-table-column label="操作" width="140">
                    <template #default="scope">
                        <el-button type="primary" link size="small" @click="openEdit(scope.row)">编辑</el-button>
                    </template>
                </el-table-column>
            </el-table>
        </el-card>

        <el-dialog v-model="editDialogVisible" title="编辑汇率" width="420px">
            <el-form label-width="100px">
                <el-form-item label="目标货币">
                    <el-select v-model="editForm.unitTo" placeholder="选择目标货币" filterable>
                        <el-option
                            v-for="unit in selectableUnits"
                            :key="unit.unitId"
                            :label="`${unit.unitNameCn} (${unit.unitNameEn})`"
                            :value="unit.unitId"
                        />
                    </el-select>
                </el-form-item>
                <el-form-item label="汇率">
                    <el-input-number v-model="editForm.rate" :precision="4" :step="0.0001" :min="0" />
                </el-form-item>
                <el-form-item label="汇率日期">
                    <el-date-picker
                        v-model="editForm.rateDate"
                        type="date"
                        value-format="YYYY-MM-DD"
                        placeholder="选择日期"
                        style="width: 100%"
                    />
                </el-form-item>
                <el-form-item label="是否启用">
                    <el-switch v-model="editForm.rateActive" />
                </el-form-item>
            </el-form>
            <template #footer>
                <el-button @click="editDialogVisible = false">取消</el-button>
                <el-button type="primary" :loading="saving" @click="saveConversion">保存</el-button>
            </template>
        </el-dialog>
    </div>
</template>

<script setup lang="ts">
import { computed, getCurrentInstance, onMounted, ref } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'

interface CurrencyUnit {
    unitId: number
    unitNameEn: string
    unitNameCn: string
}

interface ConversionRow {
    conversionId?: number
    unitFrom: number
    unitTo: number
    rate: number | null
    rateDate?: string
    rateActive?: boolean
}

const { appContext } = getCurrentInstance()
const $api_baseUrl = appContext.config.globalProperties.$apiBaseUrl

const loading = ref(false)
const saving = ref(false)
const editDialogVisible = ref(false)

const currencyUnits = ref<CurrencyUnit[]>([])
const conversions = ref<ConversionRow[]>([])
const baseUnitId = ref<number | null>(null)

const editForm = ref<ConversionRow>({
    conversionId: undefined,
    unitFrom: 0,
    unitTo: 0,
    rate: null,
    rateDate: '',
    rateActive: true,
})

const selectableUnits = computed(() => currencyUnits.value.filter((unit) => unit.unitId !== baseUnitId.value))

const baseCurrencyLabel = computed(() => {
    const baseUnit = currencyUnits.value.find((unit) => unit.unitId === baseUnitId.value)
    if (!baseUnit) return '未设置'
    return `${baseUnit.unitNameCn} (${baseUnit.unitNameEn})`
})

const displayRows = computed(() => {
    return selectableUnits.value.map((unit) => {
        const existing = conversions.value.find((item) => item.unitTo === unit.unitId)
        return {
            unitId: unit.unitId,
            unitName: `${unit.unitNameCn} (${unit.unitNameEn})`,
            rate: existing?.rate ?? null,
            rateDate: existing?.rateDate ?? '',
            rateActive: existing?.rateActive ?? false,
            conversionId: existing?.conversionId,
        }
    })
})

onMounted(() => {
    refreshData()
})

async function refreshData() {
    loading.value = true
    try {
        await fetchUnits()
        if (baseUnitId.value) {
            await fetchConversions()
        }
    } catch (error: any) {
        const message = error?.response?.data?.message || error?.message || '加载汇率信息失败'
        ElMessage.error(message)
    } finally {
        loading.value = false
    }
}

async function fetchUnits() {
    const res = await axios.get(`${$api_baseUrl}/accounting/currency_units`)
    currencyUnits.value = res.data?.units || []

    if (!baseUnitId.value) {
        const rmbUnit = currencyUnits.value.find((unit) => unit.unitNameCn === '人民币' || unit.unitNameEn.toUpperCase() === 'CNY')
        baseUnitId.value = rmbUnit?.unitId || currencyUnits.value[0]?.unitId || null
    }
}

async function fetchConversions() {
    const res = await axios.get(`${$api_baseUrl}/accounting/currency_conversions`, {
        params: { baseUnitId: baseUnitId.value },
    })
    conversions.value = res.data?.conversions || []
    if (res.data?.baseUnitId) {
        baseUnitId.value = res.data.baseUnitId
    }
}

function openEdit(row: { unitId: number; rate: number | null; rateDate: string; rateActive: boolean; conversionId?: number }) {
    editForm.value = {
        conversionId: row.conversionId,
        unitFrom: baseUnitId.value || 0,
        unitTo: row.unitId,
        rate: row.rate ?? 0,
        rateDate: row.rateDate || '',
        rateActive: row.rateActive ?? false,
    }
    editDialogVisible.value = true
}

async function saveConversion() {
    if (!editForm.value.unitTo) {
        ElMessage.warning('请选择目标货币')
        return
    }
    saving.value = true
    try {
        await axios.post(`${$api_baseUrl}/accounting/currency_conversion`, {
            unitFrom: baseUnitId.value,
            unitTo: editForm.value.unitTo,
            rate: editForm.value.rate,
            rateDate: editForm.value.rateDate,
            rateActive: editForm.value.rateActive,
        })
        ElMessage.success('汇率已保存')
        editDialogVisible.value = false
        await fetchConversions()
    } catch (error: any) {
        const message = error?.response?.data?.message || error?.message || '保存汇率失败'
        ElMessage.error(message)
    } finally {
        saving.value = false
    }
}
</script>

<style scoped>
.financial-exchange {
    display: flex;
    flex-direction: column;
    gap: 16px;
}

.card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
}

.title {
    font-size: 18px;
    font-weight: 600;
}

.actions {
    display: flex;
    align-items: center;
    gap: 12px;
    color: #606266;
}

.base-currency {
    font-size: 14px;
}

.placeholder {
    color: #c0c4cc;
}
</style>