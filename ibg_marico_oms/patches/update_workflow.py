# import frappe


# def execute():
#     frappe.db.sql("TRUNCATE `tabWorkflow`")
#     frappe.db.sql("TRUNCATE `tabWorkflow Document State`")
#     frappe.db.sql("TRUNCATE `tabWorkflow Transition`")
#     frappe.db.commit()

#     path = frappe.get_app_path("ibg_marico_oms", "patches", "imports", "workflow.csv")
#     frappe.core.doctype.data_import.data_import.import_file(
#         "Workflow", path, "Insert", console=True
#     )