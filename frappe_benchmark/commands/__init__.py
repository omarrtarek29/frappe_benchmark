"""
Bench commands for benchmark data generation and reporting.

Commands:
- bench generate-benchmark-data: Generate millions of synthetic records
- bench benchmark-report: Run robustness queries and measure performance
- bench clear-benchmark-data: Delete all benchmark data
"""

import click
import frappe
from frappe.commands import get_site, pass_context


@click.command("generate-benchmark-data")
@click.option("--customers", default=10000, help="Number of customers to generate")
@click.option("--items", default=5000, help="Number of items to generate")
@click.option("--invoices", default=100000, help="Number of invoices to generate")
@click.option("--items-per-invoice", default=3, help="Average items per invoice")
@click.option("--workers", default=4, help="Number of parallel workers for invoices")
@click.option("--inline", is_flag=True, help="Run inline instead of background jobs")
@click.option("--fast-load", is_flag=True, help="Drop indexes before load, rebuild after")
@click.option("--clear-first", is_flag=True, help="Clear existing data before generating")
@pass_context
def generate_benchmark_data(
	context,
	customers,
	items,
	invoices,
	items_per_invoice,
	workers,
	inline,
	fast_load,
	clear_first,
):
	"""
	Generate synthetic benchmark data for stress testing.

	Generates realistic-looking customers, items, and sales invoices with line items.
	Uses bulk inserts for maximum throughput. Can run in parallel via RQ workers.

	Example:
	    bench --site mysite.local generate-benchmark-data --customers 50000 --items 20000 --invoices 10000000 --workers 8
	"""
	site = get_site(context)
	frappe.init(site=site)
	frappe.connect()

	try:
		from frappe_benchmark.benchmark.generator import (
			clear_benchmark_data,
			drop_secondary_indexes,
			generate_customers,
			generate_invoices,
			generate_items,
			get_record_counts,
			rebuild_indexes,
		)

		if clear_first:
			click.echo("Clearing existing benchmark data...")
			deleted = clear_benchmark_data()
			for dt, cnt in deleted.items():
				click.echo(f"  Deleted {cnt:,} {dt} records")

		click.echo("\nGenerating benchmark data:")
		click.echo(f"  Customers: {customers:,}")
		click.echo(f"  Items: {items:,}")
		click.echo(f"  Invoices: {invoices:,} (avg {items_per_invoice} items each)")
		click.echo(f"  Mode: {'inline' if inline else f'{workers} parallel workers'}")
		click.echo(f"  Fast load: {fast_load}\n")

		dropped_indexes = {}
		if fast_load:
			click.echo("Dropping secondary indexes for fast load...")
			for dt in [
				"Benchmark Customer",
				"Benchmark Item",
				"Benchmark Sales Invoice",
				"Benchmark Sales Invoice Item",
			]:
				try:
					dropped = drop_secondary_indexes(dt)
					dropped_indexes[dt] = dropped
					if dropped:
						click.echo(f"  {dt}: dropped {len(dropped)} indexes")
				except Exception:
					pass

		click.echo("\nGenerating customers...")
		generate_customers(customers)
		click.echo(f"  Created {customers:,} customers")

		click.echo("\nGenerating items...")
		generate_items(items)
		click.echo(f"  Created {items:,} items")

		click.echo("\nGenerating invoices...")
		if inline:
			generate_invoices(invoices, items_per_invoice=items_per_invoice)
			click.echo(f"  Created {invoices:,} invoices")
		else:
			_enqueue_invoice_batches(invoices, items_per_invoice, workers)
			click.echo(f"  Enqueued {workers} batch jobs for {invoices:,} invoices")
			click.echo("  Monitor with: bench --site <site> show-pending-jobs")

		if fast_load and dropped_indexes:
			click.echo("\nRebuilding indexes...")
			for dt in dropped_indexes:
				try:
					rebuild_indexes(dt)
					click.echo(f"  {dt}: rebuilt indexes")
				except Exception as e:
					click.echo(f"  {dt}: rebuild failed - {e}")

		click.echo("\nCurrent record counts:")
		for dt, cnt in get_record_counts().items():
			click.echo(f"  {dt}: {cnt:,}")

	finally:
		frappe.destroy()


def _enqueue_invoice_batches(total: int, items_per_invoice: int, workers: int) -> None:
	"""
	Split invoice generation into batches and enqueue to RQ workers.

	Args:
	    total: Total number of invoices to generate.
	    items_per_invoice: Average items per invoice.
	    workers: Number of parallel batches.
	"""
	import uuid

	batch_size = total // workers
	remainder = total % workers
	batch_prefix = uuid.uuid4().hex[:8]

	offset = 0
	for i in range(workers):
		count = batch_size + (1 if i < remainder else 0)
		if count <= 0:
			continue

		frappe.enqueue(
			"frappe_benchmark.benchmark.generator.generate_invoices",
			queue="long",
			timeout=3600 * 6,
			count=count,
			job_id=f"generate_invoices_{batch_prefix}_W{i}",
			items_per_invoice=items_per_invoice,
			batch_prefix=f"{batch_prefix}-W{i}",
			start_offset=offset,
		)
		offset += count


@click.command("benchmark-report")
@click.option("--save", is_flag=True, help="Save results to Benchmark Run doctype")
@pass_context
def benchmark_report(context, save):
	"""
	Run robustness queries and measure database performance.

	Executes a suite of representative heavy queries (aggregations, joins, filters)
	and reports execution times. Useful for stress testing DB server under load.
	"""
	site = get_site(context)
	frappe.init(site=site)
	frappe.connect()

	try:
		from frappe_benchmark.benchmark.queries import run_benchmark_queries

		click.echo("Running benchmark queries...\n")
		results = run_benchmark_queries()

		click.echo(f"{'Query':<45} {'Rows':>12} {'Time (s)':>12}")
		click.echo("-" * 72)

		total_time = 0
		for r in results:
			click.echo(f"{r['name']:<45} {r['rows']:>12,} {r['time_seconds']:>12.3f}")
			total_time += r["time_seconds"]

		click.echo("-" * 72)
		click.echo(f"{'TOTAL':<45} {'':<12} {total_time:>12.3f}")

		if save:
			_save_benchmark_run(results, total_time)
			click.echo("\nResults saved to Benchmark Run doctype.")

	finally:
		frappe.destroy()


def _save_benchmark_run(results: list, total_time: float) -> None:
	"""
	Save benchmark results to Benchmark Run doctype.

	Args:
	    results: List of query result dicts.
	    total_time: Total execution time in seconds.
	"""
	from frappe_benchmark.benchmark.generator import get_record_counts

	counts = get_record_counts()

	doc = frappe.get_doc(
		{
			"doctype": "Benchmark Run",
			"run_date": frappe.utils.now(),
			"total_time_seconds": total_time,
			"customer_count": counts.get("Benchmark Customer", 0),
			"item_count": counts.get("Benchmark Item", 0),
			"invoice_count": counts.get("Benchmark Sales Invoice", 0),
			"invoice_item_count": counts.get("Benchmark Sales Invoice Item", 0),
			"query_results": frappe.as_json(results),
		}
	)
	doc.insert(ignore_permissions=True)
	frappe.db.commit()


@click.command("clear-benchmark-data")
@click.option("--yes", is_flag=True, help="Skip confirmation prompt")
@pass_context
def clear_benchmark_data_cmd(context, yes):
	"""
	Delete all benchmark data from the database.

	WARNING: This permanently deletes all Benchmark Customer, Item, and Invoice records.
	"""
	site = get_site(context)

	if not yes:
		if not click.confirm(f"Delete ALL benchmark data from {site}?"):
			click.echo("Aborted.")
			return

	frappe.init(site=site)
	frappe.connect()

	try:
		from frappe_benchmark.benchmark.generator import clear_benchmark_data, get_record_counts

		before = get_record_counts()
		click.echo("Deleting benchmark data...")

		clear_benchmark_data()

		for dt, cnt in before.items():
			click.echo(f"  Deleted {cnt:,} {dt} records")

		click.echo("\nDone.")

	finally:
		frappe.destroy()


@click.command("benchmark-status")
@pass_context
def benchmark_status(context):
	"""
	Show current benchmark data statistics.
	"""
	site = get_site(context)
	frappe.init(site=site)
	frappe.connect()

	try:
		from frappe_benchmark.benchmark.generator import get_record_counts

		click.echo(f"\nBenchmark data status for {site}:\n")
		for dt, cnt in get_record_counts().items():
			click.echo(f"  {dt}: {cnt:,}")

	finally:
		frappe.destroy()


commands = [
	generate_benchmark_data,
	benchmark_report,
	clear_benchmark_data_cmd,
	benchmark_status,
]
