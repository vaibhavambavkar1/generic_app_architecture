# Migration Guide: Django (HTMX) to Django REST Framework (DRF)

This document outlines the architectural strategy and step-by-step process for migrating the current Server-Side Rendered (SSR) HTMX ERP framework into a Headless API architecture using Django REST Framework (DRF).

**Note:** You do *not* have to destroy the HTMX frontend. DRF can easily run side-by-side with your existing HTMX views, allowing you to build a headless JSON API (e.g., for a mobile app or external integrations) while maintaining the fast HTMX web dashboard.

---

## Phase 1: Installation & Configuration

### 1. Install DRF & JWT Authentication
Update your `requirements.txt`:
```text
djangorestframework>=3.14.0
djangorestframework-simplejwt>=5.3.0
```
Run `docker compose exec web pip install -r requirements.txt`.

### 2. Update `settings.py`
Add DRF to your installed apps and configure the default authentication and permission classes.
```python
INSTALLED_APPS += [
    'rest_framework',
    'rest_framework_simplejwt',
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 50,
}
```

---

## Phase 2: Building the API Layer (Domain Driven)

Instead of rewriting your models, DRF sits on top of your existing `models.py` and `mixins.py`. You will build a new serialization layer.

### 1. Create `serializers.py`
In your `inventory` app, create `serializers.py`. This translates your database models into JSON.

```python
from rest_framework import serializers
from .models import Item, PurchaseOrder

class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = ['id', 'sku', 'name', 'stock_quantity', 'price', 'created_at']

class PurchaseOrderSerializer(serializers.ModelSerializer):
    item = ItemSerializer(read_only=True)
    item_id = serializers.PrimaryKeyRelatedField(
        queryset=Item.objects.all(), source='item', write_only=True
    )
    
    # Expose the workflow state dynamically
    status = serializers.CharField(source='workflow_state.name', read_only=True)

    class Meta:
        model = PurchaseOrder
        fields = ['id', 'item', 'item_id', 'quantity', 'total_cost', 'status', 'created_at']
```

### 2. Create `api_views.py` (or rewrite `views.py`)
Use DRF's highly optimized `ViewSets` to automatically generate all CRUD operations (Create, Read, Update, Delete) without writing manual HTML handlers.

```python
from rest_framework import viewsets
from .models import Item, PurchaseOrder
from .serializers import ItemSerializer, PurchaseOrderSerializer

class ItemViewSet(viewsets.ModelViewSet):
    queryset = Item.objects.all()
    serializer_class = ItemSerializer

class PurchaseOrderViewSet(viewsets.ModelViewSet):
    queryset = PurchaseOrder.objects.select_related('item', 'workflow_state')
    serializer_class = PurchaseOrderSerializer
```

---

## Phase 3: Routing the API

Create a centralized API router in your main `erp_framework/urls.py` (or inside the apps).

```python
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from inventory.api_views import ItemViewSet, PurchaseOrderViewSet
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

# Initialize the REST Router
router = DefaultRouter()
router.register(r'items', ItemViewSet)
router.register(r'pos', PurchaseOrderViewSet)

urlpatterns = [
    # Existing HTMX Web Routes
    path('', include('core.urls')),
    path('inventory/', include('inventory.urls')),
    
    # New DRF API Routes
    path('api/v1/', include(router.urls)),
    
    # Authentication Endpoints
    path('api/v1/auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/v1/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
```

---

## Phase 4: Refactoring Advanced Core Features

Since we built advanced asynchronous logic into `core`, here is how you port it to DRF:

### 1. Migrating the Universal Audit Log
Currently, our HTMX views inject `request.user` into the model (or via Middleware). 
In DRF, you can override the `perform_create` and `perform_update` methods in your ViewSets to inject the user:

```python
class PurchaseOrderViewSet(viewsets.ModelViewSet):
    # ...
    def perform_create(self, serializer):
        # Inject the JWT authenticated user for the Audit Log
        serializer.save(_audit_user_id=self.request.user.id)
```

### 2. Migrating the Workflow Rule Engine
To execute a workflow transition via API, create a custom `@action` inside the `PurchaseOrderViewSet`:

```python
from rest_framework.decorators import action
from rest_framework.response import Response

class PurchaseOrderViewSet(viewsets.ModelViewSet):
    # ...
    
    @action(detail=True, methods=['post'])
    def transition(self, request, pk=None):
        po = self.get_object()
        transition_id = request.data.get('transition_id')
        
        try:
            transition = Transition.objects.get(id=transition_id)
            po.transition_to(transition, request.user)
            return Response({'status': 'Workflow transition successful', 'new_state': po.workflow_state.name})
        except Exception as e:
            return Response({'error': str(e)}, status=400)
```

---

## Phase 5: Decoupling the Frontend

Once the API is stable, you have two choices:
1. **Hybrid Mode (Recommended):** Keep the fast, Server-Side Rendered HTMX dashboards for internal staff, and expose the `/api/v1/` routes exclusively for mobile apps, external clients, or 3rd party B2B integrations.
2. **Full Decoupling:** Delete the `templates/` directory entirely. Build a separate React/Vue/Angular/NextJS frontend that runs on a different Node.js server, communicating exclusively with Django via JSON API requests and JWT Bearer Tokens.
