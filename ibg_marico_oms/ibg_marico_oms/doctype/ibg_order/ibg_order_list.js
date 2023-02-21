frappe.listview_settings["IBG Order"] = {
    hide_name_column: true,
    // refresh: function (listview) {
    //   var is_true = frappe.user_roles.find((role) => role === "Supply Chain");
    //   if (is_true || frappe.session.user == "Administrator") {
    //     listview.page.add_inner_button(
    //       __("Firm Plan Report"),
    //       function () {
    //         frappe.call({
    //           method:
    //             "ibg_marico_oms.ibg_marico_oms.doctype.ibg_order.ibg_order.firm_plan_report",
    //           freeze: true,
    //           args: {
    //             doc_filters: frappe
    //               .get_user_settings("IBG Order")
    //               ["List"].filters.map((filter) => filter.slice(1, 4)),
    //           },
    //           callback: (res) => {
    //             window.open(res.message);
    //           },
    //         });
    //       }
    //     );
    //   }
    // },  
    onload: function (listview) {
      var is_true = frappe.user_roles.find((role) => role === "Initiator");
      if (is_true || frappe.session.user == "Administrator") {
        listview.page.add_inner_button(
          __("Download Template"),
          function () {
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
          }
        );
      }     
      if (is_true || frappe.session.user == "Administrator") {
        listview.page.add_inner_button(__("Order Upload"), function () {
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
      };
    },
  };
  