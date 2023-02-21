import os
import frappe

__version__ = '0.2.0-dev'


def supplychain_permission_query(user):
    if not user:
        user = frappe.session.user
    user_doc = frappe.get_doc("User", user).as_dict()
    if "Supply Chain" in [r.role for r in user_doc.roles]:
        return "(`tabIBG Order`.status = 'Approved by IBG Finance' or `tabIBG Order`.status = 'Approved by Supply Chain' or `tabIBG Order`._assign like '%{user_session}%')".format(user_session=user)

def download_file(dataframe, file_name, file_extention, sheet_name):
    file_name = "{}.{}".format(file_name, file_extention)
    file_path = frappe.utils.get_files_path(file_name)
    if os.path.exists(file_path):
        os.remove(file_path)
    file_path = frappe.utils.get_files_path(file_name)
    dataframe.to_excel(file_path, sheet_name=sheet_name, index=False)
    file_url = frappe.utils.get_url("files/{}".format(file_name))
    return file_url
