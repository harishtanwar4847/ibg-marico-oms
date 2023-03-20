// Copyright (c) 2023, Atrina Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('IBG Order', {
	refresh: function(frm) {
		var is_true = frappe.user_roles.find((role) => role === "Supply Chain");
		var is_supuser = frappe.user_roles.find((role) => role === "System Manager");
		var is_ibg = frappe.user_roles.find((role) => role === "IBG Finance");
		if (!is_true) {
			frm.set_df_property("order_type", "read_only", 1);
			frm.set_df_property("division", "read_only", 1);
			frm.set_df_property("sales_organizational", "read_only", 1);
			frm.set_df_property("sales_office", "read_only", 1);
			frm.set_df_property("distribution_channel", "read_only", 1);
			frm.set_df_property("sales_group", "read_only", 1);
		}
		frm.page.sidebar.remove(); // this removes the sidebar
		frm.page.wrapper.find(".layout-main-section-wrapper").removeClass("col-md-10"); // this removes class "col-md-10" from content block, which sets width to 83%

		var fg_code = frappe.meta.get_docfield("IBG Order Items","fg_code",cur_frm.doc.name);
		var qty = frappe.meta.get_docfield("IBG Order Items","qty_in_cases",cur_frm.doc.name);
		var is_initiator = frappe.user_roles.find((role) => role === "Initiator");
		if (is_initiator && cur_frm.doc.status == 'Rejected by IBG Finance') {
			fg_code.read_only = 0;
			qty.read_only = 0;
		}

	// 	var is_true = frappe.user_roles.find((role) => role === "Initiator");
    //   	var is_supuser = frappe.user_roles.find((role) => role === "System Manager");
	// 	if (is_true || is_supuser || frappe.session.user == "Administrator") {
	// 	  frm.add_custom_button(__("Download Order Template"), function () {
	// 		frappe.call({
	// 		  method:
	// 		  "ibg_marico_oms.ibg_marico_oms.doctype.ibg_order.ibg_order.ibg_order_template",
	// 		  freeze: true,
	// 		  args: {
	// 			doc_filters: frappe
	// 			  .get_user_settings("IBG Order")
	// 			  ["List"].filters.map((filter) => filter.slice(1, 4)),
	// 		  },
	// 		  callback: (res) => {
	// 			window.open(res.message);
	// 		  },
	// 		});
	// 	  }, __("Utilities")); 
	// 	  frm.add_custom_button(__("Upload Order"), function () {
	// 		let d = new frappe.ui.Dialog({
	// 		title: "Enter details",
	// 		fields: [
	// 		  {
	// 			label: "Upload CSV",
	// 			fieldname: "file",
	// 			fieldtype: "Attach",
	// 		  },
	// 		],
	// 		primary_action_label: "Submit",
	// 		primary_action(values) {
	// 			// if (values.file.split(".")[1].toLowerCase() == "csv") {
	// 			//   // pass
	// 			// } else {
	// 			//   frappe.throw("Other than CSV file format not supported");
	// 			// }
	// 		  frappe.call({
	// 			method: "ibg_marico_oms.ibg_marico_oms.doctype.ibg_order.ibg_order.order_file_upload",
	// 			args: {
	// 			  upload_file: values.file,
	// 			  doc_name : frm.doc.name
	// 			},  
	// 			freeze: false,
	// 		  });
	// 		  d.hide();
	// 		},
	// 	  });
	// 	  d.show();
	// 	}, __("Utilities"));
	//   }
	},
	before_workflow_action: (frm) => {
		var is_ibg = frappe.user_roles.find((role) => role === "IBG Finance");
		var is_supuser = frappe.user_roles.find((role) => role === "System Manager");
		if ((is_ibg || is_supuser) && (frm.selected_workflow_action === "Reject" || frm.selected_workflow_action === "Hold")) {
            
            var me = this;
            var d = new frappe.ui.Dialog({
                title: __('Reason for Rejection/Hold'),
                fields: [
                    {
                        "label": "Remarks",
						"fieldname": "remarks",
                        "fieldtype": "Small Text",
                        "reqd": 1,
                    }
                ],
                primary_action: function() {
                    var data = d.get_values();
                    let reason_for_reject = 'Reason for Rejection/Hold: ' + data.remarks;
                    if (window.timeout){
						clearTimeout(window.timeout)
						delete window.timeout
					}
					window.timeout=setTimeout(function(){
						frm.set_value("remarks",data.remarks) 
						frm.refresh_field("remarks")              
						frm.save()
					},2500)
                    
                    frappe.call({
                        callback: function(r) {
                            frm.reload_doc();
                            d.hide();
                        }
                    });                    
                }
            });
            d.show();          
        }

    },
	order_items_on_form_rendered(frm, cdt, cdn) {
		var is_true = frappe.user_roles.find((role) => role === "Supply Chain");
		var is_fin = frappe.user_roles.find((role) => role === "IBG Finance");
		if (is_true || is_fin) {
			frm.fields_dict["order_items"].grid.wrapper.find(".grid-shortcuts").hide();
			frm.fields_dict["order_items"].grid.wrapper.find(".grid-delete-row").hide();
			frm.fields_dict["order_items"].grid.wrapper.find(".grid-insert-row-below").hide();
			frm.fields_dict["order_items"].grid.wrapper.find(".grid-insert-row").hide();
			frm.fields_dict["order_items"].grid.wrapper.find(".grid-duplicate-row").hide();
			frm.fields_dict["order_items"].grid.wrapper.find(".grid-append-row").hide();
		}
  },
});
