frappe.listview_settings["Bill To"] = {
    hide_name_column: true,
    refresh: function (listview) {
        console.log("AAlo aat")
        listview.page.sidebar.remove(); // this removes the sidebar
		listview.page.wrapper.find(".layout-main-section-wrapper").removeClass("col-md-10");
        var is_true = frappe.user_roles.find((role) => role === "System Manager");
        if (is_true || frappe.session.user == "Administrator") {
            listview.page.add_menu_item(__("Download Bill To Template"), function () {
            frappe.call({
                method:
                "ibg_marico_oms.ibg_marico_oms.doctype.bill_to.bill_to.bill_to_template",
                freeze: true,
                callback: (res) => {
                window.open(res.message);
                },
            });
            });
        };
        if (is_true || frappe.session.user == "Administrator") { 
        listview.page.add_menu_item(__("Upload Bill To File"), function () {
            let d = new frappe.ui.Dialog({
            title: "Enter details",
            fields: [
                {
                label: "Upload CSV/Excel",
                fieldname: "file",
                fieldtype: "Attach",
                },
                {
                fieldname: "columnbreak",
                fieldtype: "Column Break",
                label: "*Select My Device to upload the file"
                },
            ],
            primary_action_label: "Submit",
            primary_action(values) {
                // if (values.file.split(".")[1].toLowerCase() == "csv") {
                //   // pass
                // } else {
                //   frappe.throw("Other than CSV file format not supported");
                // }
                frappe.call({
                method: "ibg_marico_oms.ibg_marico_oms.doctype.bill_to.bill_to.bill_to_file_upload",
                args: {
                    upload_file: values.file,
                },  
                freeze: false,
                });
                d.hide();
            },
            });
            d.show();
        });
        }
    }
};
    