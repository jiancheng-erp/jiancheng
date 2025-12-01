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

    quantity_sum_map = {
        "pendingInbound": 0,
        "pendingOutbound": 0,
        "inboundAmount": 0,
        "outboundAmount": 0,
        "makeInventoryInbound": 0,
        "makeInventoryOutbound": 0,
        "currentAmount": 0,
        "currentItemTotalPrice": 0,
    }

    # Insert materials data starting from row 8
    start_row = 8
    current_row = start_row
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

        # Update sums
        quantity_sum_map["pendingInbound"] += data.get("pendingInbound", 0)
        quantity_sum_map["pendingOutbound"] += data.get("pendingOutbound", 0)
        quantity_sum_map["inboundAmount"] += data.get("inboundAmount", 0)
        quantity_sum_map["outboundAmount"] += data.get("outboundAmount", 0)
        quantity_sum_map["makeInventoryInbound"] += data.get("makeInventoryInbound", 0)
        quantity_sum_map["makeInventoryOutbound"] += data.get("makeInventoryOutbound", 0)
        quantity_sum_map["currentAmount"] += data.get("currentAmount", 0)
        quantity_sum_map["currentItemTotalPrice"] += data.get("currentItemTotalPrice", 0)

        current_row += 1
    
    # Insert totals in the row after the last data row
    total_row = current_row
    sheet[f"J{total_row}"] = "合计"
    sheet[f"K{total_row}"] = quantity_sum_map["pendingInbound"]
    sheet[f"L{total_row}"] = quantity_sum_map["pendingOutbound"]
    sheet[f"M{total_row}"] = quantity_sum_map["inboundAmount"]
    sheet[f"N{total_row}"] = quantity_sum_map["outboundAmount"]
    sheet[f"O{total_row}"] = quantity_sum_map["makeInventoryInbound"]
    sheet[f"P{total_row}"] = quantity_sum_map["makeInventoryOutbound"]
    sheet[f"Q{total_row}"] = quantity_sum_map["currentAmount"]
    sheet[f"U{total_row}"] = quantity_sum_map["currentItemTotalPrice"]

    # Save the modified file
    workbook.save(save_path)
    return save_path
