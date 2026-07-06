from django.core.management.base import BaseCommand
from core.models import Workflow, State, Transition

class Command(BaseCommand):
    help = 'Seeds workflows for Item and Vendor models'

    def handle(self, *args, **options):
        # 1. Vendor Workflow
        vwf, _ = Workflow.objects.get_or_create(
            name="Vendor Approval Flow",
            model_name="inventory.Vendor",
            defaults={'description': "Approve vendors before using them for POs"}
        )
        vdraft, _ = State.objects.get_or_create(workflow=vwf, name="Draft", defaults={'is_initial': True})
        vactive, _ = State.objects.get_or_create(workflow=vwf, name="Active", defaults={'is_final': True})
        Transition.objects.get_or_create(workflow=vwf, name="Approve Vendor", from_state=vdraft, to_state=vactive)

        # 2. Item Workflow
        iwf, _ = Workflow.objects.get_or_create(
            name="Item Master Flow",
            model_name="inventory.Item",
            defaults={'description': "Verify new items before they can be purchased"}
        )
        idraft, _ = State.objects.get_or_create(workflow=iwf, name="Draft", defaults={'is_initial': True})
        iactive, _ = State.objects.get_or_create(workflow=iwf, name="Active", defaults={'is_final': True})
        Transition.objects.get_or_create(workflow=iwf, name="Approve Item", from_state=idraft, to_state=iactive)

        self.stdout.write(self.style.SUCCESS('Successfully seeded Vendor and Item workflows!'))
