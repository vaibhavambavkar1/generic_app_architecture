from django.test import TestCase
from decimal import Decimal
from django.core.exceptions import ValidationError

from .models import Account, AccountCategory, JournalEntry, JournalEntryLine

class FinanceLedgerTests(TestCase):
    
    def setUp(self):
        # Setup Chart of Accounts
        self.asset_acc = Account.objects.create(
            code="1000", name="Cash", category=AccountCategory.ASSET
        )
        self.expense_acc = Account.objects.create(
            code="5000", name="Rent Expense", category=AccountCategory.EXPENSE
        )
        self.liability_acc = Account.objects.create(
            code="2000", name="Accounts Payable", category=AccountCategory.LIABILITY
        )
        self.revenue_acc = Account.objects.create(
            code="4000", name="Sales Revenue", category=AccountCategory.REVENUE
        )
        self.equity_acc = Account.objects.create(
            code="3000", name="Owner Equity", category=AccountCategory.EQUITY
        )

    def test_account_balance_calculation_asset_and_expense(self):
        """
        Assets and Expenses should increase on Debit and decrease on Credit.
        Balance = Debits - Credits
        """
        je = JournalEntry.objects.create(entry_number="JE-001", is_posted=False)
        
        # Add 500 Debit and 100 Credit to Asset
        JournalEntryLine.objects.create(journal_entry=je, account=self.asset_acc, debit=Decimal("500.00"))
        JournalEntryLine.objects.create(journal_entry=je, account=self.asset_acc, credit=Decimal("100.00"))
        
        # Add 300 Debit to Expense
        JournalEntryLine.objects.create(journal_entry=je, account=self.expense_acc, debit=Decimal("300.00"))
        
        # Cash: 500 - 100 = 400
        self.assertEqual(self.asset_acc.balance, Decimal("400.00"))
        # Expense: 300 - 0 = 300
        self.assertEqual(self.expense_acc.balance, Decimal("300.00"))

    def test_account_balance_calculation_liability_revenue_equity(self):
        """
        Liabilities, Revenue, and Equity should increase on Credit and decrease on Debit.
        Balance = Credits - Debits
        """
        je = JournalEntry.objects.create(entry_number="JE-002", is_posted=False)
        
        # Revenue: 1000 Credit, 200 Debit -> Balance: 800
        JournalEntryLine.objects.create(journal_entry=je, account=self.revenue_acc, credit=Decimal("1000.00"))
        JournalEntryLine.objects.create(journal_entry=je, account=self.revenue_acc, debit=Decimal("200.00"))
        
        # Liability: 500 Credit -> Balance: 500
        JournalEntryLine.objects.create(journal_entry=je, account=self.liability_acc, credit=Decimal("500.00"))
        
        self.assertEqual(self.revenue_acc.balance, Decimal("800.00"))
        self.assertEqual(self.liability_acc.balance, Decimal("500.00"))

    def test_journal_entry_line_validation(self):
        """
        Test that a Journal Entry Line cannot have both Debit and Credit > 0, 
        and cannot have both == 0.
        """
        je = JournalEntry.objects.create(entry_number="JE-003")
        
        # Both > 0 should fail
        line_both = JournalEntryLine(journal_entry=je, account=self.asset_acc, debit=Decimal("100.00"), credit=Decimal("100.00"))
        with self.assertRaises(ValidationError):
            line_both.clean()
            
        # Both == 0 should fail
        line_neither = JournalEntryLine(journal_entry=je, account=self.asset_acc, debit=Decimal("0.00"), credit=Decimal("0.00"))
        with self.assertRaises(ValidationError):
            line_neither.clean()

    def test_journal_entry_post_validation(self):
        """
        Test that a Journal Entry cannot be posted if Total Debits != Total Credits.
        """
        je = JournalEntry.objects.create(entry_number="JE-004")
        
        # Add imbalanced lines: 500 Debit, 400 Credit
        JournalEntryLine.objects.create(journal_entry=je, account=self.asset_acc, debit=Decimal("500.00"))
        JournalEntryLine.objects.create(journal_entry=je, account=self.liability_acc, credit=Decimal("400.00"))
        
        # Attempting to post should raise validation error
        je.is_posted = True
        with self.assertRaises(ValidationError):
            je.clean()
            
        # Fix the balance by adding 100 more Credit
        JournalEntryLine.objects.create(journal_entry=je, account=self.liability_acc, credit=Decimal("100.00"))
        
        # Now it should clean successfully without raising
        try:
            je.clean()
        except ValidationError:
            self.fail("JournalEntry clean() raised ValidationError unexpectedly on balanced entry.")
