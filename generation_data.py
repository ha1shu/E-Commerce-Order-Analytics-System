import csv, random
from datetime import datetime, timedelta
from faker import Faker

fake = Faker()
random.seed(42)  # so results are reproducible when you re-run

N_CUSTOMERS = 200
N_PRODUCTS = 80
N_ORDERS = 600
N_ORDER_ITEMS = 1200

# ---------- customers.csv ----------
customer_types = ["REGULAR", "PREMIUM", "VIP"]
customers = []
for i in range(1, N_CUSTOMERS + 1):
    email = fake.email()
    if random.random() < 0.02:  # 2% invalid emails
        email = email.replace("@", "").replace(".com", "")  # break it
    customers.append({
        "customer_id": i,
        "customer_name": fake.name(),
        "email": email,
        "registration_date": fake.date_between(start_date="-2y", end_date="-1M"),
        "customer_type": random.choice(customer_types)
    })

# ---------- products.csv ----------
categories = {
    "Electronics": ["Mobiles", "Laptops", "Accessories"],
    "Clothing": ["Men", "Women", "Kids"],
    "Home": ["Furniture", "Kitchen", "Decor"],
    "Books": ["Fiction", "Non-Fiction", "Academic"]
}
products = []
for i in range(1, N_PRODUCTS + 1):
    cat = random.choice(list(categories.keys()))
    name = fake.word().capitalize() + " " + fake.word().capitalize()
    if random.random() < 0.1:  # messy names
        name = "  " + name.lower() + "   "
    products.append({
        "product_id": i,
        "product_name": name,
        "category": cat,
        "subcategory": random.choice(categories[cat]),
        "cost_price": round(random.uniform(100, 5000), 2)
    })

# ---------- orders.csv ----------
statuses = ["PLACED", "SHIPPED", "DELIVERED", "CANCELLED", "RETURNED"]
regions = ["NORTH", "SOUTH", "EAST", "WEST"]
orders = []
for i in range(1, N_ORDERS + 1):
    cust_id = random.choice(customers)["customer_id"]
    if random.random() < 0.05:  # 5% missing customer_id
        cust_id = ""
    order_dt = fake.date_time_between(start_date="-1y", end_date="now")
    date_str = order_dt.strftime("%Y-%m-%d %H:%M:%S")
    if random.random() < 0.05:  # wrong format
        date_str = order_dt.strftime("%d-%m-%Y")
    orders.append({
        "order_id": i,
        "customer_id": cust_id,
        "order_date": date_str,
        "status": random.choice(statuses),
        "region_code": random.choice(regions)
    })

# ---------- order_items.csv ----------
order_items = []
for i in range(1, N_ORDER_ITEMS + 1):
    order_id = random.choice(orders)["order_id"]
    if random.random() < 0.01:  # break referential integrity on purpose
        order_id = 99999 + i
    qty = random.randint(1, 5)
    if random.random() < 0.03:  # 3% negative (returns)
        qty = -qty
    order_items.append({
        "item_id": i,
        "order_id": order_id,
        "product_id": random.choice(products)["product_id"],
        "quantity": qty,
        "unit_price": round(random.uniform(100, 3000), 2),
        "discount_percent": random.choice([0, 5, 10, 15, 20, 25, 110])  # 110 = bad data on purpose
    })

def write_csv(filename, rows):
    with open(f"data/{filename}", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

write_csv("customers.csv", customers)
write_csv("products.csv", products)
write_csv("orders.csv", orders)
write_csv("order_items.csv", order_items)

print("Done. Files created in /data")