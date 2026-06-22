"""
Benchmark Revenue Summary Report.

Aggregates revenue by territory and time period for stress testing report performance.
"""

import frappe


def execute(filters=None):
	"""
	Execute the Benchmark Revenue Summary report.

	Args:
	    filters: Report filters (from_date, to_date, territory, group_by).

	Returns:
	    Tuple of (columns, data).
	"""
	columns = get_columns(filters)
	data = get_data(filters)
	return columns, data


def get_columns(filters):
	"""
	Define report columns.

	Args:
	    filters: Report filters.

	Returns:
	    List of column definitions.
	"""
	group_by = filters.get("group_by", "Territory")

	columns = [
		{
			"fieldname": "group_key",
			"label": group_by,
			"fieldtype": "Data",
			"width": 200,
		},
		{
			"fieldname": "invoice_count",
			"label": "Invoice Count",
			"fieldtype": "Int",
			"width": 120,
		},
		{
			"fieldname": "net_total",
			"label": "Net Total",
			"fieldtype": "Currency",
			"width": 150,
		},
		{
			"fieldname": "tax_amount",
			"label": "Tax Amount",
			"fieldtype": "Currency",
			"width": 150,
		},
		{
			"fieldname": "grand_total",
			"label": "Grand Total",
			"fieldtype": "Currency",
			"width": 150,
		},
		{
			"fieldname": "outstanding_amount",
			"label": "Outstanding",
			"fieldtype": "Currency",
			"width": 150,
		},
		{
			"fieldname": "avg_invoice_value",
			"label": "Avg Invoice Value",
			"fieldtype": "Currency",
			"width": 150,
		},
	]
	return columns


def get_data(filters):
	"""
	Fetch aggregated revenue data.

	Args:
	    filters: Report filters.

	Returns:
	    List of row dicts.
	"""
	conditions = get_conditions(filters)
	group_by = filters.get("group_by", "Territory")

	group_field = get_group_field(group_by)

	query = """
        SELECT
            {group_field} AS group_key,
            COUNT(*) AS invoice_count,
            SUM(net_total) AS net_total,
            SUM(tax_amount) AS tax_amount,
            SUM(grand_total) AS grand_total,
            SUM(outstanding_amount) AS outstanding_amount,
            AVG(grand_total) AS avg_invoice_value
        FROM `tabBenchmark Sales Invoice`
        WHERE 1=1 {conditions}
        GROUP BY {group_field}
        ORDER BY grand_total DESC
    """.format(
		group_field=group_field,
		conditions=conditions,
	)

	return frappe.db.sql(query, filters, as_dict=True)


def get_group_field(group_by):
	"""
	Map group_by selection to SQL field.

	Args:
	    group_by: Group by selection string.

	Returns:
	    SQL field expression.
	"""
	mapping = {
		"Territory": "territory",
		"Status": "status",
		"Currency": "currency",
		"Month": "DATE_FORMAT(posting_date, '%Y-%m')",
		"Year": "YEAR(posting_date)",
		"Sales Person": "sales_person",
	}
	return mapping.get(group_by, "territory")


def get_conditions(filters):
	"""
	Build SQL WHERE conditions from filters.

	Args:
	    filters: Report filters.

	Returns:
	    SQL condition string.
	"""
	conditions = []

	if filters.get("from_date"):
		conditions.append("AND posting_date >= %(from_date)s")

	if filters.get("to_date"):
		conditions.append("AND posting_date <= %(to_date)s")

	if filters.get("territory"):
		conditions.append("AND territory = %(territory)s")

	if filters.get("status"):
		conditions.append("AND status = %(status)s")

	return " ".join(conditions)
