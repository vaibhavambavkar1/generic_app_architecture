import os

def fix_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    # The most common replacements
    content = content.replace("'product'", "'inventory_item'")
    content = content.replace('"product"', '"inventory_item"')
    content = content.replace("product=", "inventory_item=")
    content = content.replace("product_id", "inventory_item_id")
    content = content.replace("product__", "inventory_item__")
    
    # Let's preserve `product` inside comments/strings if needed, but it's safe to just blanket replace 
    # exact variable attributes if they cause issues. Let's just do a blanket replace for the known field names.
    # Like select_related('product' -> 'inventory_item'
    
    with open(filepath, 'w') as f:
        f.write(content)

base_dir = '/home/pravi/web-app/generic_workflow_app'
fix_file(os.path.join(base_dir, 'inventory/views.py'))
fix_file(os.path.join(base_dir, 'inventory/admin.py'))

print("Fixed admin and views.")
