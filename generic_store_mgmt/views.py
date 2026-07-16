from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.urls import reverse
from django.contrib import messages
from .models import Product, Category, Brand
from .forms import ProductForm

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

@login_required
def product_create_modal(request):
    if request.method == "POST":
        form = ProductForm(request.POST)
        if form.is_valid():
            product = form.save()
            messages.success(request, f"Product {product.name} created.")
            if request.headers.get('HX-Request'):
                response = HttpResponse()
                response['HX-Refresh'] = 'true'
                return response
            return redirect('generic_store_mgmt:product_list')
    else:
        form = ProductForm()
    return render(request, 'generic_store_mgmt/product_form_modal.html', {'form': form, 'is_edit': False})

@login_required
def product_edit_modal(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == "POST":
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            product = form.save()
            messages.success(request, f"Product {product.name} updated.")
            if request.headers.get('HX-Request'):
                response = HttpResponse()
                response['HX-Refresh'] = 'true'
                return response
            return redirect('generic_store_mgmt:product_list')
    else:
        form = ProductForm(instance=product)
    return render(request, 'generic_store_mgmt/product_form_modal.html', {'form': form, 'is_edit': True, 'product': product})

