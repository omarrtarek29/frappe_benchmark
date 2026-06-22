"""
Benchmark Customer Activity Report.

Shows customer activity metrics with invoice statistics for stress testing joins.
"""

import frappe


def execute(filters=None):
	"""
	Execute the Benchmark Customer Activity report.

	Args:
	    filters: Report filters (customer_group, territory, min_invoices).

	Returns:
	    Tuple of (columns, data).
	"""
	columns = get_columns()
	data = get_data(filters)
	return columns, data


def get_columns():
	"""
	Define report columns.

	Returns:
	    List of column definitions.
	"""
	return [
		{
			"fieldname": "customer",
			"label": "Customer ID",
			"fieldtype": "Link",
			"options": "Benchmark Customer",
			"width": 150,
		},
		{
			"fieldname": "customer_name",
			"label": "Customer Name",
			"fieldtype": "Data",
			"width": 200,
		},
		{
			"fieldname": "customer_group",
			"label": "Customer Group",
			"fieldtype": "Data",
			"width": 120,
		},
		{
			"fieldname": "territory",
			"label": "Territory",
			"fieldtype": "Data",
			"width": 120,
		},
		{
			"fieldname": "credit_limit",
			"label": "Credit Limit",
			"fieldtype": "Currency",
			"width": 120,
		},
		{
			"fieldname": "invoice_count",
			"label": "Invoice Count",
			"fieldtype": "Int",
			"width": 100,
		},
		{
			"fieldname": "total_revenue",
			"label": "Total Revenue",
			"fieldtype": "Currency",
			"width": 150,
		},
		{
			"fieldname": "total_outstanding",
			"label": "Outstanding",
			"fieldtype": "Currency",
			"width": 150,
		},
		{
			"fieldname": "avg_invoice_value",
			"label": "Avg Invoice",
			"fieldtype": "Currency",
			"width": 120,
		},
		{
			"fieldname": "first_invoice",
			"label": "First Invoice",
			"fieldtype": "Date",
			"width": 100,
		},
		{
			"fieldname": "last_invoice",
			"label": "Last Invoice",
			"fieldtype": "Date",
			"width": 100,
		},
		{
			"fieldname": "credit_status",
			"label": "Credit Status",
			"fieldtype": "Data",
			"width": 100,
		},
	]


def get_data(filters):
	"""
	Fetch customer activity data with invoice statistics.

	Args:
	    filters: Report filters.

	Returns:
	    List of row dicts.
	"""
	conditions = get_conditions(filters)
	having_clause = get_having_clause(filters)

	query = """
        SELECT
            c.name AS customer,
            c.customer_name,
            c.customer_group,
            c.territory,
            c.credit_limit,
            COALESCE(inv.invoice_count, 0) AS invoice_count,
            COALESCE(inv.total_revenue, 0) AS total_revenue,
            COALESCE(inv.total_outstanding, 0) AS total_outstanding,
            COALESCE(inv.avg_invoice_value, 0) AS avg_invoice_value,
            inv.first_invoice,
            inv.last_invoice,
            CASE
                WHEN COALESCE(inv.total_outstanding, 0) > c.credit_limit AND c.credit_limit > 0 THEN 'Over Limit'
                WHEN COALESCE(inv.total_outstanding, 0) > c.credit_limit * 0.8 AND c.credit_limit > 0 THEN 'Near Limit'
                ELSE 'OK'
            END AS credit_status
        FROM `tabBenchmark Customer` c
        LEFT JOIN (
            SELECT
                customer,
                COUNT(*) AS invoice_count,
                SUM(grand_total) AS total_revenue,
                SUM(outstanding_amount) AS total_outstanding,
                AVG(grand_total) AS avg_invoice_value,
                MIN(posting_date) AS first_invoice,
                MAX(posting_date) AS last_invoice
            FROM `tabBenchmark Sales Invoice`
            GROUP BY customer
        ) inv ON inv.customer = c.name
        WHERE 1=1 {conditions}
        {having_clause}
        ORDER BY total_revenue DESC
        LIMIT %(limit)s
    """.format(
		conditions=conditions,
		having_clause=having_clause,
	)

	filters["limit"] = filters.get("limit", 1000)
	return frappe.db.sql(query, filters, as_dict=True)


def get_conditions(filters):
	"""
	Build SQL WHERE conditions from filters.

	Args:
	    filters: Report filters.

	Returns:
	    SQL condition string.
	"""
	conditions = []

	if filters.get("customer_group"):
		conditions.append("AND c.customer_group = %(customer_group)s")

	if filters.get("territory"):
		conditions.append("AND c.territory = %(territory)s")

	return " ".join(conditions)


def get_having_clause(filters):
	"""
	Build HAVING clause for aggregate filters.

	Args:
	    filters: Report filters.

	Returns:
	    SQL HAVING clause string.
	"""
	if filters.get("min_invoices"):
		return "HAVING COALESCE(inv.invoice_count, 0) >= %(min_invoices)s"
	return ""
