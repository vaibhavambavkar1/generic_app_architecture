from django.core.management.base import BaseCommand
from core.models import Workflow, State, Transition

class Command(BaseCommand):
    help = 'Sets up the Workflow states and transitions for Hotel POS'

    def handle(self, *args, **options):
        self.stdout.write('Setting up Hotel POS Workflows...')
        
        # 1. Order Workflow
        order_wf, _ = Workflow.objects.get_or_create(
            name='Order Lifecycle',
            defaults={'model_name': 'hotel_pos.Order', 'description': 'Workflow for processing an entire order table.'}
        )
        
        o_open, _ = State.objects.get_or_create(workflow=order_wf, name='Open', defaults={'is_initial': True})
        o_billed, _ = State.objects.get_or_create(workflow=order_wf, name='Billed')
        o_paid, _ = State.objects.get_or_create(workflow=order_wf, name='Paid')
        o_closed, _ = State.objects.get_or_create(workflow=order_wf, name='Closed', defaults={'is_final': True})
        o_cancelled, _ = State.objects.get_or_create(workflow=order_wf, name='Cancelled', defaults={'is_final': True})
        
        Transition.objects.get_or_create(workflow=order_wf, from_state=o_open, to_state=o_billed, name='Generate Bill')
        Transition.objects.get_or_create(workflow=order_wf, from_state=o_billed, to_state=o_paid, name='Receive Payment')
        Transition.objects.get_or_create(workflow=order_wf, from_state=o_paid, to_state=o_closed, name='Close Order')
        Transition.objects.get_or_create(workflow=order_wf, from_state=o_open, to_state=o_cancelled, name='Cancel Order')
        Transition.objects.get_or_create(workflow=order_wf, from_state=o_billed, to_state=o_cancelled, name='Cancel Billed Order')
        
        # 2. OrderItem Workflow
        item_wf, _ = Workflow.objects.get_or_create(
            name='Order Item Lifecycle',
            defaults={'model_name': 'hotel_pos.OrderItem', 'description': 'Workflow for processing individual items (KOT).'}
        )
        
        i_pending, _ = State.objects.get_or_create(workflow=item_wf, name='Pending', defaults={'is_initial': True})
        i_cooking, _ = State.objects.get_or_create(workflow=item_wf, name='Cooking')
        i_served, _ = State.objects.get_or_create(workflow=item_wf, name='Served', defaults={'is_final': True})
        i_cancelled, _ = State.objects.get_or_create(workflow=item_wf, name='Cancelled', defaults={'is_final': True})
        
        Transition.objects.get_or_create(workflow=item_wf, from_state=i_pending, to_state=i_cooking, name='Send to Kitchen')
        Transition.objects.get_or_create(workflow=item_wf, from_state=i_cooking, to_state=i_served, name='Mark Served')
        Transition.objects.get_or_create(workflow=item_wf, from_state=i_pending, to_state=i_cancelled, name='Cancel Pending Item')
        Transition.objects.get_or_create(workflow=item_wf, from_state=i_cooking, to_state=i_cancelled, name='Cancel Cooking Item')
        
        self.stdout.write(self.style.SUCCESS('Successfully set up Hotel POS Workflows with Cancelled states!'))
