from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from .models import Waybill, DispatchManifest, ManifestItem

def dispatcher_dashboard(request):
    open_manifests = DispatchManifest.objects.filter(status='Draft')
    
    # Just grab the first open manifest for the demo if it exists
    active_manifest = open_manifests.first()
    
    context = {
        'open_manifests': open_manifests,
        'active_manifest': active_manifest,
    }
    return render(request, 'courier/dispatcher_dashboard.html', context)

def add_waybill_to_manifest(request, manifest_id):
    if request.method == "POST":
        manifest = get_object_or_404(DispatchManifest, id=manifest_id)
        waybill_number = request.POST.get('waybill_number', '').strip()
        
        if not waybill_number:
             return HttpResponse("<div class='text-error text-sm mt-1'>Please enter a waybill number.</div>")
             
        try:
            waybill = Waybill.objects.get(waybill_number=waybill_number)
            
            if waybill.status not in ['Draft', 'Manifested']:
                return HttpResponse(f"<div class='text-error text-sm mt-1'>Waybill {waybill_number} is already in state {waybill.status}</div>")
                
            if ManifestItem.objects.filter(manifest=manifest, waybill=waybill).exists():
                 return HttpResponse(f"<div class='text-warning text-sm mt-1'>Waybill {waybill_number} is already in this manifest.</div>")
            
            # Add to manifest
            seq = manifest.items.count() + 1
            ManifestItem.objects.create(manifest=manifest, waybill=waybill, sequence=seq)
            
            # Transition waybill status
            if waybill.status == 'Draft':
                waybill.add_to_manifest()
                waybill.save()
            
            items = manifest.items.all().order_by('sequence')
            return render(request, 'courier/partials/manifest_items.html', {'manifest': manifest, 'items': items})
            
        except Waybill.DoesNotExist:
            return HttpResponse(f"<div class='text-error text-sm mt-1'>Waybill {waybill_number} not found.</div>")
    return HttpResponse("Invalid Request", status=400)

def download_waybill_pdf(request, waybill_id):
    from .pdf import generate_waybill_pdf
    waybill = get_object_or_404(Waybill, id=waybill_id)
    return generate_waybill_pdf(waybill)

from django.contrib import messages
from django.shortcuts import redirect

def dispatch_manifest(request, manifest_id):
    if request.method == "POST":
        manifest = get_object_or_404(DispatchManifest, id=manifest_id)
        if manifest.status == 'Draft':
            manifest.dispatch()
            manifest.save()
            messages.success(request, f"Manifest {manifest.manifest_number} successfully dispatched!")
        else:
            messages.error(request, f"Manifest {manifest.manifest_number} cannot be dispatched from state {manifest.status}.")
    return redirect('courier:dispatcher_dashboard')

from .forms import DispatchManifestForm

import uuid

def manifest_create(request):
    if request.method == 'POST':
        form = DispatchManifestForm(request.POST)
        if form.is_valid():
            manifest = form.save(commit=False)
            manifest.manifest_number = f"MAN-{uuid.uuid4().hex[:8].upper()}"
            manifest.status = 'Draft'
            manifest.save()
            messages.success(request, f"Manifest {manifest.manifest_number} created!")
            
            response = HttpResponse()
            response['HX-Redirect'] = request.build_absolute_uri('/courier/dashboard/')
            return response
    else:
        form = DispatchManifestForm()
        
    return render(request, 'courier/modals/manifest_form.html', {'form': form})
