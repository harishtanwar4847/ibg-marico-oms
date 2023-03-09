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
        #sap_price()
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

#@frappe.whitelist()
#def sap_rfc_data():
    # Use a breakpoint in the code line below to debug your script.
    # SERVICE_URL = 'https://myxxxxx-api.saps4hanacloud.cn/sap/opu/odata/sap/API_OUTBOUND_DELIVERY_SRV;v=0002/A_OutbDeliveryItem/?$format=json'
 #   SERVICE_URL = 'http://mlr3dev0:8000/sap/bc/soap/wsdl11?services=ZBAPI_IBG_ORD&sap-client=540&sap-user=portal&sap-password=portal@345'
  #  response = requests.get(SERVICE_URL,auth=('portal', 'portal@345'), headers={"Prefer": "odata.maxpagesize=500", "Prefer": "odata.track-changes"})
   # data = response.content.decode("utf-8")
    # init_json = json.loads(response.content)
    #init_json = xmltodict.parse(data)
    #print("Initi json :", init_json)
    # length = len(init_json['d']['results'])
    # print(length)
    # # print(init_json['d']['results'])
    # l_output = []
    # l_record = []
    # # l_record = ('DeliveryDocument','DeliveryDocumentItem','Plant','ReferenceSDDocumentCategory','ReferenceSDDocument','ReferenceSDDocumentItem','ActualDeliveredQtyInBaseUnit','BaseUnit')
    # l_output.append(l_record)
    # i=0
    # while i < length:
    #     l_record = (init_json['d']['results'][i]['DeliveryDocument'],init_json['d']['results'][i]['DeliveryDocumentItem'],init_json['d']['results'][i]['Plant'],init_json['d']['results'][i]['ReferenceSDDocumentCategory'],init_json['d']['results'][i]['ReferenceSDDocument'],init_json['d']['results'][i]['ReferenceSDDocumentItem'],init_json['d']['results'][i]['ActualDeliveredQtyInBaseUnit'],init_json['d']['results'][i]['BaseUnit'])
    #     l_output.append(l_record)
    #     i=i+1
    # # print(l_output)

    # df_dn = pd.DataFrame(l_output,columns=['DeliveryDocument','DeliveryDocumentItem','Plant','ReferenceSDDocumentCategory','SalesOrder','SalesOrderItem','ActualDeliveredQtyInBaseUnit','BaseUnit'])
    # # delete leading 0 from so item column
    # df_dn['SalesOrderItem'] = df_dn['SalesOrderItem'].str.lstrip('0')
    # # change data type from string to float for actual delivery quantity column
    # df_dn[['ActualDeliveredQtyInBaseUnit']] = df_dn[['ActualDeliveredQtyInBaseUnit']].astype('float')
    # #subtotal the columnn ActualDeliveredQtyInBaseUnit by SalesOrder,SalesOrderItem,BaseUnit
    # df_dn = df_dn[['SalesOrder','SalesOrderItem','BaseUnit','ActualDeliveredQtyInBaseUnit']].groupby(['SalesOrder','SalesOrderItem','BaseUnit']).agg('sum')

    # # get so item data from S4HC
    # SERVICE_URL = 'https://myxxxxxx-api.saps4hanacloud.cn/sap/opu/odata/sap/API_SALES_ORDER_SRV/A_SalesOrderItem/?$format=json'
    # response = requests.get(SERVICE_URL,auth=('communication user', 'communication user password'), headers={"Prefer": "odata.maxpagesize=500", "Prefer": "odata.track-changes"})
    # init_json = json.loads(response.content)
    # length = len(init_json['d']['results'])
    # i=0
    # l_output = []
    # l_record = []
    # while i<length:
    #     l_record = (
    #     init_json['d']['results'][i]['SalesOrder'], init_json['d']['results'][i]['SalesOrderItem'],
    #     init_json['d']['results'][i]['SalesOrderItemText'], init_json['d']['results'][i]['Material'],
    #     init_json['d']['results'][i]['OrderQuantityUnit'], init_json['d']['results'][i]['ConfdDelivQtyInOrderQtyUnit'],
    #     init_json['d']['results'][i]['TransactionCurrency'], init_json['d']['results'][i]['NetAmount'])
    #     l_output.append(l_record)
    #     i = i + 1

    # df_so = pd.DataFrame(l_output, columns=[ 'SalesOrder','SalesOrderItem','SalesOrderItemText','Material', 'OrderQuantityUnit','ConfdDelivQtyInOrderQtyUnit','TransactionCurrency','NetAmount'])
    # # change data type from string to float for ConfdDelivQtyInOrderQtyUnit column
    # df_so[['ConfdDelivQtyInOrderQtyUnit']] = df_so[['ConfdDelivQtyInOrderQtyUnit']].astype('float')
    # df_so[['NetAmount']] = df_so[['NetAmount']].astype('float')

    # # join the so item table and dn item subtotal table
    # df_so=pd.merge(df_so,df_dn,how='inner',on=['SalesOrder','SalesOrderItem'])
    # print(df_so)
    # file_name = 'so_' + str(datetime.now().strftime('%Y_%m_%d_%H_%M_%S')) + '.csv'
    # # save the result in local file
    # df_so.to_csv(file_name, index=True, header=True,encoding='utf-8')

#@frappe.whitelist()
#def sap_price():
    # http://mlr3dev0:8000/sap/bc/soap/wsdl11?services=ZBAPI_IBG_ORD&sap-client=540&sap-user=portal&sap-password=portal@345

 #   from pyrfc import Connection, ABAPApplicationError, ABAPRuntimeError, LogonError, CommunicationError
  #  from configparser import ConfigParser
   # from pprint import PrettyPrinter
   # import pyrfc

    #ASHOST='219.64.5.107'
    #CLIENT='540'
    #SYSNR='00'
    #USER='portal'
    #PASSWD='portal@345'
    #conn = Connection(ashost=ASHOST, sysnr=SYSNR, client=CLIENT, user=USER, passwd=PASSWD,)
    # conn = pyrfc.Connection(user='portal', passwd='portal@345',mshost='sap.example.com', sysid='TE1', client='220', msserv='3600', group='EXAMPLE',)

    #try:
     #   options = [{ 'TEXT': "SALES_ORG = 'MIL'"}]
      #  pp = PrettyPrinter(indent=4)
       # ROWS_AT_A_TIME = 10
       # rowskips = 0
       # while True:
            # cursor = conn.cursor()
            
            # table = """ CREATE TABLE Price_items (COND_TYPE varchar(255), SALES_ORG varchar(255), CUSTOMER varchar(255), MATERIAL varchar(255), VALID_TO varchar(255), VALID_FROM varchar(255), DEL_IND varchar(255), RATE varchar(255))"""

        #    result = conn.call('RFC_READ_TABLE', \
         #   QUERY_TABLE = 'ZBAPI_PRICE_MASTER', \
          #  OPTIONS = options, \
           # ROWSKIPS = rowskips, ROWCOUNT = ROWS_AT_A_TIME)

           # log = {
            #        "url": ASHOST,
             #       "headers": 540,
              #      "request": options,
               #     "response": str(result),
               # }

           # ibg_marico_oms.create_log(log, "IBG_Price")
           # frappe.log_error(frappe.log_error(
            #    message= log ,
             #   title="Price BAPI Call",
            #))


            #pp.pprint(result['DATA'])

            #rowskips += ROWS_AT_A_TIME
           # if len(result['DATA']) < ROWS_AT_A_TIME:
            #    break
   # except Exception as e:
    #    frappe.log_error(
     #       message=frappe.get_traceback()
      #      + "\n\nLog details -\n{}".format(str(log)),
      #       title="Create Log Error",
       # )
    #except CommunicationError:
     #   print("Could not connect to server.")
      #  raise
   # except LogonError:
    #    print("Could not log in. Wrong credentials?")
     #   raise
   # except (ABAPApplicationError, ABAPRuntimeError):
    #    print("An error occurred.")
     #   raise
    
