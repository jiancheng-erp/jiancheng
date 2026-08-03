import axios from 'axios'
import ExcelJS from 'exceljs'
import { saveAs } from 'file-saver'

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

const materialCategories = [
    { key: 'surfaceMaterialData', label: '面料' },
    { key: 'outsoleMaterialData', label: '大底' },
    { key: 'midsoleMaterialData', label: '中底' }
]

// 工艺单按车间分组的材料来源
const workshopGroups = [
    { name: '裁断车间', keys: ['surfaceMaterialData', 'insideMaterialData'], specialKey: 'cuttingSpecialCraft' },
    { name: '针车车间', keys: ['accessoryMaterialData'], specialKey: 'sewingSpecialCraft' },
    { name: '成型车间', keys: ['hotsoleMaterialData', 'outsoleMaterialData', 'midsoleMaterialData'], specialKey: 'moldingSpecialCraft' }
]

function formatCraftMaterialName(m) {
    const head = [m.supplierName, m.materialName].filter(Boolean).join(' ')
    const detail = [m.materialModel, m.materialSpecification].filter(Boolean).join('/')
    let line = detail ? `${head}；${detail}` : head
    if (m.processingRemark) line += `（${m.processingRemark}）`
    return line
}

// 按车间分组构建工艺单明细行
export function buildCraftGroups(colorData, detail) {
    return workshopGroups
        .map((g) => {
            const list = []
            g.keys.forEach((key) => {
                ;(colorData[key] || []).forEach((m) => list.push({ partBase: m.materialType || '', m }))
            })
            const totalByType = {}
            list.forEach((it) => (totalByType[it.partBase] = (totalByType[it.partBase] || 0) + 1))
            const seen = {}
            const rows = list.map((it) => {
                let label
                if (totalByType[it.partBase] > 1) {
                    seen[it.partBase] = (seen[it.partBase] || 0) + 1
                    label = `${it.partBase}${seen[it.partBase]}`
                } else {
                    label = it.partBase
                }
                return {
                    part: label,
                    desc: formatCraftMaterialName(it.m),
                    craft: it.m.materialCraftName || it.m.craftName || '',
                    pairs: it.m.pairs != null ? it.m.pairs : '',
                    usage: it.m.unitUsage != null ? it.m.unitUsage : ''
                }
            })
            return { name: g.name, rows, special: (detail || {})[g.specialKey] || '' }
        })
        .filter((g) => g.rows.length > 0 || g.special)
}

function formatMaterial(m) {
    const head = [m.supplierName, m.materialName].filter(Boolean).join(' ')
    const detail = [m.materialModel, m.materialSpecification].filter(Boolean).join('/')
    let line = detail ? `${head}；${detail}` : head
    if (m.processingRemark) line += `（${m.processingRemark}）`
    return line
}

function shoeRowCount(shoe) {
    return (shoe.orderShoeTypes || []).reduce((sum, colorType) => sum + (colorType.shoeTypeBatchInfoList?.length || 0), 0)
}

// 拉取订单信息 + 每个工厂款号的投产指令单，生成与查看页面一致的 A4 横向 Excel（无金额）
export async function exportProductionOrderExcel(apiBaseUrl, orderDbId) {
    const response = await axios.get(`${apiBaseUrl}/order/getbusinessorderinfo?orderid=${orderDbId}`)
    const orderData = response.data
    const orderShoeData = orderData.orderShoeAllData || []
    const batchInfoType = orderData.batchInfoType || {}
    const sizes = Object.keys(attrMappingToAmount)
        .filter((key) => batchInfoType[key] != null && batchInfoType[key] !== '')
        .map((key) => ({ name: batchInfoType[key], amountKey: attrMappingToAmount[key] }))

    // 投产指令单
    const instructionMap = {}
    await Promise.all(
        orderShoeData
            .filter((shoe) => shoe.shoeRid)
            .map(async (shoe) => {
                try {
                    const res = await axios.get(`${apiBaseUrl}/devproductionorder/getproductioninstruction`, {
                        params: { orderid: orderData.orderRid, ordershoeid: shoe.shoeRid }
                    })
                    instructionMap[shoe.shoeRid] = { status: 'exists', colors: res.data.instructionData || [] }
                } catch (error) {
                    instructionMap[shoe.shoeRid] = { status: error.response && error.response.status === 404 ? 'missing' : 'error' }
                }
            })
    )

    const getInstruction = (shoeRid) => instructionMap[shoeRid] || { status: 'missing' }
    const getColorMaterials = (shoeRid, colorName, key) => {
        const ins = instructionMap[shoeRid]
        if (!ins || ins.status !== 'exists') return []
        const colorData = ins.colors.find((c) => c.color === colorName)
        return colorData ? colorData[key] || [] : []
    }

    // 仅展示实际有数据的材料类别；全空时兜底展示全部类别
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
    const catsPresent = materialCategories.filter((cat) => present.has(cat.key))
    const cats = catsPresent.length > 0 ? catsPresent : materialCategories
    const M = cats.length

    const totalCols = 5 + M + 1 + sizes.length + 3 + 1
    const remarkCol = totalCols - 1
    const peimaCol = 5 + M

    const aoa = []
    const merges = []
    let r = 0

    aoa.push([`健诚集团${orderData.customerName || ''}号客人${orderData.customerBrand || ''}生产通知单`])
    merges.push({ s: { r, c: 0 }, e: { r, c: totalCols - 1 } })
    r++

    const infoPairs = [
        ['单号', orderData.orderRid],
        ['下单日期', orderData.startDate],
        ['出货日期', orderData.endDate],
        ['客户订单号', orderData.orderCid],
        ['业务', orderData.orderStaffName],
        ['配码类型', orderData.batchInfoTypeName]
    ]
    const infoRow = new Array(totalCols).fill('')
    const infoLabelCols = new Set()
    let ic = 0
    infoPairs.forEach(([k, v]) => {
        if (ic >= totalCols) return
        infoRow[ic] = k
        infoLabelCols.add(ic)
        const valStart = ic + 1
        const valEnd = Math.min(ic + 2, totalCols - 1)
        if (valStart <= totalCols - 1) {
            infoRow[valStart] = v ?? ''
            if (valEnd > valStart) merges.push({ s: { r: 1, c: valStart }, e: { r: 1, c: valEnd } })
        }
        ic = valEnd + 1
    })
    if (ic <= totalCols - 1) merges.push({ s: { r: 1, c: ic }, e: { r: 1, c: totalCols - 1 } })
    aoa.push(infoRow)
    r++

    const header = ['鞋图', '工厂款号', '客户型号', '颜色', '客户颜色']
    cats.forEach((cat) => header.push(cat.label))
    header.push('配码')
    sizes.forEach((s) => header.push(s.name))
    header.push('对/件', '件数', '双数', '备注')
    aoa.push(header)
    r++

    const sizeTotals = {}
    sizes.forEach((s) => (sizeTotals[s.amountKey] = 0))
    let grandTotalPairs = 0

    orderShoeData.forEach((shoe) => {
        const shoeStartRow = r
        const shoeRows = shoeRowCount(shoe)
        const ins = getInstruction(shoe.shoeRid)
        ;(shoe.orderShoeTypes || []).forEach((colorType) => {
            const batchList = colorType.shoeTypeBatchInfoList || []
            const colorStartRow = r
            grandTotalPairs += Number(colorType.shoeTypeBatchData?.totalAmount) || 0
            batchList.forEach((batch, bi) => {
                const row = new Array(totalCols).fill('')
                if (r === shoeStartRow) {
                    row[1] = shoe.shoeRid
                    row[2] = shoe.shoeCid
                    row[remarkCol] = shoe.orderShoeRemarkExist ? shoe.orderShoeRemarkRep : '--'
                }
                if (bi === 0) {
                    row[3] = colorType.shoeTypeColorName
                    row[4] = colorType.customerColorName
                    if (ins.status === 'exists') {
                        cats.forEach((cat, mi) => {
                            const mats = getColorMaterials(shoe.shoeRid, colorType.shoeTypeColorName, cat.key)
                            row[5 + mi] = mats.map(formatMaterial).join('\n')
                        })
                    } else if (r === shoeStartRow) {
                        row[5] = ins.status === 'missing' ? '投产指令单未创建' : ins.status === 'loading' ? '加载中…' : '投产指令单加载失败'
                    }
                }
                row[peimaCol] = batch.packagingInfoName
                sizes.forEach((s, si) => {
                    const v = batch[s.amountKey] || ''
                    row[peimaCol + 1 + si] = v
                    sizeTotals[s.amountKey] += Number(batch[s.amountKey]) || 0
                })
                const afterSizes = peimaCol + 1 + sizes.length
                row[afterSizes] = batch.totalQuantityRatio
                row[afterSizes + 1] = batch.unitPerRatio
                row[afterSizes + 2] = batch.total
                aoa.push(row)
                r++
            })
            if (batchList.length > 1) {
                merges.push({ s: { r: colorStartRow, c: 3 }, e: { r: r - 1, c: 3 } })
                merges.push({ s: { r: colorStartRow, c: 4 }, e: { r: r - 1, c: 4 } })
                if (ins.status === 'exists') {
                    for (let mi = 0; mi < M; mi++) merges.push({ s: { r: colorStartRow, c: 5 + mi }, e: { r: r - 1, c: 5 + mi } })
                }
            }
        })
        if (shoeRows > 1) {
            merges.push({ s: { r: shoeStartRow, c: 0 }, e: { r: r - 1, c: 0 } })
            merges.push({ s: { r: shoeStartRow, c: 1 }, e: { r: r - 1, c: 1 } })
            merges.push({ s: { r: shoeStartRow, c: 2 }, e: { r: r - 1, c: 2 } })
            merges.push({ s: { r: shoeStartRow, c: remarkCol }, e: { r: r - 1, c: remarkCol } })
        }
        if (ins.status !== 'exists' && M > 0) {
            merges.push({ s: { r: shoeStartRow, c: 5 }, e: { r: r - 1, c: 5 + M - 1 } })
        }
    })

    const totalRow = new Array(totalCols).fill('')
    totalRow[0] = '合计'
    const totalRowIndex = r
    merges.push({ s: { r, c: 0 }, e: { r, c: 4 + M } })
    sizes.forEach((s, si) => (totalRow[peimaCol + 1 + si] = sizeTotals[s.amountKey] || ''))
    const afterSizes = peimaCol + 1 + sizes.length
    totalRow[afterSizes + 2] = grandTotalPairs
    aoa.push(totalRow)

    // ---- ExcelJS 输出（A4 横向打印） ----
    const wb = new ExcelJS.Workbook()
    const ws = wb.addWorksheet('生产通知单', {
        pageSetup: {
            paperSize: 9,
            orientation: 'landscape',
            fitToPage: true,
            fitToWidth: 1,
            fitToHeight: 0,
            horizontalCentered: true,
            margins: { left: 0.2, right: 0.2, top: 0.3, bottom: 0.3, header: 0.15, footer: 0.15 }
        }
    })

    aoa.forEach((row) => ws.addRow(row))
    merges.forEach((m) => ws.mergeCells(m.s.r + 1, m.s.c + 1, m.e.r + 1, m.e.c + 1))

    const colWidths = [6, 11, 11, 7, 9]
    for (let i = 0; i < M; i++) colWidths.push(18)
    colWidths.push(7)
    sizes.forEach(() => colWidths.push(4.6))
    colWidths.push(6, 5, 5, 16)
    colWidths.forEach((w, i) => (ws.getColumn(i + 1).width = w))

    const font = (opts = {}) => ({ name: '微软雅黑', ...opts })
    const thin = { style: 'thin', color: { argb: 'FFB7BEC8' } }
    const border = { top: thin, bottom: thin, left: thin, right: thin }
    const fill = (rgb) => ({ type: 'pattern', pattern: 'solid', fgColor: { argb: 'FF' + rgb } })
    const missingTexts = ['投产指令单未创建', '加载中…', '投产指令单加载失败']

    const titleStyle = { font: font({ bold: true, size: 16, color: { argb: 'FF1F2D3D' } }), alignment: { horizontal: 'center', vertical: 'middle', wrapText: true } }
    const infoLabelStyle = { font: font({ bold: true, size: 11, color: { argb: 'FF3A7BD5' } }), fill: fill('EEF4FF'), alignment: { horizontal: 'center', vertical: 'middle', wrapText: true }, border }
    const infoValueStyle = { font: font({ size: 11 }), alignment: { horizontal: 'center', vertical: 'middle', wrapText: true }, border }
    const headerStyle = { font: font({ bold: true, size: 11, color: { argb: 'FF1F2D3D' } }), fill: fill('EAEEF4'), alignment: { horizontal: 'center', vertical: 'middle', wrapText: true }, border }
    const cellStyle = { font: font({ size: 10 }), alignment: { horizontal: 'center', vertical: 'middle', wrapText: true }, border }
    const materialStyle = { font: font({ size: 10 }), alignment: { horizontal: 'left', vertical: 'top', wrapText: true }, border }
    const missingStyle = { font: font({ size: 11, bold: true, color: { argb: 'FFF56C6C' } }), alignment: { horizontal: 'center', vertical: 'middle', wrapText: true }, border }
    const totalStyle = { font: font({ bold: true, size: 11 }), fill: fill('F5F7FA'), alignment: { horizontal: 'center', vertical: 'middle', wrapText: true }, border }

    const applyStyle = (rr, cc, style) => {
        const cell = ws.getCell(rr + 1, cc + 1)
        cell.font = style.font
        cell.alignment = style.alignment
        cell.border = style.border
        if (style.fill) cell.fill = style.fill
    }

    applyStyle(0, 0, titleStyle)
    for (let c = 0; c < totalCols; c++) applyStyle(1, c, infoLabelCols.has(c) ? infoLabelStyle : infoValueStyle)
    for (let c = 0; c < totalCols; c++) applyStyle(2, c, headerStyle)
    for (let rr = 3; rr < totalRowIndex; rr++) {
        for (let c = 0; c < totalCols; c++) {
            const val = aoa[rr] && aoa[rr][c] != null ? String(aoa[rr][c]) : ''
            if (c >= 5 && c < 5 + M) {
                applyStyle(rr, c, missingTexts.includes(val) ? missingStyle : materialStyle)
            } else if (c === remarkCol) {
                applyStyle(rr, c, materialStyle)
            } else {
                applyStyle(rr, c, cellStyle)
            }
        }
    }
    for (let c = 0; c < totalCols; c++) applyStyle(totalRowIndex, c, totalStyle)

    const estLines = (text, colUnitWidth) => {
        if (text == null || text === '') return 1
        const perLine = Math.max(1, Math.floor(colUnitWidth / 2))
        return String(text)
            .split('\n')
            .reduce((sum, seg) => sum + Math.max(1, Math.ceil(seg.length / perLine)), 0)
    }
    for (let rr = 0; rr < aoa.length; rr++) {
        let h
        if (rr === 0) h = 30
        else {
            let maxLines = 1
            for (let c = 0; c < totalCols; c++) {
                const v = aoa[rr] ? aoa[rr][c] : null
                const lines = estLines(v, colWidths[c])
                if (lines > maxLines) maxLines = lines
            }
            h = Math.min(420, Math.max(22, maxLines * 15 + 4))
        }
        ws.getRow(rr + 1).height = h
    }

    const buffer = await wb.xlsx.writeBuffer()
    saveAs(new Blob([buffer], { type: 'application/octet-stream' }), `生产通知单_${orderData.orderRid || ''}.xlsx`)
}

// 拉取工艺单数据，按“工厂款号+颜色”各生成一个工作表的工艺单 Excel
export async function exportCraftSheetExcel(apiBaseUrl, orderDbId) {
    const response = await axios.get(`${apiBaseUrl}/order/getbusinessorderinfo?orderid=${orderDbId}`)
    const orderData = response.data
    const orderShoeData = orderData.orderShoeAllData || []
    const batchInfoType = orderData.batchInfoType || {}
    const sizes = Object.keys(attrMappingToAmount)
        .filter((key) => batchInfoType[key] != null && batchInfoType[key] !== '')
        .map((key) => ({ name: batchInfoType[key], amountKey: attrMappingToAmount[key] }))
    const sizeRangeText = sizes.length ? (sizes.length === 1 ? sizes[0].name : `${sizes[0].name}-${sizes[sizes.length - 1].name}`) : ''

    const craftMap = {}
    const instrMap = {}
    await Promise.all(
        orderShoeData
            .filter((shoe) => shoe.shoeRid)
            .map(async (shoe) => {
                try {
                    const res = await axios.get(`${apiBaseUrl}/craftsheet/getcraftsheetinfo`, {
                        params: { orderid: orderData.orderRid, ordershoeid: shoe.shoeRid }
                    })
                    craftMap[shoe.shoeRid] = { status: 'exists', detail: res.data.craftSheetDetail || {}, colors: res.data.uploadData || [] }
                } catch (error) {
                    craftMap[shoe.shoeRid] = { status: error.response && error.response.status === 404 ? 'missing' : 'error' }
                }
                try {
                    const res2 = await axios.get(`${apiBaseUrl}/devproductionorder/getproductioninstruction`, {
                        params: { orderid: orderData.orderRid, ordershoeid: shoe.shoeRid }
                    })
                    instrMap[shoe.shoeRid] = { detail: res2.data.productionInstructionDetail || {} }
                } catch (error) {
                    instrMap[shoe.shoeRid] = { detail: {} }
                }
            })
    )

    const sheets = []
    orderShoeData.forEach((shoe) => {
        const cs = craftMap[shoe.shoeRid]
        if (!cs || cs.status !== 'exists') return
        const detail = cs.detail || {}
        const instrDetail = (instrMap[shoe.shoeRid] && instrMap[shoe.shoeRid].detail) || {}
        const colors = cs.colors || []
        colors.forEach((colorData) => {
            const colorName = colorData.color
            let lastType = instrDetail.lastType || ''
            const lm = (colorData.lastMaterialData || [])[0]
            if (lm && lm.materialName) lastType = lm.materialName

            const groups = buildCraftGroups(colorData, detail)

            sheets.push({
                shoeRid: shoe.shoeRid,
                shoeCid: shoe.shoeCid,
                colorName,
                designer: instrDetail.designer,
                adjuster: detail.adjuster,
                cutDie: detail.cutDie,
                reviewer: detail.reviewer,
                sizeRange: instrDetail.sizeRange || sizeRangeText,
                sizeDifference: instrDetail.sizeDifference,
                originSize: instrDetail.originSize,
                lastType,
                burnSoleCraft: instrDetail.burnSoleCraft,
                postProcessing: detail.postProcessing,
                oilyGlue: detail.oilyGlue,
                productionRemark: detail.productionRemark,
                groups
            })
        })
    })

    if (sheets.length === 0) {
        throw new Error('无工艺单数据')
    }

    const wb = new ExcelJS.Workbook()
    const usedNames = new Set()
    const makeSheetName = (base) => {
        const clean = String(base).replace(/[\\/?*[\]:]/g, ' ').slice(0, 28) || 'Sheet'
        let candidate = clean
        let i = 2
        while (usedNames.has(candidate)) {
            candidate = `${clean.slice(0, 25)}_${i}`
            i++
        }
        usedNames.add(candidate)
        return candidate
    }

    const font = (opts = {}) => ({ name: '微软雅黑', ...opts })
    const thin = { style: 'thin', color: { argb: 'FFB7BEC8' } }
    const border = { top: thin, bottom: thin, left: thin, right: thin }
    const fill = (rgb) => ({ type: 'pattern', pattern: 'solid', fgColor: { argb: 'FF' + rgb } })
    const titleStyle = { font: font({ bold: true, size: 16, color: { argb: 'FF1F2D3D' } }), alignment: { horizontal: 'center', vertical: 'middle', wrapText: true } }
    const labelStyle = { font: font({ bold: true, size: 11, color: { argb: 'FF3A7BD5' } }), fill: fill('EEF4FF'), alignment: { horizontal: 'center', vertical: 'middle', wrapText: true }, border }
    const valueStyle = { font: font({ size: 11 }), alignment: { horizontal: 'center', vertical: 'middle', wrapText: true }, border }
    const headerStyle = { font: font({ bold: true, size: 11, color: { argb: 'FF1F2D3D' } }), fill: fill('EAEEF4'), alignment: { horizontal: 'center', vertical: 'middle', wrapText: true }, border }
    const workshopStyle = { font: font({ bold: true, size: 11 }), fill: fill('F5F7FA'), alignment: { horizontal: 'center', vertical: 'middle', wrapText: true }, border }
    const partStyle = { font: font({ bold: true, size: 10, color: { argb: 'FF1F2D3D' } }), alignment: { horizontal: 'center', vertical: 'middle', wrapText: true }, border }
    const leftStyle = { font: font({ size: 10 }), alignment: { horizontal: 'left', vertical: 'top', wrapText: true }, border }
    const craftStyle = { font: font({ size: 10, color: { argb: 'FFAD6800' } }), alignment: { horizontal: 'left', vertical: 'top', wrapText: true }, border }
    const centerStyle = { font: font({ size: 10 }), alignment: { horizontal: 'center', vertical: 'middle', wrapText: true }, border }
    const extraLabelStyle = { font: font({ bold: true, size: 11, color: { argb: 'FF3A7BD5' } }), fill: fill('EEF4FF'), alignment: { horizontal: 'center', vertical: 'middle', wrapText: true }, border }
    const extraValueStyle = { font: font({ size: 10, color: { argb: 'FFAD6800' } }), fill: fill('FFFDF5'), alignment: { horizontal: 'left', vertical: 'top', wrapText: true }, border }

    const COLS = 6
    const colWidths = [8, 12, 44, 26, 8, 8]

    const estLines = (text, colUnitWidth) => {
        if (text == null || text === '') return 1
        const perLine = Math.max(1, Math.floor(colUnitWidth / 2))
        return String(text)
            .split('\n')
            .reduce((sum, seg) => sum + Math.max(1, Math.ceil(seg.length / perLine)), 0)
    }

    sheets.forEach((s) => {
        const ws = wb.addWorksheet(makeSheetName(`${s.shoeRid || ''}-${s.colorName || ''}`), {
            pageSetup: {
                paperSize: 9,
                orientation: 'landscape',
                fitToPage: true,
                fitToWidth: 1,
                fitToHeight: 0,
                horizontalCentered: true,
                margins: { left: 0.2, right: 0.2, top: 0.3, bottom: 0.3, header: 0.15, footer: 0.15 }
            }
        })
        colWidths.forEach((w, i) => (ws.getColumn(i + 1).width = w))

        const aoa = []
        const merges = []
        const cellStyles = {} // "r,c" -> style
        const setStyle = (rr, cc, st) => (cellStyles[`${rr},${cc}`] = st)
        let r = 0

        aoa.push(['健诚鞋业工艺生产指令单', '', '', '', '', ''])
        merges.push({ s: { r, c: 0 }, e: { r, c: 5 } })
        setStyle(r, 0, titleStyle)
        r++

        const infoRow = (cells, labelCols) => {
            aoa.push(cells)
            for (let c = 0; c < COLS; c++) setStyle(r, c, labelCols.includes(c) ? labelStyle : valueStyle)
            return r++
        }
        infoRow(['工厂型号', s.shoeRid || '', '客户型号', s.shoeCid || '', '设计', s.designer || '--'], [0, 2, 4])
        infoRow(['调版', s.adjuster || '--', '刀模', s.cutDie || '--', '楦型', s.lastType || '--'], [0, 2, 4])
        aoa.push(['颜色', s.colorName || '', '', '', '', ''])
        setStyle(r, 0, labelStyle)
        for (let c = 1; c < COLS; c++) setStyle(r, c, valueStyle)
        merges.push({ s: { r, c: 1 }, e: { r, c: 5 } })
        r++
        aoa.push(['配码', s.sizeRange || '--', '', '', '订单号', orderData.orderRid || ''])
        setStyle(r, 0, labelStyle)
        setStyle(r, 4, labelStyle)
        for (let c of [1, 2, 3, 5]) setStyle(r, c, valueStyle)
        merges.push({ s: { r, c: 1 }, e: { r, c: 3 } })
        r++
        infoRow(['本码', s.originSize || '--', '码差', s.sizeDifference || '--', '审核人', s.reviewer || '--'], [0, 2, 4])

        aoa.push(['车间', '部件', '材料名称', '工艺', '双数', '用量'])
        for (let c = 0; c < COLS; c++) setStyle(r, c, headerStyle)
        r++

        s.groups.forEach((g) => {
            if (g.rows.length === 0) return
            const groupStart = r
            g.rows.forEach((row, ri) => {
                aoa.push([ri === 0 ? g.name : '', row.part, row.desc, row.craft, row.pairs, row.usage])
                setStyle(r, 0, workshopStyle)
                setStyle(r, 1, partStyle)
                setStyle(r, 2, leftStyle)
                setStyle(r, 3, craftStyle)
                setStyle(r, 4, centerStyle)
                setStyle(r, 5, centerStyle)
                r++
            })
            if (g.rows.length > 1) merges.push({ s: { r: groupStart, c: 0 }, e: { r: r - 1, c: 0 } })
        })

        const extraRows = []
        s.groups.filter((g) => g.special).forEach((g) => extraRows.push([`${g.name}特殊工艺`, g.special]))
        if (s.postProcessing) extraRows.push(['后处理', s.postProcessing])
        if (s.oilyGlue) extraRows.push(['料盆油性胶', s.oilyGlue])
        if (s.burnSoleCraft) extraRows.push(['烫底工艺', s.burnSoleCraft])
        if (s.productionRemark) extraRows.push(['生产备注', s.productionRemark])
        extraRows.forEach(([label, value]) => {
            aoa.push([label, value, '', '', '', ''])
            setStyle(r, 0, extraLabelStyle)
            for (let c = 1; c < COLS; c++) setStyle(r, c, extraValueStyle)
            merges.push({ s: { r, c: 1 }, e: { r, c: 5 } })
            r++
        })

        aoa.forEach((row) => ws.addRow(row))
        merges.forEach((m) => ws.mergeCells(m.s.r + 1, m.s.c + 1, m.e.r + 1, m.e.c + 1))
        Object.entries(cellStyles).forEach(([key, st]) => {
            const [rr, cc] = key.split(',').map(Number)
            const cell = ws.getCell(rr + 1, cc + 1)
            cell.font = st.font
            cell.alignment = st.alignment
            cell.border = st.border
            if (st.fill) cell.fill = st.fill
        })

        for (let rr = 0; rr < aoa.length; rr++) {
            let h
            if (rr === 0) h = 30
            else {
                let maxLines = 1
                for (let c = 0; c < COLS; c++) {
                    const lines = estLines(aoa[rr] ? aoa[rr][c] : null, colWidths[c])
                    if (lines > maxLines) maxLines = lines
                }
                h = Math.min(420, Math.max(22, maxLines * 15 + 4))
            }
            ws.getRow(rr + 1).height = h
        }
    })

    const buffer = await wb.xlsx.writeBuffer()
    saveAs(new Blob([buffer], { type: 'application/octet-stream' }), `工艺单_${orderData.orderRid || ''}.xlsx`)
}

