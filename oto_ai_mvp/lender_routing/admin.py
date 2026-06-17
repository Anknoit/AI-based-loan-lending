from django.contrib import admin
from .models import LenderRoute

@admin.register(LenderRoute)
class LenderRouteAdmin(admin.ModelAdmin):
    list_display = ['applicant', 'selected_lender', 'lender_response', 'approval_probability', 'expected_yield']
    list_filter = ['selected_lender', 'lender_response']
