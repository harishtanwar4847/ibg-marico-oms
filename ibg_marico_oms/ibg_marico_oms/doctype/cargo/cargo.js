// Copyright (c) 2024, Atrina Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Cargo', {
	refresh: function(frm) {
		if (frm.doc.docstatus === 1) {
			frm.add_custom_button(__('Send Mail'), function() {
				frappe.call({
					method: 'ibg_marico_oms.ibg_marico_oms.doctype.cargo.cargo.send_email_attachments',
					freeze: true,
					args: {
						doc_name: frm.doc.name,
					},
					callback: function(response) {
                        frappe.show_alert(response.message);
                    }
				});
			});
		}
	}
});
