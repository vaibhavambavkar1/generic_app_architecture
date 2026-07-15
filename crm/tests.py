from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from core.models import Workflow, State, Organization
from crm.models import Customer, Lead
from decimal import Decimal
from datetime import date

User = get_user_model()

class CRMTests(TestCase):
    def setUp(self):
        # Bypass Organization Setup redirect
        Organization.objects.create(
            name='Test Org',
            owner_name='Test Owner',
            email='test@example.com'
        )

        # Create a test user
        self.user = User.objects.create_user(
            username='testuser', 
            email='test@example.com', 
            password='testpassword'
        )
        self.client = Client()
        self.client.login(username='testuser', password='testpassword')

        # Create workflows and states for Lead
        self.workflow = Workflow.objects.create(name='Lead Pipeline Workflow', model_name='crm.Lead')
        self.state_draft = State.objects.create(name='Draft', workflow=self.workflow, is_initial=True)
        self.state_contacted = State.objects.create(name='Contacted', workflow=self.workflow)
        self.state_qualified = State.objects.create(name='Qualified', workflow=self.workflow)
        self.state_proposal = State.objects.create(name='Proposal', workflow=self.workflow)
        self.state_won = State.objects.create(name='Won', workflow=self.workflow)
        self.state_lost = State.objects.create(name='Lost', workflow=self.workflow)

        # Create a customer
        self.customer = Customer.objects.create(
            name='Acme Corp',
            email='info@acmecorp.com',
            phone='1234567890',
            industry='Technology'
        )

        # Create a lead
        self.lead = Lead.objects.create(
            title='Website Redesign',
            customer=self.customer,
            value=Decimal('5000.00'),
            status='Draft',
            workflow_state=self.state_draft,
            expected_close_date=date(2026, 12, 31)
        )

    def test_customer_creation(self):
        """Test Customer model creation and string representation."""
        self.assertEqual(self.customer.name, 'Acme Corp')
        self.assertEqual(str(self.customer), 'Acme Corp')
        self.assertTrue(self.customer.is_active)

    def test_lead_creation(self):
        """Test Lead model creation and string representation."""
        self.assertEqual(self.lead.title, 'Website Redesign')
        self.assertEqual(self.lead.value, Decimal('5000.00'))
        self.assertEqual(str(self.lead), 'Website Redesign - Acme Corp')
        self.assertEqual(self.lead.status, 'Draft')

    def test_lead_state_transitions(self):
        """Test FSM state transitions for Lead."""
        # Draft -> Contacted
        self.lead.mark_contacted()
        self.lead.save()
        self.assertEqual(self.lead.status, 'Contacted')

        # Contacted -> Qualified
        self.lead.mark_qualified()
        self.lead.save()
        self.assertEqual(self.lead.status, 'Qualified')

        # Qualified -> Proposal
        self.lead.send_proposal()
        self.lead.save()
        self.assertEqual(self.lead.status, 'Proposal')

        # Proposal -> Won
        self.lead.mark_won()
        self.lead.save()
        self.assertEqual(self.lead.status, 'Won')

    def test_lead_lost_transition(self):
        """Test transitioning a lead straight to Lost."""
        self.lead.mark_lost()
        self.lead.save()
        self.assertEqual(self.lead.status, 'Lost')

    def test_dashboard_view(self):
        """Test the CRM dashboard view."""
        response = self.client.get(reverse('crm:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'crm/dashboard.html')
        self.assertIn('kanban_data', response.context)

    def test_customer_list_view(self):
        """Test Customer List view."""
        response = self.client.get(reverse('crm:customer_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'crm/customer_list.html')
        self.assertContains(response, 'Acme Corp')

    def test_customer_create_view(self):
        """Test creating a customer via view."""
        data = {
            'name': 'Globex',
            'email': 'contact@globex.com',
            'phone': '0987654321',
            'industry': 'Manufacturing',
            'is_active': True
        }
        response = self.client.post(reverse('crm:customer_create'), data)
        self.assertEqual(response.status_code, 302)  # Should redirect on success
        self.assertTrue(Customer.objects.filter(name='Globex').exists())

    def test_lead_list_view(self):
        """Test Lead List (Pipeline) view."""
        response = self.client.get(reverse('crm:lead_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'crm/lead_list.html')
        self.assertContains(response, 'Website Redesign')

    def test_lead_create_view(self):
        """Test creating a lead via view."""
        data = {
            'title': 'SEO Optimization',
            'customer': self.customer.id,
            'value': '1500.00',
            'expected_close_date': '2026-10-15',
            'notes': 'Needs quick turnaround.'
        }
        response = self.client.post(reverse('crm:lead_create'), data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Lead.objects.filter(title='SEO Optimization').exists())
        
        new_lead = Lead.objects.get(title='SEO Optimization')
        self.assertEqual(new_lead.status, 'Draft')
        self.assertEqual(new_lead.workflow_state.name, 'Draft')

    def test_lead_detail_view(self):
        """Test Lead Detail view."""
        response = self.client.get(reverse('crm:lead_detail', args=[self.lead.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'crm/lead_detail.html')
        self.assertContains(response, 'Website Redesign')
        self.assertContains(response, 'Acme Corp')

    def test_lead_transition_via_view(self):
        """Test advancing a lead's state via POST request."""
        # Initial state is Draft. We should be able to move to Contacted.
        data = {'method': 'mark_contacted'}
        response = self.client.post(reverse('crm:lead_detail', args=[self.lead.pk]), data)
        self.assertEqual(response.status_code, 302)  # Redirects back to detail page
        
        self.lead.refresh_from_db()
        self.assertEqual(self.lead.status, 'Contacted')
        self.assertEqual(self.lead.workflow_state.name, 'Contacted')

    def test_auth_required(self):
        """Test that views require login."""
        self.client.logout()
        response = self.client.get(reverse('crm:dashboard'))
        self.assertNotEqual(response.status_code, 200)  # Should redirect to login or give 403
