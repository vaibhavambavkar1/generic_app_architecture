from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from core.models import Workflow, State, Organization
from helpdesk.models import TicketCategory, Ticket, TicketComment

User = get_user_model()

class HelpdeskTests(TestCase):
    def setUp(self):
        # Bypass Organization Setup redirect
        Organization.objects.create(
            name='Test Org',
            owner_name='Test Owner',
            email='test@example.com'
        )

        # Create reporter and assignee users
        self.reporter = User.objects.create_user(username='reporter', email='rep@test.com', password='testpassword')
        self.assignee = User.objects.create_user(username='assignee', email='ass@test.com', password='testpassword')

        self.client = Client()
        self.client.login(username='reporter', password='testpassword')

        # Create Category
        self.category = TicketCategory.objects.create(name='IT Support', description='Hardware/Software issues')

        # Setup Workflow
        self.workflow = Workflow.objects.create(name='Helpdesk Ticket', model_name='helpdesk.Ticket')
        self.state_open = State.objects.create(name='Open', workflow=self.workflow, is_initial=True)
        self.state_in_progress = State.objects.create(name='In Progress', workflow=self.workflow)
        self.state_resolved = State.objects.create(name='Resolved', workflow=self.workflow)
        self.state_closed = State.objects.create(name='Closed', workflow=self.workflow)

        # Create Ticket
        self.ticket = Ticket.objects.create(
            title='Cannot connect to VPN',
            description='VPN client keeps dropping connection after 5 minutes.',
            category=self.category,
            priority='High',
            reporter=self.reporter,
            status='Open',
            workflow_state=self.state_open
        )

    # --- 1. Model Tests ---
    def test_ticket_creation(self):
        """Test Ticket model creation and string representation."""
        self.assertEqual(self.ticket.title, 'Cannot connect to VPN')
        self.assertEqual(self.ticket.reporter, self.reporter)
        self.assertIsNone(self.ticket.assignee)
        self.assertEqual(str(self.ticket), f"TKT-{self.ticket.id}: Cannot connect to VPN")

    # --- 2. State Machine Tests ---
    def test_ticket_assign_transition(self):
        """Test FSM transition from Open to In Progress."""
        self.ticket.assign_ticket(self.assignee)
        self.ticket.save()
        self.assertEqual(self.ticket.status, 'In Progress')
        self.assertEqual(self.ticket.assignee, self.assignee)

    def test_ticket_resolved_transition(self):
        """Test FSM transition from In Progress to Resolved."""
        self.ticket.assign_ticket(self.assignee)
        self.ticket.save()
        
        self.ticket.mark_resolved(notes="Updated VPN config.")
        self.ticket.save()
        
        self.assertEqual(self.ticket.status, 'Resolved')
        self.assertEqual(self.ticket.resolution_notes, "Updated VPN config.")

    def test_ticket_close_transition(self):
        """Test FSM transition from Resolved to Closed."""
        self.ticket.assign_ticket(self.assignee)
        self.ticket.mark_resolved(notes="Done.")
        self.ticket.save()
        
        self.ticket.close_ticket()
        self.ticket.save()
        
        self.assertEqual(self.ticket.status, 'Closed')

    # --- 3. View Tests ---
    def test_dashboard_view(self):
        """Test Helpdesk Dashboard rendering."""
        response = self.client.get(reverse('helpdesk:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'helpdesk/dashboard.html')
        self.assertIn('total_tickets', response.context)
        self.assertIn('kanban_data', response.context)

    def test_ticket_list_view(self):
        """Test Ticket List view."""
        response = self.client.get(reverse('helpdesk:ticket_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'helpdesk/ticket_list.html')
        self.assertContains(response, 'Cannot connect to VPN')

    def test_ticket_create_view(self):
        """Test creating a new ticket via view/form."""
        data = {
            'title': 'New Monitor Request',
            'description': 'I need a second monitor.',
            'category': self.category.id,
            'priority': 'Low'
        }
        response = self.client.post(reverse('helpdesk:ticket_create'), data)
        self.assertEqual(response.status_code, 302)  # redirect to list
        self.assertTrue(Ticket.objects.filter(title='New Monitor Request').exists())
        
        new_ticket = Ticket.objects.get(title='New Monitor Request')
        self.assertEqual(new_ticket.reporter, self.reporter)
        self.assertEqual(new_ticket.status, 'Open')

    def test_ticket_detail_and_comment(self):
        """Test viewing a ticket and posting a comment."""
        response = self.client.get(reverse('helpdesk:ticket_detail', args=[self.ticket.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Cannot connect to VPN')
        
        # Add comment
        data = {
            'add_comment': '1',
            'body': 'Have you tried turning it off and on again?',
            'is_internal': False
        }
        response = self.client.post(reverse('helpdesk:ticket_detail', args=[self.ticket.id]), data)
        self.assertEqual(response.status_code, 302)
        
        self.assertTrue(TicketComment.objects.filter(ticket=self.ticket, body__icontains='turning it off').exists())

    def test_ticket_transition_via_view(self):
        """Test assignment transition via POST on detail view."""
        data = {
            'method': 'assign_ticket'
        }
        response = self.client.post(reverse('helpdesk:ticket_detail', args=[self.ticket.id]), data)
        self.assertEqual(response.status_code, 302)
        
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.status, 'In Progress')
        self.assertEqual(self.ticket.assignee, self.reporter) # Since reporter clicked "Assign to Me"
