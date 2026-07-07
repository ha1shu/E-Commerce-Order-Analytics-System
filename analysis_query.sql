
-- BASIC QUERIES
-------------------------

-- 1. Total revenue per category
SELECT p.category,
       ROUND(SUM(oi.quantity * oi.unit_price * (1 - oi.discount_percent/100.0)), 2) AS revenue
FROM order_items oi
JOIN products p ON oi.product_id = p.product_id
GROUP BY p.category;


-- 2. Top 10 customers by total order value
SELECT o.customer_id,
       ROUND(SUM(oi.quantity * oi.unit_price * (1 - oi.discount_percent/100.0)), 2) AS total_value
FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id
WHERE o.customer_id IS NOT NULL
GROUP BY o.customer_id
ORDER BY total_value DESC
LIMIT 10;


-- 3. Month-wise order count, last 12 months
SELECT strftime('%Y-%m', order_date) AS month, COUNT(*) AS order_count
FROM orders
WHERE order_date >= date('now', '-12 months')
GROUP BY month
ORDER BY month;



-- INTERMEDIATE QUERIES
----------------------------------
-- 4. Customers who ordered but never had anything delivered
SELECT DISTINCT customer_id
FROM orders o
WHERE customer_id IS NOT NULL
AND customer_id NOT IN (
    SELECT customer_id FROM orders WHERE status = 'DELIVERED' AND customer_id IS NOT NULL
);


-- 5. Products with more returns than purchases
SELECT product_id,
       SUM(CASE WHEN quantity > 0 THEN quantity ELSE 0 END) AS purchased,
       SUM(CASE WHEN quantity < 0 THEN -quantity ELSE 0 END) AS returned
FROM order_items
GROUP BY product_id
HAVING returned > purchased;


-- 6. Return rate per category
SELECT p.category,
       ROUND(SUM(CASE WHEN oi.quantity < 0 THEN -oi.quantity ELSE 0 END) * 1.0 /
       SUM(ABS(oi.quantity)), 4) AS return_rate
FROM order_items oi
JOIN products p ON oi.product_id = p.product_id
GROUP BY p.category;



-- ADVANCED QUERIES (Window Functions, CTEs)
--------------------------------------------

-- 7. Running total of revenue per region
SELECT region_code, order_date, daily_revenue,
       SUM(daily_revenue) OVER (PARTITION BY region_code ORDER BY order_date) AS running_total
FROM (
    SELECT o.region_code, DATE(o.order_date) AS order_date,
           SUM(oi.quantity * oi.unit_price * (1 - oi.discount_percent/100.0)) AS daily_revenue
    FROM orders o JOIN order_items oi ON o.order_id = oi.order_id
    GROUP BY o.region_code, DATE(o.order_date)
);


-- 8. DENSE_RANK products by revenue within category
SELECT category, product_name, total_revenue,
       DENSE_RANK() OVER (PARTITION BY category ORDER BY total_revenue DESC) AS rank_in_category
FROM (
    SELECT p.category, p.product_name,
           SUM(oi.quantity * oi.unit_price * (1 - oi.discount_percent/100.0)) AS total_revenue
    FROM order_items oi JOIN products p ON oi.product_id = p.product_id
    GROUP BY p.category, p.product_name
);


-- 9. LAG analysis: days between consecutive orders + At Risk flag
WITH gaps AS (
    SELECT customer_id, order_date,
           LAG(order_date) OVER (PARTITION BY customer_id ORDER BY order_date) AS previous_order_date
    FROM orders
    WHERE customer_id IS NOT NULL
),
gaps_calc AS (
    SELECT customer_id, order_date, previous_order_date,
           julianday(order_date) - julianday(previous_order_date) AS days_gap
    FROM gaps
)
SELECT customer_id, order_date, previous_order_date, days_gap,
       CASE WHEN (SELECT AVG(days_gap) FROM gaps_calc g2
                  WHERE g2.customer_id = gaps_calc.customer_id AND g2.days_gap IS NOT NULL) > 30
            THEN 'At Risk' ELSE 'Normal' END AS risk_flag
FROM gaps_calc
ORDER BY customer_id, order_date;


-- 10. CTE with multiple levels: monthly revenue -> category -> count per month
WITH monthly_revenue AS (
    SELECT o.customer_id, strftime('%Y-%m', o.order_date) AS month,
           SUM(oi.quantity * oi.unit_price * (1 - oi.discount_percent/100.0)) AS revenue
    FROM orders o JOIN order_items oi ON o.order_id = oi.order_id
    WHERE o.customer_id IS NOT NULL
    GROUP BY o.customer_id, month
),
categorized AS (
    SELECT customer_id, month, revenue,
        CASE WHEN revenue > 10000 THEN 'High'
             WHEN revenue >= 5000 THEN 'Medium'
             ELSE 'Low' END AS spend_category
    FROM monthly_revenue
)
SELECT month, spend_category, COUNT(*) AS customer_count
FROM categorized
GROUP BY month, spend_category
ORDER BY month, spend_category;


-- 11. NTILE quartiles by customer lifetime value
WITH customer_totals AS (
    SELECT o.customer_id,
           SUM(oi.quantity * oi.unit_price * (1 - oi.discount_percent/100.0)) AS total_value
    FROM orders o JOIN order_items oi ON o.order_id = oi.order_id
    WHERE o.customer_id IS NOT NULL
    GROUP BY o.customer_id
)
SELECT customer_id, total_value,
       NTILE(4) OVER (ORDER BY total_value DESC) AS quartile,
       CASE NTILE(4) OVER (ORDER BY total_value DESC)
            WHEN 1 THEN 'Platinum' WHEN 2 THEN 'Gold'
            WHEN 3 THEN 'Silver' ELSE 'Bronze' END AS quartile_label
FROM customer_totals;


-- 12. Year-over-Year comparison
WITH monthly_rev AS (
    SELECT strftime('%Y', o.order_date) AS year, strftime('%m', o.order_date) AS month,
           SUM(oi.quantity * oi.unit_price * (1 - oi.discount_percent/100.0)) AS revenue
    FROM orders o JOIN order_items oi ON o.order_id = oi.order_id
    GROUP BY year, month
)
SELECT curr.year, curr.month, curr.revenue,
       prev.revenue AS prev_year_revenue,
       CASE WHEN prev.revenue IS NULL OR prev.revenue = 0 THEN NULL
            ELSE ROUND((curr.revenue - prev.revenue) * 100.0 / prev.revenue, 2) END AS yoy_growth_percent
FROM monthly_rev curr
LEFT JOIN monthly_rev prev
    ON prev.month = curr.month
    AND CAST(prev.year AS INTEGER) = CAST(curr.year AS INTEGER) - 1
ORDER BY curr.year, curr.month;


-- 13. First/last purchased category per customer
WITH customer_category_orders AS (
    SELECT o.customer_id, p.category, o.order_date,
        ROW_NUMBER() OVER (PARTITION BY o.customer_id ORDER BY o.order_date ASC) AS rn_first,
        ROW_NUMBER() OVER (PARTITION BY o.customer_id ORDER BY o.order_date DESC) AS rn_last
    FROM orders o
    JOIN order_items oi ON o.order_id = oi.order_id
    JOIN products p ON oi.product_id = p.product_id
    WHERE o.customer_id IS NOT NULL
),
first_cat AS (SELECT customer_id, category AS first_category FROM customer_category_orders WHERE rn_first = 1),
last_cat AS (SELECT customer_id, category AS last_category FROM customer_category_orders WHERE rn_last = 1)
SELECT f.customer_id, f.first_category, l.last_category,
       CASE WHEN f.first_category != l.last_category THEN 'Yes' ELSE 'No' END AS category_shift
FROM first_cat f JOIN last_cat l ON f.customer_id = l.customer_id;


-- 14. Cumulative revenue distribution
WITH customer_rev AS (
    SELECT o.customer_id,
           SUM(oi.quantity * oi.unit_price * (1 - oi.discount_percent/100.0)) AS revenue
    FROM orders o JOIN order_items oi ON o.order_id = oi.order_id
    WHERE o.customer_id IS NOT NULL
    GROUP BY o.customer_id
),
ranked AS (
    SELECT customer_id, revenue,
        SUM(revenue) OVER (ORDER BY revenue DESC) AS cumulative_revenue,
        SUM(revenue) OVER () AS total_revenue
    FROM customer_rev
)
SELECT customer_id, revenue, cumulative_revenue,
       ROUND(cumulative_revenue * 100.0 / total_revenue, 2) AS cumulative_percent
FROM ranked
ORDER BY revenue DESC;


-- 15. Cohort analysis (registration month cohorts, retention by month 0-3)
WITH cohorts AS (
    SELECT customer_id, strftime('%Y-%m', registration_date) AS cohort_month
    FROM customers
),
customer_orders AS (
    SELECT o.customer_id, o.order_date, c.cohort_month,
        (CAST(strftime('%Y', o.order_date) AS INTEGER) * 12 + CAST(strftime('%m', o.order_date) AS INTEGER))
        - (CAST(strftime('%Y', c.cohort_month || '-01') AS INTEGER) * 12 + CAST(strftime('%m', c.cohort_month || '-01') AS INTEGER)) AS month_number
    FROM orders o
    JOIN cohorts c ON o.customer_id = c.customer_id
    WHERE o.customer_id IS NOT NULL
),
cohort_size AS (
    SELECT cohort_month, COUNT(DISTINCT customer_id) AS total_customers
    FROM cohorts GROUP BY cohort_month
)
SELECT co.cohort_month, co.month_number,
       COUNT(DISTINCT co.customer_id) AS active_customers,
       cs.total_customers,
       ROUND(COUNT(DISTINCT co.customer_id) * 100.0 / cs.total_customers, 2) AS retention_rate
FROM customer_orders co
JOIN cohort_size cs ON co.cohort_month = cs.cohort_month
WHERE co.month_number BETWEEN 0 AND 3
GROUP BY co.cohort_month, co.month_number
ORDER BY co.cohort_month, co.month_number;


-- 16. Self-join: products frequently bought together
WITH order_products AS (
    SELECT DISTINCT o.order_id, oi.product_id
    FROM orders o JOIN order_items oi ON o.order_id = oi.order_id
    WHERE oi.quantity > 0
)
SELECT a.product_id AS product_a, b.product_id AS product_b, COUNT(*) AS times_bought_together
FROM order_products a
JOIN order_products b ON a.order_id = b.order_id AND a.product_id < b.product_id
GROUP BY a.product_id, b.product_id
ORDER BY times_bought_together DESC;