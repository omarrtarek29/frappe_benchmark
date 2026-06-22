frappe.query_reports["Benchmark Revenue Summary"] = {
	filters: [
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: frappe.datetime.add_months(frappe.datetime.get_today(), -12),
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			default: frappe.datetime.get_today(),
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
			fieldname: "status",
			label: __("Status"),
			fieldtype: "Select",
			options: ["", "Draft", "Unpaid", "Paid", "Overdue", "Cancelled"],
		},
		{
			fieldname: "group_by",
			label: __("Group By"),
			fieldtype: "Select",
			options: ["Territory", "Status", "Currency", "Month", "Year", "Sales Person"],
			default: "Territory",
		},
	],
};
