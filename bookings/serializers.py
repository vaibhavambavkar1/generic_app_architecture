from rest_framework import serializers
from .models import Resource, Booking, Customer

class ResourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resource
        fields = ['id', 'name', 'code', 'capacity', 'is_active']

class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ['id', 'name', 'email', 'phone']

class BookingSerializer(serializers.ModelSerializer):
    customer = CustomerSerializer(read_only=True)
    
    class Meta:
        model = Booking
        fields = ['id', 'booking_number', 'customer', 'status', 'start_datetime', 'end_datetime', 'total_amount', 'created_at']
