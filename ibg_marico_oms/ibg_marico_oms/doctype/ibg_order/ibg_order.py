# Copyright (c) 2023, Atrina Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt
from __future__ import unicode_literals

import frappe
import pandas as pd
import ibg_marico_oms
from frappe.model.document import Document
from frappe.utils.csvutils import read_csv_content
from frappe import _
from datetime import datetime
from itertools import groupby
import xmltodict
import requests
import pyodata
import pandas as pd
import io
import json

class IBGOrder(Document):
    def before_save(self):
        user_roles = frappe.db.get_values(
            "Has Role", {"parent": frappe.session.user, "parenttype": "User"}, ["role"]
        )
        user_role = []
        for i in list(user_roles):
            user_role.append(i[0])
        if "IBG Finance" in user_role or "System Manager" in user_role:
            if (self.status == "Rejected by IBG Finance" or self.status == "On Hold by IBG Finance") and not self.remarks:
                frappe.throw(_("Please enter valid reason in remarks"))
        
        count_billing_rate = 0
        count_order_value = 0
        count_valid_from = 0
        count_valid_to = 0
        if "IBG Finance" in user_role:
            for i in self.order_items:
                if not i.billing_rate or float(i.billing_rate) <= 0:
                    count_billing_rate += 1
                if not i.order_value or float(i.order_value) <= 0:
                    count_order_value += 1
                if not i.billing_rate:
                    count_valid_from +=1
                if not i.billing_rate:
                    count_valid_to +=1

            if count_billing_rate > 0 and self.status == "Approved by IBG Finance":
                frappe.throw(_("Please enter the billing rate in the order items"))
            if count_order_value > 0 and self.status == "Approved by IBG Finance":
                frappe.throw(_("Please enter the order value in the order items"))
            if count_valid_from > 0 and self.status == "Approved by IBG Finance":
                frappe.throw(_("Please enter the Valid from date in the order items"))
            if count_valid_to > 0 and self.status == "Approved by IBG Finance":
                frappe.throw(_("Please enter the Valid to date in the order items"))

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


@frappe.whitelist()
def firm_plan_report(doc_filters):
    data =[]

    order_items = frappe.get_all(
        "IBG Order Items",
        filters=doc_filters,
        fields=["*"],
    )

    if order_items:
        for i in order_items:
            order_doc = frappe.get_doc("IBG Order", i.parent)
            currency = [''.join(g) for _, g in groupby(i.billing_rate, str.isalpha)][1]
            order_dict = {"Customer Code" : "", "Customer Name" : order_doc.customer, "Country" : order_doc.country, "Order ID" : order_doc.name, "Month" : order_doc.created_date, "FG Code" : i.fg_code, "Rate/Cs" : i.billing_rate, "Currency" : currency, "Units/Cs": "", "SAP Plant Code" : "", "Material Group" : "", "Product Description" : i.product_description, "Qty in Case" : i.qty_in_cases, "Qty in Nos" : "", "Qty in kl" : "", "Order Value" : i.order_value}

            data.append(order_dict)
        
    if data == []:
        frappe.throw(("Record does not exist"))
    final = pd.DataFrame(data)
    file_name = "Firm_Plan_Report_{}".format(frappe.utils.now_datetime())
    sheet_name = "Firm Plan Report"
    return ibg_marico_oms.download_file(
        dataframe=final,
        file_name=file_name,
        file_extention="xlsx",
        sheet_name=sheet_name,
    )


@frappe.whitelist()
def set_approver_name(doc, method):	
    if doc.status in ['Approved by IBG Finance', 'Approved by Supply Chain']:
        order_doc = frappe.get_doc("IBG Order", doc.name)
        order_doc.approved_by = doc.modified_by
        order_doc.save()
        frappe.db.commit()
