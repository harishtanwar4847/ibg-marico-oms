// Copyright (c) 2023, Atrina Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('IBG Order', {
	

	refresh: function(frm) {
		frm.add_custom_button(__('buttonName'), function(){
			var selected_attachments = frm.doc.selected_attachments;
			if (selected_attachments && selected_attachments.length > 0) {
				frappe.call({
					method: 'ibg_marico_oms.ibg_marico_oms.doctype.ibg_order.send_attachments_email',
					args: {
						selected_attachments: selected_attachments
					},
					callback: function(response) {
						if (response.message) {
							frappe.msgprint(response.message);
						}
					}
				});
			}else {
                frappe.msgprint("No attachments selected.");
            }

		  });
		  
		if (frm.doc.__islocal === 1){
			frm.set_value("remarks","") 
			frm.set_value("created_date",new Date().toJSON().slice(0, 10)) 
			frm.set_value("approved_by_ibgfinance","") 
			frm.set_value("approved_by_supplychain","") 
			frm.set_value("order_type","") 
			frm.set_value("sales_organizational","") 
			frm.set_value("distribution_channel","") 
			frm.set_value("division","") 
			frm.set_value("sales_office","") 
			frm.set_value("sales_group","") 
			frm.set_value("sap_so_number","")
			frm.set_value("status","Pending")
			frm.refresh_field("remarks")              
			frm.refresh_field("created_date")              
			frm.refresh_field("approved_by_ibgfinance")              
			frm.refresh_field("approved_by_supplychain")
			frm.refresh_field("order_type") 
			frm.refresh_field("sales_organizational") 
			frm.refresh_field("distribution_channel") 
			frm.refresh_field("division") 
			frm.refresh_field("sales_office") 
			frm.refresh_field("sales_group") 
			frm.refresh_field("sap_so_number")              
			frm.refresh_field("status")
		}
		var is_ini = frappe.user_roles.find((role) => role === "Initiator");
		var is_ibg = frappe.user_roles.find((role) => role === "IBG Finance");
		if (is_ibg || is_ini) {
			frm.set_df_property("order_type", "read_only", 1);
			frm.set_df_property("division", "read_only", 1);
			frm.set_df_property("sales_organizational", "read_only", 1);
			frm.set_df_property("sales_office", "read_only", 1);
			frm.set_df_property("distribution_channel", "read_only", 1);
			frm.set_df_property("sales_group", "read_only", 1);
		}
		frm.page.sidebar.remove(); // this removes the sidebar
		frm.page.wrapper.find(".layout-main-section-wrapper").removeClass("col-md-10"); // this removes class "col-md-10" from content block, which sets width to 83%
	},
	before_workflow_action: (frm) => {
		var is_ibg = frappe.user_roles.find((role) => role === "IBG Finance");
		var is_sc = frappe.user_roles.find((role) => role === "Supply Chain");
		var is_supuser = frappe.user_roles.find((role) => role === "System Manager");	
		if ((is_ibg || is_supuser) && (frm.doc.status === "Pending") && (frm.selected_workflow_action === "Reject")) {
            var d = new frappe.ui.Dialog({
                title: __('Reason for Rejection'),
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
                    if (window.timeout){
						clearTimeout(window.timeout)
						delete window.timeout
					}
					window.timeout=setTimeout(function(){
						frm.set_value("remarks",data.remarks) 
						frm.set_value("status","Rejected by IBG Finance") 
						frm.set_value("workflow_state","Rejected by IBG Finance") 
						frm.refresh_field("remarks")              
						frm.save()
					},50)
                    
					d.hide();                  
                }
            });
            d.show();          
        }
		if ((is_sc || is_supuser) && (frm.doc.status === "Approved by IBG Finance") && (frm.selected_workflow_action === "Reject")) {
            var d = new frappe.ui.Dialog({
                title: __('Reason for Rejection'),
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
                    if (window.timeout){
						clearTimeout(window.timeout)
						delete window.timeout
					}
					window.timeout=setTimeout(function(){
						frm.set_value("supplychain_remarks",data.remarks) 
						frm.set_value("status","Rejected by Supply Chain") 
						frm.set_value("workflow_state","Rejected by Supply Chain") 
						frm.refresh_field("supplychain_remarks")              
						frm.save()
					},50)
                    
					d.hide();                  
                }
            });
            d.show();          
        }
		if ((is_ibg || is_supuser) && (frm.selected_workflow_action === "Hold")) {
            var d = new frappe.ui.Dialog({
                title: __('Reason for Hold'),
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
                    if (window.timeout){
						clearTimeout(window.timeout)
						delete window.timeout
					}
					window.timeout=setTimeout(function(){
						frm.set_value("remarks",data.remarks) 
						frm.set_value("status","On Hold by IBG Finance") 
						frm.set_value("workflow_state","On Hold by IBG Finance") 
						frm.refresh_field("remarks")              
						frm.save()
					},50)
                    
					d.hide();                   
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
