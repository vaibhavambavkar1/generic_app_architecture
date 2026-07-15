from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Product, Category, Brand

@login_required
def dashboard(request):
    total_products = Product.objects.count()
    active_products = Product.objects.filter(is_active=True).count()
    categories = Category.objects.count()
    brands = Brand.objects.count()
    
    context = {
        'total_products': total_products,
        'active_products': active_products,
        'categories': categories,
        'brands': brands,
    }
    return render(request, 'generic_store_mgmt/dashboard.html', context)

@login_required
def product_list(request):
    products = Product.objects.all()
    if request.GET.get('q'):
        products = products.filter(name__icontains=request.GET['q'])
    
    return render(request, 'generic_store_mgmt/product_list.html', {'products': products})
