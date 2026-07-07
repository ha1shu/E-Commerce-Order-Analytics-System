import sqlite3
import pandas as pd

conn = sqlite3.connect("ecommerce.db")

pd.read_csv("cleaned/customers_clean.csv").to_sql("customers", conn, if_exists="replace", index=False)
pd.read_csv("cleaned/products_clean.csv").to_sql("products", conn, if_exists="replace", index=False)
pd.read_csv("cleaned/orders_clean.csv").to_sql("orders", conn, if_exists="replace", index=False)
pd.read_csv("cleaned/order_items_clean.csv").to_sql("order_items", conn, if_exists="replace", index=False)

conn.close()
print("Loaded into ecommerce.db")