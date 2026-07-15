from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from core.models import Organization, Workflow, State, UserProfile, Transition
from core.middleware import OrganizationEnforcementMiddleware
from django.test import RequestFactory

User = get_user_model()

class CoreTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='admin', email='admin@test.com', password='testpassword')
        self.factory = RequestFactory()

    def test_organization_singleton(self):
        """Test that only one Organization can be created."""
        org1 = Organization(name='Org 1', owner_name='Owner 1', email='test1@test.com')
        org1.full_clean()
        org1.save()

        org2 = Organization(name='Org 2', owner_name='Owner 2', email='test2@test.com')
        with self.assertRaises(ValidationError):
            org2.clean()
            
    def test_user_profile_signal_and_security(self):
        """Test UserProfile is created via signals and security answer hashing works."""
        profile = UserProfile.objects.get(user=self.user)
        self.assertIsNotNone(profile)
        
        profile.set_security_answer("MySecretAnswer")
        self.assertTrue(profile.check_security_answer("mysecretanswer"))
        self.assertFalse(profile.check_security_answer("wronganswer"))
        
    def test_workflow_models_creation(self):
        """Test creation of Workflow, State, and Transition."""
        wf = Workflow.objects.create(name='Test Workflow', model_name='core.TestModel')
        state1 = State.objects.create(name='State 1', workflow=wf, is_initial=True)
        state2 = State.objects.create(name='State 2', workflow=wf)
        
        trans = Transition.objects.create(
            workflow=wf,
            name='Move to State 2',
            from_state=state1,
            to_state=state2
        )
        self.assertEqual(str(trans), 'Move to State 2 (State 1 -> State 2)')

    def test_organization_enforcement_middleware_redirect(self):
        Organization.objects.all().delete()
        self.client.login(username='admin', password='testpassword')
        response = self.client.get(reverse('inventory:dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('core:organization_create'), response.url)

    def test_organization_enforcement_middleware_pass(self):
        Organization.objects.create(name='Test Org', owner_name='Owner 1', email='test@test.com')
        self.client.login(username='admin', password='testpassword')
        response = self.client.get(reverse('inventory:dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_organization_create_view(self):
        Organization.objects.all().delete()
        self.client.login(username='admin', password='testpassword')
        data = {
            'name': 'New Startup',
            'owner_name': 'John Doe',
            'email': 'startup@example.com',
            'phone': '9876543210'
        }
        response = self.client.post(reverse('core:organization_create'), data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Organization.objects.filter(name='New Startup').exists())

    def test_global_search_view(self):
        """Test the global search view logic."""
        Organization.objects.create(name='Test Org', owner_name='Owner 1', email='test@test.com')
        self.client.login(username='admin', password='testpassword')
        
        response = self.client.get(reverse('core:global_search') + "?q=Test")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/components/search_results.html')
        self.assertIn('query', response.context)
