import pandas as pd
from collections import defaultdict
from logger import logger
def get_order_xls():
    df = pd.read_excel('C:/Users/19825/Desktop/工作簿1.xlsx', header=1)
    logger.debug(df)
    return df.to_dict(orient='records')
xls = get_order_xls()
def generate_key(item):
    return (item['工厂型号'], item['客户型号'], item['中文颜色'], item['英文颜色'])

# Use a defaultdict to group by the generated key
filtered_data_dict = defaultdict(list)
for item in xls:
    key = generate_key(item)
    filtered_data_dict[key].append(item)

# Now `filtered_data_dict` is a dictionary where the key is a tuple 
# (工厂型号, 客户型号, 中文颜色, 英文颜色) and the value is a list of dictionaries

# Example of accessing data
for key, items in filtered_data_dict.items():
    logger.debug(f"Key: {key}")
    for item in items:
        logger.debug(f"  Item: {item}")

