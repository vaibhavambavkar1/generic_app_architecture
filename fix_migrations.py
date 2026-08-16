import os

file_path = '/home/pravi/web-app/generic_workflow_app/inventory/models.py'
with open(file_path, 'r') as f:
    content = f.read()

# We need to add null=True to inventory_item in Batch, SerialNumber, WastageLog
# Actually let's just blanket add null=True to inventory_item = models.ForeignKey('InventoryItem'
content = content.replace("models.ForeignKey('InventoryItem', on_delete=models.CASCADE, related_name='batches')", "models.ForeignKey('InventoryItem', on_delete=models.CASCADE, related_name='batches', null=True)")
content = content.replace("models.ForeignKey('InventoryItem', on_delete=models.CASCADE, related_name='serial_numbers')", "models.ForeignKey('InventoryItem', on_delete=models.CASCADE, related_name='serial_numbers', null=True)")
content = content.replace("models.ForeignKey('InventoryItem', on_delete=models.CASCADE)", "models.ForeignKey('InventoryItem', on_delete=models.CASCADE, null=True)")

with open(file_path, 'w') as f:
    f.write(content)
print("Added null=True")
