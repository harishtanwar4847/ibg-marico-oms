// Copyright (c) 2023, Atrina Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('IBG Order', {
	refresh: function(frm) {
		if (frm.doc.__islocal === 1){
			frm.set_value("remarks","") 
			frm.set_value("approved_by_ibgfinance","") 
			frm.set_value("approved_by_supplychain","") 
			frm.set_value("order_type","") 
			frm.set_value("sales_organizational","") 
			frm.set_value("distribution_channel","") 
			frm.set_value("division","") 
			frm.set_value("sales_office","") 
			frm.set_value("sales_group","") 
			frm.set_value("sap_so_number","")
			frm.set_value("status","")
			frm.refresh_field("remarks")              
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
			frm.save()
		}
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
	},
	onload: function(frm) {
		var is_initiator = frappe.user_roles.find((role) => role === "Initiator");
		if (is_initiator && frm.doc.status == 'Rejected by IBG Finance') {
			frm.set_df_property("country", "read_only", 1);
			frm.set_df_property("bill_to", "read_only", 1);
			frm.set_df_property("ship_to", "read_only", 1);
			frm.set_df_property("customer", "read_only", 1);
			frm.set_df_property("order_etd", "read_only", 1);
		}
	},
	before_workflow_action: (frm) => {
		var is_ibg = frappe.user_roles.find((role) => role === "IBG Finance");
		var is_supuser = frappe.user_roles.find((role) => role === "System Manager");
		if ((is_ibg || is_supuser) && (frm.selected_workflow_action === "Reject")) {
			console.log("Inside if condition")
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
					console.log("Inside primary action condition")
                    var data = d.get_values();
                    if (window.timeout){
						console.log("Inside timeout if condition")
						clearTimeout(window.timeout)
						delete window.timeout
						console.log("After delete condition")
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
		if ((is_ibg || is_supuser) && (frm.selected_workflow_action === "Hold")) {
			console.log("Inside if condition")
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
					console.log("Inside primary action condition")
                    var data = d.get_values();
                    if (window.timeout){
						console.log("Inside timeout if condition")
						clearTimeout(window.timeout)
						delete window.timeout
						console.log("After delete condition")
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
