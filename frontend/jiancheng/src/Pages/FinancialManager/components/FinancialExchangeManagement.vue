<template>
    <div class="financial-exchange">
        <el-card shadow="hover">
            <div class="card-header">
                <div class="title">汇率管理（按月）</div>
                <div class="actions">
                    <span class="base-currency">基础货币：{{ baseCurrencyLabel }}</span>
                    <el-date-picker
                        v-model="selectedMonth"
                        type="month"
                        value-format="YYYY-MM"
                        placeholder="选择月份"
                        style="width: 160px"
                        @change="onMonthChange"
                    />
                    <el-button size="small" :loading="loading" @click="refreshData">刷新</el-button>
                </div>
            </div>

            <el-table :data="conversions" v-loading="loading">
                <el-table-column label="目标货币" min-width="140">
                    <template #default="scope">
                        {{ scope.row.unitToNameCn }} ({{ scope.row.unitToNameEn }})
                    </template>
                </el-table-column>
                <el-table-column label="人民币兑目标汇率" min-width="160">
                    <template #default="scope">
                        <span v-if="scope.row.rate !== null">{{ scope.row.rate }}</span>
                        <span v-else class="placeholder">--</span>
                    </template>
                </el-table-column>
                <el-table-column label="汇率来源" min-width="140">
                    <template #default="scope">
                        <template v-if="scope.row.rate !== null">
                            <el-tag v-if="scope.row.inherited" type="warning" size="small">
                                沿用 {{ scope.row.rateYear }}-{{ String(scope.row.rateMonth).padStart(2, '0') }}
                            </el-tag>
                            <el-tag v-else type="success" size="small">本月填写</el-tag>
                        </template>
                        <span v-else class="placeholder">--</span>
                    </template>
                </el-table-column>
                <el-table-column label="启用" width="80">
                    <template #default="scope">
                        <el-tag :type="scope.row.rateActive ? 'success' : 'info'" size="small">
                            {{ scope.row.rateActive ? '启用' : '停用' }}
                        </el-tag>
                    </template>
                </el-table-column>
                <el-table-column label="操作" width="180">
                    <template #default="scope">
                        <el-button type="primary" link size="small" @click="openEdit(scope.row)">
                            {{ scope.row.inherited || scope.row.rate === null ? '填写本月' : '编辑' }}
                        </el-button>
                        <el-button
                            v-if="!scope.row.inherited && scope.row.rate !== null"
                            type="danger" link size="small"
                            @click="handleDelete(scope.row)"
                        >删除</el-button>
                    </template>
                </el-table-column>
            </el-table>
        </el-card>

        <el-dialog v-model="editDialogVisible" :title="editDialogTitle" width="420px">
            <el-form label-width="100px">
                <el-form-item label="目标货币">
                    <span>{{ editForm.unitToLabel }}</span>
                </el-form-item>
                <el-form-item label="月份">
                    <span>{{ currentYear }}-{{ String(currentMonth).padStart(2, '0') }}</span>
                </el-form-item>
                <el-form-item label="汇率">
                    <el-input-number v-model="editForm.rate" :precision="4" :step="0.0001" :min="0" />
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
import { ElMessage, ElMessageBox } from 'element-plus'

interface CurrencyUnit {
    unitId: number
    unitNameEn: string
    unitNameCn: string
}

interface ConversionRow {
    conversionId: number | null
    unitFrom: number
    unitTo: number
    rate: number | null
    rateYear: number | null
    rateMonth: number | null
    rateActive: boolean
    inherited: boolean
    unitToNameEn: string
    unitToNameCn: string
}

const { appContext } = getCurrentInstance()!
const $api_baseUrl = appContext.config.globalProperties.$apiBaseUrl

const loading = ref(false)
const saving = ref(false)
const editDialogVisible = ref(false)

const currencyUnits = ref<CurrencyUnit[]>([])
const conversions = ref<ConversionRow[]>([])
const baseUnitId = ref<number | null>(null)

const now = new Date()
const selectedMonth = ref(`${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`)

const currentYear = computed(() => parseInt(selectedMonth.value.split('-')[0]))
const currentMonth = computed(() => parseInt(selectedMonth.value.split('-')[1]))

const editForm = ref({
    unitTo: 0,
    unitToLabel: '',
    rate: 0 as number | null,
    rateActive: true,
})

const editDialogTitle = computed(() => {
    return `${currentYear.value}-${String(currentMonth.value).padStart(2, '0')} 汇率`
})

const baseCurrencyLabel = computed(() => {
    const baseUnit = currencyUnits.value.find((unit) => unit.unitId === baseUnitId.value)
    if (!baseUnit) return '未设置'
    return `${baseUnit.unitNameCn} (${baseUnit.unitNameEn})`
})

onMounted(() => {
    refreshData()
})

function onMonthChange() {
    if (baseUnitId.value) fetchConversions()
}

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
        const rmbUnit = currencyUnits.value.find(
            (unit) => unit.unitNameCn === '人民币' || unit.unitNameEn.toUpperCase() === 'CNY'
        )
        baseUnitId.value = rmbUnit?.unitId || currencyUnits.value[0]?.unitId || null
    }
}

async function fetchConversions() {
    loading.value = true
    try {
        const res = await axios.get(`${$api_baseUrl}/accounting/currency_conversions`, {
            params: {
                baseUnitId: baseUnitId.value,
                year: currentYear.value,
                month: currentMonth.value,
            },
        })
        conversions.value = res.data?.conversions || []
        if (res.data?.baseUnitId) {
            baseUnitId.value = res.data.baseUnitId
        }
    } catch (error: any) {
        const message = error?.response?.data?.message || error?.message || '加载汇率信息失败'
        ElMessage.error(message)
    } finally {
        loading.value = false
    }
}

function openEdit(row: ConversionRow) {
    editForm.value = {
        unitTo: row.unitTo,
        unitToLabel: `${row.unitToNameCn} (${row.unitToNameEn})`,
        rate: row.rate ?? 0,
        rateActive: row.rateActive ?? true,
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
            rateYear: currentYear.value,
            rateMonth: currentMonth.value,
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

async function handleDelete(row: ConversionRow) {
    if (!row.conversionId) return
    try {
        await ElMessageBox.confirm(
            `确定删除 ${row.unitToNameCn} ${currentYear.value}-${String(currentMonth.value).padStart(2, '0')} 的汇率记录吗？删除后将沿用上月汇率。`,
            '确认删除',
            { type: 'warning' }
        )
        await axios.delete(`${$api_baseUrl}/accounting/currency_conversion/${row.conversionId}`)
        ElMessage.success('已删除')
        await fetchConversions()
    } catch {
        // 用户取消
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
    flex-wrap: wrap;
    gap: 8px;
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