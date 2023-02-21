# Copyright (c) 2023, Atrina Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt
from __future__ import unicode_literals

import frappe
import pandas as pd
import ibg_marico_oms
from frappe.model.document import Document
from frappe.utils.csvutils import read_csv_content
from frappe import _

class IBGOrder(Document):
    pass
	# def before_save(self):
        # if (self.status == "Rejected by IBG Finance" or self.status == "On Hold by IBG Finance") and not self.remarks:
        #     frappe.throw(_("Please enter valid reason in remarks"))

@frappe.whitelist()
def ibg_order_template():
    try:
        data = []
        df = pd.DataFrame(
            data,
            columns=[
                "Country",
                "Customer",
                "Bill To",
                "Ship To",
                "Order ETD (yyyy/mm/dd)",
                "FG Code (Order Items)",
                "Qty in cases (Order Items)"
            ],
        )
        file_name = "IBG_Order_{}".format(frappe.utils.now_datetime())
        sheet_name = "IBG_Order"
        return ibg_marico_oms.download_file(
            dataframe=df,
            file_name=file_name,
            file_extention="xlsx",
            sheet_name=sheet_name,
        )
    except Exception as e:
        frappe.log_error(e)

@frappe.whitelist()
def order_file_upload(upload_file):
    files = frappe.get_all("File", filters={"file_url": upload_file}, page_length=1)
    file = frappe.get_doc("File", files[0].name)
    file_path = file.get_full_path()
    with open(file_path, "r") as upfile:
        fcontent = upfile.read()

    csv_data = read_csv_content(fcontent)
    parent = ""

    for i in csv_data[1:]:
        if not i[0] and not i[1] and not i[2] and not i[3] and not i[4]:
            if parent:
                item = frappe.get_doc(
                    {
                        "doctype": "IBG Order Items",
                        "parent": parent,
                        "parentfield": "order_items",
                        "parenttype": "IBG Order",
                        "fg_code": i[5],
                        "product_description":frappe.db.get_value(
                            "FG Code",
                            {"name": i[5]},
                            "product_description",
                        ),

                        "qty_in_cases": i[6],
                        "order_created_on": frappe.utils.now_datetime().date()
                    }
                ).insert(ignore_permissions=True)
                frappe.db.commit()
        else:
            ibg_order = frappe.get_doc(
                dict(
                    doctype="IBG Order",
                    country=i[0],
                    customer=i[1],
                    bill_to=i[2],
                    ship_to=i[3],
                    order_etd=i[4],
                    )
            ).insert(ignore_permissions=True)
            frappe.db.commit()

            parent = ibg_order.name

            item = item = frappe.get_doc(
                {
                    "doctype": "IBG Order Items",
                    "parent": parent,
                    "parentfield": "order_items",
                    "parenttype": "IBG Order",
                    "fg_code": i[5],
                    "product_description":frappe.db.get_value(
                        "FG Code",
                        {"name": i[5]},
                        "product_description",
                    ),

                    "qty_in_cases": i[6],
                    "order_created_on": frappe.utils.now_datetime().date()
                }
            ).insert(ignore_permissions=True)
            frappe.db.commit()


# @frappe.whitelist()
# def firm_plan_report(doc_filters):
#     if len(doc_filters) == 2:
#         doc_filters = {"creation_date": str(frappe.utils.now_datetime().date())}
    
#     data =[]
#     df = pd.DataFrame(
#             data,
#             columns=[
#                 "Customer Code"
#                 "Customer Name",
#                 "Country",
#                 "Order ID"
#                 "Month",
#                 "FG Code",
#                 "Rate/Cs",
#                 "Currency",
#                 "Units/Cs",
#                 "SAP plant Code",
#                 "Material Group",
#                 "Product description",
#                 "Qty in Case",
#                 "Qty in Nos",
#                 "Qty in kl",
#                 "Order Value"
#             ],
#         )

#     ibg_order_doc = frappe.get_all(
#         "IBG Order",
#         filters=doc_filters,
#         fields=["*"],
#     )

#     for i in ibg_order_doc:
#         df.loc[len(df.index)] = [frappe.db.get_value("Customer",{"name": i.customer},"customer_code"), i.customer, i.country, i.name, i.created_date, i.order_items[0]["fg_code"], ""]

#     if ibg_order_doc == []:
#         frappe.throw(("Record does not exist"))
#     final = pd.DataFrame([c.values() for c in ibg_order_doc], index=None)
#     file_name = "Firm_Plan_Report_{}".format(frappe.utils.now_datetime())
#     sheet_name = "Firm Plan Report"
#     return ibg_marico_oms.download_file(
#         dataframe=final,
#         file_name=file_name,
#         file_extention="xlsx",
#         sheet_name=sheet_name,
#     )


# @frappe.whitelist()
# def set_approver_name(doc, method):
#     print("Document", doc)
	
#     if doc.status in ['Approved by IBG Finance', 'Approved by Supply Chain']:
#         get_approver_name = frappe.db.get_value('Comment', {'reference_name':doc.name, 'content':['IN',['Approved by IBG Finance', 'Approved by Supply Chain']]}, 'owner')
#         print("Approver :", doc.modified_by)
#         # frappe.db.set_value(doc.doctype, {'name': doc.name}, 'approved_by', doc.modified_by)
#         order_doc = frappe.get_doc("IBG Order", doc.name)
#         order_doc.approved_by = doc.modified_by
#         order_doc.save()
#         frappe.db.commit()