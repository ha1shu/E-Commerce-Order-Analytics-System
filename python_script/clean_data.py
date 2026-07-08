import pandas as pd
import re

issues_report = []

def clean_orders(df):
    df = df.copy()
    # fix DD-MM-YYYY dates into proper format
    def fix_date(x):
        for fmt in ("%Y-%m-%d %H:%M:%S", "%d-%m-%Y"):
            try:
                return pd.to_datetime(x, format=fmt)
            except Exception:
                continue
        return pd.NaT

    df["order_date"] = df["order_date"].apply(fix_date)

    missing = df["customer_id"].isna() | (df["customer_id"] == "")
    issues_report.append(f"Orders with missing customer_id: {missing.sum()}")
    df["customer_id"] = df["customer_id"].replace("", pd.NA)
    return df

def clean_products(df):
    df = df.copy()
    df["product_name"] = df["product_name"].str.strip().str.title()
    return df

def validate_emails(df):
    pattern = r"^[^@]+@[^@]+\.[^@]+$"
    bad = df[~df["email"].str.match(pattern, na=False)]
    issues_report.append(f"Invalid emails found: {len(bad)}")
    return bad["customer_id"].tolist()

def check_referential_integrity(orders_df, items_df):
    valid_ids = set(orders_df["order_id"])
    bad_items = items_df[~items_df["order_id"].isin(valid_ids)]
    issues_report.append(f"order_items with invalid order_id: {len(bad_items)}")
    return bad_items

if __name__ == "__main__":
    orders = pd.read_csv("data/orders.csv")
    products = pd.read_csv("data/products.csv")
    customers = pd.read_csv("data/customers.csv")
    items = pd.read_csv("data/order_items.csv")

    orders_clean = clean_orders(orders)
    products_clean = clean_products(products)
    bad_emails = validate_emails(customers)
    bad_items = check_referential_integrity(orders, items)

    orders_clean.to_csv("cleaned/orders_clean.csv", index=False)
    products_clean.to_csv("cleaned/products_clean.csv", index=False)
    customers.to_csv("cleaned/customers_clean.csv", index=False)
    items.to_csv("cleaned/order_items_clean.csv", index=False)

    with open("cleaned/issues_report.txt", "w") as f:
        f.write("\n".join(issues_report))

    print("Cleaning done. Report saved.")