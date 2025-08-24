# services/inventory_excel.py
from io import BytesIO
from datetime import datetime
from decimal import Decimal
import openpyxl
from openpyxl.styles import Alignment, Font, PatternFill, Border, Side
from openpyxl.utils import get_column_letter

def _to_float(v):
    if isinstance(v, Decimal):
        return float(v)
    return float(v or 0)

def build_inventory_excel(*, rows, size_range, inventory_date:str="", inventory_reason:str=""):
    """
    传入 query_inventory_summary 的 rows 与 size_range，返回 BytesIO（二进制Excel）
    """
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "材料盘库"

    # 样式
    title_font = Font(size=14, bold=True)
    bold = Font(bold=True)
    center = Alignment(horizontal="center", vertical="center")
    right = Alignment(horizontal="right", vertical="center")
    header_fill = PatternFill("solid", fgColor="E9EEF3")
    thin_border = Border(left=Side(style="thin"), right=Side(style="thin"),
                         top=Side(style="thin"), bottom=Side(style="thin"))

    # 抬头
    title = "材料盘库清单"
    total_cols = 11 + len(size_range)  # 表头列总数
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=total_cols)
    ws.cell(row=1, column=1, value=title).font = title_font
    ws.cell(row=1, column=1).alignment = center

    ws.cell(row=2, column=1, value=f"盘库日期：{inventory_date or '-'}")
    ws.cell(row=2, column=6, value=f"盘库原因：{inventory_reason or '-'}")
    ws.cell(row=3, column=1, value=f"导出时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 表头
    base_headers = [
        "SPU编号", "厂家名称", "材料类型", "材料名称",
        "材料型号", "材料规格", "颜色", "单位",
        "总库存", "总价格", "平均单价"
    ]
    size_headers = [f"尺码{sz}" for sz in size_range]
    headers = base_headers + size_headers

    header_row = 5
    for idx, h in enumerate(headers, 1):
        c = ws.cell(row=header_row, column=idx, value=h)
        c.font = bold
        c.alignment = center
        c.fill = header_fill
        c.border = thin_border

    # 数据
    start_row = header_row + 1
    for i, r in enumerate(rows, start=start_row):
        data_row = [
            r.spu_rid or "",
            r.material_supplier or "",
            r.material_type_name or "",
            r.material_name or "",
            r.material_model or "",
            r.material_specification or "",
            r.color or "",
            r.unit or "",
            _to_float(r.total_current_amount),
            _to_float(r.total_value_amount),
            _to_float(r.avg_unit_price),
        ]
        for sz in size_range:
            data_row.append(_to_float(getattr(r, f"size_{sz}", 0)))

        for j, val in enumerate(data_row, 1):
            c = ws.cell(row=i, column=j, value=val)
            c.border = thin_border
            if j >= 9:  # 数字列右对齐
                c.alignment = right

    # 列宽
    width_map = {1:16, 2:16, 3:14, 4:16, 5:16, 6:18, 7:10, 8:8, 9:12, 10:14, 11:12}
    for col_idx, w in width_map.items():
        ws.column_dimensions[get_column_letter(col_idx)].width = w
    for k in range(len(base_headers) + 1, len(headers) + 1):
        ws.column_dimensions[get_column_letter(k)].width = 10

    bio = BytesIO()
    wb.save(bio)
    bio.seek(0)
    return bio
