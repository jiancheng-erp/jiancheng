from openpyxl.utils import range_boundaries

from openpyxl import load_workbook
from logger import logger

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
        paid_amount = data.get("paidAmount", 0)
        transaction_count = data.get("transactionCount", 0)
        unpaid_amount = total_amount - paid_amount if total_amount and paid_amount else 0
        
        # Fill the cells
        sheet[f"A{index}"] = str(series_number)
        sheet[f"B{index}"] = str(order_date)
        sheet[f"C{index}"] = str(order_id)
        sheet[f"D{index}"] = customer_name
        sheet[f"E{index}"] = str(paid_amount)
        sheet[f"F{index}"] = str(unpaid_amount)
        sheet[f"G{index}"] = str(total_amount)
        sheet[f"H{index}"] = str(transaction_count)
        sheet[f"I{index}"] = str(order_end_date)
        series_number += 1

    # Save the modified file
    workbook.save(save_path)
    return save_path