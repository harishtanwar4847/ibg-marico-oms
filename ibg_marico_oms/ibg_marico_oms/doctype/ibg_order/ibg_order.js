// Copyright (c) 2023, Atrina Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('IBG Order', {
	refresh: function(frm) {
		var is_true = frappe.user_roles.find((role) => role === "Supply Chain");
		var is_ibg = frappe.user_roles.find((role) => role === "IBG Finance");
		if (!is_true) {
			frm.set_df_property("order_type", "read_only", 1);
			frm.set_df_property("division", "read_only", 1);
			frm.set_df_property("sales_organizational", "read_only", 1);
			frm.set_df_property("sales_office", "read_only", 1);
			frm.set_df_property("distribution_channel", "read_only", 1);
			frm.set_df_property("sales_group", "read_only", 1);
		}
		if (!is_ibg || frappe.session.user != "Administrator") {
			frm.set_df_property("remarks", "read_only", 1);
		}
	},
	before_workflow_action: (frm) => {
		var is_ibg = frappe.user_roles.find((role) => role === "IBG Finance");
        if (is_ibg && (frm.selected_workflow_action === "Reject" || frm.selected_workflow_action === "Hold")) {
            
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
                        // method: "frappe.desk.form.utils.add_comment",
                        // args: {
                        //     reference_doctype: frm.doc.doctype,
                        //     reference_name: frm.doc.name,
                        //     content: __(reason_for_reject),
                        //     comment_email: frappe.session.user,
                        //     comment_by: frappe.session.user_fullname
                        // },
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
