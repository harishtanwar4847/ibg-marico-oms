

frappe.listview_settings["OBD"] = {
    hide_name_column: true,
    refresh: function (listview) {
        listview.page.sidebar.remove(); // this removes the sidebar
		listview.page.wrapper.find(".layout-main-section-wrapper").removeClass("col-md-10");
    }

}