# Copyright (c) 2023, Atrina Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt
from __future__ import unicode_literals
import calendar
from random import randint

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
from zeep import Client
from zeep.transports import Transport
from requests import Session
from requests.auth import HTTPBasicAuth
from zeep import Client

class IBGOrder(Document):
    def before_save(self):
        user_roles = frappe.db.get_values(
            "Has Role", {"parent": frappe.session.user, "parenttype": "User"}, ["role"]
        )
        user_role = []
        for i in list(user_roles):
            user_role.append(i[0])
        
        # if self.status == "Pending":
        #     self.order_type = ""
        #     self.sales_organizational = ""
        #     self.distribution_channel = ""
        #     self.division = ""
        #     self.sales_office = ""
        #     self.sales_group = ""
        
        if "IBG Finance" in user_role or "System Manager" in user_role:
            if (self.status == "Rejected by IBG Finance" or self.status == "On Hold by IBG Finance") and not self.remarks:
                frappe.throw(_("Please enter valid reason in remarks"))

        for i in self.order_items:
            if i.billing_rate:
                i.order_value = float(i.qty_in_cases) * float(i.billing_rate)
                
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
                if not i.rate_valid_from:
                    count_valid_from +=1
                if not i.rate_valid_to:
                    count_valid_to +=1

            if count_billing_rate > 0 and self.status == "Approved by IBG Finance":
                frappe.throw(_("Please enter the billing rate in the order items"))
            if count_order_value > 0 and self.status == "Approved by IBG Finance":
                frappe.throw(_("Please enter the order value in the order items"))
            if count_valid_from > 0 and self.status == "Approved by IBG Finance":
                frappe.throw(_("Please enter the Valid from date in the order items"))
            if count_valid_to > 0 and self.status == "Approved by IBG Finance":
                frappe.throw(_("Please enter the Valid to date in the order items"))

        if "IBG Finance" in user_role and self.status == 'Approved by IBG Finance' and not self.approved_by_ibgfinance:
            self.approved_by_ibgfinance = self.modified_by
        
        if self.status == 'Rejected by IBG Finance':
            modified_by = self.modified_by
            user_roles = frappe.db.get_values("Has Role", {"parent": modified_by, "parenttype": "User"}, ["role"])
            user_role = []
            for i in list(user_roles):
                user_role.append(i[0])
            if "Initiator" in user_role:
                self.status = 'Pending'
                self.workflow_state = 'Pending'
        

    def before_submit(self):
        sap_number = sap_rfc_data(self)
        frappe.log_error(
                message= "SAP Error -\n{}".format(sap_number),
                title="SAP Order Number Generation Error",
            )
        if len(sap_number['sap_error']) > 1:
            frappe.throw(_(sap_number['sap_error'][1]['ERROR_MSG']))

        if len(sap_number['sap_so_number']) > 1:
            self.sap_so_number = sap_number['sap_so_number'][1]['SALES_ORD']
            frappe.msgprint("SAP SO number generated is {}".format(sap_number['sap_so_number'][1]['SALES_ORD']))

        user_roles = frappe.db.get_values(
            "Has Role", {"parent": frappe.session.user, "parenttype": "User"}, ["role"]
        )
        user_role = []
        for i in list(user_roles):
            user_role.append(i[0])
        
        if "Supply Chain" in user_role and (not self.order_type or not self.division or not self.sales_organizational or not self.sales_office or not self.distribution_channel or not self.sales_group):
            frappe.throw(_("Please fill the Supply Chain section"))
        if self.status in ['Approved by Supply Chain']:
            self.approved_by_supplychain = self.modified_by

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
def order_file_upload(upload_file, doc_name = None):
    files = frappe.get_all("File", filters={"file_url": upload_file}, page_length=1)
    file = frappe.get_doc("File", files[0].name)
    file_path = file.get_full_path()
    with open(file_path, "rb") as upfile:
        fcontent = upfile.read()

    if ((file.file_name).split('.'))[1] == 'xlsx':
        excelFile = pd.read_excel (fcontent)
        file_name = (file.file_name).split('.')
        csv_name = "{order}{rand}.csv".format(order = file_name[0],rand = randint(1111,9999))
        name_csv = excelFile.to_csv (csv_name, index = None, header=True)
        with open(csv_name, "r") as csv_upfile:
            csv_fcontent = csv_upfile.read()
        csv_data = read_csv_content(csv_fcontent)
    else:
        csv_data = read_csv_content(fcontent)

    parent = ""
    frappe.log_error(
                message= "SAP Error -\n{}"
                + "\n\nOrder details -\n{}".format(type(csv_data[1][2]), csv_data[1]),
                title="Upload File format",
            )
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
                    bill_to=str(int(float(i[2]))),
                    ship_to=str(int(float(i[3]))),
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
def firm_plan_report():
    data =[]
    order_name_list =[]
    curr_first = frappe.utils.now_datetime().date().replace(day=1)
    calendar.monthrange(curr_first.year, curr_first.month)
    res = calendar.monthrange(curr_first.year, curr_first.month) 
    curr_last = frappe.utils.now_datetime().date().replace(day=res[1])
    
    order_items = frappe.get_all(
        "IBG Order Items",
        filters={"order_created_on" :["BETWEEN", [curr_first, curr_last]]},
        fields=["*"],
    )
    order_list = frappe.get_all("IBG Order",fields=["name"])
    for i in order_list:
        order_name_list.append(i.name)


    if order_items:
        for i in order_items:
            if i.parent in order_name_list:
                order_doc = frappe.get_doc("IBG Order", i.parent)
                if order_doc and order_doc.status == "Approved by Supply Chain":
                    units_cs = frappe.db.get_value("FG Code",{"fg_code": i.fg_code},"unitscs",)
                    material_group = frappe.db.get_value("FG Code",{"fg_code": i.fg_code},"material_group",)
                    num = ''
                    for i in material_group:
                        if i.isdigit():
                            num+=i
                    qty = (int(num)/1000)
                    cust_code = frappe.db.get_value("IBG Distributor",{"customer_name": order_doc.customer},"customer_code",)

                    curr_month = calendar.month_abbr[order_doc.created_date.month]
                    next_month = calendar.month_abbr[(order_doc.created_date.month)+1]
                    next_nd_month = calendar.month_abbr[(order_doc.created_date.month)+2]
                    order_dict = {"Customer Code" : cust_code, "Customer Name" : order_doc.customer, "Country" : order_doc.country, "Order ID" : order_doc.name, "Month" : order_doc.created_date, "FG Code" : i.fg_code, "Rate/Cs" : i.billing_rate, "Currency" : i.units, "Units/Cs": units_cs, "SAP Plant Code" : "", "Material Group" : material_group, "Product Description" : i.product_description, "Qty in Case({})".format(curr_month) : i.qty_in_cases, "Qty in Nos({})".format(curr_month) : (float(i.qty_in_cases) * float(units_cs)), "Qty in kl({})".format(curr_month) : (((float(i.qty_in_cases) * float(units_cs))*qty)/1000), "Order Value({})".format(curr_month) : i.order_value, "Qty in Case({})".format(next_month) : "", "Qty in Nos({})".format(next_month) : "", "Qty in kl({})".format(next_month) : "", "Order Value({})".format(next_month) : "", "Qty in Case({})".format(next_nd_month) : "", "Qty in Nos({})".format(next_nd_month) : "", "Qty in kl({})".format(next_nd_month) : "", "Order Value({})".format(next_nd_month) : ""}

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
def sap_rfc_data(doc):
    try:
        doc = frappe.get_doc('IBG Order', doc.name)
        wsdl = 'http://14.140.115.225:8000/sap/bc/soap/wsdl11?services=ZBAPI_IBG_ORD&sap-client=540&sap-user=portal&sap-password=portal@345'
        client = Client(wsdl)
        session = Session()
        session.auth = HTTPBasicAuth("portal", "portal@345")
        client=Client(wsdl,transport=Transport(session=session))
        items = []
        for i in doc.order_items:
            order_dict = {'SALES_ORG': doc.sales_organizational,
                 'ORD_TYPE' : doc.order_type,
                 'DIST_CHAN': doc.distribution_channel, 
                 'DIVISION': doc.division,
                 'BILL_TO' : doc.bill_to, 
                 'SHIP_TO' : doc.ship_to,
                 'IBG_ORD': doc.name, 
                 'IBG_ORD_DT' : doc.created_date,
                 'MATERIAL' : i.fg_code, 
                 'QTY' : i.qty_in_cases, 
                 'UOM': '', 
                 'PLANT' : '', 
                 'ORD_ETD' : doc.order_etd}
            items.append(order_dict)

        request_data={'IT_ERR':'','IT_RET' :'','IT_SO':{'item':items}}
        response=client.service.ZBAPI_IBG_ORD(**request_data)
        order_details = response['IT_SO']['item']
        if len(response['IT_ERR']['item']) > 1:
            frappe.log_error(
                message= "SAP Error -\n{}"
                + "\n\nFile name -\n{}\n\nOrder details -\n{}".format(response['IT_ERR']['item'][1]['ERROR_MSG'] , doc.name, order_details),
                title="SAP Order Number Generation Error",
            )        
        sap_response = {"sap_error" : response['IT_ERR']['item'] , "sap_so_number" : response['IT_RET']['item']}

        return sap_response
        
    except Exception as e:
        frappe.log_error(
            message=frappe.get_traceback()
            + "\n\nFile name -\n{}".format(doc.name),
            title="SAP Order Number Generation",
        )

@frappe.whitelist()
def sap_price():
    try:
        wsdl = "http://14.140.115.225:8000/sap/bc/soap/wsdl11?services=ZBAPI_PRICE_MASTER&sap-client=540&sap-user=portal&sap-password=portal%40345"
        client = Client(wsdl)
        session = Session()
        session.auth = HTTPBasicAuth("portal", "portal@345")
        client=Client(wsdl,transport=Transport(session=session))
        request_data={'IT_PRICE': '','SALES_ORG' : 'MME'}
        response=client.service.ZBAPI_PRICE_MASTER(**request_data)
        for i in response:
            fgcode_list = frappe.get_all("FG Code", filters = {"fg_code": int(i['MATERIAL'])}, fields=["*"])
            if len(fgcode_list) > 0:
                fgcode_doc = frappe.get_doc("FG Code", fgcode_list[0].name)
                fgcode_doc.valid_from =i['VALID_FROM']
                fgcode_doc.valid_to = i['VALID_TO']
                fgcode_doc.rate = float(i['RATE'])
                fgcode_doc.currency = i['CURRENCY']
                fgcode_doc.save(ignore_permissions = True)
                frappe.db.commit()

    except Exception as e:
        frappe.log_error(
            message=frappe.get_traceback(),
            title="SAP Price Master Entry",
        )

# @frappe.whitelist()
# def ibg_order_items_template():
#     try:
#         data = []
#         df = pd.DataFrame(
#             data,
#             columns=[
#                 "FG Code (Order Items)",
#                 "Qty in cases (Order Items)"
#             ],
#         )
#         file_name = "IBG_Order_{}".format(frappe.utils.now_datetime())
#         sheet_name = "IBG_Order"
#         return ibg_marico_oms.download_file(
#             dataframe=df,
#             file_name=file_name,
#             file_extention="xlsx",
#             sheet_name=sheet_name,
#         )
#     except Exception as e:
#         frappe.log_error(e)

# @frappe.whitelist()
# def order_items_file_upload(upload_file, doc_name):
#     files = frappe.get_all("File", filters={"file_url": upload_file}, page_length=1)
#     file = frappe.get_doc("File", files[0].name)
#     file_path = file.get_full_path()
#     with open(file_path, "r") as upfile:
#         fcontent = upfile.read()

#     csv_data = read_csv_content(fcontent)
#     parent = doc_name

#     for i in csv_data[1:]:
#         if parent:
#             item = frappe.get_doc(
#                 {
#                     "doctype": "IBG Order Items",
#                     "parent": parent,
#                     "parentfield": "order_items",
#                     "parenttype": "IBG Order",
#                     "fg_code": i[0],
#                     "product_description":frappe.db.get_value(
#                         "FG Code",
#                         {"name": i[0]},
#                         "product_description",
#                     ),
#                     "qty_in_cases": i[1],
#                     "order_created_on": frappe.utils.now_datetime().date()
#                 }
#             ).insert(ignore_permissions=True)
#             frappe.db.commit()
