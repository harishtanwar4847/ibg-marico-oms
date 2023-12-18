# Copyright (c) 2023, Atrina Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils.csvutils import read_csv_content
import ibg_marico_oms
import pandas as pd
from random import randint

class FGCode(Document):
	pass

@frappe.whitelist()
def fgcode_unitscs_template():
    try:
        data = []
        df = pd.DataFrame(
            data,
            columns=[
                "FG Code",
                "Units/CS",
                "Product Description",
                "Material Group",
                "Company Code",
            ],
        )
        file_name = "Product_list_{}".format(frappe.utils.now_datetime().date())
        sheet_name = "Product_list"
        return ibg_marico_oms.download_file(
            dataframe=df,
            file_name=file_name,
            file_extention="xlsx",
            sheet_name=sheet_name,
        )
    except Exception as e:
        frappe.log_error(
            message=frappe.get_traceback(),
            title="FGCode Download template Error",
        )

@frappe.whitelist()
def fgcode_unitscs_file_upload(upload_file):
    try:
        files = frappe.get_all("File", filters={"file_url": upload_file}, page_length=1)
        file = frappe.get_doc("File", files[0].name)
        file_path = file.get_full_path()
        with open(file_path, "rb") as upfile:
            fcontent = upfile.read()

        if ((file.file_name).split('.'))[1] == 'xlsx':
            excelFile = pd.read_excel (fcontent)
            file_name = (file.file_name).split('.')
            csv_name = "{fgcode}{rand}.csv".format(fgcode = file_name[0],rand = randint(1111,9999))
            name_csv = excelFile.to_csv (csv_name, index = None, header=True)
            with open(csv_name, "r") as csv_upfile:
                csv_fcontent = csv_upfile.read()
            csv_data = read_csv_content(csv_fcontent)
        else:
            csv_data = read_csv_content(fcontent)

        for i in csv_data[1:]:
            fgcode_list = frappe.get_list("FG Code", filters = {"name" : i[0]}, fields =["name"])
            if fgcode_list:
                product_doc = frappe.get_doc("FG Code", i[0])
                product_doc.unitscs = i[1]
                if not product_doc.company_code:
                    product_doc.company_code = i[4] if i[4] else ''
                elif i[4] and product_doc.company_code and str(product_doc.company_code) != str(i[4]):
                    product_doc.company_code = ""
                    product_doc.apply_to_all_company_code = 1
                product_doc.save(ignore_permissions = True)
                frappe.db.commit()
            else:
                print("i[2]",i[2])
                product_code = frappe.get_doc({
                    "doctype" : "FG Code",
                    "fg_code" : i[0],
					"unitscs" : i[1],
                    "product_description" : i[2],
                    "material_group" : i[3],
					"company_code" : i[4],
				}).insert(ignore_permissions = True)    
                frappe.db.commit()
    except Exception as e:
        frappe.log_error(
            message=frappe.get_traceback(),
            title="FG Code upload file Error",
        )