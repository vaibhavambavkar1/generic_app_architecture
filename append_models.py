import os

inventory_models = """

# --- Hotel Management Additions ---
class Batch(AuditableMixin):
    product = models.ForeignKey('inventory.Product', on_delete=models.CASCADE, related_name='batches')
    batch_number = models.CharField(max_length=100, unique=True)
    manufacturing_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=3, default=0)

    def __str__(self):
        return f"{self.product.name} - {self.batch_number}"

class WastageLog(AuditableMixin):
    product = models.ForeignKey('inventory.Product', on_delete=models.CASCADE)
    batch = models.ForeignKey(Batch, on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=3)
    reason = models.TextField()
    date_recorded = models.DateTimeField(auto_now_add=True)
"""

hrms_models = """

# --- Hotel Management Additions ---
class Shift(AuditableMixin):
    name = models.CharField(max_length=100)
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.start_time} - {self.end_time})"

class Attendance(AuditableMixin):
    employee = models.ForeignKey('hrms.Employee', on_delete=models.CASCADE)
    shift = models.ForeignKey(Shift, on_delete=models.SET_NULL, null=True, blank=True)
    date = models.DateField(auto_now_add=True)
    check_in = models.DateTimeField(null=True, blank=True)
    check_out = models.DateTimeField(null=True, blank=True)
"""

finance_models = """

# --- Hotel Management Additions ---
class DayClosing(AuditableMixin):
    branch_code = models.CharField(max_length=50) # reference to HotelBranch
    date = models.DateField(auto_now_add=True)
    total_sales = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_expenses = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    net_cash = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    closed_by = models.ForeignKey('core.UserProfile', on_delete=models.SET_NULL, null=True)
    is_reconciled = models.BooleanField(default=False)
"""

core_backup = """

    def upload_to_google_drive(self, file_path):
        # Stub for Google Drive upload integration
        print(f"Uploading {file_path} to Google Drive...")
        # Implementation would use google-api-python-client
        pass
"""

def append_to_file(filepath, content):
    with open(filepath, 'a') as f:
        f.write(content)

def replace_in_file(filepath, target, replacement):
    with open(filepath, 'r') as f:
        data = f.read()
    data = data.replace(target, replacement)
    with open(filepath, 'w') as f:
        f.write(data)

base_dir = '/home/pravi/web-app/generic_workflow_app'

append_to_file(os.path.join(base_dir, 'inventory/models.py'), inventory_models)
append_to_file(os.path.join(base_dir, 'hrms/models.py'), hrms_models)
append_to_file(os.path.join(base_dir, 'finance/models.py'), finance_models)

backup_file = os.path.join(base_dir, 'core/backup.py')
with open(backup_file, 'a') as f:
    f.write(core_backup)

print("Models appended.")
