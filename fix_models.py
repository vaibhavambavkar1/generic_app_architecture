import os

def fix_inventory():
    file_path = '/home/pravi/web-app/generic_workflow_app/inventory/models.py'
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    # Remove the duplicate Batch block and change Product to InventoryItem
    new_lines = []
    skip = False
    for line in lines:
        if line.strip() == '# --- Hotel Management Additions ---':
            skip = False # keep reading but we need to watch for Batch
            
        if line.startswith('class Batch(AuditableMixin):') and len(new_lines) > 300:
            skip = True
            continue
            
        if skip and line.startswith('class WastageLog(AuditableMixin):'):
            skip = False
            
        if not skip:
            line = line.replace('models.ForeignKey(Product,', "models.ForeignKey('InventoryItem',")
            line = line.replace("models.ForeignKey('inventory.Product',", "models.ForeignKey('InventoryItem',")
            line = line.replace('self.product.name', 'self.inventory_item.name')
            # rename field from product to inventory_item
            if line.strip().startswith('product = models.ForeignKey'):
                line = line.replace('product = ', 'inventory_item = ')
            if "unique_together = ('product', " in line:
                line = line.replace("'product'", "'inventory_item'")
            new_lines.append(line)
            
    with open(file_path, 'w') as f:
        f.writelines(new_lines)

def fix_recipes():
    file_path = '/home/pravi/web-app/generic_workflow_app/hotel_recipes/models.py'
    with open(file_path, 'r') as f:
        content = f.read()
    
    content = content.replace("'inventory.Product'", "'inventory.InventoryItem'")
    content = content.replace("product =", "inventory_item =")
    content = content.replace("self.product.name", "self.inventory_item.name")
    
    with open(file_path, 'w') as f:
        f.write(content)

fix_inventory()
fix_recipes()
print("Fixed models!")
