// Copyright (c) 2023, Atrina Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('IBG Order', {
	refresh: function(frm) {
		var is_true = frappe.user_roles.find((role) => role === "Supply Chain");
		if (!is_true) {
			frm.set_df_property("order_type", "read_only", 1);
			frm.set_df_property("division", "read_only", 1);
			frm.set_df_property("sales_organizational", "read_only", 1);
			frm.set_df_property("sales_office", "read_only", 1);
			frm.set_df_property("distribution_channel", "read_only", 1);
			frm.set_df_property("sales_group", "read_only", 1);
		}
	}
});
