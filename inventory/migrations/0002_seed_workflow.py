from django.db import migrations

def seed_po_workflow(apps, schema_editor):
    Workflow = apps.get_model('core', 'Workflow')
    State = apps.get_model('core', 'State')
    Transition = apps.get_model('core', 'Transition')

    # Create Workflow
    wf, created = Workflow.objects.get_or_create(
        name="Purchase Order Workflow",
        model_name="inventory.PurchaseOrder",
        defaults={"description": "Standard Purchase Order processing workflow."}
    )

    # Create States
    draft, _ = State.objects.get_or_create(workflow=wf, name="Draft", defaults={"is_initial": True, "is_final": False})
    pending, _ = State.objects.get_or_create(workflow=wf, name="Pending Approval", defaults={"is_initial": False, "is_final": False})
    approved, _ = State.objects.get_or_create(workflow=wf, name="Approved", defaults={"is_initial": False, "is_final": False})
    received, _ = State.objects.get_or_create(workflow=wf, name="Received", defaults={"is_initial": False, "is_final": True})

    # Create Transitions
    Transition.objects.get_or_create(
        workflow=wf,
        name="Submit",
        from_state=draft,
        to_state=pending,
        defaults={"conditions": "", "actions": ""}
    )
    Transition.objects.get_or_create(
        workflow=wf,
        name="Approve",
        from_state=pending,
        to_state=approved,
        defaults={"conditions": "is_manager_or_admin", "actions": ""}
    )
    Transition.objects.get_or_create(
        workflow=wf,
        name="Receive Stock",
        from_state=approved,
        to_state=received,
        defaults={"conditions": "", "actions": "replenish_item_stock"}
    )

def remove_po_workflow(apps, schema_editor):
    Workflow = apps.get_model('core', 'Workflow')
    Workflow.objects.filter(model_name="inventory.PurchaseOrder").delete()

class Migration(migrations.Migration):
    dependencies = [
        ('inventory', '0001_initial'),
        ('core', '0004_userprofile'),
    ]

    operations = [
        migrations.RunPython(seed_po_workflow, remove_po_workflow),
    ]
