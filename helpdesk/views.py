from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count
from .models import Ticket, TicketCategory, TicketComment
from .forms import TicketForm, TicketCommentForm
from core.models import State, Workflow

@login_required
def dashboard(request):
    """Helpdesk Dashboard."""
    total_tickets = Ticket.objects.count()
    open_tickets = Ticket.objects.filter(status='Open').count()
    in_progress = Ticket.objects.filter(status='In Progress').count()
    resolved = Ticket.objects.filter(status='Resolved').count()
    
    # My tickets
    my_tickets = Ticket.objects.filter(reporter=request.user).order_by('-created_at')[:5]
    assigned_to_me = Ticket.objects.filter(assignee=request.user, status__in=['Open', 'In Progress']).order_by('-created_at')[:5]
    
    # Kanban data
    board_columns = ['Open', 'In Progress', 'Resolved', 'Closed']
    kanban_data = {}
    for col in board_columns:
        kanban_data[col] = Ticket.objects.filter(status=col).select_related('reporter', 'assignee')
        
    return render(request, 'helpdesk/dashboard.html', {
        'total_tickets': total_tickets,
        'open_tickets': open_tickets,
        'in_progress': in_progress,
        'resolved': resolved,
        'my_tickets': my_tickets,
        'assigned_to_me': assigned_to_me,
        'kanban_data': kanban_data,
        'board_columns': board_columns
    })

@login_required
def ticket_list(request):
    query = request.GET.get('q', '')
    if query:
        tickets = Ticket.objects.filter(title__icontains=query)
    else:
        tickets = Ticket.objects.all().order_by('-created_at')
    return render(request, 'helpdesk/ticket_list.html', {'tickets': tickets, 'query': query})

@login_required
def ticket_create(request):
    if request.method == 'POST':
        form = TicketForm(request.POST)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.reporter = request.user
            
            workflow, _ = Workflow.objects.get_or_create(
                name='Helpdesk Ticket', 
                defaults={'model_name': ticket.get_workflow_name()}
            )
            state, _ = State.objects.get_or_create(
                name='Open', 
                workflow=workflow,
                defaults={'is_initial': True}
            )
            
            ticket.workflow_state = state
            ticket.status = 'Open'
            ticket.save()
            messages.success(request, "Ticket created successfully.")
            return redirect('helpdesk:ticket_list')
    else:
        form = TicketForm()
    return render(request, 'helpdesk/ticket_form.html', {'form': form, 'title': 'Create New Ticket'})

@login_required
def ticket_detail(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)
    comments = ticket.comments.all().order_by('created_at')
    
    fsm_map = ticket.__class__._get_fsm_transition_map()
    available_transitions = []
    
    for (source, target), method_name in fsm_map.items():
        if source == ticket.status or source == '*':
            available_transitions.append({
                'name': method_name.replace('_', ' ').title(),
                'target': target,
                'method': method_name
            })
            
    if request.method == 'POST':
        if 'add_comment' in request.POST:
            form = TicketCommentForm(request.POST)
            if form.is_valid():
                comment = form.save(commit=False)
                comment.ticket = ticket
                comment.author = request.user
                comment.save()
                messages.success(request, "Comment added.")
                return redirect('helpdesk:ticket_detail', pk=ticket.pk)
        elif 'method' in request.POST:
            method_name = request.POST.get('method')
            if method_name:
                if method_name == 'assign_ticket':
                    ticket.assign_ticket(request.user)
                elif method_name == 'mark_resolved':
                    notes = request.POST.get('resolution_notes', '')
                    ticket.mark_resolved(notes=notes)
                elif method_name == 'close_ticket':
                    ticket.close_ticket()
                elif method_name == 'reopen_ticket':
                    ticket.reopen_ticket()
                    
                ticket.save(update_fields=['status', 'assignee', 'resolution_notes'])
                
                # Sync state
                workflow, _ = Workflow.objects.get_or_create(
                    name='Helpdesk Ticket', 
                    defaults={'model_name': ticket.get_workflow_name()}
                )
                state, _ = State.objects.get_or_create(name=ticket.status, workflow=workflow)
                ticket.workflow_state = state
                ticket.save(update_fields=['workflow_state'])
                
                messages.success(request, f"Ticket moved to {ticket.status}.")
                return redirect('helpdesk:ticket_detail', pk=ticket.pk)
    else:
        form = TicketCommentForm()
        
    return render(request, 'helpdesk/ticket_detail.html', {
        'ticket': ticket,
        'comments': comments,
        'form': form,
        'available_transitions': available_transitions
    })
