frappe.listview_settings["IBG Order"] = {
    hide_name_column: true,
    refresh: function (listview) {
      listview.page.sidebar.remove(); // this removes the sidebar
		  listview.page.wrapper.find(".layout-main-section-wrapper").removeClass("col-md-10");
      var is_true = frappe.user_roles.find((role) => role === "Supply Chain");
      var is_supuser = frappe.user_roles.find((role) => role === "System Manager");
      if (is_true || is_supuser || frappe.session.user == "Administrator") {
        listview.page.add_menu_item(
          __("Firm Plan Report"),
          function () {
            frappe.call({
              method:
                "ibg_marico_oms.ibg_marico_oms.doctype.ibg_order.ibg_order.firm_plan_report",
              freeze: true,
              args: {
                doc_filters: frappe
                  .get_user_settings("IBG Order")
                  ["List"].filters.map((filter) => filter.slice(1, 4)),
              },      
              callback: (res) => {
                window.open(res.message);
              },
            });
          }
        );
      }
    },
    onload: function (listview) {
      var is_true = frappe.user_roles.find((role) => role === "Initiator");
      var is_supuser = frappe.user_roles.find((role) => role === "System Manager");
      if (is_true || is_supuser || frappe.session.user == "Administrator") {
        listview.page.add_menu_item(__("Download Order Template"), function () {
          frappe.call({
            method:
            "ibg_marico_oms.ibg_marico_oms.doctype.ibg_order.ibg_order.ibg_order_template",
            freeze: true,
            args: {
              doc_filters: frappe
                .get_user_settings("IBG Order")
                ["List"].filters.map((filter) => filter.slice(1, 4)),
            },
            callback: (res) => {
              window.open(res.message);
            },
          });
        });
      };
      if (is_true|| is_supuser || frappe.session.user == "Administrator") { 
      listview.page.add_menu_item(__("Upload Order"), function () {
        let d = new frappe.ui.Dialog({
          title: "Enter details",
          fields: [
            {
              label: "Upload CSV/Excel File",
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
              // if (!(values.file.split(".")[1].toLowerCase() == "csv") || !(values.file.split(".")[1].toLowerCase() == "xlsx")) {
              //   pass
              // } else {
              //   frappe.throw("Other than CSV/XLSX file format not supported");
              // }
            frappe.call({
              method: "ibg_marico_oms.ibg_marico_oms.doctype.ibg_order.ibg_order.order_file_upload",
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
  