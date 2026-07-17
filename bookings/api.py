from rest_framework import viewsets, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Resource, Booking
from .serializers import ResourceSerializer, BookingSerializer

class TenantAPIPermission(permissions.BasePermission):
    """
    Custom permission to ensure API requests have a resolved tenant.
    """
    def has_permission(self, request, view):
        return hasattr(request, 'tenant') and request.tenant is not None

class ResourceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows resources to be viewed.
    """
    serializer_class = ResourceSerializer
    permission_classes = [permissions.IsAuthenticated, TenantAPIPermission]

    def get_queryset(self):
        return Resource.objects.filter(business=self.request.tenant)

class BookingViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows bookings to be viewed.
    """
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated, TenantAPIPermission]

    def get_queryset(self):
        return Booking.objects.filter(business=self.request.tenant)
        
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        booking = self.get_object()
        from .services.booking_service import BookingService
        
        try:
            BookingService.cancel_booking(booking, user=request.user)
            return Response({'status': 'Booking cancelled successfully.'})
        except Exception as e:
            return Response({'error': str(e)}, status=400)
