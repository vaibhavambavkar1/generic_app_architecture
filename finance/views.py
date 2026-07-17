from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from .models import Account, JournalEntry, JournalEntryLine
from .forms import JournalEntryForm, JournalEntryLineForm, AccountForm
from django.core.paginator import Paginator

@login_required
def account_list(request):
    accounts_list = Account.objects.all().order_by('category', 'code')
    paginator = Paginator(accounts_list, 10)
    page_number = request.GET.get('page')
    accounts = paginator.get_page(page_number)
    return render(request, 'finance/account_list.html', {'accounts': accounts})

@login_required
def account_create(request):
    if request.method == "POST":
        form = AccountForm(request.POST)
        if form.is_valid():
            acc = form.save()
            messages.success(request, f"Account {acc.code} created successfully.")
            if request.headers.get('HX-Request'):
                response = HttpResponse()
                response['HX-Refresh'] = 'true'
                return response
            return redirect('finance:account_list')
    else:
        form = AccountForm()
    return render(request, 'finance/account_create_modal.html', {'form': form})

@login_required
def journal_list(request):
    entries_list = JournalEntry.objects.all().order_by('-date', '-id')
    paginator = Paginator(entries_list, 10)
    page_number = request.GET.get('page')
    entries = paginator.get_page(page_number)
    return render(request, 'finance/journal_list.html', {'entries': entries})

@login_required
def journal_create(request):
    if request.method == "POST":
        form = JournalEntryForm(request.POST)
        if form.is_valid():
            je = form.save()
            return redirect('finance:journal_detail', pk=je.pk)
    else:
        form = JournalEntryForm()
    return render(request, 'finance/journal_form.html', {'form': form})

@login_required
def journal_detail(request, pk):
    je = get_object_or_404(JournalEntry, pk=pk)
    
    if request.method == "POST":
        if je.is_posted:
            messages.error(request, "Cannot modify a posted journal entry.")
        else:
            line_form = JournalEntryLineForm(request.POST)
            if line_form.is_valid():
                line = line_form.save(commit=False)
                line.journal_entry = je
                
                if line.debit > 0 and line.credit > 0:
                    messages.error(request, "A line cannot have both Debit and Credit.")
                elif line.debit == 0 and line.credit == 0:
                    messages.error(request, "A line must have either Debit or Credit.")
                else:
                    line.save()
                    messages.success(request, "Line added.")
            else:
                messages.error(request, "Invalid form.")
                
        if request.headers.get('HX-Request'):
            response = HttpResponse()
            response['HX-Refresh'] = 'true'
            return response
        return redirect('finance:journal_detail', pk=pk)
        
    line_form = JournalEntryLineForm()
    total_debit = sum(l.debit for l in je.lines.all())
    total_credit = sum(l.credit for l in je.lines.all())
    
    context = {
        'je': je,
        'line_form': line_form,
        'total_debit': total_debit,
        'total_credit': total_credit,
        'is_balanced': total_debit == total_credit and total_debit > 0
    }
    return render(request, 'finance/journal_detail.html', context)

@login_required
def journal_post(request, pk):
    je = get_object_or_404(JournalEntry, pk=pk)
    if not je.is_posted:
        total_debit = sum(l.debit for l in je.lines.all())
        total_credit = sum(l.credit for l in je.lines.all())
        if total_debit == total_credit and total_debit > 0:
            je.is_posted = True
            je.save()
            messages.success(request, "Journal Entry posted successfully.")
        else:
            messages.error(request, "Cannot post: Debits and Credits must balance and be > 0.")
            
    if request.headers.get('HX-Request'):
        response = HttpResponse()
        response['HX-Refresh'] = 'true'
        return response
    return redirect('finance:journal_detail', pk=pk)

@login_required
def account_edit(request, pk):
    acc = get_object_or_404(Account, pk=pk)
    if request.method == "POST":
        form = AccountForm(request.POST, instance=acc)
        if form.is_valid():
            form.save()
            messages.success(request, f"Account {acc.code} updated.")
            if request.headers.get('HX-Request'):
                response = HttpResponse()
                response['HX-Refresh'] = 'true'
                return response
            return redirect('finance:account_list')
    else:
        form = AccountForm(instance=acc)
    return render(request, 'finance/account_edit_modal.html', {'form': form, 'account': acc})

@login_required
def account_delete(request, pk):
    acc = get_object_or_404(Account, pk=pk)
    if request.method == "POST":
        if acc.journal_lines.exists():
            messages.error(request, f"Cannot delete Account {acc.code} because it has associated Journal Entries.")
        else:
            acc.delete()
            messages.success(request, f"Account {acc.code} deleted.")
        return redirect('finance:account_list')
    return redirect('finance:account_list')

@login_required
def journal_edit(request, pk):
    je = get_object_or_404(JournalEntry, pk=pk)
    if je.is_posted:
        messages.error(request, "Cannot edit a posted journal entry.")
        return redirect('finance:journal_list')
        
    if request.method == "POST":
        form = JournalEntryForm(request.POST, instance=je)
        if form.is_valid():
            form.save()
            messages.success(request, f"Journal Entry {je.entry_number} updated.")
            if request.headers.get('HX-Request'):
                response = HttpResponse()
                response['HX-Refresh'] = 'true'
                return response
            return redirect('finance:journal_list')
    else:
        form = JournalEntryForm(instance=je)
    return render(request, 'finance/journal_edit_modal.html', {'form': form, 'je': je})

@login_required
def journal_delete(request, pk):
    je = get_object_or_404(JournalEntry, pk=pk)
    if request.method == "POST":
        if je.is_posted:
            messages.error(request, "Cannot delete a posted journal entry.")
        else:
            je.delete()
            messages.success(request, f"Journal Entry {je.entry_number} deleted.")
        return redirect('finance:journal_list')
    return redirect('finance:journal_list')
