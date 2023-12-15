

frappe.listview_settings["OBD"] = {
    hide_name_column: true,
    colwidths: {"customer_name": 50},

    refresh: function (listview) {
        listview.page.sidebar.remove(); // this removes the sidebar
		listview.page.wrapper.find(".layout-main-section-wrapper").removeClass("col-md-10");
    }

}
