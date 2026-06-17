from django.contrib import admin
from .models import Applicant

@admin.register(Applicant)
class ApplicantAdmin(admin.ModelAdmin):
    list_display = ['name', 'city', 'employment_type', 'bike_model', 'loan_amount', 'disbursed']
    list_filter = ['city', 'employment_type', 'disbursed']
    search_fields = ['name', 'email', 'phone']
