// Copyright (c) 2023, Atrina Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('OBD', {
	refresh: function(frm) {
		frm.page.sidebar.remove(); // this removes the sidebar
		frm.page.wrapper.find(".layout-main-section-wrapper").removeClass("col-md-10"); // this removes class "col-md-10" from content block, which sets width to 83%

		if (frm.doc.final_status === "Pending") {
			frm.add_custom_button(__('Short Close'), function () {
				console.log("Doc Name :",frm.doc.name)
				frappe.call({
					method: 'ibg_marico_oms.ibg_marico_oms.doctype.obd.obd.order_reject',
					freeze: true,
					args: {
						doc: frm.doc.name,
					},
				});
			});
		}
	},
	// on_load: function(frm) {
	// 	console.log("ON Load Function")
	// 	frappe.call({
	// 		method: 'ibg_marico_oms.ibg_marico_oms.doctype.obd.obd.order_status',
	// 		freeze: true,
	// 		args: {
	// 			doc_name: frm.doc.name,
	// 		},
	// 	});
	// }
});

