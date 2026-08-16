import os
import re

file_path = '/home/pravi/web-app/generic_workflow_app/inventory/models.py'
with open(file_path, 'r') as f:
    content = f.read()

# Replace any models.ForeignKey('InventoryItem', ... with null=True if not already present
def add_null(match):
    m = match.group(0)
    if 'null=True' not in m:
        return m.replace("models.ForeignKey('InventoryItem',", "models.ForeignKey('InventoryItem', null=True, blank=True,")
    return m

content = re.sub(r"models\.ForeignKey\('InventoryItem',[^\)]*\)", add_null, content)

with open(file_path, 'w') as f:
    f.write(content)

print("Added null=True to all inventory_item foreign keys.")
