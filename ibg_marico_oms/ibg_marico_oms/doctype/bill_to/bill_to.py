# Copyright (c) 2023, Atrina Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils.csvutils import read_csv_content
import ibg_marico_oms
import pandas as pd
from random import randint

class BillTo(Document):
	pass

@frappe.whitelist()
def bill_to_template():
    try:
        data = []
        df = pd.DataFrame(
            data,
            columns=[
                "Bill To",
                "Company Code",
                "Customer",
            ],
        )
        file_name = "Bill_to_list_{}".format(frappe.utils.now_datetime().date())
        sheet_name = "Bill_to_list"
        return ibg_marico_oms.download_file(
            dataframe=df,
            file_name=file_name,
            file_extention="xlsx",
            sheet_name=sheet_name,
        )
    except Exception as e:
        frappe.log_error(
            message=frappe.get_traceback(),
            title="Bill To Download template Error",
        )

@frappe.whitelist()
def bill_to_file_upload(upload_file):
    try:
        files = frappe.get_all("File", filters={"file_url": upload_file}, page_length=1)
        file = frappe.get_doc("File", files[0].name)
        file_path = file.get_full_path()
        with open(file_path, "rb") as upfile:
            fcontent = upfile.read()

        if ((file.file_name).split('.'))[1] == 'xlsx':
            excelFile = pd.read_excel (fcontent)
            file_name = (file.file_name).split('.')
            csv_name = "{bill_to}{rand}.csv".format(bill_to = file_name[0],rand = randint(1111,9999))
            name_csv = excelFile.to_csv (csv_name, index = None, header=True)
            with open(csv_name, "r") as csv_upfile:
                csv_fcontent = csv_upfile.read()
            csv_data = read_csv_content(csv_fcontent)
        else:
            csv_data = read_csv_content(fcontent)

        for i in csv_data[1:]:
            bill_to_list = frappe.get_list("Bill To", filters = {"name" : i[0]}, fields =["name"])
            if bill_to_list:
                bill_to_doc = frappe.get_doc("Bill To", i[0])
                bill_to_doc.customer = i[2]
                if not bill_to_doc.company_code:
                    bill_to_doc.company_code = i[1] if i[1] else ''
                elif i[1] and bill_to_doc.company_code and str(bill_to_doc.company_code) != str(i[1]):
                    bill_to_doc.company_code = ""
                    bill_to_doc.apply_to_all_company_code = 1
                bill_to_doc.save(ignore_permissions = True)
                frappe.db.commit()
            else:
                bill_to = frappe.get_doc({
                    "doctype" : "Bill To",
                    "bill_to" : i[0],
					"company_code" : i[1],
                    "customer" : i[2],
				}).insert(ignore_permissions = True)    
                frappe.db.commit()
    except Exception as e:
        frappe.log_error(
            message=frappe.get_traceback(),
            title="Bill To upload file Error",
        )
