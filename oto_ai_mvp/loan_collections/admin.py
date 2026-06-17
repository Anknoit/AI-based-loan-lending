from django.contrib import admin
from .models import LoanRepayment, CollectionsAlert

@admin.register(LoanRepayment)
class LoanRepaymentAdmin(admin.ModelAdmin):
    list_display = ['applicant', 'month_number', 'emi_amount', 'paid_on_time', 'days_past_due']
    list_filter = ['paid_on_time']

@admin.register(CollectionsAlert)
class CollectionsAlertAdmin(admin.ModelAdmin):
    list_display = ['applicant', 'risk_bucket', 'dpd_30_prob', 'recommended_channel', 'language']
    list_filter = ['risk_bucket', 'language']
