from django.contrib import admin
from .models import KYCRecord

@admin.register(KYCRecord)
class KYCRecordAdmin(admin.ModelAdmin):
    list_display = ['applicant', 'kyc_status', 'bureau_score', 'bureau_source', 'name_match_score']
    list_filter = ['kyc_status', 'bureau_source']
