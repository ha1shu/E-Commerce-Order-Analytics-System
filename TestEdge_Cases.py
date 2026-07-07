import pandas as pd
from datetime import datetime, timedelta


# Test 1: order_items referencing a non-existent order_id

def test_invalid_order_id():
    orders = pd.DataFrame({"order_id": [1, 2, 3]})
    items = pd.DataFrame({"order_id": [1, 2, 99], "item_id": [101, 102, 103]})

    valid_ids = set(orders["order_id"])
    bad_items = items[~items["order_id"].isin(valid_ids)]

    assert len(bad_items) == 1, "Expected exactly 1 invalid order_id row"
    assert bad_items.iloc[0]["order_id"] == 99
    print("test_invalid_order_id passed -> orphan rows detected, should be logged and excluded from revenue calcs")



# Test 2: discount_percent > 100 (invalid data)

def test_discount_over_100():
    df = pd.DataFrame({"discount_percent": [10, 110, 50, -5]})

    invalid = df[(df["discount_percent"] > 100) | (df["discount_percent"] < 0)]

    assert len(invalid) == 2, "Expected 2 invalid discount rows (110 and -5)"
    print("test_discount_over_100 passed -> discount >100 or <0 is invalid, should be capped or flagged, not used raw in revenue formula")



# Test 3: quantity is 0

def test_zero_quantity():
    df = pd.DataFrame({"quantity": [0, 5, -2, 0]})

    zero_rows = df[df["quantity"] == 0]

    assert len(zero_rows) == 2

    # Business decision: quantity=0 contributes nothing to revenue, and it's not a real purchase
   
    print("test_zero_quantity passed -> quantity=0 rows contribute 0 revenue but should be flagged as junk, not silently kept")



# Test 4: order_date is in the future

def test_future_order_date():
    today = pd.Timestamp.now()
    df = pd.DataFrame({
        "order_date": pd.to_datetime(["2026-07-01", "2027-01-01", "2025-01-01"])
    })

    future_orders = df[df["order_date"] > today]

    assert len(future_orders) == 1
    
    print("test_future_order_date passed -> future-dated orders are likely bad data entry, should be flagged and excluded from 'last 12 months' style reports")


if __name__ == "__main__":
    test_invalid_order_id()
    test_discount_over_100()
    test_zero_quantity()
    test_future_order_date()
    print("\nAll edge case tests passed.")