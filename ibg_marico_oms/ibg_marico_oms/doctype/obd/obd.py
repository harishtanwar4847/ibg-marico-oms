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
        order_item_status = []
        order_status = order_status_bapi(doc = self)
        if len(order_status['IT_SO']['item'])>1:
            for i in order_status['IT_SO']['item']:
                for j in self.items:
                    if str(self.sap_so_number) == str(i["SALES_ORDER"]) and int(j.fg_code) == int(i['FG_CODE']) and float(j.sales_order_qty) == float(i["SALES_QTY"]) and not j.reason_of_reject:
                        j.sales_item =  i['SALES_ITEM']
                        j.delivery_no = i['DELIVERY_NO'] if i['DELIVERY_NO'] else ''
                        self.sap_obd_number = j.delivery_no
                        j.obd_sap_qty = float(i['OBD_QTY'])
                        j.pending_qty = float(i['PENDING_QTY']) if i['PENDING_QTY'] else 0
                        j.rejected_qty = float(i['REJECTED_QTY']) if i['REJECTED_QTY'] else 0
                        j.order_status = i['ORDER_STATUS']
                        j.final_status = i['FINAL_STATUS'] 
                        order_item_status.append(str(i["ORDER_STATUS"]))       

        if "Partial serviced" in order_item_status:
            self.order_status = "Partial serviced"
        else:
            self.order_status = "Fully serviced"
            self.final_status = "Completed"

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
def order_status():
    try:
        obd_list = frappe.get_all("OBD", filters = {"final_status" : "Pending", "sap_obd_number" : ""}, fields = ["name"])

        for i in obd_list:
            doc = frappe.get_doc("OBD", i.name)
            order_status_details = order_status_bapi(doc = doc)
            if order_status_details:
                for i in order_status_details:
                    for j in doc.items:
                        if str(self.sap_so_number) == str(i["SALES_ORDER"]) and int(j.fg_code) == int(i['FG_CODE']) and float(j.sales_order_qty) == float(i["SALES_QTY"]):
                            j.sales_item =  i['SALES_ITEM']
                            j.delivery_no = i['DELIVERY_NO'] if i['DELIVERY_NO'] else ''
                            j.obd_sap_qty = float(i['OBD_QTY'])
                            j.pending_qty = float(i['PENDING_QTY']) if i['PENDING_QTY'] else 0
                            j.rejected_qty = float(i['REJECTED_QTY']) if i['REJECTED_QTY'] else 0
                            j.order_status = i['ORDER_STATUS']
                            j.final_status = i['FINAL_STATUS']
                
                if doc.items[0].delivery_no:
                    doc.sap_obd_number = doc.items[0].delivery_no
            doc.save(ignore_permissions=True)
            frappe.db.commit()

    except Exception:
        frappe.log_error(
            message=frappe.get_traceback(),
            title="SAP Order Status OBD Entry",
        )

@frappe.whitelist()
def order_reject(doc):
    try:
        doc = frappe.get_doc("OBD", doc)
        for item in doc.items:
            if item.final_status == "Pending":
                ibg_marico_oms.create_log(
                    {"datetime" : str(frappe.utils.now_datetime()),"response" : "",},
                    "order_reject_before_request",
                )
                if frappe.utils.get_url() == "https://marico.atriina.com":
                    wsdl = "http://219.64.5.107:8000/sap/bc/soap/wsdl11?services=ZBAPI_ORD_REJ&sap-client=400&sap-user=minet&sap-password=ramram"
                    userid = "minet"
                    pswd = "ramram"
                else:
                    wsdl = "http://14.140.115.225:8000/sap/bc/soap/wsdl11?services=ZBAPI_ORD_REJ&sap-client=540&sap-user=portal&sap-password=portal%40345"
                    userid = "portal"
                    pswd = "portal@345"
                client = Client(wsdl)
                session = Session()
                session.auth = HTTPBasicAuth(userid, pswd)
                client=Client(wsdl,transport=Transport(session=session))
                fg_code = item.fg_code
                if len(fg_code)< 18:
                    fg_code = fg_code.zfill(18) 
                request_data={"SALES_ORDER" : doc.sap_so_number ,"SALES_ITEM" : item.sales_item,"FG_CODE" : fg_code, 'IT_SO': "", 'IT_RETURN':""}
                ibg_marico_oms.create_log(
                    {"datetime" : str(frappe.utils.now_datetime()),"request" : str(request_data),},
                    "order_reject_request",
                )
                response=client.service.ZBAPI_ORD_REJ(**request_data)
                ibg_marico_oms.create_log(
                    {"datetime" : str(frappe.utils.now_datetime()),"request" : str(request_data),"response" : str(response),},
                    "order_reject_response",
                )
                order_details = response['IT_SO']['item']
                ibg_marico_oms.create_log(
                    {"datetime" : str(frappe.utils.now_datetime()),"request" : str(request_data),"response" : str(order_details[1:]),},
                    "order_details",
                )
                for i in order_details[1:]:
                    if str(i["SALES_ORDER"]) == str(doc.sap_so_number) and int(i["SALES_ITEM"]) == int(item.sales_item) and int(item.fg_code) == int(i["FG_CODE"]):
                        item_doc = frappe.get_doc("OBD Items", item.name)
                        item.rejected_qty = float(i["REJECTED_QTY"])
                        item.reason_of_reject = i["REASON_OF_REJECT"]
                        item.order_status = "Fully serviced" if item.reason_of_reject else "Partial serviced"
                        item.final_status = "Completed" if item.reason_of_reject else "Pending"
                        item.save(ignore_permissions = True)
                        # frappe.db.sql(""" update `tabOBD Items` set rejected_qty = {qty}, reason_of_reject = '{reason}', order_status = '{order_status}' , final_status = '{final_status}'  where name = '{name}' """.format(qty = float(i["REJECTED_QTY"]), reason = i["REASON_OF_REJECT"], order_status = "Fully serviced", final_status = "Completed", name = item.name))
                        frappe.db.commit()


                        ibg_marico_oms.create_log(
                            {"datetime" : str(frappe.utils.now_datetime()),"response" : str(item.as_dict()), "Item Doc" : str(item.name)},
                            "obd_item",
                        )
        # doc.save(ignore_permissions = True)
        # frappe.db.commit()
        doc.reload()
        frappe.reload_doc()
    
    except Exception as e:
        frappe.log_error(
            message="Traceback : {},  Doc : {},  doc_type : {}".format(frappe.get_traceback(),doc.name,type(doc)),
            title="SAP Order Rejection Entry",
        )
