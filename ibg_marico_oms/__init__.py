import json
import os
import frappe
import re
import pyodbc as p

__version__ = '0.5.2-dev'

def download_file(dataframe, file_name, file_extention, sheet_name):
    file_name = "{}.{}".format(file_name, file_extention)
    file_path = frappe.utils.get_files_path(file_name)
    if os.path.exists(file_path):
        os.remove(file_path)
    file_path = frappe.utils.get_files_path(file_name)
    dataframe.to_excel(file_path, sheet_name=sheet_name, index=False)
    file_url = frappe.utils.get_url("files/{}".format(file_name))
    return file_url

def create_log(log, file_name):
    try:
        log_file = frappe.utils.get_files_path("{}.json".format(file_name))
        logs = None
        if os.path.exists(log_file):
            with open(log_file, "r") as f:
                logs = f.read()
            f.close()
        logs = json.loads(logs or "[]")
        log["req_time"] = str(frappe.utils.now_datetime())
        logs.append(log)
        with open(log_file, "w") as f:
            f.write(json.dumps(logs))
        f.close()
    except json.decoder.JSONDecodeError:
        log_text_file = (
            log_file.replace(".json", "") + str(frappe.utils.now_datetime()) + ".txt"
        ).replace(" ", "-")
        with open(log_text_file, "w") as txt_f:
            txt_f.write(logs + "\nLast Log \n" + str(log))
        txt_f.close()
        os.remove(log_file)
        frappe.log_error(
            message=frappe.get_traceback()
            + "\n\nFile name -\n{}\n\nLog details -\n{}".format(file_name, str(log)),
            title="Create Log JSONDecodeError",
        )
    except Exception as e:
        frappe.log_error(
            message=frappe.get_traceback()
            + "\n\nFile name -\n{}\n\nLog details -\n{}".format(file_name, str(log)),
            title="Create Log Error",
        )

def extract_product_data():
    try:
        conn = p.connect('DRIVER={ODBC Driver 18 for SQL Server};Server=219.64.5.107;Port=1433;Database=IBGSCM;uid=sa;pwd=@MinetApps7;TrustServerCertificate=yes;')
        cursor = conn.cursor()
        cursor.execute('SELECT *  FROM MB_Item_Master_MME')
        product_list = []
        for i in cursor:
            product_list.append(i)
        for i in product_list:
            fg_code_list = frappe.get_all("FG Code", filters={"fg_code" : i[0]}, fields = ["name"])
            if len(fg_code_list) == 0:
                product = frappe.get_doc(
                    dict(
                        doctype="FG Code",
                        fg_code=i[0],
                        product_description=i[1],
                        material_group = i[10],
                        )).insert(ignore_permissions=True)
                frappe.db.commit()
    
    except Exception as e:
        frappe.log_error(
            message=frappe.get_traceback(),
            title="Product Master Error",
        )


def extract_customer_shipto():
    try:
        conn = p.connect('DRIVER={ODBC Driver 18 for SQL Server};Server=219.64.5.107;Port=1433;Database=IBGSCM;uid=sa;pwd=@MinetApps7;TrustServerCertificate=yes;')
        cursor = conn.cursor()
        cursor.execute('SELECT *  FROM Mst_Distributor')
        cust_list = []
        cust_name_list = []
        for i in cursor:
            cust_list.append(i)
            cust_name_list.append(i[2])
        cust_name_list = list(set(cust_name_list))
        for i in cust_list:
            customer_doc = frappe.get_all("IBG Distributor", filters = {"customer_name" :i[2]}, fields =["name"])
            if i[-2] == 'A'and len(customer_doc)== 0 and i[2] in cust_name_list:
                customer = frappe.get_doc(
                    dict(
                        doctype="IBG Distributor",
                        customer_name=i[2],
                        country = i[5],
                        ship_to = i[1]
                        )).insert(ignore_permissions=True)
                frappe.db.commit()
                pop_name = cust_name_list.pop(0)
                bill_to = frappe.get_doc(
                    dict(
                        doctype="Bill To",
                        bill_to=i[1],
                        customer = i[2],
                        )).insert(ignore_permissions=True)
                frappe.db.commit()
        cursor.execute('SELECT *  FROM Mst_customer')
        custcode_list = []
        for i in cursor:
            custcode_list.append(i)
        for i in custcode_list:
            customer_doc = frappe.get_all("IBG Distributor", filters = {"customer_name" :i[3]}, fields =["name"])
            if len(customer_doc) > 0:
                cust = frappe.get_doc("IBG Distributor", i[3])
                if cust:
                    cust.customer_code = i[2]
                    cust.save(ignore_permissions=True)
                    frappe.db.commit()
        customer_list = frappe.get_all("IBG Distributor", fields =["*"])
        for i in customer_list:
            if i.customer_code == None:
                customer = frappe.get_doc("IBG Distributor", i.name)
                customer.customer_code = customer.ship_to
                customer.save(ignore_permissions=True)
                frappe.db.commit()
    except Exception as e:
        frappe.log_error(
            message=frappe.get_traceback(),
            title="Customer Master Storage Error",
        )

def change_date_format(dt):
    return re.sub(r'(\d{4})-(\d{1,2})-(\d{1,2})', '\\3-\\2-\\1', dt)
