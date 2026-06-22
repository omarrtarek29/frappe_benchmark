"""Benchmark Sales Invoice DocType controller."""

import frappe
from frappe.model.document import Document


class BenchmarkSalesInvoice(Document):
	"""Synthetic sales invoice for benchmark testing."""

	def validate(self):
		"""Calculate totals from line items."""
		self.calculate_totals()

	def calculate_totals(self):
		"""Sum line item amounts to compute net_total, tax, grand_total."""
		self.net_total = sum(item.amount or 0 for item in self.items)
		if not self.tax_amount:
			self.tax_amount = self.net_total * 0.15
		self.grand_total = self.net_total + self.tax_amount
		if not self.outstanding_amount:
			self.outstanding_amount = self.grand_total if self.status in ("Draft", "Unpaid", "Overdue") else 0
