frappe.listview_settings["IBG Order"] = {
    hide_name_column: true,
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
    },
  };
  