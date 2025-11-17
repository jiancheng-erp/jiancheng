from openpyxl.utils import range_boundaries

from openpyxl import load_workbook
from logger import logger
from warehouse import material_storage


def generate_accounting_warehouse_excel(
    template_path,
    save_path,
    warehouse_name,
    supplier_name,
    time_range,
    materials_data,
):

    # Load the workbook and select the first sheet
    workbook = load_workbook(template_path)
    sheet = workbook["Sheet1"]

    # Insert metadata
    sheet["C2"] = warehouse_name if warehouse_name else "全部"
    sheet["F2"] = supplier_name if supplier_name else "全部"
    sheet["K2"] = time_range if time_range else "全部"

    # Insert materials data starting from row 3
    start_row = 8
    for index, data in enumerate(materials_data, start=start_row):
        for j, col in enumerate(
            [
                "materialWarehouse",
                "supplierName",
                "materialType",
                "materialName",
                "materialModel",
                "materialSpecification",
                "color",
                "orderRId",
                "customerProductName",
                "shoeRId",
                "pendingInbound",
                "pendingOutbound",
                "inboundAmount",
                "outboundAmount",
                "makeInventoryInbound",
                "makeInventoryOutbound",
                "currentAmount",
                "unitPrice",
                "actualInboundUnit",
                "averagePrice",
                "currentItemTotalPrice",
            ]
        ):
            # determine the column letter
            col_letter = chr(65 + j)  # 65 is 'A'
            cell = f"{col_letter}{index}"
            sheet[cell] = data.get(col, "")

    # Save the modified file
    workbook.save(save_path)
    return save_path
