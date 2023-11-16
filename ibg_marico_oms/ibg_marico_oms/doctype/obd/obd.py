# Copyright (c) 2023, Atrina Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import ibg_marico_oms
import frappe
from frappe.model.document import Document
from zeep import Client
from zeep.transports import Transport
from requests import Session
from requests.auth import HTTPBasicAuth

class OBD(Document):
    def before_save(self):
        order_status = order_status_bapi(doc = self)
        if order_status:
            for i in order_status:
                for j in self.items:
                    frappe.log_error(
                        message="i ==> {} ".format(self.sap_so_number, i["SALES_ORDER"], type(self.sap_so_number), type(i["SALES_ORDER"])),
                        title="SAP Order Status BAPI Response",
                    )
                    if str(self.sap_so_number) == str(i["SALES_ORDER"]) and int(j.fg_code) == int(i['FG_CODE']) and float(j.sales_order_qty) == float(i["SALES_QTY"]):
                        j.sales_item =  i['SALES_ITEM']
                        j.delivery_no = i['DELIVERY_NO'] if i['DELIVERY_NO'] else ''
                        j.obd_sap_qty = float(i['OBD_QTY'])
                        j.pending_qty = float(i['PENDING_QTY']) if i['PENDING_QTY'] else 0
                        j.rejected_qty = float(i['REJECTED_QTY']) if i['REJECTED_QTY'] else 0
                        j.order_status = i['ORDER_STATUS']
                        j.final_status = i['FINAL_STATUS']
            
            if self.items[0].delivery_no:
                self.sap_obd_number = self.items[0].delivery_no        


@frappe.whitelist()
def order_status_bapi(doc):
    try:
        ibg_marico_oms.create_log(
            {"datetime" : str(frappe.utils.now_datetime()),"response" : "",},
            "order_status_before_request",
        )
        if frappe.utils.get_url() == "https://marico.atriina.com":
            wsdl = "http://219.64.5.107:8000/sap/bc/soap/wsdl11?services=ZBAPI_ORD_STATUS&sap-client=400&sap-user=minet&sap-password=ramram"
            userid = "minet"
            pswd = "ramram"
        else:
            wsdl = "http://14.140.115.225:8000/sap/bc/soap/wsdl11?services=ZBAPI_ORD_STATUS&sap-client=540&sap-user=portal&sap-password=portal%40345"
            userid = "portal"
            pswd = "portal@345"
        client = Client(wsdl)
        session = Session()
        session.auth = HTTPBasicAuth(userid, pswd)
        client=Client(wsdl,transport=Transport(session=session))
        items = []
        for i in doc.items:
            order_dict = {'FG_CODE': i.fg_code}
            items.append(order_dict)
        request_data={"SALES_ORDER" : doc.sap_so_number ,'IT_SO': "", 'IT_RETURN':""}
        ibg_marico_oms.create_log(
            {"datetime" : str(frappe.utils.now_datetime()),"request" : str(request_data),},
            "order_status_request",
        )
        response=client.service.ZBAPI_ORD_STATUS(**request_data)
        ibg_marico_oms.create_log(
            {"datetime" : str(frappe.utils.now_datetime()),"request" : str(request_data),"response" : str(response),},
            "order_status_response",
        )
        return response

    except Exception:
        frappe.log_error(
            message=frappe.get_traceback(),
            title="SAP Order Status BAPI Response",
        )


@frappe.whitelist()
def order_status(doc):
    try:
        obd_list = frappe.get_all("OBD", filters = {"final_status" : "Pending", "sap_obd_number" : ""}, fields = ["name"])

        for i in obd_list:
            doc = frappe.get_doc("OBD", i.name)
            order_status_details = order_status_bapi(doc = doc)
            if order_status_details:
                for i in order_status_details:
                    for j in doc.items:
                        if doc.sap_so_number == i["SALES_ORDER"] and int(j.fg_code) == int(i['FG_CODE']) and float(j.sales_order_qty) == float(i["SALES_QTY"]):
                            j.sales_item =  i['SALES_ITEM']
                            j.delivery_no = i['DELIVERY_NO'] if i['DELIVERY_NO'] else ''
                            j.obd_sap_qty = float(i['OBD_QTY'])
                            j.pending_qty = float(i['PENDING_QTY']) if i['PENDING_QTY'] else 0
                            j.rejected_qty = float(i['REJECTED_QTY']) if i['REJECTED_QTY'] else 0
                            j.order_status = i['ORDER_STATUS']
                            j.final_status = i['FINAL_STATUS']
                
                if doc.items[0].delivery_no:
                    doc.sap_obd_number = doc.items[0].delivery_no
    except Exception:
        frappe.log_error(
            message=frappe.get_traceback(),
            title="SAP Order Status OBD Entry",
        )
