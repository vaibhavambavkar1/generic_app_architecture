import os

settings_path = '/home/pravi/web-app/generic_workflow_app/erp_framework/settings.py'
with open(settings_path, 'r') as f:
    lines = f.readlines()

new_lines = []
apps_to_remove = [
    "'crm',", "'itam',", "'helpdesk',", "'generic_store_mgmt',",
    "'purchasing',", "'sales',", "'bookings',", "'logistics_core',",
    "'fleet_mgmt',", "'courier',", "'freight',", "'wms_3pl',", "'logistics_finance',"
]
for line in lines:
    if any(app in line for app in apps_to_remove):
        continue
    new_lines.append(line)

with open(settings_path, 'w') as f:
    f.writelines(new_lines)


urls_path = '/home/pravi/web-app/generic_workflow_app/erp_framework/urls.py'
with open(urls_path, 'r') as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if any(app in line for app in apps_to_remove) or any(p in line for p in ['crm.urls', 'itam.urls', 'helpdesk.urls', 'generic_store_mgmt.urls', 'purchasing.urls', 'sales.urls', 'bookings.urls', 'courier.urls', 'freight.urls', 'logistics_finance.urls']):
        continue
    new_lines.append(line)

with open(urls_path, 'w') as f:
    f.writelines(new_lines)

print("Cleaned up settings and urls")
