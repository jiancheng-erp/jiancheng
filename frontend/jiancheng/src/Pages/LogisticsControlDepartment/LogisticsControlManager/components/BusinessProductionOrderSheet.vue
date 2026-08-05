<template>
    <div class="sheet-page">
        <div class="toolbar">
            <el-button @click="$emit('back')">返回列表</el-button>
            <el-dropdown trigger="click" @command="downloadExcel">
                <el-button type="success" :loading="loading">下载Excel</el-button>
                <template #dropdown>
                    <el-dropdown-menu>
                        <el-dropdown-item command="notice">生产通知单</el-dropdown-item>
                        <el-dropdown-item command="craft">工艺单</el-dropdown-item>
                    </el-dropdown-menu>
                </template>
            </el-dropdown>
        </div>

        <el-tabs v-model="activeTab" class="sheet-tabs">
            <el-tab-pane label="生产通知单" name="notice">
        <div class="order-sheet" v-loading="loading">
            <div class="sheet-title">健诚集团{{ orderData.customerName }}号客人{{ orderData.customerBrand }}生产通知单</div>

            <table class="excel-table info-table">
                <tbody>
                    <tr>
                        <td class="info-label">单号</td>
                        <td class="info-value">{{ orderData.orderRid }}</td>
                        <td class="info-label">下单日期</td>
                        <td class="info-value">{{ orderData.startDate }}</td>
                        <td class="info-label">出货日期</td>
                        <td class="info-value">{{ orderData.endDate }}</td>
                        <td class="info-label">客户订单号</td>
                        <td class="info-value">{{ orderData.orderCid }}</td>
                        <td class="info-label">业务</td>
                        <td class="info-value">{{ orderData.orderStaffName }}</td>
                        <td class="info-label">配码类型</td>
                        <td class="info-value">{{ orderData.batchInfoTypeName }}</td>
                    </tr>
                </tbody>
            </table>

            <table class="excel-table main-table">
                <thead>
                    <tr>
                        <th style="width: 130px">鞋图</th>
                        <th style="width: 90px">工厂款号</th>
                        <th style="width: 100px">客户型号</th>
                        <th style="width: 70px">颜色</th>
                        <th style="width: 90px">客户颜色</th>
                        <th style="width: 170px" v-for="cat in materialColumns" :key="cat.key">{{ cat.label }}</th>
                        <th style="width: 80px">配码</th>
                        <th class="size-col" v-for="s in activeSizes" :key="s.amountKey">{{ s.name }}</th>
                        <th style="width: 55px">对/件</th>
                        <th style="width: 55px">件数</th>
                        <th style="width: 55px">双数</th>
                        <th style="width: 200px">备注</th>
                    </tr>
                </thead>
                <tbody>
                    <template v-for="shoe in orderShoeData" :key="shoe.orderShoeId">
                        <template v-for="(colorType, ci) in shoe.orderShoeTypes" :key="colorType.orderShoeTypeId">
                            <tr v-for="(batch, bi) in colorType.shoeTypeBatchInfoList" :key="`${colorType.orderShoeTypeId}-${bi}`">
                                <td v-if="ci === 0 && bi === 0" :rowspan="shoeRowCount(shoe)" class="img-cell">
                                    <div v-for="ct in shoe.orderShoeTypes" :key="`img-${ct.orderShoeTypeId}`" class="img-wrap">
                                        <el-image
                                            v-if="ct.shoeTypeImgUrl"
                                            :src="ct.shoeTypeImgUrl"
                                            :preview-src-list="[ct.shoeTypeImgUrl]"
                                            fit="contain"
                                            style="width: 120px; height: 80px"
                                        ></el-image>
                                        <span v-else class="no-img">暂无图片</span>
                                    </div>
                                </td>
                                <td v-if="ci === 0 && bi === 0" :rowspan="shoeRowCount(shoe)">{{ shoe.shoeRid }}</td>
                                <td v-if="ci === 0 && bi === 0" :rowspan="shoeRowCount(shoe)">{{ shoe.shoeCid }}</td>
                                <td v-if="bi === 0" :rowspan="colorType.shoeTypeBatchInfoList.length">{{ colorType.shoeTypeColorName }}</td>
                                <td v-if="bi === 0" :rowspan="colorType.shoeTypeBatchInfoList.length">{{ colorType.customerColorName }}</td>
                                <td
                                    v-if="ci === 0 && bi === 0 && getInstruction(shoe.shoeRid).status !== 'exists'"
                                    :rowspan="shoeRowCount(shoe)"
                                    :colspan="materialColumns.length"
                                    class="material-missing-cell"
                                >
                                    <span v-if="getInstruction(shoe.shoeRid).status === 'missing'" class="instruction-missing">投产指令单未创建</span>
                                    <span v-else class="instruction-hint">{{ getInstruction(shoe.shoeRid).status === 'loading' ? '加载中…' : '投产指令单加载失败' }}</span>
                                </td>
                                <template v-if="bi === 0 && getInstruction(shoe.shoeRid).status === 'exists'">
                                    <td
                                        v-for="cat in materialColumns"
                                        :key="cat.key"
                                        :rowspan="colorType.shoeTypeBatchInfoList.length"
                                        class="material-cell"
                                    >
                                        <div
                                            v-for="(m, mi) in getColorMaterials(shoe.shoeRid, colorType.shoeTypeColorName, cat.key)"
                                            :key="mi"
                                            class="material-line"
                                        >
                                            {{ formatMaterial(m) }}
                                        </div>
                                    </td>
                                </template>
                                <td>{{ batch.packagingInfoName }}</td>
                                <td class="size-col" v-for="s in activeSizes" :key="s.amountKey">
                                    {{ batch[s.amountKey] || '' }}
                                </td>
                                <td>{{ batch.totalQuantityRatio }}</td>
                                <td>{{ batch.unitPerRatio }}</td>
                                <td>{{ batch.total }}</td>
                                <td v-if="ci === 0 && bi === 0" :rowspan="shoeRowCount(shoe)" class="remark-cell">
                                    <div v-if="shoe.orderShoeRemarkExist" class="remark-text">{{ shoe.orderShoeRemarkRep }}</div>
                                    <span v-else>--</span>
                                </td>
                            </tr>
                        </template>
                    </template>
                    <tr class="total-row">
                        <td :colspan="5 + materialColumns.length">合计</td>
                        <td></td>
                        <td class="size-col" v-for="s in activeSizes" :key="`total-${s.amountKey}`">{{ sizeTotals[s.amountKey] || '' }}</td>
                        <td></td>
                        <td></td>
                        <td>{{ grandTotalPairs }}</td>
                        <td></td>
                    </tr>
                </tbody>
            </table>
        </div>
            </el-tab-pane>

            <el-tab-pane label="生产订单" name="production">
                <div class="order-sheet" v-loading="loading">
                    <div class="sheet-title">{{ orderData.title || `健诚集团${orderData.customerName || ''}号客人${orderData.customerBrand || ''}生产订单` }}</div>

                    <table class="excel-table info-table">
                        <tbody>
                            <tr>
                                <td class="info-label">单号</td>
                                <td class="info-value">{{ orderData.orderRid }}</td>
                                <td class="info-label">下单日期</td>
                                <td class="info-value">{{ orderData.startDate }}</td>
                                <td class="info-label">出货日期</td>
                                <td class="info-value">{{ orderData.endDate }}</td>
                                <td class="info-label">客户订单号</td>
                                <td class="info-value">{{ orderData.orderCid }}</td>
                                <td class="info-label">业务</td>
                                <td class="info-value">{{ orderData.orderStaffName }}</td>
                            </tr>
                        </tbody>
                    </table>

                    <table class="excel-table main-table">
                        <thead>
                            <tr>
                                <th style="width: 130px">鞋图</th>
                                <th style="width: 90px">工厂型号</th>
                                <th style="width: 100px">客户型号</th>
                                <th style="width: 70px">颜色</th>
                                <th style="width: 90px">客户颜色</th>
                                <th style="width: 90px">配码</th>
                                <th class="size-col" v-for="s in activeSizes" :key="`po-h-${s.amountKey}`">{{ s.name }}</th>
                                <th style="width: 70px">总双数</th>
                                <th style="width: 55px">件数</th>
                                <th style="width: 55px">双数</th>
                                <th style="width: 200px">备注</th>
                            </tr>
                        </thead>
                        <tbody>
                            <template v-for="shoe in orderShoeData" :key="`po-${shoe.orderShoeId}`">
                                <template v-for="(colorType, ci) in shoe.orderShoeTypes" :key="`po-${colorType.orderShoeTypeId}`">
                                    <tr v-for="(batch, bi) in colorType.shoeTypeBatchInfoList" :key="`po-${colorType.orderShoeTypeId}-${bi}`">
                                        <td v-if="bi === 0" :rowspan="colorType.shoeTypeBatchInfoList.length" class="img-cell">
                                            <el-image
                                                v-if="colorType.shoeTypeImgUrl"
                                                :src="colorType.shoeTypeImgUrl"
                                                :preview-src-list="[colorType.shoeTypeImgUrl]"
                                                fit="contain"
                                                style="width: 120px; height: 80px"
                                            ></el-image>
                                            <span v-else class="no-img">暂无图片</span>
                                        </td>
                                        <td v-if="ci === 0 && bi === 0" :rowspan="shoeRowCount(shoe)">{{ shoe.shoeRid }}</td>
                                        <td v-if="ci === 0 && bi === 0" :rowspan="shoeRowCount(shoe)">{{ shoe.shoeCid }}</td>
                                        <td v-if="bi === 0" :rowspan="colorType.shoeTypeBatchInfoList.length">{{ colorType.shoeTypeColorName }}</td>
                                        <td v-if="bi === 0" :rowspan="colorType.shoeTypeBatchInfoList.length">{{ colorType.customerColorName }}</td>
                                        <td>{{ batch.packagingInfoName }}</td>
                                        <td class="size-col" v-for="s in activeSizes" :key="`po-${colorType.orderShoeTypeId}-${bi}-${s.amountKey}`">
                                            {{ batch[s.amountKey] || '' }}
                                        </td>
                                        <td>{{ batch.totalQuantityRatio }}</td>
                                        <td>{{ batch.unitPerRatio }}</td>
                                        <td>{{ batch.total }}</td>
                                        <td v-if="ci === 0 && bi === 0" :rowspan="shoeRowCount(shoe)" class="remark-cell">
                                            <div v-if="shoe.orderShoeRemarkExist" class="remark-text">{{ shoe.orderShoeRemarkRep }}</div>
                                            <span v-else>--</span>
                                        </td>
                                    </tr>
                                </template>
                            </template>
                            <tr class="total-row">
                                <td colspan="6">合计</td>
                                <td class="size-col" v-for="s in activeSizes" :key="`po-total-${s.amountKey}`">{{ sizeTotals[s.amountKey] || '' }}</td>
                                <td></td>
                                <td>{{ productionPieceTotal }}</td>
                                <td>{{ productionPairTotal }}</td>
                                <td></td>
                            </tr>
                        </tbody>
                    </table>

                    <div class="packaging-section">
                        <div class="packaging-header">包装资料</div>
                        <div v-if="orderData.packagingDoc && orderData.packagingDoc.exists" class="packaging-body">
                            <div class="packaging-file-row">
                                <span class="packaging-file-name">{{ orderData.packagingDoc.fileName }}</span>
                                <el-button type="primary" size="small" :loading="packagingDownloading" @click="downloadPackagingDoc">
                                    下载包装资料
                                </el-button>
                            </div>
                            <!-- PDF 内嵌预览 -->
                            <iframe
                                v-if="packagingPreviewUrl"
                                :src="packagingPreviewUrl"
                                class="packaging-preview"
                            ></iframe>
                        </div>
                        <div v-else class="packaging-empty">暂无包装资料</div>
                    </div>
                </div>
            </el-tab-pane>

            <el-tab-pane label="工艺单" name="craft">
                <div class="craft-wrap" v-loading="loading">
                    <div v-if="craftTabs.length === 0" class="craft-empty">
                        暂无工艺单数据（工艺单未创建或加载中）
                    </div>
                    <el-tabs v-else v-model="activeCraftTab" type="card" class="craft-color-tabs">
                    <el-tab-pane v-for="cs in craftTabs" :key="cs.key" :label="cs.label" :name="cs.key" lazy>
                    <div class="craft-sheet">
                        <div class="sheet-title">健诚鞋业工艺生产指令单</div>

                        <table class="excel-table craft-info-table">
                            <tbody>
                                <tr>
                                    <td class="info-label">工厂型号</td>
                                    <td>{{ cs.shoe.shoeRid }}</td>
                                    <td class="info-label">客户型号</td>
                                    <td>{{ cs.shoe.shoeCid }}</td>
                                    <td class="info-label">设计</td>
                                    <td>{{ cs.detail.designer || '--' }}</td>
                                    <td class="craft-img-cell" rowspan="5">
                                        <el-image
                                            v-if="cs.imgUrl"
                                            :src="cs.imgUrl"
                                            :preview-src-list="[cs.imgUrl]"
                                            fit="contain"
                                            style="width: 130px; height: 100px"
                                        ></el-image>
                                        <span v-else class="no-img">暂无图片</span>
                                    </td>
                                </tr>
                                <tr>
                                    <td class="info-label">调版</td>
                                    <td>{{ cs.detail.adjuster || '--' }}</td>
                                    <td class="info-label">刀模</td>
                                    <td>{{ cs.detail.cutDie || '--' }}</td>
                                    <td class="info-label">楦型</td>
                                    <td>{{ cs.lastType || '--' }}</td>
                                </tr>
                                <tr>
                                    <td class="info-label">颜色</td>
                                    <td colspan="5">{{ cs.colorNames.join('、') }}</td>
                                </tr>
                                <tr>
                                    <td class="info-label">配码</td>
                                    <td colspan="3">{{ cs.detail.sizeRange || orderData.batchInfoTypeName || '--' }}</td>
                                    <td class="info-label">订单号</td>
                                    <td>{{ orderData.orderRid }}</td>
                                </tr>
                                <tr>
                                    <td class="info-label">本码</td>
                                    <td>{{ cs.detail.originSize || '--' }}</td>
                                    <td class="info-label">码差</td>
                                    <td>{{ cs.detail.sizeDifference || '--' }}</td>
                                    <td class="info-label">审核人</td>
                                    <td>{{ cs.detail.reviewer || '--' }}</td>
                                </tr>
                            </tbody>
                        </table>

                        <table class="excel-table craft-material-table">
                            <thead>
                                <tr>
                                    <th style="width: 80px">车间</th>
                                    <th style="width: 100px">部件</th>
                                    <th>材料名称</th>
                                    <th>工艺</th>
                                    <th style="width: 70px">双数</th>
                                    <th style="width: 70px">用量</th>
                                </tr>
                            </thead>
                            <tbody>
                                <template v-for="g in cs.groups" :key="g.name">
                                    <tr v-for="(row, ri) in g.rows" :key="`${g.name}-${ri}`">
                                        <td v-if="ri === 0" :rowspan="g.rows.length" class="workshop-cell">{{ g.name }}</td>
                                        <td class="part-cell">{{ row.part }}</td>
                                        <td class="craft-desc-cell">{{ row.desc }}</td>
                                        <td class="craft-name-cell">{{ row.craft }}</td>
                                        <td>{{ row.pairs }}</td>
                                        <td>{{ row.usage }}</td>
                                    </tr>
                                </template>
                            </tbody>
                        </table>

                        <table class="excel-table craft-extra-table">
                            <tbody>
                                <tr v-for="g in cs.groups.filter((x) => x.special)" :key="`sp-${g.name}`">
                                    <td class="info-label">{{ g.name }}特殊工艺</td>
                                    <td colspan="6" class="craft-extra-value">{{ g.special }}</td>
                                </tr>
                                <tr v-if="cs.detail.postProcessing">
                                    <td class="info-label">后处理</td>
                                    <td colspan="6" class="craft-extra-value">{{ cs.detail.postProcessing }}</td>
                                </tr>
                                <tr v-if="cs.detail.oilyGlue">
                                    <td class="info-label">料盆油性胶</td>
                                    <td colspan="6" class="craft-extra-value">{{ cs.detail.oilyGlue }}</td>
                                </tr>
                                <tr v-if="cs.detail.burnSoleCraft">
                                    <td class="info-label">烫底工艺</td>
                                    <td colspan="6" class="craft-extra-value">{{ cs.detail.burnSoleCraft }}</td>
                                </tr>
                                <tr v-if="cs.detail.productionRemark">
                                    <td class="info-label">生产备注</td>
                                    <td colspan="6" class="craft-extra-value">{{ cs.detail.productionRemark }}</td>
                                </tr>
                            </tbody>
                        </table>

                        <div class="craft-image-section">
                            <div class="craft-image-block">
                                <div class="craft-image-title">工艺单图片备注</div>
                                <el-image
                                    v-if="cs.detail.picNoteImgPath"
                                    :src="cs.detail.picNoteImgPath"
                                    :preview-src-list="[cs.detail.picNoteImgPath]"
                                    fit="contain"
                                    class="craft-image-preview"
                                ></el-image>
                                <span v-else class="no-img">暂无工艺单图片备注</span>
                            </div>
                            <div class="craft-image-block">
                                <div class="craft-image-title">刀模图</div>
                                <el-image
                                    v-if="cs.detail.cutDieImgPath"
                                    :src="cs.detail.cutDieImgPath"
                                    :preview-src-list="[cs.detail.cutDieImgPath]"
                                    fit="contain"
                                    class="craft-image-preview"
                                ></el-image>
                                <span v-else class="no-img">暂无刀模图</span>
                            </div>
                        </div>
                    </div>
                    </el-tab-pane>
                    </el-tabs>
                </div>
            </el-tab-pane>
        </el-tabs>
    </div>
</template>

<script setup>
import axios from 'axios'
import { onMounted, ref, reactive, computed, watch, getCurrentInstance } from 'vue'
import { ElMessage } from 'element-plus'
import { exportProductionOrderExcel, exportCraftSheetExcel, buildCraftGroups } from './productionOrderExcel'

const $api_baseUrl = getCurrentInstance().appContext.config.globalProperties.$apiBaseUrl

const props = defineProps(['orderId'])
defineEmits(['back'])

const orderData = ref({})
const orderShoeData = ref([])
const activeSizes = ref([])
const loading = ref(false)
const activeTab = ref('notice')
const activeCraftTab = ref('')
const packagingDownloading = ref(false)
const packagingPreviewUrl = ref('')

// 每个工厂款号(shoeRid)对应的投产指令单状态：loading/exists/missing/error
const instructionMap = reactive({})
// 每个工厂款号(shoeRid)对应的工艺单状态（工艺单页数据来源）
const craftSheetMap = reactive({})

const materialCategories = [
    { key: 'surfaceMaterialData', label: '面料' },
    { key: 'outsoleMaterialData', label: '大底' },
    { key: 'midsoleMaterialData', label: '中底' }
]

function getInstruction(shoeRid) {
    return instructionMap[shoeRid] || { status: 'loading' }
}

// 仅展示实际有数据的材料类别列；全部无数据时兜底展示全部类别以承载"未创建"提示
const materialColumns = computed(() => {
    const present = new Set()
    Object.values(instructionMap).forEach((ins) => {
        if (ins && ins.status === 'exists') {
            ins.colors.forEach((c) => {
                materialCategories.forEach((cat) => {
                    if ((c[cat.key] || []).length > 0) present.add(cat.key)
                })
            })
        }
    })
    const cols = materialCategories.filter((cat) => present.has(cat.key))
    return cols.length > 0 ? cols : materialCategories
})

function getColorMaterials(shoeRid, colorName, key) {
    const ins = instructionMap[shoeRid]
    if (!ins || ins.status !== 'exists') return []
    const colorData = ins.colors.find((c) => c.color === colorName)
    if (!colorData) return []
    return colorData[key] || []
}

function formatMaterial(m) {
    const head = [m.supplierName, m.materialName].filter(Boolean).join(' ')
    const detail = [m.materialModel, m.materialSpecification].filter(Boolean).join('/')
    let line = detail ? `${head}；${detail}` : head
    if (m.processingRemark) line += `（${m.processingRemark}）`
    return line
}

// ---- 工艺单（数据来自工艺单 craftsheet，按车间分组的材料明细） ----
const sizeRangeText = computed(() => {
    const s = activeSizes.value
    if (!s.length) return ''
    return s.length === 1 ? s[0].name : `${s[0].name}-${s[s.length - 1].name}`
})

// 每个鞋款的每个颜色生成一张工艺单，按颜色分tab显示
const craftTabs = computed(() => {
    const tabs = []
    orderShoeData.value.forEach((shoe) => {
        const cs = craftSheetMap[shoe.shoeRid]
        if (!cs || cs.status !== 'exists') return
        const detail = cs.detail || {}
        // 尺码/设计/楦型等工艺单未存储的字段，从投产指令单补齐
        const instrDetail = (instructionMap[shoe.shoeRid] && instructionMap[shoe.shoeRid].detail) || {}
        const colors = cs.colors || []
        if (colors.length === 0) return

        colors.forEach((colorData) => {
            const colorName = colorData.color
            const ct = (shoe.orderShoeTypes || []).find((t) => t.shoeTypeColorName === colorName && t.shoeTypeImgUrl)
            const imgUrl = ct ? ct.shoeTypeImgUrl : ''
            // 楦型：优先取该颜色楦材料名称，否则用投产指令单楦型
            let lastType = instrDetail.lastType || ''
            const lm = (colorData.lastMaterialData || [])[0]
            if (lm && lm.materialName) lastType = lm.materialName

            const groups = buildCraftGroups(colorData, detail)

            const mergedDetail = {
                designer: instrDetail.designer,
                adjuster: detail.adjuster,
                cutDie: detail.cutDie,
                reviewer: detail.reviewer,
                sizeRange: instrDetail.sizeRange || sizeRangeText.value,
                sizeDifference: instrDetail.sizeDifference,
                originSize: instrDetail.originSize,
                burnSoleCraft: instrDetail.burnSoleCraft,
                postProcessing: detail.postProcessing,
                oilyGlue: detail.oilyGlue,
                productionRemark: detail.productionRemark,
                picNoteImgPath: detail.picNoteImgPath,
                cutDieImgPath: detail.cutDieImgPath
            }
            tabs.push({
                key: `${shoe.shoeRid}__${colorName}`,
                label: `${shoe.shoeRid} ${colorName}`,
                shoe,
                colorNames: [colorName],
                detail: mergedDetail,
                imgUrl,
                lastType,
                groups
            })
        })
    })
    return tabs
})

watch(
    craftTabs,
    (tabs) => {
        if (tabs.length && !tabs.some((t) => t.key === activeCraftTab.value)) {
            activeCraftTab.value = tabs[0].key
        }
    },
    { immediate: true }
)


const attrMappingToAmount = {
    size34Name: 'size34Amount',
    size35Name: 'size35Amount',
    size36Name: 'size36Amount',
    size37Name: 'size37Amount',
    size38Name: 'size38Amount',
    size39Name: 'size39Amount',
    size40Name: 'size40Amount',
    size41Name: 'size41Amount',
    size42Name: 'size42Amount',
    size43Name: 'size43Amount',
    size44Name: 'size44Amount',
    size45Name: 'size45Amount',
    size46Name: 'size46Amount'
}

const sizeTotals = computed(() => {
    const totals = {}
    activeSizes.value.forEach((s) => (totals[s.amountKey] = 0))
    orderShoeData.value.forEach((shoe) =>
        (shoe.orderShoeTypes || []).forEach((colorType) =>
            (colorType.shoeTypeBatchInfoList || []).forEach((batch) => {
                activeSizes.value.forEach((s) => {
                    totals[s.amountKey] += Number(batch[s.amountKey]) || 0
                })
            })
        )
    )
    return totals
})

const grandTotalPairs = computed(() => {
    let total = 0
    orderShoeData.value.forEach((shoe) =>
        (shoe.orderShoeTypes || []).forEach((colorType) => {
            total += Number(colorType.shoeTypeBatchData?.totalAmount) || 0
        })
    )
    return total
})

// ---- 生产订单tab（数量订单：各码显示总数量，不含单价/金额）----
const productionPieceTotal = computed(() => {
    let total = 0
    orderShoeData.value.forEach((shoe) =>
        (shoe.orderShoeTypes || []).forEach((colorType) =>
            (colorType.shoeTypeBatchInfoList || []).forEach((batch) => {
                total += Number(batch.unitPerRatio) || 0
            })
        )
    )
    return total
})

const productionPairTotal = computed(() => {
    let total = 0
    orderShoeData.value.forEach((shoe) =>
        (shoe.orderShoeTypes || []).forEach((colorType) =>
            (colorType.shoeTypeBatchInfoList || []).forEach((batch) => {
                total += Number(batch.total) || 0
            })
        )
    )
    return total
})

function shoeRowCount(shoe) {
    return (shoe.orderShoeTypes || []).reduce((sum, colorType) => sum + (colorType.shoeTypeBatchInfoList?.length || 0), 0)
}

onMounted(() => {
    getOrderInfo()
})

async function getOrderInfo() {
    if (!props.orderId) return
    loading.value = true
    try {
        const response = await axios.get(`${$api_baseUrl}/order/getbusinessorderinfo?orderid=${props.orderId}`)
        orderData.value = response.data
        orderShoeData.value = response.data.orderShoeAllData || []
        const batchInfoType = response.data.batchInfoType || {}
        activeSizes.value = Object.keys(attrMappingToAmount)
            .filter((key) => batchInfoType[key] != null && batchInfoType[key] !== '')
            .map((key) => ({
                name: batchInfoType[key],
                amountKey: attrMappingToAmount[key]
            }))
        fetchAllInstructions()
        loadPackagingPreview()
    } catch (error) {
        ElMessage.error('获取生产订单信息失败')
    } finally {
        loading.value = false
    }
}

// 包装资料内嵌预览：仅 PDF 用 iframe，其它格式仅提供下载
async function loadPackagingPreview() {
    if (packagingPreviewUrl.value) {
        window.URL.revokeObjectURL(packagingPreviewUrl.value)
        packagingPreviewUrl.value = ''
    }
    const doc = orderData.value.packagingDoc
    if (!doc || !doc.exists || doc.ext !== '.pdf') return
    try {
        const resp = await axios.get(`${$api_baseUrl}/order/downloadpackagingdoc`, {
            params: { orderId: props.orderId },
            responseType: 'arraybuffer'
        })
        packagingPreviewUrl.value = window.URL.createObjectURL(
            new Blob([resp.data], { type: 'application/pdf' })
        )
    } catch (error) {
        packagingPreviewUrl.value = ''
    }
}

async function downloadPackagingDoc() {
    if (!props.orderId) return
    packagingDownloading.value = true
    try {
        const resp = await axios.get(`${$api_baseUrl}/order/downloadpackagingdoc`, {
            params: { orderId: props.orderId },
            responseType: 'blob'
        })
        const fileName = (orderData.value.packagingDoc && orderData.value.packagingDoc.fileName) || '包装资料'
        const url = window.URL.createObjectURL(new Blob([resp.data]))
        const link = document.createElement('a')
        link.href = url
        link.download = fileName
        document.body.appendChild(link)
        link.click()
        link.remove()
        window.URL.revokeObjectURL(url)
    } catch (error) {
        ElMessage.error('下载包装资料失败')
    } finally {
        packagingDownloading.value = false
    }
}

function fetchAllInstructions() {
    orderShoeData.value.forEach((shoe) => {
        if (!shoe.shoeRid) return
        instructionMap[shoe.shoeRid] = { status: 'loading' }
        fetchInstruction(shoe.shoeRid)
        craftSheetMap[shoe.shoeRid] = { status: 'loading' }
        fetchCraftSheet(shoe.shoeRid)
    })
}

async function fetchCraftSheet(shoeRid) {
    try {
        const response = await axios.get(`${$api_baseUrl}/craftsheet/getcraftsheetinfo`, {
            params: { orderid: orderData.value.orderRid, ordershoeid: shoeRid }
        })
        craftSheetMap[shoeRid] = {
            status: 'exists',
            detail: response.data.craftSheetDetail || {},
            colors: response.data.uploadData || []
        }
    } catch (error) {
        craftSheetMap[shoeRid] = { status: error.response && error.response.status === 404 ? 'missing' : 'error' }
    }
}

async function fetchInstruction(shoeRid) {
    try {
        const response = await axios.get(`${$api_baseUrl}/devproductionorder/getproductioninstruction`, {
            params: { orderid: orderData.value.orderRid, ordershoeid: shoeRid }
        })
        const colors = response.data.instructionData || []
        instructionMap[shoeRid] = {
            status: 'exists',
            detail: response.data.productionInstructionDetail || {},
            colors
        }
    } catch (error) {
        if (error.response && error.response.status === 404) {
            instructionMap[shoeRid] = { status: 'missing' }
        } else {
            instructionMap[shoeRid] = { status: 'error' }
        }
    }
}

// 导出：按命令区分生产通知单 / 工艺单
async function downloadExcel(type = 'notice') {
    try {
        if (type === 'craft') {
            await exportCraftSheetExcel($api_baseUrl, props.orderId)
        } else {
            await exportProductionOrderExcel($api_baseUrl, props.orderId)
        }
    } catch (error) {
        ElMessage.error(type === 'craft' ? '导出工艺单 Excel 失败' : '导出生产通知单 Excel 失败')
    }
}
</script>

<style scoped>
.sheet-page {
    width: 100%;
}

.packaging-section {
    margin-top: 24px;
    border-top: 1px dashed #d5d8dd;
    padding-top: 16px;
}

.packaging-header {
    font-size: 16px;
    font-weight: 700;
    color: #1f2d3d;
    margin-bottom: 12px;
}

.packaging-file-row {
    display: flex;
    align-items: center;
    gap: 12px;
}

.packaging-file-name {
    font-size: 14px;
    color: #303133;
}

.packaging-preview {
    width: 100%;
    height: 600px;
    margin-top: 12px;
    border: 1px solid #d5d8dd;
    border-radius: 8px;
}

.packaging-empty {
    font-size: 14px;
    color: #909399;
}

.toolbar {
    margin-bottom: 16px;
    display: flex;
    gap: 10px;
}

.order-sheet {
    background: #ffffff;
    border-radius: 12px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
    padding: 24px 28px 30px;
    overflow-x: auto;
}

.sheet-title {
    text-align: center;
    font-size: 23px;
    font-weight: 700;
    letter-spacing: 3px;
    color: #1f2d3d;
    padding: 4px 0 20px;
}

.sheet-title::after {
    content: '';
    display: block;
    width: 90px;
    height: 3px;
    margin: 12px auto 0;
    background: linear-gradient(90deg, #409eff, #66b1ff);
    border-radius: 2px;
}

.excel-table {
    border-collapse: collapse;
    width: 100%;
    table-layout: fixed;
    font-size: 13px;
    color: #303133;
}

.excel-table th,
.excel-table td {
    border: 1px solid #d5d8dd;
    padding: 6px 6px;
    text-align: center;
    vertical-align: middle;
    word-break: break-word;
}

.excel-table th {
    background: linear-gradient(180deg, #f7f9fc, #eaeef4);
    font-weight: 600;
    color: #1f2d3d;
}

.info-table {
    margin-bottom: -1px;
}

.info-table .info-label {
    background: #eef4ff;
    color: #3a7bd5;
    font-weight: 600;
    width: 80px;
    white-space: nowrap;
}

.info-table .info-value {
    white-space: nowrap;
    color: #303133;
}

.main-table thead th {
    position: sticky;
    top: 0;
    z-index: 2;
}

.main-table .size-col {
    width: 44px;
    background: #fbfcfe;
}

.main-table tbody tr:hover td {
    background: #f2f8ff;
}

.img-cell {
    padding: 6px;
    background: #fff;
}

.img-cell .img-wrap {
    display: flex;
    justify-content: center;
    align-items: center;
    padding: 3px 0;
}

.no-img {
    color: #909399;
    font-size: 12px;
}

.total-row td {
    font-weight: 700;
    background: #f5f7fa;
}

.remark-cell .remark-text {
    white-space: pre-line;
    text-align: left;
}

.instruction-missing {
    color: #f56c6c;
    font-weight: 600;
    padding: 6px 0;
}

.instruction-hint {
    color: #909399;
    padding: 6px 0;
}

.material-cell {
    text-align: left;
    vertical-align: top;
    font-size: 12px;
    line-height: 1.5;
}

.material-line {
    padding: 1px 0;
    word-break: break-word;
}

.material-missing-cell {
    color: #f56c6c;
    font-weight: 600;
}

/* ---- 工艺单 ---- */
.craft-wrap {
    display: flex;
    flex-direction: column;
    gap: 30px;
}

.craft-empty {
    text-align: center;
    color: #909399;
    padding: 40px 0;
    background: #ffffff;
    border-radius: 12px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
}

.craft-sheet {
    background: #ffffff;
    border-radius: 12px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
    padding: 24px 28px 30px;
    overflow-x: auto;
}

.craft-info-table {
    margin-bottom: -1px;
}

.craft-info-table .info-label {
    background: #eef4ff;
    color: #3a7bd5;
    font-weight: 600;
    width: 90px;
    white-space: nowrap;
}

.craft-img-cell {
    width: 150px;
    background: #fff;
}

.craft-material-table .workshop-cell {
    background: #f5f7fa;
    font-weight: 700;
    writing-mode: vertical-lr;
    letter-spacing: 4px;
}

.craft-material-table .part-cell {
    white-space: nowrap;
    color: #1f2d3d;
    font-weight: 600;
}

.craft-material-table .craft-desc-cell {
    text-align: left;
    white-space: pre-line;
    line-height: 1.6;
}

.craft-material-table .craft-name-cell {
    text-align: left;
    white-space: pre-line;
    line-height: 1.6;
    color: #ad6800;
}

.craft-color-tabs {
    margin-top: 4px;
}

.craft-extra-table {
    margin-top: -1px;
}

.craft-extra-table .info-label {
    background: #eef4ff;
    color: #3a7bd5;
    font-weight: 600;
    width: 110px;
    white-space: nowrap;
}

.craft-extra-table .craft-extra-value {
    text-align: left;
    white-space: pre-line;
    line-height: 1.7;
    color: #ad6800;
    background: #fffdf5;
}

.craft-image-section {
    display: flex;
    flex-wrap: wrap;
    gap: 24px;
    margin-top: 16px;
}

.craft-image-block {
    flex: 1 1 320px;
    min-width: 280px;
}

.craft-image-title {
    font-weight: 600;
    color: #3a7bd5;
    margin-bottom: 8px;
}

.craft-image-preview {
    width: 100%;
    max-width: 480px;
    border: 1px solid #d5d8dd;
    border-radius: 8px;
}
</style>
