import os

finance_views = '/home/pravi/web-app/generic_workflow_app/finance/views.py'
with open(finance_views, 'r') as f:
    lines = f.readlines()

new_lines = []
skip = False
for line in lines:
    if line.startswith('from sales.models import B2BSalesInvoice') or line.startswith('from purchasing.models import SupplierBill'):
        continue
    if line.startswith('@login_required') and ('invoicing_dashboard' in ''.join(lines) or 'invoice_payment' in ''.join(lines)):
        pass # we will manually slice

content = ''.join(lines)
# Remove invoicing_dashboard and invoice_payment functions
import re
content = re.sub(r'from sales\.models import B2BSalesInvoice\n', '', content)
content = re.sub(r'from purchasing\.models import SupplierBill\n', '', content)
content = re.sub(r'@login_required\ndef invoicing_dashboard\(request\):[\s\S]*?return render.*?$', '', content, flags=re.MULTILINE)
content = re.sub(r'@login_required\ndef invoice_payment\(request, invoice_type, invoice_id\):[\s\S]*?return redirect.*?$', '', content, flags=re.MULTILINE)

with open(finance_views, 'w') as f:
    f.write(content)

finance_urls = '/home/pravi/web-app/generic_workflow_app/finance/urls.py'
with open(finance_urls, 'r') as f:
    content = f.read()

content = re.sub(r"path\('invoicing/', views\.invoicing_dashboard, name='invoicing_dashboard'\),", "", content)
content = re.sub(r"path\('invoicing/pay/<str:invoice_type>/<int:invoice_id>/', views\.invoice_payment, name='invoice_payment'\),", "", content)

with open(finance_urls, 'w') as f:
    f.write(content)

print("Fixed finance views and urls")
