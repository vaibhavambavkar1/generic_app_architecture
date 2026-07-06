from django.core.management.base import BaseCommand
from core.models import Workflow, State, Transition
from inventory.models import PurchaseOrder

class Command(BaseCommand):
    help = 'Seeds the database with standard Inventory workflows'

    def handle(self, *args, **options):
        # 1. Create Workflow for PurchaseOrder
        wf, created = Workflow.objects.get_or_create(
            name="Standard Procurement Flow",
            model_name="inventory.PurchaseOrder",
            defaults={'description': "Default PO Approval and Receiving Workflow"}
        )
        
        # 2. Create States
        draft, _ = State.objects.get_or_create(workflow=wf, name="Draft", defaults={'is_initial': True})
        pending, _ = State.objects.get_or_create(workflow=wf, name="Pending Approval")
        approved, _ = State.objects.get_or_create(workflow=wf, name="Approved")
        received, _ = State.objects.get_or_create(workflow=wf, name="Received", defaults={'is_final': True})
        rejected, _ = State.objects.get_or_create(workflow=wf, name="Rejected", defaults={'is_final': True})
        
        # 3. Create Transitions
        Transition.objects.get_or_create(
            workflow=wf, name="Submit for Approval",
            from_state=draft, to_state=pending
        )
        Transition.objects.get_or_create(
            workflow=wf, name="Approve PO",
            from_state=pending, to_state=approved
        )
        Transition.objects.get_or_create(
            workflow=wf, name="Reject PO",
            from_state=pending, to_state=rejected
        )
        Transition.objects.get_or_create(
            workflow=wf, name="Receive Goods",
            from_state=approved, to_state=received,
            defaults={'actions': 'receive_po_stock'}  # <-- Triggers our custom ledger logic
        )
        
        self.stdout.write(self.style.SUCCESS('Successfully seeded Standard Procurement Flow!'))
