import shutil
from openpyxl import load_workbook, Workbook
from openpyxl.utils import get_column_letter, column_index_from_string
from openpyxl.drawing.image import Image
from constants import SHOESIZERANGE
from file_locations import IMAGE_UPLOAD_PATH
import os


# Function to load the Excel template and prepare for modification
def load_template(template_path, new_file_path):
    # Copy the template to a new file
    shutil.copy(template_path, new_file_path)
    # Load the new workbook
    wb = load_workbook(new_file_path)
    return wb


def get_next_column_name(current_column_name):
    # Convert column letter to index
    column_index = column_index_from_string(current_column_name)
    # Increment the index to get the next column
    next_column_index = column_index + 1
    # Convert the new index back to a column letter
    next_column_name = get_column_letter(next_column_index)
    return next_column_name


# Function to copy formatting and insert a new row
def insert_row_with_format(ws, row_to_copy, new_row_idx):
    # Insert a new row
    ws.insert_rows(new_row_idx)
    ws.row_dimensions[new_row_idx].height = ws.row_dimensions[row_to_copy].height
    # Copy the formatting
    for col_idx, cell in enumerate(ws[row_to_copy], start=1):
        new_cell = ws.cell(row=new_row_idx, column=col_idx)
        if cell.has_style:
            new_cell.border = cell.border.copy()
            new_cell.alignment = cell.alignment.copy()
            new_cell.number_format = cell.number_format


def insert_series_data(wb: Workbook, series_data, col, row):
    ws = wb.active
    for order_shoe_id in series_data:
        # order_rid = series_data[order_shoe_id].get("order_rid")
        customer_product_name = series_data[order_shoe_id].get("customerProductName")
        for color_shoe in series_data[order_shoe_id]["shoes"]:
            color_name = color_shoe.get("colorName")
            img_url = color_shoe.get("imgUrl")
            image = None
            if img_url:
                image = Image(os.path.join(IMAGE_UPLOAD_PATH, img_url))
            unit_price = color_shoe.get("unitPrice")
            packaging_info = color_shoe.get("packagingInfo")
            column_name = "A"
            for packaging_item in packaging_info:
                total_quantity_ratio = packaging_item.get("totalQuantityRatio")
                count = packaging_item.get("count")
                packaging_info_name = packaging_item.get("packagingInfoName")
                insert_row_with_format(ws, row, row + 1)
                if image:
                    image.height = 120
                    image.width = 120
                    ws.add_image(image, f"{column_name}{row}")
                column_name = get_next_column_name(column_name)
                ws[f"{column_name}{row}"] = customer_product_name
                # skip material
                column_name = get_next_column_name(column_name)
                column_name = get_next_column_name(column_name)
                ws[f"{column_name}{row}"] = color_name
                column_name = get_next_column_name(column_name)
                ws[f"{column_name}{row}"] = packaging_info_name
                column_name = get_next_column_name(column_name)
                for i in SHOESIZERANGE:
                    ws[f"{column_name}{row}"] = packaging_item.get(f"size{i}Ratio")
                    column_name = get_next_column_name(column_name)
                ws[f"{column_name}{row}"] = total_quantity_ratio
                column_name = get_next_column_name(column_name)
                ws[f"{column_name}{row}"] = count
                column_name = get_next_column_name(column_name)
                # total pairs
                ws[f"{column_name}{row}"] = total_quantity_ratio * count
                column_name = get_next_column_name(column_name)
                ws[f"{column_name}{row}"] = unit_price
                column_name = get_next_column_name(column_name)
                ws[f"{column_name}{row}"] = unit_price * total_quantity_ratio * count
                row += 1
                
def insert_series_data_amount(wb: Workbook, series_data, col, row):
    ws = wb.active
    for order_shoe_id in series_data:
        # order_rid = series_data[order_shoe_id].get("order_rid")
        customer_product_name = series_data[order_shoe_id].get("customerProductName")
        for color_shoe in series_data[order_shoe_id]["shoes"]:
            color_name = color_shoe.get("colorName")
            img_url = color_shoe.get("imgUrl")
            image = None
            if img_url:
                image = Image(os.path.join(IMAGE_UPLOAD_PATH, img_url))
            unit_price = color_shoe.get("unitPrice")
            packaging_info = color_shoe.get("packagingInfo")
            column_name = "A"
            for packaging_item in packaging_info:
                total_quantity_ratio = packaging_item.get("totalQuantityRatio")
                count = packaging_item.get("count")
                packaging_info_name = packaging_item.get("packagingInfoName")
                insert_row_with_format(ws, row, row + 1)
                if image:
                    image.height = 120
                    image.width = 120
                    ws.add_image(image, f"{column_name}{row}")
                column_name = get_next_column_name(column_name)
                ws[f"{column_name}{row}"] = customer_product_name
                # skip material
                column_name = get_next_column_name(column_name)
                column_name = get_next_column_name(column_name)
                ws[f"{column_name}{row}"] = color_name
                column_name = get_next_column_name(column_name)
                ws[f"{column_name}{row}"] = packaging_info_name
                column_name = get_next_column_name(column_name)
                for i in SHOESIZERANGE:
                    ws[f"{column_name}{row}"] = packaging_item.get(f"size{i}Ratio") * count
                    column_name = get_next_column_name(column_name)
                ws[f"{column_name}{row}"] = total_quantity_ratio
                column_name = get_next_column_name(column_name)
                ws[f"{column_name}{row}"] = count
                column_name = get_next_column_name(column_name)
                # total pairs
                ws[f"{column_name}{row}"] = total_quantity_ratio * count
                column_name = get_next_column_name(column_name)
                ws[f"{column_name}{row}"] = unit_price
                column_name = get_next_column_name(column_name)
                ws[f"{column_name}{row}"] = unit_price * total_quantity_ratio * count
                row += 1


# Function to save the workbook after modification
def save_workbook(wb, new_file_path):
    wb.save(new_file_path)


# Main function to generate the Excel file
def generate_excel_file(template_path, new_file_path, order_data: dict, metadata: dict):
    print(f"Generating Excel file")
    # Load template
    wb = load_template(template_path, new_file_path)
    ws = wb.active
    # Insert the series data
    insert_series_data(wb, order_data, "A", 9)

    # insert shoe size name
    column = "F"
    row = 8
    for i in range(len(SHOESIZERANGE)):
        ws[f"{column}{row}"] = metadata["sizeNames"][i]
        column = get_next_column_name(column)

    # Save the workbook
    save_workbook(wb, new_file_path)
    print(f"Workbook saved as {new_file_path}")
    
def generate_amount_excel_file(template_path, new_file_path, order_data: dict, metadata: dict):
    print(f"Generating Excel file")
    # Load template
    wb = load_template(template_path, new_file_path)
    ws = wb.active
    # Insert the series data
    insert_series_data_amount(wb, order_data, "A", 9)

    # insert shoe size name
    column = "F"
    row = 8
    for i in range(len(SHOESIZERANGE)):
        ws[f"{column}{row}"] = metadata["sizeNames"][i]
        column = get_next_column_name(column)

    # Save the workbook
    save_workbook(wb, new_file_path)
    print(f"Workbook saved as {new_file_path}")
