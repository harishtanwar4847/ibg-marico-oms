# Copyright (c) 2024, Atrina Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document
import frappe
from frappe.utils import now_datetime
from frappe.utils.file_manager import get_file
from frappe import _

class Cargo(Document):
    def before_submit(self):
        send_email_attachments(self.name)

@frappe.whitelist()
def send_email_attachments(doc_name):
	try:
		doc = frappe.get_doc("Cargo", doc_name)
		if doc.distributor_email_id:
			attachments = []
			for attachment_row in doc.attachments:
				file_path = attachment_row.attachment
				attachments.append({'file_url':file_path})

			email_content = "Please find attached the files you requested."

			
			frappe.sendmail(
				recipients= doc.distributor_email_id,
				subject="Email with Attachments",
				message=email_content,
				attachments=attachments,
			)
			frappe.msgprint(_("Email sent successfully."))
	except Exception as e:
		frappe.log_error(f"Error sending email: {e}")