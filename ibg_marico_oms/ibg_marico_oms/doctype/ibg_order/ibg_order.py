# Copyright (c) 2023, Atrina Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt
from __future__ import unicode_literals
import calendar
from random import randint
import re

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

class IBGOrder(Document):
    def before_save(self):
        user_roles = frappe.db.get_values(
            "Has Role", {"parent": frappe.session.user, "parenttype": "User"}, ["role"]
        )
        user_role = []
        for i in list(user_roles):
            user_role.append(i[0])

        price_update(doc=self)
        
        # if (("IBG Finance" in user_role) or ("System Manager" in user_role)) and self.status == "Approved by IBG Finance":
        #     price = sap_price(doc = self)
        #     price_data = []
        #     if price:
        #         for j in price:
        #             if (j['CUSTOMER'].isnumeric()==True) and (int(self.bill_to) == int(j['CUSTOMER'])):
        #                 price_data.append(j)
        #     if len(price_data) >= 1:
        #         for i in self.order_items:
        #             for j in price_data:
        #                 if int(i.fg_code) == int(j['MATERIAL']):
        #                     i.billing_rate = float(j['RATE'])
        #                     i.rate_valid_from = j['VALID_FROM']
        #                     i.rate_valid_to = j['VALID_TO']
        #                     i.units = j['CURRENCY']
        #     else:
        #         frappe.log_error(
        #             message= "Order Id -{}\n"
        #             + "Customer name -{}\n"
        #             + "Bill To Code -{}\n"
        #             + "Message - Price Data Unavailable.".format(self.name,self.customer,self.bill_to),
        #             title="Price Data unavailable in SAP Price BAPI",
        #         )
        #         # frappe.throw(_("Data for the Customer name ({})/Bill To ({}) unavailable in SAP.".format(self.customer, self.bill_to)))

            
        if "IBG Finance" in user_role or "System Manager" in user_role or "Supply Chain" in user_role:
            if (self.status == "Rejected by IBG Finance" or self.status == "On Hold by IBG Finance") and not self.remarks:
                frappe.throw(_("Please enter valid reason in remarks"))
            if self.status == "Rejected by Supply Chain" and not self.supplychain_remarks:
                frappe.throw(_("Please enter valid reason in remarks"))

        total_order_value = 0
        total_qty = 0
        for i in self.order_items:
            if i.billing_rate:
                i.order_value = float(i.qty_in_cases) * float(i.billing_rate)
                total_order_value += i.order_value
            total_qty += float(i.qty_in_cases)
        self.total_qty_in_cases = total_qty
        self.total_order_value = total_order_value
                
        count_billing_rate = 0
        count_order_value = 0
        count_valid_from = 0
        count_valid_to = 0
        if ("IBG Finance" in user_role) or ("System Manager" in user_role):
            for i in self.order_items:
                if not i.billing_rate or float(i.billing_rate) <= 0:
                    count_billing_rate += 1
                elif not i.order_value or float(i.order_value) <= 0:
                    count_order_value += 1
                elif not i.rate_valid_from:
                    count_valid_from +=1
                elif not i.rate_valid_to:
                    count_valid_to +=1

            if count_billing_rate > 0 and self.status == "Approved by IBG Finance":
                frappe.throw(_("Please enter the billing rate in the order items"))
            elif count_order_value > 0 and self.status == "Approved by IBG Finance":
                frappe.throw(_("Please enter the order value in the order items"))
            elif count_valid_from > 0 and self.status == "Approved by IBG Finance":
                frappe.throw(_("Please enter the Valid from date in the order items"))
            elif count_valid_to > 0 and self.status == "Approved by IBG Finance":
                frappe.throw(_("Please enter the Valid to date in the order items"))

        if "IBG Finance" in user_role and self.status == 'Approved by IBG Finance' and not self.approved_by_ibgfinance:
            self.approved_by_ibgfinance = self.modified_by
        
        if self.status == 'Rejected by IBG Finance' or self.status == "Rejected by Supply Chain" :
            modified_by = self.modified_by
            user_roles = frappe.db.get_values("Has Role", {"parent": modified_by, "parenttype": "User"}, ["role"])
            user_role = []
            for i in list(user_roles):
                user_role.append(i[0])
            if "Initiator" in user_role:
                self.status = 'Pending'
                self.workflow_state = 'Pending'
                self.remarks = ''
                self.supplychain_remarks =''

    def onload(self):
        price_update(doc=self)

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
            frappe.msgprint(_("SAP SO Number generated is {}".format(sap_number['sap_so_number'][1]['SALES_ORD'])))

        user_roles = frappe.db.get_values(
            "Has Role", {"parent": frappe.session.user, "parenttype": "User"}, ["role"]
        )
        user_role = []
        for i in list(user_roles):
            user_role.append(i[0])
        
        if "Supply Chain" in user_role and (self.status == "Approved by Supply Chain" or self.status == "Approved by IBG Finance") and (not self.order_type or not self.division or not self.sales_organizational or not self.distribution_channel):
            frappe.throw(_("Please fill the Supply Chain section"))
        if self.status in ['Approved by Supply Chain']:
            self.approved_by_supplychain = self.modified_by
        
    def on_submit(self):
        items = []
        for i in self.order_items:
            item_entry = frappe.get_doc(
                {
                    "doctype": "OBD Items",
                    "fg_code": i.fg_code,
                    "fg_description": i.product_description,
                    "sales_order_qty": i.qty_in_cases,
                }
            )
            items.append(item_entry)
        obd = frappe.get_doc(
            {
                "doctype" : "OBD",
                "ibg_order_id" : self.name,
                "sap_so_number" : self.sap_so_number,
                "items" : items
            }
        )
        obd.insert(ignore_permissions=True)
        frappe.db.commit()


@frappe.whitelist()
def ibg_order_template():
    try:
        data = []
        df = pd.DataFrame(
            data,
            columns=[
                "Country",
                "Customer Name",
                "Bill To",
                "Company Code",
                "Order ETD (yyyy-mm-dd)",
                "FG Code (Order Items)",
                "Qty in cases (Order Items)"
            ],
        )
        file_name = "IBG_Order_{}".format(frappe.utils.now_datetime().date())
        sheet_name = "IBG_Order"
        return ibg_marico_oms.download_file(
            dataframe=df,
            file_name=file_name,
            sheet_name=sheet_name,
        )
    except Exception as e:
        frappe.log_error(
            message=frappe.get_traceback(),
            title="IBG Order Download template Error",
        )

@frappe.whitelist()
def order_file_upload(upload_file, doc_name = None):
    try:
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

        parent_list = []
        parent = ""
        for i in csv_data[1:]:
            if not i[0] and not i[1] and not i[2] and not i[4]:
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
                            "created_date": frappe.utils.now_datetime().date()
                        }
                    ).insert(ignore_permissions=True)
                    frappe.db.commit()
            else:
                customer = frappe.get_all("IBG Distributor", filters={"name" : i[1]}, fields = ["name"])
                if len(customer) == 0:
                    frappe.throw(_("Please enter a Valid Customer Name in Customer column."))
                
                date_pattern_str1 = r'^\d{4}-\d{2}-\d{2}$'
                date_pattern_str2 = r'^\d{2}-\d{2}-\d{4}$'
                date_pattern_str3 = r'^\d{4}/\d{2}/\d{2}$'
                date_pattern_str4 = r'^\d{2}/\d{2}/\d{4}$'
                if re.match(date_pattern_str1, i[4]):
                    date = frappe.utils.datetime.datetime.strptime(i[4], "%Y-%m-%d")
                elif re.match(date_pattern_str2, i[4]):
                    date = frappe.utils.datetime.datetime.strptime(i[4], "%d-%m-%Y")
                elif re.match(date_pattern_str3, i[4]):
                    date = frappe.utils.datetime.datetime.strptime(i[4], "%Y/%m/%d")
                elif re.match(date_pattern_str4, i[4]):
                    date = frappe.utils.datetime.datetime.strptime(i[4], "%d/%m/%Y")
                else:
                    date = ""
                    frappe.throw(_("Please enter Order ETD date {} in valid date format.".format(i[4])))
                

                # bill_to = frappe.get_all("Bill To", filters={"name" : i[2]}, fields = ["name"])
                # if len(bill_to) == 0:
                #     frappe.throw(_("Please enter a Valid Bill To code in Bill To column."))

                ibg_order = frappe.get_doc(
                    dict(
                        doctype="IBG Order",
                        country=i[0],
                        customer=i[1],
                        bill_to=str(int(float(i[2]))),
                        company_code = i[4],
                        order_etd=date,
                        )
                ).insert(ignore_permissions=True)
                frappe.db.commit()

                parent = ibg_order.name
                parent_list.append(parent)

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
                        "created_date": frappe.utils.now_datetime().date()
                    }
                ).insert(ignore_permissions=True)
                frappe.db.commit()
        for i in parent_list:
            doc = frappe.get_doc("IBG Order", i)
            # price = sap_price(doc = doc)
            # price_data = []
            # if price:
            #     for j in price:
            #         if (j['CUSTOMER'].isnumeric()==True) and (int(doc.bill_to) == int(j['CUSTOMER'])):
            #             price_data.append(j)
            # if len(price_data) >= 1:
            #     for i in doc.order_items:
            #         for j in price_data:
            #             if int(i.fg_code) == int(j['MATERIAL']):
            #                 i.billing_rate = float(j['RATE'])
            #                 i.rate_valid_from = j['VALID_FROM']
            #                 i.rate_valid_to = j['VALID_TO']
            #                 i.units = j['CURRENCY']
            #             else:
            #                frappe.log_error(
            #                     message= "Order Id -{}\n"
            #                     + "Customer name -{}\n"
            #                     + "Bill To Code -{}\n"
            #                     + "Message - Price Data for {} Unavailable.".format(doc.name,doc.customer, doc.bill_to, i.fg_code),
            #                     title="Price Data unavailable in SAP Price BAPI",
            #     
            #             ) 
            price_update(doc=doc)
            doc.save(ignore_permissions = True)
            frappe.db.commit()

            # else:
            #     frappe.log_error(
            #         message= "Order Id -{}\n"
            #         + "Customer name -{}\n"
            #         + "Bill To Code -{}\n"
            #         + "Message - Price Data Unavailable.".format(doc.name,doc.customer,doc.bill_to),
            #         title="Price Data unavailable in SAP Price BAPI",
            #     )
        #         frappe.throw(_("Data for the Customer name ({})/Bill To ({}) unavailable in SAP.".format(doc.customer, doc.bill_to)))

    except Exception as e:
        frappe.log_error(
            message=frappe.get_traceback(),
            title="IBG Order Uplaod file Error",
        )


@frappe.whitelist()
def firm_plan_report(doc_filters = None):
    try:
        data =[]
        order_name_list =[]
        curr_first = frappe.utils.now_datetime().date().replace(day=1)
        res = calendar.monthrange(curr_first.year, curr_first.month) 
        curr_last = frappe.utils.now_datetime().date().replace(day=res[1])
        
        if len(doc_filters) > 2:
            order_items = frappe.get_all(
                "IBG Order Items",
                filters = doc_filters,
                fields=["*"],
            )
        else:
            order_items = frappe.get_all(
            "IBG Order Items",
            filters={"created_date" :["BETWEEN", [curr_first, curr_last]]},
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
                        for j in i.product_description:
                            if j.isdigit():
                                num+=j
                        qty = (float((num))/1000)
                        cust_code = frappe.db.get_value("IBG Distributor",{"customer_name": order_doc.customer},"customer_code",)

                        if len(doc_filters)>2:
                            curr_month = ""
                            next_month = calendar.month_abbr[(order_items[-1].created_date.month)+1]
                            next_nd_month = calendar.month_abbr[(order_items[-1].created_date.month)+2]
                        else:
                            curr_month = calendar.month_abbr[order_doc.created_date.month]
                            next_month = calendar.month_abbr[(order_doc.created_date.month)+1]
                            next_nd_month = calendar.month_abbr[(order_doc.created_date.month)+2]

                        order_dict = {"Customer Code" : cust_code, "Customer Name" : order_doc.customer, "Country" : order_doc.country, "Order ID" : order_doc.name, "Month" : calendar.month_abbr[order_doc.created_date.month], "FG Code" : i.fg_code, "Rate/Cs" : i.billing_rate, "Currency" : i.units, "Units/Cs": units_cs, "SAP Plant Code" : "", "Material Group" : material_group, "Product Description" : i.product_description, "Qty in Case({})".format(curr_month) : i.qty_in_cases, "Qty in Nos({})".format(curr_month) : (float(i.qty_in_cases) * float(units_cs)), "Qty in kl({})".format(curr_month) : (((float(i.qty_in_cases) * float(units_cs))*qty)/1000), "Order Value({})".format(curr_month) : float(i.order_value), "Qty in Case({})".format(next_month) : "", "Qty in Nos({})".format(next_month) : "", "Qty in kl({})".format(next_month) : "", "Order Value({})".format(next_month) : "", "Qty in Case({})".format(next_nd_month) : "", "Qty in Nos({})".format(next_nd_month) : "", "Qty in kl({})".format(next_nd_month) : "", "Order Value({})".format(next_nd_month) : ""}

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
    except Exception as e:
        frappe.log_error(
            message=frappe.get_traceback(),
            title="Firm Plan Report Error",
        )

@frappe.whitelist()
def sap_rfc_data(doc):
    try:
        doc = frappe.get_doc('IBG Order', doc.name)
        setting_doc = frappe.get_single("IBG-App Settings")
        ibg_marico_oms.create_log(
            {"datetime" : str(frappe.utils.now_datetime()),"response" : "", "Order_id" : str(doc.name)},
            "sap_ord_before_request",
        )
        if frappe.utils.get_url() == "https://marico.atriina.com":
            wsdl = (setting_doc.live_url).format(setting_doc.order_bapi)
            userid = setting_doc.live_sap_user
            pswd = setting_doc.live_sap_password
        else:
            wsdl = (setting_doc.staging_url).format(setting_doc.order_bapi)
            userid = setting_doc.staging_sap_user
            pswd = setting_doc.staging_sap_password
        client = Client(wsdl)
        session = Session()
        session.auth = HTTPBasicAuth(userid, pswd)
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
        ibg_marico_oms.create_log(
            {"datetime" : str(frappe.utils.now_datetime()),"request" : str(request_data), "Order_id" : str(doc.name),},
            "sap_ord_request",
        )
        response=client.service.ZBAPI_IBG_ORD(**request_data)
        ibg_marico_oms.create_log(
            {"datetime" : str(frappe.utils.now_datetime()),"request" : str(request_data),"response" : str(response), "Order_id" : str(doc.name),},
            "sap_ord_response",
        )
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
def sap_price(doc):
    try:
        if doc.company_code:
            setting_doc = frappe.get_single("IBG-App Settings")
            ibg_marico_oms.create_log(
                {"datetime" : str(frappe.utils.now_datetime()),"response" : "",},
                "sap_price_before_request",
            )
            if frappe.utils.get_url() == "https://marico.atriina.com":
                wsdl = (setting_doc.live_url).format(setting_doc.price_bapi)
                userid = setting_doc.live_sap_user
                pswd = setting_doc.live_sap_password
            else:
                wsdl = (setting_doc.staging_url).format(setting_doc.price_bapi)
                userid = setting_doc.staging_sap_user
                pswd = setting_doc.staging_sap_password
            client = Client(wsdl)
            session = Session()
            session.auth = HTTPBasicAuth(userid, pswd)
            client=Client(wsdl,transport=Transport(session=session))
            request_data={'IT_PRICE': '','SALES_ORG' : doc.company_code}
            ibg_marico_oms.create_log(
                {"datetime" : str(frappe.utils.now_datetime()),"request" : str(request_data),},
                "sap_price_request",
            )
            response=client.service.ZBAPI_PRICE_MASTER(**request_data)
            ibg_marico_oms.create_log(
                {"datetime" : str(frappe.utils.now_datetime()),"request" : str(request_data),"response" : str(response),},
                "sap_price_response",
            )
            return response
        
        else:
            frappe.throw(_("Please Enter a valid Company Code"))

    except Exception as e:
        frappe.log_error(
            message=frappe.get_traceback(),
            title="SAP Price Master Entry",
        )


@frappe.whitelist()
def price_update(doc):
        price = sap_price(doc = doc)
        total_order_value = 0
        qty = 0
        price_data = []
        if price:
            for j in price:
                if (j['CUSTOMER'].isnumeric()==True) and (int(doc.bill_to) == int(j['CUSTOMER'])):
                    price_data.append(j)
        if len(price_data) >= 1:
            for i in doc.order_items:
                for j in price_data:
                    if int(i.fg_code) == int(j['MATERIAL']):
                        i.billing_rate = float(j['RATE'])
                        i.rate_valid_from = j['VALID_FROM']
                        i.rate_valid_to = j['VALID_TO']
                        i.units = j['CURRENCY']
                qty += float(i.qty_in_cases)
                if i.billing_rate:
                    i.order_value = float(i.qty_in_cases) * float(i.billing_rate)
                    total_order_value += float(i.order_value)
            doc.total_qty_in_cases = qty
            doc.total_order_value = total_order_value

        else:
            frappe.log_error(
                message= "Order Id -{}\n"
                + "Customer name -{}\n"
                + "Bill To Code -{}\n"
                + "Message - Price Data Unavailable.".format(doc.name,doc.customer,doc.bill_to),
                title="Price Data unavailable in SAP Price BAPI",
            )

@frappe.whitelist()
def cargo_tracking(doc):
    try:
        doc = frappe.get_doc('IBG Order',doc)
        print("++++++++++++++++",doc.customer)
        cargo = frappe.get_doc(
            {
                "doctype" : "Cargo",
                "distributor_name":doc.customer,
                "distributor_code" : doc.bill_to,
                "so_number" : doc.sap_so_number
            }
        )
        cargo.insert(ignore_permissions= True)
        frappe.db.commit()
        print("****************",cargo.name)
        if doc.sap_so_number:
            setting_doc = frappe.get_single("IBG-App Settings")
            ibg_marico_oms.create_log(
                {"datetime" : str(frappe.utils.now_datetime()),"response" : "",},
                "sap_cargo_tracking_request",
            )
            if frappe.utils.get_url() == "https://marico.atriina.com":
                wsdl = (setting_doc.live_url).format(setting_doc.cargo_bapi)
                userid = setting_doc.live_sap_user
                pswd = setting_doc.live_sap_password
            else:
                wsdl = (setting_doc.staging_url).format(setting_doc.cargo_bapi)
                userid = setting_doc.staging_sap_user
                pswd = setting_doc.staging_sap_password
            client = Client(wsdl)
            session = Session()
            session.auth = HTTPBasicAuth(userid, pswd)
            client=Client(wsdl,transport=Transport(session=session))
            request_data={'IT_FINAL':''}
            ibg_marico_oms.create_log(
                {"datetime" : str(frappe.utils.now_datetime()),"request" : str(request_data),},
                "sap_cargo_tracking_request",
            )
            response=client.service.ZBAPI_IBG_CARGO_TRACKING(**request_data)
            ibg_marico_oms.create_log(
                {"datetime" : str(frappe.utils.now_datetime()),"request" : str(request_data),"response" : str(response),},
                "sap_cargo_tracking_request",
            )
            if response:
                for i in response:
                    if i['SO_NO'] == doc.sap_so_number:
                        invoice_details = frappe.get_doc(
                        {
                            'doctype' : 'Invoice Details',
                            'parent' : cargo.name,
                            'parenttype':'Cargo',
                            'invoice_number':i['INV_NO'],
                            'distributor_po_no':i['DIST_PO_NO'],
                            'invoice_value_usd':i['INV_VAL_USD'],
                            'noof_cases':i['CASES_NO']
                        }
                        )
                        invoice_details.insert(ignore_permissions= True)
                        frappe.db.commit()
        else:
            frappe.throw(_("Error"))

    except Exception as e:
        frappe.log_error(
            message=frappe.get_traceback(),
            title="SAP Cargo Tracking Error",
        )

