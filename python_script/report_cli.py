import sqlite3
from datetime import datetime, timedelta

DB_FILE = "ecommerce.db"

def get_summary(start_date, end_date):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    cur.execute("""
        SELECT COUNT(DISTINCT o.order_id),
               SUM(oi.quantity * oi.unit_price * (1 - oi.discount_percent/100.0)),
               COUNT(DISTINCT o.customer_id)
        FROM orders o
        JOIN order_items oi ON o.order_id = oi.order_id
        WHERE o.order_date BETWEEN ? AND ?
    """, (start_date, end_date))
    total_orders, revenue, unique_customers = cur.fetchone()

    cur.execute("""
        SELECT p.product_name, SUM(oi.quantity * oi.unit_price) AS rev
        FROM order_items oi
        JOIN products p ON oi.product_id = p.product_id
        JOIN orders o ON oi.order_id = o.order_id
        WHERE o.order_date BETWEEN ? AND ?
        GROUP BY p.product_name
        ORDER BY rev DESC
        LIMIT 3
    """, (start_date, end_date))
    top_products = cur.fetchall()

    conn.close()

    return {
        "orders": total_orders or 0,
        "revenue": revenue or 0,
        "customers": unique_customers or 0,
        "top_products": top_products
    }


def get_previous_period(start_date, end_date):
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")
    period_length = (end_dt - start_dt).days

    prev_end_dt = start_dt - timedelta(days=1)
    prev_start_dt = prev_end_dt - timedelta(days=period_length)

    return prev_start_dt.strftime("%Y-%m-%d"), prev_end_dt.strftime("%Y-%m-%d")


def print_report(report_type, start_date, end_date):
    current = get_summary(start_date, end_date)
    prev_start, prev_end = get_previous_period(start_date, end_date)
    previous = get_summary(prev_start, prev_end)

    print(f"\n===== {report_type.upper()} REPORT =====")
    print(f"Period: {start_date} to {end_date}")
    print(f"Total Orders     : {current['orders']}")
    print(f"Total Revenue    : {current['revenue']:.2f}")
    print(f"Unique Customers : {current['customers']}")

    print("\nTop 3 Products:")
    if current['top_products']:
        for name, rev in current['top_products']:
            print(f"  - {name}: {rev:.2f}")
    else:
        print("  (no data)")

    print(f"\nPrevious Period: {prev_start} to {prev_end}")
    if previous['revenue']:
        change = ((current['revenue'] - previous['revenue']) / previous['revenue']) * 100
        print(f"Revenue Change vs Previous Period: {change:.2f}%")
    else:
        print("Revenue Change vs Previous Period: N/A (no data in previous period)")

    print("=" * 35 + "\n")


if __name__ == "__main__":
    report_type = input("Report type (daily/weekly/monthly): ").strip().lower()
    start_date = input("Start date (YYYY-MM-DD): ").strip()
    end_date = input("End date (YYYY-MM-DD): ").strip()

    valid_types = ["daily", "weekly", "monthly"]
    if report_type not in valid_types:
        print(f"Invalid report type. Choose from {valid_types}")
    else:
        print_report(report_type, start_date, end_date)