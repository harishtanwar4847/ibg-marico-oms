from . import __version__ as app_version

app_name = "ibg_marico_oms"
app_title = "IBG Marico OMS"
app_publisher = "Atrina Technologies Pvt. Ltd."
app_description = "Marico"
app_email = "developers@atriina.com"
app_license = "MIT"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/ibg_marico_oms/css/ibg_marico_oms.css"
# app_include_js = "/assets/ibg_marico_oms/js/ibg_marico_oms.js"

# include js, css files in header of web template
# web_include_css = "/assets/ibg_marico_oms/css/ibg_marico_oms.css"
# web_include_js = "/assets/ibg_marico_oms/js/ibg_marico_oms.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "ibg_marico_oms/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
#	"methods": "ibg_marico_oms.utils.jinja_methods",
#	"filters": "ibg_marico_oms.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "ibg_marico_oms.install.before_install"
# after_install = "ibg_marico_oms.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "ibg_marico_oms.uninstall.before_uninstall"
# after_uninstall = "ibg_marico_oms.uninstall.after_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "ibg_marico_oms.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	# "Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
#     "IBG Order": "ibg_marico_oms.supplychain_permission_query",
# }
#
# has_permission = {
#	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
#	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"IBG Order": {
# 		"before_save": "ibg_marico_oms.ibg_marico_oms.doctype.ibg_order.ibg_order.set_approver_name",
# 		"on_submit": "ibg_marico_oms.ibg_marico_oms.doctype.ibg_order.ibg_order.set_approver_name",
# 	}
# }

# Scheduled Tasks
# ---------------

scheduler_events = {
	# "all": [
	# 	"ibg_marico_oms.tasks.all"
	# ],
	# "daily": [
	# 	"ibg_marico_oms.tasks.daily"
	# ],
	# "hourly": [
	# 	"ibg_marico_oms.tasks.hourly"
	# ],
	# "weekly": [
	# 	"ibg_marico_oms.tasks.weekly"
	# ],
	# "monthly": [
	# 	"ibg_marico_oms.tasks.monthly"
	# ],
	"cron" : {
		"0 2 * * *": ["ibg_marico_oms.extract_product_data"],  # At 02:00 AM daily
        # "0 0,12 * * *": [
        #     "ibg_marico_oms.ibg_marico_oms.doctype.ibg_order.ibg_order.sap_price"
        # ],  # At 12:00 AM daily
        "0 1 * * *": [
            "ibg_marico_oms.extract_customer_shipto"
        ],  # At 01:00 AM

	},
}

# Testing
# -------

# before_tests = "ibg_marico_oms.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
#	"frappe.desk.doctype.event.event.get_events": "ibg_marico_oms.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
#	"Task": "ibg_marico_oms.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]


# User Data Protection
# --------------------

# user_data_fields = [
#	{
#		"doctype": "{doctype_1}",
#		"filter_by": "{filter_by}",
#		"redact_fields": ["{field_1}", "{field_2}"],
#		"partial": 1,
#	},
#	{
#		"doctype": "{doctype_2}",
#		"filter_by": "{filter_by}",
#		"partial": 1,
#	},
#	{
#		"doctype": "{doctype_3}",
#		"strict": False,
#	},
#	{
#		"doctype": "{doctype_4}"
#	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
#	"ibg_marico_oms.auth.validate"
# ]
