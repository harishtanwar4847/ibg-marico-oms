# Copyright (c) 2023, Atrina Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils.csvutils import read_csv_content
import ibg_marico_oms
import pandas as pd
from random import randint

class IBGDistributor(Document):
	pass

@frappe.whitelist()
def distributor_template():
    try:
        data = []
        df = pd.DataFrame(
            data,
            columns=[
                "Customer Name",
                "Customer Code",
                "Country",
                "Ship To",
                "Company Code",
            ],
        )
        file_name = "Distributor_list_{}".format(frappe.utils.now_datetime().date())
        sheet_name = "Distributor_list"
        return ibg_marico_oms.download_file(
            dataframe=df,
            file_name=file_name,
            file_extention="xlsx",
            sheet_name=sheet_name,
        )
    except Exception as e:
        frappe.log_error(
            message=frappe.get_traceback(),
            title="Distributor Download template Error",
        )

@frappe.whitelist()
def distributor_file_upload(upload_file):
    try:
        files = frappe.get_all("File", filters={"file_url": upload_file}, page_length=1)
        file = frappe.get_doc("File", files[0].name)
        file_path = file.get_full_path()
        with open(file_path, "rb") as upfile:
            fcontent = upfile.read()

        if ((file.file_name).split('.'))[1] == 'xlsx':
            excelFile = pd.read_excel (fcontent)
            file_name = (file.file_name).split('.')
            csv_name = "{distributor}{rand}.csv".format(distributor = file_name[0],rand = randint(1111,9999))
            name_csv = excelFile.to_csv (csv_name, index = None, header=True)
            with open(csv_name, "r") as csv_upfile:
                csv_fcontent = csv_upfile.read()
            csv_data = read_csv_content(csv_fcontent)
        else:
            csv_data = read_csv_content(fcontent)

        for i in csv_data[1:]:
            distributor_list = frappe.get_list("IBG Distributor", filters = {"name" : i[0]}, fields =["name"])
            if distributor_list:
                distributor_doc = frappe.get_doc("IBG Distributor", i[0])
                distributor_doc.customer_code = i[1]
                distributor_doc.country = i[2]
                distributor_doc.ship_to = i[3]
                if not distributor_doc.company_code:
                    distributor_doc.company_code = i[4] if i[4] else ''
                elif i[4] and distributor_doc.company_code and str(distributor_doc.company_code) != str(i[4]):
                    distributor_doc.company_code = ""
                distributor_doc.save(ignore_permissions = True)
                frappe.db.commit()
            else:
                distributor = frappe.get_doc({
                    "doctype" : "IBG Distributor",
                    "customer_name" : i[0],
                    "customer_code" : i[1],
					"country" : i[2],
					"ship_to" : i[3],
					"company_code" : i[4],
				}).insert(ignore_permissions = True)    
                frappe.db.commit()
    except Exception as e:
        frappe.log_error(
            message=frappe.get_traceback(),
            title="Distributor upload file Error",
        )
