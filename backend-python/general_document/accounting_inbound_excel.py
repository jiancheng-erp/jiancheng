from openpyxl import load_workbook
def generate_accounting_inbound_excel(template_path, save_path, warehouse_name, supplier_name, material_model,time_range, materials_data):

    # Load the workbook and select the first sheet
    workbook = load_workbook(template_path)
    sheet = workbook["Sheet1"]
    
    # Insert metadata
    sheet["B2"] = warehouse_name if warehouse_name else "全部"
    sheet["E2"] = supplier_name if supplier_name else "全部"
    sheet["G2"] = material_model if material_model else "全部"
    sheet["J2"] = time_range if time_range else "全部"
    

    # Insert materials data starting from row 3
    start_row = 8
    for index, data in enumerate(materials_data, start=start_row):
        inbound_rid = data.get("inboundRid", "")
        inbound_datetime = data.get("inboundDatetime", "")
        supplier_name = data.get("supplierName", "")
        material_name = data.get("materialName", "")
        material_model = data.get("materialModel", "")
        material_specification = data.get("materialSpecification", "")
        material_storage_color = data.get("color", "")
        unit_price = data.get("unitPrice", 0)
        material_unit = data.get("materialUnit", "")
        inbound_amount = data.get("inboundAmount", 0)
        item_total_price = data.get("itemTotalPrice", 0)
        order_rid = data.get("orderRid", "")
        shoe_rid = data.get("shoeRid", "")
        remark = data.get("remark", "")
        
        # Fill the cells
        sheet[f"A{index}"] = str(inbound_rid)
        sheet[f"B{index}"] = str(order_rid)
        sheet[f"C{index}"] = str(shoe_rid)
        sheet[f"D{index}"] = str(inbound_datetime)
        sheet[f"E{index}"] = supplier_name
        sheet[f"F{index}"] = material_name
        sheet[f"G{index}"] = material_model
        sheet[f"H{index}"] = material_specification
        sheet[f"I{index}"] = material_storage_color
        sheet[f"J{index}"] = unit_price
        sheet[f"K{index}"] = material_unit
        sheet[f"L{index}"] = str(inbound_amount)
        sheet[f"M{index}"] = str(item_total_price)
        sheet[f"N{index}"] = remark

    # Save the modified file
    workbook.save(save_path)
    return save_path