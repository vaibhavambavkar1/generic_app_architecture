from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.urls import reverse
from django.contrib import messages
from .models import PurchaseRequest, GoodsReceiptNote, StorePurchaseOrder
from .forms import PurchaseRequestForm, GRNForm

@login_required
def dashboard(request):
    prs = PurchaseRequest.objects.count()
    pos = StorePurchaseOrder.objects.count()
    grns = GoodsReceiptNote.objects.count()
    
    context = {
        'prs': prs,
        'pos': pos,
        'grns': grns
    }
    return render(request, 'purchasing/dashboard.html', context)

@login_required
def pr_list(request):
    prs = PurchaseRequest.objects.all().order_by('-created_at')
    return render(request, 'purchasing/pr_list.html', {'prs': prs})

@login_required
def pr_create(request):
    if request.method == "POST":
        form = PurchaseRequestForm(request.POST)
        if form.is_valid():
            pr = form.save()
            messages.success(request, f"Purchase Request {pr.request_number} created successfully.")
            if request.headers.get('HX-Request'):
                response = HttpResponse()
                response['HX-Redirect'] = reverse('purchasing:pr_list')
                return response
            return redirect('purchasing:pr_list')
    else:
        form = PurchaseRequestForm()
    
    return render(request, 'purchasing/pr_form.html', {'form': form})

@login_required
def grn_list(request):
    grns = GoodsReceiptNote.objects.select_related('purchase_order').all().order_by('-created_at')
    return render(request, 'purchasing/grn_list.html', {'grns': grns})

@login_required
def grn_create(request):
    if request.method == "POST":
        form = GRNForm(request.POST)
        if form.is_valid():
            grn = form.save()
            messages.success(request, f"Goods Receipt Note {grn.grn_number} created successfully.")
            if request.headers.get('HX-Request'):
                response = HttpResponse()
                response['HX-Redirect'] = reverse('purchasing:grn_list')
                return response
            return redirect('purchasing:grn_list')
    else:
        form = GRNForm()
        
    return render(request, 'purchasing/grn_form.html', {'form': form})

from .models import PurchaseRequestItem, GRNLineItem
from .forms import PurchaseRequestItemForm, GRNLineItemForm

@login_required
def pr_detail(request, pk):
    pr = get_object_or_404(PurchaseRequest, pk=pk)
    item_form = PurchaseRequestItemForm()
    return render(request, 'purchasing/pr_detail.html', {'pr': pr, 'item_form': item_form})

@login_required
def pr_add_item(request, pk):
    pr = get_object_or_404(PurchaseRequest, pk=pk)
    if request.method == "POST":
        form = PurchaseRequestItemForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.purchase_request = pr
            item.save()
            messages.success(request, "Item added to PR.")
        else:
            messages.error(request, "Failed to add item. Check form.")
    if request.headers.get('HX-Request'):
        response = HttpResponse()
        response['HX-Refresh'] = 'true'
        return response
    return redirect('purchasing:pr_detail', pk=pk)

@login_required
def pr_delete_item(request, item_pk):
    item = get_object_or_404(PurchaseRequestItem, pk=item_pk)
    pr_pk = item.purchase_request.pk
    item.delete()
    messages.success(request, "Item removed.")
    if request.headers.get('HX-Request'):
        response = HttpResponse()
        response['HX-Refresh'] = 'true'
        return response
    return redirect('purchasing:pr_detail', pk=pr_pk)


@login_required
def grn_detail(request, pk):
    grn = get_object_or_404(GoodsReceiptNote, pk=pk)
    
    # If POST and action=approve, do FSM approve
    if request.method == "POST" and request.POST.get('action') == 'approve':
        try:
            grn.receive_goods()
            grn.save()
            messages.success(request, f"GRN #{grn.grn_number} received. Ledger updated.")
        except Exception as e:
            messages.error(request, f"Failed to approve GRN: {str(e)}")
            
        if request.headers.get('HX-Request'):
            response = HttpResponse()
            response['HX-Refresh'] = 'true'
            return response
        return redirect('purchasing:grn_detail', pk=pk)
        
    item_form = GRNLineItemForm()
    return render(request, 'purchasing/grn_detail.html', {'grn': grn, 'item_form': item_form})

@login_required
def grn_add_item(request, pk):
    grn = get_object_or_404(GoodsReceiptNote, pk=pk)
    if request.method == "POST":
        form = GRNLineItemForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.grn = grn
            item.save()
            messages.success(request, "Item added to GRN.")
        else:
            messages.error(request, "Failed to add item.")
    if request.headers.get('HX-Request'):
        response = HttpResponse()
        response['HX-Refresh'] = 'true'
        return response
    return redirect('purchasing:grn_detail', pk=pk)

@login_required
def grn_delete_item(request, item_pk):
    item = get_object_or_404(GRNLineItem, pk=item_pk)
    grn_pk = item.grn.pk
    item.delete()
    messages.success(request, "Item removed.")
    if request.headers.get('HX-Request'):
        response = HttpResponse()
        response['HX-Refresh'] = 'true'
        return response
    return redirect('purchasing:grn_detail', pk=grn_pk)

@login_required
def grn_approve_modal(request, pk):
    grn = get_object_or_404(GoodsReceiptNote, pk=pk)
    return render(request, 'purchasing/grn_approve_modal.html', {'grn': grn})
