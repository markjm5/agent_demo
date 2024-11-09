import datetime
from langchain.agents import tool
import pandas as pd

@tool
def check_system_time(format:str = "%Y-%m-%d %H:%M:%S"):
    """Returns the current date and time in the specified format"""
    current_time = datetime.datetime.now()

    formatted_time = current_time.strftime(format)

    return formatted_time

@tool
def get_order_id(order_email:str):
    """Returns the order email of an order using order id"""

    df = pd.DataFrame()
    df.insert(0,str("Order Id").strip(),[],True)
    df.insert(1,str("Email Address").strip(),[],True)

    temp_row = []
    order_number = str("12345").strip()
    email_address = str("rmorris@gmail.com").strip()

    temp_row.append(order_number)      
    temp_row.append(email_address)      

    df.loc[len(df.index)] = temp_row

    return df.to_json(orient='records', lines=True)

@tool
def get_order_detail(order_id:str):
    """Returns the details of an order using order email"""

    df = pd.DataFrame()
    df.insert(0,str("Order Number").strip(),[],True)
    df.insert(1,str("Product Name").strip(),[],True)
    df.insert(2,str("Quantity").strip(),[],True)
    df.insert(3,str("Value").strip(),[],True)

    temp_row = []
    order_number = str("12345").strip()
    product_name = str("Roverito Shoes").strip()
    quantity = str("5").strip()
    value = str("10.00").strip()

    temp_row.append(order_number)      
    temp_row.append(product_name)        
    temp_row.append(quantity)        
    temp_row.append(value)        

    df.loc[len(df.index)] = temp_row

    return df.to_json(orient='records', lines=True)
