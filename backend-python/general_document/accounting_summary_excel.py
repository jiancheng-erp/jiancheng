from openpyxl.utils import range_boundaries

from openpyxl import load_workbook

from warehouse import material_storage
def generate_accounting_summary_excel(template_path, save_path, warehouse_name, supplier_name, material_model,time_range, materials_data):

    # Load the workbook and select the first sheet
    workbook = load_workbook(template_path)
    sheet = workbook["Sheet1"]
    
    # Insert metadata
    sheet["B2"] = warehouse_name if warehouse_name else "全部"
    sheet["D2"] = supplier_name if supplier_name else "全部"
    sheet["F2"] = material_model if material_model else "全部"
    sheet["I2"] = time_range if time_range else "全部"
    

    # Insert materials data starting from row 3
    start_row = 8
    for index, data in enumerate(materials_data, start=start_row):
        supplier_name = data.get("supplierName", "")
        material_name = data.get("materialName", "")
        material_model = data.get("materialModel", "")
        material_specification = data.get("materialSpecification", "")
        material_storage_color = data.get("materialColor", "")
        unit_price = data.get("unitPrice", 0)
        material_unit = data.get("materialUnit", "")
        inbound_amount = data.get("totalAmount", 0)
        item_total_price = data.get("totalPrice", 0)
        spu_rid = data.get("spuRid", "")
        order_rid = data.get("orderRid", "")
        
        # Fill the cells
        sheet[f"A{index}"] = order_rid
        sheet[f"B{index}"] = supplier_name
        sheet[f"C{index}"] = material_name
        sheet[f"D{index}"] = material_model
        sheet[f"E{index}"] = material_storage_color
        sheet[f"F{index}"] = material_specification
        sheet[f"G{index}"] = unit_price
        sheet[f"H{index}"] = material_unit
        sheet[f"I{index}"] = str(inbound_amount)
        sheet[f"J{index}"] = str(item_total_price)
        sheet[f"K{index}"] = spu_rid

    # Save the modified file
    workbook.save(save_path)
    return save_path