from django.apps import apps
from django.shortcuts import get_object_or_404, redirect
from django.http import HttpResponse
from django.template.response import TemplateResponse
from django.forms import modelform_factory
from django.contrib.auth.decorators import login_required

from django.core.paginator import Paginator

def get_model(model_name):
    return apps.get_model('inventory', model_name)

@login_required
def manage_list(request, model_name):
    model = get_model(model_name)
    queryset = model.objects.all()
    if hasattr(model, 'created_at'):
        queryset = queryset.order_by('-created_at')
    else:
        queryset = queryset.order_by('-id')
    
    # Simple Generic Search
    q = request.GET.get('q', '')
    if q and hasattr(model, 'name'):
        queryset = queryset.filter(name__icontains=q)
        
    paginator = Paginator(queryset, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
        
    # Exclude complex relationships or large text fields from generic list view
    exclude_fields = ['id', 'description', 'address'] 
    fields = [f.name for f in model._meta.fields if f.name not in exclude_fields]
    
    context = {
        'objects': page_obj.object_list,
        'page_obj': page_obj,
        'paginator': paginator,
        'model_name': model_name,
        'model_name_display': model._meta.verbose_name_plural.title(),
        'fields': fields,
        'search_url': request.path,
    }
    
    if request.htmx:
        return TemplateResponse(request, 'inventory/generic/partials/list_rows.html', context)
    return TemplateResponse(request, 'inventory/generic/list.html', context)

@login_required
def manage_create(request, model_name):
    model = get_model(model_name)
    Form = modelform_factory(model, exclude=['workflow_state', 'created_at', 'updated_at'])
    
    if request.method == 'POST':
        form = Form(request.POST)
        if form.is_valid():
            obj = form.save()
            return redirect('inventory:manage_list', model_name=model_name)
    else:
        form = Form()
        
    context = {'form': form, 'model_name': model_name, 'action': 'Create'}
    return TemplateResponse(request, 'inventory/generic/form.html', context)

@login_required
def manage_update(request, model_name, pk):
    model = get_model(model_name)
    obj = get_object_or_404(model, pk=pk)
    Form = modelform_factory(model, exclude=['workflow_state', 'created_at', 'updated_at'])
    
    if request.method == 'POST':
        form = Form(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            return redirect('inventory:manage_list', model_name=model_name)
    else:
        form = Form(instance=obj)
        
    context = {'form': form, 'model_name': model_name, 'action': 'Update', 'object': obj}
    return TemplateResponse(request, 'inventory/generic/form.html', context)

@login_required
def manage_delete(request, model_name, pk):
    model = get_model(model_name)
    obj = get_object_or_404(model, pk=pk)
    if request.method == 'POST':
        obj.delete()
        if request.htmx:
            response = HttpResponse()
            response['HX-Redirect'] = f"/inventory/manage/{model_name}/"
            return response
        return redirect('inventory:manage_list', model_name=model_name)
        
    context = {'object': obj, 'model_name': model_name}
    return TemplateResponse(request, 'inventory/generic/delete.html', context)
