"""
Robustness queries for benchmark testing.

Contains representative heavy queries for stress-testing database performance:
- Aggregations (SUM, COUNT, GROUP BY)
- Joins across parent-child tables
- Filtered queries with various indexes
- Pagination simulations
"""

import time

import frappe


def _timed_query(name: str, query: str, values: dict | None = None) -> dict:
	"""
	Execute a query and measure execution time.

	Args:
	    name: Human-readable query name.
	    query: SQL query string with %(param)s placeholders.
	    values: Dict of parameter values.

	Returns:
	    Dict with name, rows count, time_seconds, and raw result.
	"""
	start = time.perf_counter()
	result = frappe.db.sql(query, values or {}, as_dict=True)
	elapsed = time.perf_counter() - start

	return {
		"name": name,
		"rows": len(result),
		"time_seconds": round(elapsed, 4),
		"result": result,
	}


def query_total_counts() -> dict:
	"""Count all records in each benchmark table."""
	query = """
        SELECT
            (SELECT COUNT(*) FROM `tabBenchmark Customer`) AS customers,
            (SELECT COUNT(*) FROM `tabBenchmark Item`) AS items,
            (SELECT COUNT(*) FROM `tabBenchmark Sales Invoice`) AS invoices,
            (SELECT COUNT(*) FROM `tabBenchmark Sales Invoice Item`) AS invoice_items
    """
	return _timed_query("Total record counts", query)


def query_revenue_by_month() -> dict:
	"""Aggregate grand_total by month across all invoices."""
	query = """
        SELECT
            DATE_FORMAT(posting_date, '%%Y-%%m') AS month,
            COUNT(*) AS invoice_count,
            SUM(grand_total) AS total_revenue,
            SUM(outstanding_amount) AS total_outstanding
        FROM `tabBenchmark Sales Invoice`
        GROUP BY DATE_FORMAT(posting_date, '%%Y-%%m')
        ORDER BY month DESC
        LIMIT 60
    """
	return _timed_query("Revenue by month (60 months)", query)


def query_revenue_by_territory() -> dict:
	"""Aggregate revenue by territory."""
	query = """
        SELECT
            territory,
            COUNT(*) AS invoice_count,
            SUM(grand_total) AS total_revenue,
            AVG(grand_total) AS avg_invoice_value
        FROM `tabBenchmark Sales Invoice`
        WHERE territory IS NOT NULL AND territory != ''
        GROUP BY territory
        ORDER BY total_revenue DESC
    """
	return _timed_query("Revenue by territory", query)


def query_revenue_by_customer_group() -> dict:
	"""Aggregate revenue by customer group (join query)."""
	query = """
        SELECT
            c.customer_group,
            COUNT(DISTINCT i.customer) AS customer_count,
            COUNT(*) AS invoice_count,
            SUM(i.grand_total) AS total_revenue
        FROM `tabBenchmark Sales Invoice` i
        JOIN `tabBenchmark Customer` c ON i.customer = c.name
        WHERE c.customer_group IS NOT NULL AND c.customer_group != ''
        GROUP BY c.customer_group
        ORDER BY total_revenue DESC
    """
	return _timed_query("Revenue by customer group (join)", query)


def query_top_customers_by_revenue() -> dict:
	"""Find top 100 customers by total revenue."""
	query = """
        SELECT
            customer,
            customer_name,
            COUNT(*) AS invoice_count,
            SUM(grand_total) AS total_revenue,
            SUM(outstanding_amount) AS total_outstanding
        FROM `tabBenchmark Sales Invoice`
        GROUP BY customer, customer_name
        ORDER BY total_revenue DESC
        LIMIT 100
    """
	return _timed_query("Top 100 customers by revenue", query)


def query_top_customers_by_outstanding() -> dict:
	"""Find top 100 customers by outstanding amount."""
	query = """
        SELECT
            customer,
            customer_name,
            COUNT(*) AS invoice_count,
            SUM(outstanding_amount) AS total_outstanding
        FROM `tabBenchmark Sales Invoice`
        WHERE outstanding_amount > 0
        GROUP BY customer, customer_name
        ORDER BY total_outstanding DESC
        LIMIT 100
    """
	return _timed_query("Top 100 customers by outstanding", query)


def query_invoice_status_distribution() -> dict:
	"""Count invoices by status."""
	query = """
        SELECT
            status,
            COUNT(*) AS count,
            SUM(grand_total) AS total_value
        FROM `tabBenchmark Sales Invoice`
        GROUP BY status
        ORDER BY count DESC
    """
	return _timed_query("Invoice status distribution", query)


def query_top_items_by_quantity() -> dict:
	"""Find top 100 items by total quantity sold."""
	query = """
        SELECT
            ii.item,
            ii.item_name,
            SUM(ii.qty) AS total_qty,
            SUM(ii.amount) AS total_amount,
            COUNT(DISTINCT ii.parent) AS invoice_count
        FROM `tabBenchmark Sales Invoice Item` ii
        GROUP BY ii.item, ii.item_name
        ORDER BY total_qty DESC
        LIMIT 100
    """
	return _timed_query("Top 100 items by quantity", query)


def query_average_items_per_invoice() -> dict:
	"""Calculate average line items per invoice."""
	query = """
        SELECT
            COUNT(*) / NULLIF((SELECT COUNT(*) FROM `tabBenchmark Sales Invoice`), 0) AS avg_items_per_invoice,
            MIN(item_count) AS min_items,
            MAX(item_count) AS max_items
        FROM (
            SELECT parent, COUNT(*) AS item_count
            FROM `tabBenchmark Sales Invoice Item`
            GROUP BY parent
        ) AS item_counts
    """
	return _timed_query("Average items per invoice", query)


def query_invoices_date_range() -> dict:
	"""Query invoices within a date range (index usage test)."""
	query = """
        SELECT
            COUNT(*) AS count,
            SUM(grand_total) AS total
        FROM `tabBenchmark Sales Invoice`
        WHERE posting_date BETWEEN DATE_SUB(CURDATE(), INTERVAL 1 YEAR) AND CURDATE()
    """
	return _timed_query("Invoices last 12 months (date index)", query)


def query_filtered_by_status_territory() -> dict:
	"""Query with multiple filter conditions (compound index test)."""
	query = """
        SELECT
            COUNT(*) AS count,
            SUM(grand_total) AS total
        FROM `tabBenchmark Sales Invoice`
        WHERE status = 'Unpaid'
          AND territory = 'North America'
    """
	return _timed_query("Unpaid invoices in North America", query)


def query_paginated_list_simulation() -> dict:
	"""Simulate paginated list view (LIMIT/OFFSET test)."""
	query = """
        SELECT
            name, customer, customer_name, posting_date, status, grand_total
        FROM `tabBenchmark Sales Invoice`
        ORDER BY posting_date DESC, name DESC
        LIMIT 100 OFFSET 10000
    """
	return _timed_query("Paginated list (page 100)", query)


def query_full_invoice_with_items() -> dict:
	"""Fetch complete invoice data with all line items (join simulation)."""
	query = """
        SELECT
            i.name AS invoice_name,
            i.customer,
            i.posting_date,
            i.grand_total,
            ii.item,
            ii.qty,
            ii.rate,
            ii.amount
        FROM `tabBenchmark Sales Invoice` i
        JOIN `tabBenchmark Sales Invoice Item` ii ON ii.parent = i.name
        WHERE i.posting_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
        LIMIT 10000
    """
	return _timed_query("Invoice + items join (last 30 days, 10k limit)", query)


def query_customer_invoice_summary() -> dict:
	"""Complex aggregation: customer summary with invoice stats."""
	query = """
        SELECT
            c.name AS customer_id,
            c.customer_name,
            c.territory,
            c.customer_group,
            c.credit_limit,
            COALESCE(inv.invoice_count, 0) AS invoice_count,
            COALESCE(inv.total_revenue, 0) AS total_revenue,
            COALESCE(inv.total_outstanding, 0) AS total_outstanding,
            CASE
                WHEN COALESCE(inv.total_outstanding, 0) > c.credit_limit THEN 'Over Limit'
                ELSE 'Within Limit'
            END AS credit_status
        FROM `tabBenchmark Customer` c
        LEFT JOIN (
            SELECT
                customer,
                COUNT(*) AS invoice_count,
                SUM(grand_total) AS total_revenue,
                SUM(outstanding_amount) AS total_outstanding
            FROM `tabBenchmark Sales Invoice`
            GROUP BY customer
        ) inv ON inv.customer = c.name
        ORDER BY total_revenue DESC
        LIMIT 500
    """
	return _timed_query("Customer invoice summary (top 500)", query)


def query_monthly_trend_analysis() -> dict:
	"""Monthly trend with year-over-year comparison."""
	query = """
        SELECT
            YEAR(posting_date) AS year,
            MONTH(posting_date) AS month,
            COUNT(*) AS invoice_count,
            SUM(grand_total) AS revenue,
            AVG(grand_total) AS avg_invoice_value
        FROM `tabBenchmark Sales Invoice`
        WHERE posting_date >= DATE_SUB(CURDATE(), INTERVAL 3 YEAR)
        GROUP BY YEAR(posting_date), MONTH(posting_date)
        ORDER BY year DESC, month DESC
    """
	return _timed_query("Monthly trend (3 years)", query)


def run_benchmark_queries() -> list:
	"""
	Run all benchmark queries and return timing results.

	Returns:
	    List of result dicts with name, rows, time_seconds for each query.
	"""
	queries = [
		query_total_counts,
		query_revenue_by_month,
		query_revenue_by_territory,
		query_revenue_by_customer_group,
		query_top_customers_by_revenue,
		query_top_customers_by_outstanding,
		query_invoice_status_distribution,
		query_top_items_by_quantity,
		query_average_items_per_invoice,
		query_invoices_date_range,
		query_filtered_by_status_territory,
		query_paginated_list_simulation,
		query_full_invoice_with_items,
		query_customer_invoice_summary,
		query_monthly_trend_analysis,
	]

	results = []
	for query_fn in queries:
		try:
			result = query_fn()
			results.append(
				{
					"name": result["name"],
					"rows": result["rows"],
					"time_seconds": result["time_seconds"],
				}
			)
		except Exception as e:
			results.append(
				{
					"name": query_fn.__name__,
					"rows": 0,
					"time_seconds": 0,
					"error": str(e),
				}
			)

	return results
