frappe.listview_settings["FG Code"] = {
    hide_name_column: true,
    refresh: function (listview) {
      var is_true = frappe.user_roles.find((role) => role === "System Manager");
      if (is_true || frappe.session.user == "Administrator") {
        // console.log("INSIDE REFRESH")
        listview.page.add_menu_item(__("Download Product Units Template"), function () {
          frappe.call({
            method:
            "ibg_marico_oms.ibg_marico_oms.doctype.fg_code.fg_code.fgcode_unitscs_template",
            freeze: true,
            callback: (res) => {
              window.open(res.message);
            },
          });
        });
      };
      if (is_true || frappe.session.user == "Administrator") { 
      listview.page.add_menu_item(__("Upload Units/CS File"), function () {
        let d = new frappe.ui.Dialog({
          title: "Enter details",
          fields: [
            {
              label: "Upload CSV",
              fieldname: "file",
              fieldtype: "Attach",
            },
          ],
          primary_action_label: "Submit",
          primary_action(values) {
              if (values.file.split(".")[1].toLowerCase() == "csv") {
                // pass
              } else {
                frappe.throw("Other than CSV file format not supported");
              }
            frappe.call({
              method: "ibg_marico_oms.ibg_marico_oms.doctype.fg_code.fg_code.fgcode_unitscs_file_upload",
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
  