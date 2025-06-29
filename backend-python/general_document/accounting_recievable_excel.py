from openpyxl.utils import range_boundaries

from openpyxl import load_workbook
from logger import logger
from shared_apis import order

def generate_accounting_recievable_excel(template_path, save_path, customer_name, time_range, receivables_data):
    # Load the workbook and select the first sheet
    workbook = load_workbook(template_path)
    sheet = workbook["Sheet1"]
    
    # Insert metadata
    sheet["C2"] = customer_name if customer_name else "全部"
    sheet["E2"] = time_range if time_range else "全部"
    
    # Insert receivables data starting from row 3
    start_row = 4
    series_number = 1
    for index, data in enumerate(receivables_data, start=start_row):
        order_id = data.get("orderCode", "")
        customer_name = data.get("customerName", "")
        order_date = data.get("orderDate", "")
        order_end_date = data.get("orderEndDate", "")
        total_amount = data.get("totalAmount", 0)
        is_paid = data.get("isPaid", False)
        if is_paid:
            paid_string = "是"
        else:
            paid_string = "否"
        order_actual_end_date = data.get("orderActualEndDate", "")
        customer_brand = data.get("customerBrand", "")
        
        # Fill the cells
        sheet[f"A{index}"] = str(series_number)
        sheet[f"B{index}"] = str(order_date)
        sheet[f"C{index}"] = str(order_id)
        sheet[f"D{index}"] = customer_name
        sheet[f"E{index}"] = customer_brand
        sheet[f"F{index}"] = paid_string
        sheet[f"G{index}"] = str(total_amount)
        sheet[f"H{index}"] = str(order_end_date)
        sheet[f"I{index}"] = str(order_actual_end_date)
        series_number += 1

    # Save the modified file
    workbook.save(save_path)
    return save_path