frappe.query_reports["Benchmark Customer Activity"] = {
	filters: [
		{
			fieldname: "customer_group",
			label: __("Customer Group"),
			fieldtype: "Select",
			options: ["", "Retail", "Wholesale", "Enterprise", "Government", "Non-Profit"],
		},
		{
			fieldname: "territory",
			label: __("Territory"),
			fieldtype: "Select",
			options: [
				"",
				"North America",
				"Europe",
				"Asia Pacific",
				"Middle East",
				"Africa",
				"Latin America",
			],
		},
		{
			fieldname: "min_invoices",
			label: __("Minimum Invoices"),
			fieldtype: "Int",
			default: 0,
		},
		{
			fieldname: "limit",
			label: __("Max Results"),
			fieldtype: "Int",
			default: 1000,
		},
	],
};
