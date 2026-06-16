import os
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, Side
from openpyxl.utils import get_column_letter
from logger import logger


def generate_excel_file(template_path, new_file_path, order_data):
    """
    从零生成标准采购订单 Excel（不依赖模板文件）。

    order_data keys:
        供应商, 客户名, 订单信息, 日期, 备注,
        环保要求, 发货地址, 交货期限,
        seriesData: list of {物品名称, 单位, 数量, 单价, 用途说明, 备注}
    """
    logger.debug(f"Generating Excel file for order {order_data.get('订单信息', '')}")

    wb = Workbook()
    ws = wb.active
    ws.title = "采购订单"

    thin = Side(border_style="thin", color="000000")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)
    center = Alignment(horizontal="center", vertical="center", wrap_text=True)
    left = Alignment(horizontal="left", vertical="center", wrap_text=True)

    # ── Row 1: title ─────────────────────────────────────────────────────────
    ws.merge_cells("A1:F1")
    ws["A1"] = "采  购  订  单"
    ws["A1"].font = Font(bold=True, size=16)
    ws["A1"].alignment = center

    ws.merge_cells("G1:H1")
    ws["G1"] = order_data.get("客户名", "")
    ws["G1"].font = Font(bold=True, size=12)
    ws["G1"].alignment = center
    ws.row_dimensions[1].height = 32

    # ── Row 2: supplier / order / date ────────────────────────────────────────
    ws["A2"] = "供应商："
    ws["A2"].alignment = center
    ws.merge_cells("B2:C2")
    ws["B2"] = order_data.get("供应商", "")
    ws["B2"].alignment = center

    ws["D2"] = "订单信息："
    ws["D2"].alignment = center
    ws.merge_cells("E2:F2")
    ws["E2"] = order_data.get("订单信息", "")
    ws["E2"].alignment = center

    ws["G2"] = "日期："
    ws["G2"].alignment = center
    ws["H2"] = order_data.get("日期", "")
    ws["H2"].alignment = center
    ws.row_dimensions[2].height = 20

    # ── Row 3: column headers ─────────────────────────────────────────────────
    headers = ["序号", "物品名称", "单位", "数量", "单价", "用途说明", "备注", ""]
    for col_idx, header in enumerate(headers, start=1):
        cell = ws.cell(row=3, column=col_idx, value=header)
        cell.font = Font(bold=True)
        cell.alignment = center
        cell.border = border
    ws.row_dimensions[3].height = 20

    # ── Data rows ─────────────────────────────────────────────────────────────
    series = order_data.get("seriesData", [])
    # Ensure at least 5 rows
    min_rows = max(len(series), 5)
    total_qty = 0
    for i in range(min_rows):
        row = 4 + i
        item = series[i] if i < len(series) else {}
        qty = item.get("数量", "") if item else ""
        if isinstance(qty, (int, float)):
            total_qty += qty
        values = [
            i + 1,
            item.get("物品名称", ""),
            item.get("单位", ""),
            qty,
            item.get("单价", ""),
            item.get("用途说明", ""),
            item.get("备注", ""),
            "",
        ]
        for col_idx, value in enumerate(values, start=1):
            cell = ws.cell(row=row, column=col_idx, value=value)
            cell.border = border
            cell.alignment = center
        ws.row_dimensions[row].height = 20

    last_data_row = 3 + min_rows

    # ── Footer rows ──────────────────────────────────────────────────────────
    r = last_data_row + 1

    # 合计 row
    ws.merge_cells(f"A{r}:D{r}")
    ws[f"A{r}"] = "合计"
    ws[f"A{r}"].font = Font(bold=True)
    ws[f"A{r}"].alignment = center
    ws[f"A{r}"].border = border
    ws[f"E{r}"] = total_qty if total_qty else ""
    ws[f"E{r}"].alignment = center
    ws[f"E{r}"].border = border
    ws.merge_cells(f"F{r}:H{r}")
    ws[f"F{r}"] = order_data.get("备注", "")
    ws[f"F{r}"].alignment = center
    ws[f"F{r}"].border = border
    ws.row_dimensions[r].height = 20

    # 环保要求
    r += 1
    ws[f"A{r}"] = "环境要求:"
    ws[f"A{r}"].alignment = center
    ws[f"A{r}"].border = border
    ws.merge_cells(f"B{r}:H{r}")
    ws[f"B{r}"] = order_data.get("环保要求", "")
    ws[f"B{r}"].alignment = left
    ws[f"B{r}"].border = border
    ws.row_dimensions[r].height = 20

    # 发货地址
    r += 1
    ws[f"A{r}"] = "发货地址:"
    ws[f"A{r}"].alignment = center
    ws[f"A{r}"].border = border
    ws.merge_cells(f"B{r}:H{r}")
    ws[f"B{r}"] = order_data.get("发货地址", "")
    ws[f"B{r}"].alignment = left
    ws[f"B{r}"].border = border
    ws.row_dimensions[r].height = 20

    # 交货期限
    r += 1
    ws[f"A{r}"] = "交货期限:"
    ws[f"A{r}"].alignment = center
    ws[f"A{r}"].border = border
    ws.merge_cells(f"B{r}:D{r}")
    ws[f"B{r}"] = order_data.get("交货期限", "")
    ws[f"B{r}"].alignment = center
    ws[f"B{r}"].border = border
    ws.merge_cells(f"E{r}:H{r}")
    ws[f"E{r}"] = "如有特殊情况提前5天反馈，无故延期有贵公司承担后续责任。"
    ws[f"E{r}"].font = Font(color="FF0000")
    ws[f"E{r}"].alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ws[f"E{r}"].border = border
    ws.row_dimensions[r].height = 35

    # 制表 / 审核
    r += 1
    ws.merge_cells(f"A{r}:D{r}")
    ws[f"A{r}"] = "制表："
    ws[f"A{r}"].alignment = center
    ws.merge_cells(f"E{r}:H{r}")
    ws[f"E{r}"] = "审核："
    ws[f"E{r}"].alignment = center
    ws.row_dimensions[r].height = 30

    # ── Column widths ─────────────────────────────────────────────────────────
    col_widths = [8, 30, 8, 10, 10, 20, 15, 5]
    for col_idx, width in enumerate(col_widths, start=1):
        ws.column_dimensions[get_column_letter(col_idx)].width = width

    os.makedirs(os.path.dirname(new_file_path), exist_ok=True)
    wb.save(new_file_path)
    logger.debug(f"采购订单 saved: {new_file_path}")


# def test_case_1():
#     template_path = "H:\git-projects\jiancheng\\backend-python\general_document/标准采购订单.xlsx"
#     new_file_path = "H:\git-projects\jiancheng\\backend-python\general_document/pur_test.xlsx"
#     order_data = {
#         "订单信息": "订单编号12345",
#         "供应商": "供应商A",
#         "日期": "2024-11-19",
#         "seriesData": [
#             {"物品名称": "商品1", "单位": "个", "数量": 10, "单价": 5.5, "用途说明": "用途1", "备注": "备注1"},
#             {"物品名称": "商品2", "单位": "箱", "数量": 20, "单价": 15.0, "用途说明": "用途2", "备注": "备注2"},
#         ],
#         "合计": 350,
#         "备注": "总备注",
#         "环保要求": "符合环保标准",
#         "发货地址": "测试地址",
#         "交货期限": "2024-12-01",
#     }
#     generate_excel_file(template_path, new_file_path, order_data)
#     logger.debug("Test Case 1: Basic functionality passed.")

