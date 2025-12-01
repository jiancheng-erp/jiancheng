from openpyxl.utils import range_boundaries

from openpyxl import load_workbook
from logger import logger
from warehouse import material_storage
def generate_accounting_warehouse_excel(template_path, save_path, warehouse_name, supplier_name, material_model,time_range, materials_data):

    # Load the workbook and select the first sheet
    workbook = load_workbook(template_path)
    sheet = workbook["Sheet1"]
    
    # Insert metadata
    sheet["C2"] = warehouse_name if warehouse_name else "全部"
    sheet["F2"] = supplier_name if supplier_name else "全部"
    sheet["H2"] = material_model if material_model else "全部"
    sheet["K2"] = time_range if time_range else "全部"

    quantity_sum_map = {
        "pendingInbound": 0,
        "pendingOutbound": 0,
        "inboundAmount": 0,
        "outboundAmount": 0,
        "makeInventoryInbound": 0,
        "makeInventoryOutbound": 0,
        "currentAmount": 0,
        "itemTotalPrice": 0,
    }
    

    # Insert materials data starting from row 8
    start_row = 8
    current_row = start_row
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
        order_rid = data.get("orderRid", "")
        shoe_rid = data.get("shoeRid", "")
        customer_product_name = data.get("customerProductName", "")
        current_amount = data.get("currentAmount", 0)
        average_price = data.get("averagePrice", 0)
        item_total_price = data.get("itemTotalPrice", 0)
        pending_inbound = data.get("pendingInbound", 0)
        pending_outbound = data.get("pendingOutbound", 0)
        outbound_amount = data.get("outboundAmount", 0)
        make_inventory_inbound = data.get("makeInventoryInbound", 0)
        make_inventory_outbound = data.get("makeInventoryOutbound", 0)
        
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
        sheet[f"K{index}"] = str(pending_inbound) 
        sheet[f"L{index}"] = str(pending_outbound)
        sheet[f"M{index}"] = str(inbound_amount)
        sheet[f"N{index}"] = str(outbound_amount)
        sheet[f"O{index}"] = str(make_inventory_inbound)
        sheet[f"P{index}"] = str(make_inventory_outbound)
        sheet[f"Q{index}"] = str(current_amount)
        sheet[f"R{index}"] = str(unit_price)
        sheet[f"S{index}"] = str(material_unit)
        sheet[f"T{index}"] = str(average_price)
        sheet[f"U{index}"] = str(item_total_price)

        # Update sums
        quantity_sum_map["pendingInbound"] += pending_inbound
        quantity_sum_map["pendingOutbound"] += pending_outbound
        quantity_sum_map["inboundAmount"] += inbound_amount
        quantity_sum_map["outboundAmount"] += outbound_amount
        quantity_sum_map["makeInventoryInbound"] += make_inventory_inbound
        quantity_sum_map["makeInventoryOutbound"] += make_inventory_outbound
        quantity_sum_map["currentAmount"] += current_amount
        quantity_sum_map["itemTotalPrice"] += item_total_price

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
    sheet[f"U{total_row}"] = quantity_sum_map["itemTotalPrice"]

    # Save the modified file
    workbook.save(save_path)
    return save_path