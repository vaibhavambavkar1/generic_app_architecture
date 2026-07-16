from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.urls import reverse
from django.contrib import messages
from .models import Product, Category, Brand, UnitOfMeasure
from .forms import ProductForm, CategoryForm, BrandForm, UnitOfMeasureForm

@login_required
def dashboard(request):
    total_products = Product.objects.count()
    active_products = Product.objects.filter(is_active=True).count()
    categories_count = Category.objects.count()
    brands_count = Brand.objects.count()
    
    context = {
        'total_products': total_products,
        'active_products': active_products,
        'categories_count': categories_count,
        'brands_count': brands_count,
        'categories': Category.objects.all(),
        'brands': Brand.objects.all(),
        'uoms': UnitOfMeasure.objects.all(),
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

@login_required
def category_create_modal(request):
    if request.method == "POST":
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Category created.")
            if request.headers.get('HX-Request'):
                response = HttpResponse()
                response['HX-Refresh'] = 'true'
                return response
            return redirect('generic_store_mgmt:dashboard')
    else:
        form = CategoryForm()
    return render(request, 'generic_store_mgmt/master_data_form_modal.html', {'form': form, 'is_edit': False, 'model_name': 'Category'})

@login_required
def category_edit_modal(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == "POST":
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, "Category updated.")
            if request.headers.get('HX-Request'):
                response = HttpResponse()
                response['HX-Refresh'] = 'true'
                return response
            return redirect('generic_store_mgmt:dashboard')
    else:
        form = CategoryForm(instance=category)
    return render(request, 'generic_store_mgmt/master_data_form_modal.html', {'form': form, 'is_edit': True, 'model_name': 'Category'})

@login_required
def brand_create_modal(request):
    if request.method == "POST":
        form = BrandForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Brand created.")
            if request.headers.get('HX-Request'):
                response = HttpResponse()
                response['HX-Refresh'] = 'true'
                return response
            return redirect('generic_store_mgmt:dashboard')
    else:
        form = BrandForm()
    return render(request, 'generic_store_mgmt/master_data_form_modal.html', {'form': form, 'is_edit': False, 'model_name': 'Brand'})

@login_required
def brand_edit_modal(request, pk):
    brand = get_object_or_404(Brand, pk=pk)
    if request.method == "POST":
        form = BrandForm(request.POST, instance=brand)
        if form.is_valid():
            form.save()
            messages.success(request, "Brand updated.")
            if request.headers.get('HX-Request'):
                response = HttpResponse()
                response['HX-Refresh'] = 'true'
                return response
            return redirect('generic_store_mgmt:dashboard')
    else:
        form = BrandForm(instance=brand)
    return render(request, 'generic_store_mgmt/master_data_form_modal.html', {'form': form, 'is_edit': True, 'model_name': 'Brand'})

@login_required
def uom_create_modal(request):
    if request.method == "POST":
        form = UnitOfMeasureForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "UOM created.")
            if request.headers.get('HX-Request'):
                response = HttpResponse()
                response['HX-Refresh'] = 'true'
                return response
            return redirect('generic_store_mgmt:dashboard')
    else:
        form = UnitOfMeasureForm()
    return render(request, 'generic_store_mgmt/master_data_form_modal.html', {'form': form, 'is_edit': False, 'model_name': 'UOM'})

@login_required
def uom_edit_modal(request, pk):
    uom = get_object_or_404(UnitOfMeasure, pk=pk)
    if request.method == "POST":
        form = UnitOfMeasureForm(request.POST, instance=uom)
        if form.is_valid():
            form.save()
            messages.success(request, "UOM updated.")
            if request.headers.get('HX-Request'):
                response = HttpResponse()
                response['HX-Refresh'] = 'true'
                return response
            return redirect('generic_store_mgmt:dashboard')
    else:
        form = UnitOfMeasureForm(instance=uom)
    return render(request, 'generic_store_mgmt/master_data_form_modal.html', {'form': form, 'is_edit': True, 'model_name': 'UOM'})
