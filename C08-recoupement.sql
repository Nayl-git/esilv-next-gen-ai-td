SELECT COALESCE(SUM(o.quantity_product * p.price), 0) AS revenue_cents
FROM orders o
JOIN product p   ON p.product_id  = o.product_id
JOIN customers c ON c.customer_id = o.customer_id
WHERE c.birth_date >= '2000-09-25' AND c.birth_date <= '2001-09-24';
