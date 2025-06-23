from openpyxl.utils import range_boundaries

from openpyxl import load_workbook
from logger import logger
from warehouse import material_storage
def generate_accounting_warehouse_excel(template_path, save_path, warehouse_name, supplier_name, material_model,time_range, materials_data):

    # Load the workbook and select the first sheet
    workbook = load_workbook(template_path)
    sheet = workbook["Sheet1"]
    
    # Insert metadata
    sheet["B2"] = warehouse_name if warehouse_name else "全部"
    sheet["F2"] = supplier_name if supplier_name else "全部"
    sheet["H2"] = material_model if material_model else "全部"
    sheet["K2"] = time_range if time_range else "全部"
    

    # Insert materials data starting from row 3
    start_row = 8
    for index, data in enumerate(materials_data, start=start_row):
        warehouse_name = data.get("materialWarehouse", "")
        supplier_name = data.get("supplierName", "")
        material_type = data.get("materialType", "")
        material_name = data.get("materialName", "")
        material_model = data.get("materialModel", "")
        material_specification = data.get("materialSpecification", "")
        material_storage_color = data.get("color", "")
        unit_price = data.get("unitPrice", 0)
        material_unit = data.get("actualInboundUnit", "")
        inbound_amount = data.get("inboundAmount", 0)
        item_total_price = data.get("itemTotalPrice", 0)
        order_rid = data.get("orderRid", "")
        shoe_rid = data.get("shoeRid", "")
        customer_product_name = data.get("customerProductName", "")
        current_amount = data.get("currentAmount", 0)
        average_price = data.get("averagePrice", 0)
        item_total_price = data.get("itemTotalPrice", 0)
        
        # Fill the cells
        sheet[f"A{index}"] = str(warehouse_name)
        sheet[f"B{index}"] = str(supplier_name)
        sheet[f"C{index}"] = str(material_type)
        sheet[f"D{index}"] = material_name
        sheet[f"E{index}"] = material_model
        sheet[f"F{index}"] = material_specification
        sheet[f"G{index}"] = material_storage_color
        sheet[f"H{index}"] = order_rid
        sheet[f"I{index}"] = customer_product_name
        sheet[f"J{index}"] = shoe_rid
        sheet[f"K{index}"] = str(inbound_amount)
        sheet[f"L{index}"] = str(current_amount)
        sheet[f"M{index}"] = str(unit_price)
        sheet[f"N{index}"] = material_unit
        sheet[f"O{index}"] = str(average_price)
        sheet[f"P{index}"] = str(item_total_price)

    # Save the modified file
    workbook.save(save_path)
    return save_path