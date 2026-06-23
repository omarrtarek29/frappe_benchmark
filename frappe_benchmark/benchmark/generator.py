"""
High-throughput benchmark data generator using Faker and bulk inserts.

Generates realistic-looking synthetic data for stress testing Frappe deployments.
Uses frappe.db.bulk_insert for maximum throughput, bypassing the ORM.
"""

import random
import uuid
from collections.abc import Iterator
from datetime import date, timedelta

import frappe
from faker import Faker

fake = Faker()

CUSTOMER_GROUPS = ["Retail", "Wholesale", "Enterprise", "Government", "Non-Profit"]
TERRITORIES = ["North America", "Europe", "Asia Pacific", "Middle East", "Africa", "Latin America"]
ITEM_GROUPS = [
	"Electronics",
	"Clothing",
	"Food & Beverage",
	"Furniture",
	"Office Supplies",
	"Industrial",
	"Healthcare",
	"Automotive",
]
CURRENCIES = ["USD", "EUR", "GBP", "AED", "SAR", "INR", "CNY", "JPY"]
STATUSES = ["Draft", "Unpaid", "Paid", "Overdue", "Cancelled"]
STATUS_WEIGHTS = [0.05, 0.15, 0.60, 0.15, 0.05]

BRANDS = [
	"TechCorp",
	"GlobalMax",
	"PrimeLine",
	"EliteChoice",
	"ValueStar",
	"ProEdge",
	"MegaMart",
	"SwiftGo",
	"TrustBrand",
	"NexGen",
]

SALES_PERSONS = [
	"John Smith",
	"Sarah Johnson",
	"Mike Williams",
	"Emily Brown",
	"David Jones",
	"Lisa Garcia",
	"James Miller",
	"Maria Martinez",
]


def _now_str() -> str:
	"""Return current datetime as string for DB fields."""
	return frappe.utils.now()


def _generate_customer_row(idx: int, batch_prefix: str) -> tuple:
	"""
	Generate a single customer row tuple for bulk insert.

	Args:
	    idx: The sequential index for this customer.
	    batch_prefix: Prefix to ensure uniqueness across batches.

	Returns:
	    Tuple of field values matching CUSTOMER_FIELDS order.
	"""
	now = _now_str()
	name = f"BCUST-{batch_prefix}-{idx:08d}"
	customer_name = fake.company()
	email = fake.company_email()
	phone = fake.phone_number()[:20]
	city = fake.city()
	country = fake.country()[:50]
	customer_group = random.choice(CUSTOMER_GROUPS)
	territory = random.choice(TERRITORIES)
	credit_limit = round(random.uniform(5000, 500000), 2)

	return (
		name,
		"Administrator",
		now,
		now,
		"Administrator",
		0,
		"BCUST-.#####",
		customer_name,
		email,
		phone,
		city,
		country,
		customer_group,
		territory,
		credit_limit,
	)


CUSTOMER_FIELDS = [
	"name",
	"owner",
	"creation",
	"modified",
	"modified_by",
	"docstatus",
	"naming_series",
	"customer_name",
	"email",
	"phone",
	"city",
	"country",
	"customer_group",
	"territory",
	"credit_limit",
]


def generate_customers(count: int, batch_prefix: str | None = None, chunk_size: int = 5000) -> int:
	"""
	Generate benchmark customer records using bulk insert.

	Args:
	    count: Number of customers to generate.
	    batch_prefix: Unique prefix for this batch (defaults to short UUID).
	    chunk_size: Number of rows per INSERT statement.

	Returns:
	    Number of customers created.
	"""
	if not batch_prefix:
		batch_prefix = uuid.uuid4().hex[:8]

	def row_generator() -> Iterator[tuple]:
		for i in range(count):
			yield _generate_customer_row(i, batch_prefix)

	frappe.db.bulk_insert(
		"Benchmark Customer",
		CUSTOMER_FIELDS,
		row_generator(),
		ignore_duplicates=True,
		chunk_size=chunk_size,
	)
	frappe.db.commit()

	return count


def _generate_item_row(idx: int, batch_prefix: str) -> tuple:
	"""
	Generate a single item row tuple for bulk insert.

	Args:
	    idx: The sequential index for this item.
	    batch_prefix: Prefix to ensure uniqueness across batches.

	Returns:
	    Tuple of field values matching ITEM_FIELDS order.
	"""
	now = _now_str()
	name = f"BITEM-{batch_prefix}-{idx:08d}"
	item_name = f"{fake.word().title()} {fake.word().title()} {random.choice(['Pro', 'Max', 'Plus', 'Ultra', 'Lite', 'Standard'])}"
	item_group = random.choice(ITEM_GROUPS)
	brand = random.choice(BRANDS)
	standard_rate = round(random.uniform(10, 5000), 2)

	return (
		name,
		"Administrator",
		now,
		now,
		"Administrator",
		0,
		"BITEM-.#####",
		item_name,
		item_group,
		brand,
		standard_rate,
	)


ITEM_FIELDS = [
	"name",
	"owner",
	"creation",
	"modified",
	"modified_by",
	"docstatus",
	"naming_series",
	"item_name",
	"item_group",
	"brand",
	"standard_rate",
]


def generate_items(count: int, batch_prefix: str | None = None, chunk_size: int = 5000) -> int:
	"""
	Generate benchmark item records using bulk insert.

	Args:
	    count: Number of items to generate.
	    batch_prefix: Unique prefix for this batch (defaults to short UUID).
	    chunk_size: Number of rows per INSERT statement.

	Returns:
	    Number of items created.
	"""
	if not batch_prefix:
		batch_prefix = uuid.uuid4().hex[:8]

	def row_generator() -> Iterator[tuple]:
		for i in range(count):
			yield _generate_item_row(i, batch_prefix)

	frappe.db.bulk_insert(
		"Benchmark Item",
		ITEM_FIELDS,
		row_generator(),
		ignore_duplicates=True,
		chunk_size=chunk_size,
	)
	frappe.db.commit()

	return count


INVOICE_FIELDS = [
	"name",
	"owner",
	"creation",
	"modified",
	"modified_by",
	"docstatus",
	"naming_series",
	"customer",
	"customer_name",
	"status",
	"posting_date",
	"due_date",
	"territory",
	"sales_person",
	"currency",
	"net_total",
	"tax_amount",
	"grand_total",
	"outstanding_amount",
]

INVOICE_ITEM_FIELDS = [
	"name",
	"owner",
	"creation",
	"modified",
	"modified_by",
	"docstatus",
	"parent",
	"parentfield",
	"parenttype",
	"idx",
	"item",
	"item_name",
	"qty",
	"rate",
	"amount",
]


def _random_posting_date() -> date:
	"""Generate a random date within the last 5 years."""
	days_back = random.randint(0, 365 * 5)
	return date.today() - timedelta(days=days_back)


def generate_invoices(
	count: int,
	items_per_invoice: int = 3,
	batch_prefix: str | None = None,
	chunk_size: int = 2000,
	start_offset: int = 0,
) -> int:
	"""
	Generate benchmark sales invoice records with child items using bulk insert.

	Args:
	    count: Number of invoices to generate.
	    items_per_invoice: Average number of line items per invoice (varies +-2).
	    batch_prefix: Unique prefix for this batch (defaults to short UUID).
	    chunk_size: Number of rows per INSERT statement.
	    start_offset: Starting index offset for parallel batch generation.

	Returns:
	    Number of invoices created.
	"""
	if not batch_prefix:
		batch_prefix = uuid.uuid4().hex[:8]

	customers = frappe.get_all("Benchmark Customer", fields=["name", "customer_name", "territory"], limit=0)
	items = frappe.get_all("Benchmark Item", fields=["name", "item_name", "standard_rate"], limit=0)

	if not customers:
		frappe.throw("No Benchmark Customers found. Generate customers first.")
	if not items:
		frappe.throw("No Benchmark Items found. Generate items first.")

	invoice_rows = []
	item_rows = []
	now = _now_str()

	for i in range(count):
		idx = start_offset + i
		inv_name = f"BINV-{batch_prefix}-{idx:010d}"
		customer = random.choice(customers)
		posting_date = _random_posting_date()
		due_date = posting_date + timedelta(days=random.choice([15, 30, 45, 60]))
		status = random.choices(STATUSES, weights=STATUS_WEIGHTS)[0]
		territory = customer.get("territory") or random.choice(TERRITORIES)
		sales_person = random.choice(SALES_PERSONS)
		currency = random.choice(CURRENCIES)

		num_items = max(1, items_per_invoice + random.randint(-2, 2))
		net_total = 0.0

		for item_idx in range(num_items):
			item = random.choice(items)
			qty = random.randint(1, 20)
			rate = float(item.get("standard_rate") or random.uniform(10, 1000))
			amount = round(qty * rate, 2)
			net_total += amount

			item_row_name = f"{inv_name}-I{item_idx:03d}"
			item_rows.append(
				(
					item_row_name,
					"Administrator",
					now,
					now,
					"Administrator",
					0,
					inv_name,
					"items",
					"Benchmark Sales Invoice",
					item_idx + 1,
					item.get("name"),
					item.get("item_name"),
					qty,
					rate,
					amount,
				)
			)

		tax_amount = round(net_total * 0.15, 2)
		grand_total = round(net_total + tax_amount, 2)
		outstanding = grand_total if status in ("Draft", "Unpaid", "Overdue") else 0.0

		invoice_rows.append(
			(
				inv_name,
				"Administrator",
				now,
				now,
				"Administrator",
				0,
				"BINV-.YYYY.-.#####",
				customer.get("name"),
				customer.get("customer_name"),
				status,
				str(posting_date),
				str(due_date),
				territory,
				sales_person,
				currency,
				round(net_total, 2),
				tax_amount,
				grand_total,
				outstanding,
			)
		)

		if len(invoice_rows) >= chunk_size:
			_flush_invoices(invoice_rows, item_rows, chunk_size)
			invoice_rows = []
			item_rows = []

	if invoice_rows:
		_flush_invoices(invoice_rows, item_rows, chunk_size)

	return count


def _flush_invoices(invoice_rows: list, item_rows: list, chunk_size: int) -> None:
	"""
	Flush invoice and item rows to DB via bulk insert.

	Args:
	    invoice_rows: List of invoice row tuples.
	    item_rows: List of invoice item row tuples.
	    chunk_size: Number of rows per INSERT statement.
	"""
	frappe.db.bulk_insert(
		"Benchmark Sales Invoice",
		INVOICE_FIELDS,
		invoice_rows,
		ignore_duplicates=True,
		chunk_size=chunk_size,
	)
	frappe.db.bulk_insert(
		"Benchmark Sales Invoice Item",
		INVOICE_ITEM_FIELDS,
		item_rows,
		ignore_duplicates=True,
		chunk_size=chunk_size * 5,
	)
	frappe.db.commit()


def drop_secondary_indexes(doctype: str) -> list:
	"""
	Drop non-primary indexes from a DocType table for faster bulk loading.

	Args:
	    doctype: The DocType name.

	Returns:
	    List of dropped index names for later recreation.
	"""
	table = f"tab{doctype}"
	indexes = frappe.db.sql(
		"""
        SELECT DISTINCT INDEX_NAME
        FROM INFORMATION_SCHEMA.STATISTICS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = %s
          AND INDEX_NAME != 'PRIMARY'
        """,
		(table,),
		as_dict=True,
	)

	dropped = []
	for idx in indexes:
		idx_name = idx.get("INDEX_NAME")
		try:
			frappe.db.sql_ddl(f"DROP INDEX `{idx_name}` ON `{table}`")
			dropped.append(idx_name)
		except Exception:
			pass

	frappe.db.commit()
	return dropped


def rebuild_indexes(doctype: str) -> None:
	"""
	Rebuild indexes for a DocType table from its current meta.

	Args:
	    doctype: The DocType name.
	"""
	frappe.db.updatedb(doctype)
	frappe.db.commit()


def get_record_counts() -> dict:
	"""
	Get current record counts for all benchmark DocTypes.

	Returns:
	    Dict with DocType names as keys and counts as values.
	"""
	return {
		"Benchmark Customer": frappe.db.count("Benchmark Customer"),
		"Benchmark Item": frappe.db.count("Benchmark Item"),
		"Benchmark Sales Invoice": frappe.db.count("Benchmark Sales Invoice"),
		"Benchmark Sales Invoice Item": frappe.db.count("Benchmark Sales Invoice Item"),
	}


def clear_benchmark_data() -> dict:
	"""
	Delete all benchmark data (use with caution).

	Returns:
	    Dict with deleted counts per DocType.
	"""
	counts = get_record_counts()

	frappe.db.delete("Benchmark Sales Invoice Item")
	frappe.db.delete("Benchmark Sales Invoice")
	frappe.db.delete("Benchmark Item")
	frappe.db.delete("Benchmark Customer")
	frappe.db.commit()

	return counts
